"""Windows tray application for correcting a selection with Ctrl+Alt+X."""

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication, QLabel, QMainWindow, QMenu, QPushButton,
    QSystemTrayIcon, QVBoxLayout, QWidget,
)

from selection_conversion import QtClipboard, SelectionConverter
from windows_api import HotkeyFilter, WindowsAPI


class MainWindow(QMainWindow):
    def __init__(self, native=None):
        super().__init__()
        self.native = WindowsAPI() if native is None else native
        self.is_enabled = False
        self.quitting = False
        self.setWindowTitle("Persian Typo Fixer")
        self.setMinimumSize(460, 330)
        self.setLayoutDirection(Qt.RightToLeft)
        self.create_interface()
        self.create_tray()
        self.converter = SelectionConverter(
            self.native, QtClipboard(QApplication.clipboard()), self
        )
        self.converter.status_changed.connect(self.status_label.setText)
        self.converter.finished.connect(self.conversion_finished)
        self.hotkey_filter = HotkeyFilter(self.start_conversion)
        QApplication.instance().installNativeEventFilter(self.hotkey_filter)
        QApplication.instance().aboutToQuit.connect(self.cleanup)
        self.set_enabled(True)

    def create_interface(self):
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        title = QLabel("اصلاح تایپ فارسی و انگلیسی")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        description = QLabel(
            "۱. متن اشتباه را در برنامه مقصد انتخاب کنید.\n"
            "۲. کلیدهای Ctrl+Alt+X را بزنید و رها کنید.\n"
            "متن در همان محل به چیدمان درست تبدیل می‌شود."
        )
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        example = QLabel("sghl  ↔  سلام")
        example.setLayoutDirection(Qt.LeftToRight)
        example.setAlignment(Qt.AlignCenter)
        example.setStyleSheet("font-size: 20px;")
        self.toggle_button = QPushButton()
        self.toggle_button.setMinimumHeight(42)
        self.toggle_button.clicked.connect(self.toggle_enabled)
        self.hide_button = QPushButton("ادامه در پس‌زمینه")
        self.hide_button.setMinimumHeight(42)
        self.hide_button.clicked.connect(self.hide)
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        for widget in (title, description, example, self.toggle_button,
                       self.hide_button, self.status_label):
            layout.addWidget(widget)
        self.setCentralWidget(central)

    def create_tray(self):
        self.tray = QSystemTrayIcon(self)
        icon = self.create_app_icon()
        self.setWindowIcon(icon)
        self.tray.setIcon(icon)
        menu = QMenu(self)
        show_action = menu.addAction("نمایش برنامه")
        show_action.triggered.connect(self.show_window)
        self.toggle_action = QAction("میان‌بر فعال باشد", self)
        self.toggle_action.setCheckable(True)
        self.toggle_action.triggered.connect(self.toggle_enabled)
        menu.addAction(self.toggle_action)
        menu.addSeparator()
        menu.addAction("خروج", self.exit_application)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.tray_activated)
        tray_available = QSystemTrayIcon.isSystemTrayAvailable()
        self.hide_button.setEnabled(tray_available)
        if tray_available:
            self.tray.show()

    @staticmethod
    def create_app_icon():
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor("#2563EB"))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(2, 2, 60, 60, 14, 14)
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Segoe UI", 30, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "ف")
        painter.end()
        return QIcon(pixmap)

    def tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_window()

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
        self.toggle_button.setText("غیرفعال کردن میان‌بر" if self.is_enabled else "فعال کردن میان‌بر")
        self.status_label.setText(message)
        self.tray.setToolTip("Persian Typo Fixer — " + ("فعال" if self.is_enabled else "غیرفعال"))

    def toggle_enabled(self):
        self.set_enabled(not self.is_enabled)

    def start_conversion(self):
        if self.is_enabled and not self.quitting:
            self.converter.start()

    def show_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        if self.tray.isVisible() and not self.quitting:
            self.hide()
            event.ignore()
        else:
            event.accept()
            self.exit_application()

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
        self.converter.cancel(force=True)
        try:
            self.native.unregister_hotkey()
        except OSError:
            pass  # Windows also releases registration on process exit.
        QApplication.instance().removeNativeEventFilter(self.hotkey_filter)
        self.tray.hide()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Persian Typo Fixer")
    app.setQuitOnLastWindowClosed(False)
    window = MainWindow()
    if "--background" not in sys.argv or not window.is_enabled or not window.tray.isVisible():
        window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
