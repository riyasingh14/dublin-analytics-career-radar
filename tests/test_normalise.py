import unittest
from pathlib import Path

from career_radar.normalise import classify_role, deduplication_key, extract_skills, load_taxonomy
from career_radar.greenhouse import html_to_text, normalise_greenhouse_job
from career_radar.adzuna import normalise_adzuna_job, planned_request_count


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

    def test_adzuna_job_retains_source_url_and_description(self):
        job = {
            "id": "az-123",
            "redirect_url": "https://www.adzuna.ie/details/az-123",
            "title": "Business Analyst",
            "company": {"display_name": "Example Company"},
            "location": {"display_name": "Dublin"},
            "description": "Gather requirements and use SQL.",
            "created": "2026-10-12T00:00:00Z",
        }
        normalised = normalise_adzuna_job(job)
        self.assertEqual(normalised["source_job_id"], "az-123")
        self.assertEqual(normalised["canonical_url"], "https://www.adzuna.ie/details/az-123")

    def test_adzuna_request_plan_is_explicit(self):
        self.assertEqual(planned_request_count(("data analyst", "bi analyst"), 2), 4)
        with self.assertRaises(ValueError):
            planned_request_count(("data analyst",), 0)


if __name__ == "__main__":
    unittest.main()
