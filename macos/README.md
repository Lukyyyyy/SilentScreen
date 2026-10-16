# Silent Screen (macOS)

macOS 版静默截图工具：常驻菜单栏，全局快捷键全屏截图并保存为高质量 JPEG。无弹窗、不抢焦点、不写剪贴板、不出声。

由 Windows 版（[windows](../windows/)）移植，支持全局快捷键和鼠标左键长按全屏截图。

## 功能

- 全局快捷键截取鼠标所在屏幕（默认 `⌃⌥A`，可在设置窗口自定义）
- 可选启用鼠标左键长按截屏，时长以秒为单位自定义，默认 1 秒
- 快捷键和鼠标可分别启用或禁用，默认只启用快捷键
- 截图后自动保存为高质量 JPEG，文件名含时间戳
- 菜单栏托盘常驻：设置 / 打开截图目录 / 打开日志 / 退出
- 无 Dock 图标（LSUIElement）
- 单实例运行

## 运行环境

- Apple Silicon macOS（在 Python 3.14 上开发测试；具体兼容版本取决于 Python 和 PySide6）
- Python 3.10+

## 安装与启动（源码）

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

安装包下载与快速上手见[项目首页](../README.md)。

## 打包为 .app

```bash
./build.sh
# 产物: dist/SilentScreen.app
```

构建使用登录钥匙串中的 `SilentScreen Local Code Signing` 本地代码签名证书。请保留同一证书和私钥用于后续构建；首次从临时签名切换到此证书后，需要重新授予录屏权限。此签名供本机自用。

## 首次使用：屏幕录制权限

首次截屏时，应用会检查实际录屏权限并请求授权；权限未生效时会记录在“设置”的运行状态中，不会保存只有壁纸的截图。需要：

1. 打开 系统设置 → 隐私与安全性 → 屏幕录制
2. 勾选 SilentScreen（源码运行时勾选你的终端应用，如 iTerm2/Terminal）
3. 完全退出本应用并重新启动

若已勾选却仍提示权限未生效（例如重新打包后），请移除旧授权条目，重新添加当前的 `SilentScreen.app`，然后重启应用。

授权后即可截到完整画面。另外说明两点系统行为，无法从应用侧规避：

- 截屏时菜单栏会出现屏幕采集指示图标
- macOS 15+ 会定期提醒你重新确认该应用的屏幕录制权限

## 配置与日志

- 配置：`~/Library/Application Support/SilentScreen/settings.json`
- 日志：`~/Library/Application Support/SilentScreen/logs/app.log`
- 默认截图目录：`~/Pictures/Screenshots`

## 快捷键说明

- 默认 `⌃⌥A`（对应 Windows 版的 Ctrl+Alt+A），在设置窗口的输入框中直接按下想要的组合键即可更换
- 修饰键对应关系（Qt macOS 惯例）：`Ctrl` = ⌘ Command，`Meta` = ⌃ Control，`Alt` = ⌥ Option，`Shift` = ⇧ Shift
- 实现基于 Carbon `RegisterEventHotKey`，全局生效、不抢焦点，且不需要"辅助功能"等额外权限

## 鼠标左键长按截屏

在设置中勾选“启用鼠标左键长按截屏”，可设置 `0.1` 至 `3600` 秒（支持小数，默认 `1` 秒）。按住达到时长时自动截取鼠标所在屏幕，无需松开，每次按住只截一次。松开再按可再次截图。快捷键和鼠标开关相互独立，可同时启用或同时禁用。

监听不会拦截鼠标操作，长按仍可能在当前应用中选择或拖动。设置窗口打开期间暂停触发，保存或取消后恢复；启用鼠标截图时已按住的左键需先松开再按。旧配置升级后默认只启用快捷键，保留原快捷键和保存目录。

## 与 Windows 版的差异

| | Windows 版 | macOS 版 |
|---|---|---|
| 全局快捷键 | Win32 `RegisterHotKey` | Carbon `RegisterEventHotKey`（ctypes） |
| 截屏 | mss | macOS 系统 `screencapture`（静默、鼠标所在屏幕） |
| 鼠标截图 | 左键长按自动截屏 | 左键长按自动截屏 |
| 配置目录 | `%LOCALAPPDATA%\SilentScreen` | `~/Library/Application Support/SilentScreen` |
| 系统限制 | — | 需授予屏幕录制权限；菜单栏有采集指示 |

## 已知限制

- 每次只截触发时鼠标所在的一块屏幕
- 截图分辨率由 macOS 系统截图工具决定（Retina 屏幕可输出高分辨率图像）
