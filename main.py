"""Windows tray application for correcting a selection with Ctrl+Alt+X."""

import sys

from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from app_version import VERSION
from single_instance import SingleInstance
from startup import StartupPreference
from selection_conversion import QtClipboard, SelectionConverter
from windows_api import HotkeyFilter, WindowsAPI


class TrayApplication(QObject):
    def __init__(self, native=None):
        super().__init__()
        self.native = WindowsAPI() if native is None else native
        self.is_enabled = False
        self.quitting = False
        self.cleaned_up = False
        self.last_status = ""
        self.startup = StartupPreference()
        self.create_tray()
        self.converter = SelectionConverter(
            self.native, QtClipboard(QApplication.clipboard()), self
        )
        self.converter.status_changed.connect(self.show_status)
        self.converter.finished.connect(self.conversion_finished)
        self.hotkey_filter = HotkeyFilter(self.start_conversion)
        QApplication.instance().installNativeEventFilter(self.hotkey_filter)
        QApplication.instance().aboutToQuit.connect(self.cleanup)
        self.set_enabled(True)

    def create_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.menu = QMenu()
        self.menu.setLayoutDirection(Qt.RightToLeft)
        self.toggle_action = QAction("فعال", self)
        self.toggle_action.setCheckable(True)
        self.toggle_action.triggered.connect(self.toggle_enabled)
        self.menu.addAction(self.toggle_action)
        self.startup_action = QAction("اجرا هنگام ورود به ویندوز", self)
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
        painter.setFont(QFont("Segoe UI", 30, QFont.Bold))
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
        self.tray.setToolTip(f"Persian Typo Fixer\n{state}\n{message}")

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
        self.converter.cancel(force=True)
        try:
            self.native.unregister_hotkey()
        except OSError:
            pass  # Windows also releases registration on process exit.
        QApplication.instance().removeNativeEventFilter(self.hotkey_filter)
        self.tray.hide()


def main():
    instance = SingleInstance()
    if instance.already_running:
        instance.close()
        return 0
    app = QApplication(sys.argv)
    app.setApplicationName("Persian Typo Fixer")
    app.setApplicationVersion(VERSION)
    app.setQuitOnLastWindowClosed(False)
    controller = TrayApplication()
    controller.tray.show()
    try:
        return app.exec()
    finally:
        instance.close()


if __name__ == "__main__":
    sys.exit(main())
