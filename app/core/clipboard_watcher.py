import base64
import time
from io import BytesIO

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class ClipboardWatcher(QThread):
    new_text  = pyqtSignal(str)
    new_image = pyqtSignal(str)   # base64-encoded PNG

    def __init__(self):
        super().__init__()
        self._last_text = ""
        self._last_img  = ""
        self._running   = True

    def run(self):
        app = QApplication.instance()
        while self._running:
            try:
                cb   = app.clipboard()
                mime = cb.mimeData()

                if mime.hasImage() and PIL_AVAILABLE:
                    img = cb.image()
                    if not img.isNull():
                        buf = BytesIO()
                        ba  = img.bits()
                        ba.setsize(img.byteCount())
                        pil = Image.frombytes("RGBA", (img.width(), img.height()), bytes(ba))
                        pil.save(buf, format="PNG")
                        b64 = base64.b64encode(buf.getvalue()).decode()
                        if b64 != self._last_img:
                            self._last_img = b64
                            self.new_image.emit(b64)

                elif mime.hasText():
                    text = mime.text()
                    if text and text != self._last_text:
                        self._last_text = text
                        self.new_text.emit(text)

            except Exception:
                pass

            time.sleep(0.5)

    def stop(self):
        self._running = False
