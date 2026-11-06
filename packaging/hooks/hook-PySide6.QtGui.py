"""Collect only the platform plugins needed by this raster tray application."""

from pathlib import Path

from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
binaries = [
    (source, destination) for source, destination in binaries
    if "/plugins/" not in destination.replace("\\", "/")
    or Path(source).name.lower() in {"qwindows.dll", "qoffscreen.dll"}
]
