import base64
import logging
import time
from io import BytesIO

from PyQt5.QtCore import QObject, QTimer, pyqtSignal, Qt
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import QApplication

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

log = logging.getLogger(__name__)


class ClipboardWatcher(QObject):
    """Polls the clipboard from the GUI thread.

    QClipboard / QImage are Qt GUI objects and must only be used from the
    thread that owns the GUI.  The previous implementation polled them from a
    QThread, which is undefined behaviour on X11 and a plausible source of the
    intermittent "double free or corruption" aborts.

    Text is polled every POLL_MS (cheap, ~0.3 ms).  Reading an image is
    expensive (a full X11 transfer + decode, ~180 ms for 2560x1440), so an
    image that is already in the clipboard is only re-read every
    IMAGE_RECHECK_MS seconds; a cheap 16x16 fingerprint decides whether the
    expensive PNG encoding is needed at all.
    """

    new_text  = pyqtSignal(str)
    new_image = pyqtSignal(str)   # base64-encoded PNG

    POLL_MS = 500
    IMAGE_RECHECK_MS = 5000

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_text    = ""
        self._last_img     = ""
        self._last_img_sig = None
        self._last_formats = ()
        self._last_image_at = 0.0
        self._running  = False
        self._failures = 0
        self._clipboard = None
        self._timer = QTimer(self)
        self._timer.setInterval(self.POLL_MS)
        self._timer.timeout.connect(self.poll)

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def start(self):
        app = QApplication.instance()
        if app is None:
            log.error("no QApplication instance, clipboard watcher will not start")
            return
        self._clipboard = app.clipboard()
        self._running = True
        self._timer.start()
        self.poll()          # capture whatever is already on the clipboard
        log.info("clipboard watcher started in GUI thread (poll=%dms, image recheck=%dms, PIL=%s)",
                 self.POLL_MS, self.IMAGE_RECHECK_MS, PIL_AVAILABLE)

    def stop(self):
        if self._running:
            self._running = False
            self._timer.stop()
            log.info("clipboard watcher stopped")

    # ── polling ───────────────────────────────────────────────────────────────

    def poll(self):
        if not self._running or self._clipboard is None:
            return
        try:
            mime = self._clipboard.mimeData()
            if mime is None:
                return
            formats = tuple(mime.formats())
            if mime.hasImage() and PIL_AVAILABLE:
                now = time.monotonic()
                if (formats != self._last_formats
                        or now - self._last_image_at >= self.IMAGE_RECHECK_MS / 1000.0):
                    self._last_image_at = now
                    self._read_image(self._clipboard.image())
            elif mime.hasText():
                self._read_text(mime)
            self._last_formats = formats
            self._failures = 0
        except Exception:
            self._failures += 1
            if self._failures <= 20 or self._failures % 100 == 0:
                log.exception("clipboard poll failed (consecutive failures: %d)", self._failures)

    def _read_text(self, mime):
        text = mime.text()
        if text and text != self._last_text:
            self._last_text = text
            log.info("new text captured (%d chars)", len(text))
            self.new_text.emit(text)

    def _read_image(self, img):
        if img is None or img.isNull():
            return
        # Cheap fingerprint first: hashing a 16x16 downscale is ~1 ms, while
        # PNG-encoding the full image can take tens of milliseconds.
        small = img.scaled(16, 16, Qt.IgnoreAspectRatio, Qt.FastTransformation)
        ba = small.constBits()
        ba.setsize(small.sizeInBytes())
        sig = (img.width(), img.height(), hash(bytes(ba)))
        if sig == self._last_img_sig:
            return

        img = img.convertToFormat(QImage.Format_RGBA8888)
        buf = BytesIO()
        raw = img.constBits()
        raw.setsize(img.sizeInBytes())
        pil = Image.frombytes("RGBA", (img.width(), img.height()), bytes(raw))
        pil.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        self._last_img_sig = sig
        if b64 != self._last_img:
            self._last_img = b64
            log.info("new image captured (%dx%d, %d bytes base64)",
                     img.width(), img.height(), len(b64))
            self.new_image.emit(b64)
