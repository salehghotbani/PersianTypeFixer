"""Small, typed Win32 boundary. No global keyboard hook or worker thread."""

import ctypes
import sys
from ctypes import wintypes as w
from functools import lru_cache

from PySide6.QtCore import QAbstractNativeEventFilter

from shortcut import DEFAULT_SHORTCUT

HOTKEY_ID = 0x5054
WM_HOTKEY = 0x0312
MOD_NOREPEAT = 0x4000
MODIFIER_MASKS = {"Alt": 0x0001, "Ctrl": 0x0002, "Shift": 0x0004}
KEYEVENTF_KEYUP = 0x0002
ULONG_PTR = ctypes.c_size_t


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", w.WORD), ("wScan", w.WORD), ("dwFlags", w.DWORD),
        ("time", w.DWORD), ("dwExtraInfo", ULONG_PTR),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", w.LONG), ("dy", w.LONG), ("mouseData", w.DWORD),
        ("dwFlags", w.DWORD), ("time", w.DWORD), ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", w.DWORD), ("wParamL", w.WORD), ("wParamH", w.WORD)]


class INPUTUNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("data",)
    _fields_ = [("type", w.DWORD), ("data", INPUTUNION)]


class GUITHREADINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", w.DWORD), ("flags", w.DWORD),
        ("hwndActive", w.HWND), ("hwndFocus", w.HWND),
        ("hwndCapture", w.HWND), ("hwndMenuOwner", w.HWND),
        ("hwndMoveSize", w.HWND), ("hwndCaret", w.HWND),
        ("rcCaret", w.RECT),
    ]


class WindowsAPI:
    def __init__(self):
        if sys.platform != "win32":
            raise OSError("This application requires Windows 10 or later.")
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        signatures = {
            "RegisterHotKey": ([w.HWND, ctypes.c_int, w.UINT, w.UINT], w.BOOL),
            "UnregisterHotKey": ([w.HWND, ctypes.c_int], w.BOOL),
            "GetForegroundWindow": ([], w.HWND),
            "GetWindowThreadProcessId": ([w.HWND, ctypes.POINTER(w.DWORD)], w.DWORD),
            "GetGUIThreadInfo": ([w.DWORD, ctypes.POINTER(GUITHREADINFO)], w.BOOL),
            "GetAsyncKeyState": ([ctypes.c_int], w.SHORT),
            "GetClipboardSequenceNumber": ([], w.DWORD),
            "GetClipboardOwner": ([], w.HWND),
            "SendInput": ([w.UINT, ctypes.POINTER(INPUT), ctypes.c_int], w.UINT),
            "GetKeyboardLayout": ([w.DWORD], w.HKL),
            "GetKeyboardLayoutList": ([ctypes.c_int, ctypes.POINTER(w.HKL)], ctypes.c_int),
            "LoadKeyboardLayoutW": ([w.LPCWSTR, w.UINT], w.HKL),
            "UnloadKeyboardLayout": ([w.HKL], w.BOOL),
            "MapVirtualKeyExW": ([w.UINT, w.UINT, w.HKL], w.UINT),
            "ToUnicodeEx": ([w.UINT, w.UINT, ctypes.POINTER(w.BYTE),
                             w.LPWSTR, ctypes.c_int, w.UINT, w.HKL], ctypes.c_int),
        }
        for name, (arguments, result) in signatures.items():
            function = getattr(self.user32, name)
            function.argtypes = arguments
            function.restype = result
        self.registered = False
        self.shortcut = DEFAULT_SHORTCUT
        self.last_persian_layout = None

    def register_hotkey(self, shortcut=DEFAULT_SHORTCUT):
        if not self.registered:
            mask = MOD_NOREPEAT | sum(MODIFIER_MASKS[key] for key in shortcut.modifiers)
            if not self.user32.RegisterHotKey(None, HOTKEY_ID, mask, ord(shortcut.letter)):
                raise ctypes.WinError(ctypes.get_last_error())
            self.shortcut = shortcut
            self.registered = True

    def unregister_hotkey(self):
        if self.registered:
            if not self.user32.UnregisterHotKey(None, HOTKEY_ID):
                raise ctypes.WinError(ctypes.get_last_error())
            self.registered = False

    def focused_target(self) -> tuple[int, int]:
        window = self.user32.GetForegroundWindow()
        if not window:
            return (0, 0)
        thread = self.user32.GetWindowThreadProcessId(window, None)
        info = GUITHREADINFO(cbSize=ctypes.sizeof(GUITHREADINFO))
        if not self.user32.GetGUIThreadInfo(thread, ctypes.byref(info)):
            return (0, 0)
        return (window, info.hwndFocus or 0)

    def keys_pressed(self) -> bool:
        # Wait rather than synthesize key-up for keys the user still holds.
        return any(self.user32.GetAsyncKeyState(key) & 0x8000
                   for key in (0x10, 0x11, 0x12, 0x5B, 0x5C, ord(self.shortcut.letter)))

    def clipboard_sequence(self) -> int:
        return self.user32.GetClipboardSequenceNumber()

    def copy_belongs_to(self, target: tuple[int, int]) -> bool:
        owner = self.user32.GetClipboardOwner()
        if not owner:
            return False
        source_pid, target_pid = w.DWORD(), w.DWORD()
        self.user32.GetWindowThreadProcessId(owner, ctypes.byref(source_pid))
        self.user32.GetWindowThreadProcessId(target[0], ctypes.byref(target_pid))
        return bool(source_pid.value and source_pid.value == target_pid.value)

    def send_shortcut(self, letter: str):
        # Release a matching global grab until the conversion finishes so the
        # target receives the synthesized Ctrl+C or Ctrl+V.
        if self.registered and self.shortcut.conflicts_with_copy_or_paste(letter):
            self.unregister_hotkey()
        key = ord(letter.upper())
        events = (INPUT * 4)()
        for event, (vk, flags) in zip(events, (
            (0x11, 0), (key, 0), (key, KEYEVENTF_KEYUP), (0x11, KEYEVENTF_KEYUP),
        )):
            event.type = 1
            event.ki = KEYBDINPUT(wVk=vk, dwFlags=flags)
        sent = self.user32.SendInput(4, events, ctypes.sizeof(INPUT))
        if sent != 4:
            error = ctypes.get_last_error()
            # Recover injected key-down events if only part was accepted.
            releases = (INPUT * 2)()
            for event, vk in zip(releases, (key, 0x11)):
                event.type = 1
                event.ki = KEYBDINPUT(wVk=vk, dwFlags=KEYEVENTF_KEYUP)
            self.user32.SendInput(2, releases, ctypes.sizeof(INPUT))
            raise OSError(error, "ارسال کلیدها ممکن نشد؛ سطح دسترسی برنامه مقصد را بررسی کنید.")

    def layout_mapping(self, window: int) -> dict[str, str]:
        thread = self.user32.GetWindowThreadProcessId(window, None)
        active = self.user32.GetKeyboardLayout(thread)
        count = self.user32.GetKeyboardLayoutList(0, None)
        layouts = (w.HKL * count)()
        count = self.user32.GetKeyboardLayoutList(count, layouts)
        persian = [layout for layout in layouts[:count] if layout & 0xFFFF == 0x0429]
        if active and active & 0xFFFF == 0x0429:
            chosen = active
        elif self.last_persian_layout in persian:
            chosen = self.last_persian_layout
        else:
            chosen = persian[0] if persian else None
        if chosen:
            self.last_persian_layout = chosen
            return dict(self._read_mapping(chosen))
        # Do not activate or persist a layout if Persian is not installed.
        chosen = self.user32.LoadKeyboardLayoutW("00000429", 0)
        if not chosen:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            return dict(self._read_mapping(chosen))
        finally:
            self.user32.UnloadKeyboardLayout(chosen)

    @lru_cache(maxsize=8)
    def _read_mapping(self, layout: int) -> tuple[tuple[str, str], ...]:
        # US QWERTY keys. Bit 2 leaves the user's dead-key state untouched.
        keys = [(ord(char.upper()), char, char.upper()) for char in "abcdefghijklmnopqrstuvwxyz"]
        keys += [(ord(char), char, shifted) for char, shifted in zip("0123456789", ")!@#$%^&*(")]
        keys += [(vk, plain, shifted) for vk, plain, shifted in (
            (0xBA, ";", ":"), (0xBB, "=", "+"), (0xBC, ",", "<"),
            (0xBD, "-", "_"), (0xBE, ".", ">"), (0xBF, "/", "?"),
            (0xC0, "`", "~"), (0xDB, "[", "{"), (0xDC, "\\", "|"),
            (0xDD, "]", "}"), (0xDE, "'", '"'),
        )]
        mapping = {}
        for shifted in (False, True):
            state = (w.BYTE * 256)()
            if shifted:
                state[0x10] = 0x80
            for vk, plain, upper in keys:
                buffer = ctypes.create_unicode_buffer(8)
                scan = self.user32.MapVirtualKeyExW(vk, 0, layout)
                length = self.user32.ToUnicodeEx(vk, scan, state, buffer, 8, 4, layout)
                if length > 0:
                    mapping[upper if shifted else plain] = buffer[:length]
        return tuple(mapping.items())


class HotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def nativeEventFilter(self, event_type, message):
        if event_type in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            event = w.MSG.from_address(int(message))
            if event.message == WM_HOTKEY and event.wParam == HOTKEY_ID:
                self.callback()
                return True, 0
        return False, 0
