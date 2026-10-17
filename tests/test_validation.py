import unittest
from pathlib import Path

from career_radar.analytics import read_csv
from career_radar.build_snapshot import build_snapshot_payload
from career_radar.ingest import read_jobs
from career_radar.normalise import (
    classify_role,
    classify_work_pattern,
    extract_skills,
    load_taxonomy,
)
from career_radar.validation import build_quality_profile, build_review_queue, evaluate_review


ROOT = Path(__file__).resolve().parents[1]


class ValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source_jobs = read_jobs(ROOT / "tests/fixtures/authorised_sample_jobs.csv")
        taxonomy = load_taxonomy(ROOT / "data/reference/skills.csv")
        cls.jobs = []
        cls.evidence = []
        seen = set()
        for source in source_jobs:
            identity = (source["title"], source["employer_name"], source["description_text"])
            if identity in seen:
                continue
            seen.add(identity)
            role_name, _ = classify_role(source["title"])
            job = {
                **source,
                "source_name": "Fixture",
                "role_name": role_name or "Unclassified",
                "work_pattern": classify_work_pattern(
                    source["location_text"] + " " + source["description_text"]
                ),
            }
            cls.jobs.append(job)
            cls.evidence.extend(
                {**skill, "canonical_url": source["canonical_url"]}
                for skill in extract_skills(source["description_text"], taxonomy)
            )

    def test_quality_profile_reports_duplicate_and_employer_risk(self):
        profile = build_quality_profile(self.jobs, self.evidence, source_row_count=4)
        self.assertEqual(profile["sample_size"], 3)
        self.assertEqual(profile["duplicates_removed"], 1)
        self.assertEqual(profile["duplicate_rate_pct"], 25.0)
        self.assertEqual(profile["classified_role_pct"], 100.0)
        self.assertEqual(profile["unique_employer_count"], 3)

    def test_review_queue_is_reproducible_and_contains_context(self):
        first = build_review_queue(self.jobs, self.evidence, sample_size=5, seed=7)
        second = build_review_queue(self.jobs, self.evidence, sample_size=5, seed=7)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 5)
        self.assertTrue(all(row["source_phrase"] in row["context"] for row in first))

        complete_queue = build_review_queue(self.jobs, self.evidence, sample_size=100, seed=7)
        self.assertEqual(len(complete_queue), len(self.evidence))

    def test_evaluation_scores_reviewed_rows_and_threshold(self):
        rows = [
            {"category": "Data", "reviewer_label": "accepted"} for _ in range(90)
        ] + [{"category": "Data", "reviewer_label": "rejected"} for _ in range(10)]
        evaluation = evaluate_review(rows)
        self.assertEqual(evaluation["precision_pct"], 90.0)
        self.assertTrue(evaluation["publication_threshold_met"])
        self.assertEqual(evaluation["precision_95_ci_pct"], [82.6, 94.5])

    def test_invalid_review_label_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_review([{"category": "Data", "reviewer_label": "maybe"}])

    def test_validated_label_alone_cannot_enable_publication(self):
        without_review = build_snapshot_payload(
            self.jobs, self.evidence, "Fixture", "validated"
        )
        self.assertFalse(without_review["metadata"]["publish_allowed"])

        with_review = build_snapshot_payload(
            self.jobs,
            self.evidence,
            "Fixture",
            "validated",
            evaluation={"publication_threshold_met": True},
        )
        self.assertTrue(with_review["metadata"]["publish_allowed"])


if __name__ == "__main__":
    unittest.main()
