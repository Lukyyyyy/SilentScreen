from __future__ import annotations

import ctypes
import ctypes.wintypes
import time
from dataclasses import dataclass

from PySide6.QtCore import QObject, QAbstractNativeEventFilter, QTimer, Signal

user32 = ctypes.windll.user32

WM_HOTKEY = 0x0312
VK_LBUTTON = 0x01
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000


class HotkeyError(RuntimeError):
    pass


@dataclass(slots=True, frozen=True)
class HotkeyHandle:
    hotkey_id: int
    hotkey_str: str
    modifiers: int
    vk_code: int


MODIFIER_MAP = {
    "ALT": MOD_ALT,
    "CTRL": MOD_CONTROL,
    "CONTROL": MOD_CONTROL,
    "SHIFT": MOD_SHIFT,
    "WIN": MOD_WIN,
    "META": MOD_WIN,
}

VK_NAME_MAP = {
    "SPACE": 0x20,
    "TAB": 0x09,
    "ENTER": 0x0D,
    "RETURN": 0x0D,
    "ESC": 0x1B,
    "ESCAPE": 0x1B,
    "BACKSPACE": 0x08,
    "DELETE": 0x2E,
    "INSERT": 0x2D,
    "HOME": 0x24,
    "END": 0x23,
    "PAGEUP": 0x21,
    "PGUP": 0x21,
    "PAGEDOWN": 0x22,
    "PGDOWN": 0x22,
    "LEFT": 0x25,
    "UP": 0x26,
    "RIGHT": 0x27,
    "DOWN": 0x28,
    "PLUS": 0xBB,
    "MINUS": 0xBD,
    "COMMA": 0xBC,
    "PERIOD": 0xBE,
}

for index in range(1, 25):
    VK_NAME_MAP[f"F{index}"] = 0x6F + index


def _split_parts(hotkey_str: str) -> list[str]:
    return [part.strip() for part in hotkey_str.replace("++", "+PLUS").split("+") if part.strip()]


def parse_hotkey(hotkey_str: str) -> tuple[int, int]:
    parts = _split_parts(hotkey_str)
    if len(parts) < 2:
        raise HotkeyError("快捷键必须至少包含一个修饰键和一个主键。")

    modifiers = MOD_NOREPEAT
    key_code = None

    for part in parts:
        normalized = part.upper()
        if normalized in MODIFIER_MAP:
            modifiers |= MODIFIER_MAP[normalized]
            continue

        if key_code is not None:
            raise HotkeyError("快捷键只能有一个主键。")

        if len(normalized) == 1 and normalized.isalnum():
            key_code = ord(normalized)
            continue

        if normalized in VK_NAME_MAP:
            key_code = VK_NAME_MAP[normalized]
            continue

        raise HotkeyError(f"不支持的按键: {part}")

    if key_code is None:
        raise HotkeyError("快捷键缺少主键。")

    if modifiers == MOD_NOREPEAT:
        raise HotkeyError("快捷键必须包含至少一个修饰键。")

    return modifiers, key_code


class HotkeyEventFilter(QAbstractNativeEventFilter):
    def __init__(self, owner: "GlobalHotkeyManager") -> None:
        super().__init__()
        self._owner = owner

    def nativeEventFilter(self, event_type, message):
        if event_type not in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            return False, 0

        msg = ctypes.wintypes.MSG.from_address(int(message))
        if msg.message == WM_HOTKEY:
            self._owner.handle_hotkey_message(int(msg.wParam))
            return True, 0
        return False, 0


class GlobalHotkeyManager(QObject):
    activated = Signal(str)

    def __init__(self, qt_app) -> None:
        super().__init__()
        self._qt_app = qt_app
        self._filter = HotkeyEventFilter(self)
        self._qt_app.installNativeEventFilter(self._filter)
        self._current: HotkeyHandle | None = None
        self._next_id = 1

    @property
    def current(self) -> HotkeyHandle | None:
        return self._current

    def register_hotkey(self, hotkey_str: str) -> HotkeyHandle:
        modifiers, vk_code = parse_hotkey(hotkey_str)
        hotkey_id = self._next_id
        self._next_id += 1

        if not user32.RegisterHotKey(None, hotkey_id, modifiers, vk_code):
            raise HotkeyError("快捷键注册失败，可能已被其他程序占用。")

        handle = HotkeyHandle(
            hotkey_id=hotkey_id,
            hotkey_str=hotkey_str,
            modifiers=modifiers,
            vk_code=vk_code,
        )
        self._current = handle
        return handle

    def update_hotkey(self, hotkey_str: str) -> HotkeyHandle:
        old_handle = self._current
        new_handle = self.register_hotkey(hotkey_str)
        if old_handle is not None:
            self.unregister_hotkey(old_handle)
        return new_handle

    def unregister_hotkey(self, handle: HotkeyHandle | None = None) -> None:
        target = handle or self._current
        if target is None:
            return

        user32.UnregisterHotKey(None, target.hotkey_id)
        if self._current == target:
            self._current = None

    def cleanup(self) -> None:
        self.unregister_hotkey()
        self._qt_app.removeNativeEventFilter(self._filter)

    def handle_hotkey_message(self, hotkey_id: int) -> None:
        if self._current and self._current.hotkey_id == hotkey_id:
            self.activated.emit(self._current.hotkey_str)


class GlobalMouseCaptureManager(QObject):
    activated = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._hold_seconds = 1.0
        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._poll_mouse_state)
        self._press_started_at: float | None = None
        self._was_pressed = False

    def start(self, hold_seconds: float) -> None:
        self.cleanup()
        self._hold_seconds = hold_seconds
        # 启用时已按住的左键需先松开，避免保存设置后立即误截。
        self._was_pressed = self._is_pressed()
        self._timer.start()

    def cleanup(self) -> None:
        self._timer.stop()
        self._press_started_at = None
        self._was_pressed = False

    def _is_pressed(self) -> bool:
        return bool(user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000)

    def _poll_mouse_state(self) -> None:
        is_pressed = self._is_pressed()
        now = time.monotonic()
        if is_pressed and not self._was_pressed:
            self._press_started_at = now
        elif not is_pressed:
            self._press_started_at = None
        self._was_pressed = is_pressed
        if (
            self._press_started_at is not None
            and now - self._press_started_at >= self._hold_seconds
        ):
            # 清除计时后再发信号，每次长按只截一次。
            self._press_started_at = None
            self.activated.emit("mouse-left-hold")
