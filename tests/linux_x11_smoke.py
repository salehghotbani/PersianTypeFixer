"""Exercise the global shortcut against a separate Qt editor under Xvfb."""

import ctypes
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import time

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QPlainTextEdit
from Xlib import X
from Xlib.ext import xtest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from linux_api import LinuxAPI, window_id
from linux_session import SingleInstance, StartupPreference
from shortcut import DEFAULT_SHORTCUT, MODIFIERS, Shortcut


class XkbState(ctypes.Structure):
    _fields_ = [
        ("group", ctypes.c_ubyte), ("locked_group", ctypes.c_ubyte),
        ("base_group", ctypes.c_ushort), ("latched_group", ctypes.c_ushort),
        *[(name, ctypes.c_ubyte) for name in (
            "mods", "base_mods", "latched_mods", "locked_mods", "compat_state",
            "grab_mods", "compat_grab_mods", "lookup_mods", "compat_lookup_mods",
        )],
        ("ptr_buttons", ctypes.c_ushort),
    ]


def switch_layout(group):
    x11 = ctypes.CDLL("libX11.so.6")
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XkbLockGroup.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint]
    x11.XkbGetState.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.POINTER(XkbState)]
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    connection = x11.XOpenDisplay(None)
    assert connection
    try:
        assert x11.XkbLockGroup(connection, 0x0100, group)
        state = XkbState()
        assert x11.XkbGetState(connection, 0x0100, ctypes.byref(state)) == 0
        assert state.group == group, f"XKB group {group} was requested, but {state.group} is active"
    finally:
        x11.XCloseDisplay(connection)


def wait_for(app, process, condition, message):
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        app.processEvents()
        if process.poll() is not None:
            raise RuntimeError(f"Application exited with status {process.returncode}")
        if condition():
            return
        time.sleep(0.025)
    raise RuntimeError(message)


def exercise(app, editor, native, command, shortcut, cases):
    process = subprocess.Popen([*command, "--verbose"])
    try:
        def hotkey_taken():
            try:
                native.register_hotkey(shortcut)
            except OSError:
                return True
            native.unregister_hotkey()
            return False

        wait_for(app, process, hotkey_taken, f"The tray did not register {shortcut}")
        for group, original, corrected in cases:
            switch_layout(group)
            editor.setPlainText(original)
            editor.selectAll()
            prior = f"prior clipboard for {shortcut} in XKB group {group}"
            # Start with a separate owner, so Qt must claim the selection when
            # the editor receives Ctrl+C, even on a coarse X server clock.
            subprocess.run(["xclip", "-selection", "clipboard", "-in"],
                           input=prior.encode(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           check=True, timeout=2)
            app.processEvents()
            assert editor.hasFocus() and editor.textCursor().hasSelection()
            prior_owner = window_id(native.display.get_selection_owner(native.clipboard))
            assert prior_owner and not native.copy_belongs_to(native.focused_target())
            keycodes = [native.keycode(f"{key.replace('Ctrl', 'Control')}_L")
                        for key in MODIFIERS if key in shortcut.modifiers]
            keycodes.append(native.keys[shortcut.letter.lower()])
            for code in keycodes:
                xtest.fake_input(native.display, X.KeyPress, code)
            native.display.sync()
            time.sleep(0.04)
            for code in reversed(keycodes):
                xtest.fake_input(native.display, X.KeyRelease, code)
            native.display.flush()
            wait_for(app, process, lambda: editor.toPlainText() == corrected,
                     f"{shortcut} did not convert the selection for XKB group {group}")

            # Read through a separate X11 client to bypass Qt's clipboard cache.
            def restored():
                owner = window_id(native.display.get_selection_owner(native.clipboard))
                if not owner or owner == prior_owner:
                    return False
                result = subprocess.run(
                    ["xclip", "-selection", "clipboard", "-out"],
                    capture_output=True, encoding="utf-8", timeout=2,
                )
                return result.returncode == 0 and result.stdout == prior

            wait_for(app, process, restored, f"Clipboard not restored for {shortcut} and XKB group {group}")
            wait_for(app, process, hotkey_taken, f"The tray did not restore {shortcut} after conversion")
    finally:
        process.terminate()
        process.wait(timeout=5)


def main():
    app = QApplication([])
    # Keep a client connected while setxkbmap exits so the X server retains the map.
    subprocess.run(["setxkbmap", "-layout", "us,ir", "-option", ""], check=True)
    editor = QPlainTextEdit()
    editor.show()
    app.processEvents()
    native = LinuxAPI()
    assert native.mapping["x"] == "ط", "The default hotkey must use the X / ط key"
    window = native.display.create_resource_object("window", int(editor.winId()))
    window.set_input_focus(X.RevertToParent, X.CurrentTime)
    native.display.sync()
    editor.setFocus()
    command = sys.argv[1:] or [sys.executable, str(ROOT / "main.py")]

    with TemporaryDirectory() as directory:
        os.environ["XDG_RUNTIME_DIR"] = directory
        os.environ["XDG_CONFIG_HOME"] = directory
        first = SingleInstance()
        duplicate = SingleInstance()
        assert not first.already_running and duplicate.already_running
        duplicate.close()
        first.close()
        startup = StartupPreference()
        assert not startup.is_enabled()
        startup.set_enabled(True)
        subprocess.run(["desktop-file-validate", str(startup.path)], check=True)
        startup.set_enabled(False)
        assert not startup.is_enabled()

        cases = ((0, "sghl", "سلام"), (1, "سلام", "sghl"))
        settings = QSettings(str(Path(directory) / "ghotbani.ir/PersianTypoFixer.conf"), QSettings.Format.IniFormat)
        try:
            exercise(app, editor, native, command, DEFAULT_SHORTCUT, cases)
            for shortcut, case in (
                (Shortcut("J", frozenset({"Alt", "Shift"})), cases[1]),
                (Shortcut("C", frozenset({"Ctrl"})), cases[0]),
                (Shortcut("V", frozenset({"Ctrl"})), cases[1]),
            ):
                settings.setValue("shortcut", str(shortcut))
                settings.sync()
                exercise(app, editor, native, command, shortcut, (case,))
        finally:
            native.close()
    print("Default and custom X11 shortcuts, both directions, clipboard restoration, and XDG autostart passed")


if __name__ == "__main__":
    main()
