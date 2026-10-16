"""Unit tests for modernized PySide6 UI widgets (InteractiveCanvas, ToolSelector, MainWindow)."""
from __future__ import annotations

import os
from pathlib import Path
from PIL import Image
import pytest
from PySide6 import QtCore, QtGui, QtWidgets

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp():
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


def test_tool_selector(qapp):
    from photoai.ui.widgets.tool_selector import ToolSelector, RECIPE_ITEMS

    selector = ToolSelector()
    assert selector.count() == 10
    assert selector.count() == len(RECIPE_ITEMS)

    # First recipe default
    assert selector.current_recipe_id() == "upscale_4k"

    # Switching row emits recipe_selected signal
    received = []
    selector.recipe_selected.connect(received.append)

    selector.setCurrentRow(1)
    assert selector.current_recipe_id() == "skin_retouch"
    assert "skin_retouch" in received


def test_interactive_canvas(qapp):
    from photoai.ui.widgets.interactive_canvas import InteractiveCanvas

    canvas = InteractiveCanvas()
    assert not canvas.has_image()
    assert not canvas.has_mask()
    assert canvas.mode() == InteractiveCanvas.MODE_PAN

    # Set pixmap
    pm = QtGui.QPixmap(200, 150)
    pm.fill(QtCore.Qt.GlobalColor.white)
    canvas.set_image(pm)

    assert canvas.has_image()
    assert canvas.image_size() == QtCore.QSize(200, 150)

    # Change mode & brush size
    canvas.set_mode(InteractiveCanvas.MODE_BRUSH)
    assert canvas.mode() == InteractiveCanvas.MODE_BRUSH
    canvas.set_brush_size(42)
    assert canvas.brush_size() == 42

    canvas.clear_mask()
    assert not canvas.has_mask()

    canvas.clear()
    assert not canvas.has_image()


def test_main_window_init(qapp, tmp_path):
    from photoai.ui.main_window import MainWindow

    window = MainWindow()
    assert window.tools.count() == 10
    assert window.image_info_chip.text() == "Chưa có ảnh"
    assert window.brush_size_label.text() == "28 px"

    # Test loading an image via _load_path
    img_path = tmp_path / "test_input.jfif"
    img = Image.new("RGB", (320, 240), color="blue")
    img.save(img_path)

    window._load_path(str(img_path))
    assert window.canvas.has_image()
    assert "JFIF" in window.image_info_chip.text()
    assert "320×240" in window.image_info_chip.text()
    assert window.action_run.isEnabled()
