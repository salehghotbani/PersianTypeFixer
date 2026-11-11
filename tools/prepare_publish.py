"""Validate release artifacts and write checksums for every platform."""

import hashlib
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app_version import VERSION


def prepare(directory):
    prefix = f"PersianTypoFixer-v{VERSION}"
    windows = {
        f"{prefix}-windows-x64.exe",
        f"{prefix}-windows-x64-setup.exe",
        f"{prefix}-windows-x64-portable.zip",
        f"{prefix}-windows-x64-notices.zip",
    }
    expected = windows | {
        f"{prefix}-linux-amd64.deb",
        f"{prefix}-linux-x86_64.rpm",
    }
    checksum_file = directory / "SHA256SUMS.txt"
    actual = {path.name for path in directory.iterdir()}
    if actual != expected | {checksum_file.name}:
        raise ValueError(f"Unexpected release files: {actual ^ (expected | {checksum_file.name})}")
    digests = {}
    for name in sorted(expected):
        path = directory / name
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f"Missing or empty release asset: {name}")
        with path.open("rb") as stream:
            digests[name] = hashlib.file_digest(stream, "sha256").hexdigest()
        if path.suffix == ".zip":
            with zipfile.ZipFile(path) as archive:
                if archive.testzip() is not None:
                    raise ValueError(f"Corrupt release archive: {name}")
    original = {}
    for line in checksum_file.read_text(encoding="ascii").splitlines():
        digest, name = line.split(maxsplit=1)
        if name in original or name not in windows:
            raise ValueError(f"Unexpected Windows checksum entry: {name}")
        original[name] = digest
    if original != {name: digests[name] for name in windows}:
        raise ValueError("Windows build checksums do not match the downloaded assets")
    checksum_file.write_text(
        "".join(f"{digest}  {name}\n" for name, digest in sorted(digests.items())),
        encoding="ascii",
    )
    print(f"Validated {len(expected)} release assets for v{VERSION}")


if __name__ == "__main__":
    prepare(Path(sys.argv[1]))
