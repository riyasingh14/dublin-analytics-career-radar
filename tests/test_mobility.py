import math
import unittest
from collections import Counter
from copy import deepcopy

from career_radar.mobility import (
    LABEL, Scenario, derive_transitions, generate_histories, metadata, salary_metrics,
)


class MobilityTests(unittest.TestCase):
    def test_seed_reproducibility_and_scenario_event_identity(self):
        baseline = Scenario(people=50)
        first = generate_histories(baseline)
        self.assertEqual(first, generate_histories(baseline))
        adjusted = generate_histories(Scenario(people=50, employer_change_pct=15))
        self.assertEqual([{k: v for k, v in r.items() if k != "salary_eur_annual_fte"} for r in first],
                         [{k: v for k, v in r.items() if k != "salary_eur_annual_fte"} for r in adjusted])
        self.assertNotEqual(first, generate_histories(Scenario(seed=43, people=50)))

    def test_chronology_and_references(self):
        spells = generate_histories(Scenario(people=40))
        ids = {r["spell_id"] for r in spells}
        self.assertEqual(len(ids), 200)
        events = derive_transitions(spells)
        self.assertEqual(len(events), 160)
        self.assertEqual(len({r["transition_id"] for r in events}), len(events))
        for row in events:
            self.assertIn(row["before_spell_id"], ids)
            self.assertIn(row["after_spell_id"], ids)
        for before, after in zip(spells, spells[1:]):
            if before["person_id"] == after["person_id"]:
                self.assertEqual(before["end_date"], after["start_date"])
                self.assertGreaterEqual(after["experience_years"], before["experience_years"])
        overlap = deepcopy(spells[:2])
        overlap[1]["start_date"] = overlap[0]["start_date"]
        with self.assertRaisesRegex(ValueError, "Overlapping"):
            derive_transitions(overlap)

    def test_exclusive_categories_reconcile_and_include_counterexamples(self):
        events = derive_transitions(generate_histories())
        counts = Counter(r["category"] for r in events)
        self.assertEqual(sum(counts.values()), len(events))
        self.assertGreater(counts["Stayer"], 0)
        self.assertGreater(counts["Career break / return"], 0)
        self.assertTrue(any(" + " in c for c in counts))
        for row in events:
            if row["category"] == "Stayer":
                self.assertFalse(any(row[k] for k in ("employer_change", "occupation_change", "industry_change", "promotion")))
            if row["category"] == "Career break / return":
                self.assertFalse(row["valid_pair"])
        changes = [r["individual_pct_change"] for r in events if r["valid_pair"]]
        self.assertTrue(any(v < 0 for v in changes))
        self.assertTrue(any(v == 0 for v in changes))
        self.assertTrue(any(v > 0 for v in changes))

    def test_histories_include_adjacent_occupations_without_claiming_real_mobility(self):
        spells = generate_histories(Scenario(people=100))
        roles = {row["occupation"] for row in spells}
        self.assertTrue({"Operations Coordinator", "Finance Associate", "Customer Support Specialist"} <= roles)
        self.assertTrue(all(row["data_label"] == LABEL for row in spells))

    def paired(self, before, after):
        # Derive through the real pair-validity path rather than precomputing outcomes.
        spells = generate_histories(Scenario(people=1, years=2))
        spells[0]["salary_eur_annual_fte"] = before
        spells[1]["salary_eur_annual_fte"] = after
        return derive_transitions(spells)[0]

    def test_metrics_cuts_unchanged_and_distinct_median_definitions(self):
        rows = [self.paired(100, 50), self.paired(200, 200), self.paired(1000, 1200)]
        values = salary_metrics(rows)
        self.assertEqual(values["valid_pairs"], 3)
        self.assertEqual(values["people"], 1)
        self.assertEqual(values["valid_people"], 1)
        self.assertAlmostEqual(values["median_individual_pct_change"], 0)
        self.assertAlmostEqual(values["change_between_cohort_medians_pct"], 0)
        self.assertAlmostEqual(values["share_decreased"], 1 / 3)
        rows = [self.paired(100, 200), self.paired(200, 150), self.paired(1000, 1200)]
        values = salary_metrics(rows)
        self.assertAlmostEqual(values["median_individual_pct_change"], 20)
        self.assertAlmostEqual(values["change_between_cohort_medians_pct"], 0)
        self.assertFalse(values["comparison_available"])
        self.assertTrue(salary_metrics(rows * 7)["comparison_available"])

    def test_missing_nan_zero_negative_incomparable_pairs_and_empty(self):
        invalid = [(None, 100), (100, None), (float("nan"), 100), (100, float("inf")),
                   (0, 100), (-100, 100), (100, 0), (100, -1)]
        rows = [self.paired(a, b) for a, b in invalid]
        self.assertTrue(all(not r["valid_pair"] for r in rows))
        self.assertEqual(salary_metrics(rows)["excluded_pairs"], 8)
        self.assertIsNone(salary_metrics(rows)["median_individual_pct_change"])
        spells = generate_histories(Scenario(people=1, years=2))
        spells[1]["currency"] = "USD"
        self.assertFalse(derive_transitions(spells)[0]["valid_pair"])
        values = salary_metrics([])
        self.assertEqual(values["events"], 0)
        self.assertEqual(values["people"], 0)
        self.assertIsNone(values["share_decreased"])

    def test_labels_and_parameter_guards(self):
        self.assertEqual(metadata(Scenario())["data_label"], LABEL)
        self.assertTrue(all(r["data_label"] == LABEL for r in generate_histories(Scenario(people=2))))
        for args in ({"people": 0}, {"years": 1}, {"promotion_pct": math.nan}, {"occupation_change_pct": 40}):
            with self.assertRaises(ValueError):
                Scenario(**args)


if __name__ == "__main__":
    unittest.main()
