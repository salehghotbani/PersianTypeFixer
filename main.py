import sys
import time
import uuid

import keyboard
import pyperclip

from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QSystemTrayIcon,
    QMenu,
)


# =========================================================
# Keyboard layout mappings
# =========================================================

EN_TO_FA = {
    "q": "ض", "w": "ص", "e": "ث", "r": "ق",
    "t": "ف", "y": "غ", "u": "ع", "i": "ه",
    "o": "خ", "p": "ح", "[": "ج", "]": "چ",

    "a": "ش", "s": "س", "d": "ی", "f": "ب",
    "g": "ل", "h": "ا", "j": "ت", "k": "ن",
    "l": "م", ";": "ک", "'": "گ",

    "z": "ظ", "x": "ط", "c": "ز", "v": "ر",
    "b": "ذ", "n": "د", "m": "ئ",
    ",": "و", ".": ".", "/": "/",
}

FA_TO_EN = {
    value: key for key, value in EN_TO_FA.items()
}

# Support Arabic variants commonly found in copied text.
FA_TO_EN["ي"] = "d"
FA_TO_EN["ك"] = ";"

def convert_text(text: str) -> str:
    """
    Automatically choose conversion direction based on
    the first recognized character in the selection.
    """
    for char in text:
        if char in EN_TO_FA:
            return "".join(EN_TO_FA.get(c, c) for c in text)

        if char in FA_TO_EN:
            return "".join(FA_TO_EN.get(c, c) for c in text)

    return text


# =========================================================
# Thread-safe hotkey signal
# =========================================================

class AppSignals(QObject):
    hotkey_pressed = Signal()


# =========================================================
# Main application
# =========================================================

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Persian Typo Fixer")
        self.setMinimumSize(420, 300)

        self.is_enabled = True
        self.hotkey_registered = False

        self.clipboard_marker = None
        self.old_clipboard = None
        self.converted_clipboard = None
        self.wait_count = 0

        self.signals = AppSignals()
        self.signals.hotkey_pressed.connect(
            self.start_conversion
        )

        self.create_interface()
        self.create_tray()
        self.set_enabled(True)

    # -----------------------------------------------------
    # User interface
    # -----------------------------------------------------

    def create_interface(self):
        central = QWidget()
        layout = QVBoxLayout(central)

        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("اصلاح تایپ فارسی")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "font-size: 24px; font-weight: bold;"
        )

        description = QLabel(
            "متن اشتباه را در هر برنامه انتخاب کنید "
            "و کلید F10 را فشار دهید."
        )
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)

        self.convert_button = QPushButton(
            "اصلاح متن انتخاب‌شده (F10)"
        )
        self.convert_button.setMinimumHeight(48)
        self.convert_button.clicked.connect(
            self.start_conversion
        )

        self.toggle_button = QPushButton()
        self.toggle_button.setMinimumHeight(42)
        self.toggle_button.clicked.connect(
            self.toggle_enabled
        )

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(self.convert_button)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.status_label)

        self.setCentralWidget(central)

    # -----------------------------------------------------
    # System tray
    # -----------------------------------------------------

    def create_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.create_app_icon())
        self.tray.setToolTip("Persian Typo Fixer")

        menu = QMenu()

        self.show_action = QAction("نمایش برنامه", self)
        self.show_action.triggered.connect(
            self.show_window
        )
        menu.addAction(self.show_action)

        self.toggle_action = QAction(
            "اصلاح متن فعال باشد", self
        )
        self.toggle_action.setCheckable(True)
        self.toggle_action.setChecked(True)
        self.toggle_action.triggered.connect(
            self.toggle_enabled
        )
        menu.addAction(self.toggle_action)

        menu.addSeparator()

        exit_action = QAction("خروج", self)
        exit_action.triggered.connect(
            self.exit_application
        )
        menu.addAction(exit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(
            self.tray_activated
        )

        self.tray.show()

    def create_app_icon(self):
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setBrush(QColor("#2563EB"))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(
            2, 2, 60, 60, 14, 14
        )

        painter.setPen(QColor("white"))
        painter.setFont(
            QFont("Segoe UI", 30, QFont.Bold)
        )
        painter.drawText(
            pixmap.rect(),
            Qt.AlignCenter,
            "ف"
        )

        painter.end()
        return QIcon(pixmap)

    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

    # -----------------------------------------------------
    # Enable / disable
    # -----------------------------------------------------

    def set_enabled(self, enabled: bool):
        self.is_enabled = enabled

        if enabled:
            if not self.hotkey_registered:
                try:
                    keyboard.add_hotkey(
                        "f10",
                        self.on_hotkey,
                        suppress=True,
                    )
                    self.hotkey_registered = True
                except Exception as error:
                    self.status_label.setText(
                        f"خطا در ثبت میانبر: {error}"
                    )
                    self.is_enabled = False
                    return

            self.status_label.setText("وضعیت: فعال")
            self.toggle_button.setText(
                "غیرفعال کردن اصلاح متن"
            )
            self.tray.setToolTip(
                "Persian Typo Fixer - فعال"
            )

        else:
            if self.hotkey_registered:
                keyboard.remove_hotkey("f10")
                self.hotkey_registered = False

            self.status_label.setText("وضعیت: غیرفعال")
            self.toggle_button.setText(
                "فعال کردن اصلاح متن"
            )
            self.tray.setToolTip(
                "Persian Typo Fixer - غیرفعال"
            )

        self.toggle_action.setChecked(self.is_enabled)

    def toggle_enabled(self):
        self.set_enabled(not self.is_enabled)

    # -----------------------------------------------------
    # Hotkey
    # -----------------------------------------------------

    def on_hotkey(self):
        # The keyboard hook runs outside the Qt GUI thread.
        # Send a signal so clipboard operations happen in Qt.
        self.signals.hotkey_pressed.emit()

    # -----------------------------------------------------
    # Text conversion
    # -----------------------------------------------------

    def start_conversion(self):
        if not self.is_enabled:
            return

        if self.clipboard_marker is not None:
            return

        try:
            self.old_clipboard = pyperclip.paste()
        except Exception:
            self.old_clipboard = ""

        self.clipboard_marker = (
            "__PERSIAN_FIXER_"
            + uuid.uuid4().hex
            + "__"
        )

        try:
            pyperclip.copy(self.clipboard_marker)

            # Copy the selection from the currently focused app.
            keyboard.send("ctrl+c")

        except Exception as error:
            self.status_label.setText(
                f"خطا در کپی متن: {error}"
            )
            self.restore_clipboard()
            return

        self.wait_count = 0

        self.clipboard_timer = QTimer(self)
        self.clipboard_timer.timeout.connect(
            self.check_clipboard
        )
        self.clipboard_timer.start(100)

    def check_clipboard(self):
        self.wait_count += 1

        try:
            copied_text = pyperclip.paste()
        except Exception:
            copied_text = ""

        if copied_text != self.clipboard_marker:
            self.clipboard_timer.stop()

            if not copied_text:
                self.status_label.setText(
                    "متنی انتخاب نشده است."
                )
                self.restore_clipboard()
                return

            converted_text = convert_text(copied_text)

            if converted_text == copied_text:
                self.status_label.setText(
                    "متن قابل تبدیل نیست."
                )
                self.restore_clipboard()
                return

            try:
                pyperclip.copy(converted_text)
                self.converted_clipboard = converted_text

                keyboard.send("ctrl+v")

                self.status_label.setText(
                    "متن با موفقیت اصلاح شد."
                )

                # Allow the target application to finish pasting.
                QTimer.singleShot(
                    1200,
                    self.restore_clipboard,
                )

            except Exception as error:
                self.status_label.setText(
                    f"خطا در جایگزینی متن: {error}"
                )
                self.restore_clipboard()

        elif self.wait_count >= 20:
            self.clipboard_timer.stop()

            self.status_label.setText(
                "متن انتخاب‌شده دریافت نشد."
            )
            self.restore_clipboard()

    def restore_clipboard(self):
        if self.clipboard_marker is None:
            return

        try:
            current_clipboard = pyperclip.paste()

            # Restore only if our operation still owns the clipboard.
            if (
                current_clipboard == self.clipboard_marker
                or current_clipboard == self.converted_clipboard
            ):
                pyperclip.copy(self.old_clipboard or "")

        except Exception:
            pass

        self.clipboard_marker = None
        self.old_clipboard = None
        self.converted_clipboard = None

    # -----------------------------------------------------
    # Window behavior
    # -----------------------------------------------------

    def show_window(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        # Closing the window keeps the app in the tray.
        self.hide()
        event.ignore()

    # -----------------------------------------------------
    # Exit
    # -----------------------------------------------------

    def exit_application(self):
        if self.hotkey_registered:
            keyboard.remove_hotkey("f10")
            self.hotkey_registered = False

        self.tray.hide()
        QApplication.quit()


# =========================================================
# Entry point
# =========================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow()

    # Start in the background by default.
    if "--show" in sys.argv:
        window.show()
    else:
        window.hide()

    sys.exit(app.exec())