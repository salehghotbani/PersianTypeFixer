# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path
import runpy

from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo, StringFileInfo, StringStruct, StringTable,
    VarFileInfo, VarStruct, VSVersionInfo,
)

root = Path(SPECPATH)
version = runpy.run_path(str(root / 'app_version.py'))['VERSION']
version_tuple = tuple(int(part) for part in version.split('.')) + (0,)
version_info = VSVersionInfo(
    ffi=FixedFileInfo(filevers=version_tuple, prodvers=version_tuple,
                      mask=0x3f, flags=0, OS=0x40004, fileType=1,
                      subtype=0, date=(0, 0)),
    kids=[
        StringFileInfo([StringTable('040904B0', [
            StringStruct('CompanyName', 'Seyed Mohammad Saleh Ghotbani'),
            StringStruct('FileDescription', 'Persian and English keyboard layout fixer'),
            StringStruct('FileVersion', version),
            StringStruct('ProductName', 'Persian Typo Fixer'),
            StringStruct('ProductVersion', version),
            StringStruct('LegalCopyright', 'Copyright (c) 2026 Seyed Mohammad Saleh Ghotbani'),
        ])]),
        VarFileInfo([VarStruct('Translation', [1033, 1200])]),
    ],
)


# Prefer Windows system DLLs over unrelated tools on PATH. In particular,
# Poppler/Conda can supply an incompatible icuuc.dll that breaks QtCore at
# startup. PyInstaller recognizes System32 DLLs and leaves them to Windows.
system_directory = Path(os.environ['SystemRoot']) / 'System32'
os.environ['PATH'] = str(system_directory) + os.pathsep + os.environ.get('PATH', '')


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[(str(root / name), '.') for name in
           ('README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md', 'CHANGELOG.md')]
          + [(str(root / 'licenses'), 'licenses'),
             (str(root / 'build/assets/build-info.json'), '.')],
    hiddenimports=['PySide6.support.deprecated'],
    hookspath=[str(root / 'packaging/hooks')],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PySide6.QtNetwork', 'PySide6.QtQml', 'PySide6.QtQuick',
              'PySide6.QtPdf', 'PySide6.QtOpenGL'],
    noarchive=False,
    optimize=0,
)
# The tray icon uses raster painting; the optional software OpenGL renderer
# is not needed and would add a separate third-party graphics runtime.
a.binaries = [entry for entry in a.binaries
              if Path(entry[0]).name.lower() != 'opengl32sw.dll']
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PersianTypoFixer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(root / 'build/assets/app.ico'),
    version=version_info,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='PersianTypoFixer',
)

standalone = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PersianTypoFixer-Standalone',
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(root / 'build/assets/app.ico'),
    version=version_info,
)
