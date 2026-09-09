# -*- mode: python ; coding: utf-8 -*-
# PyInstaller 打包配置：macOS .app（无 Dock 图标，仅菜单栏托盘）

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/silentscreen-logo-v3.png', 'assets'), ('assets/tray-icon.svg', 'assets')],
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
    [],
    exclude_binaries=True,
    name='SilentScreen',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='SilentScreen',
)
app = BUNDLE(
    coll,
    name='SilentScreen.app',
    icon='assets/SilentScreen.icns',
    bundle_identifier='com.silentscreen.mac',
    info_plist={
        'LSUIElement': True,
        'NSHighResolutionCapable': True,
        'NSPrincipalClass': 'NSApplication',
        'CFBundleName': 'SilentScreen',
        'CFBundleDisplayName': 'Silent Screen',
        'CFBundleShortVersionString': '1.0.1',
        'CFBundleVersion': '1.0.1',
    },
)
