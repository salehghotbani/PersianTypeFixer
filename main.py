"""Tray application for correcting a selection with Ctrl+Alt+X."""

import os
import sys

from PySide6.QtCore import QObject, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMenu, QProxyStyle, QStyle, QStyleOptionMenuItem, QSystemTrayIcon,
)

from about_dialog import show_about
from app_version import APP_NAME, VERSION
from selection_conversion import QtClipboard, SelectionConverter
from tray_updates import TrayUpdates
from update_dialogs import show_update_message

LINUX = sys.platform.startswith("linux")
if LINUX:
    from linux_api import LinuxAPI as NativeAPI
    from linux_session import DESKTOP_ID, SingleInstance, StartupPreference
else:
    from single_instance import SingleInstance
    from startup import StartupPreference
    from windows_api import HotkeyFilter, WindowsAPI as NativeAPI


class TrayMenuStyle(QProxyStyle):
    def drawControl(self, element, option, painter, widget=None):
        if element != QStyle.CE_MenuItem or not option.text:
            super().drawControl(element, option, painter, widget)
            return

        # Ask Qt to paint the native check column on the left, then draw the RTL label.
        row = QStyleOptionMenuItem(option)
        row.direction = Qt.LeftToRight
        row.text = ""
        super().drawControl(element, row, painter, widget)

        style_name = self.baseStyle().objectName()
        solid_selection = style_name in {"windows", "fusion"} or (
            QApplication.styleHints().colorScheme() == Qt.ColorScheme.Unknown
        )
        role = QPalette.Text
        if solid_selection and option.state & QStyle.State_Selected:
            role = QPalette.HighlightedText
        painter.save()
        painter.setFont(option.font)
        self.drawItemText(
            painter, option.rect.adjusted(0, 0, -10, 0),
            Qt.AlignRight | Qt.AlignAbsolute | Qt.AlignVCenter
            | Qt.TextForceRightToLeft | Qt.TextSingleLine,
            option.palette, bool(option.state & QStyle.State_Enabled), option.text, role,
        )
        painter.restore()


class TrayApplication(QObject):
    def __init__(self, native=None):
        super().__init__()
        self.native = NativeAPI() if native is None else native
        self.is_enabled = False
        self.quitting = False
        self.cleaned_up = False
        self.last_status = ""
        self.startup = StartupPreference()
        self.create_tray()
        self.updates = TrayUpdates(self)
        about_action = QAction("دربارهٔ برنامه", self)
        about_action.triggered.connect(lambda: show_about(self.create_app_icon(True)))
        self.menu.insertAction(self.menu.actions()[-1], about_action)
        self.converter = SelectionConverter(
            self.native, QtClipboard(QApplication.clipboard()), self
        )
        self.converter.status_changed.connect(self.show_status)
        self.converter.finished.connect(self.conversion_finished)
        if LINUX:
            self.native.watch_hotkey(self.start_conversion)
        else:
            self.hotkey_filter = HotkeyFilter(self.start_conversion)
            QApplication.instance().installNativeEventFilter(self.hotkey_filter)
        QApplication.instance().aboutToQuit.connect(self.cleanup)
        self.set_enabled(True)

    def create_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.menu = QMenu()
        self.menu.setLayoutDirection(Qt.RightToLeft)
        style = TrayMenuStyle(self.menu.style().objectName())
        style.setParent(self.menu)
        self.menu.setStyle(style)
        self.toggle_action = QAction("فعال", self)
        self.toggle_action.setCheckable(True)
        self.toggle_action.triggered.connect(self.toggle_enabled)
        self.menu.addAction(self.toggle_action)
        self.startup_action = QAction("اجرا هنگام ورود" if LINUX else "اجرا هنگام ورود به ویندوز", self)
        self.startup_action.setCheckable(True)
        self.startup_action.triggered.connect(self.toggle_startup)
        self.menu.addAction(self.startup_action)
        self.menu.aboutToShow.connect(self.refresh_startup)
        self.refresh_startup()
        self.menu.addSeparator()
        self.menu.addAction("خروج", self.exit_application)
        self.tray.setContextMenu(self.menu)

    @staticmethod
    def create_app_icon(enabled):
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor("#2563EB" if enabled else "#6B7280"))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(2, 2, 60, 60, 14, 14)
        painter.setPen(QColor("white"))
        painter.setFont(QFont("DejaVu Sans" if LINUX else "Segoe UI", 30, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "ف")
        painter.end()
        return QIcon(pixmap)

    def set_enabled(self, enabled):
        try:
            if enabled:
                self.native.register_hotkey()
            else:
                self.native.unregister_hotkey()
                self.converter.cancel()
            self.is_enabled = enabled
            message = "وضعیت: فعال — Ctrl+Alt+X" if enabled else "وضعیت: غیرفعال"
        except OSError as error:
            self.is_enabled = self.native.registered
            message = f"خطای میان‌بر: {error}\nممکن است برنامه دیگری Ctrl+Alt+X را گرفته باشد."
        self.toggle_action.setChecked(self.is_enabled)
        self.tray.setIcon(self.create_app_icon(self.is_enabled))
        self.show_status(message)

    def show_status(self, message):
        self.last_status = message
        state = "فعال — Ctrl+Alt+X" if self.is_enabled else "غیرفعال"
        self.tray.setToolTip(f"{APP_NAME}\n{state}\n{message}")

    def toggle_enabled(self):
        self.set_enabled(not self.is_enabled)

    def refresh_startup(self):
        try:
            self.startup_action.setChecked(self.startup.is_enabled())
        except OSError as error:
            self.startup_action.setChecked(False)
            self.show_status(f"خواندن تنظیم اجرای خودکار ممکن نشد: {error}")

    def toggle_startup(self, enabled):
        try:
            self.startup.set_enabled(enabled)
            self.show_status("اجرای خودکار فعال شد." if enabled else "اجرای خودکار غیرفعال شد.")
        except OSError as error:
            self.show_status(f"تنظیم اجرای خودکار ممکن نشد: {error}")
        self.refresh_startup()

    def start_conversion(self):
        if self.is_enabled and not self.quitting:
            self.converter.start()

    def exit_application(self):
        self.quitting = True
        self.updates.stop()
        self.set_enabled(False)
        # Let an already queued paste consume the clipboard before exiting.
        if not self.converter.busy:
            QApplication.quit()

    def conversion_finished(self):
        if self.quitting:
            QApplication.quit()

    def cleanup(self):
        if self.cleaned_up:
            return
        self.cleaned_up = True
        self.updates.stop()
        self.converter.cancel(force=True)
        try:
            self.native.unregister_hotkey()
        except OSError:
            pass  # The platform releases registration on process exit.
        if LINUX:
            self.native.close()
        else:
            QApplication.instance().removeNativeEventFilter(self.hotkey_filter)
        self.tray.hide()


def main():
    if sys.argv[1:] == ["--version"]:
        print(f"{APP_NAME} {VERSION}")
        return 0
    if LINUX:
        session = os.environ.get("XDG_SESSION_TYPE", "").lower()
        if session == "wayland" or (not session and os.environ.get("WAYLAND_DISPLAY")) or not os.environ.get("DISPLAY"):
            print("Persian Typo Fixer requires an X11 desktop session on Linux.", file=sys.stderr)
            return 1
    instance = SingleInstance()
    if instance.already_running:
        instance.close()
        return 0
    try:
        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion(VERSION)
        app.setQuitOnLastWindowClosed(False)
        if LINUX:
            app.setDesktopFileName(DESKTOP_ID)
            if app.platformName() != "xcb":
                print("Persian Typo Fixer requires the Qt X11 (xcb) platform.", file=sys.stderr)
                return 1
        controller = TrayApplication()
        app.setWindowIcon(controller.create_app_icon(True))
        controller.tray.show()
        if "--update-install-failed" in sys.argv:
            QTimer.singleShot(0, lambda: show_update_message(
                "نصب به‌روزرسانی کامل نشد. از منوی کنار ساعت دوباره امتحان کنید.", warning=True,
            ))
        return app.exec()
    except OSError as error:
        if not LINUX:
            raise
        print(f"{APP_NAME}: {error}", file=sys.stderr)
        return 1
    finally:
        instance.close()


if __name__ == "__main__":
    sys.exit(main())
