from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

APP_NAME = "SilentScreen"


@dataclass(slots=True)
class AppSettings:
    hotkey: str
    save_dir: str
    hotkey_enabled: bool = True
    mouse_capture_enabled: bool = False
    mouse_hold_seconds: float = 1.0
    filename_pattern: str = "Screenshot_%Y%m%d_%H%M%S_%f.jpg"


def _app_support_dir() -> Path:
    return Path.home() / "Library" / "Application Support" / APP_NAME


def get_app_dir() -> Path:
    path = _app_support_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_logs_dir() -> Path:
    path = get_app_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_log_file() -> Path:
    return get_logs_dir() / "app.log"


def get_settings_file() -> Path:
    return get_app_dir() / "settings.json"


def get_default_save_dir() -> Path:
    path = Path.home() / "Pictures" / "Screenshots"
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_settings() -> AppSettings:
    return AppSettings(
        hotkey="Meta+Alt+A",  # ⌃⌥A，对应 Windows 版的 Ctrl+Alt+A
        save_dir=str(get_default_save_dir()),
    )


def load_settings() -> AppSettings:
    settings_file = get_settings_file()
    defaults = default_settings()
    if not settings_file.exists():
        save_settings(defaults)
        return defaults

    try:
        data: dict[str, Any] = json.loads(settings_file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("settings.json 顶层必须是对象")
    except (OSError, ValueError) as exc:
        # 配置文件损坏时回退到默认值并重写，避免应用无法启动或丢失全部设置。
        logging.getLogger("silent_screen").warning(
            "设置文件损坏，已重置为默认值: %s (%s)", settings_file, exc
        )
        save_settings(defaults)
        return defaults

    mouse_hold_seconds = data.get("mouse_hold_seconds", defaults.mouse_hold_seconds)
    if (
        type(mouse_hold_seconds) not in (int, float)
        or not 0.1 <= mouse_hold_seconds <= 3600
    ):
        mouse_hold_seconds = defaults.mouse_hold_seconds
    return AppSettings(
        hotkey=str(data.get("hotkey", defaults.hotkey)),
        save_dir=str(data.get("save_dir", defaults.save_dir)),
        hotkey_enabled=data.get("hotkey_enabled", True) is True,
        mouse_capture_enabled=data.get("mouse_capture_enabled", False) is True,
        mouse_hold_seconds=mouse_hold_seconds,
        filename_pattern=str(data.get("filename_pattern", defaults.filename_pattern)),
    )


def save_settings(settings: AppSettings) -> None:
    settings_file = get_settings_file()
    # 先写临时文件再原子替换，避免写入途中崩溃导致 settings.json 损坏。
    fd, tmp_name = tempfile.mkstemp(
        dir=settings_file.parent, prefix=settings_file.name, suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
            tmp_file.write(json.dumps(asdict(settings), ensure_ascii=False, indent=2))
        os.replace(tmp_name, settings_file)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def ensure_writable_directory(path_text: str) -> Path:
    if not path_text.strip():
        raise ValueError("保存路径不能为空。")

    path = Path(path_text).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    if not path.is_dir():
        raise ValueError("保存路径不是目录。")

    try:
        with tempfile.NamedTemporaryFile(dir=path, prefix=".write_test_", delete=True):
            pass
    except OSError as exc:
        raise ValueError(f"保存路径不可写: {path}") from exc

    return path.resolve()
