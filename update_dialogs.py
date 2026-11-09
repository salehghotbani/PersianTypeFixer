"""Right-to-left dialogs that follow the desktop color scheme."""

import ctypes
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPalette, QTextCursor, QTextDocument
from PySide6.QtWidgets import (
    QApplication, QDialog, QHBoxLayout, QLabel, QProgressBar, QPushButton, QTextBrowser, QVBoxLayout,
)

RIGHT = Qt.AlignRight | Qt.AlignAbsolute | Qt.AlignVCenter
PERSIAN_DIGITS = str.maketrans("0123456789.", "۰۱۲۳۴۵۶۷۸۹٫")
DWMWA_CAPTION_COLOR = 35
DWMWA_TEXT_COLOR = 36

DARK = {"background": "#0E192E", "text": "#EFF5FF", "muted": "#B9C9E3",
        "surface": "#14223B", "control": "#192A46", "hover": "#223958", "border": "#334D73",
        "accent": "#285BC9", "accent_hover": "#2E66DB", "link": "#A9C9FF", "focus": "#ADCFFF",
        "warning_bg": "#382C2C", "warning_text": "#FFD28F"}
LIGHT = {"background": "#F7FAFF", "text": "#132745", "muted": "#405778",
         "surface": "#FFFFFF", "control": "#E9F0FC", "hover": "#D9E7FC", "border": "#9CB2D2",
         "accent": "#2152B7", "accent_hover": "#19469F", "link": "#1E4EA8", "focus": "#1B4DAB",
         "warning_bg": "#FFF0DA", "warning_text": "#7B3A00"}

THEME = """
QDialog#updateDialog, QDialog#dashboard {{ background: {background}; }}
QLabel {{ color: {text}; font-size: 14px; }}
QLabel#title {{ font-size: 24px; font-weight: 700; }}
QLabel#description {{ color: {muted}; }}
QLabel#badge, QLabel#version {{
    background: {control}; color: {link}; border-radius: 11px;
    font-size: 12px; font-weight: 600; padding: 5px 11px;
}}
QLabel#warning, QLabel#validation {{
    background: {warning_bg}; color: {warning_text}; border-radius: 11px;
    font-size: 12px; font-weight: 600; padding: 5px 11px;
}}
QLabel#percentage {{ color: {link}; font-size: 18px; font-weight: 700; }}
QTextBrowser#notes {{
    background: {surface}; color: {text}; border: 1px solid {border};
    border-radius: 12px; padding: 5px; font-size: 14px;
    selection-background-color: {accent}; selection-color: white;
}}
QTextBrowser#notes:focus {{ border-color: {focus}; }}
QScrollBar:vertical {{ background: {surface}; width: 10px; margin: 5px 1px; }}
QScrollBar::handle:vertical {{ background: {border}; border-radius: 4px; min-height: 24px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
QProgressBar {{ background: {control}; border: 0; border-radius: 5px; height: 10px; }}
QProgressBar::chunk {{ background: {link}; border-radius: 5px; }}
QPushButton {{
    background: {control}; color: {text}; border: 2px solid {border};
    border-radius: 9px; min-height: 20px; padding: 7px 16px; font-size: 14px;
}}
QPushButton:hover {{ background: {hover}; }}
QPushButton#primary {{ background: {accent}; color: white; border-color: {accent}; font-weight: 600; }}
QPushButton#primary:hover {{ background: {accent_hover}; }}
QPushButton:focus, QPushButton#primary:focus {{ border-color: {focus}; }}
QCheckBox {{ color: {text}; spacing: 6px; }}
QComboBox {{ background: {control}; color: {text}; min-width: 58px; padding: 5px; }}
QComboBox QAbstractItemView {{
    background: {surface}; color: {text}; selection-background-color: {accent}; selection-color: white;
}}
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


class ThemedDialog(QDialog):
    extra_theme = ""

    def __init__(self, title, object_name, appearance):
        super().__init__()
        self.setObjectName(object_name)
        self.setWindowTitle(title)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setLayoutDirection(Qt.RightToLeft)
        self.appearance = appearance
        self.colors = None
        self.apply_theme()
        appearance.changed.connect(self.apply_theme)
        QApplication.styleHints().colorSchemeChanged.connect(self.apply_theme)
        QApplication.instance().paletteChanged.connect(self.apply_theme)

    def showEvent(self, event):
        super().showEvent(event)
        self.apply_caption()

    def apply_theme(self, *_):
        colors = DARK if self.appearance.is_dark() else LIGHT
        if self.colors is colors:
            return
        self.colors = colors
        palette = QPalette()
        for role, key in ((QPalette.Link, "link"), (QPalette.Text, "text"),
                          (QPalette.ButtonText, "text"), (QPalette.Base, "surface"),
                          (QPalette.Button, "control"), (QPalette.Window, "background"),
                          (QPalette.WindowText, "text"), (QPalette.Highlight, "accent"),
                          (QPalette.Mid, "border")):
            palette.setColor(role, QColor(colors[key]))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        self.setPalette(palette)
        self.setStyleSheet((THEME + self.extra_theme).format(**colors))
        if self.isVisible():
            self.apply_caption()

    def apply_caption(self):
        if sys.platform == "win32" and QApplication.platformName() == "windows":
            # The explicit caption colors are supported by Windows 11.
            hwnd = ctypes.c_void_p(int(self.winId()))
            for attribute, role in ((DWMWA_CAPTION_COLOR, "background"), (DWMWA_TEXT_COLOR, "text")):
                color = self.colors[role]
                rgb = bytes.fromhex(color[1:])
                colorref = ctypes.c_uint32(int.from_bytes(rgb, "little"))
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attribute, ctypes.byref(colorref), ctypes.sizeof(colorref),
                )


class UpdateDialog(ThemedDialog):
    def __init__(self, title, status, description, appearance, version=None, warning=False):
        super().__init__(title, "updateDialog", appearance)
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


def release_dialog(release, appearance, linux=False):
    description = ("تغییرات را بخوانید و بستهٔ نصب را از صفحهٔ انتشار بگیرید." if linux
                   else "تغییرات این نسخه را بخوانید و نصب را شروع کنید.")
    dialog = UpdateDialog(
        "نسخهٔ جدید آماده است", "به‌روزرسانی", description, appearance,
        version=release.version,
    )
    dialog.setAttribute(Qt.WA_DeleteOnClose)
    dialog.resize(520, 395)
    dialog.content.addWidget(notes_browser(
        release.notes.strip() or "برای این نسخه توضیحی منتشر نشده است.", "توضیحات انتشار",
    ), 1)
    dialog.add_actions("بعداً", primary="صفحهٔ دریافت" if linux else "دانلود و نصب")
    return dialog


def notes_browser(markdown, accessible_name):
    notes = QTextBrowser()
    notes.setObjectName("notes")
    notes.setAccessibleName(accessible_name)
    notes.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
    document = ReleaseNotesDocument(notes)
    notes.setDocument(document)
    document.setDocumentMargin(14)
    text_layout = document.defaultTextOption()
    text_layout.setTextDirection(Qt.RightToLeft)
    text_layout.setAlignment(Qt.AlignRight | Qt.AlignAbsolute)
    document.setDefaultTextOption(text_layout)
    document.setMarkdown(
        markdown,
        QTextDocument.MarkdownDialectGitHub | QTextDocument.MarkdownNoHTML,
    )
    notes.moveCursor(QTextCursor.Start)
    return notes


class DownloadDialog(UpdateDialog):
    def __init__(self, release, appearance):
        super().__init__(
            "در حال دانلود نصاب", "دانلود به‌روزرسانی", "پس از دریافت و بررسی فایل، نصب شروع می‌شود.",
            appearance, version=release.version,
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


def show_update_message(text, appearance, warning=False):
    title = "مشکلی در به‌روزرسانی رخ داد" if warning else "بررسی نسخه کامل شد"
    status = "نیاز به بررسی" if warning else "به‌روز"
    dialog = UpdateDialog(title, status, text, appearance, warning=warning)
    dialog.add_actions("باشه")
    dialog.resize(460, dialog.sizeHint().height())
    dialog.exec()
