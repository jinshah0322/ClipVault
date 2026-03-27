from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import QAction, QApplication, QMenu, QSystemTrayIcon

from app.shared.constants import C_ACCENT


class TrayIcon(QSystemTrayIcon):
    def __init__(self, window, app: QApplication):
        super().__init__(app)
        self.window = window

        self.setIcon(self._make_icon())
        self.setToolTip("ClipVault — Clipboard Manager")

        menu = QMenu()

        show_act = QAction("Show / Hide  (Super+V)", menu)
        show_act.triggered.connect(self._toggle)

        clear_act = QAction("Clear History", menu)
        clear_act.triggered.connect(
            lambda: (window.history.clear_unpinned(), window._refresh_list())
        )

        quit_act = QAction("Quit ClipVault", menu)
        quit_act.triggered.connect(app.quit)

        menu.addAction(show_act)
        menu.addSeparator()
        menu.addAction(clear_act)
        menu.addSeparator()
        menu.addAction(quit_act)
        self.setContextMenu(menu)

        self.activated.connect(self._on_activated)
        self.show()

    def _make_icon(self):
        pix = QPixmap(32, 32)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QBrush(QColor(C_ACCENT)))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(2, 2, 28, 28, 6, 6)
        p.setPen(QPen(Qt.white, 2))
        p.setFont(QFont("Arial", 14, QFont.Bold))
        p.drawText(pix.rect(), Qt.AlignCenter, "C")
        p.end()
        return QIcon(pix)

    def _toggle(self):
        if self.window.isVisible():
            self.window.hide()
        else:
            self.window._position_window()
            self.window.show()
            self.window.raise_()
            self.window.activateWindow()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self._toggle()
