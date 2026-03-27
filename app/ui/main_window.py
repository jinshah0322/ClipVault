import base64
import subprocess
import sys

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QFrame, QGraphicsDropShadowEffect,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QVBoxLayout, QWidget,
)

from app.core.clipboard_watcher import ClipboardWatcher
from app.core.history_manager import HistoryManager
from app.models.clip_item import ClipItem
from app.shared.constants import (
    C_ACCENT, C_BG, C_BORDER, C_CLOSE,
    C_SEARCH_BG, C_SURFACE, C_TEXT, C_TEXT_DIM,
)
from app.ui.widgets.clip_item_widget import ClipItemWidget
from app.workers.hotkey_listener import PYNPUT_AVAILABLE, start_global_hotkey

try:
    from pynput.keyboard import Controller, Key
except ImportError:
    Controller = None
    Key = None


class ClipVaultWindow(QWidget):
    def __init__(self, history: HistoryManager):
        super().__init__()
        self.history       = history
        self._search_query = ""

        self._init_window()
        self._build_ui()
        self._start_watcher()
        self._start_hotkey()
        self._refresh_list()

    # ── Window setup ──────────────────────────────────────────────────────────

    def _init_window(self):
        self.setWindowTitle("ClipVault")
        self.setWindowFlags(
            Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(380)
        self.setMinimumHeight(200)
        self.setMaximumHeight(600)
        self._position_window()

    def _position_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 20, screen.bottom() - 620)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(0)

        self.card = QFrame()
        self.card.setObjectName("card")
        self.card.setStyleSheet(f"""
            #card {{
                background: {C_BG};
                border-radius: 12px;
                border: 1px solid {C_BORDER};
            }}
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(10)

        card_layout.addLayout(self._build_header())
        card_layout.addWidget(self._build_search_bar())
        card_layout.addLayout(self._build_tabs())
        card_layout.addWidget(self._build_scroll_area())

        self.empty_label = QLabel(
            "No clipboard history yet.\nCopy something to get started!"
        )
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet(
            f"color: {C_TEXT_DIM}; font-size: 12px; background: transparent;"
        )
        self.empty_label.hide()
        card_layout.addWidget(self.empty_label)

        footer = QLabel("Press  Super+V  to toggle  •  Click item to paste")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet(
            f"color: {C_TEXT_DIM}; font-size: 9px; background: transparent;"
        )
        card_layout.addWidget(footer)

        outer.addWidget(self.card)

    def _build_header(self):
        _bold = lambda size: (
            QFont("Segoe UI Semibold", size, QFont.Bold)
            if sys.platform == "win32"
            else QFont("Ubuntu Bold", size, QFont.Bold)
        )
        _regular = lambda size: (
            QFont("Segoe UI", size) if sys.platform == "win32" else QFont("Ubuntu", size)
        )

        header = QHBoxLayout()
        header.setSpacing(8)

        title_row = QVBoxLayout()
        title = QLabel("Clipboard")
        title.setFont(_bold(14 if sys.platform == "win32" else 13))
        title.setStyleSheet(f"color: {C_TEXT}; background: transparent;")

        sub = QLabel("History")
        sub.setFont(_regular(9))
        sub.setStyleSheet(f"color: {C_TEXT_DIM}; background: transparent;")

        title_row.addWidget(title)
        title_row.addWidget(sub)
        header.addLayout(title_row)
        header.addStretch()

        self.clear_btn = QPushButton("Clear all")
        self.clear_btn.setFixedHeight(28)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {C_ACCENT};
                border: 1px solid {C_ACCENT};
                border-radius: 6px;
                padding: 0 10px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {C_ACCENT};
                color: white;
            }}
        """)
        self.clear_btn.clicked.connect(self._clear_all)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {C_TEXT_DIM};
                border: none;
                border-radius: 6px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {C_CLOSE};
                color: white;
            }}
        """)
        close_btn.clicked.connect(self.hide)

        header.addWidget(self.clear_btn)
        header.addWidget(close_btn)
        return header

    def _build_search_bar(self):
        search_frame = QFrame()
        search_frame.setStyleSheet(f"""
            QFrame {{
                background: {C_SEARCH_BG};
                border-radius: 8px;
                border: 1px solid {C_BORDER};
            }}
        """)
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(10, 0, 10, 0)
        search_layout.setSpacing(6)

        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("background: transparent; border: none;")

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search clipboard…")
        self.search_box.setFrame(False)
        self.search_box.setFixedHeight(36)
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                background: transparent;
                color: {C_TEXT};
                border: none;
                font-size: 12px;
            }}
            QLineEdit::placeholder {{
                color: {C_TEXT_DIM};
            }}
        """)
        self.search_box.textChanged.connect(self._on_search)

        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.search_box)
        return search_frame

    def _build_tabs(self):
        tabs_layout = QHBoxLayout()
        tabs_layout.setSpacing(4)
        self._tab_btns  = []
        self._active_tab = "All"

        for label in ("All", "Pinned", "Text", "Images"):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(26)
            btn.setStyleSheet(self._tab_style(False))
            btn.clicked.connect(lambda _, l=label, b=btn: self._on_tab(l, b))
            tabs_layout.addWidget(btn)
            self._tab_btns.append(btn)

        self._tab_btns[0].setChecked(True)
        self._tab_btns[0].setStyleSheet(self._tab_style(True))
        return tabs_layout

    def _build_scroll_area(self):
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{
                background: {C_SURFACE};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {C_BORDER};
                border-radius: 3px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(4)
        self.list_layout.addStretch()

        self.scroll.setWidget(self.list_container)
        return self.scroll

    def _tab_style(self, active):
        if active:
            return f"""
                QPushButton {{
                    background: {C_ACCENT};
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 0 10px;
                    font-size: 11px;
                }}
            """
        return f"""
            QPushButton {{
                background: transparent;
                color: {C_TEXT_DIM};
                border: 1px solid {C_BORDER};
                border-radius: 5px;
                padding: 0 10px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: #424242;
                color: {C_TEXT};
            }}
        """

    # ── List management ───────────────────────────────────────────────────────

    def _on_tab(self, label, clicked_btn):
        self._active_tab = label
        for b in self._tab_btns:
            b.setChecked(False)
            b.setStyleSheet(self._tab_style(False))
        clicked_btn.setChecked(True)
        clicked_btn.setStyleSheet(self._tab_style(True))
        self._refresh_list()

    def _on_search(self, text):
        self._search_query = text
        self._refresh_list()

    def _refresh_list(self):
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        items = self.history.items

        if self._active_tab == "Pinned":
            items = [i for i in items if i.pinned]
        elif self._active_tab == "Text":
            items = [i for i in items if i.kind == "text"]
        elif self._active_tab == "Images":
            items = [i for i in items if i.kind == "image"]

        if self._search_query:
            q     = self._search_query.lower()
            items = [i for i in items if q in i.preview_text().lower()]

        if not items:
            self.empty_label.show()
            self.scroll.hide()
        else:
            self.empty_label.hide()
            self.scroll.show()
            for item in items:
                w = ClipItemWidget(item)
                w.paste_requested.connect(self._paste_item)
                w.pin_toggled.connect(self._toggle_pin)
                w.delete_requested.connect(self._delete_item)
                self.list_layout.insertWidget(self.list_layout.count() - 1, w)

        target_h = min(600, max(200, 200 + len(items) * 82))
        self.setFixedHeight(target_h + 16)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _paste_item(self, item: ClipItem):
        cb = QApplication.clipboard()
        if item.kind == "image":
            raw = base64.b64decode(item.content)
            pix = QPixmap()
            pix.loadFromData(raw)
            cb.setPixmap(pix)
        else:
            cb.setText(item.content)
        self.hide()
        QTimer.singleShot(200, self._simulate_paste)

    def _simulate_paste(self):
        try:
            if PYNPUT_AVAILABLE and Controller is not None:
                kb = Controller()
                kb.press(Key.ctrl)
                kb.press("v")
                kb.release("v")
                kb.release(Key.ctrl)
            else:
                subprocess.run(["xdotool", "key", "ctrl+v"], check=False)
        except Exception:
            pass

    def _toggle_pin(self, item: ClipItem):
        self.history.toggle_pin(item)
        self._refresh_list()

    def _delete_item(self, item: ClipItem):
        self.history.remove(item)
        self._refresh_list()

    def _clear_all(self):
        self.history.clear_unpinned()
        self._refresh_list()

    # ── Clipboard watcher ─────────────────────────────────────────────────────

    def _start_watcher(self):
        self._watcher = ClipboardWatcher()
        self._watcher.new_text.connect(self._on_new_text)
        self._watcher.new_image.connect(self._on_new_image)
        self._watcher.start()

    def _on_new_text(self, text):
        if self.history.add(text, "text"):
            self._refresh_list()

    def _on_new_image(self, b64):
        if self.history.add(b64, "image"):
            self._refresh_list()

    # ── Global hotkey ─────────────────────────────────────────────────────────

    def _start_hotkey(self):
        def on_activate():
            if self.isVisible():
                self.hide()
            else:
                self._position_window()
                self.show()
                self.raise_()
                self.activateWindow()
                self.search_box.setFocus()

        start_global_hotkey(on_activate)

    # ── Qt event overrides ────────────────────────────────────────────────────

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.hide()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.LeftButton and hasattr(self, "_drag_pos"):
            self.move(e.globalPos() - self._drag_pos)
