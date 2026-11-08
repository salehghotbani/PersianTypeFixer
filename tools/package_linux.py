"""Create the Linux amd64 Debian package from the bundled application."""

import os
from pathlib import Path
import platform
import runpy
import shutil
import subprocess
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
METADATA = runpy.run_path(str(ROOT / "app_version.py"))
DESKTOP_ID = "ir.ghotbani.persiantypefixer"
DEPENDENCIES = (
    "ca-certificates", "fonts-dejavu-core", "libdbus-1-3", "libegl1", "libfontconfig1",
    "libgl1", "libglib2.0-0", "libice6", "libsm6", "libssl3", "libx11-6", "libx11-xcb1",
    "libxcb-cursor0", "libxcb-icccm4", "libxcb-image0", "libxcb-keysyms1", "libxcb-randr0",
    "libxcb-render-util0", "libxcb-shape0", "libxcb-shm0", "libxcb-sync1", "libxcb-xfixes0",
    "libxcb-xkb1", "libxext6", "libxkbcommon-x11-0", "libxkbcommon0", "libxrender1", "xkb-data",
)


def main():
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise SystemExit("Build the Debian package on Linux x86-64.")
    version = METADATA["VERSION"]
    output = ROOT / "dist/release"
    output.mkdir(parents=True, exist_ok=True)
    desktop = ROOT / "packaging" / f"{DESKTOP_ID}.desktop"
    subprocess.run(["desktop-file-validate", str(desktop)], check=True)
    with TemporaryDirectory(prefix="deb-", dir=ROOT / "build") as directory:
        package = Path(directory)
        os.chmod(package, 0o755)
        control = package / "DEBIAN/control"
        control.parent.mkdir()
        shutil.copytree(ROOT / "dist/PersianTypoFixer-linux", package / "opt/persiantypefixer")
        for source, destination in (
            (desktop, f"usr/share/applications/{desktop.name}"),
            (ROOT / "docs/assets/icon.svg", f"usr/share/icons/hicolor/scalable/apps/{DESKTOP_ID}.svg"),
            (ROOT / "LICENSE", "usr/share/doc/persiantypefixer/copyright"),
            (ROOT / "THIRD_PARTY_NOTICES.md", "usr/share/doc/persiantypefixer/THIRD_PARTY_NOTICES.md"),
        ):
            target = package / destination
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        size = sum(path.stat().st_size for path in package.rglob("*") if path.is_file())
        control.write_text(
            f"Package: persiantypefixer\nVersion: {version}\nArchitecture: amd64\n"
            f"Maintainer: {METADATA['PUBLISHER']} <salehghotbani@users.noreply.github.com>\n"
            f"Section: utils\nPriority: optional\nInstalled-Size: {(size + 1023) // 1024}\n"
            f"Depends: {', '.join(DEPENDENCIES)}\nHomepage: {METADATA['PROJECT_URL']}\n"
            "Description: Persian and English keyboard layout fixer\n"
            " Correct selected text with a configurable shortcut in an X11 desktop session.\n",
            encoding="utf-8",
        )
        subprocess.run(["dpkg-deb", "--root-owner-group", "--build", str(package),
                        str(output / f"PersianTypoFixer-v{version}-linux-amd64.deb")], check=True)


if __name__ == "__main__":
    main()
