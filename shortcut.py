"""The global shortcut shared by the settings and both native backends."""

from dataclasses import dataclass
from string import ascii_uppercase

MODIFIERS = ("Ctrl", "Alt", "Shift")


@dataclass(frozen=True)
class Shortcut:
    letter: str
    modifiers: frozenset[str]

    def __post_init__(self):
        if (len(self.letter) != 1 or self.letter not in ascii_uppercase
                or not self.modifiers or self.modifiers.difference(MODIFIERS)):
            raise ValueError("یک حرف و دست‌کم یکی از کلیدهای Ctrl، Alt یا Shift را انتخاب کنید.")

    def __str__(self):
        return "+".join([*(key for key in MODIFIERS if key in self.modifiers), self.letter])

    @classmethod
    def parse(cls, text):
        *modifiers, letter = text.split("+")
        if len(modifiers) != len(set(modifiers)):
            raise ValueError("کلیدهای میان‌بر تکراری هستند.")
        return cls(letter, frozenset(modifiers))

    def conflicts_with_copy_or_paste(self, letter):
        return self.modifiers == {"Ctrl"} and self.letter == letter.upper()


DEFAULT_SHORTCUT = Shortcut("X", frozenset({"Ctrl", "Alt"}))
