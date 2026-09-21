from __future__ import annotations

import ctypes
import ctypes.wintypes
from datetime import datetime
from pathlib import Path

import mss
from PySide6.QtGui import QImage

user32 = ctypes.windll.user32


def cursor_screen_region() -> dict[str, int]:
    cursor = ctypes.wintypes.POINT()
    if not user32.GetCursorPos(ctypes.byref(cursor)):
        raise RuntimeError("无法获取鼠标位置。")

    with mss.mss() as sct:
        for monitor in sct.monitors[1:]:
            if (
                monitor["left"] <= cursor.x < monitor["left"] + monitor["width"]
                and monitor["top"] <= cursor.y < monitor["top"] + monitor["height"]
            ):
                return dict(monitor)
    raise RuntimeError("无法获取鼠标所在屏幕。")


def capture_screen(region: dict[str, int]):
    with mss.mss() as sct:
        return sct.grab(region)


def capture_screen_region(left: int, top: int, right: int, bottom: int):
    return capture_screen(normalize_region(left, top, right, bottom))


def normalize_region(left: int, top: int, right: int, bottom: int) -> dict[str, int]:
    normalized_left = min(left, right)
    normalized_top = min(top, bottom)
    width = abs(right - left) + 1
    height = abs(bottom - top) + 1
    return {
        "left": normalized_left,
        "top": normalized_top,
        "width": width,
        "height": height,
    }


def save_image(image, save_dir: str | Path, filename_pattern: str) -> Path:
    output_dir = Path(save_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = datetime.now().strftime(filename_pattern)
    destination = (output_dir / filename).with_suffix(".jpg")
    if destination.exists():
        destination = output_dir / (
            f"{destination.stem}_{datetime.now().strftime('%f')}{destination.suffix}"
        )

    width, height = image.size
    if not QImage(
        image.rgb, width, height, width * 3, QImage.Format.Format_RGB888
    ).save(str(destination), "JPEG", 90):
        raise RuntimeError("JPEG 截图保存失败。")
    return destination
