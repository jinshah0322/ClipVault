import threading
from typing import Callable

try:
    from pynput import keyboard as pynput_keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False


def start_global_hotkey(on_activate: Callable[[], None]) -> None:
    """Spawn a daemon thread that listens for Super+V and calls on_activate."""
    if not PYNPUT_AVAILABLE:
        return

    def listen():
        kb = pynput_keyboard

        hotkey = kb.HotKey(kb.HotKey.parse("<cmd>+v"), on_activate)

        def on_press(key):
            try:
                hotkey.press(kb.Listener.canonical(listener, key))
            except Exception:
                pass

        def on_release(key):
            try:
                hotkey.release(kb.Listener.canonical(listener, key))
            except Exception:
                pass

        with kb.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()

    t = threading.Thread(target=listen, daemon=True)
    t.start()
