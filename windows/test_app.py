import threading
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock

from app import SilentScreenApp
from hotkey import HotkeyError


class StartupTest(TestCase):
    def test_hotkey_conflict_keeps_application_running(self) -> None:
        events = []
        controller = SilentScreenApp.__new__(SilentScreenApp)
        controller.logger = Mock()
        controller.settings = SimpleNamespace(hotkey="Ctrl+Alt+A")
        controller._issues = {}
        controller._issues_lock = threading.Lock()
        controller.tray = Mock()
        controller.mouse_selection = Mock()
        controller.hotkeys = Mock()
        controller.tray.show.side_effect = lambda: events.append("tray")

        def reject_hotkey(_hotkey):
            events.append("hotkey")
            raise HotkeyError("快捷键已被占用")

        controller.hotkeys.register_hotkey.side_effect = reject_hotkey

        controller.start()

        self.assertEqual(events, ["tray", "hotkey"])
        self.assertIn("快捷键注册失败", controller._issues["hotkey"])
        controller.mouse_selection.start.assert_called_once()
