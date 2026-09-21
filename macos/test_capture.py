import subprocess
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from capture import capture_and_save


class CaptureTest(TestCase):
    def test_saves_jpeg_even_with_legacy_png_pattern(self) -> None:
        def fake_capture(command, **_kwargs):
            Path(command[-1]).write_bytes(b"jpeg")
            return subprocess.CompletedProcess(command, 0, "", "")

        with tempfile.TemporaryDirectory() as directory:
            with patch("capture.ensure_capture_permission"), patch(
                "capture.subprocess.run", side_effect=fake_capture
            ) as run:
                saved = capture_and_save(
                    directory, "Screenshot_%Y%m%d.png", (0, 0, 100, 100)
                )
                self.assertTrue(saved.is_file())

        self.assertEqual(saved.suffix, ".jpg")
        self.assertEqual(run.call_args.args[0][-2], "jpg")
