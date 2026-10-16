"""Interactive canvas: zoom/pan, mask painting, drag & drop (design §2).

Provides the states the design system requires — an empty state, a visible mask
overlay (so painting is never guesswork) and clear cursor feedback — plus
drag-and-drop and clamped zoom so a 4K image can never be lost off-screen.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from photoai.storage.image_codec import SUPPORTED_INPUT_EXTENSIONS
from photoai.ui import icons, theme

MIN_ZOOM, MAX_ZOOM = 0.05, 8.0
_IMAGE_EXT = SUPPORTED_INPUT_EXTENSIONS


class InteractiveCanvas(QtWidgets.QGraphicsView):
    mask_changed = QtCore.Signal()
    file_dropped = QtCore.Signal(str)
    zoom_changed = QtCore.Signal(float)

    MODE_PAN = "pan"
    MODE_BRUSH = "brush"
    MODE_ERASE = "erase"

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("InteractiveCanvas")
        self.setAcceptDrops(True)
        self.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform, True)
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.setBackgroundBrush(QtGui.QColor(theme.CANVAS_BG))
        self.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self._scene = QtWidgets.QGraphicsScene(self)
        self.setScene(self._scene)
        self._pix_item: Optional[QtWidgets.QGraphicsPixmapItem] = None
        self._mask: Optional[QtGui.QImage] = None
        self._mask_overlay: Optional[QtGui.QImage] = None
        self._mask_overlay_bytes: Optional[bytes] = None
        self._cached_overlay_array: Optional[np.ndarray] = None
        self._mask_used = False
        self._dirty_overlay = False
        self._dragging_file = False
        self._empty_icon = icons.pixmap("image", theme.PALETTE.text_faint, 48)
        self._drop_icon = icons.pixmap("folder", theme.PALETTE.accent, 48)

        self._mode = self.MODE_PAN
        self._brush = 28
        self._painting = False
        self._panning = False
        self._pan_origin = QtCore.QPoint()

        self.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)
        self._apply_cursor()

    # --- state ------------------------------------------------------------
    def has_image(self) -> bool:
        return self._pix_item is not None

    def image_size(self) -> QtCore.QSize:
        if self._pix_item is None:
            return QtCore.QSize()
        return self._pix_item.pixmap().size()

    def set_image(self, pixmap: QtGui.QPixmap) -> None:
        self._scene.clear()
        self._pix_item = self._scene.addPixmap(pixmap)
        self._pix_item.setTransformationMode(QtCore.Qt.TransformationMode.SmoothTransformation)
        self._scene.setSceneRect(QtCore.QRectF(pixmap.rect()))
        self._mask = QtGui.QImage(pixmap.size(), QtGui.QImage.Format.Format_Grayscale8)
        self._mask.fill(0)
        self._mask_overlay = None
        self._mask_used = False
        self._dirty_overlay = True
        self.fit_to_view()
        self.viewport().update()

    def clear(self) -> None:
        self._scene.clear()
        self._pix_item = None
        self._mask = None
        self._mask_overlay = None
        self._cached_overlay_array = None
        self._scene.setSceneRect(QtCore.QRectF())
        self.resetTransform()
        self.viewport().update()


    def mask_image(self) -> Optional[QtGui.QImage]:
        """Return the painted mask (grayscale, white = selected) or ``None``."""
        if self._mask is None:
            return None
        return self._mask

    def has_mask(self) -> bool:
        """True once the user has painted anything on the mask."""
        return self._mask is not None and self._mask_used

    # --- modes / brush ----------------------------------------------------
    def set_mode(self, mode: str) -> None:
        self._mode = mode
        self._apply_cursor()

    def mode(self) -> str:
        return self._mode

    def set_brush_size(self, size: int) -> None:
        self._brush = max(2, int(size))

    def brush_size(self) -> int:
        return self._brush

    def clear_mask(self) -> None:
        if self._mask is not None:
            self._mask.fill(0)
            self._mask_overlay = None
            self._mask_used = False
            self._dirty_overlay = True
            self.viewport().update()
            self.mask_changed.emit()

    def _apply_cursor(self) -> None:
        if self._mode == self.MODE_PAN:
            self.setCursor(QtCore.Qt.CursorShape.OpenHandCursor)
        else:
            self.setCursor(QtCore.Qt.CursorShape.CrossCursor)

    # --- zoom -------------------------------------------------------------
    def current_zoom(self) -> float:
        return float(self.transform().m11())

    def fit_to_view(self) -> None:
        if self._pix_item is None:
            return
        self.resetTransform()
        self.fitInView(self._scene.sceneRect(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        self.zoom_changed.emit(self.current_zoom())

    def zoom_to(self, factor: float) -> None:
        if self._pix_item is None:
            return
        self.resetTransform()
        self.scale(factor, factor)
        self.zoom_changed.emit(self.current_zoom())

    def zoom_by(self, step: float) -> None:
        if self._pix_item is None:
            return
        target = max(MIN_ZOOM, min(MAX_ZOOM, self.current_zoom() * step))
        factor = target / max(self.current_zoom(), 1e-9)
        self.scale(factor, factor)
        self.zoom_changed.emit(self.current_zoom())

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        if self._pix_item is None:
            return
        delta = event.angleDelta().y()
        if delta == 0:
            return
        step = 1.15 if delta > 0 else 1 / 1.15
        before = self.current_zoom()
        target = max(MIN_ZOOM, min(MAX_ZOOM, before * step))
        self.scale(target / before, target / before)
        self.zoom_changed.emit(self.current_zoom())

    # --- mouse ------------------------------------------------------------
    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._pix_item is None:
            super().mousePressEvent(event)
            return

        space_pan = event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier
        if event.button() == QtCore.Qt.MouseButton.MiddleButton or (
            event.button() == QtCore.Qt.MouseButton.LeftButton
            and (self._mode == self.MODE_PAN or space_pan)
        ):
            self._panning = True
            self._pan_origin = event.position().toPoint()
            self.setCursor(QtCore.Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        if event.button() == QtCore.Qt.MouseButton.LeftButton and self._mode in (
            self.MODE_BRUSH,
            self.MODE_ERASE,
        ):
            self._painting = True
            self._paint_at(event.position())
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._panning:
            delta = event.position().toPoint() - self._pan_origin
            self._pan_origin = event.position().toPoint()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        if self._painting:
            self._paint_at(event.position())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._panning:
            self._panning = False
            self._apply_cursor()
        if self._painting:
            self._painting = False
            self.mask_changed.emit()
        super().mouseReleaseEvent(event)

    def _paint_at(self, viewport_pos: QtCore.QPointF) -> None:
        if self._mask is None or self._pix_item is None:
            return
        scene_pos = self.mapToScene(viewport_pos.toPoint())
        painter = QtGui.QPainter(self._mask)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        colour = 255 if self._mode == self.MODE_BRUSH else 0
        pen = QtGui.QPen(QtGui.QColor(colour, colour, colour), self._brush)
        pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawPoint(scene_pos)
        painter.end()
        self._mask_used = True
        self._dirty_overlay = True
        self.viewport().update()

    # --- drag & drop ------------------------------------------------------
    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(_IMAGE_EXT):
                    self._dragging_file = True
                    self.viewport().update()
                    event.acceptProposedAction()
                    return
        super().dragEnterEvent(event)

    def dragLeaveEvent(self, event: QtGui.QDragLeaveEvent) -> None:
        if self._dragging_file:
            self._dragging_file = False
            self.viewport().update()
        super().dragLeaveEvent(event)

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        self._dragging_file = False
        self.viewport().update()
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(_IMAGE_EXT):
                self.file_dropped.emit(path)
                event.acceptProposedAction()
                return

    # --- painting ---------------------------------------------------------
    def drawForeground(self, painter: QtGui.QPainter, _rect: QtCore.QRectF) -> None:
        if self._mask is None or self._pix_item is None:
            return
        if self._dirty_overlay or self._mask_overlay is None:
            self._rebuild_overlay()
        painter.drawImage(QtCore.QRectF(self._pix_item.pixmap().rect()), self._mask_overlay)

    def _rebuild_overlay(self) -> None:
        """Vectorised mask -> translucent overlay (memory-efficient preallocated buffer)."""
        mask = self._mask
        if mask is None:
            return
        height, width = mask.height(), mask.width()
        stride = mask.bytesPerLine()
        raw = np.frombuffer(mask.constBits(), dtype=np.uint8, count=stride * height)
        gray = raw.reshape(height, stride)[:, :width]

        r, g, b, a = theme.MASK_RGBA

        # Re-allocate RGB channels only when image dimensions change
        if (
            self._cached_overlay_array is None
            or self._cached_overlay_array.shape[0] != height
            or self._cached_overlay_array.shape[1] != width
        ):
            self._cached_overlay_array = np.zeros((height, width, 4), dtype=np.uint8)  # BGRA (ARGB32)
            self._cached_overlay_array[..., 0] = b
            self._cached_overlay_array[..., 1] = g
            self._cached_overlay_array[..., 2] = r

        # Fast bitwise scalar multiply and shift: (gray * a) >> 8
        self._cached_overlay_array[..., 3] = (gray.astype(np.uint16) * a >> 8).astype(np.uint8)
        self._mask_overlay_bytes = self._cached_overlay_array.tobytes()
        # .copy() detaches Qt from the Python buffer so it cannot be freed early.
        self._mask_overlay = QtGui.QImage(
            self._mask_overlay_bytes, width, height, QtGui.QImage.Format.Format_ARGB32
        ).copy()
        self._dirty_overlay = False

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        super().paintEvent(event)
        if self._pix_item is not None and not self._dragging_file:
            return

        painter = QtGui.QPainter(self.viewport())
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        rect = self.viewport().rect().adjusted(24, 24, -24, -24)

        if self._dragging_file:
            # Glow state when hovering files
            pen = QtGui.QPen(QtGui.QColor(theme.PALETTE.accent))
            pen.setStyle(QtCore.Qt.PenStyle.DashLine)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(QtGui.QColor(34, 197, 94, 25))
            painter.drawRoundedRect(rect, theme.RADIUS_CARD, theme.RADIUS_CARD)

            icon_pm = self._drop_icon
            painter.drawPixmap(rect.center().x() - 24, rect.center().y() - 60, icon_pm)

            font = painter.font()
            font.setPointSizeF(13.0)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QtGui.QColor(theme.PALETTE.accent))
            painter.drawText(
                rect.adjusted(0, 10, 0, 0),
                QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignCenter,
                "Thả ảnh để mở ngay",
            )
            font.setPointSizeF(10.5)
            font.setBold(False)
            painter.setFont(font)
            painter.setPen(QtGui.QColor(theme.PALETTE.text_muted))
            painter.drawText(
                rect.adjusted(0, 50, 0, 0),
                QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignCenter,
                "Tự động chuẩn hóa màu sRGB & bảo toàn ảnh gốc tuyệt đối",
            )
            painter.end()
            return

        if self._pix_item is None:
            # Modern Empty State with format pills
            pen = QtGui.QPen(QtGui.QColor(theme.PALETTE.border))
            pen.setStyle(QtCore.Qt.PenStyle.DashLine)
            pen.setWidth(1)
            painter.setPen(pen)
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect, theme.RADIUS_CARD, theme.RADIUS_CARD)

            icon_pm = self._empty_icon
            painter.drawPixmap(rect.center().x() - 24, rect.center().y() - 75, icon_pm)

            font = painter.font()
            font.setPointSizeF(12.5)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QtGui.QColor(theme.PALETTE.text))
            painter.drawText(
                rect.adjusted(0, -10, 0, 0),
                QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignCenter,
                "Không gian làm việc",
            )

            font.setPointSizeF(10.5)
            font.setBold(False)
            painter.setFont(font)
            painter.setPen(QtGui.QColor(theme.PALETTE.text_muted))
            painter.drawText(
                rect.adjusted(0, 20, 0, 0),
                QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignCenter,
                "Kéo thả ảnh vào đây hoặc bấm Mở ảnh (Ctrl+O)",
            )

            # Draw supported format pill chips
            formats = ["JFIF", "JPG", "PNG", "WEBP", "BMP", "TIFF"]
            pill_w, pill_h, gap = 48, 22, 8
            total_w = len(formats) * pill_w + (len(formats) - 1) * gap
            start_x = rect.center().x() - total_w // 2
            pill_y = rect.center().y() + 52

            pill_font = QtGui.QFont("JetBrains Mono")
            pill_font.setPointSizeF(8.5)
            pill_font.setBold(True)
            painter.setFont(pill_font)

            for i, fmt in enumerate(formats):
                px = start_x + i * (pill_w + gap)
                pill_rect = QtCore.QRectF(px, pill_y, pill_w, pill_h)
                painter.setPen(QtGui.QPen(QtGui.QColor(theme.PALETTE.border)))
                painter.setBrush(QtGui.QColor(theme.PALETTE.elevated))
                painter.drawRoundedRect(pill_rect, 4, 4)

                painter.setPen(QtGui.QColor(theme.PALETTE.text_muted))
                painter.drawText(pill_rect, QtCore.Qt.AlignmentFlag.AlignCenter, fmt)

            painter.end()
