"""基于 Carbon Event Manager 的全局快捷键（免系统权限）。

Qt 在 macOS 上的修饰键惯例（PortableText）：
- "Ctrl"  → ⌘ Command
- "Meta"  → ⌃ Control
- "Alt"   → ⌥ Option
- "Shift" → ⇧ Shift
"""

from __future__ import annotations

import ctypes
import ctypes.util
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal


class HotkeyError(RuntimeError):
    pass


# ---- Carbon Event Manager C API（纯 C 接口，经 ctypes 调用，无需任何系统权限） ----

_carbon_path = ctypes.util.find_library("Carbon") or "/System/Library/Frameworks/Carbon.framework/Carbon"
_carbon = ctypes.CDLL(_carbon_path)

EventHandlerProc = ctypes.CFUNCTYPE(ctypes.c_int32, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)


class EventHotKeyID(ctypes.Structure):
    _fields_ = [
        ("signature", ctypes.c_uint32),
        ("id", ctypes.c_uint32),
    ]


class EventTypeSpec(ctypes.Structure):
    _fields_ = [
        ("event_class", ctypes.c_uint32),
        ("event_kind", ctypes.c_uint16),
    ]


_carbon.GetApplicationEventTarget.restype = ctypes.c_void_p
_carbon.GetApplicationEventTarget.argtypes = []

_carbon.RegisterEventHotKey.restype = ctypes.c_int32
_carbon.RegisterEventHotKey.argtypes = [
    ctypes.c_uint32,          # inHotKeyCode
    ctypes.c_uint32,          # inHotKeyModifiers
    EventHotKeyID,            # inHotKeyID
    ctypes.c_void_p,          # inTarget
    ctypes.c_uint32,          # inOptions
    ctypes.POINTER(ctypes.c_void_p),  # outRef
]

_carbon.UnregisterEventHotKey.restype = ctypes.c_int32
_carbon.UnregisterEventHotKey.argtypes = [ctypes.c_void_p]

_carbon.InstallEventHandler.restype = ctypes.c_int32
_carbon.InstallEventHandler.argtypes = [
    ctypes.c_void_p,          # inTarget
    EventHandlerProc,         # inHandler
    ctypes.c_uint32,          # inNumTypes
    ctypes.POINTER(EventTypeSpec),  # inList
    ctypes.c_void_p,          # inUserData
    ctypes.POINTER(ctypes.c_void_p),  # outRef
]

_carbon.RemoveEventHandler.restype = ctypes.c_int32
_carbon.RemoveEventHandler.argtypes = [ctypes.c_void_p]

_carbon.GetEventParameter.restype = ctypes.c_int32
_carbon.GetEventParameter.argtypes = [
    ctypes.c_void_p,                    # inEvent
    ctypes.c_uint32,                    # inName
    ctypes.c_uint32,                    # inDesiredType
    ctypes.POINTER(ctypes.c_uint32),    # outActualType
    ctypes.c_uint32,                    # inBufferSize
    ctypes.POINTER(ctypes.c_uint32),    # outActualSize
    ctypes.c_void_p,                    # outData
]

# 以下常量均已对照 SDK 头文件 HIToolbox/CarbonEvents.h / Events.h 核实
kEventClassKeyboard = 0x6B657962  # 'keyb'
kEventHotKeyPressed = 5
kEventParamDirectObject = 0x2D2D2D2D  # '----'
typeEventHotKeyID = 0x686B6964  # 'hkid'

MOD_CMD = 0x0100  # cmdKey = 1 << 8
MOD_SHIFT = 0x0200  # shiftKey = 1 << 9
MOD_OPTION = 0x0800  # optionKey = 1 << 11
MOD_CONTROL = 0x1000  # controlKey = 1 << 12

MODIFIER_MAP = {
    # Qt PortableText：macOS 上 "Ctrl" 指向 Command 键
    "CTRL": MOD_CMD,
    "CMD": MOD_CMD,
    "COMMAND": MOD_CMD,
    # Qt PortableText：macOS 上 "Meta" 指向 Control 键
    "META": MOD_CONTROL,
    "CONTROL": MOD_CONTROL,
    "ALT": MOD_OPTION,
    "OPTION": MOD_OPTION,
    "SHIFT": MOD_SHIFT,
}

VK_NAME_MAP = {
    "SPACE": 0x31,
    "TAB": 0x30,
    "ENTER": 0x24,
    "RETURN": 0x24,
    "ESC": 0x35,
    "ESCAPE": 0x35,
    "BACKSPACE": 0x33,
    "DELETE": 0x75,
    "FORWARDDELETE": 0x75,
    "HOME": 0x73,
    "END": 0x77,
    "PAGEUP": 0x74,
    "PGUP": 0x74,
    "PAGEDOWN": 0x79,
    "PGDOWN": 0x79,
    "LEFT": 0x7B,
    "UP": 0x7E,
    "RIGHT": 0x7C,
    "DOWN": 0x7D,
    "MINUS": 0x1B,
    "EQUAL": 0x18,
    "LEFTBRACKET": 0x21,
    "RIGHTBRACKET": 0x1E,
    "BACKSLASH": 0x2A,
    "SEMICOLON": 0x29,
    "QUOTE": 0x27,
    "COMMA": 0x2B,
    "PERIOD": 0x2F,
    "SLASH": 0x2C,
    "GRAVE": 0x32,
}

_ANSI_LETTERS = {
    "A": 0x00, "S": 0x01, "D": 0x02, "F": 0x03, "H": 0x04, "G": 0x05,
    "Z": 0x06, "X": 0x07, "C": 0x08, "V": 0x09, "B": 0x0B, "Q": 0x0C,
    "W": 0x0D, "E": 0x0E, "R": 0x0F, "Y": 0x10, "T": 0x11,
    "O": 0x1F, "U": 0x20, "I": 0x22, "P": 0x23, "L": 0x25, "J": 0x26,
    "K": 0x28, "N": 0x2D, "M": 0x2E,
}

_ANSI_DIGITS = {
    "0": 0x1D, "1": 0x12, "2": 0x13, "3": 0x14, "4": 0x15,
    "5": 0x17, "6": 0x16, "7": 0x1A, "8": 0x1C, "9": 0x19,
}

_FUNCTION_KEYS = {
    "F1": 0x7A, "F2": 0x78, "F3": 0x63, "F4": 0x76, "F5": 0x60,
    "F6": 0x61, "F7": 0x62, "F8": 0x64, "F9": 0x65, "F10": 0x6D,
    "F11": 0x67, "F12": 0x6F, "F13": 0x69, "F14": 0x6B, "F15": 0x71,
    "F16": 0x6A, "F17": 0x40, "F18": 0x4F, "F19": 0x50, "F20": 0x5A,
}


def _split_parts(hotkey_str: str) -> list[str]:
    return [part.strip() for part in hotkey_str.replace("++", "+PLUS").split("+") if part.strip()]


def parse_hotkey(hotkey_str: str) -> tuple[int, int]:
    """把 Qt PortableText 快捷键串解析为 (Carbon 修饰键, 虚拟键码)。"""
    parts = _split_parts(hotkey_str)
    if len(parts) < 2:
        raise HotkeyError("快捷键必须至少包含一个修饰键和一个主键。")

    modifiers = 0
    key_code = None

    for part in parts:
        normalized = part.upper()
        if normalized in MODIFIER_MAP:
            modifiers |= MODIFIER_MAP[normalized]
            continue

        if key_code is not None:
            raise HotkeyError("快捷键只能有一个主键。")

        if normalized in ("WIN", "SUPER", "META_WIN"):
            raise HotkeyError("macOS 上没有 Win 键，请使用 Ctrl(⌘)/Meta(⌃)/Alt(⌥)/Shift(⇧)。")

        if normalized == "PLUS":
            key_code = 0x18
            continue

        if len(normalized) == 1 and normalized.isalnum():
            if normalized.isalpha():
                key_code = _ANSI_LETTERS[normalized]
            else:
                key_code = _ANSI_DIGITS[normalized]
            continue

        if normalized in VK_NAME_MAP:
            key_code = VK_NAME_MAP[normalized]
            continue

        if normalized in _FUNCTION_KEYS:
            key_code = _FUNCTION_KEYS[normalized]
            continue

        raise HotkeyError(f"不支持的按键: {part}")

    if key_code is None:
        raise HotkeyError("快捷键缺少主键。")

    if modifiers == 0:
        raise HotkeyError("快捷键必须包含至少一个修饰键。")

    return modifiers, key_code


@dataclass(slots=True, frozen=True)
class HotkeyHandle:
    hotkey_id: int
    hotkey_ref: int
    hotkey_str: str
    modifiers: int
    key_code: int


class GlobalHotkeyManager(QObject):
    activated = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._hotkeys: dict[int, HotkeyHandle] = {}
        self._next_id = 1
        self._handler_proc = EventHandlerProc(self._carbon_event_handler)
        self._handler_ref = ctypes.c_void_p()

        spec = (EventTypeSpec * 1)(EventTypeSpec(kEventClassKeyboard, kEventHotKeyPressed))
        err = _carbon.InstallEventHandler(
            _carbon.GetApplicationEventTarget(),
            self._handler_proc,
            1,
            spec,
            None,
            ctypes.byref(self._handler_ref),
        )
        if err != 0 or not self._handler_ref:
            raise HotkeyError(f"安装快捷键事件处理器失败 (err={err})")

    @property
    def current(self) -> HotkeyHandle | None:
        for handle in self._hotkeys.values():
            return handle
        return None

    def register_hotkey(self, hotkey_str: str) -> HotkeyHandle:
        modifiers, key_code = parse_hotkey(hotkey_str)
        hotkey_id = self._next_id
        self._next_id += 1

        ref = ctypes.c_void_p()
        hid = EventHotKeyID(signature=0x53534D53, id=hotkey_id)  # 'SSMS'
        err = _carbon.RegisterEventHotKey(
            key_code,
            modifiers,
            hid,
            _carbon.GetApplicationEventTarget(),
            0,
            ctypes.byref(ref),
        )
        if err != 0 or not ref:
            raise HotkeyError("快捷键注册失败，可能已被其他程序占用。")

        handle = HotkeyHandle(
            hotkey_id=hotkey_id,
            hotkey_ref=ref.value,
            hotkey_str=hotkey_str,
            modifiers=modifiers,
            key_code=key_code,
        )
        self._hotkeys[hotkey_id] = handle
        return handle

    def update_hotkey(self, hotkey_str: str) -> HotkeyHandle:
        old_handle = self.current
        new_handle = self.register_hotkey(hotkey_str)
        if old_handle is not None:
            self.unregister_hotkey(old_handle)
        return new_handle

    def unregister_hotkey(self, handle: HotkeyHandle | None = None) -> None:
        target = handle or self.current
        if target is None:
            return
        _carbon.UnregisterEventHotKey(ctypes.c_void_p(target.hotkey_ref))
        self._hotkeys.pop(target.hotkey_id, None)

    def cleanup(self) -> None:
        for handle in list(self._hotkeys.values()):
            self.unregister_hotkey(handle)
        if self._handler_ref:
            _carbon.RemoveEventHandler(ctypes.c_void_p(self._handler_ref.value))
            self._handler_ref = ctypes.c_void_p()

    def _carbon_event_handler(self, _call_ref, event_ref, _user_data) -> int:
        if not event_ref:
            return 0

        hid = EventHotKeyID()
        size = ctypes.c_uint32(0)
        err = _carbon.GetEventParameter(
            event_ref,
            kEventParamDirectObject,
            typeEventHotKeyID,
            None,
            ctypes.sizeof(EventHotKeyID),
            ctypes.byref(size),
            ctypes.byref(hid),
        )
        if err == 0:
            handle = self._hotkeys.get(hid.id)
            if handle is not None:
                self.activated.emit(handle.hotkey_str)
        return 0
