"""About and offline release history content."""

from html import escape
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel

from app_version import LICENSE_NAME, PROJECT_URL, PUBLISHER, VERSION
from update_dialogs import label, notes_browser


def add_about(content, icon):
    profile = QHBoxLayout()
    mark = QLabel()
    mark.setPixmap(icon.pixmap(48, 48))
    profile.addWidget(mark)
    profile.addWidget(label(f"سازنده\n{PUBLISHER}", "description"))
    profile.addStretch()
    content.addLayout(profile)
    links = QLabel(
        f'<div dir="rtl">نسخهٔ فعلی <bdi dir="ltr">{escape(VERSION)}</bdi><br>'
        f'مجوز <a href="{PROJECT_URL}/blob/main/LICENSE">{LICENSE_NAME}</a><br>'
        f'<a href="{PROJECT_URL}">کد منبع در GitHub</a>'
        f' · <a href="{PROJECT_URL}/issues">گزارش مشکل</a></div>'
    )
    links.setTextFormat(Qt.RichText)
    links.setTextInteractionFlags(Qt.TextBrowserInteraction)
    links.setOpenExternalLinks(True)
    content.addWidget(links)


def version_history():
    try:
        notes = Path(__file__).with_name("CHANGELOG.md").read_text(encoding="utf-8")
    except OSError:
        notes = "خواندن فایل تاریخچهٔ نسخه‌ها ممکن نشد."
    return notes_browser(notes, "تاریخچهٔ نسخه‌ها")
