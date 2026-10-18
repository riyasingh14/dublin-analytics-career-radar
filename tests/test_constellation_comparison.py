"""Hand-counted cross-role denominators and isolated fictional comparison fixture."""
import unittest
from pathlib import Path

from career_radar.constellation_comparison import build_role_comparison
from career_radar.constellation_comparison_demo import comparison_demo
from career_radar.demo import constellation_demo
from career_radar.normalise import load_taxonomy


class RoleComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.taxonomy = load_taxonomy(Path(__file__).resolve().parents[1] / "data/reference/skills.csv")

    def test_hand_counted_shared_axis_includes_zero_skill_postings(self):
        snapshot = {"postings": [
            {"canonical_url": "fixture://1", "role_name": "A", "location_text": "Dublin, Ireland"},
            {"canonical_url": "fixture://2", "role_name": "A", "location_text": "Dublin, Ireland"},
            {"canonical_url": "fixture://3", "role_name": "B", "location_text": "Cork, Ireland"},
        ], "evidence": [
            {"canonical_url": "fixture://1", "skill_id": "sql"},
            {"canonical_url": "fixture://1", "skill_id": "sql"},
            {"canonical_url": "fixture://3", "skill_id": "python"},
            {"canonical_url": "fixture://orphan", "skill_id": "excel"},
        ]}
        result = build_role_comparison(snapshot, self.taxonomy)
        sql = next(row for row in result["skills"] if row["skill_id"] == "sql")
        self.assertEqual(sql["category"], "Data")
        self.assertEqual(sql["values"], [
            {"role": "A", "job_count": 1, "sample_size": 2, "share": .5},
            {"role": "B", "job_count": 0, "sample_size": 1, "share": 0},
        ])
        filtered = build_role_comparison(snapshot, self.taxonomy, geography="Dublin")
        self.assertEqual(filtered["skills"][0]["values"][1]["share"], None)
        self.assertEqual(filtered["roles"][0]["jobs_with_skills"], 1)
        self.assertEqual({r["skill_id"] for r in result["skills"]}, {"sql", "python"})

    def test_comparison_fixture_is_separate_and_has_truthful_geography_and_coverage(self):
        original = constellation_demo(self.taxonomy)
        comparison = comparison_demo(self.taxonomy)
        self.assertEqual(len(original["postings"]), 30)
        self.assertEqual(len(comparison["postings"]), 90)
        self.assertFalse(comparison["metadata"]["publish_allowed"])
        result = build_role_comparison(comparison, self.taxonomy)
        self.assertEqual([r["sample_size"] for r in result["roles"]], [30, 30, 30])
        self.assertEqual([r["jobs_with_skills"] for r in result["roles"]], [29, 30, 29])
        dublin = build_role_comparison(comparison, self.taxonomy, geography="Dublin")
        rest = build_role_comparison(comparison, self.taxonomy, geography="Rest of Ireland")
        self.assertEqual([r["sample_size"] for r in dublin["roles"]], [20, 20, 20])
        self.assertEqual([r["sample_size"] for r in rest["roles"]], [10, 10, 10])

    def test_empty_and_unclassified_samples(self):
        self.assertEqual(build_role_comparison({"postings": [], "evidence": []}, self.taxonomy)["skills"], [])
        result = build_role_comparison({"postings": [{"canonical_url": "fixture://1"}], "evidence": []}, self.taxonomy)
        self.assertEqual(result["roles"], [{"role": "Unclassified", "sample_size": 1, "jobs_with_skills": 0}])


if __name__ == "__main__":
    unittest.main()
