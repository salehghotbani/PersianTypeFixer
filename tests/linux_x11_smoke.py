"""Exercise the global shortcut against a separate Qt editor under Xvfb."""

import ctypes
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import time

from PySide6.QtWidgets import QApplication, QPlainTextEdit
from Xlib import X
from Xlib.ext import xtest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from linux_api import LinuxAPI
from linux_session import SingleInstance, StartupPreference


def switch_layout(group):
    x11 = ctypes.CDLL("libX11.so.6")
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XkbLockGroup.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint]
    x11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
    connection = x11.XOpenDisplay(None)
    assert connection
    try:
        assert x11.XkbLockGroup(connection, 0x0100, group)
        x11.XSync(connection, 0)
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


def main():
    subprocess.run(["setxkbmap", "-layout", "us,ir"], check=True)
    app = QApplication([])
    editor = QPlainTextEdit()
    editor.show()
    app.processEvents()
    native = LinuxAPI()
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

        process = subprocess.Popen(command)
        try:
            def hotkey_taken():
                try:
                    native.register_hotkey()
                except OSError:
                    return True
                native.unregister_hotkey()
                return False

            wait_for(app, process, hotkey_taken, "The tray did not register Ctrl+Alt+X")
            for group, original, corrected in ((0, "sghl", "سلام"), (1, "سلام", "sghl")):
                switch_layout(group)
                editor.setPlainText(original)
                editor.selectAll()
                app.clipboard().setText("prior clipboard")
                app.processEvents()
                keycodes = [native.ctrl, native.keycode("Alt_L"), native.keys["x"]]
                for code in keycodes:
                    xtest.fake_input(native.display, X.KeyPress, code)
                for code in reversed(keycodes):
                    xtest.fake_input(native.display, X.KeyRelease, code)
                native.display.flush()
                wait_for(app, process, lambda: editor.toPlainText() == corrected,
                         f"Selection was not converted for XKB group {group}")
                wait_for(app, process, lambda: app.clipboard().text() == "prior clipboard",
                         "The original clipboard was not restored")
        finally:
            process.terminate()
            process.wait(timeout=5)
            native.close()
    print("X11 global shortcut, both directions, clipboard restoration, and XDG autostart passed")


if __name__ == "__main__":
    main()
