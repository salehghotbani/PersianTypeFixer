"""The app's on-demand About dialog."""

from html import escape

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel

from app_version import APP_NAME, LICENSE_NAME, PROJECT_URL, PUBLISHER, VERSION
from update_dialogs import UpdateDialog, label


def show_about(icon):
    version = QApplication.applicationVersion() or VERSION
    dialog = UpdateDialog(
        "دربارهٔ برنامه", APP_NAME, "اصلاح متن انتخاب‌شده بین چیدمان فارسی و انگلیسی با میان‌بر Ctrl+Alt+X.",
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
        f'مجوز <a style="color:#a9c9ff" href="{PROJECT_URL}/blob/main/LICENSE">{LICENSE_NAME}</a><br>'
        f'<a style="color:#a9c9ff" href="{PROJECT_URL}">کد منبع در GitHub</a>'
        f' · <a style="color:#a9c9ff" href="{PROJECT_URL}/issues">گزارش مشکل</a></div>'
    )
    links.setTextFormat(Qt.RichText)
    links.setTextInteractionFlags(Qt.TextBrowserInteraction)
    links.setOpenExternalLinks(True)
    dialog.content.addWidget(links)
    dialog.add_actions("بستن")
    dialog.resize(480, dialog.sizeHint().height())
    dialog.exec()
