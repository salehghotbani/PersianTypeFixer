"""Per-user Windows logon preference shared with the installer."""

from pathlib import Path
import subprocess
import sys
import winreg

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "PersianTypoFixer"


def startup_command():
    executable = Path(sys.executable).resolve()
    if getattr(sys, "frozen", False):
        return subprocess.list2cmdline([str(executable)])
    pythonw = executable.with_name("pythonw.exe")
    return subprocess.list2cmdline([
        str(pythonw if pythonw.exists() else executable),
        str(Path(__file__).resolve().with_name("main.py")),
    ])


class StartupPreference:
    def __init__(self, key_path=RUN_KEY):
        self.key_path = key_path

    def is_enabled(self):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.key_path) as key:
                value, kind = winreg.QueryValueEx(key, VALUE_NAME)
                return kind == winreg.REG_SZ and bool(value)
        except FileNotFoundError:
            return False

    def set_enabled(self, enabled):
        if enabled:
            command = startup_command()
            if len(command) > 260:
                raise OSError("مسیر برنامه برای اجرای خودکار طولانی است؛ برنامه را در مسیر کوتاه‌تری نصب کنید.")
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, self.key_path,
                                    access=winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, command)
        else:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.key_path,
                                    access=winreg.KEY_SET_VALUE) as key:
                    winreg.DeleteValue(key, VALUE_NAME)
            except FileNotFoundError:
                pass
