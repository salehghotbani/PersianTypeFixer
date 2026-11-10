"""Create the x86-64 Debian or RPM package from the same Linux bundle."""

import argparse
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
    "libgl1", "libglib2.0-0t64 | libglib2.0-0", "libice6", "libsm6", "libssl3t64 | libssl3",
    "libwayland-client0", "libwayland-cursor0", "libwayland-egl1", "libx11-6", "libx11-xcb1",
    "libxcb-cursor0", "libxcb-icccm4", "libxcb-image0", "libxcb-keysyms1", "libxcb-randr0",
    "libxcb-render-util0", "libxcb-shape0", "libxcb-shm0", "libxcb-sync1", "libxcb-xfixes0",
    "libxcb-xkb1", "libxext6", "libxkbcommon-x11-0", "libxkbcommon0", "libxrender1", "xkb-data",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rpm", action="store_true", help="Build the Fedora RPM")
    args = parser.parse_args()
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise SystemExit("Build the Linux packages on Linux x86-64.")
    version = METADATA["VERSION"]
    output = ROOT / "dist/release"
    output.mkdir(parents=True, exist_ok=True)
    desktop = ROOT / "packaging" / f"{DESKTOP_ID}.desktop"
    subprocess.run(["desktop-file-validate", str(desktop)], check=True)
    with TemporaryDirectory(prefix="package-", dir=ROOT / "build") as directory:
        package = Path(directory) / "payload"
        package.mkdir()
        os.chmod(package, 0o755)
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
        if args.rpm:
            build_rpm(Path(directory), package, version, output)
            return
        control = package / "DEBIAN/control"
        control.parent.mkdir()
        size = sum(path.stat().st_size for path in package.rglob("*") if path.is_file())
        control.write_text(
            f"Package: persiantypefixer\nVersion: {version}\nArchitecture: amd64\n"
            f"Maintainer: {METADATA['PUBLISHER']} <salehghotbani@users.noreply.github.com>\n"
            f"Section: utils\nPriority: optional\nInstalled-Size: {(size + 1023) // 1024}\n"
            f"Depends: {', '.join(DEPENDENCIES)}\nHomepage: {METADATA['PROJECT_URL']}\n"
            "Recommends: xdg-desktop-portal, libglib2.0-bin\n"
            "Description: Persian and English keyboard layout fixer\n"
            " Correct selected text in X11 or in a Wayland session with a compatible desktop portal.\n",
            encoding="utf-8",
        )
        subprocess.run(["dpkg-deb", "--root-owner-group", "--build", str(package),
                        str(output / f"PersianTypoFixer-v{version}-linux-amd64.deb")], check=True)


def build_rpm(work, payload, version, output):
    spec = ROOT / "packaging/fedora.spec"
    subprocess.run([
        "rpmbuild", "-bb", "--define", f"_topdir {work}",
        "--define", f"app_version {version}", "--define", f"app_payload {payload}", str(spec),
    ], check=True)
    package = work / "RPMS" / "x86_64" / f"persiantypefixer-{version}-1.x86_64.rpm"
    shutil.copyfile(package, output / f"PersianTypoFixer-v{version}-linux-x86_64.rpm")


if __name__ == "__main__":
    main()
