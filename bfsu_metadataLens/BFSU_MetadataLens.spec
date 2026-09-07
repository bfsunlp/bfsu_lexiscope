# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = [
    ('assets/app.png', 'assets'),
    ('assets/app_2048.png', 'assets'),
    ('assets/app.ico', 'assets'),
    ('templates/system', 'templates/system'),
]
datas += collect_data_files('customtkinter')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=['pypdf', 'openpyxl', 'openai'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BFSU_MetadataLens',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='assets/app.ico',
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=True, name='BFSU_MetadataLens')
