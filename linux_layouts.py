"""Read the standard US and Iranian physical key mapping from XKB data."""

import ctypes as c


class RuleNames(c.Structure):
    _fields_ = [(name, c.c_char_p) for name in ("rules", "model", "layout", "variant", "options")]


def standard_mapping():
    xkb = c.CDLL("libxkbcommon.so.0")
    pointer = c.c_void_p
    uint = c.c_uint32
    symbols = c.POINTER(uint)
    for name, arguments, result in (
        ("xkb_context_new", [c.c_int], pointer),
        ("xkb_context_unref", [pointer], None),
        ("xkb_keymap_new_from_names", [pointer, c.POINTER(RuleNames), c.c_int], pointer),
        ("xkb_keymap_unref", [pointer], None),
        ("xkb_keymap_min_keycode", [pointer], uint),
        ("xkb_keymap_max_keycode", [pointer], uint),
        ("xkb_keymap_key_get_syms_by_level", [pointer, uint, uint, uint, c.POINTER(symbols)], c.c_int),
        ("xkb_keysym_to_utf32", [uint], uint),
    ):
        function = getattr(xkb, name)
        function.argtypes = arguments
        function.restype = result

    context = xkb.xkb_context_new(0)
    if not context:
        raise OSError("راه‌اندازی XKB ممکن نشد.")
    keymap = None
    try:
        names = RuleNames(b"evdev", b"pc105", b"us,ir", None, None)
        keymap = xkb.xkb_keymap_new_from_names(context, c.byref(names), 0)
        if not keymap:
            raise OSError("چیدمان فارسی و انگلیسی XKB پیدا نشد.")
        mapping = {}
        shortcuts = {}
        codes = range(xkb.xkb_keymap_min_keycode(keymap), xkb.xkb_keymap_max_keycode(keymap) + 1)
        for level in (0, 1):
            for code in codes:
                english, persian = (key_symbol(xkb, keymap, code, group, level) for group in (0, 1))
                source = xkb.xkb_keysym_to_utf32(english)
                destination = xkb.xkb_keysym_to_utf32(persian)
                if 32 < source < 127 and destination >= 32:
                    mapping.setdefault(chr(source), chr(destination))
                    if chr(source) in "cvx":
                        shortcuts[chr(source)] = (english, persian, code)
        return mapping, shortcuts
    finally:
        if keymap:
            xkb.xkb_keymap_unref(keymap)
        xkb.xkb_context_unref(context)


def key_symbol(xkb, keymap, code, group, level):
    result = c.POINTER(c.c_uint32)()
    if xkb.xkb_keymap_key_get_syms_by_level(keymap, code, group, level, c.byref(result)) == 1:
        return result[0]
    return 0
