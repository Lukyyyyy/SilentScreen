# Silent Screen

Windows 10/11 下的静默截图工具，使用 Python 编写。安装包下载与快速上手见[项目首页](../README.md)。

## 功能

- 全局快捷键截图，支持在设置窗口中自定义
- 支持鼠标左键长按两次进行区域截图，可在设置中关闭
- 截取快捷键触发时鼠标所在屏幕
- 截图后自动保存为 PNG
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

区域截图方式：

- 第一次鼠标左键按住至少 `2` 秒，记录截图区域左上角顶点
- 第二次鼠标左键按住至少 `2` 秒，记录截图区域右下角顶点并立即截图
- 两次长按间隔超过 `2` 秒会自动重置，需重新记录第一个顶点

## 说明

- 当前版本仅保存为 PNG
- “无感截图”指不弹窗、不抢焦点、不使用剪贴板、不发声，不能承诺对所有录屏或安全软件绝对不可检测

## 打包为 .exe

在 Windows 上进入 `windows/` 目录后执行：

```powershell
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean SilentScreen.spec
```

产物为 `dist/SilentScreen.exe`。
