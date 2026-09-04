from __future__ import annotations

import logging
import sys
import threading
from pathlib import Path

from PySide6.QtCore import QObject, QSharedMemory, Signal
from PySide6.QtGui import QCursor, QIcon
from PySide6.QtWidgets import QApplication

from capture import capture_and_save, ensure_capture_permission
from hotkey import GlobalHotkeyManager, HotkeyError
from settings import AppSettings, get_log_file, load_settings, save_settings
from ui import SettingsDialog, TrayController


def _hide_dock_icon() -> None:
    """设为 accessory 应用：不显示 Dock 图标，仅保留菜单栏托盘。"""
    try:
        from AppKit import NSApplication

        # 1 == NSApplicationActivationPolicyAccessory
        NSApplication.sharedApplication().setActivationPolicy_(1)
    except Exception:
        # pyobjc 不可用时继续运行，只是会显示 Dock 图标
        pass


class SilentScreenApp(QObject):
    capture_failed = Signal(str, str)

    def __init__(self, qt_app: QApplication) -> None:
        super().__init__(qt_app)
        self.qt_app = qt_app
        self.qt_app.setApplicationDisplayName("Silent Screen")
        self.qt_app.setQuitOnLastWindowClosed(False)

        self.logger = self._configure_logging()
        self.settings = load_settings()
        self.logger.info(
            "Loaded settings: hotkey=%s save_dir=%s",
            self.settings.hotkey,
            self.settings.save_dir,
        )
        assets = Path(__file__).resolve().parent / 'assets'
        self.qt_app.setWindowIcon(QIcon(str(assets / 'silentscreen-logo-v3.png')))
        tray_icon = QIcon(str(assets / 'tray-icon.svg'))
        tray_icon.setIsMask(True)  # macOS template 图标：随菜单栏背景自动切换颜色。

        self.hotkeys = GlobalHotkeyManager()
        self.hotkeys.activated.connect(self._capture_and_save)

        self.tray = TrayController(tray_icon, qt_app)
        self.capture_failed.connect(self.tray.show_error)
        self.tray.settings_action.triggered.connect(self.open_settings)
        self.tray.open_folder_action.triggered.connect(self.open_save_dir)
        self.tray.open_log_action.triggered.connect(self.open_log_file)
        self.tray.quit_action.triggered.connect(self.quit)

    def start(self) -> None:
        self.logger.info("Application starting")
        self._register_initial_hotkey()
        self.tray.show()

    def _configure_logging(self) -> logging.Logger:
        logger = logging.getLogger("silent_screen")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        logger.propagate = False

        handler = logging.FileHandler(get_log_file(), encoding="utf-8")
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        )
        logger.addHandler(handler)
        return logger

    def _register_initial_hotkey(self) -> None:
        try:
            handle = self.hotkeys.register_hotkey(self.settings.hotkey)
            self.logger.info("Registered hotkey: %s", handle.hotkey_str)
        except HotkeyError as exc:
            self.logger.exception("Failed to register initial hotkey")
            self.tray.show_error("快捷键注册失败", str(exc))
            raise

    def _capture_and_save(self, hotkey_str: str) -> None:
        self.logger.info("Hotkey triggered: %s", hotkey_str)
        try:
            # 授权请求必须在 GUI 线程发起。
            ensure_capture_permission(request=True)
        except PermissionError as exc:
            self.logger.warning("Screen capture permission unavailable: %s", exc)
            self.tray.show_error("需要屏幕录制权限", str(exc))
            return
        screen = self.qt_app.screenAt(QCursor.pos()) or self.qt_app.primaryScreen()
        if screen is None:
            self.tray.show_error("截图失败", "未找到可用屏幕。")
            return
        # 在快捷键触发时固定屏幕范围，避免后台线程启动后鼠标已移到另一屏。
        screen_rect = screen.geometry().getRect()
        settings = self.settings
        worker = threading.Thread(
            target=self._capture_worker,
            args=(settings.save_dir, settings.filename_pattern, screen_rect),
            daemon=True,
        )
        worker.start()

    def _capture_worker(self, save_dir: str, filename_pattern: str, screen_rect: tuple[int, int, int, int]) -> None:
        try:
            saved_path = capture_and_save(
                save_dir=save_dir,
                filename_pattern=filename_pattern,
                screen_rect=screen_rect,
            )
            self.logger.info("Fullscreen screenshot saved: %s", saved_path)
        except Exception as exc:
            self.logger.exception("Failed to capture fullscreen screenshot")
            self.capture_failed.emit("截图失败", str(exc))

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.settings)
        # 释放 Carbon 全局快捷键，让输入框也能收到当前正在使用的组合键。
        self.hotkeys.unregister_hotkey()
        try:
            try:
                result = dialog.exec()
            finally:
                self.hotkeys.register_hotkey(self.settings.hotkey)
        except HotkeyError as exc:
            self.logger.exception("Failed to restore hotkey after settings")
            self.tray.show_error("恢复快捷键失败", str(exc))
            return
        if result != SettingsDialog.DialogCode.Accepted:
            return

        new_settings = dialog.result_settings
        if new_settings is None:
            return

        new_settings.filename_pattern = self.settings.filename_pattern

        old_hotkey = self.settings.hotkey
        try:
            if new_settings.hotkey != old_hotkey:
                self.hotkeys.update_hotkey(new_settings.hotkey)
                self.logger.info("Updated hotkey: %s -> %s", old_hotkey, new_settings.hotkey)
        except HotkeyError as exc:
            self.logger.exception("Failed to update hotkey")
            self.tray.show_error("更新快捷键失败", str(exc))
            return

        self.settings = new_settings
        save_settings(self.settings)
        self.logger.info("Settings updated: save_dir=%s", self.settings.save_dir)

    def open_save_dir(self) -> None:
        self.tray.open_path(self.settings.save_dir)

    def open_log_file(self) -> None:
        self.tray.open_path(str(get_log_file()))

    def quit(self) -> None:
        self.logger.info("Application exiting")
        self.hotkeys.cleanup()
        self.tray.tray.hide()
        self.qt_app.quit()


def ensure_single_instance() -> QSharedMemory:
    shared = QSharedMemory("SilentScreenSingleton")
    if shared.attach():
        # attach 后立即 detach，清理上次进程被强杀留下的陈旧共享内存段；
        # 若真有另一个实例在运行，其持有引用会让下面的 create 失败。
        shared.detach()
    if not shared.create(1):
        raise RuntimeError("Silent Screen 已经在运行。")
    return shared


def main() -> int:
    app = QApplication(sys.argv)
    _hide_dock_icon()

    try:
        shared = ensure_single_instance()
    except RuntimeError:
        return 1

    app.setProperty("single_instance_guard", shared)

    controller = SilentScreenApp(app)
    try:
        controller.start()
    except HotkeyError:
        return 2

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
