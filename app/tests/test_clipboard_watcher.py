from unittest.mock import MagicMock, patch

import pytest

from app.core.clipboard_watcher import ClipboardWatcher


class TestClipboardWatcherInit:
    def test_initial_state(self):
        watcher = ClipboardWatcher()
        assert watcher._running is True
        assert watcher._last_text == ""
        assert watcher._last_img == ""

    def test_stop_sets_running_false(self):
        watcher = ClipboardWatcher()
        watcher.stop()
        assert watcher._running is False


class TestClipboardWatcherRun:
    def _make_watcher(self):
        watcher = ClipboardWatcher()
        watcher.new_text  = MagicMock()
        watcher.new_image = MagicMock()
        return watcher

    def _run_one_tick(self, watcher, mime):
        """Simulate one poll loop iteration then stop."""
        mock_cb = MagicMock()
        mock_cb.mimeData.return_value = mime

        mock_app = MagicMock()
        mock_app.clipboard.return_value = mock_cb

        # Stop after first iteration so the loop exits
        original_sleep = __import__("time").sleep

        call_count = [0]

        def fake_sleep(_):
            call_count[0] += 1
            watcher._running = False  # stop after first tick

        with patch("app.core.clipboard_watcher.QApplication") as mock_qapp, \
             patch("app.core.clipboard_watcher.time.sleep", side_effect=fake_sleep):
            mock_qapp.instance.return_value = mock_app
            watcher.run()

    def test_new_text_emitted_on_change(self):
        watcher = self._make_watcher()

        mime = MagicMock()
        mime.hasImage.return_value = False
        mime.hasText.return_value  = True
        mime.text.return_value     = "new text"

        self._run_one_tick(watcher, mime)
        watcher.new_text.emit.assert_called_once_with("new text")

    def test_same_text_not_emitted_twice(self):
        watcher = self._make_watcher()
        watcher._last_text = "same"

        mime = MagicMock()
        mime.hasImage.return_value = False
        mime.hasText.return_value  = True
        mime.text.return_value     = "same"

        self._run_one_tick(watcher, mime)
        watcher.new_text.emit.assert_not_called()

    def test_empty_text_not_emitted(self):
        watcher = self._make_watcher()

        mime = MagicMock()
        mime.hasImage.return_value = False
        mime.hasText.return_value  = True
        mime.text.return_value     = ""

        self._run_one_tick(watcher, mime)
        watcher.new_text.emit.assert_not_called()

    def test_exception_during_poll_is_swallowed(self):
        watcher = self._make_watcher()

        mock_app = MagicMock()
        mock_app.clipboard.side_effect = RuntimeError("clipboard error")

        def fake_sleep(_):
            watcher._running = False

        with patch("app.core.clipboard_watcher.QApplication") as mock_qapp, \
             patch("app.core.clipboard_watcher.time.sleep", side_effect=fake_sleep):
            mock_qapp.instance.return_value = mock_app
            watcher.run()   # should not raise

        watcher.new_text.emit.assert_not_called()
