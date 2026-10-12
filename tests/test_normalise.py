import unittest
from pathlib import Path

from career_radar.normalise import classify_role, deduplication_key, extract_skills, load_taxonomy
from career_radar.greenhouse import html_to_text, normalise_greenhouse_job


ROOT = Path(__file__).resolve().parents[1]


class NormalisationTests(unittest.TestCase):
    def setUp(self):
        self.taxonomy = load_taxonomy(ROOT / "data/reference/skills.csv")

    def test_extracts_skills_with_original_phrases(self):
        evidence = extract_skills("Use SQL and PowerBI with stakeholder management.", self.taxonomy)
        self.assertEqual({row["skill_id"] for row in evidence}, {"sql", "power_bi", "stakeholder_management"})
        self.assertIn("PowerBI", {row["source_phrase"] for row in evidence})

    def test_classifies_target_role(self):
        self.assertEqual(classify_role("Senior Business Intelligence Analyst"), ("BI Analyst", 0.99))

    def test_deduplication_is_case_and_space_insensitive(self):
        first = deduplication_key("Data Analyst", "Example", "Dublin", "Use SQL")
        second = deduplication_key(" data analyst ", "example", "dublin", "use   sql")
        self.assertEqual(first, second)

    def test_greenhouse_job_retains_public_source_fields(self):
        job = {
            "id": 42,
            "absolute_url": "https://careers.example.test/jobs/42",
            "title": "Data Analyst",
            "location": {"name": "Dublin, Ireland"},
            "content": "<p>Use <strong>SQL</strong> &amp; Power BI.</p>",
            "updated_at": "2026-10-12T00:00:00Z",
        }
        normalised = normalise_greenhouse_job(job, "Example Company")
        self.assertEqual(normalised["description_text"], "Use SQL & Power BI.")
        self.assertEqual(normalised["location_text"], "Dublin, Ireland")


if __name__ == "__main__":
    unittest.main()
