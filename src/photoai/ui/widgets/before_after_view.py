"""Before/After comparison slider (design §2 ui/widgets).

Both frames are letterboxed consistently and labelled ("Trước" / "Sau") so the
comparison never relies on position alone. The divider is draggable and shows a
grip handle.
"""
from __future__ import annotations

from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

from photoai.ui import theme


class BeforeAfterView(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("BeforeAfterView")
        self.setMinimumHeight(200)
        self.setMouseTracking(True)
        self._before: Optional[QtGui.QPixmap] = None
        self._after: Optional[QtGui.QPixmap] = None
        self._split = 0.5
        self._dragging = False
        self._scaled_size: Optional[QtCore.QSize] = None
        self._scaled_before: Optional[QtGui.QPixmap] = None
        self._scaled_after: Optional[QtGui.QPixmap] = None

    def set_images(self, before: QtGui.QPixmap, after: QtGui.QPixmap) -> None:
        self._before = before
        self._after = after
        self._scaled_size = None
        self._scaled_before = None
        self._scaled_after = None
        self.update()

    def clear(self) -> None:
        self._before = self._after = None
        self._scaled_size = None
        self._scaled_before = None
        self._scaled_after = None
        self.update()

    # --- interaction ------------------------------------------------------
    def _target_rect(self, pixmap: QtGui.QPixmap) -> QtCore.QRect:
        scaled = pixmap.size().scaled(self.size(), QtCore.Qt.AspectRatioMode.KeepAspectRatio)
        return QtCore.QRect(
            (self.width() - scaled.width()) // 2,
            (self.height() - scaled.height()) // 2,
            scaled.width(),
            scaled.height(),
        )

    def _hit_zone(self) -> QtCore.QRect:
        if self._after is None:
            return QtCore.QRect()
        rect = self._target_rect(self._after)
        x = rect.left() + int(rect.width() * self._split)
        return QtCore.QRect(x - 10, rect.top(), 20, rect.height())

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._after is not None and event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._dragging = True
            self._update_split(event.position().x())

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._after is None:
            self.unsetCursor()
            return
        if self._dragging:
            self._update_split(event.position().x())
        elif self._hit_zone().contains(event.position().toPoint()):
            self.setCursor(QtCore.Qt.CursorShape.SplitHCursor)
        else:
            self.unsetCursor()

    def mouseReleaseEvent(self, _event: QtGui.QMouseEvent) -> None:
        self._dragging = False

    def _update_split(self, x: float) -> None:
        if self._after is None:
            return
        rect = self._target_rect(self._after)
        if rect.width() <= 0:
            return
        self._split = max(0.0, min(1.0, (x - rect.left()) / rect.width()))
        self.update()

    # --- rendering --------------------------------------------------------
    def paintEvent(self, _event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtGui.QColor(theme.PALETTE.surface))

        if self._before is None or self._after is None:
            painter.setPen(QtGui.QColor(theme.PALETTE.text_faint))
            painter.drawText(self.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, "So sánh Trước / Sau hiện ở đây")
            painter.end()
            return

        rect = self._target_rect(self._after)

        # Scale only once when viewport dimensions change
        if (
            self._scaled_size != rect.size()
            or self._scaled_before is None
            or self._scaled_after is None
        ):
            self._scaled_size = rect.size()
            self._scaled_after = self._after.scaled(
                rect.size(),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
            self._scaled_before = self._before.scaled(
                rect.size(),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )

        painter.drawPixmap(rect.topLeft(), self._scaled_after)
        split_x = rect.left() + int(rect.width() * self._split)
        painter.save()
        painter.setClipRect(QtCore.QRect(rect.left(), rect.top(), split_x - rect.left(), rect.height()))
        painter.drawPixmap(rect.topLeft(), self._scaled_before)
        painter.restore()

        # corner labels (state is not conveyed by position alone)
        self._draw_label(painter, rect.adjusted(8, 8, 0, 0), "TRƯỚC", QtCore.Qt.AlignmentFlag.AlignLeft)
        self._draw_label(painter, rect.adjusted(0, 8, -8, 0), "SAU", QtCore.Qt.AlignmentFlag.AlignRight)

        # divider + grip
        painter.setPen(QtGui.QPen(QtGui.QColor(theme.PALETTE.text), 2))
        painter.drawLine(split_x, rect.top(), split_x, rect.bottom())
        painter.setBrush(QtGui.QColor(theme.PALETTE.accent))
        painter.setPen(QtGui.QPen(QtGui.QColor(theme.PALETTE.accent_text), 1))
        painter.drawEllipse(QtCore.QPoint(split_x, rect.center().y()), 9, 9)
        painter.end()


    def _draw_label(self, painter: QtGui.QPainter, anchor: QtCore.QRect, text: str, align) -> None:
        metrics = painter.fontMetrics()
        width = metrics.horizontalAdvance(text) + 16
        box = QtCore.QRect(anchor.left(), anchor.top(), width, 22)
        if align == QtCore.Qt.AlignmentFlag.AlignRight:
            box.moveRight(anchor.right())
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor(0, 0, 0, 150))
        painter.drawRoundedRect(box, theme.RADIUS_PILL, theme.RADIUS_PILL)
        painter.setPen(QtGui.QColor(theme.PALETTE.text))
        painter.drawText(box, QtCore.Qt.AlignmentFlag.AlignCenter, text)
