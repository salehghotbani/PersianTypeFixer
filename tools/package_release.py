"""Package the already-built executables, notices, and SHA-256 checksums."""

import hashlib
from pathlib import Path
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app_version import VERSION


def main():
    dist = ROOT / "dist"
    output = dist / "release"
    output.mkdir(parents=True, exist_ok=True)
    prefix = f"PersianTypoFixer-v{VERSION}-windows-x64"
    standalone = output / f"{prefix}.exe"
    shutil.copy2(dist / "PersianTypoFixer-Standalone.exe", standalone)
    portable = output / f"{prefix}-portable.zip"
    application = dist / "PersianTypoFixer"
    with zipfile.ZipFile(portable, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(application.rglob("*")):
            if path.is_file():
                archive.write(path, Path("PersianTypoFixer") / path.relative_to(application))
        for name in ("README.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "CHANGELOG.md"):
            archive.write(ROOT / name, Path("PersianTypoFixer") / name)
    documents = output / f"{prefix}-notices.zip"
    with zipfile.ZipFile(documents, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in ("README.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "CHANGELOG.md"):
            archive.write(ROOT / name, name)
        for path in sorted((ROOT / "licenses").rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(ROOT))
        archive.write(ROOT / "build/assets/build-info.json", "build-info.json")
    installer = output / f"{prefix}-setup.exe"
    if not installer.is_file():
        raise RuntimeError("Build the Windows installer before packaging a release.")
    assets = (standalone, portable, documents, installer)
    checksums = []
    for path in assets:
        with path.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        checksums.append(f"{digest}  {path.name}")
        print(f"{path.name}: {path.stat().st_size:,} bytes")
    (output / "SHA256SUMS.txt").write_text("\n".join(checksums) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
