"""Right-to-left Windows dialogs for the tray updater."""

import ctypes
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QTextDocument
from PySide6.QtWidgets import (
    QApplication, QDialog, QHBoxLayout, QLabel, QProgressBar, QPushButton, QTextBrowser, QVBoxLayout,
)

BACKGROUND = "#0E192E"
FOREGROUND = "#EFF5FF"
RIGHT = Qt.AlignRight | Qt.AlignAbsolute | Qt.AlignVCenter
PERSIAN_DIGITS = str.maketrans("0123456789.", "۰۱۲۳۴۵۶۷۸۹٫")
DWMWA_CAPTION_COLOR = 35
DWMWA_TEXT_COLOR = 36

THEME = f"""
QDialog#updateDialog {{ background: {BACKGROUND}; }}
QLabel {{ color: {FOREGROUND}; font-size: 14px; }}
QLabel#title {{ font-size: 24px; font-weight: 700; }}
QLabel#description {{ color: #B9C9E3; }}
QLabel#badge, QLabel#version {{
    background: #1B3051; color: #B8D3FF; border-radius: 11px;
    font-size: 12px; font-weight: 600; padding: 5px 11px;
}}
QLabel#version {{ background: #16253E; color: #D9E6FF; }}
QLabel#warning {{
    background: #382C2C; color: #FFD28F; border-radius: 11px;
    font-size: 12px; font-weight: 600; padding: 5px 11px;
}}
QLabel#percentage {{ color: #A9C9FF; font-size: 18px; font-weight: 700; }}
QTextBrowser#notes {{
    background: #14223B; color: {FOREGROUND}; border: 1px solid #2B4164;
    border-radius: 12px; padding: 5px; font-size: 14px; selection-background-color: #345FA7;
}}
QTextBrowser#notes:focus {{ border-color: #79A8FF; }}
QScrollBar:vertical {{ background: #14223B; width: 10px; margin: 5px 1px; }}
QScrollBar::handle:vertical {{ background: #526C98; border-radius: 4px; min-height: 24px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
QProgressBar {{ background: #243756; border: 0; border-radius: 5px; height: 10px; }}
QProgressBar::chunk {{ background: #669BFF; border-radius: 5px; }}
QPushButton {{
    background: #192A46; color: {FOREGROUND}; border: 2px solid #334D73;
    border-radius: 9px; min-height: 20px; padding: 7px 16px; font-size: 14px;
}}
QPushButton:hover {{ background: #223958; }}
QPushButton:pressed {{ background: #15233B; }}
QPushButton#primary {{ background: #285BC9; border-color: #285BC9; font-weight: 600; }}
QPushButton#primary:hover {{ background: #2E66DB; }}
QPushButton#primary:pressed {{ background: #204DAF; }}
QPushButton:focus, QPushButton#primary:focus {{ border-color: #ADCFFF; }}
"""


def label(text, name):
    widget = QLabel(text)
    widget.setObjectName(name)
    widget.setTextFormat(Qt.PlainText)
    widget.setAlignment(RIGHT)
    return widget


class ReleaseNotesDocument(QTextDocument):
    def loadResource(self, resource_type, name):
        # A null image is a valid QVariant, so Qt skips its local-file fallback.
        return QImage()


class UpdateDialog(QDialog):
    def __init__(self, title, status, description, version=None, warning=False):
        super().__init__()
        self.setObjectName("updateDialog")
        self.setWindowTitle(title)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet(THEME)
        self.setMinimumWidth(360)

        self.content = QVBoxLayout(self)
        self.content.setContentsMargins(26, 22, 26, 22)
        self.content.setSpacing(12)
        header = QHBoxLayout()
        header.addWidget(label(status, "warning" if warning else "badge"))
        header.addStretch()
        if version:
            version_label = label(version, "version")
            version_label.setLayoutDirection(Qt.LeftToRight)
            header.addWidget(version_label)
        self.content.addLayout(header)
        self.content.addWidget(label(title, "title"))
        subtitle = label(description, "description")
        subtitle.setWordWrap(True)
        self.content.addWidget(subtitle)

    def add_actions(self, dismiss, primary=None):
        row = QHBoxLayout()
        row.setSpacing(9)
        if primary:
            button = QPushButton(primary)
            button.setObjectName("primary")
            button.setAutoDefault(False)
            button.clicked.connect(self.accept)
            row.addWidget(button)
        cancel = QPushButton(dismiss)
        cancel.setDefault(True)
        cancel.clicked.connect(self.reject)
        row.addWidget(cancel)
        row.addStretch()
        self.content.addSpacing(5)
        self.content.addLayout(row)
        cancel.setFocus()

    def showEvent(self, event):
        super().showEvent(event)
        if sys.platform == "win32" and QApplication.platformName() == "windows":
            # The explicit caption colors are supported by Windows 11.
            hwnd = ctypes.c_void_p(int(self.winId()))
            for attribute, color in ((DWMWA_CAPTION_COLOR, BACKGROUND), (DWMWA_TEXT_COLOR, FOREGROUND)):
                rgb = bytes.fromhex(color[1:])
                colorref = ctypes.c_uint32(int.from_bytes(rgb, "little"))
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attribute, ctypes.byref(colorref), ctypes.sizeof(colorref),
                )


def release_dialog(release, linux=False):
    description = ("تغییرات را بخوانید و بستهٔ نصب را از صفحهٔ انتشار بگیرید." if linux
                   else "تغییرات این نسخه را بخوانید و نصب را شروع کنید.")
    dialog = UpdateDialog(
        "نسخهٔ جدید آماده است", "به‌روزرسانی", description,
        version=release.version,
    )
    dialog.setAttribute(Qt.WA_DeleteOnClose)
    dialog.resize(520, 395)
    notes = QTextBrowser()
    notes.setObjectName("notes")
    notes.setAccessibleName("توضیحات انتشار")
    notes.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
    document = ReleaseNotesDocument(notes)
    notes.setDocument(document)
    document.setDocumentMargin(14)
    text_layout = document.defaultTextOption()
    text_layout.setTextDirection(Qt.RightToLeft)
    text_layout.setAlignment(Qt.AlignRight | Qt.AlignAbsolute)
    document.setDefaultTextOption(text_layout)
    document.setMarkdown(
        release.notes.strip() or "برای این نسخه توضیحی منتشر نشده است.",
        QTextDocument.MarkdownDialectGitHub | QTextDocument.MarkdownNoHTML,
    )
    dialog.content.addWidget(notes, 1)
    dialog.add_actions("بعداً", primary="صفحهٔ دریافت" if linux else "دانلود و نصب")
    return dialog


class DownloadDialog(UpdateDialog):
    def __init__(self, release):
        super().__init__(
            "در حال دانلود نصاب", "دانلود به‌روزرسانی", "پس از دریافت و بررسی فایل، نصب شروع می‌شود.",
            version=release.version,
        )
        self.resize(460, self.sizeHint().height())
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, release.size)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setAccessibleName("پیشرفت دانلود نصاب")
        self.content.addWidget(self.progress_bar)
        stats = QHBoxLayout()
        self.percentage = label("", "percentage")
        self.size_label = label("", "description")
        stats.addWidget(self.percentage)
        stats.addStretch()
        stats.addWidget(self.size_label)
        self.content.addLayout(stats)
        self.set_progress(0, release.size)
        self.add_actions("لغو دانلود")

    def set_progress(self, received, total):
        self.progress_bar.setValue(received)
        self.percentage.setText(f"{100 * received // total}٪".translate(PERSIAN_DIGITS))
        self.size_label.setText(f"{received / 1e6:.1f} از {total / 1e6:.1f} مگابایت".translate(PERSIAN_DIGITS))


def show_update_message(text, warning=False):
    title = "مشکلی در به‌روزرسانی رخ داد" if warning else "بررسی نسخه کامل شد"
    status = "نیاز به بررسی" if warning else "به‌روز"
    dialog = UpdateDialog(title, status, text, warning=warning)
    dialog.add_actions("باشه")
    dialog.resize(460, dialog.sizeHint().height())
    dialog.exec()
