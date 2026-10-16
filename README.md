<div align="center">
  <img src="macos/assets/silentscreen-logo-v3.png" alt="SilentScreen 图标" width="112" />
  <h1>SilentScreen</h1>
  <p>按下快捷键，把屏幕保存为图片。</p>
  <p>Windows / macOS · 本地保存 · 高质量 JPEG · MIT</p>
</div>

SilentScreen 是一个常驻系统托盘或菜单栏的轻量截图工具。截图成功后直接保存到指定目录，不弹出预览、不抢焦点、不写入剪贴板、不播放提示音，适合工作记录、资料整理和连续截图。

## 功能

- **全局快捷键**：在其他应用中也能触发截图，支持自定义组合键。
- **自动保存**：输出高质量 JPEG，兼顾清晰度与文件体积；文件名包含时间戳，支持自定义保存目录。
- **托盘操作**：通过菜单修改设置、打开截图目录、查看日志或退出。
- **本地处理**：无需登录账号，应用不提供截图上传或消息推送功能。
- **鼠标长按截图**：可选启用左键长按，达到自定义时长后自动截图，每次按住只截一次。
- **独立开关**：快捷键和鼠标可分别启用或禁用，默认只启用快捷键。

| 功能 | Windows | macOS |
| --- | --- | --- |
| 默认快捷键 | `Ctrl + Alt + A` | `Control + Option + A`（`⌃⌥A`） |
| 全屏截图 | 快捷键触发时鼠标所在屏幕 | 快捷键触发时鼠标所在屏幕 |
| 鼠标截图 | 左键长按，默认 1 秒，可自定义 | 左键长按，默认 1 秒，可自定义 |
| 默认触发方式 | 仅启用快捷键 | 仅启用快捷键 |
| 常驻位置 | 系统托盘 | 菜单栏，不显示 Dock 图标 |
| 截图权限 | 无应用内授权步骤 | 需要屏幕录制权限 |

这里的“静默”指截图时减少打扰。应用自身错误不会自动弹窗，可在“设置”的运行状态中查看；macOS 仍可能显示系统授权窗口或屏幕采集指示。

## 下载与安装

在[Releases](https://github.com/Lukyyyyy/SilentScreen/releases) 页面下载适合设备的附件，无需安装 Python。首个正式版本为 **v1.0.0**，两个平台使用同一版本号发布。

| 平台 | Release 附件 | 使用方式 |
| --- | --- | --- |
| Windows 10 / 11，x64 | `SilentScreen-windows-x64.exe` | 下载后直接运行 |
| macOS，Apple Silicon（M 系列） | `SilentScreen-macos-arm64.app.zip` | 解压，将 `SilentScreen.app` 拖入“应用程序”后打开 |

首版不提供 Windows ARM 或 Intel Mac 安装包。各版本的系统兼容信息见 Release 说明。

### macOS 首次打开

macOS 发布包尚未经过 Apple 公证。如果系统阻止打开，请先确认文件来自本仓库的 Release，再到 **系统设置 → 隐私与安全性** 中查看拦截提示，选择“仍要打开”并按提示确认。

首次截图时，需要授予屏幕录制权限：

1. 按下 `Control + Option + A`，触发授权提示。
2. 在 **系统设置 → 隐私与安全性 → 屏幕录制**（部分系统名为“屏幕与系统音频录制”）中允许 SilentScreen。
3. 完全退出应用并重新打开，然后再次截图。

从源码运行时，请授权启动应用的终端。

## 使用

### 全屏截图

1. 启动应用，在系统托盘或菜单栏找到 SilentScreen。
2. 按下默认快捷键，截图会自动保存为 JPEG。
3. 通过菜单中的“打开截图目录”查看图片。

默认保存目录为用户目录下的 `Pictures/Screenshots`。在“设置”中可以修改保存位置和截图快捷键。

### 鼠标左键长按截图（Windows / macOS）

1. 在“设置”中勾选“启用鼠标左键长按截屏”。
2. 设置“长按时长”，单位为秒，支持 `0.1` 至 `3600` 秒及小数，默认 `1` 秒。
3. 按住左键，达到时长后自动截取鼠标所在屏幕，无需松开；持续按住只截一次，松开后可再次长按。

快捷键和鼠标可分别启用或禁用，也可同时启用或同时禁用。默认仅启用快捷键；两者都关闭后，仍可通过托盘或菜单栏打开设置重新启用。设置窗口打开期间暂停触发，保存或取消后恢复。

鼠标监听不拦截左键，长按仍可能在当前应用中触发选择或拖动；截图时会包含这些操作的当前画面。应用启用鼠标截图时，已经按住的左键需先松开再按。检测以约 50 毫秒间隔轮询，触发时间会有少量延迟。

Windows 原有的“两次左键长按区域截图”已替换为上述全屏截图。旧配置升级后默认只启用快捷键，原快捷键和保存目录保留。

## 常见问题

**启动后为什么没有窗口？**

应用默认常驻托盘或菜单栏。Windows 图标可能位于托盘的折叠区域；点击图标菜单可打开设置。

**按快捷键没有生成图片怎么办？**

确认应用正在运行、保存目录可写，检查快捷键是否被其他软件占用，并通过“打开日志”查看错误。macOS 还需确认屏幕录制权限已生效。

**macOS 已授权，为什么仍提示权限不足？**

先完全退出并重新打开应用。如果更新或重新打包后仍有问题，在屏幕录制权限中移除旧条目，重新添加当前的 `SilentScreen.app`，再重启应用。

**能否一次截取所有显示器，或编辑截图？**

当前全屏截图每次只保存一个屏幕，不提供拼接、标注、编辑或录屏功能。

## 从源码运行

下载仓库源码并解压，或使用 Git 克隆仓库。以下命令均从项目根目录开始执行。

### Windows

需要 Windows 10 / 11 和 Python 3.12 或更高版本。在 PowerShell 中执行：

```powershell
cd windows
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

示例使用 Python 3.12；如安装的是其他受支持版本，请相应调整 `py` 的版本参数。

### macOS

源码使用 Python 3.10 或更高版本；Python、PySide6 和系统版本需相互兼容。

```bash
cd macos
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

更多平台说明见 [Windows 文档](windows/README.md)和 [macOS 文档](macos/README.md)。

## 本地打包

请在目标平台上打包，并先完成对应平台的依赖安装。以下命令从项目根目录开始执行。

### Windows → EXE

```powershell
cd windows
.\.venv\Scripts\python.exe -m pip install pyinstaller
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean SilentScreen.spec
```

产物为 `windows/dist/SilentScreen.exe`。

### macOS → APP

```bash
cd macos
.venv/bin/python -m pip install pyinstaller
.venv/bin/python -m PyInstaller --noconfirm --clean SilentScreenMac.spec
```

产物为 `macos/dist/SilentScreen.app`。打包架构取决于 Python 运行环境；构建首版 ARM64 应用时，请使用 Apple Silicon 原生 Python。

`macos/build.sh` 额外使用本机钥匙串中的 `SilentScreen Local Code Signing` 证书签名，适合维护者本机使用。普通源码构建可直接执行上述 PyInstaller 命令，无需该证书；本地签名不等同于 Apple 公证。

## 配置与日志

| 文件 | Windows | macOS |
| --- | --- | --- |
| 配置 | `%USERPROFILE%\AppData\Local\SilentScreen\settings.json` | `~/Library/Application Support/SilentScreen/settings.json` |
| 日志 | `%USERPROFILE%\AppData\Local\SilentScreen\logs\app.log` | `~/Library/Application Support/SilentScreen/logs/app.log` |
| 默认截图目录 | `%USERPROFILE%\Pictures\Screenshots` | `~/Pictures/Screenshots` |

应用首次运行时创建配置和日志目录。优先通过设置窗口修改配置；手动编辑配置文件前，请先退出应用。日志可能包含本机路径，提交问题反馈前请移除个人信息。

## 项目结构

```text
SilentScreen/
├── README.md
├── LICENSE
├── windows/             # Windows 应用与 PyInstaller 配置
└── macos/               # macOS 应用、图标与打包配置
```

两端分别维护平台实现，共享相同的使用理念。界面使用 PySide6；Windows 使用 Win32 全局快捷键与 mss 截图，macOS 使用 Carbon 全局快捷键与系统截图工具。

## 参与贡献

欢迎提交 Issue 和 Pull Request。

- **反馈问题**：提供系统版本、处理器架构、应用版本、复现步骤和相关日志。
- **提出功能**：描述具体使用场景，以及现有功能无法满足的部分。
- **提交代码**：让改动聚焦于一个问题；涉及平台功能时，在目标系统检查启动、快捷键、截图保存、设置和退出流程。

提交信息遵循 Conventional Commits，例如 `fix: 修复截图保存失败的问题`。请勿提交虚拟环境、打包产物、个人截图、真实配置或签名私钥。

## 许可证

本项目采用 [MIT 许可证](LICENSE)。第三方依赖遵循各自的许可证。
