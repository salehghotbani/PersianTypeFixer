import sys
import unittest

from layout_conversion import convert_text


@unittest.skipUnless(sys.platform == "win32", "Requires Windows keyboard layouts")
class WindowsLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from windows_api import WindowsAPI
        cls.native = WindowsAPI()

    def mapping_for(self, name):
        import ctypes
        from ctypes import wintypes as w
        api = self.native.user32
        active = api.GetKeyboardLayout(0)
        count = api.GetKeyboardLayoutList(0, None)
        existing = (w.HKL * count)()
        api.GetKeyboardLayoutList(count, existing)
        handle = api.LoadKeyboardLayoutW(name, 0)
        self.assertTrue(handle, f"Could not load {name}")
        try:
            mapping = dict(self.native._read_mapping(handle))
            self.assertEqual(api.GetKeyboardLayout(0), active, "Reading a layout must not activate it")
            return mapping
        finally:
            if handle not in existing:
                api.UnloadKeyboardLayout(handle)

    def test_classic_windows_persian_including_shift_and_peh(self):
        mapping = self.mapping_for("00000429")
        self.assertEqual(convert_text("sghl", mapping), "سلام")
        self.assertEqual(convert_text("سلام", mapping), "sghl")
        self.assertEqual(convert_text("Hf?", mapping), "آب؟")
        self.assertEqual(convert_text("آب؟", mapping), "Hf?")
        self.assertEqual(mapping["\\"], "پ")
        self.assertEqual(mapping["m"], "ئ")

    def test_standard_windows_persian_including_digits_and_half_space(self):
        mapping = self.mapping_for("00050429")
        self.assertEqual(convert_text("sghl 123", mapping), "سلام ۱۲۳")
        self.assertEqual(convert_text("سلام ۱۲۳", mapping), "sghl 123")
        self.assertEqual(mapping["m"], "پ")
        self.assertEqual(mapping["B"], "\u200c")
        self.assertEqual(convert_text("mB", mapping), "پ\u200c")


if __name__ == "__main__":
    unittest.main()
