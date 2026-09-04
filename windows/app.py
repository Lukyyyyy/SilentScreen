from __future__ import annotations

import logging
import sys
import threading

from PySide6.QtCore import QSharedMemory
from PySide6.QtWidgets import QApplication, QStyle

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
        tray_icon = self.qt_app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)

        self.hotkeys = GlobalHotkeyManager(qt_app)
        self.hotkeys.activated.connect(self._capture_and_save)
        self.mouse_selection = GlobalMouseSelectionManager()
        self.mouse_selection.region_selected.connect(self._capture_region_and_save)

        self.tray = TrayController(tray_icon, qt_app)
        self.tray.settings_action.triggered.connect(self.open_settings)
        self.tray.open_folder_action.triggered.connect(self.open_save_dir)
        self.tray.open_log_action.triggered.connect(self.open_log_file)
        self.tray.quit_action.triggered.connect(self.quit)

    def start(self) -> None:
        self.logger.info("Application starting")
        self._register_initial_hotkey()
        self._start_mouse_selection()
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

    def _start_mouse_selection(self) -> None:
        try:
            self.mouse_selection.start()
            self.logger.info("Mouse selection listener started")
        except MouseSelectionError as exc:
            self.logger.exception("Failed to start mouse selection listener")
            self.tray.show_error("鼠标监听启动失败", str(exc))
            raise

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
            self.logger.info("%s screenshot saved: %s", job_name.capitalize(), saved_path)
        except Exception:
            self.logger.exception("Failed to capture %s screenshot", job_name)

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.settings)
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
        self.tray.open_path(get_log_file())

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

    controller = SilentScreenApp(app)
    try:
        controller.start()
    except (HotkeyError, MouseSelectionError):
        return 2

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
