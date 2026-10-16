from __future__ import annotations

import logging
import sys
import threading
from pathlib import Path

from PySide6.QtCore import QObject, QSharedMemory, Signal
from PySide6.QtGui import QCursor, QIcon
from PySide6.QtWidgets import QApplication

from capture import capture_and_save, ensure_capture_permission
from hotkey import GlobalHotkeyManager, GlobalMouseCaptureManager, HotkeyError
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
    capture_status = Signal(str)

    def __init__(self, qt_app: QApplication) -> None:
        super().__init__(qt_app)
        self.qt_app = qt_app
        self.qt_app.setApplicationDisplayName("Silent Screen")
        self.qt_app.setQuitOnLastWindowClosed(False)

        self.logger = self._configure_logging()
        self.settings = load_settings()
        self._issues: dict[str, str] = {}
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
        self.mouse_capture = GlobalMouseCaptureManager()
        self.mouse_capture.activated.connect(self._capture_and_save)

        self.tray = TrayController(tray_icon, qt_app)
        self.capture_status.connect(self._set_capture_status)
        self.tray.settings_action.triggered.connect(self.open_settings)
        self.tray.open_folder_action.triggered.connect(self.open_save_dir)
        self.tray.open_log_action.triggered.connect(self.open_log_file)
        self.tray.quit_action.triggered.connect(self.quit)

    def start(self) -> None:
        self.logger.info("Application starting")
        self.tray.show()
        self._register_initial_hotkey()
        if self.settings.mouse_capture_enabled:
            self.mouse_capture.start(self.settings.mouse_hold_seconds)

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
        if not self.settings.hotkey_enabled:
            return
        try:
            handle = self.hotkeys.register_hotkey(self.settings.hotkey)
            self._issues.pop("hotkey", None)
            self.logger.info("Registered hotkey: %s", handle.hotkey_str)
        except HotkeyError as exc:
            self.logger.exception("Failed to register initial hotkey")
            self._record_issue("hotkey", f"快捷键注册失败：{exc} 请更换快捷键。")

    def _record_issue(self, key: str, message: str) -> None:
        self._issues[key] = message

    def _set_capture_status(self, message: str) -> None:
        if message:
            self._record_issue("capture", message)
        else:
            self._issues.pop("capture", None)

    def _capture_and_save(self, trigger: str) -> None:
        self.logger.info("Capture triggered: %s", trigger)
        try:
            # 授权请求必须在 GUI 线程发起。
            ensure_capture_permission(request=True)
        except PermissionError as exc:
            self.logger.warning("Screen capture permission unavailable: %s", exc)
            self._record_issue("permission", f"需要屏幕录制权限：{exc}")
            return
        self._issues.pop("permission", None)
        screen = self.qt_app.screenAt(QCursor.pos()) or self.qt_app.primaryScreen()
        if screen is None:
            self._record_issue("capture", "截图失败：未找到可用屏幕。")
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
            self.capture_status.emit("")
        except Exception as exc:
            self.logger.exception("Failed to capture fullscreen screenshot")
            self.capture_status.emit(f"截图失败：{exc}")

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, tuple(self._issues.values()))
        # 设置期间暂停触发，也让快捷键输入框能收到当前组合键。
        self.hotkeys.unregister_hotkey()
        self.mouse_capture.cleanup()
        try:
            result = dialog.exec()
            new_settings = dialog.result_settings
            if result != SettingsDialog.DialogCode.Accepted or new_settings is None:
                self._register_initial_hotkey()
                return

            new_settings.filename_pattern = self.settings.filename_pattern
            try:
                if new_settings.hotkey_enabled:
                    self.hotkeys.register_hotkey(new_settings.hotkey)
            except HotkeyError as exc:
                self.logger.exception("Failed to update hotkey")
                self._register_initial_hotkey()
                self._record_issue("hotkey", f"更新快捷键失败：{exc}")
                return

            self._issues.pop("hotkey", None)
            self.settings = new_settings
            try:
                save_settings(self.settings)
                self._issues.pop("settings", None)
            except OSError as exc:
                self.logger.exception("Failed to save settings")
                self._record_issue("settings", f"设置保存失败：{exc}")
            self.logger.info("Settings updated: save_dir=%s", self.settings.save_dir)
        finally:
            if self.settings.mouse_capture_enabled:
                self.mouse_capture.start(self.settings.mouse_hold_seconds)

    def open_save_dir(self) -> None:
        try:
            self.tray.open_path(self.settings.save_dir)
            self._issues.pop("save_dir", None)
        except OSError as exc:
            self._record_issue("save_dir", f"无法打开截图目录：{exc}")

    def open_log_file(self) -> None:
        try:
            self.tray.open_path(str(get_log_file()))
            self._issues.pop("log", None)
        except OSError as exc:
            self._record_issue("log", f"无法打开日志：{exc}")

    def quit(self) -> None:
        self.logger.info("Application exiting")
        self.mouse_capture.cleanup()
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

    try:
        controller = SilentScreenApp(app)
        controller.start()
    except Exception:
        logging.getLogger("silent_screen").exception("Application failed to start")
        return 3

    def handle_uncaught_exception(exc_type, exc_value, exc_traceback) -> None:
        controller.logger.error(
            "Unhandled application error",
            exc_info=(exc_type, exc_value, exc_traceback),
        )
        controller._record_issue("runtime", f"运行异常：{exc_value}")

    sys.excepthook = handle_uncaught_exception

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
