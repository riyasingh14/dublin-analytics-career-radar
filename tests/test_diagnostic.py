import unittest
from pathlib import Path
from career_radar.normalise import load_taxonomy
from career_radar.requirements_model import extract_requirements
from career_radar.diagnostic import analyze_description

ROOT = Path(__file__).resolve().parents[1]

class RequirementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.taxonomy = load_taxonomy(ROOT / "data/reference/skills.csv")

    def kinds(self, text):
        return {row["skill_id"]: row["requirement_type"] for row in extract_requirements(text, self.taxonomy)}

    def test_mixed_clauses_and_negation(self):
        cases = [
            ("SQL is required; Python is preferred.", {"sql":"required", "python":"preferred"}),
            ("SQL required and Python is not required.", {"sql":"required", "python":"negated"}),
            ("No prior experience with SQL required; Python preferred.", {"sql":"negated", "python":"preferred"}),
            ("Required: SQL and Python. Excel is a bonus.", {"sql":"required", "python":"required", "excel":"preferred"}),
            ("SQL is not required, but Python is essential.", {"sql":"negated", "python":"required"}),
            ("No SQL or Python experience is required.", {"sql":"negated", "python":"negated"}),
            ("No SQL experience is required and Python is mandatory.", {"sql":"negated", "python":"required"}),
            ("SQL, Python and Excel are required.", {"sql":"required", "python":"required", "excel":"required"}),
            ("We use SQL, Python is required.", {"sql":"uncertain", "python":"required"}),
            ("Required: SQL, Python, Excel.", {"sql":"required", "python":"required", "excel":"required"}),
            ("No Excel experience required.", {"excel":"negated"}),
            ("Use SQL and Python to build reports.", {"sql":"uncertain", "python":"uncertain"}),
            ("Python is optional, SQL is mandatory.", {"python":"preferred", "sql":"required"}),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(self.kinds(text), expected)

    def test_headings_and_offsets_and_repeat_mentions(self):
        text = "Essential skills:\nSQL\nPreferred skills:\nPython\nResponsibilities:\nUse SQL."
        rows = extract_requirements(text, self.taxonomy)
        self.assertEqual([row["requirement_type"] for row in rows], ["required", "preferred", "uncertain"])
        self.assertEqual(rows, extract_requirements(text, self.taxonomy))
        self.assertEqual(len({row["requirement_id"] for row in rows}), 3)
        for row in rows:
            self.assertEqual(text[row["start"]:row["end"]], row["source_phrase"])
            self.assertIn(row["source_phrase"], row["source_text"])

    def test_plain_section_headings_end_required_scope(self):
        for heading in ("Benefits", "About us", "Responsibilities", "What we offer:"):
            text = f"Required skills:\nSQL\n{heading}\nPython training provided."
            self.assertEqual(self.kinds(text), {"sql": "required", "python": "uncertain"})

    def test_contextual_examples_are_not_mandatory(self):
        rows = extract_requirements('Examples such as SQL are required reading.', self.taxonomy)
        self.assertEqual(rows[0]["requirement_type"], "uncertain")

    def test_every_finding_has_span_or_absent_field(self):
        text = "Junior analyst. 5 years required. Salary €50000. SQL required; Python preferred."
        result = analyze_description(text, self.taxonomy)
        self.assertTrue(any(row["rule"] == "consistency.entry_experience" for row in result["findings"]))
        for finding in result["findings"]:
            if finding["start"] is None:
                self.assertTrue(finding["absent_field"])
            else:
                self.assertEqual(text[finding["start"]:finding["end"]], finding["source_phrase"])
            self.assertTrue(finding["rationale"])
        self.assertIsNone(result["benchmark"])
        self.assertTrue(result["rule_version"])

    def test_completeness_unknown_is_not_missing(self):
        result = analyze_description("Competitive salary. Flexible working.", self.taxonomy)
        self.assertEqual(result["completeness"]["salary"]["status"], "unknown")
        self.assertEqual(result["completeness"]["location"]["status"], "missing")
        result = analyze_description("Dublin, permanent, hybrid. Salary EUR 50000 per year. You will create reports.", self.taxonomy)
        self.assertTrue(all(row["status"] == "present" for row in result["completeness"].values()))

    def test_empty_input_and_no_invented_salary(self):
        result = analyze_description("", self.taxonomy)
        self.assertFalse(result["requirements"])
        self.assertTrue(any(row["rule"] == "quality.empty" for row in result["findings"]))
        self.assertFalse(any("50000" in row["suggestion"] for row in result["findings"]))


    def test_ui_explicit_demo_review_and_reset(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_string(
            "from pathlib import Path\n"
            "from career_radar.normalise import load_taxonomy\n"
            "from career_radar.ui.diagnostic import render\n"
            f"render(None, load_taxonomy(Path({str(ROOT / 'data/reference/skills.csv')!r})))"
        ).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.text_area[0].value, "")
        app.radio[0].set_value("Synthetic example").run()
        self.assertFalse(app.exception)
        original = app.text_area[0].value
        self.assertIn("Synthetic demonstration", original)
        app.selectbox[0].set_value("Dismissed").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.text_area[0].value, original)
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.radio[0].value, "Paste text")

if __name__ == "__main__":
    unittest.main()
