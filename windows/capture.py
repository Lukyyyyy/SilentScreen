from __future__ import annotations

from datetime import datetime
from pathlib import Path

import mss
import mss.tools


def capture_primary_screen():
    with mss.mss() as sct:
        primary_monitor = sct.monitors[1]
        return sct.grab(primary_monitor)


def capture_screen_region(left: int, top: int, right: int, bottom: int):
    region = normalize_region(left, top, right, bottom)
    with mss.mss() as sct:
        return sct.grab(region)


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
    destination = output_dir / filename
    if destination.exists():
        destination = output_dir / (
            f"{destination.stem}_{datetime.now().strftime('%f')}{destination.suffix}"
        )

    mss.tools.to_png(image.rgb, image.size, output=str(destination))
    return destination
