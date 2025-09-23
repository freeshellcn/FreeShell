# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['FreeShell.py'],
    pathex=[],
    binaries=[],
    datas=[('resources', 'resources'),(".venv/Lib/site-packages/PySide6/translations/qtbase_zh_CN.qm", "translations")],
    hiddenimports=['PySide6.QtWidgets','PySide6.QtCore','PySide6.QtWebEngineWidgets', 'PySide6.QtGui', 'paramiko'],
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
    name='FreeShell',
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
    icon=['resources\\image\\logo.ico'],
    version='version.txt'
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FreeShell',
)
