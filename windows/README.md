# Silent Screen

Windows 10/11 下的静默截图工具，使用 Python 编写。安装包下载与快速上手见[项目首页](../README.md)。

## 功能

- 全局快捷键截图，支持在设置窗口中自定义
- 支持鼠标左键长按自动截取鼠标所在屏幕，默认 1 秒，支持自定义秒数
- 快捷键和鼠标可分别启用或禁用，默认只启用快捷键
- 截取快捷键触发时鼠标所在屏幕
- 截图后自动保存为高质量 JPEG
- 支持自定义保存目录
- 系统托盘常驻运行

## 运行环境

- Windows 10 / 11
- Python 3.12+

## 安装依赖

```powershell
python -m pip install -r requirements.txt
```

## 启动

```powershell
python app.py
```

首次启动会在用户配置目录下创建配置和日志：

- 配置：`%LOCALAPPDATA%\SilentScreen\settings.json`
- 日志：`%LOCALAPPDATA%\SilentScreen\logs\app.log`

默认截图保存目录：

- `%USERPROFILE%\Pictures\Screenshots`

默认快捷键：

- `Ctrl+Alt+A`

鼠标截图方式：

- 在设置中启用鼠标左键长按截屏，时长可设为 `0.1` 至 `3600` 秒，支持小数，默认 `1` 秒
- 左键按住达到时长后自动截图，无需松开；每次按住只截一次，松开再按可再次截图
- 不拦截鼠标操作，长按仍可能触发当前应用的选择或拖动
- 设置窗口打开期间暂停触发，保存或取消后恢复；启用时已按住的左键需先松开再按
- 原“两次长按区域截图”已替换；升级旧配置后默认只启用快捷键，保留原快捷键和保存路径

## 说明

- 当前版本仅保存为 JPEG（质量 90）
- “无感截图”指不弹窗、不抢焦点、不使用剪贴板、不发声，不能承诺对所有录屏或安全软件绝对不可检测

## 打包为 .exe

在 Windows 上进入 `windows/` 目录后执行：

```powershell
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean SilentScreen.spec
```

产物为 `dist/SilentScreen.exe`。
