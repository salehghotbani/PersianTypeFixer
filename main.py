"""Tray application for correcting a selection with a global shortcut."""

import os
import sys

from PySide6.QtCore import QEvent, QObject, QSettings, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QCursor, QFont, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMenu, QProxyStyle, QStyle, QStyleOptionMenuItem, QSystemTrayIcon,
)

from app_version import APP_NAME, VERSION
from appearance import Appearance
from selection_conversion import QtClipboard, SelectionConverter
from shortcut import DEFAULT_SHORTCUT, Shortcut
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
    def __init__(self, native=None, wayland=False):
        super().__init__()
        self.wayland = wayland
        self.dashboard = None
        self.trigger_description = ""
        self.is_enabled = False
        self.quitting = False
        self.cleaned_up = False
        self.last_status = ""
        settings = self.shortcut_settings()
        self.appearance = Appearance(settings, self)
        try:
            self.shortcut = Shortcut.parse(settings.value("shortcut", str(DEFAULT_SHORTCUT), type=str))
        except ValueError:
            self.shortcut = DEFAULT_SHORTCUT
        self.startup = StartupPreference()
        self.create_tray()
        self.updates = TrayUpdates(self)
        self.menu.insertAction(self.menu.actions()[-1], QAction("تاریخچهٔ نسخه‌ها", self, triggered=self.open_history))
        about_action = QAction("دربارهٔ برنامه", self)
        about_action.triggered.connect(self.open_about)
        self.menu.insertAction(self.menu.actions()[-1], about_action)
        if self.wayland:
            from wayland_session import WaylandSession

            self.converter = WaylandSession(settings, self)
            self.converter.ready_changed.connect(self.wayland_status)
            self.converter.trigger_changed.connect(self.set_trigger_description)
        else:
            self.native = NativeAPI() if native is None else native
            self.converter = SelectionConverter(self.native, QtClipboard(QApplication.clipboard()), self)
        self.converter.status_changed.connect(self.show_status)
        self.converter.finished.connect(self.conversion_finished)
        if not self.wayland:
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
        self.menu.addAction("تنظیمات", self.open_settings)
        self.menu.addSeparator()
        self.toggle_action = QAction("فعال", self)
        self.toggle_action.setCheckable(True)
        self.toggle_action.triggered.connect(self.toggle_enabled)
        self.menu.addAction(self.toggle_action)
        self.startup_action = QAction("اجرا هنگام روشن کردن سیستم", self)
        self.startup_action.setCheckable(True)
        self.startup_action.triggered.connect(self.toggle_startup)
        self.menu.addAction(self.startup_action)
        self.menu.aboutToShow.connect(self.refresh_startup)
        self.menu.addSeparator()
        self.exit_action = self.menu.addAction("خروج", self.exit_application)
        if self.wayland:
            # An xdg-popup requires a Wayland parent surface and an input serial.
            # Tray activation arrives over D-Bus, so use the same menu as a tool.
            self.menu.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
            self.menu.installEventFilter(self)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self.show_tray_menu)

    def show_tray_menu(self, reason):
        # Qt and the desktop host already handle the native context click.
        if reason == QSystemTrayIcon.Trigger and not self.menu.isVisible():
            self.menu.popup(QCursor.pos())

    def eventFilter(self, watched, event):
        if watched is self.menu and event.type() == QEvent.WindowDeactivate:
            self.menu.hide()
        return super().eventFilter(watched, event)

    def open_dashboard(self, page):
        if self.dashboard is None:
            from dashboard import Dashboard

            self.dashboard = Dashboard(self)
        self.refresh_startup()
        self.dashboard.open_page(page)

    def open_settings(self):
        self.open_dashboard(0)

    def open_history(self):
        self.open_dashboard(1)

    def open_about(self):
        self.open_dashboard(2)

    @staticmethod
    def shortcut_settings():
        return QSettings("ghotbani.ir", "PersianTypoFixer")

    def change_shortcut(self, shortcut):
        if shortcut == self.shortcut:
            return
        if self.converter.busy:
            raise OSError("صبر کنید اصلاح متن کامل شود و دوباره تلاش کنید.")

        was_enabled = self.is_enabled
        settings = self.shortcut_settings()
        self.native.unregister_hotkey()
        try:
            try:
                self.native.register_hotkey(shortcut)
            except OSError as error:
                raise OSError(f"ثبت میان‌بر {shortcut} ممکن نشد. ممکن است سیستم یا برنامهٔ دیگری از آن استفاده کند.") from error
            if not was_enabled:
                self.native.unregister_hotkey()
            settings.setValue("shortcut", str(shortcut))
            settings.sync()
            if settings.status() != QSettings.Status.NoError:
                raise OSError("ذخیرهٔ میان‌بر ممکن نشد.")
        except OSError:
            try:
                self.native.unregister_hotkey()
                if was_enabled:
                    self.native.register_hotkey(self.shortcut)
            except OSError as error:
                message = "میان‌بر قبلی دوباره ثبت نشد. ترکیب دیگری را در تنظیمات انتخاب کنید."
                self.update_enabled_status(self.native.registered, message)
                raise OSError(message) from error
            raise

        self.shortcut = shortcut
        self.show_status("میان‌بر ذخیره شد.")

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
        if self.wayland:
            self.toggle_action.setChecked(self.is_enabled)
            self.toggle_action.setEnabled(False)
            if enabled:
                self.show_status("در انتظار پاسخ محیط دسکتاپ برای فعال کردن میان‌بر…")
            self.converter.set_enabled(enabled, self.shortcut)
            return
        try:
            if enabled:
                self.native.register_hotkey(self.shortcut)
            else:
                self.native.unregister_hotkey()
                self.is_enabled = False
                self.converter.cancel()
            message = "وضعیت: فعال" if enabled else "وضعیت: غیرفعال"
        except OSError as error:
            message = f"خطای میان‌بر: {error}\nممکن است برنامهٔ دیگری {self.shortcut} را گرفته باشد."
        self.update_enabled_status(self.native.registered, message)

    def update_enabled_status(self, enabled, message):
        self.is_enabled = enabled
        self.toggle_action.setChecked(self.is_enabled)
        self.tray.setIcon(self.create_app_icon(self.is_enabled))
        self.show_status(message)

    def wayland_status(self, enabled, message):
        self.toggle_action.setEnabled(True)
        self.update_enabled_status(enabled, message)

    def set_trigger_description(self, description):
        self.trigger_description = description
        self.show_status(self.last_status)

    def show_status(self, message):
        self.last_status = message
        if "--verbose" in sys.argv:
            print(message, file=sys.stderr, flush=True)
        trigger = self.trigger_description or self.shortcut
        state = f"فعال — \u2066{trigger}\u2069" if self.is_enabled else "غیرفعال"
        self.tray.setToolTip(f"{APP_NAME}\n{state}\n{message}")
        if self.dashboard is not None:
            self.dashboard.refresh_status()

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
        if self.wayland:
            QApplication.quit()
            return
        self.set_enabled(False)
        # Let an already queued paste consume the clipboard before exiting.
        if not self.converter.busy:
            QApplication.quit()

    def conversion_finished(self):
        if self.quitting:
            QApplication.quit()
        elif not self.wayland and self.is_enabled and not self.cleaned_up and not self.native.registered:
            self.set_enabled(True)

    def cleanup(self):
        if self.cleaned_up:
            return
        self.cleaned_up = True
        self.updates.stop()
        if self.dashboard is not None:
            self.dashboard.close()
        if self.wayland:
            self.converter.close()
            self.tray.hide()
            return
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
    wayland = False
    if LINUX:
        session = os.environ.get("XDG_SESSION_TYPE", "").lower()
        wayland = session == "wayland" or (not session and bool(os.environ.get("WAYLAND_DISPLAY")))
        if not wayland and not os.environ.get("DISPLAY"):
            print("Persian Typo Fixer requires a graphical desktop session on Linux.", file=sys.stderr)
            return 1
        if wayland:
            os.environ.setdefault("QT_QPA_PLATFORM", "wayland")
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
            if not (app.platformName().startswith("wayland") if wayland else app.platformName() == "xcb"):
                print("The Qt platform does not match the Linux desktop session.", file=sys.stderr)
                return 1
        controller = TrayApplication(wayland=wayland)
        app.setWindowIcon(controller.tray.icon())
        controller.tray.show()
        if "--update-install-failed" in sys.argv:
            QTimer.singleShot(0, lambda: show_update_message(
                "نصب به‌روزرسانی کامل نشد. از منوی کنار ساعت دوباره امتحان کنید.",
                controller.appearance, warning=True,
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
