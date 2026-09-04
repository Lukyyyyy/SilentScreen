## SilentScreen v1.0.0

首个正式版本，同时提供 Windows x64 和 macOS Apple Silicon 应用。

### 功能

- 全局快捷键截图，自动以时间戳命名并保存为 PNG。
- 自定义快捷键与保存目录，通过托盘或菜单栏访问设置和日志。
- Windows 支持全屏截图和两次鼠标长按区域截图。
- macOS 截取鼠标所在屏幕，常驻菜单栏。
- 截图保存在本地，无账号登录或推送功能。

### 下载

| 文件 | 平台 |
| --- | --- |
| `SilentScreen-windows-x64.exe` | Windows 10 / 11，x64 |
| `SilentScreen-macos-arm64.app.zip` | macOS，Apple Silicon（M 系列） |
| `SHA256SUMS.txt` | 附件 SHA-256 校验值 |

下载应用无需安装 Python。macOS 包在 macOS 15 ARM64 环境构建；其他系统版本的兼容性取决于打包依赖，不代表已逐一验证。

### 首次运行

Windows 下载 EXE 后直接运行。macOS 解压后将应用拖入“应用程序”，打开并按提示授予屏幕录制权限，完全退出后重新启动。

macOS 应用未经 Apple 公证；若系统拦截，请确认下载来源后在“系统设置 → 隐私与安全性”中允许打开。Windows 应用未做代码签名，也可能显示系统安全提示。

两端应用已由维护者验证；CI 另行检查源码导入、打包结果及 macOS 架构和签名。默认快捷键为 Windows `Ctrl + Alt + A`、macOS `Control + Option + A`。

完整使用说明见 [README](https://github.com/Lukyyyyy/SilentScreen#readme)。
