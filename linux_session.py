"""Linux session lock and XDG desktop autostart preference."""

import fcntl
import hashlib
import os
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile

from app_version import APP_NAME

DESKTOP_ID = "ir.ghotbani.persiantypefixer"


def xdg_directory(variable, fallback):
    value = Path(os.environ.get(variable, ""))
    return value if value.is_absolute() else Path.home() / fallback


class SingleInstance:
    def __init__(self):
        runtime = xdg_directory("XDG_RUNTIME_DIR", ".cache") / DESKTOP_ID
        runtime.mkdir(mode=0o700, parents=True, exist_ok=True)
        display = os.environ.get("WAYLAND_DISPLAY") or os.environ.get("DISPLAY", "")
        display_id = hashlib.sha256(display.encode()).hexdigest()[:16]
        self.lock = (runtime / f"{display_id}.lock").open("ab")
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.already_running = False
        except BlockingIOError:
            self.already_running = True
        except OSError:
            self.close()
            raise

    def close(self):
        self.lock.close()


def desktop_argument(argument):
    if any(char in argument for char in "\n\r\0"):
        raise OSError("مسیر برنامه برای اجرای خودکار معتبر نیست.")
    # Exec has two escape layers, plus percent-based field codes.
    escaped = argument.replace("\\", "\\\\").replace("%", "%%")
    for char in ('"', '$', '`'):
        escaped = escaped.replace(char, "\\" + char)
    return '"' + escaped.replace("\\", "\\\\") + '"'


class StartupPreference:
    def __init__(self):
        self.path = xdg_directory("XDG_CONFIG_HOME", ".config") / "autostart" / f"{DESKTOP_ID}.desktop"

    def is_enabled(self):
        return self.path.is_file()

    def set_enabled(self, enabled):
        if not enabled:
            self.path.unlink(missing_ok=True)
            return
        arguments = [sys.executable]
        if not getattr(sys, "frozen", False):
            arguments.append(str(Path(__file__).resolve().with_name("main.py")))
        command = " ".join(map(desktop_argument, arguments))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with NamedTemporaryFile("w", encoding="utf-8", dir=self.path.parent, delete=False) as target:
                temporary = Path(target.name)
                target.write(f"[Desktop Entry]\nType=Application\nName={APP_NAME}\nExec={command}\n"
                             f"Icon={DESKTOP_ID}\nTerminal=false\nNoDisplay=true\n")
            temporary.replace(self.path)
        finally:
            if temporary:
                temporary.unlink(missing_ok=True)
