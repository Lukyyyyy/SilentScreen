from __future__ import annotations

import logging
import sys
import threading
from pathlib import Path

from PySide6.QtCore import QSharedMemory
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from capture import capture_primary_screen, capture_screen_region, save_image
from hotkey import GlobalHotkeyManager, GlobalMouseSelectionManager, HotkeyError, MouseSelectionError
from settings import AppSettings, get_log_file, load_settings, save_settings
from ui import SettingsDialog, TrayController


class SilentScreenApp:
    def __init__(self, qt_app: QApplication) -> None:
        self.qt_app = qt_app
        self.qt_app.setApplicationDisplayName("Silent Screen")
        self.qt_app.setQuitOnLastWindowClosed(False)

        self.logger = self._configure_logging()
        self.settings = load_settings()
        self._issues: dict[str, str] = {}
        self._issues_lock = threading.Lock()
        base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        app_icon = QIcon(str(base_dir / "assets" / "SilentScreen.ico"))
        self.qt_app.setWindowIcon(app_icon)

        self.hotkeys = GlobalHotkeyManager(qt_app)
        self.hotkeys.activated.connect(self._capture_and_save)
        self.mouse_selection = GlobalMouseSelectionManager()
        self.mouse_selection.region_selected.connect(self._capture_region_and_save)

        self.tray = TrayController(app_icon, qt_app)
        self.tray.settings_action.triggered.connect(self.open_settings)
        self.tray.open_folder_action.triggered.connect(self.open_save_dir)
        self.tray.open_log_action.triggered.connect(self.open_log_file)
        self.tray.quit_action.triggered.connect(self.quit)

    def start(self) -> None:
        self.logger.info("Application starting")
        self.tray.show()
        self._register_initial_hotkey()
        self._start_mouse_selection()

    def _configure_logging(self) -> logging.Logger:
        logger = logging.getLogger("silent_screen")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        logger.propagate = False

        try:
            handler = logging.FileHandler(get_log_file(), encoding="utf-8")
        except OSError:
            handler = logging.NullHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        )
        logger.addHandler(handler)
        return logger

    def _register_initial_hotkey(self) -> None:
        try:
            handle = self.hotkeys.register_hotkey(self.settings.hotkey)
            self._clear_issue("hotkey")
            self.logger.info("Registered hotkey: %s", handle.hotkey_str)
        except HotkeyError as exc:
            self.logger.exception("Failed to register initial hotkey")
            self._record_issue(
                "hotkey",
                f"快捷键注册失败：{exc} 请更换快捷键。",
            )

    def _start_mouse_selection(self) -> None:
        try:
            self.mouse_selection.start()
            self._clear_issue("mouse")
            self.logger.info("Mouse selection listener started")
        except MouseSelectionError as exc:
            self.logger.exception("Failed to start mouse selection listener")
            self._record_issue("mouse", f"鼠标监听启动失败：{exc}")

    def _record_issue(self, key: str, message: str) -> None:
        with self._issues_lock:
            self._issues[key] = message

    def _clear_issue(self, key: str) -> None:
        with self._issues_lock:
            self._issues.pop(key, None)

    def _issue_messages(self) -> tuple[str, ...]:
        with self._issues_lock:
            return tuple(self._issues.values())

    def _capture_and_save(self, hotkey_str: str) -> None:
        self.logger.info("Hotkey triggered: %s", hotkey_str)
        self._run_capture_job(
            job_name="fullscreen",
            capture_func=capture_primary_screen,
        )

    def _capture_region_and_save(self, left: int, top: int, right: int, bottom: int) -> None:
        self.logger.info(
            "Mouse region triggered: (%s, %s) -> (%s, %s)",
            left,
            top,
            right,
            bottom,
        )
        self._run_capture_job(
            job_name="region",
            capture_func=lambda: capture_screen_region(left, top, right, bottom),
        )

    def _run_capture_job(self, job_name: str, capture_func) -> None:
        settings = self.settings
        worker = threading.Thread(
            target=self._capture_worker,
            args=(job_name, capture_func, settings.save_dir, settings.filename_pattern),
            daemon=True,
        )
        worker.start()

    def _capture_worker(
        self,
        job_name: str,
        capture_func,
        save_dir: str,
        filename_pattern: str,
    ) -> None:
        try:
            image = capture_func()
            saved_path = save_image(
                image=image,
                save_dir=save_dir,
                filename_pattern=filename_pattern,
            )
            self._clear_issue(f"capture_{job_name}")
            self.logger.info("%s screenshot saved: %s", job_name.capitalize(), saved_path)
        except Exception as exc:
            self.logger.exception("Failed to capture %s screenshot", job_name)
            self._record_issue(f"capture_{job_name}", f"截图失败：{exc}")

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self._issue_messages())
        if dialog.exec() != SettingsDialog.DialogCode.Accepted:
            return

        new_settings = dialog.result_settings
        if new_settings is None:
            return

        new_settings.image_format = self.settings.image_format
        new_settings.filename_pattern = self.settings.filename_pattern
        new_settings.monitor_mode = self.settings.monitor_mode

        old_hotkey = self.settings.hotkey
        try:
            if new_settings.hotkey != old_hotkey:
                self.hotkeys.update_hotkey(new_settings.hotkey)
                self._clear_issue("hotkey")
                self.logger.info("Updated hotkey: %s -> %s", old_hotkey, new_settings.hotkey)
        except HotkeyError as exc:
            self.logger.exception("Failed to update hotkey")
            self._record_issue("hotkey", f"更新快捷键失败：{exc}")
            return

        self.settings = new_settings
        try:
            save_settings(self.settings)
            self._clear_issue("settings")
        except OSError as exc:
            self.logger.exception("Failed to save settings")
            self._record_issue("settings", f"设置保存失败：{exc}")
        self.logger.info("Settings updated: save_dir=%s", self.settings.save_dir)

    def open_save_dir(self) -> None:
        try:
            Path(self.settings.save_dir).mkdir(parents=True, exist_ok=True)
            self.tray.open_path(self.settings.save_dir)
            self._clear_issue("save_dir")
        except OSError as exc:
            self._record_issue("save_dir", f"无法打开截图目录：{exc}")

    def open_log_file(self) -> None:
        try:
            self.tray.open_path(get_log_file())
            self._clear_issue("log")
        except OSError as exc:
            self._record_issue("log", f"无法打开日志：{exc}")

    def quit(self) -> None:
        self.logger.info("Application exiting")
        self.mouse_selection.cleanup()
        self.hotkeys.cleanup()
        self.tray.tray.hide()
        self.qt_app.quit()


def ensure_single_instance() -> QSharedMemory:
    shared = QSharedMemory("SilentScreenSingleton")
    if not shared.create(1):
        raise RuntimeError("Silent Screen 已经在运行。")
    return shared


def main() -> int:
    app = QApplication(sys.argv)

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
