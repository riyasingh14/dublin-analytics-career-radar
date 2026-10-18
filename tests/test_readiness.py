import copy
import json
import unittest
from pathlib import Path

from career_radar.normalise import load_taxonomy
from career_radar.readiness import assess_readiness, export_analysis, hypothetical_readiness
from career_radar.requirements_model import extract_requirements


def requirement(identifier, kind="required", skill=None):
    return {"requirement_id": identifier, "skill_id": skill or identifier, "skill_name": skill or identifier, "requirement_type": kind, "source_phrase": skill or identifier, "source_text": "Explicit requirement context"}


class ReadinessTests(unittest.TestCase):
    def test_weighted_score_and_exclusions(self):
        requirements = [requirement("sql"), requirement("python", "preferred"), requirement("excel", "uncertain"), requirement("r", "negated")]
        result = assess_readiness(requirements, {"sql": {"status": "supported", "note": "Built a SQL reconciliation project"}, "python": {"status": "partial", "note": "Implemented CSV transforms; tests pending"}})
        self.assertEqual(result["alignment_pct"], 87.5)
        self.assertEqual(result["coverage_pct"], 100)
        self.assertEqual(len(result["excluded_requirements"]), 2)

    def test_unknown_excluded_and_low_coverage_hides_index(self):
        requirements = [requirement("a"), requirement("b", "preferred")]
        result = assess_readiness(requirements, {"a": {"status": "supported", "note": "Project"}})
        self.assertEqual(result["coverage_pct"], 75)
        self.assertEqual(result["unassessed_weight"], 1)
        self.assertIsNone(result["alignment_pct"])

    def test_coverage_boundary_and_missing_zero_credit(self):
        requirements = [requirement(str(i), "preferred") for i in range(5)]
        evidence = {str(i): {"status": "missing"} for i in range(4)}
        result = assess_readiness(requirements, evidence)
        self.assertEqual(result["coverage_pct"], 80)
        self.assertEqual(result["alignment_pct"], 0)

    def test_no_confirmed_skills_means_no_index_or_coverage(self):
        for requirements in ([], [requirement("a", "uncertain")]):
            result = assess_readiness(requirements)
            self.assertIsNone(result["coverage_pct"])
            self.assertIsNone(result["alignment_pct"])

    def test_supported_without_evidence_stays_unknown(self):
        result = assess_readiness([requirement("a")], {"a": {"status": "supported", "note": "  "}})
        self.assertEqual(result["rows"][0]["status"], "unknown")
        self.assertIsNotNone(result["rows"][0]["issue"])
        self.assertEqual(result["assessed_weight"], 0)

    def test_repeated_skill_once_strongest_classification_and_conservative_context(self):
        requirements = [requirement("1", "required", "sql"), requirement("2", "preferred", "sql"), requirement("3", "required", "sql")]
        evidence = {"1": {"status": "supported", "note": "Project"}, "2": {"status": "missing"}, "3": {"status": "partial", "note": "Coursework"}}
        result = assess_readiness(requirements, evidence)
        self.assertEqual(result["total_weight"], 3)
        self.assertEqual(result["confirmed_skill_count"], 1)
        self.assertEqual(result["alignment_pct"], 50)

    def test_scenario_is_separate_and_labelled_and_does_not_mutate_inputs(self):
        requirements = [requirement("a")]
        evidence = {"a": {"status": "missing"}}
        before = copy.deepcopy((requirements, evidence))
        scenario = hypothetical_readiness(requirements, evidence, "a", "Planned project")
        self.assertEqual((requirements, evidence), before)
        self.assertEqual(scenario["alignment_pct"], 100)
        self.assertEqual(scenario["rows"][0]["evidence_provenance"], "hypothetical")
        self.assertIn("Hypothetical", scenario["label"])
        self.assertEqual(assess_readiness(requirements, evidence)["alignment_pct"], 0)
        with self.assertRaises(ValueError):
            hypothetical_readiness(requirements, evidence, "a", " ")

    def test_export_omits_free_text_identity_and_contact(self):
        requirements = [requirement("a")]
        requirements[0]["source_text"] = "Contact hiring@example.com"
        result = assess_readiness(requirements, {"a": {"status": "supported", "note": "Contact me@example.com +353123456789"}})
        report = json.dumps(export_analysis(result))
        self.assertNotIn("@example.com", report)
        self.assertNotIn("+353123456789", report)
        self.assertIn("self-reported", report)

    def test_extractor_integration_preferred_and_negated_are_not_required(self):
        taxonomy = load_taxonomy(Path(__file__).resolve().parents[1] / "data/reference/skills.csv")
        rows = extract_requirements("SQL is required. Python is preferred. No Excel experience required.", taxonomy)
        self.assertTrue(rows)
        result = assess_readiness(rows)
        self.assertEqual(result["total_weight"], 4)
        self.assertTrue(any(r["requirement_type"] == "negated" for r in result["excluded_requirements"]))

    def test_ui_evidence_submission_hypothetical_and_clear(self):
        from streamlit.testing.v1 import AppTest

        app = AppTest.from_string('''
from pathlib import Path
from career_radar.normalise import load_taxonomy
from career_radar.ui.readiness import render
render(None, load_taxonomy(Path("data/reference/skills.csv")))
''').run()
        self.assertFalse(app.exception)
        app.radio[0].set_value("Demonstration description").run()
        self.assertFalse(app.exception)
        for select in app.selectbox:
            if select.label == "Evidence status":
                select.set_value("supported")
        for note in app.text_input:
            note.set_value("Built an assessed coursework project")
        next(button for button in app.button if button.label == "Assess self-reported evidence").click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any(metric.value == "100.0 / 100" for metric in app.metric))
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.radio[0].value, "Paste a description")
        self.assertEqual(len(app.metric), 0)
        self.assertNotIn("readiness_result", app.session_state)
        self.assertNotIn("readiness_scenario", app.session_state)

    def test_ui_hypothetical_keeps_baseline_and_changing_source_clears_results(self):
        from streamlit.testing.v1 import AppTest

        app = AppTest.from_string('''
from pathlib import Path
from career_radar.normalise import load_taxonomy
from career_radar.ui.readiness import render
render(None, load_taxonomy(Path("data/reference/skills.csv")))
''').run()
        app.radio[0].set_value("Demonstration description").run()
        for select in app.selectbox:
            if select.label == "Evidence status":
                select.set_value("missing")
        next(b for b in app.button if b.label == "Assess self-reported evidence").click().run()
        self.assertEqual(app.session_state["readiness_result"]["alignment_pct"], 0)
        next(t for t in app.text_input if t.label == "Planned evidence").set_value("A planned SQL reporting project")
        next(b for b in app.button if b.label == "Compare hypothetical evidence").click().run()
        self.assertFalse(app.exception)
        self.assertGreater(app.session_state["readiness_scenario"]["alignment_pct"], 0)
        self.assertEqual(app.session_state["readiness_result"]["alignment_pct"], 0)
        app.radio[0].set_value("Paste a description").run()
        self.assertNotIn("readiness_result", app.session_state)
        self.assertNotIn("readiness_scenario", app.session_state)

    def test_ui_requirement_correction_preserves_extraction_and_resets(self):
        from streamlit.testing.v1 import AppTest

        app = AppTest.from_string('''
from pathlib import Path
from career_radar.normalise import load_taxonomy
from career_radar.ui.readiness import render
render(None, load_taxonomy(Path("data/reference/skills.csv")))
''').run()
        app.text_area[0].set_value("Our team uses SQL.").run()
        classification = next(s for s in app.selectbox if s.label == "Confirm or correct requirement classification")
        self.assertEqual(classification.value, "uncertain")
        correction_key = classification.key
        classification.set_value("required")
        next(s for s in app.selectbox if s.label == "Evidence status").set_value("missing")
        next(b for b in app.button if b.label == "Assess self-reported evidence").click().run()
        self.assertFalse(app.exception)
        row = app.session_state["readiness_result"]["rows"][0]
        self.assertEqual(row["requirement_type"], "required")
        self.assertEqual(row["extracted_requirement_type"], "uncertain")
        self.assertEqual(row["classification_provenance"], "user-confirmed")
        self.assertTrue(row["classification_corrected"])
        self.assertEqual(app.session_state["readiness_result"]["total_weight"], 3)
        app.text_area[0].set_value("Our team uses Python.").run()
        self.assertNotIn(correction_key, app.session_state)
        self.assertNotIn("readiness_result", app.session_state)
        self.assertEqual(next(s for s in app.selectbox if s.label == "Confirm or correct requirement classification").value, "uncertain")
        app.button[0].click().run()
        self.assertEqual(app.text_area[0].value, "")
        self.assertNotIn("readiness_result", app.session_state)


if __name__ == "__main__":
    unittest.main()
