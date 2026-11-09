"""Edit the global shortcut in the settings page."""

from string import ascii_uppercase

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from shortcut import DEFAULT_SHORTCUT, MODIFIERS, Shortcut
from update_dialogs import label


class ShortcutEditor(QWidget):
    def __init__(self, current, save):
        super().__init__()
        content = QVBoxLayout(self)
        content.setContentsMargins(0, 0, 0, 0)
        hint = label(
            "یک حرف از چیدمان انگلیسی و دست‌کم یکی از کلیدهای Ctrl، Alt یا Shift را انتخاب کنید.",
            "description",
        )
        hint.setWordWrap(True)
        content.addWidget(hint)
        self.save = save
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
        content.addLayout(row)

        self.validation = label("", "validation")
        self.validation.setWordWrap(True)
        self.validation.hide()
        content.addWidget(self.validation)
        actions = QHBoxLayout()
        apply = QPushButton("ذخیرهٔ میان‌بر")
        apply.setObjectName("primary")
        apply.setAutoDefault(False)
        apply.clicked.connect(self.apply_shortcut)
        actions.addWidget(apply)
        restore = QPushButton("بازگردانی پیش‌فرض")
        restore.setAutoDefault(False)
        restore.clicked.connect(lambda: self.set_shortcut(DEFAULT_SHORTCUT))
        actions.addWidget(restore)
        actions.addStretch()
        content.addLayout(actions)
        self.set_shortcut(current)

    def set_shortcut(self, shortcut):
        self.letter.setCurrentText(shortcut.letter)
        for key, checkbox in self.modifiers.items():
            checkbox.setChecked(key in shortcut.modifiers)
        self.validation.hide()

    def apply_shortcut(self):
        try:
            modifiers = frozenset(key for key, box in self.modifiers.items() if box.isChecked())
            self.save(Shortcut(self.letter.currentText(), modifiers))
        except (OSError, ValueError) as error:
            self.validation.setText(str(error))
            self.validation.show()
        else:
            self.validation.hide()
