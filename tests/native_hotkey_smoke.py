"""Run explicitly on Windows, outside restricted desktops/sandboxes.

Runs the tray controller and posts WM_HOTKEY to this process only. It never
copies user text or sends keys to another application.
"""

import ctypes
import os
import sys
from ctypes import wintypes as w
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from main import TrayApplication
from windows_api import HOTKEY_ID, WM_HOTKEY


def main():
    app = QApplication([])
    controller = TrayApplication()
    if not controller.is_enabled:
        raise RuntimeError(controller.last_status)
    received = []
    controller.converter.start = lambda: received.append("converted")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetCurrentThreadId.restype = w.DWORD
    thread = kernel.GetCurrentThreadId()
    api = ctypes.WinDLL("user32", use_last_error=True)
    api.PostThreadMessageW.argtypes = [w.DWORD, w.UINT, w.WPARAM, w.LPARAM]
    api.PostThreadMessageW.restype = w.BOOL
    errors = []

    def check():
        try:
            assert received == ["converted"], received
            assert not any(widget.isVisible() for widget in app.topLevelWidgets())
            assert [action.text() for action in controller.menu.actions()
                    if not action.isSeparator()] == ["فعال", "اجرا هنگام ورود به ویندوز", "خروج"]
            controller.toggle_action.trigger()
            assert not controller.is_enabled and not controller.native.registered
            assert not controller.toggle_action.isChecked()
            controller.start_conversion()
            assert received == ["converted"], received
            controller.toggle_action.trigger()
            assert controller.is_enabled and controller.native.registered
            assert controller.toggle_action.isChecked()
        except Exception as error:
            errors.append(error)
            app.quit()
        else:
            controller.menu.actions()[-1].trigger()

    def timed_out():
        errors.append(TimeoutError("The tray Exit action did not stop the application"))
        app.quit()

    if not api.PostThreadMessageW(thread, WM_HOTKEY, HOTKEY_ID, 0):
        controller.cleanup()
        raise ctypes.WinError(ctypes.get_last_error())
    QTimer.singleShot(250, check)
    QTimer.singleShot(2000, timed_out)
    app.exec()
    assert controller.quitting
    assert not controller.native.registered
    if errors:
        raise errors[0]
    print("Tray-only startup, native hotkey, menu toggle, and cleanup passed")


if __name__ == "__main__":
    main()
