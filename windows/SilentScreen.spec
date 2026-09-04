# -*- mode: python ; coding: utf-8 -*-

import site


def _safe_getusersitepackages():
    try:
        path = site._get_path(site.USER_BASE) if hasattr(site, "_get_path") else site.getusersitepackages()
        if path:
            import pathlib
            candidate = pathlib.Path(path)
            if candidate.exists() and candidate.is_dir():
                return str(candidate)
    except (OSError, PermissionError):
        pass
    return ""


site.getusersitepackages = _safe_getusersitepackages

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='SilentScreen',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
