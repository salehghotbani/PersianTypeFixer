# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, copy_metadata

root = Path(SPECPATH).parent
a = Analysis(
    [str(root / 'main.py')],
    pathex=[str(root)],
    datas=[(str(root / name), '.') for name in ('README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md')]
          + [(str(root / 'licenses'), 'licenses')]
          + copy_metadata('python-xlib') + copy_metadata('six'),
    hiddenimports=['PySide6.support.deprecated'] + collect_submodules('Xlib'),
    excludes=['PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtPdf', 'PySide6.QtOpenGL',
              'windows_api', 'single_instance', 'startup'],
)
# Use the user's system X11 libraries and only the Qt platform plugins we support.
a.exclude_system_libraries()
a.binaries = [entry for entry in a.binaries if '/plugins/' not in entry[0]
              or Path(entry[0]).parent.name in ('platformthemes', 'tls', 'iconengines', 'imageformats')
              or Path(entry[0]).name in ('libqxcb.so', 'libqoffscreen.so')]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='PersianTypoFixer', upx=False)
coll = COLLECT(exe, a.binaries, a.datas, name='PersianTypoFixer-linux', upx=False)
