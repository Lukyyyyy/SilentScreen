import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from settings import load_settings


class SettingsTest(TestCase):
    def test_invalid_settings_fall_back_to_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings_file = Path(directory) / "settings.json"
            settings_file.write_text("not json", encoding="utf-8")

            with self.assertLogs("silent_screen", level="ERROR"):
                with patch("settings.get_settings_file", return_value=settings_file):
                    settings = load_settings()

        self.assertEqual(settings.hotkey, "Ctrl+Alt+A")
