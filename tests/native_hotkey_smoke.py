"""Run explicitly on Windows, outside restricted desktops/sandboxes.

Uses a hidden Qt window and posts WM_HOTKEY to this process only. It never
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

from main import MainWindow
from windows_api import HOTKEY_ID, WM_HOTKEY


def main():
    app = QApplication([])
    window = MainWindow()
    if not window.is_enabled:
        raise RuntimeError(window.status_label.text())
    received = []
    window.converter.start = lambda: received.append("converted")
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
            window.set_enabled(False)
            assert not window.is_enabled and not window.native.registered
            window.start_conversion()
            assert received == ["converted"], received
            window.set_enabled(True)
            assert window.is_enabled and window.native.registered
        except Exception as error:
            errors.append(error)
        finally:
            app.quit()

    if not api.PostThreadMessageW(thread, WM_HOTKEY, HOTKEY_ID, 0):
        window.cleanup()
        raise ctypes.WinError(ctypes.get_last_error())
    QTimer.singleShot(250, check)
    app.exec()
    assert not window.native.registered
    if errors:
        raise errors[0]
    print("Native WM_HOTKEY dispatch, disable, enable, and cleanup passed")


if __name__ == "__main__":
    main()
