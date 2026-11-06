"""Verify both Windows release formats without sending keys to other apps.

Run explicitly on a normal Windows desktop with existing app instances closed.
Each test process is started offscreen and its entire process tree is stopped.
"""

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app_version import VERSION
from windows_api import WindowsAPI


def check_startup(executable):
    native = WindowsAPI()
    # Fail before launch if an existing user application holds the shortcut.
    native.register_hotkey()
    native.unregister_hotkey()
    process = subprocess.Popen(
        [str(executable)], env=dict(os.environ, QT_QPA_PLATFORM="offscreen"),
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    try:
        time.sleep(4)
        if process.poll() is not None:
            raise RuntimeError(f"{executable.name} exited with {process.returncode}")
        try:
            native.register_hotkey()
        except OSError as error:
            if error.winerror != 1409:
                raise
        else:
            native.unregister_hotkey()
            raise RuntimeError(f"{executable.name} did not register Ctrl+Alt+X")
        print(f"Startup and Ctrl+Alt+X passed: {executable.name}", flush=True)
    finally:
        native.unregister_hotkey()
        if process.poll() is None:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        process.wait(timeout=10)
    native.register_hotkey()
    native.unregister_hotkey()


def main():
    release = ROOT / "dist/release"
    prefix = f"PersianTypoFixer-v{VERSION}-windows-x64"
    for line in (release / "SHA256SUMS.txt").read_text(encoding="ascii").splitlines():
        digest, name = line.split("  ", 1)
        with (release / name).open("rb") as source:
            assert hashlib.file_digest(source, "sha256").hexdigest() == digest, name
    staging = ROOT / "build/release-smoke" / VERSION
    single_directory = staging / "standalone"
    single_directory.mkdir(parents=True, exist_ok=True)
    standalone = single_directory / f"{prefix}.exe"
    shutil.copy2(release / standalone.name, standalone)
    assert list(single_directory.iterdir()) == [standalone], "Standalone test folder must contain only the EXE"
    check_startup(standalone)

    with zipfile.ZipFile(release / f"{prefix}-portable.zip") as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert not any("virtualkeyboard" in name.lower() for name in names)
        assert "PersianTypoFixer/_internal/licenses/OpenSSL.txt" in names
        assert "PersianTypoFixer/_internal/licenses/LGPL-3.0.txt" in names
        archive.extractall(staging / "portable")
    check_startup(staging / "portable/PersianTypoFixer/PersianTypoFixer.exe")
    print("Release checksums, standalone EXE, portable ZIP, and notices passed")


if __name__ == "__main__":
    main()
