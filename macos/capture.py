from __future__ import annotations

import ctypes
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

_core = ctypes.CDLL("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
_core.CGPreflightScreenCaptureAccess.argtypes = []
_core.CGPreflightScreenCaptureAccess.restype = ctypes.c_bool
_core.CGRequestScreenCaptureAccess.argtypes = []
_core.CGRequestScreenCaptureAccess.restype = ctypes.c_bool


def ensure_capture_permission(*, request: bool = False) -> None:
    if _core.CGPreflightScreenCaptureAccess():
        return
    if request:
        _core.CGRequestScreenCaptureAccess()
    raise PermissionError(
        "屏幕录制权限尚未对当前进程生效。请在系统设置 → 隐私与安全性 → "
        "屏幕与系统音频录制中允许 SilentScreen，然后完全退出并重新打开应用。"
        "若已开启，请移除旧条目后重新添加当前应用；源码运行时请授权启动它的终端。"
    )


def capture_and_save(
    save_dir: str | Path, filename_pattern: str, screen_rect: tuple[int, int, int, int]
) -> Path:
    ensure_capture_permission()
    output_dir = Path(save_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = datetime.now().strftime(filename_pattern)
    destination = (output_dir / filename).with_suffix(".jpg")
    if destination.exists():
        destination = output_dir / (
            f"{destination.stem}_{datetime.now().strftime('%f')}{destination.suffix}"
        )

    # 系统截图工具负责窗口合成；不再使用 mss 的旧 CGWindowListCreateImage 接口。
    with tempfile.TemporaryDirectory(dir=output_dir, prefix=".capture-") as temp_dir:
        temporary = Path(temp_dir) / "screen.jpg"
        result = subprocess.run(
            ["/usr/sbin/screencapture", "-x", "-R" + ",".join(map(str, screen_rect)), "-t", "jpg", str(temporary)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode or not temporary.is_file() or temporary.stat().st_size == 0:
            raise RuntimeError(f"系统截图失败：{result.stderr.strip() or '未生成图像'}")
        temporary.replace(destination)
    return destination
