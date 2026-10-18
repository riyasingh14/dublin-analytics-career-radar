"""Hand-calculated metric and denominator checks for source-backed co-mentions."""
import unittest

from career_radar.constellation import (
    association_metrics, build_constellation, pair_evidence, safe_source_url,
)


def posting(number, role="Data Analyst", location="Dublin, Ireland"):
    return {"canonical_url": f"https://jobs.example/{number}", "title": f"Job {number}",
            "role_name": role, "location_text": location, "employer_name": "Example"}


def mention(number, skill, phrase=None):
    return {"canonical_url": f"https://jobs.example/{number}", "skill_id": skill,
            "skill_name": skill.upper(), "source_phrase": phrase or skill,
            "extraction_version": "test-v1", "extraction_method": "rule"}


def sample():
    # Four unique jobs, including a posting with zero skills. A=3, B=2, AB=2.
    return {"postings": [posting(1), posting(2), posting(3, "Engineer", "Cork, Ireland"),
                         posting(4), posting(1)],
            "evidence": [mention(1, "a"), mention(1, "a", "A again"), mention(1, "b"),
                         mention(2, "a"), mention(2, "b"), mention(3, "a"),
                         mention("orphan", "c")]}


class ConstellationTests(unittest.TestCase):
    def test_hand_calculated_pair_metrics(self):
        result = build_constellation(sample())
        self.assertEqual(result["sample_size"], 4)
        pair = result["pairs"][0]
        self.assertEqual((pair["count_a"], pair["count_b"], pair["pair_count"]), (3, 2, 2))
        self.assertAlmostEqual(pair["support"], 1 / 2)
        self.assertAlmostEqual(pair["jaccard"], 2 / 3)
        self.assertAlmostEqual(pair["lift"], 4 / 3)
        self.assertEqual(result["nodes"][0]["sample_share"], 3 / 4)

    def test_filters_recompute_denominator_including_no_skill_jobs(self):
        result = build_constellation(sample(), geography="Dublin", role="Data Analyst")
        self.assertEqual(result["sample_size"], 3)
        self.assertEqual(result["jobs_with_skills"], 2)
        self.assertEqual(result["pairs"][0]["support"], 2 / 3)
        self.assertEqual(result["pairs"][0]["jaccard"], 1)
        self.assertEqual(result["pairs"][0]["lift"], 1.5)
        other = build_constellation(sample(), geography="Rest of Ireland")
        self.assertEqual(other["sample_size"], 1)
        self.assertEqual(other["nodes"][0]["job_count"], 1)
        self.assertEqual(other["pairs"], [])

    def test_duplicate_mentions_and_orphans_do_not_create_edges(self):
        result = build_constellation(sample())
        self.assertEqual(len(result["pairs"]), 1)
        self.assertEqual({node["skill_id"] for node in result["nodes"]}, {"a", "b"})
        self.assertTrue(all(pair["skill_a"] != pair["skill_b"] for pair in result["pairs"]))
        sources = pair_evidence(result, "a", "b")
        self.assertEqual(len(sources), result["pairs"][0]["pair_count"])
        self.assertEqual(len(sources[0]["skills"]["a"]), 2)
        self.assertEqual(pair_evidence(result, "a", "a"), [])

    def test_source_evidence_respects_filters_and_posting_metadata(self):
        snapshot = sample()
        snapshot["evidence"][0]["title"] = "Wrong metadata"
        result = build_constellation(snapshot, role="Data Analyst", geography="Dublin")
        for source in pair_evidence(result, "a", "b"):
            self.assertEqual(source["posting"]["geography"], "Dublin")
            self.assertNotEqual(source["posting"]["title"], "Wrong metadata")
            self.assertTrue(source["skills"]["b"][0]["source_phrase"])

    def test_empty_sample_zero_and_sparse_display_guards(self):
        self.assertEqual(association_metrics(0, 0, 0, 0), {"support": 0, "jaccard": 0, "lift": 0})
        result = build_constellation(sample(), role="Nonexistent")
        self.assertEqual(result["sample_size"], 0)
        self.assertEqual(result["pairs"], [])
        self.assertFalse(result["network_eligible"])
        self.assertFalse(build_constellation(sample())["eligible_pairs"])
        result = build_constellation(sample(), min_sample_size=4, min_pair_count=2)
        self.assertTrue(result["network_eligible"])
        self.assertEqual(len(result["eligible_pairs"]), 1)
        self.assertEqual(build_constellation(sample(), min_sample_size=4, min_pair_count=3)["eligible_pairs"], [])

    def test_ireland_group_includes_unspecified_but_excludes_belfast(self):
        snapshot = {"postings": [posting(1), posting(2, location="Cork, Ireland"),
                                 posting(3, location="Ireland"), posting(4, location="Belfast, Northern Ireland")],
                    "evidence": []}
        self.assertEqual(build_constellation(snapshot, geography="Ireland")["sample_size"], 3)

    def test_legacy_snapshot_rebuild_required(self):
        with self.assertRaisesRegex(ValueError, "Rebuild"):
            build_constellation({"evidence": sample()["evidence"], "market": {"sample_size": 4}})
        for counts in [(1, 1, 2, 3), (3, 3, 0, 4), (-1, 0, 0, 0)]:
            with self.assertRaises(ValueError):
                association_metrics(*counts)

    def test_only_safe_source_links_are_exposed(self):
        self.assertEqual(safe_source_url("https://jobs.example/1"), "https://jobs.example/1")
        for value in ["javascript:alert(1)", "data:text/html,hi", "//jobs.example", "https://user:secret@jobs.example", "https://[bad"]:
            self.assertIsNone(safe_source_url(value))


if __name__ == "__main__":
    unittest.main()
