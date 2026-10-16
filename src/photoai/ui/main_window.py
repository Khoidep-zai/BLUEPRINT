"""Main desktop window (design §2 ui/main_window.py).

Layout: menu bar + toolbar → sidebar of the ten functions → canvas workspace
(canvas controls over the image, before/after slider below) → QA dock on the
right → status bar with progress and inference device.

Includes the required UI states: empty (no image), busy (running), success and
error banners, and full keyboard operation.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image
from PySide6 import QtCore, QtGui, QtWidgets

from photoai.config import ASSETS_DIR, PROJECT_ROOT, device, ensure_workspace_dirs
from photoai.engine.loader import load_recipe_by_id
from photoai.storage.image_codec import (
    SUPPORTED_INPUT_EXTENSIONS,
    load_image,
    normalize_export_path,
    save_image,
)
from photoai.ui import icons, theme
from photoai.ui.widgets.before_after_view import BeforeAfterView
from photoai.ui.widgets.interactive_canvas import InteractiveCanvas
from photoai.ui.widgets.qa_panel import QaPanel
from photoai.ui.widgets.tool_selector import ToolSelector
from photoai.ui.widgets.watermark_dialog import WatermarkDialog
from photoai.ui.workers_qt import PipelineWorker

_STAGE_LABEL = {
    "Ingest": "Chuẩn hoá ảnh",
    "Detect": "Nhận diện",
    "Mask": "Tạo mask / ROI",
    "GPU Edit": "Xử lý (CV + GPU)",
    "Blend": "Ghép vùng",
    "QA": "Chấm điểm chất lượng",
    "Done": "Hoàn tất",
}


def _pil_to_pixmap(image: Image.Image) -> QtGui.QPixmap:
    rgb = image.convert("RGB")
    data = rgb.tobytes("raw", "RGB")
    qimage = QtGui.QImage(data, rgb.width, rgb.height, rgb.width * 3, QtGui.QImage.Format.Format_RGB888)
    return QtGui.QPixmap.fromImage(qimage.copy())


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        ensure_workspace_dirs()

        self.setWindowTitle("Photo AI Desktop — Chỉnh ảnh offline")
        self.resize(1440, 900)
        self.setMinimumSize(1080, 680)
        self.setAcceptDrops(True)

        qss = ASSETS_DIR / "dark.qss"
        if qss.is_file():
            self.setStyleSheet(qss.read_text(encoding="utf-8"))

        self._source_path: Optional[Path] = None
        self._source_image: Optional[Image.Image] = None
        self._result_image: Optional[Image.Image] = None
        self._worker: Optional[PipelineWorker] = None

        self._build_actions()
        self._build_menu()
        self._build_toolbar()
        self._build_body()
        self._build_statusbar()
        self._wire_shortcuts()

        self._on_recipe(self.tools.current_recipe_id())
        self._set_idle_state()

    # --- construction -----------------------------------------------------
    def _build_actions(self) -> None:
        self.action_open = QtGui.QAction(icons.icon("folder", theme.PALETTE.text), "Mở ảnh…", self)
        self.action_open.setShortcut("Ctrl+O")
        self.action_open.triggered.connect(self._open_image)

        self.action_save = QtGui.QAction(icons.icon("save", theme.PALETTE.text), "Lưu kết quả…", self)
        self.action_save.setShortcut("Ctrl+S")
        self.action_save.setEnabled(False)
        self.action_save.triggered.connect(self._save_result)

        self.action_run = QtGui.QAction(icons.icon("play", theme.PALETTE.accent_text), "Chạy xử lý", self)
        self.action_run.setShortcut("Ctrl+Return")
        self.action_run.setEnabled(False)
        self.action_run.triggered.connect(self._run_pipeline)

        self.action_clear_mask = QtGui.QAction(icons.icon("clear", theme.PALETTE.text), "Xóa mask", self)
        self.action_clear_mask.setShortcut("Ctrl+Shift+M")
        self.action_clear_mask.triggered.connect(lambda: self.canvas.clear_mask())

        self.action_fit = QtGui.QAction("Vừa khung", self)
        self.action_fit.setShortcut("Ctrl+0")
        self.action_fit.triggered.connect(lambda: self.canvas.fit_to_view())

        self.action_actual = QtGui.QAction("Kích thước thật", self)
        self.action_actual.setShortcut("Ctrl+1")
        self.action_actual.triggered.connect(lambda: self.canvas.zoom_to(1.0))

        self.action_quit = QtGui.QAction("Thoát", self)
        self.action_quit.setShortcut("Ctrl+Q")
        self.action_quit.triggered.connect(self.close)

        self.action_about = QtGui.QAction("Giới thiệu", self)
        self.action_about.triggered.connect(self._show_about)

    def _build_menu(self) -> None:
        menu_file = self.menuBar().addMenu("&Tệp")
        menu_file.addAction(self.action_open)
        menu_file.addAction(self.action_save)
        menu_file.addSeparator()
        menu_file.addAction(self.action_quit)

        menu_run = self.menuBar().addMenu("&Xử lý")
        menu_run.addAction(self.action_run)
        menu_run.addAction(self.action_clear_mask)
        menu_run.addSeparator()
        menu_run.addAction(self.action_fit)
        menu_run.addAction(self.action_actual)

        menu_help = self.menuBar().addMenu("&Trợ giúp")
        menu_help.addAction(self.action_about)

    def _build_toolbar(self) -> None:
        bar = QtWidgets.QToolBar("Chính")
        bar.setMovable(False)
        bar.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        bar.addAction(self.action_open)
        bar.addAction(self.action_run)
        bar.addSeparator()
        bar.addAction(self.action_save)
        self.addToolBar(bar)

    def _build_body(self) -> None:
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_sidebar())
        splitter.addWidget(self._build_workspace())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([300, 1140])
        self.setCentralWidget(splitter)

        self.qa_panel = QaPanel()
        dock = QtWidgets.QDockWidget("Chất lượng (QA)", self)
        dock.setWidget(self.qa_panel)
        dock.setAllowedAreas(
            QtCore.Qt.DockWidgetArea.RightDockWidgetArea | QtCore.Qt.DockWidgetArea.LeftDockWidgetArea
        )
        dock.setMinimumWidth(340)
        self.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def _build_sidebar(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QWidget()
        panel.setObjectName("Sidebar")
        panel.setMaximumWidth(360)
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(theme.SPACE_MD, theme.SPACE_MD, theme.SPACE_MD, theme.SPACE_MD)
        layout.setSpacing(theme.SPACE_SM)

        title = QtWidgets.QLabel("Chức năng")
        title.setProperty("role", "h2")
        layout.addWidget(title)

        hint = QtWidgets.QLabel("Chọn 1 trong 10 chức năng, sau đó bấm Chạy xử lý.")
        hint.setProperty("role", "caption")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.tools = ToolSelector()
        self.tools.recipe_selected.connect(self._on_recipe)
        layout.addWidget(self.tools, stretch=1)

        # Recipe info card
        self.recipe_card = QtWidgets.QFrame()
        self.recipe_card.setObjectName("RecipeCard")
        card_layout = QtWidgets.QVBoxLayout(self.recipe_card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(4)

        card_title = QtWidgets.QLabel("THÔNG TIN CÔNG THỨC")
        card_title.setObjectName("RecipeCardHeader")
        card_layout.addWidget(card_title)

        self.recipe_note = QtWidgets.QLabel()
        self.recipe_note.setProperty("role", "faint")
        self.recipe_note.setWordWrap(True)
        card_layout.addWidget(self.recipe_note)
        layout.addWidget(self.recipe_card)

        self.run_button = QtWidgets.QPushButton("Chạy xử lý")
        self.run_button.setObjectName("PrimaryButton")
        self.run_button.setIcon(icons.icon("play", theme.PALETTE.accent_text, 18))
        self.run_button.clicked.connect(self._run_pipeline)
        layout.addWidget(self.run_button)

        row = QtWidgets.QHBoxLayout()
        row.setSpacing(theme.SPACE_SM)
        self.open_button = QtWidgets.QPushButton("Mở ảnh…")
        self.open_button.setIcon(icons.icon("folder", theme.PALETTE.text, 16))
        self.open_button.setObjectName("GhostButton")
        self.open_button.clicked.connect(self._open_image)
        self.save_button = QtWidgets.QPushButton("Lưu kết quả…")
        self.save_button.setIcon(icons.icon("save", theme.PALETTE.text, 16))
        self.save_button.setObjectName("GhostButton")
        self.save_button.clicked.connect(self._save_result)
        row.addWidget(self.open_button)
        row.addWidget(self.save_button)
        layout.addLayout(row)
        return panel

    def _build_workspace(self) -> QtWidgets.QWidget:
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(theme.SPACE_MD, theme.SPACE_MD, theme.SPACE_MD, theme.SPACE_MD)
        layout.setSpacing(theme.SPACE_SM)

        self.banner = QtWidgets.QLabel()
        self.banner.setProperty("role", "banner")
        self.banner.setWordWrap(True)
        self.banner.setVisible(False)
        layout.addWidget(self.banner)

        layout.addWidget(self._build_canvas_controls())

        self.canvas = InteractiveCanvas()
        self.canvas.file_dropped.connect(self._load_path)
        self.canvas.zoom_changed.connect(self._on_zoom)
        layout.addWidget(self.canvas, stretch=1)

        compare_header = QtWidgets.QLabel("So sánh Trước / Sau")
        compare_header.setProperty("role", "caption")
        layout.addWidget(compare_header)

        self.compare = BeforeAfterView()
        layout.addWidget(self.compare, stretch=0)
        return container

    def _build_canvas_controls(self) -> QtWidgets.QWidget:
        bar = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(bar)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(theme.SPACE_XS)

        self.pan_button = QtWidgets.QToolButton()
        self.pan_button.setIcon(icons.icon("hand", theme.PALETTE.text, 16))
        self.pan_button.setText("Di chuyển")
        self.pan_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.pan_button.setCheckable(True)
        self.pan_button.setChecked(True)

        self.brush_button = QtWidgets.QToolButton()
        self.brush_button.setIcon(icons.icon("brush", theme.PALETTE.text, 16))
        self.brush_button.setText("Cọ mask")
        self.brush_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.brush_button.setCheckable(True)

        self.eraser_button = QtWidgets.QToolButton()
        self.eraser_button.setIcon(icons.icon("eraser", theme.PALETTE.text, 16))
        self.eraser_button.setText("Tẩy")
        self.eraser_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.eraser_button.setCheckable(True)

        for button in (self.pan_button, self.brush_button, self.eraser_button):
            button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            row.addWidget(button)

        self.pan_button.clicked.connect(lambda: self._set_mode(InteractiveCanvas.MODE_PAN))
        self.brush_button.clicked.connect(lambda: self._set_mode(InteractiveCanvas.MODE_BRUSH))
        self.eraser_button.clicked.connect(lambda: self._set_mode(InteractiveCanvas.MODE_ERASE))

        brush_label = QtWidgets.QLabel("Cỡ cọ")
        brush_label.setProperty("role", "caption")
        row.addWidget(brush_label)

        self.brush_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.brush_slider.setRange(4, 160)
        self.brush_slider.setValue(28)
        self.brush_slider.setFixedWidth(130)
        self.brush_slider.valueChanged.connect(self._on_brush_change)
        row.addWidget(self.brush_slider)

        self.brush_size_label = QtWidgets.QLabel("28 px")
        self.brush_size_label.setObjectName("BrushSizeLabel")
        row.addWidget(self.brush_size_label)

        clear_button = QtWidgets.QToolButton()
        clear_button.setIcon(icons.icon("clear", theme.PALETTE.text, 16))
        clear_button.setText("Xóa mask")
        clear_button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        clear_button.clicked.connect(lambda: self.canvas.clear_mask())
        row.addWidget(clear_button)

        row.addStretch(1)

        self.image_info_chip = QtWidgets.QLabel("Chưa có ảnh")
        self.image_info_chip.setObjectName("ImageInfoChip")
        row.addWidget(self.image_info_chip)

        for text, name, handler in (
            ("−", "zoom-out", lambda: self.canvas.zoom_by(1 / 1.25)),
            ("+", "zoom-in", lambda: self.canvas.zoom_by(1.25)),
            ("Vừa khung", "fit", lambda: self.canvas.fit_to_view()),
        ):
            button = QtWidgets.QToolButton()
            button.setIcon(icons.icon(name, theme.PALETTE.text, 16))
            button.setText(text)
            button.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            button.clicked.connect(handler)
            row.addWidget(button)

        self.zoom_label = QtWidgets.QLabel("100%")
        self.zoom_label.setObjectName("DeviceChip")
        self.zoom_label.setMinimumWidth(56)
        self.zoom_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        row.addWidget(self.zoom_label)
        return bar

    def _build_statusbar(self) -> None:
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedWidth(220)
        self.progress.setTextVisible(False)

        self.device_chip = QtWidgets.QLabel(f"device: {device()}")
        self.device_chip.setObjectName("DeviceChip")

        self.statusBar().addWidget(self.progress)
        self.statusBar().addPermanentWidget(self.device_chip)
        self.statusBar().showMessage("Sẵn sàng — mở ảnh để bắt đầu.")

    def _wire_shortcuts(self) -> None:
        for key, delta in (("[", -8), ("]", 8)):
            shortcut = QtGui.QShortcut(QtGui.QKeySequence(key), self)
            shortcut.activated.connect(lambda d=delta: self._nudge_brush(d))

    # --- state helpers ----------------------------------------------------
    def _set_idle_state(self) -> None:
        has_image = self._source_image is not None
        self.action_run.setEnabled(has_image and self._worker is None)
        self.run_button.setEnabled(has_image and self._worker is None)
        self.action_save.setEnabled(self._result_image is not None)
        self.save_button.setEnabled(self._result_image is not None)

    def _show_banner(self, text: str, tone: str = "info") -> None:
        self.banner.setText(text)
        self.banner.setProperty("tone", tone)
        self.banner.style().unpolish(self.banner)
        self.banner.style().polish(self.banner)
        self.banner.setVisible(True)

    def _hide_banner(self) -> None:
        self.banner.setVisible(False)

    def _on_brush_change(self, value: int) -> None:
        self.canvas.set_brush_size(value)
        self.brush_size_label.setText(f"{value} px")

    def _nudge_brush(self, delta: int) -> None:
        self.brush_slider.setValue(self.brush_slider.value() + delta)

    def _set_mode(self, mode: str) -> None:
        self.canvas.set_mode(mode)
        self.pan_button.setChecked(mode == InteractiveCanvas.MODE_PAN)
        self.brush_button.setChecked(mode == InteractiveCanvas.MODE_BRUSH)
        self.eraser_button.setChecked(mode == InteractiveCanvas.MODE_ERASE)

    def _on_zoom(self, factor: float) -> None:
        self.zoom_label.setText(f"{factor * 100:.0f}%")

    def _on_recipe(self, recipe_id: str) -> None:
        if not recipe_id:
            return
        try:
            recipe = load_recipe_by_id(recipe_id)
        except Exception:
            return
        prompt = ""
        if recipe.prompt.vi:
            prompt_path = (PROJECT_ROOT / recipe.prompt.vi).resolve()
            try:
                if prompt_path.is_file():
                    prompt = prompt_path.read_text(encoding="utf-8").strip().splitlines()[0]
            except Exception:
                prompt = ""
        note = recipe.name_en
        if recipe.ownership_required:
            note += " · cần xác nhận quyền sở hữu"
        if prompt:
            note += f"\n{prompt}"
        self.recipe_note.setText(note)

    # --- drag & drop on window --------------------------------------------
    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(SUPPORTED_INPUT_EXTENSIONS):
                self._load_path(path)
                event.acceptProposedAction()
                return

    # --- actions ----------------------------------------------------------
    def _open_image(self) -> None:
        filters = (
            "Tất cả định dạng ảnh hỗ trợ (*.jfif *.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff *.gif);;"
            "Ảnh JFIF (*.jfif);;"
            "Ảnh JPEG (*.jpg *.jpeg);;"
            "Ảnh PNG (*.png);;"
            "Ảnh WebP (*.webp);;"
            "Ảnh BMP (*.bmp);;"
            "Ảnh TIFF (*.tif *.tiff);;"
            "Tất cả tệp (*.*)"
        )
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Chọn ảnh", "", filters)
        if path:
            self._load_path(path)

    def _load_path(self, path: str) -> None:
        try:
            image = load_image(Path(path))
        except Exception as exc:
            self._show_banner(f"Không mở được ảnh: {exc}", "error")
            return

        self._source_path = Path(path)
        self._source_image = image
        self._result_image = None
        self.canvas.set_image(_pil_to_pixmap(image))
        self.compare.clear()
        self.qa_panel.clear_report()
        self._hide_banner()
        self._set_idle_state()

        ext_name = self._source_path.suffix.upper().lstrip(".") or "IMAGE"
        self.image_info_chip.setText(f"{ext_name} · {image.width}×{image.height} px")
        self.statusBar().showMessage(
            f"Đã mở: {self._source_path.name} · Định dạng: {ext_name} · Kích thước: {image.width}×{image.height}px"
        )

    def _run_pipeline(self) -> None:
        if self._source_image is None or self._worker is not None:
            return

        recipe_id = self.tools.current_recipe_id()
        params: dict = {"seed": 42}

        if recipe_id == "remove_watermark":
            dialog = WatermarkDialog(self)
            if dialog.exec() != QtWidgets.QDialog.DialogCode.Accepted or not dialog.confirmed():
                self.statusBar().showMessage("Đã huỷ: chưa xác nhận quyền sở hữu.", 5000)
                return
            params["ownership_confirmed"] = True

        mask = self._canvas_mask()

        self.progress.setValue(0)
        self.action_run.setEnabled(False)
        self.run_button.setEnabled(False)
        self._show_banner(f"Đang xử lý: {recipe_id}…", "info")

        self._worker = PipelineWorker(recipe_id, self._source_image.copy(), mask=mask, params=params)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _canvas_mask(self) -> Optional[Image.Image]:
        if not self.canvas.has_mask():
            return None
        qimage = self.canvas.mask_image()
        if qimage is None:
            return None
        gray = qimage.convertToFormat(QtGui.QImage.Format.Format_Grayscale8)
        width, height = gray.width(), gray.height()
        stride = gray.bytesPerLine()
        raw = np.frombuffer(gray.constBits(), dtype=np.uint8, count=stride * height)
        array = raw.reshape(height, stride)[:, :width].copy()
        return Image.fromarray(array, mode="L")

    @QtCore.Slot(str, int)
    def _on_progress(self, stage: str, percent: int) -> None:
        self.progress.setValue(percent)
        self.statusBar().showMessage(_STAGE_LABEL.get(stage, stage))

    @QtCore.Slot(object)
    def _on_finished(self, result) -> None:
        self._worker = None
        self._result_image = result.image
        self.compare.set_images(_pil_to_pixmap(self._source_image), _pil_to_pixmap(result.image))
        self.qa_panel.show_report(result.report.metrics, result.report.thresholds, result.report.passed)
        self._set_idle_state()
        self.progress.setValue(100)

        if result.report.passed:
            self._show_banner("Hoàn tất — kết quả đạt mọi chỉ số chất lượng.", "success")
        else:
            self._show_banner(
                "Hoàn tất nhưng chưa đạt QA — đã trả về nhánh Classical CV an toàn.",
                "error",
            )
        location = result.context.export_path or "(chưa lưu)"
        self.statusBar().showMessage(f"Xong trong {result.duration_ms:.0f} ms · {location}", 8000)

    @QtCore.Slot(str)
    def _on_failed(self, message: str) -> None:
        self._worker = None
        self._set_idle_state()
        self.progress.setValue(0)
        self._show_banner(f"Lỗi: {message}", "error")
        self.statusBar().showMessage("Xử lý thất bại.")

    def _save_result(self) -> None:
        if self._result_image is None:
            return

        base_stem = self._source_path.stem if self._source_path else "photoai"
        default = f"{base_stem}_photoai.png"
        filters = "Ảnh PNG (*.png);;Ảnh JPEG (*.jpg *.jpeg)"
        path, selected_filter = QtWidgets.QFileDialog.getSaveFileName(
            self, "Lưu kết quả (Luôn xuất PNG hoặc JPG)", default, filters
        )
        if not path:
            return

        # Enforce strict PNG or JPG output
        is_jpeg = "jpg" in selected_filter.lower() or Path(path).suffix.lower() in (".jpg", ".jpeg")
        format_hint = "JPEG" if is_jpeg else "PNG"
        target_path = normalize_export_path(Path(path), preferred_format="jpg" if is_jpeg else "png")

        try:
            saved = save_image(self._result_image, target_path, format=format_hint)
        except Exception as exc:
            self._show_banner(f"Không lưu được: {exc}", "error")
            return

        ext_label = saved.suffix.upper().lstrip(".")
        self._show_banner(f"Đã lưu kết quả thành công: {saved.name} [{ext_label}]", "success")
        self.statusBar().showMessage(f"Đã lưu: {saved} ({ext_label})", 8000)


    def _show_about(self) -> None:
        QtWidgets.QMessageBox.information(
            self,
            "Photo AI Desktop",
            "Ứng dụng chỉnh ảnh 100% offline trên GPU cục bộ.\n\n"
            "Pipeline 7 bước: Ingest → Detect → ROI/Mask → Edit → Blend → AutoQA → Export.\n"
            f"Thiết bị suy luận hiện tại: {device()}",
        )
