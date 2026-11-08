"""Run explicitly on Windows, outside restricted desktops/sandboxes.

Runs the tray controller and posts WM_HOTKEY to this process only. It never
copies user text or sends keys to another application.
"""

import ctypes
import os
import sys
from ctypes import wintypes as w
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QSettings, QTimer
from PySide6.QtWidgets import QApplication

from main import TrayApplication
from shortcut import Shortcut
from windows_api import HOTKEY_ID, WM_HOTKEY


def main():
    app = QApplication([])
    with TemporaryDirectory() as directory:
        TrayApplication.shortcut_settings = staticmethod(
            lambda: QSettings(str(Path(directory) / "settings.ini"), QSettings.Format.IniFormat)
        )
        custom = Shortcut("J", frozenset({"Ctrl", "Alt", "Shift"}))
        settings = TrayApplication.shortcut_settings()
        settings.setValue("shortcut", str(custom))
        settings.sync()
        exercise(app, custom)


def exercise(app, custom):
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
            assert controller.updates.client is None
            assert "PySide6.QtNetwork" not in sys.modules
            assert controller.updates.initial_check.interval() == 120_000
            assert not controller.converter.timer.isActive()
            assert controller.native.shortcut == custom
            assert [action.text() for action in controller.menu.actions()
                    if action.isVisible() and not action.isSeparator()] == [
                        "فعال", "اجرا هنگام روشن کردن سیستم", "تنظیمات", "بررسی به‌روزرسانی",
                        "تاریخچهٔ نسخه‌ها", "دربارهٔ برنامه", "خروج",
                    ]
            changed = Shortcut("K", frozenset({"Ctrl", "Shift"}))
            controller.change_shortcut(changed)
            assert controller.native.shortcut == changed
            assert controller.shortcut_settings().value("shortcut") == str(changed)
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
