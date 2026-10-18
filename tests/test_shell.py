"""Landing and navigation remain useful without a private market dataset."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


class ShellTests(unittest.TestCase):
    def test_home_without_snapshot_has_four_working_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"CAREER_RADAR_SNAPSHOT": str(Path(directory) / "missing.json")}):
                app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
                self.assertFalse(app.exception)
                self.assertEqual(app.title[0].value, "Evidence for your next career move")
                self.assertEqual(sum(button.key.startswith("open_") for button in app.button), 4)
                app.button(key="home_methodology").click().run(timeout=30)
                self.assertFalse(app.exception)
                self.assertEqual(app.radio[0].value, "Methodology")
                self.assertEqual(app.title[0].value, "Evidence, with its limits in view")

    def test_invalid_snapshot_does_not_crash_home(self):
        for payload in (
            "{broken", "[]", '{"metadata":{},"market":{}}',
            '{"metadata":{},"market":{"sample_size":-1}}',
            '{"metadata":{},"market":{"sample_size":2},"postings":{}}',
            '{"metadata":{},"market":{"sample_size":2},"evidence":[null]}',
            '{"metadata":{},"market":{"sample_size":2},"provenance":[]}',
        ):
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as directory:
                snapshot = Path(directory) / "snapshot.json"
                snapshot.write_text(payload)
                with patch.dict(os.environ, {"CAREER_RADAR_SNAPSHOT": str(snapshot)}):
                    app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
                    self.assertFalse(app.exception)
                    self.assertTrue(any("could not be read" in item.value for item in app.info))
                    self.assertEqual(len(app.metric), 0)

    def test_home_metrics_are_from_loaded_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory) / "snapshot.json"
            snapshot.write_text(json.dumps({"metadata": {"data_status": "unreviewed", "publish_allowed": False}, "market": {"sample_size": 7}}))
            with patch.dict(os.environ, {"CAREER_RADAR_SNAPSHOT": str(snapshot)}):
                app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=30)
                self.assertFalse(app.exception)
                self.assertEqual(app.metric[0].value, "7")
                self.assertEqual(app.metric[2].value, "Not supplied")
                self.assertTrue(any("UNREVIEWED" in item.value for item in app.warning))


if __name__ == "__main__":
    unittest.main()
