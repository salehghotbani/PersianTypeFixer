"""X11 global shortcut and clipboard ownership checks for selection conversion."""

from itertools import combinations

from PySide6.QtCore import QSocketNotifier, QTimer
from Xlib import X, XK, display, error
from Xlib.ext import xfixes, xtest

from linux_layouts import standard_mapping


def window_id(window):
    return getattr(window, "id", window)


class LinuxAPI:
    def __init__(self):
        self.mapping, shortcuts = standard_mapping()
        try:
            self.display = display.Display()
        except error.DisplayError as exc:
            raise OSError("اتصال به نشست X11 ممکن نشد.") from exc
        self.registered = False
        self.notifier = None
        try:
            for extension in ("XFIXES", "XTEST", "X-Resource"):
                if not self.display.has_extension(extension):
                    raise OSError(f"افزونهٔ X11 موردنیاز در دسترس نیست: {extension}")
            self.display.xfixes_query_version()
            self.display.res_query_version()
            self.root = self.display.screen().root
            self.clipboard = self.display.intern_atom("CLIPBOARD")
            self.sequence = 0
            self.selection_event = self.display.query_extension("XFIXES").first_event
            self.display.xfixes_select_selection_input(
                self.root, self.clipboard,
                xfixes.XFixesSetSelectionOwnerNotifyMask
                | xfixes.XFixesSelectionWindowDestroyNotifyMask
                | xfixes.XFixesSelectionClientCloseNotifyMask,
            )
            self.keys = {
                letter: self.display.keysym_to_keycode(en) or self.display.keysym_to_keycode(fa) or code
                for letter, (en, fa, code) in shortcuts.items()
            }
            self.ctrl = self.keycode("Control_L") or self.keycode("Control_R")
            modifiers = self.display.get_modifier_mapping()
            alt_keys = {self.keycode("Alt_L"), self.keycode("Alt_R")} - {0}
            alt = next((1 << index for index, codes in enumerate(modifiers) if alt_keys.intersection(codes)), X.Mod1Mask)
            self.modifiers = X.ControlMask | alt
            locks = {self.keycode(key) for key in ("Num_Lock", "Scroll_Lock", "Caps_Lock")} - {0}
            lock_masks = [1 << i for i, codes in enumerate(modifiers)
                          if locks.intersection(codes) and not self.modifiers & (1 << i)]
            self.grabs = [self.modifiers | sum(combo) for size in range(len(lock_masks) + 1)
                          for combo in combinations(lock_masks, size)]
            self.held_keys = {self.keys["x"]}
            self.held_keys.update(code for codes in modifiers for code in codes if code and code not in locks)
            self.display.sync()
        except Exception:
            self.display.close()
            raise

    def keycode(self, name):
        return self.display.keysym_to_keycode(XK.string_to_keysym(name))

    def watch_hotkey(self, callback):
        self.callback = callback
        self.notifier = QSocketNotifier(self.display.fileno(), QSocketNotifier.Read)
        self.notifier.activated.connect(self.drain_events)

    def drain_events(self, *_):
        while self.display.pending_events():
            event = self.display.next_event()
            if event.type == self.selection_event:
                self.sequence += 1
            elif self.registered and event.type == X.KeyPress and event.detail == self.keys["x"]:
                QTimer.singleShot(0, self.callback)

    def register_hotkey(self):
        if self.registered:
            return
        failed = error.CatchError(error.BadAccess)
        for modifiers in self.grabs:
            self.root.grab_key(self.keys["x"], modifiers, False, X.GrabModeAsync, X.GrabModeAsync, onerror=failed)
        self.display.sync()
        if failed.get_error():
            self.release_grabs()
            raise OSError("میان‌بر Ctrl+Alt+X در اختیار برنامهٔ دیگری است.")
        self.registered = True

    def release_grabs(self):
        for modifiers in self.grabs:
            self.root.ungrab_key(self.keys["x"], modifiers)
        self.display.sync()

    def unregister_hotkey(self):
        if self.registered:
            self.registered = False
            self.release_grabs()

    def focused_target(self):
        focus = window_id(self.display.get_input_focus().focus)
        return (focus, focus) if focus not in (X.NONE, X.PointerRoot, self.root.id) else (0, 0)

    def keys_pressed(self):
        state = self.display.query_keymap()
        return any(state[key // 8] & (1 << (key % 8)) for key in self.held_keys)

    def clipboard_sequence(self):
        self.display.sync()
        self.drain_events()
        return self.sequence

    def copy_belongs_to(self, target):
        owner = window_id(self.display.get_selection_owner(self.clipboard))
        if not owner:
            return False
        # Qt and GTK own CLIPBOARD with a hidden window on the same X connection.
        return any(
            owner & ~client.resource_mask == client.resource_base
            and target[1] & ~client.resource_mask == client.resource_base
            for client in self.display.res_query_clients().clients
        )

    def send_shortcut(self, letter):
        if not self.ctrl:
            raise OSError("کلید کنترل در X11 پیدا نشد.")
        key = self.keys[letter]
        for event, code in ((X.KeyPress, self.ctrl), (X.KeyPress, key),
                            (X.KeyRelease, key), (X.KeyRelease, self.ctrl)):
            xtest.fake_input(self.display, event, code)
        self.display.flush()

    def layout_mapping(self, _):
        return self.mapping

    def close(self):
        if self.notifier:
            self.notifier.setEnabled(False)
        self.display.close()
