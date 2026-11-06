import unittest

from PySide6.QtCore import QCoreApplication, QMimeData, QUrl
from PySide6.QtGui import QColor, QImage

from layout_conversion import EN_TO_FA
from selection_conversion import QtClipboard, SelectionConverter


class FakeNative:
    def __init__(self):
        self.target = (10, 11)
        self.held = False
        self.sequence = 1
        self.from_target = True
        self.shortcuts = []
        self.error_on = None

    def focused_target(self):
        return self.target

    def keys_pressed(self):
        return self.held

    def clipboard_sequence(self):
        return self.sequence

    def copy_belongs_to(self, target):
        return self.from_target

    def send_shortcut(self, letter):
        if letter == self.error_on:
            raise OSError("input blocked")
        self.shortcuts.append(letter)

    def layout_mapping(self, window):
        return EN_TO_FA


class FakeClipboard:
    def __init__(self, native):
        self.native = native
        self.value = {"text/plain": "original", "text/html": "<b>original</b>"}
        self.restores = 0

    def snapshot(self):
        return dict(self.value)

    def text(self):
        return self.value.get("text/plain", "")

    def set_text(self, text):
        self.value = {"text/plain": text}
        self.native.sequence += 1

    def restore(self, snapshot):
        self.value = snapshot
        self.restores += 1
        self.native.sequence += 1


class SelectionConversionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.now = 10.0
        self.native = FakeNative()
        self.clipboard = FakeClipboard(self.native)
        self.original = self.clipboard.snapshot()
        self.converter = SelectionConverter(self.native, self.clipboard, clock=lambda: self.now)
        self.messages = []
        self.converter.status_changed.connect(self.messages.append)

    def tearDown(self):
        self.converter.cancel(force=True)

    def copied(self, text="sghl"):
        self.clipboard.set_text(text)
        self.converter.advance()

    def prepare_paste(self):
        self.converter.start()
        self.copied()
        self.assertEqual(self.converter.phase, "paste")

    def test_copy_convert_paste_and_restore_all_original_formats(self):
        self.prepare_paste()
        self.converter.advance()
        self.assertEqual(self.clipboard.text(), "سلام")
        self.assertEqual(self.native.shortcuts, ["c", "v"])
        self.assertTrue(self.converter.busy)
        self.now += 1.1
        self.converter.advance()
        self.assertFalse(self.converter.busy)
        self.assertEqual(self.clipboard.value, self.original)

    def test_waits_for_all_hotkey_keys_to_be_released(self):
        self.native.held = True
        self.converter.start()
        self.assertEqual(self.native.shortcuts, [])
        self.assertEqual(self.clipboard.value, self.original)
        self.native.held = False
        self.converter.advance()
        self.assertEqual(self.native.shortcuts, ["c"])

    def test_held_keys_time_out_without_touching_clipboard(self):
        self.native.held = True
        self.converter.start()
        self.now += 3.1
        self.converter.advance()
        self.assertFalse(self.converter.busy)
        self.assertEqual(self.clipboard.value, self.original)

    def test_repeated_hotkeys_are_ignored_while_busy(self):
        self.converter.start()
        self.converter.start()
        self.assertEqual(self.native.shortcuts, ["c"])

    def test_no_selection_does_not_paste_and_restores_clipboard(self):
        self.converter.start()
        self.now += 2.1
        self.converter.advance()
        self.assertEqual(self.native.shortcuts, ["c"])
        self.assertEqual(self.clipboard.value, self.original)
        self.assertFalse(self.converter.busy)

    def test_unconvertible_selection_restores_clipboard(self):
        self.converter.start()
        self.copied("123 🙂")
        self.assertEqual(self.clipboard.value, self.original)
        self.assertEqual(self.native.shortcuts, ["c"])

    def test_empty_or_non_text_selection_restores_clipboard(self):
        self.converter.start()
        self.clipboard.value = {"image/png": b"image"}
        self.native.sequence += 1
        self.converter.advance()
        self.assertEqual(self.clipboard.value, self.original)

    def test_changed_window_before_copy_is_cancelled(self):
        self.native.held = True
        self.converter.start()
        self.native.target = (20, 21)
        self.converter.advance()
        self.assertFalse(self.converter.busy)
        self.assertEqual(self.native.shortcuts, [])

    def test_changed_focused_control_before_paste_is_cancelled(self):
        self.prepare_paste()
        self.native.target = (10, 12)
        self.converter.advance()
        self.assertEqual(self.native.shortcuts, ["c"])
        self.assertEqual(self.clipboard.value, self.original)

    def test_focus_change_during_clipboard_write_does_not_send_copy(self):
        write = self.clipboard.set_text

        def change_focus(text):
            write(text)
            self.native.target = (20, 21)

        self.clipboard.set_text = change_focus
        self.converter.start()
        self.assertEqual(self.native.shortcuts, [])
        self.assertEqual(self.clipboard.value, self.original)

    def test_focus_change_during_clipboard_write_does_not_send_paste(self):
        self.prepare_paste()
        write = self.clipboard.set_text

        def change_focus(text):
            write(text)
            self.native.target = (20, 21)

        self.clipboard.set_text = change_focus
        self.converter.advance()
        self.assertEqual(self.native.shortcuts, ["c"])
        self.assertEqual(self.clipboard.value, self.original)

    def test_copy_from_another_app_is_not_pasted_or_overwritten(self):
        self.converter.start()
        self.native.from_target = False
        self.copied("user copied something else")
        self.assertFalse(self.converter.busy)
        self.assertEqual(self.clipboard.text(), "user copied something else")
        self.assertEqual(self.native.shortcuts, ["c"])

    def test_user_copy_before_paste_wins(self):
        self.prepare_paste()
        self.clipboard.set_text("new copy")
        self.converter.advance()
        self.assertEqual(self.clipboard.text(), "new copy")
        self.assertEqual(self.native.shortcuts, ["c"])

    def test_identical_user_copy_after_paste_wins_by_sequence(self):
        self.prepare_paste()
        self.converter.advance()
        self.clipboard.set_text("سلام")
        self.now += 1.1
        self.converter.advance()
        self.assertEqual(self.clipboard.text(), "سلام")
        self.assertEqual(self.clipboard.restores, 0)

    def test_copy_input_failure_restores_and_clears_busy(self):
        self.native.error_on = "c"
        self.converter.start()
        self.assertEqual(self.clipboard.value, self.original)
        self.assertFalse(self.converter.busy)

    def test_paste_input_failure_restores_and_clears_busy(self):
        self.prepare_paste()
        self.native.error_on = "v"
        self.converter.advance()
        self.assertEqual(self.clipboard.value, self.original)
        self.assertFalse(self.converter.busy)

    def test_second_modifier_press_delays_paste_then_times_out(self):
        self.prepare_paste()
        self.native.held = True
        self.converter.advance()
        self.assertEqual(self.native.shortcuts, ["c"])
        self.now += 2.1
        self.converter.advance()
        self.assertEqual(self.clipboard.value, self.original)
        self.assertFalse(self.converter.busy)

    def test_disable_cancels_pending_copy(self):
        self.converter.start()
        self.converter.cancel()
        self.assertEqual(self.clipboard.value, self.original)
        self.assertFalse(self.converter.busy)

    def test_cancel_after_paste_waits_before_restoring(self):
        self.prepare_paste()
        self.converter.advance()
        self.converter.cancel()
        self.assertTrue(self.converter.busy)
        self.assertEqual(self.clipboard.text(), "سلام")
        self.now += 1.1
        self.converter.advance()
        self.assertEqual(self.clipboard.value, self.original)

    def test_missing_foreground_control_is_ignored(self):
        self.native.target = (0, 0)
        self.converter.start()
        self.assertFalse(self.converter.busy)
        self.assertEqual(self.native.shortcuts, [])

    def test_next_conversion_after_timeout_starts_cleanly(self):
        self.converter.start()
        self.now += 2.1
        self.converter.advance()
        self.prepare_paste()
        self.converter.advance()
        self.assertEqual(self.native.shortcuts, ["c", "c", "v"])


class ClipboardSnapshotTests(unittest.TestCase):
    def test_snapshot_is_independent_and_preserves_rich_formats(self):
        class Clipboard:
            def mimeData(self):
                return self.mime

        clipboard = Clipboard()
        clipboard.mime = QMimeData()
        clipboard.mime.setText("original")
        clipboard.mime.setHtml("<b>original</b>")
        clipboard.mime.setUrls([QUrl("file:///C:/example.txt")])
        clipboard.mime.setData("application/custom", b"opaque")
        saved = QtClipboard(clipboard).snapshot()
        clipboard.mime.setText("changed")
        self.assertEqual(saved.text(), "original")
        self.assertEqual(saved.html(), "<b>original</b>")
        self.assertEqual(saved.urls(), [QUrl("file:///C:/example.txt")])
        self.assertEqual(bytes(saved.data("application/custom")), b"opaque")

    def test_snapshot_preserves_image_and_color_variants(self):
        class Clipboard:
            def mimeData(self):
                return self.mime

        clipboard = Clipboard()
        clipboard.mime = QMimeData()
        image = QImage(2, 2, QImage.Format_ARGB32)
        image.fill(QColor("red"))
        clipboard.mime.setImageData(image)
        clipboard.mime.setColorData(QColor("blue"))
        saved = QtClipboard(clipboard).snapshot()
        self.assertEqual(saved.imageData(), image)
        self.assertEqual(saved.colorData(), QColor("blue"))


if __name__ == "__main__":
    unittest.main()
