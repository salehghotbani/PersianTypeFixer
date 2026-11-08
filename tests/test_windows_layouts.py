from contextlib import contextmanager
from string import ascii_uppercase
import sys
import unittest

from layout_conversion import convert_text


@unittest.skipUnless(sys.platform == "win32", "Requires Windows keyboard layouts")
class WindowsLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from windows_api import WindowsAPI
        cls.native = WindowsAPI()

    @contextmanager
    def keyboard_layout(self, name):
        from ctypes import wintypes as w
        api = self.native.user32
        active = api.GetKeyboardLayout(0)
        count = api.GetKeyboardLayoutList(0, None)
        existing = (w.HKL * count)()
        api.GetKeyboardLayoutList(count, existing)
        handle = api.LoadKeyboardLayoutW(name, 0)
        self.assertTrue(handle, f"Could not load {name}")
        try:
            yield handle
            self.assertEqual(api.GetKeyboardLayout(0), active, "Reading a layout must not activate it")
        finally:
            if handle not in existing:
                api.UnloadKeyboardLayout(handle)

    def mapping_for(self, name):
        with self.keyboard_layout(name) as handle:
            return dict(self.native._read_mapping(handle))

    def test_physical_shortcut_keys_match_both_persian_layouts(self):
        map_key = self.native.user32.MapVirtualKeyExW
        with self.keyboard_layout("00000409") as english:
            # MAPVK_VK_TO_VSC gets the physical position of each English letter.
            scans = {letter: map_key(ord(letter), 0, english) for letter in ascii_uppercase}
            self.assertTrue(all(scans.values()))
        for name in ("00000429", "00050429"):
            with self.subTest(layout=name), self.keyboard_layout(name) as persian:
                self.assertEqual(dict(self.native._read_mapping(persian))["x"], "ط")
                for letter, scan in scans.items():
                    # MAPVK_VSC_TO_VK_EX gives the virtual key registered by the app.
                    self.assertEqual(map_key(scan, 3, persian), ord(letter), letter)

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
