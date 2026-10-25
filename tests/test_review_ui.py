"""Private review UI saves only explicit per-record human input."""
import csv
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from career_radar.validation import build_review_queue

ROOT = Path(__file__).resolve().parents[1]


def fixture_queue():
    jobs = [{"canonical_url": f"https://example.test/review/{i}", "title": "Fictional analyst",
             "employer_name": "Fictional company", "description_text": phrase,
             "source_job_id": str(i), "location_text": "Dublin, Ireland"}
            for i, phrase in enumerate(["SQL is required.", "Excel is preferred."])]
    evidence = [{"canonical_url": jobs[i]["canonical_url"], "skill_id": skill,
                 "skill_name": name, "source_phrase": name, "category": category,
                 "extraction_method": "rule", "extraction_version": "taxonomy-v2-tech", "confidence": .98}
                for i, (skill, name, category) in enumerate([("sql", "SQL", "Data"), ("excel", "Excel", "BI")])]
    return build_review_queue(jobs, evidence)


class ReviewUITests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "review.csv"
        rows = fixture_queue()
        with self.path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        self.original = self.path.read_bytes()

    def app(self):
        with patch.dict(os.environ, {"CAREER_RADAR_REVIEW_QUEUE": str(self.path)}):
            return AppTest.from_file(str(ROOT / "review_app.py")).run(timeout=30)

    def test_no_file_opens_empty_without_creating_demo_labels(self):
        with patch.dict(os.environ, {"CAREER_RADAR_REVIEW_QUEUE": ""}):
            app = AppTest.from_file(str(ROOT / "review_app.py")).run(timeout=30)
        self.assertFalse(app.exception)
        self.assertEqual(app.title[0].value, "Private extraction review")
        self.assertTrue(any("No review queue is loaded" in item.value for item in app.info))
        self.assertEqual(len(app.radio), 0)

    def test_only_explicit_save_counts_and_clear_does_not_reload_local_input(self):
        app = self.app()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value, "0 / 2")
        self.assertEqual(len(app.code), 2)
        self.assertIn(app.code[0].value, app.code[1].value)
        app.radio[0].set_value("accepted")
        app.text_area[0].set_value("Reviewed source in context")
        self.assertEqual(app.session_state["private_review_annotations"][app.selectbox(key="private_review_selected").value]["status"], "unreviewed")
        next(button for button in app.button if button.label == "Save decision").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value, "1 / 2")
        self.assertEqual(self.path.read_bytes(), self.original)
        next(button for button in app.button if button.label == "Clear session").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.radio), 0)
        self.assertNotIn("private_review_annotations", app.session_state)
        self.assertTrue(any("No review queue is loaded" in item.value for item in app.info))
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_uncertain_is_saved_but_not_counted_as_precision_review(self):
        app = self.app()
        app.radio[0].set_value("uncertain")
        app.text_area[0].set_value("Context is insufficient")
        next(button for button in app.button if button.label == "Save decision").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value, "0 / 2")
        self.assertEqual(app.metric[3].value, "1")
        self.assertEqual(app.metric[4].value, "Not available")
        self.assertEqual(app.metric[5].value, "Not available")

    def test_category_and_status_filters_keep_completed_decisions(self):
        app = self.app()
        app.radio[0].set_value("rejected")
        next(button for button in app.button if button.label == "Save decision").click().run()
        app.selectbox(key="private_review_status").set_value("unreviewed").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value, "1 / 2")
        self.assertEqual(len(app.selectbox(key="private_review_selected").options), 1)
        app.selectbox(key="private_review_status").set_value("rejected").run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.selectbox(key="private_review_selected").options), 1)
        self.assertEqual(app.radio[0].value, "rejected")

    def test_invalid_file_is_recoverable_and_does_not_show_a_traceback(self):
        self.path.write_text("not,a,review\nwrong,values,here\n", encoding="utf-8")
        app = self.app()
        self.assertFalse(app.exception)
        self.assertTrue(any("configured queue could not be loaded" in item.value for item in app.error))
        self.assertEqual(len(app.radio), 0)
