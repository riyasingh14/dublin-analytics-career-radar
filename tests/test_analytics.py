import unittest
from pathlib import Path

from career_radar.analytics import (
    build_market_summary,
    load_proof_recommendations,
    recommend_proof_of_work,
    build_evidence_records,
)
from career_radar.ingest import read_jobs
from career_radar.normalise import classify_role, classify_work_pattern, extract_skills, load_taxonomy


ROOT = Path(__file__).resolve().parents[1]


class AnalyticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source_jobs = read_jobs(ROOT / "tests/fixtures/authorised_sample_jobs.csv")
        taxonomy = load_taxonomy(ROOT / "data/reference/skills.csv")
        seen = set()
        cls.jobs = []
        cls.evidence = []
        for source in source_jobs:
            identity = (source["title"], source["employer_name"], source["description_text"])
            if identity in seen:
                continue
            seen.add(identity)
            role_name, _ = classify_role(source["title"])
            cls.jobs.append(
                {
                    **source,
                    "role_name": role_name or "Unclassified",
                    "work_pattern": classify_work_pattern(
                        source["location_text"] + " " + source["description_text"]
                    ),
                }
            )
            for skill in extract_skills(source["description_text"], taxonomy):
                cls.evidence.append({**skill, "canonical_url": source["canonical_url"]})

    def test_market_summary_uses_unique_jobs_as_denominator(self):
        summary = build_market_summary(self.jobs, self.evidence)
        self.assertEqual(summary["sample_size"], 3)
        sql = next(row for row in summary["top_skills"] if row["skill_id"] == "sql")
        self.assertEqual(sql["job_count"], 2)
        self.assertEqual(sql["sample_share_pct"], 66.7)

    def test_recommendation_excludes_current_skills_and_retains_evidence(self):
        summary = build_market_summary(self.jobs, self.evidence)
        proof = load_proof_recommendations(ROOT / "data/reference/skills.csv")
        recommendations = recommend_proof_of_work(summary, "Data Analyst", {"sql"}, proof)
        self.assertTrue(recommendations)
        self.assertNotIn("sql", {row["skill_id"] for row in recommendations})
        self.assertTrue(all(row["reason"] and row["proof_of_work"] for row in recommendations))

    def test_unclassified_jobs_stay_in_sample_but_not_target_role_recommendations(self):
        jobs = [{**job, "role_name": "Unclassified"} for job in self.jobs]
        summary = build_market_summary(jobs, self.evidence)
        self.assertEqual(summary["sample_size"], 3)
        self.assertEqual(summary["role_counts"]["Unclassified"], 3)
        self.assertTrue(summary["top_skills"])
        self.assertNotIn("Unclassified", summary["role_skills"])

    def test_source_evidence_join_omits_orphans_and_profile_data(self):
        orphan = {**self.evidence[0], "canonical_url": "https://example.test/not-in-sample"}
        records = build_evidence_records(self.jobs, [*self.evidence, orphan])
        self.assertEqual(len(records), len(self.evidence))
        self.assertTrue(all(row["source_phrase"] and row["title"] and row["canonical_url"] for row in records))
        self.assertFalse(any("description_text" in row or "posterFullName" in row for row in records))


if __name__ == "__main__":
    unittest.main()
