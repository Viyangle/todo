# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all


pyside_datas, pyside_binaries, pyside_hiddenimports = collect_all("PySide6")
project_datas = [
    ('app/data/philosopher_quotes.json', 'app/data'),
    ('app/data/tarot_cards.json', 'app/data'),
]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=pyside_binaries,
    datas=pyside_datas + project_datas,
    hiddenimports=pyside_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Todo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Todo',
)
