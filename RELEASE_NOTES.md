## SilentScreen v1.0.1

本版本修复 Windows 启动后静默退出问题，并统一两端的静默错误处理。

### 修复与改进

- 快捷键被占用时应用继续运行，可在设置中更换快捷键。
- 错误不再自动弹窗或显示托盘气泡，统一显示在设置页“运行状态”。
- 配置损坏或应用数据目录不可写时回退到默认配置，避免启动失败。
- Windows EXE、托盘和窗口改用与 macOS 一致的 SilentScreen 图标。
- Windows 发布包增加启动存活检查，避免上传无法启动的构建产物。

### 下载

| 文件 | 平台 |
| --- | --- |
| `SilentScreen-windows-x64.exe` | Windows 10 / 11，x64 |
| `SilentScreen-macos-arm64.app.zip` | macOS，Apple Silicon（M 系列） |
| `SHA256SUMS.txt` | 附件 SHA-256 校验值 |

Windows 应用尚未做代码签名，系统或企业安全策略仍可能拦截下载或运行。macOS 应用尚未经过 Apple 公证。

完整使用说明见 [README](https://github.com/Lukyyyyy/SilentScreen#readme)。
