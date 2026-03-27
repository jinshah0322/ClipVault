import threading
from unittest.mock import MagicMock, patch

import app.workers.hotkey_listener as hl_module
from app.workers.hotkey_listener import start_global_hotkey


class TestStartGlobalHotkey:
    def test_no_op_when_pynput_unavailable(self):
        """Should return silently without spawning a thread."""
        with patch.object(hl_module, "PYNPUT_AVAILABLE", False):
            before = threading.active_count()
            start_global_hotkey(lambda: None)
            after = threading.active_count()
            assert after == before

    def test_spawns_daemon_thread_when_pynput_available(self):
        """Should start a daemon thread via threading.Thread."""
        mock_kb = MagicMock()
        mock_thread = MagicMock()

        with patch.object(hl_module, "PYNPUT_AVAILABLE", True), \
             patch("app.workers.hotkey_listener.pynput_keyboard", mock_kb), \
             patch("app.workers.hotkey_listener.threading.Thread", return_value=mock_thread) as mock_thread_cls:
            start_global_hotkey(lambda: None)

        mock_thread_cls.assert_called_once()
        _, kwargs = mock_thread_cls.call_args
        assert kwargs.get("daemon") is True
        mock_thread.start.assert_called_once()

    def test_on_activate_callback_is_wired(self):
        """on_activate must be passed to HotKey."""
        callback = MagicMock()

        captured_callback = []

        original_HotKey = MagicMock(side_effect=lambda keys, cb: captured_callback.append(cb) or MagicMock())

        mock_kb = MagicMock()
        mock_kb.HotKey.side_effect = original_HotKey
        mock_kb.HotKey.parse.return_value = "<cmd>+v"

        mock_listener_cls = MagicMock()
        mock_listener_cls.return_value.__enter__ = MagicMock(return_value=MagicMock(join=MagicMock()))
        mock_listener_cls.return_value.__exit__  = MagicMock(return_value=False)
        mock_kb.Listener = mock_listener_cls

        with patch.object(hl_module, "PYNPUT_AVAILABLE", True), \
             patch("app.workers.hotkey_listener.pynput_keyboard", mock_kb):
            start_global_hotkey(callback)
            import time; time.sleep(0.05)

        # The callback we passed should be the one wired into HotKey
        assert len(captured_callback) == 1
        assert captured_callback[0] is callback
