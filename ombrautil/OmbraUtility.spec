# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all

# Resolve icon path relative to this spec file (PyInstaller injects SPEC)
SPEC_DIR = os.path.dirname(os.path.abspath(SPEC))
ICON_PATH = os.path.normpath(os.path.join(SPEC_DIR, 'icon.ico'))
if not os.path.isfile(ICON_PATH):
    raise SystemExit('Icon not found: %s' % ICON_PATH)

# Bundle icon so the window can use it at runtime (taskbar/title bar)
datas = [(ICON_PATH, ".")]
binaries = []
hiddenimports = []
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]


a = Analysis(
    ['OmbraUtility.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

VERSION_FILE = os.path.join(SPEC_DIR, 'version_info.txt')
EXE_KW = dict(
    name='Ombra Utility Pro',
    icon=ICON_PATH,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
if os.path.isfile(VERSION_FILE):
    EXE_KW['version'] = VERSION_FILE

# One-file exe: scripts + binaries + datas all go into EXE (no COLLECT)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    **EXE_KW,
)
