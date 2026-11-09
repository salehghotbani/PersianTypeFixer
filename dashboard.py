"""The on-demand application window with settings, updates, and About pages."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QHBoxLayout, QListWidget, QPushButton,
    QStackedWidget, QVBoxLayout, QWidget,
)

from about_panel import add_about, version_history
from app_version import APP_NAME, VERSION
from shortcut_editor import ShortcutEditor
from update_dialogs import ThemedDialog, label


class Dashboard(ThemedDialog):
    extra_theme = """
        QFrame#sidebar {{ background: {surface}; border: 1px solid {border}; border-radius: 14px; }}
        QListWidget#navigation {{ background: transparent; color: {text}; border: 0; font-size: 14px; }}
        QListWidget#navigation::item {{ padding: 10px 12px; border-radius: 8px; margin-bottom: 3px; }}
        QListWidget#navigation::item:hover {{ background: {hover}; }}
        QListWidget#navigation::item:selected {{ background: {accent}; color: white; }}
        QLabel#section {{ font-size: 16px; font-weight: 600; }}
    """

    def __init__(self, controller):
        super().__init__(APP_NAME, "dashboard")
        self.controller = controller
        self.editor = None
        self.setWindowFlag(Qt.Window, True)
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
        self.setWindowIcon(controller.create_app_icon(True))
        self.resize(720, 460)
        self.setMinimumSize(570, 420)

        body = QHBoxLayout(self)
        body.setContentsMargins(16, 16, 16, 16)
        body.setSpacing(16)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(170)
        sidebar_content = QVBoxLayout(sidebar)
        sidebar_content.setContentsMargins(10, 12, 10, 10)
        brand = label("ف  Persian Typo Fixer", "badge")
        brand.setAlignment(Qt.AlignCenter)
        sidebar_content.addWidget(brand)

        self.navigation = QListWidget()
        self.navigation.setObjectName("navigation")
        self.navigation.setAccessibleName("صفحه‌های برنامه")
        self.navigation.addItems(["تنظیمات", "به‌روزرسانی", "دربارهٔ برنامه"])
        self.navigation.setSpacing(3)
        sidebar_content.addWidget(self.navigation, 1)
        sidebar_content.addWidget(self.action_button(controller.exit_action, sidebar))
        body.addWidget(sidebar)

        self.pages = QStackedWidget()
        self.pages.addWidget(self.settings_page())
        self.pages.addWidget(self.updates_page())
        self.pages.addWidget(self.about_page())
        body.addWidget(self.pages, 1)
        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.navigation.setCurrentRow(0)
        self.refresh_status()

    @staticmethod
    def page(title, description):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(12)
        layout.addWidget(label(title, "title"))
        intro = label(description, "description")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        return page, layout

    @staticmethod
    def action_button(action, parent, primary=False):
        button = QPushButton(parent)
        button.setAutoDefault(False)
        if primary:
            button.setObjectName("primary")

        def sync():
            button.setText(action.text())
            button.setEnabled(action.isEnabled())
            button.setVisible(action.isVisible())

        action.changed.connect(sync)
        button.clicked.connect(action.trigger)
        sync()
        return button

    @staticmethod
    def action_checkbox(action):
        checkbox = QCheckBox(action.text())

        def sync():
            checkbox.setChecked(action.isChecked())
            checkbox.setEnabled(action.isEnabled())

        action.changed.connect(sync)
        checkbox.clicked.connect(action.trigger)
        sync()
        return checkbox

    def settings_page(self):
        page, layout = self.page("تنظیمات", "وضعیت برنامه، اجرای خودکار و میان‌بر اصلاح متن")
        layout.addWidget(self.action_checkbox(self.controller.toggle_action))
        layout.addWidget(self.action_checkbox(self.controller.startup_action))
        self.status = label("", "description")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        layout.addSpacing(10)
        layout.addWidget(label("میان‌بر اصلاح متن", "section"))
        self.current_shortcut = label("", "badge")
        layout.addWidget(self.current_shortcut, alignment=Qt.AlignRight | Qt.AlignAbsolute)
        if self.controller.wayland:
            button = QPushButton("تنظیم میان‌بر در سیستم")
            button.setAutoDefault(False)
            button.clicked.connect(self.controller.converter.configure_shortcuts)
            layout.addWidget(button, alignment=Qt.AlignRight | Qt.AlignAbsolute)
        else:
            self.editor = ShortcutEditor(self.controller.shortcut, self.controller.change_shortcut)
            layout.addWidget(self.editor)
        layout.addStretch()
        return page

    def updates_page(self):
        page, layout = self.page("به‌روزرسانی", f"نسخهٔ نصب‌شده \u2066{VERSION}\u2069")
        actions = QHBoxLayout()
        actions.addWidget(self.action_button(self.controller.updates.action, page, primary=True))
        actions.addWidget(self.action_button(self.controller.updates.available_action, page))
        actions.addStretch()
        layout.addLayout(actions)
        layout.addWidget(label("تاریخچهٔ نسخه‌ها", "section"))
        layout.addWidget(version_history(), 1)
        return page

    def about_page(self):
        page, layout = self.page("دربارهٔ برنامه", "اصلاح متن انتخاب‌شده بین چیدمان فارسی و انگلیسی")
        add_about(layout, self.windowIcon())
        layout.addStretch()
        return page

    def refresh_status(self):
        trigger = self.controller.trigger_description or self.controller.shortcut
        self.current_shortcut.setText(f"میان‌بر فعلی  \u2066{trigger}\u2069")
        self.status.setText(self.controller.last_status)

    def open_page(self, index):
        if not self.isVisible() and self.editor:
            self.editor.set_shortcut(self.controller.shortcut)
        self.navigation.setCurrentRow(index)
        if self.isMinimized():
            self.showNormal()
        else:
            self.show()
        self.raise_()
        self.activateWindow()
