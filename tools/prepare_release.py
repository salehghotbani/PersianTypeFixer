"""Generate the Windows icon and a manifest for the current build environment."""

import importlib.metadata
import json
import os
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

from app_version import VERSION
from main import TrayApplication


def main():
    if sys.platform != "win32" or struct.calcsize("P") != 8:
        raise SystemExit("Release builds require 64-bit Python on Windows.")
    assets = ROOT / "build" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    app = QApplication([])
    font = Path(os.environ["SystemRoot"]) / "Fonts" / "segoeui.ttf"
    if QFontDatabase.addApplicationFont(str(font)) < 0:
        raise RuntimeError("Could not load the Windows font for the application icon.")
    icon = TrayApplication.create_app_icon(True)
    if not icon.pixmap(64, 64).save(str(assets / "app.ico"), "ICO"):
        raise RuntimeError("Could not write the Windows application icon.")
    manifest = {
        "application": "Persian Typo Fixer",
        "version": VERSION,
        "platform": "windows-x64",
        "python": sys.version.split()[0],
        "dependencies": {
            name: importlib.metadata.version(name)
            for name in ("PySide6-Essentials", "shiboken6", "PyInstaller", "pyinstaller-hooks-contrib")
        },
    }
    (assets / "build-info.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Prepared Windows resources for v{VERSION}")


if __name__ == "__main__":
    main()
