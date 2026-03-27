import base64
import sys

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from app.models.clip_item import ClipItem
from app.shared.constants import (
    C_BORDER, C_ITEM, C_ITEM_HOV, C_ITEM_SEL,
    C_PIN, C_SURFACE, C_TEXT, C_TEXT_DIM,
)


class ClipItemWidget(QFrame):
    paste_requested  = pyqtSignal(object)
    pin_toggled      = pyqtSignal(object)
    delete_requested = pyqtSignal(object)

    def __init__(self, item: ClipItem, parent=None):
        super().__init__(parent)
        self.item     = item
        self._hovered = False
        self.setFixedHeight(76)
        self.setCursor(Qt.PointingHandCursor)
        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 8, 8)
        layout.setSpacing(10)

        self.thumb = QLabel()
        self.thumb.setFixedSize(50, 58)
        self.thumb.setAlignment(Qt.AlignCenter)
        self._set_thumbnail()
        layout.addWidget(self.thumb)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.setContentsMargins(0, 0, 0, 0)

        _font = lambda size: (
            QFont("Segoe UI", size) if sys.platform == "win32" else QFont("Ubuntu", size)
        )

        self.preview = QLabel(self.item.preview_text())
        self.preview.setWordWrap(True)
        self.preview.setMaximumHeight(38)
        self.preview.setFont(_font(9))
        self.preview.setStyleSheet(f"color: {C_TEXT}; background: transparent;")

        self.time_lbl = QLabel(self.item.time_label())
        self.time_lbl.setFont(_font(8))
        self.time_lbl.setStyleSheet(f"color: {C_TEXT_DIM}; background: transparent;")

        text_col.addWidget(self.preview)
        text_col.addWidget(self.time_lbl)
        layout.addLayout(text_col, 1)

        btn_col = QVBoxLayout()
        btn_col.setSpacing(4)
        btn_col.setContentsMargins(0, 0, 0, 0)

        self.pin_btn = self._make_icon_btn("📌" if not self.item.pinned else "📍", C_PIN)
        self.pin_btn.setToolTip("Pin / Unpin")
        self.pin_btn.clicked.connect(lambda: self.pin_toggled.emit(self.item))

        self.del_btn = self._make_icon_btn("✕", C_TEXT_DIM)
        self.del_btn.setToolTip("Delete")
        self.del_btn.clicked.connect(lambda: self.delete_requested.emit(self.item))

        btn_col.addWidget(self.pin_btn)
        btn_col.addWidget(self.del_btn)
        layout.addLayout(btn_col)

        self._update_btn_visibility(False)

    def _make_icon_btn(self, icon, color):
        btn = QPushButton(icon)
        btn.setFixedSize(24, 24)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {color};
                border: none;
                font-size: 12px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,0.12);
            }}
        """)
        return btn

    def _set_thumbnail(self):
        if self.item.kind == "image":
            try:
                raw = base64.b64decode(self.item.content)
                pix = QPixmap()
                pix.loadFromData(raw)
                self.thumb.setPixmap(
                    pix.scaled(50, 58, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                return
            except Exception:
                pass

        self.thumb.setStyleSheet(f"""
            background: {C_SURFACE};
            border: 1px solid {C_BORDER};
            border-radius: 4px;
            color: {C_TEXT_DIM};
            font-size: 8px;
            padding: 2px;
        """)
        preview = self.item.content.strip()[:80] if self.item.kind == "text" else "IMG"
        self.thumb.setText(preview[:40])
        self.thumb.setWordWrap(True)
        self.thumb.setAlignment(Qt.AlignTop | Qt.AlignLeft)

    def _apply_style(self, hover=False, selected=False):
        bg = C_ITEM_SEL if selected else (C_ITEM_HOV if hover else C_ITEM)
        border_color = "#0078d4" if selected else C_BORDER
        style = f"""
            ClipItemWidget {{
                background: {bg};
                border-radius: 8px;
                border: 1px solid {border_color};
            }}
        """
        if self.item.pinned:
            style += f"""
                ClipItemWidget {{
                    border-left: 3px solid {C_PIN};
                }}
            """
        self.setStyleSheet(style)

    def _update_btn_visibility(self, visible):
        self.pin_btn.setVisible(visible)
        self.del_btn.setVisible(visible)

    def enterEvent(self, e):
        self._hovered = True
        self._apply_style(hover=True)
        self._update_btn_visibility(True)

    def leaveEvent(self, e):
        self._hovered = False
        self._apply_style()
        self._update_btn_visibility(False)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.paste_requested.emit(self.item)
