"""Edit the global shortcut from the tray settings."""

from string import ascii_uppercase

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QPushButton

from shortcut import DEFAULT_SHORTCUT, MODIFIERS, Shortcut
from update_dialogs import UpdateDialog, label


class ShortcutDialog(UpdateDialog):
    def __init__(self, current, save):
        super().__init__(
            "تنظیمات", "میان‌بر اصلاح متن",
            "یک حرف از چیدمان انگلیسی و دست‌کم یکی از کلیدهای Ctrl، Alt یا Shift را انتخاب کنید.",
        )
        self.save = save
        self.resize(490, self.sizeHint().height())
        row = QHBoxLayout()
        row.setDirection(QHBoxLayout.LeftToRight)
        self.modifiers = {key: QCheckBox(key) for key in MODIFIERS}
        for checkbox in self.modifiers.values():
            checkbox.setLayoutDirection(Qt.LeftToRight)
            row.addWidget(checkbox)
        self.letter = QComboBox()
        self.letter.setLayoutDirection(Qt.LeftToRight)
        self.letter.setAccessibleName("حرف میان‌بر")
        self.letter.addItems(list(ascii_uppercase))
        row.addWidget(self.letter)
        row.addStretch()
        self.content.addLayout(row)

        self.validation = label("", "validation")
        self.validation.setWordWrap(True)
        self.validation.hide()
        self.content.addWidget(self.validation)
        restore = QPushButton("بازگردانی پیش‌فرض")
        restore.setAutoDefault(False)
        restore.clicked.connect(lambda: self.set_shortcut(DEFAULT_SHORTCUT))
        self.content.addWidget(restore, alignment=Qt.AlignRight | Qt.AlignAbsolute)
        self.add_actions("انصراف", primary="ذخیره")
        self.set_shortcut(current)

    def set_shortcut(self, shortcut):
        self.letter.setCurrentText(shortcut.letter)
        for key, checkbox in self.modifiers.items():
            checkbox.setChecked(key in shortcut.modifiers)
        self.validation.hide()

    def accept(self):
        try:
            modifiers = frozenset(key for key, box in self.modifiers.items() if box.isChecked())
            self.save(Shortcut(self.letter.currentText(), modifiers))
        except (OSError, ValueError) as error:
            self.validation.setText(str(error))
            self.validation.show()
        else:
            super().accept()
