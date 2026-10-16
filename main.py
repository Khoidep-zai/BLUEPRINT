"""Photo AI Desktop entry point (see PHOTO_AI_SYSTEM_DESIGN.md).

100% local: no web server, no Redis, no cloud API.

Usage:
    python main.py               # launch the desktop app
    python main.py --self-check  # boot the window offscreen, verify, exit 0
"""
from __future__ import annotations

import os
import sys

# Make the ``photoai`` package importable when running from the project root.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from photoai.config import device, ensure_workspace_dirs  # noqa: E402
from photoai.engine.loader import load_all  # noqa: E402
from photoai.storage.db import init_db  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    self_check = "--self-check" in argv
    if self_check:
        argv = [arg for arg in argv if arg != "--self-check"]
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    ensure_workspace_dirs()
    init_db()

    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    from photoai.ui.main_window import MainWindow

    app = QApplication(argv)
    app.setApplicationName("Photo AI Desktop")
    window = MainWindow()
    window.show()

    recipes = load_all()
    print(
        f"Photo AI Desktop ready — device={device()} recipes={len(recipes)} tools={window.tools.count()}",
        flush=True,
    )

    if self_check:
        QTimer.singleShot(600, app.quit)  # boot, pump the event loop, exit cleanly
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
