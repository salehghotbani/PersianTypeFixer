"""The on-demand application window with settings, updates, and About pages."""

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QFrame, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton,
    QScrollArea, QStackedWidget, QVBoxLayout, QWidget,
)

from about_panel import add_about, version_history
from appearance import THEMES
from app_version import APP_NAME, VERSION
from shortcut_editor import ShortcutEditor
from update_dialogs import ThemedDialog, label


GENERAL_PAGE_TITLE = "عمومی"


def navigation_icon(index):
    pixmap = QPixmap(36, 36)
    pixmap.setDevicePixelRatio(2)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor("#5276A5"), 1.5, Qt.SolidLine, Qt.RoundCap))
    if index == 0:
        for y, x in ((5, 6), (9, 12), (13, 8)):
            painter.drawLine(3, y, 15, y)
            painter.drawEllipse(QRectF(x - 1, y - 1, 2, 2))
    elif index == 1:
        painter.drawArc(QRectF(3, 3, 12, 12), 48 * 16, 300 * 16)
        painter.drawLine(15, 3, 15, 8)
        painter.drawLine(15, 8, 11, 8)
    else:
        painter.drawEllipse(QRectF(2.5, 2.5, 13, 13))
        painter.drawPoint(9, 6)
        painter.drawLine(9, 9, 9, 12)
    painter.end()
    return QIcon(pixmap)


class ToggleSwitch(QCheckBox):
    def sizeHint(self):
        return QSize(46, 30)

    def hitButton(self, point):
        return self.rect().contains(point)

    def paintEvent(self, _):
        palette = self.palette()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        track = QRectF(3, 4, 40, 22)
        if not self.isEnabled():
            painter.setOpacity(0.5)
        painter.setPen(Qt.NoPen)
        painter.setBrush(palette.highlight() if self.isChecked() else palette.mid())
        painter.drawRoundedRect(track, 11, 11)
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(QRectF(24 if self.isChecked() else 6, 7, 16, 16))
        if self.hasFocus():
            painter.setPen(QPen(palette.highlight().color(), 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(track.adjusted(-2, -2, 2, 2), 13, 13)
        painter.end()


class Dashboard(ThemedDialog):
    extra_theme = """
        QFrame#sidebar {{ background: {surface}; border-left: 1px solid {border}; }}
        QFrame#card {{ background: {surface}; border: 1px solid {border}; border-radius: 12px; }}
        QFrame#divider {{ background: {border}; }}
        QScrollArea#settingsScroll, QWidget#settingsCards {{ background: transparent; border: 0; }}
        QListWidget#navigation {{ background: transparent; color: {muted}; border: 0; font-size: 14px; outline: 0; }}
        QListWidget#navigation::item {{ padding: 10px 12px; border-radius: 8px; }}
        QListWidget#navigation::item:hover {{ background: {hover}; }}
        QListWidget#navigation::item:selected {{ background: {control}; color: {link}; font-weight: 600; }}
        QListWidget#navigation::item:selected:focus {{ border: 1px solid {focus}; }}
        QLabel#title {{ font-size: 30px; }}
        QLabel#section {{ font-size: 16px; font-weight: 600; }}
        QLabel#rowTitle, QLabel#brand {{ font-weight: 600; }}
        QLabel#eyebrow, QLabel#footer {{ color: {muted}; font-size: 12px; }}
        QPushButton#themeOption {{ background: {surface}; border-width: 1px; border-radius: 6px; padding: 5px 9px; }}
        QPushButton#themeOption:hover {{ background: {hover}; }}
        QPushButton#themeOption:checked {{ background: {accent}; border-color: {accent}; color: white; }}
        QPushButton#themeOption:focus {{ border-color: {focus}; }}
    """

    def __init__(self, controller):
        super().__init__(APP_NAME, "dashboard", controller.appearance)
        self.controller = controller
        self.editor = None
        self.setWindowFlag(Qt.Window, True)
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
        self.setWindowIcon(controller.create_app_icon(True))
        self.resize(880, 580)
        self.setMinimumSize(640, 430)

        body = QHBoxLayout(self)
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(194)
        sidebar_content = QVBoxLayout(sidebar)
        sidebar_content.setContentsMargins(13, 19, 13, 14)
        sidebar_content.setSpacing(12)
        brand_row = QHBoxLayout()
        brand_row.setDirection(QHBoxLayout.LeftToRight)
        logo = label("", "brand")
        logo.setPixmap(self.windowIcon().pixmap(29, 29))
        brand_row.addWidget(logo)
        brand_row.addWidget(label(APP_NAME, "brand"), 1)
        sidebar_content.addLayout(brand_row)
        sidebar_content.addSpacing(5)

        self.navigation = QListWidget()
        self.navigation.setObjectName("navigation")
        self.navigation.setAccessibleName("صفحه‌های برنامه")
        self.navigation.setIconSize(QSize(18, 18))
        for index, title in enumerate((GENERAL_PAGE_TITLE, "به‌روزرسانی", "دربارهٔ برنامه")):
            self.navigation.addItem(QListWidgetItem(navigation_icon(index), title))
        self.navigation.setSpacing(2)
        sidebar_content.addWidget(self.navigation, 1)
        sidebar_content.addWidget(label(f"نسخهٔ \u2066{VERSION}\u2069", "footer"))
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
    def page(title, description, eyebrow):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(22, 17, 22, 18)
        layout.setSpacing(8)
        layout.addWidget(label(eyebrow, "eyebrow"))
        layout.addWidget(label(title, "title"))
        intro = label(description, "description")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        layout.addSpacing(6)
        return page, layout

    @staticmethod
    def card():
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 11)
        layout.setSpacing(7)
        return frame, layout

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
    def toggle_row(action, title, description):
        row = QHBoxLayout()
        copy = QVBoxLayout()
        copy.setSpacing(2)
        copy.addWidget(label(title, "rowTitle"))
        hint = label(description, "description")
        hint.setWordWrap(True)
        copy.addWidget(hint)
        row.addLayout(copy, 1)
        checkbox = ToggleSwitch(action.text())
        checkbox.setFixedSize(checkbox.sizeHint())
        checkbox.setAccessibleName(title)
        checkbox.setToolTip(description)
        row.addWidget(checkbox, alignment=Qt.AlignVCenter)

        def sync():
            checkbox.setChecked(action.isChecked())
            checkbox.setEnabled(action.isEnabled())

        action.changed.connect(sync)
        checkbox.clicked.connect(action.trigger)
        sync()
        return row

    def settings_page(self):
        page, layout = self.page(GENERAL_PAGE_TITLE, "میان‌بر، اجرای خودکار و ظاهر برنامه را تنظیم کنید.", "ترجیحات برنامه")
        scroll = QScrollArea()
        scroll.setObjectName("settingsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        cards = QWidget()
        cards.setObjectName("settingsCards")
        stack = QVBoxLayout(cards)
        stack.setContentsMargins(0, 0, 0, 0)
        stack.setSpacing(11)
        scroll.setWidget(cards)
        layout.addWidget(scroll, 1)

        card, content = self.card()
        content.addWidget(label("عملکرد برنامه", "section"))
        content.addLayout(self.toggle_row(self.controller.toggle_action, "فعال‌بودن اصلاح متن",
                                          "اصلاح متن با میان‌بر سراسری انجام می‌شود."))
        divider = QFrame()
        divider.setObjectName("divider")
        divider.setFixedHeight(1)
        content.addWidget(divider)
        content.addLayout(self.toggle_row(self.controller.startup_action, "اجرا هنگام روشن کردن سیستم",
                                          "برنامه پس از ورود به حساب کاربری باز می‌شود."))
        self.status = label("", "description")
        self.status.setWordWrap(True)
        content.addWidget(self.status)
        stack.addWidget(card)

        card, content = self.card()
        heading = QHBoxLayout()
        heading.addWidget(label("میان‌بر اصلاح متن", "section"))
        heading.addStretch()
        self.current_shortcut = label("", "badge")
        self.current_shortcut.setLayoutDirection(Qt.LeftToRight)
        heading.addWidget(self.current_shortcut)
        content.addLayout(heading)
        if self.controller.wayland:
            button = QPushButton("تنظیم میان‌بر در سیستم")
            button.setAutoDefault(False)
            button.clicked.connect(self.controller.converter.configure_shortcuts)
            content.addWidget(button, alignment=Qt.AlignRight | Qt.AlignAbsolute)
        else:
            self.editor = ShortcutEditor(self.controller.shortcut, self.controller.change_shortcut)
            content.addWidget(self.editor)
        stack.addWidget(card)
        stack.addWidget(self.appearance_card())
        stack.addStretch()
        return page

    def appearance_card(self):
        card, layout = self.card()
        layout.addWidget(label("ظاهر برنامه", "section"))
        row = QHBoxLayout()
        hint = label("رنگ پنجره‌ها را انتخاب کنید.", "description")
        hint.setWordWrap(True)
        row.addWidget(hint, 1)
        controls = QHBoxLayout()
        controls.setSpacing(3)
        self.theme_buttons = QButtonGroup(card)
        for index, (mode, title) in enumerate(THEMES):
            button = QPushButton(title)
            button.setObjectName("themeOption")
            button.setCheckable(True)
            button.setAutoDefault(False)
            button.setChecked(mode == self.appearance.mode)
            self.theme_buttons.addButton(button, index)
            controls.addWidget(button)
        row.addLayout(controls)
        layout.addLayout(row)
        self.theme_buttons.idClicked.connect(self.change_theme)
        self.appearance.changed.connect(self.sync_theme)
        return card

    def sync_theme(self):
        for index, (mode, _) in enumerate(THEMES):
            if mode == self.appearance.mode:
                self.theme_buttons.button(index).setChecked(True)
                break

    def change_theme(self, index):
        try:
            self.appearance.set_mode(THEMES[index][0])
        except OSError as error:
            self.controller.show_status(str(error))
            self.sync_theme()

    def updates_page(self):
        page, layout = self.page("به‌روزرسانی", f"نسخهٔ نصب‌شده \u2066{VERSION}\u2069", "نسخه‌ها")
        card, content = self.card()
        actions = QHBoxLayout()
        actions.addWidget(self.action_button(self.controller.updates.action, page, primary=True))
        actions.addWidget(self.action_button(self.controller.updates.available_action, page))
        actions.addStretch()
        content.addLayout(actions)
        content.addWidget(label("تاریخچهٔ نسخه‌ها", "section"))
        content.addWidget(version_history(), 1)
        layout.addWidget(card, 1)
        return page

    def about_page(self):
        page, layout = self.page("دربارهٔ برنامه", "اصلاح متن انتخاب‌شده بین چیدمان فارسی و انگلیسی", APP_NAME)
        card, content = self.card()
        add_about(content, self.windowIcon())
        layout.addWidget(card)
        layout.addStretch()
        return page

    def refresh_status(self):
        trigger = self.controller.trigger_description or self.controller.shortcut
        self.current_shortcut.setText(str(trigger))
        message = self.controller.last_status
        self.status.setText(message)
        self.status.setVisible(bool(message) and not message.startswith("وضعیت:"))

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
