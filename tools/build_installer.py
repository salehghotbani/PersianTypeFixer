"""Compile the per-user installer with an installed Inno Setup compiler."""
import os
from pathlib import Path
import runpy
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]
version = runpy.run_path(str(root / "app_version.py"))["VERSION"]
candidates = [os.environ.get("ISCC"), shutil.which("ISCC.exe"),
              str(root / "build/tools/InnoSetup/ISCC.exe"),
              r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
              r"C:\Program Files\Inno Setup 7\ISCC.exe"]
compiler = next((p for p in candidates if p and Path(p).is_file()), None)
if not compiler:
    raise SystemExit("Install Inno Setup, or set ISCC to the full path of ISCC.exe.")
subprocess.run([compiler, f"/DAppVersion={version}", str(root / "packaging/installer.iss")], check=True)
