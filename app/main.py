#!/usr/bin/env python3
"""
ClipVault - Windows-style Clipboard Manager for Ubuntu
Keyboard shortcut: Super+V (Win+V equivalent)
"""

import sys
import os
import argparse
import signal
import atexit

# Allow running from the project root: python app/main.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import __version__
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from app.core.history_manager import HistoryManager
from app.ui.main_window import ClipVaultWindow
from app.ui.tray_icon import TrayIcon
from app.shared.constants import PID_FILE


def _parse_args():
    parser = argparse.ArgumentParser(
        prog="clipvault",
        description="Windows-style clipboard manager for Ubuntu",
    )
    parser.add_argument(
        "--version", action="version", version=f"ClipVault {__version__}"
    )
    return parser.parse_args()


def _write_pid():
    os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))
    atexit.register(lambda: os.path.exists(PID_FILE) and os.remove(PID_FILE))


def main():
    _parse_args()
    _write_pid()

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setApplicationName("ClipVault")
    app.setQuitOnLastWindowClosed(False)

    history = HistoryManager()
    window  = ClipVaultWindow(history)
    tray    = TrayIcon(window, app)   # noqa: F841 — kept alive by reference

    # SIGUSR1 → toggle window (sent by the GNOME custom keybinding toggle script)
    signal.signal(signal.SIGUSR1, lambda *_: window._hotkey_activated.emit())

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
