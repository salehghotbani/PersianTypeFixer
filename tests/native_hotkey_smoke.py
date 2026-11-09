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
from unittest.mock import Mock

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QSettings, QTimer
from PySide6.QtWidgets import QApplication, QCheckBox, QLabel, QPushButton, QSystemTrayIcon, QTextBrowser

from main import TrayApplication
from appearance import Appearance
from shortcut import Shortcut
from update_dialogs import DARK, LIGHT, UpdateDialog
from windows_api import HOTKEY_ID, WM_HOTKEY


def main():
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)
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
            assert controller.dashboard is None
            assert [action.text() for action in controller.menu.actions()
                    if action.isVisible() and not action.isSeparator()] == [
                        "تنظیمات", "فعال", "اجرا هنگام روشن کردن سیستم", "بررسی به‌روزرسانی",
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
            exercise_dashboard(app, controller, changed)
        except Exception as error:
            errors.append(error)
            app.quit()
        else:
            controller.exit_action.trigger()

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


def exercise_dashboard(app, controller, changed):
    controller.startup = Mock()
    controller.startup.is_enabled.return_value = False
    controller.tray.activated.emit(QSystemTrayIcon.Trigger)
    assert controller.tray.contextMenu() is controller.menu and controller.menu.isVisible()
    controller.menu.hide()

    controller.open_settings()
    window = controller.dashboard
    assert window.isVisible() and window.pages.currentIndex() == 0
    assert window.navigation.item(0).text() == "عمومی"
    assert window.pages.currentWidget().findChild(QLabel, "title").text() == "عمومی"
    assert [widget for widget in app.topLevelWidgets() if widget.isVisible()] == [window]
    assert str(changed) in window.current_shortcut.text()
    assert not any(button.text() == "خروج" for button in window.findChildren(QPushButton))
    dialog = UpdateDialog("آزمون", "تم", "پیش‌نمایش", controller.appearance)
    for index, mode, colors in ((2, "dark", DARK), (1, "light", LIGHT)):
        window.theme_buttons.button(index).click()
        assert window.colors is colors and dialog.colors is colors
        assert Appearance(controller.shortcut_settings()).mode == mode
    window.theme_buttons.button(0).click()
    assert Appearance(controller.shortcut_settings()).mode == "system"
    settings_page = window.pages.currentWidget()
    checkboxes = {box.text(): box for box in settings_page.findChildren(QCheckBox)}
    checkboxes["فعال"].click()
    assert not controller.toggle_action.isChecked() and not checkboxes["فعال"].isChecked()
    controller.toggle_action.trigger()
    assert checkboxes["فعال"].isChecked()
    controller.startup.is_enabled.return_value = True
    checkboxes["اجرا هنگام روشن کردن سیستم"].click()
    controller.startup.set_enabled.assert_called_once_with(True)
    assert controller.startup_action.isChecked()

    controller.open_history()
    assert controller.dashboard is window and window.pages.currentIndex() == 1
    assert "1.0.0" in window.pages.currentWidget().findChild(QTextBrowser).toPlainText()
    check = next(button for button in window.pages.currentWidget().findChildren(QPushButton)
                 if button.text() == controller.updates.action.text())
    client = Mock()
    controller.updates.start_client = Mock(return_value=client)
    check.click()
    client.check.assert_called_once()
    assert not check.isEnabled()
    controller.open_about()
    assert controller.dashboard is window and window.pages.currentIndex() == 2
    window.navigation.setCurrentRow(0)
    assert window.pages.currentIndex() == 0
    window.close()
    app.processEvents()
    assert not window.isVisible() and not controller.quitting and controller.native.registered


if __name__ == "__main__":
    main()
