#!/usr/bin/env python3
"""
ClipVault - Windows-style Clipboard Manager for Ubuntu
Keyboard shortcut: Super+V (Win+V equivalent)
"""

import sys
import os

# Allow running from the project root: python app/main.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from app.core.history_manager import HistoryManager
from app.ui.main_window import ClipVaultWindow
from app.ui.tray_icon import TrayIcon


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ClipVault")
    app.setQuitOnLastWindowClosed(False)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    history = HistoryManager()
    window  = ClipVaultWindow(history)
    tray    = TrayIcon(window, app)   # noqa: F841 — kept alive by reference

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
