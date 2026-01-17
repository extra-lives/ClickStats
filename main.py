import json
import os
import sys
import threading
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageDraw
import pystray
from pynput import mouse

_BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(__file__)
DATA_PATH = os.path.join(_BASE_DIR, "clicks.json")

_lock = threading.Lock()
_dirty = False
_left_count = 0
_right_count = 0
_stop_event = threading.Event()
_icon = None
_listener = None
_tk_root = None
_start_time = None


def _load_count():
    global _left_count, _right_count, _start_time
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            _left_count = int(data.get("left", 0))
            _right_count = int(data.get("right", 0))
            start_raw = data.get("start")
            if isinstance(start_raw, str):
                try:
                    _start_time = datetime.fromisoformat(start_raw)
                except ValueError:
                    _start_time = None
    except FileNotFoundError:
        _left_count = 0
        _right_count = 0
        _start_time = None
    except (ValueError, json.JSONDecodeError):
        _left_count = 0
        _right_count = 0
        _start_time = None


def _save_count():
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "left": _left_count,
                "right": _right_count,
                "start": _start_time.isoformat() if _start_time else None,
            },
            f,
        )


def _saver_loop():
    global _dirty
    while not _stop_event.wait(2.0):
        with _lock:
            if _dirty:
                _save_count()
                _dirty = False


def _update_icon_text():
    # Tooltip text for the tray icon.
    since_text = _start_time.strftime("%m/%d @ %H:%M") if _start_time else "unknown"
    _icon.title = (
        f"Click Stats: {_left_count} Left & {_right_count} Right since {since_text}"
    )


def _on_click(x, y, button, pressed):
    if not pressed:
        return
    if button not in (mouse.Button.left, mouse.Button.right):
        return
    global _left_count, _right_count, _dirty
    with _lock:
        if button == mouse.Button.left:
            _left_count += 1
        elif button == mouse.Button.right:
            _right_count += 1
        _dirty = True
        _update_icon_text()
        _icon.update_menu()


def _confirm_reset():
    if _tk_root is None:
        return False
    result_event = threading.Event()
    result = {"ok": False}

    def _show_dialog():
        _tk_root.attributes("-topmost", True)
        result["ok"] = messagebox.askokcancel(
            "Reset Click Counter",
            "Reset left and right click counts to zero?",
            parent=_tk_root,
        )
        result_event.set()

    _tk_root.after(0, _show_dialog)
    result_event.wait()
    return result["ok"]


def _on_reset(icon, item):
    global _left_count, _right_count, _dirty
    if not _confirm_reset():
        return
    with _lock:
        _left_count = 0
        _right_count = 0
        _dirty = True
        _update_icon_text()
        icon.update_menu()


def _on_quit(icon, item):
    _stop_event.set()
    if _listener is not None:
        _listener.stop()
    with _lock:
        _save_count()
    icon.stop()
    if _tk_root is not None:
        _tk_root.after(0, _tk_root.quit)


def _create_image():
    # Simple circular icon.
    size = 64
    image = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, size - 8, size - 8), fill="black")
    return image


def _build_menu():
    return pystray.Menu(
        pystray.MenuItem(
            lambda item: f"Left Clicks: {_left_count} / Right Clicks: {_right_count}",
            None,
            enabled=False,
        ),
        pystray.MenuItem("Reset", _on_reset),
        pystray.MenuItem("Quit", _on_quit),
    )


def main():
    global _icon, _listener, _tk_root, _start_time, _dirty
    _load_count()
    if _start_time is None:
        _start_time = datetime.now()
        with _lock:
            _dirty = True
    _tk_root = tk.Tk()
    _tk_root.withdraw()
    _icon = pystray.Icon(
        "click_counter",
        _create_image(),
        "Right Clicks: 0 / Left Clicks: 0",
        _build_menu(),
    )
    _update_icon_text()

    _listener = mouse.Listener(on_click=_on_click)
    _listener.start()

    saver_thread = threading.Thread(target=_saver_loop, daemon=True)
    saver_thread.start()

    _icon.run_detached()
    _tk_root.mainloop()


if __name__ == "__main__":
    main()
