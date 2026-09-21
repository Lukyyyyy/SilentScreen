## SilentScreen v1.0.3

本版本将截图改为高质量 JPEG，在保持清晰度的同时显著减小文件体积。

### 修复与改进

- Windows 使用质量 90 的 JPEG 编码保存截图。
- macOS 使用系统原生 JPEG 编码保存截图。
- 旧配置中的 `.png` 文件名会自动迁移为 `.jpg`，无需重置设置。
- 修复 macOS 构建环境不完整时仍继续打包的问题。

### 下载

| 文件 | 平台 |
| --- | --- |
| `SilentScreen-windows-x64.exe` | Windows 10 / 11，x64 |
| `SilentScreen-macos-arm64.app.zip` | macOS，Apple Silicon（M 系列） |
| `SHA256SUMS.txt` | 附件 SHA-256 校验值 |

Windows 应用尚未做代码签名，系统或企业安全策略仍可能拦截下载或运行。macOS 应用尚未经过 Apple 公证。

完整使用说明见 [README](https://github.com/Lukyyyyy/SilentScreen#readme)。
