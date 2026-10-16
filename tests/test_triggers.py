"""Run with the target platform directory on PYTHONPATH."""

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

from PySide6.QtWidgets import QApplication, QDialog

import app
import hotkey
import settings
from ui import SettingsDialog


class TriggerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt_app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.defaults = settings.AppSettings("Ctrl+Alt+A", self.directory.name)

    def test_mouse_triggers_while_held_once_then_rearms(self):
        for seconds in (1.0, 2.5):
            with self.subTest(seconds=seconds):
                manager = hotkey.GlobalMouseCaptureManager()
                hits = []
                manager.activated.connect(hits.append)
                with patch.object(manager, "_is_pressed", return_value=False) as pressed, patch(
                    "hotkey.time.monotonic", return_value=100.0
                ) as clock:
                    manager.start(seconds)
                    self.assertTrue(manager._timer.isActive())
                    pressed.return_value = True
                    manager._poll_mouse_state()
                    clock.return_value = 100 + seconds - 0.01
                    manager._poll_mouse_state()
                    self.assertEqual(hits, [])
                    clock.return_value = 100 + seconds + 0.01
                    manager._poll_mouse_state()
                    self.assertEqual(hits, ["mouse-left-hold"])
                    clock.return_value += 10
                    manager._poll_mouse_state()
                    self.assertEqual(len(hits), 1)
                    pressed.return_value = False
                    manager._poll_mouse_state()
                    pressed.return_value = True
                    manager._poll_mouse_state()
                    clock.return_value += seconds + 0.01
                    manager._poll_mouse_state()
                    self.assertEqual(len(hits), 2)
                    manager.cleanup()
                    self.assertFalse(manager._timer.isActive())

    def test_short_press_and_enabling_while_held_do_not_capture(self):
        manager = hotkey.GlobalMouseCaptureManager()
        self.addCleanup(manager.cleanup)
        hits = []
        manager.activated.connect(hits.append)
        with patch.object(manager, "_is_pressed", return_value=True) as pressed, patch(
            "hotkey.time.monotonic", return_value=100.0
        ) as clock:
            manager.start(1)
            manager._poll_mouse_state()
            clock.return_value = 110
            manager._poll_mouse_state()
            self.assertEqual(hits, [])
            pressed.return_value = False
            manager._poll_mouse_state()
            pressed.return_value = True
            manager._poll_mouse_state()
            clock.return_value = 110.5
            pressed.return_value = False
            manager._poll_mouse_state()
            clock.return_value = 120
            manager._poll_mouse_state()
            self.assertEqual(hits, [])
            manager.start(2.5)
            pressed.return_value = True
            manager._poll_mouse_state()
            clock.return_value = 121.1
            manager._poll_mouse_state()
            self.assertEqual(hits, [])
            clock.return_value = 122.6
            manager._poll_mouse_state()
            self.assertEqual(len(hits), 1)

    def test_native_mouse_query_uses_left_button(self):
        manager = hotkey.GlobalMouseCaptureManager()
        if hasattr(hotkey, "user32"):
            with patch.object(hotkey.user32, "GetAsyncKeyState", return_value=0x8000) as query:
                self.assertTrue(manager._is_pressed())
                query.assert_called_once_with(0x01)
        else:
            with patch.object(hotkey._core_graphics, "CGEventSourceButtonState", return_value=True) as query:
                self.assertTrue(manager._is_pressed())
                query.assert_called_once_with(0, 0)

    def test_legacy_settings_and_round_trip(self):
        target = Path(self.directory.name) / "settings.json"
        with patch.object(settings, "get_settings_file", return_value=target), patch.object(
            settings, "get_default_save_dir", return_value=Path(self.directory.name)
        ):
            target.write_text(json.dumps({"hotkey": "Ctrl+Alt+B", "region_capture_enabled": True}))
            loaded = settings.load_settings()
            self.assertTrue(loaded.hotkey_enabled)
            self.assertFalse(loaded.mouse_capture_enabled)
            self.assertEqual(loaded.mouse_hold_seconds, 1)
            self.assertEqual(loaded.hotkey, "Ctrl+Alt+B")
            for enabled in (True, False):
                updated = replace(loaded, hotkey_enabled=enabled, mouse_capture_enabled=not enabled, mouse_hold_seconds=2.75)
                settings.save_settings(updated)
                self.assertEqual(settings.load_settings(), updated)

    def test_invalid_hold_duration_falls_back_without_losing_settings(self):
        target = Path(self.directory.name) / "settings.json"
        with patch.object(settings, "get_settings_file", return_value=target), patch.object(
            settings, "get_default_save_dir", return_value=Path(self.directory.name)
        ):
            for duration in (-1, 0, 0.01, 3601, 10**400, True, None, "2", float("nan"), float("inf")):
                with self.subTest(duration=duration):
                    target.write_text(json.dumps({"hotkey": "Ctrl+Alt+B", "mouse_hold_seconds": duration}))
                    loaded = settings.load_settings()
                    self.assertEqual(loaded.mouse_hold_seconds, 1)
                    self.assertEqual(loaded.hotkey, "Ctrl+Alt+B")

    def test_dialog_saves_independent_switches_and_duration(self):
        for keyboard in (False, True):
            for mouse in (False, True):
                with self.subTest(keyboard=keyboard, mouse=mouse):
                    dialog = SettingsDialog(self.defaults)
                    self.assertTrue(dialog._hotkey_checkbox.isChecked())
                    self.assertFalse(dialog._mouse_checkbox.isChecked())
                    self.assertEqual(dialog._hold_seconds.value(), 1)
                    dialog._hotkey_checkbox.setChecked(keyboard)
                    dialog._mouse_checkbox.setChecked(mouse)
                    self.assertEqual(dialog._hotkey_edit.isEnabled(), keyboard)
                    self.assertEqual(dialog._hold_seconds.isEnabled(), mouse)
                    dialog._hold_seconds.setValue(2.75)
                    dialog._save()
                    self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)
                    self.assertEqual(dialog.result_settings.hotkey_enabled, keyboard)
                    self.assertEqual(dialog.result_settings.mouse_capture_enabled, mouse)
                    self.assertEqual(dialog.result_settings.mouse_hold_seconds, 2.75)
                    dialog.close()

    def test_disabled_hotkey_does_not_block_mouse_only_settings(self):
        dialog = SettingsDialog(self.defaults)
        dialog._hotkey_edit.clear()
        dialog._save()
        self.assertIsNone(dialog.result_settings)
        dialog._hotkey_checkbox.setChecked(False)
        dialog._mouse_checkbox.setChecked(True)
        dialog._save()
        self.assertIsNotNone(dialog.result_settings)
        dialog.close()

    def make_controller(self, configuration):
        with patch.object(app, "load_settings", return_value=configuration), patch.object(
            app.SilentScreenApp, "_configure_logging", return_value=Mock()
        ), patch.object(app, "GlobalHotkeyManager"), patch.object(
            app, "GlobalMouseCaptureManager"
        ), patch.object(app, "TrayController"):
            return app.SilentScreenApp(self.qt_app)

    def test_start_and_save_apply_all_switch_combinations(self):
        for keyboard in (False, True):
            for mouse in (False, True):
                with self.subTest(keyboard=keyboard, mouse=mouse):
                    configuration = replace(self.defaults, hotkey_enabled=keyboard, mouse_capture_enabled=mouse, mouse_hold_seconds=2.5)
                    controller = self.make_controller(configuration)
                    controller.start()
                    self.assertEqual(controller.hotkeys.register_hotkey.called, keyboard)
                    self.assertEqual(controller.mouse_capture.start.called, mouse)
                    controller.hotkeys.reset_mock()
                    controller.mouse_capture.reset_mock()
                    updated = replace(configuration, hotkey_enabled=not keyboard, mouse_capture_enabled=not mouse)
                    with patch.object(app, "SettingsDialog") as dialog, patch.object(app, "save_settings") as save:
                        dialog.DialogCode = QDialog.DialogCode
                        dialog.return_value.exec.return_value = QDialog.DialogCode.Accepted
                        dialog.return_value.result_settings = updated
                        controller.open_settings()
                    controller.hotkeys.unregister_hotkey.assert_called_once()
                    controller.mouse_capture.cleanup.assert_called_once()
                    self.assertEqual(controller.hotkeys.register_hotkey.called, not keyboard)
                    self.assertEqual(controller.mouse_capture.start.called, not mouse)
                    save.assert_called_once_with(updated)
                    controller.quit()
                    self.assertEqual(controller.mouse_capture.cleanup.call_count, 2)
                    controller.hotkeys.cleanup.assert_called_once()

    def test_cancel_and_registration_failure_restore_previous_triggers(self):
        for accepted in (False, True):
            with self.subTest(accepted=accepted):
                configuration = replace(self.defaults, mouse_capture_enabled=True, mouse_hold_seconds=2.5)
                controller = self.make_controller(configuration)
                if accepted:
                    controller.hotkeys.register_hotkey.side_effect = [hotkey.HotkeyError("occupied"), Mock()]
                with patch.object(app, "SettingsDialog") as dialog, patch.object(app, "save_settings") as save:
                    dialog.DialogCode = QDialog.DialogCode
                    dialog.return_value.exec.return_value = QDialog.DialogCode.Accepted if accepted else QDialog.DialogCode.Rejected
                    dialog.return_value.result_settings = replace(configuration, hotkey="Ctrl+Alt+B") if accepted else None
                    controller.open_settings()
                self.assertIs(controller.settings, configuration)
                save.assert_not_called()
                controller.hotkeys.register_hotkey.assert_called_with(configuration.hotkey)
                controller.mouse_capture.start.assert_called_once_with(2.5)
                if accepted:
                    self.assertIn("occupied", controller._issues["hotkey"])


if __name__ == "__main__":
    unittest.main()
