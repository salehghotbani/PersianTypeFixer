import unittest

from layout_conversion import EN_TO_FA, convert_text, reverse_mapping


class LayoutConversionTests(unittest.TestCase):
    def test_requested_example_both_directions(self):
        self.assertEqual(convert_text("sghl"), "سلام")
        self.assertEqual(convert_text("سلام"), "sghl")

    def test_english_word_typed_in_persian(self):
        self.assertEqual(convert_text("اثممخ"), "hello")
        self.assertEqual(convert_text("hello"), "اثممخ")

    def test_leading_punctuation_does_not_choose_direction(self):
        self.assertEqual(convert_text("... سلام"), "... sghl")
        self.assertEqual(convert_text("... sghl"), "... سلام")

    def test_whitespace_and_unknown_characters_survive(self):
        self.assertEqual(convert_text("sghl\r\n\t🙂 123"), "سلام\r\n\t🙂 123")

    def test_missing_peh_and_arabic_variants(self):
        self.assertEqual(convert_text("پ"), "\\")
        self.assertEqual(convert_text("كي"), ";d")

    def test_each_unshifted_key_round_trips(self):
        for source, destination in EN_TO_FA.items():
            with self.subTest(key=source):
                self.assertEqual(convert_text(source), destination)
                self.assertEqual(convert_text(destination), source)

    def test_empty_neutral_and_other_scripts_unchanged(self):
        for text in ("", "  \n\t", "123", "./", "🙂", "中文", "Привет"):
            with self.subTest(text=text):
                self.assertEqual(convert_text(text), text)

    def test_mixed_selection_uses_dominant_script(self):
        self.assertEqual(convert_text("a سلام"), "a sghl")
        self.assertEqual(convert_text("sghl س"), "سلام س")

    def test_tied_scripts_use_first_letter(self):
        self.assertEqual(convert_text("s س"), "س س")
        self.assertEqual(convert_text("س s"), "s s")

    def test_shifted_keys_and_standard_layout_can_be_supplied(self):
        mapping = {**EN_TO_FA, "H": "آ", "C": "ژ", "?": "؟", "m": "پ", "B": "\u200c"}
        self.assertEqual(convert_text("Hf?", mapping), "آب؟")
        self.assertEqual(convert_text("آب؟", mapping), "Hf?")
        self.assertEqual(convert_text("m", mapping), "پ")
        self.assertEqual(convert_text("\u200c", mapping), "B")

    def test_reverse_prefers_unshifted_key_and_preserves_words(self):
        mapping = {**EN_TO_FA, "X": "ط", "R": "ريال"}
        self.assertEqual(reverse_mapping(mapping)["ط"], "x")
        self.assertEqual(convert_text("ريال", mapping), "vdhg")


if __name__ == "__main__":
    unittest.main()
