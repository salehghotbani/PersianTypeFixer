"""The app's on-demand About dialog."""

from html import escape
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel

from app_version import APP_NAME, LICENSE_NAME, PROJECT_URL, PUBLISHER, VERSION
from update_dialogs import UpdateDialog, label, notes_browser


def show_about(icon, shortcut):
    version = QApplication.applicationVersion() or VERSION
    dialog = UpdateDialog(
        "دربارهٔ برنامه", APP_NAME,
        f"اصلاح متن انتخاب‌شده بین چیدمان فارسی و انگلیسی با میان‌بر \u2066{shortcut}\u2069.",
        version=version,
    )
    dialog.setWindowIcon(icon)
    profile = QHBoxLayout()
    mark = QLabel()
    mark.setPixmap(icon.pixmap(48, 48))
    profile.addWidget(mark)
    profile.addWidget(label(f"سازنده\n{PUBLISHER}", "description"))
    profile.addStretch()
    dialog.content.addLayout(profile)
    links = QLabel(
        f'<div dir="rtl">نسخهٔ فعلی <bdi dir="ltr">{escape(version)}</bdi><br>'
        f'مجوز <a href="{PROJECT_URL}/blob/main/LICENSE">{LICENSE_NAME}</a><br>'
        f'<a href="{PROJECT_URL}">کد منبع در GitHub</a>'
        f' · <a href="{PROJECT_URL}/issues">گزارش مشکل</a></div>'
    )
    links.setTextFormat(Qt.RichText)
    links.setTextInteractionFlags(Qt.TextBrowserInteraction)
    links.setOpenExternalLinks(True)
    dialog.content.addWidget(links)
    dialog.add_actions("بستن")
    dialog.resize(480, dialog.sizeHint().height())
    dialog.exec()


def show_history():
    dialog = UpdateDialog(
        "تاریخچهٔ نسخه‌ها", "تغییرات برنامه", "یادداشت‌های انتشار نسخهٔ نصب‌شده و نسخه‌های قبلی.",
        version=VERSION,
    )
    try:
        notes = Path(__file__).with_name("CHANGELOG.md").read_text(encoding="utf-8")
    except OSError:
        notes = "خواندن فایل تاریخچهٔ نسخه‌ها ممکن نشد."
    dialog.content.addWidget(notes_browser(notes, "تاریخچهٔ نسخه‌ها"), 1)
    dialog.add_actions("بستن")
    dialog.resize(570, 460)
    dialog.exec()
