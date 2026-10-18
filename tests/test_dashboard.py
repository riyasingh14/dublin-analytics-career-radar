import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from career_radar.build_snapshot import build_snapshot_payload


ROOT = Path(__file__).resolve().parents[1]


class DashboardTests(unittest.TestCase):
    def payload(self):
        jobs = [
            {"canonical_url": "https://example.test/1", "title": "Data Analyst",
             "employer_name": "Example", "role_name": "Data Analyst", "work_pattern": "hybrid",
             "description_text": "Use SQL", "source_name": "Fixture", "location_text": "Cork, Ireland"},
            {"canonical_url": "https://example.test/2", "title": "Operations Manager",
             "employer_name": "Example", "role_name": "Unclassified", "work_pattern": "unknown",
             "description_text": "Use SQL", "source_name": "Fixture", "location_text": "Dublin, Ireland"},
        ]
        evidence = [
            {"canonical_url": job["canonical_url"], "skill_id": "sql", "skill_name": "SQL",
             "category": "Data", "source_phrase": "SQL", "extraction_method": "rule",
             "extraction_version": "taxonomy-v1", "confidence": "0.98"}
            for job in jobs
        ]
        return build_snapshot_payload(jobs, evidence, "Test fixture", "unreviewed")

    def test_evidence_filters_and_target_roles(self):
        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory) / "snapshot.json"
            snapshot.write_text(json.dumps(self.payload()))
            with patch.dict(os.environ, {"CAREER_RADAR_SNAPSHOT": str(snapshot)}):
                app = AppTest.from_file(str(ROOT / "market_app.py")).run(timeout=30)
                self.assertFalse(app.exception)
                self.assertEqual(len(app.tabs), 5)
                self.assertEqual(app.metric[1].value, "1")
                self.assertTrue(any("UNREVIEWED DATA" in item.value for item in app.warning))
                self.assertTrue(any("Not supplied" in item.value for item in app.caption))
                self.assertEqual(app.selectbox(key="planner_role").options, ["Data Analyst"])
                evidence_role = next(item for item in app.selectbox if item.label == "Evidence role")
                evidence_role.select("Unclassified").run()
                self.assertFalse(app.exception)
                table = next(item.value for item in app.dataframe if "source_phrase" in item.value.columns)
                self.assertEqual(len(table), 1)
                self.assertEqual(table.iloc[0]["title"], "Operations Manager")

    def test_older_snapshot_has_evidence_rebuild_message(self):
        payload = self.payload()
        payload.pop("evidence")
        payload.pop("provenance")
        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory) / "old.json"
            snapshot.write_text(json.dumps(payload))
            with patch.dict(os.environ, {"CAREER_RADAR_SNAPSHOT": str(snapshot)}):
                app = AppTest.from_file(str(ROOT / "market_app.py")).run(timeout=30)
                self.assertFalse(app.exception)
                self.assertTrue(any("Rebuild this snapshot" in item.value for item in app.info))

    def test_geography_filter_changes_market_denominator_and_role_options(self):
        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory) / "snapshot.json"
            snapshot.write_text(json.dumps(self.payload()))
            with patch.dict(os.environ, {"CAREER_RADAR_SNAPSHOT": str(snapshot)}):
                app = AppTest.from_file(str(ROOT / "market_app.py")).run(timeout=30)
                geography = next(item for item in app.selectbox if item.label == "Market geography")
                geography.select("Rest of Ireland").run()
                self.assertFalse(app.exception)
                self.assertEqual(app.metric[0].value, "1")
                self.assertEqual(app.metric[1].value, "1")
                table = next(item.value for item in app.dataframe if "source_phrase" in item.value.columns)
                self.assertEqual(len(table), 1)
                self.assertEqual(table.iloc[0]["role_name"], "Data Analyst")
