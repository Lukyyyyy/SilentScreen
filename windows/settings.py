from __future__ import annotations

import json
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

APP_NAME = "SilentScreen"


@dataclass(slots=True)
class AppSettings:
    hotkey: str
    save_dir: str
    image_format: str = "png"
    filename_pattern: str = "Screenshot_%Y%m%d_%H%M%S_%f.png"
    monitor_mode: str = "primary"


def _local_appdata_dir() -> Path:
    return Path.home() / "AppData" / "Local" / APP_NAME


def get_app_dir() -> Path:
    path = _local_appdata_dir()
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
        hotkey="Ctrl+Alt+A",
        save_dir=str(get_default_save_dir()),
    )


def load_settings() -> AppSettings:
    settings_file = get_settings_file()
    if not settings_file.exists():
        settings = default_settings()
        save_settings(settings)
        return settings

    data: dict[str, Any] = json.loads(settings_file.read_text(encoding="utf-8"))
    defaults = default_settings()
    return AppSettings(
        hotkey=str(data.get("hotkey", defaults.hotkey)),
        save_dir=str(data.get("save_dir", defaults.save_dir)),
        image_format=str(data.get("image_format", defaults.image_format)).lower(),
        filename_pattern=str(data.get("filename_pattern", defaults.filename_pattern)),
        monitor_mode=str(data.get("monitor_mode", defaults.monitor_mode)),
    )


def save_settings(settings: AppSettings) -> None:
    settings_file = get_settings_file()
    settings_file.write_text(
        json.dumps(asdict(settings), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


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
