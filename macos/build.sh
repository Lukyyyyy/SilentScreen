#!/bin/bash
# 构建 SilentScreen.app
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
fi

if ! .venv/bin/python -c "import PySide6, AppKit" 2>/dev/null; then
    .venv/bin/pip install -r requirements.txt
fi

if ! .venv/bin/python -c "import PyInstaller" 2>/dev/null; then
    .venv/bin/pip install pyinstaller
fi

.venv/bin/pyinstaller --noconfirm --clean SilentScreenMac.spec
# 本机自签名不启用需要 Apple Team ID 的 hardened runtime，也不请求时间戳。
/usr/bin/codesign --force --sign "SilentScreen Local Code Signing" --timestamp=none dist/SilentScreen.app
/usr/bin/codesign --verify --deep --strict dist/SilentScreen.app
echo "构建完成: dist/SilentScreen.app"
