from unittest.mock import MagicMock, patch

import pytest

from app.core.clipboard_watcher import ClipboardWatcher


class TestClipboardWatcherInit:
    def test_initial_state(self):
        watcher = ClipboardWatcher()
        assert watcher._running is False
        assert watcher._last_text == ""
        assert watcher._last_img == ""

    def test_stop_before_start_is_safe(self):
        watcher = ClipboardWatcher()
        watcher.stop()                      # must not raise
        assert watcher._running is False


class TestClipboardWatcherPoll:
    def _make_watcher(self):
        watcher = ClipboardWatcher()
        watcher.new_text = MagicMock()
        watcher.new_image = MagicMock()
        watcher._clipboard = MagicMock()
        watcher._running = True
        return watcher

    @staticmethod
    def _mime(text=None, image=False, formats=("text/plain",)):
        mime = MagicMock()
        mime.hasImage.return_value = image
        mime.hasText.return_value = text is not None
        mime.text.return_value = text if text is not None else ""
        mime.formats.return_value = list(formats)
        return mime

    def test_new_text_emitted_on_change(self):
        watcher = self._make_watcher()
        watcher._clipboard.mimeData.return_value = self._mime("new text")
        watcher.poll()
        watcher.new_text.emit.assert_called_once_with("new text")

    def test_same_text_not_emitted_twice(self):
        watcher = self._make_watcher()
        watcher._last_text = "same"
        watcher._clipboard.mimeData.return_value = self._mime("same")
        watcher.poll()
        watcher.new_text.emit.assert_not_called()

    def test_empty_text_not_emitted(self):
        watcher = self._make_watcher()
        watcher._clipboard.mimeData.return_value = self._mime("")
        watcher.poll()
        watcher.new_text.emit.assert_not_called()

    def test_poll_does_nothing_when_stopped(self):
        watcher = ClipboardWatcher()
        watcher._clipboard = MagicMock()
        watcher.poll()
        watcher._clipboard.mimeData.assert_not_called()

    def test_exception_during_poll_is_swallowed(self):
        watcher = self._make_watcher()
        watcher._clipboard.mimeData.side_effect = RuntimeError("clipboard error")
        watcher.poll()                      # must not raise
        watcher.new_text.emit.assert_not_called()

    @patch("app.core.clipboard_watcher.PIL_AVAILABLE", True)
    def test_image_is_read_when_formats_change(self):
        watcher = self._make_watcher()
        watcher._read_image = MagicMock()
        watcher._clipboard.mimeData.return_value = self._mime(
            image=True, formats=("image/png",)
        )
        watcher.poll()
        watcher._read_image.assert_called_once()

    @patch("app.core.clipboard_watcher.PIL_AVAILABLE", True)
    def test_image_not_reread_on_every_poll(self):
        import time

        watcher = self._make_watcher()
        watcher._read_image = MagicMock()
        watcher._last_formats = ("image/png",)
        watcher._last_image_at = time.monotonic()
        watcher._clipboard.mimeData.return_value = self._mime(
            image=True, formats=("image/png",)
        )
        watcher.poll()
        watcher._read_image.assert_not_called()
