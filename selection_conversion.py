"""Asynchronous copy/convert/paste, confined to the original focused control."""

import time
import uuid

from PySide6.QtCore import QMimeData, QObject, QTimer, Signal

from layout_conversion import convert_text


class QtClipboard:
    def __init__(self, clipboard):
        self.clipboard = clipboard

    def snapshot(self):
        original = self.clipboard.mimeData()
        saved = QMimeData()
        if original is not None:
            for format_name in original.formats():
                saved.setData(format_name, original.data(format_name))
            # Qt's image/color variants are not always serialized by data().
            if original.hasImage():
                saved.setImageData(original.imageData())
            if original.hasColor():
                saved.setColorData(original.colorData())
        return saved

    def text(self):
        return self.clipboard.text()

    def set_text(self, text):
        self.clipboard.setText(text)
        if self.clipboard.text() != text:
            raise OSError("کلیپ‌بورد در دسترس نیست؛ دوباره تلاش کنید.")

    def restore(self, snapshot):
        self.clipboard.setMimeData(snapshot)


class SelectionConverter(QObject):
    status_changed = Signal(str)
    finished = Signal()

    def __init__(self, native, clipboard, parent=None, clock=time.monotonic):
        super().__init__(parent)
        self.native = native
        self.clipboard = clipboard
        self.clock = clock
        self.timer = QTimer(self)
        self.timer.setInterval(25)
        self.timer.timeout.connect(self.advance)
        self.phase = None
        self.original = None
        self.owned_sequence = None
        self.target = (0, 0)
        self.deadline = 0.0
        self.marker = ""
        self.converted = ""

    @property
    def busy(self):
        return self.phase is not None

    def start(self):
        if self.busy:
            return
        self.target = self.native.focused_target()
        if not all(self.target):
            self.status_changed.emit("ابتدا متن را در یک کادر قابل ویرایش انتخاب کنید.")
            return
        self.phase = "release"
        self.deadline = self.clock() + 3.0
        self.timer.start()
        self.advance()

    def advance(self):
        if not self.busy:
            return
        try:
            self._advance()
        except Exception as error:
            self.finish(f"اصلاح متن انجام نشد: {error}")

    def _advance(self):
        if self.phase == "restore":
            if self.clock() >= self.deadline:
                self.finish()
            return
        if self.native.focused_target() != self.target:
            self.finish("پنجره یا کادر مقصد تغییر کرد؛ اصلاح لغو شد.")
            return
        if self.phase == "release":
            if self.native.keys_pressed():
                if self.clock() >= self.deadline:
                    self.finish("کلیدهای میان‌بر را رها کنید و دوباره تلاش کنید.")
                return
            self.original = self.clipboard.snapshot()
            self.marker = "__PERSIAN_TYPO_FIXER_" + uuid.uuid4().hex
            self.clipboard.set_text(self.marker)
            self.owned_sequence = self.native.clipboard_sequence()
            if self.native.focused_target() != self.target or self.native.keys_pressed():
                self.finish("وضعیت کادر مقصد یا کلیدها تغییر کرد؛ دوباره تلاش کنید.")
                return
            self.phase = "copy"
            self.deadline = self.clock() + 2.0
            self.native.send_shortcut("c")
            return
        if self.phase == "copy":
            if self.native.clipboard_sequence() == self.owned_sequence:
                if self.clock() >= self.deadline:
                    self.finish("متن دریافت نشد؛ متن را انتخاب کنید و دسترسی برنامه مقصد را بررسی کنید.")
                return
            if not self.native.copy_belongs_to(self.target):
                self.finish("کلیپ‌بورد در برنامه دیگری تغییر کرد؛ اصلاح لغو شد.")
                return
            copied = self.clipboard.text()
            # Reading delayed clipboard data can itself advance the sequence.
            self.owned_sequence = self.native.clipboard_sequence()
            if not copied or copied == self.marker:
                self.finish("متنی انتخاب نشده است.")
                return
            self.converted = convert_text(copied, self.native.layout_mapping(self.target[0]))
            if self.converted == copied:
                self.finish("متن انتخاب‌شده قابل تبدیل نیست.")
                return
            self.phase = "paste"
            self.deadline = self.clock() + 2.0
            return
        if self.phase == "paste":
            if self.native.clipboard_sequence() != self.owned_sequence:
                self.finish("کلیپ‌بورد تغییر کرد؛ اصلاح لغو شد.")
                return
            if self.native.keys_pressed():
                if self.clock() >= self.deadline:
                    self.finish("کلیدهای کنترل را رها کنید و دوباره تلاش کنید.")
                return
            self.clipboard.set_text(self.converted)
            self.owned_sequence = self.native.clipboard_sequence()
            if self.native.focused_target() != self.target or self.native.keys_pressed():
                self.finish("وضعیت کادر مقصد یا کلیدها تغییر کرد؛ دوباره تلاش کنید.")
                return
            self.native.send_shortcut("v")
            self.phase = "restore"
            self.deadline = self.clock() + 1.0
            self.status_changed.emit("متن اصلاح شد.")

    def cancel(self, force=False):
        if self.busy and (force or self.phase != "restore"):
            self.finish("اصلاح متن لغو شد.")

    def finish(self, message=None):
        self.timer.stop()
        try:
            # A fresh user copy wins even when its text happens to be identical.
            if (self.original is not None and self.owned_sequence is not None
                    and self.native.clipboard_sequence() == self.owned_sequence):
                self.clipboard.restore(self.original)
        except Exception as error:
            message = f"بازگرداندن کلیپ‌بورد ممکن نشد: {error}"
        finally:
            self.phase = None
            self.original = None
            self.owned_sequence = None
            self.marker = ""
            self.converted = ""
        if message:
            self.status_changed.emit(message)
        self.finished.emit()
