"""Persist the app's appearance preference without changing the system theme."""

from PySide6.QtCore import QObject, QSettings, Qt, Signal
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication

THEMES = (("system", "مطابق سیستم"), ("light", "روشن"), ("dark", "تیره"))


class Appearance(QObject):
    changed = Signal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        mode = settings.value("theme", "system", type=str)
        self.mode = mode if mode in dict(THEMES) else "system"

    def set_mode(self, mode):
        if mode == self.mode:
            return
        self.settings.setValue("theme", mode)
        self.settings.sync()
        if self.settings.status() != QSettings.Status.NoError:
            self.settings.setValue("theme", self.mode)
            raise OSError("ذخیرهٔ تم ممکن نشد.")
        self.mode = mode
        self.changed.emit()

    def is_dark(self):
        if self.mode != "system":
            return self.mode == "dark"
        scheme = QApplication.styleHints().colorScheme()
        return scheme == Qt.ColorScheme.Dark or (
            scheme == Qt.ColorScheme.Unknown and QApplication.palette().color(QPalette.Window).lightness() < 128
        )
