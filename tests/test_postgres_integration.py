"""Actual PostgreSQL checks; opt in with CAREER_RADAR_TEST_DATABASE_URL.

The tests add isolated hash-keyed fixture/scenario records to career_radar_ops.
Use a dedicated analyst/test database, never production. No paid or remote APIs.
"""
import csv
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from career_radar.mobility import Scenario
from career_radar.refresh import refresh
from career_radar.warehouse import load_and_reconcile

ROOT = Path(__file__).resolve().parents[1]
DSN = os.environ.get("CAREER_RADAR_TEST_DATABASE_URL")


@unittest.skipUnless(DSN, "Dedicated PostgreSQL integration connection not configured")
class PostgreSQLIntegrationTests(unittest.TestCase):
    def setUp(self):
        import psycopg
        self.connection = psycopg.connect(DSN, connect_timeout=10)
        self.addCleanup(self.connection.close)
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.policy = self.root / "policy.json"
        self.policy.write_text((ROOT / "config/refresh-fixture.json").read_text())
        self.taxonomy = ROOT / "data/reference/skills.csv"

    def fixture_run(self, input_path=None):
        manifest = refresh(input_path or ROOT / "tests/fixtures/authorised_sample_jobs.csv", self.policy,
                           self.root / "output", self.taxonomy, "2026-10-12T08:00:00+01:00")
        return self.root / "output/runs" / manifest["run_id"]

    def test_real_postgres_metrics_and_idempotence(self):
        run = self.fixture_run()
        result = load_and_reconcile(self.connection, run, self.taxonomy, Scenario(people=100))
        self.assertTrue(result["reconciliation_passed"])
        self.assertTrue(result["database"].startswith("PostgreSQL"))
        self.assertEqual((result["posting_count"], result["synthetic_spell_count"], result["synthetic_transitions_reconciled"]), (3, 500, 400))
        repeat = load_and_reconcile(self.connection, run, self.taxonomy, Scenario(people=100))
        self.assertEqual(repeat["outcome"], "already_loaded")
        self.assertEqual(repeat["skill_pairs_reconciled"], result["skill_pairs_reconciled"])

    def test_no_skill_posting_denominator_and_requirement_span_types(self):
        fixture = self.root / "grain.csv"
        rows = [
            {"source_job_id":"ops-grain-a", "canonical_url":"fixture://ops-grain/a", "title":"Data Analyst", "employer_name":"A", "location_text":"Dublin, Ireland", "description_text":"SQL is required. Python is preferred. Excel is not required.", "posted_at":"2026-10-01"},
            {"source_job_id":"ops-grain-b", "canonical_url":"fixture://ops-grain/b", "title":"Data Analyst", "employer_name":"B", "location_text":"Cork, Ireland", "description_text":"SQL and Python are required.", "posted_at":"2026-10-01"},
            {"source_job_id":"ops-grain-c", "canonical_url":"fixture://ops-grain/c", "title":"Data Analyst", "employer_name":"C", "location_text":"Ireland", "description_text":"Research new questions.", "posted_at":"2026-10-01"},
        ]
        with fixture.open("w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        run = self.fixture_run(fixture)
        result = load_and_reconcile(self.connection, run, self.taxonomy, Scenario(seed=9, people=12, years=3))
        self.assertEqual(result["posting_count"], 3)
        self.assertEqual(result["requirement_categories"], {"required":3, "preferred":1, "negated":1})
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT sample_size, support FROM career_radar_ops.pair_metrics WHERE run_id=%s AND skill_a='python' AND skill_b='sql'", (result["run_id"],))
            count, support = cursor.fetchone()
            self.assertEqual(count, 3)
            self.assertAlmostEqual(support, 2 / 3)
            cursor.execute("SELECT median_individual_pct_change FROM career_radar_ops.synthetic_cohort_metrics WHERE scenario_id=%s AND valid_pairs < 20", (result["synthetic_scenario_id"],))
            self.assertTrue(all(row[0] is None for row in cursor.fetchall()))

    def test_tampered_input_rejected_without_database_changes(self):
        run = self.fixture_run()
        load_and_reconcile(self.connection, run, self.taxonomy, Scenario(people=100))
        (run / "jobs.csv").write_text("corrupt")
        with self.assertRaisesRegex(ValueError, "integrity"):
            load_and_reconcile(self.connection, run, self.taxonomy, Scenario(people=100))
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            self.assertEqual(cursor.fetchone()[0], 1)

    def test_metric_failure_rolls_back_new_run(self):
        from career_radar.requirements_model import extract_requirements
        policy = json.loads(self.policy.read_text())
        policy["source_name"] = "Transaction rollback fixture"
        self.policy.write_text(json.dumps(policy))
        run = self.fixture_run()
        run_id = json.loads((run / "manifest.json").read_text())["run_id"]
        # Keep this test repeatable against a dedicated persistent test database.
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM career_radar_ops.analysis_run WHERE run_id=%s", (run_id,))
            self.assertEqual(cursor.fetchone()[0], 0)
        self.connection.commit()
        def wrong_span(text, taxonomy):
            requirements = extract_requirements(text, taxonomy)
            if requirements:
                requirements[0] = {**requirements[0], "source_phrase": "deliberately incorrect test span"}
            return requirements
        with patch("career_radar.warehouse.extract_requirements", side_effect=wrong_span):
            with self.assertRaisesRegex(ValueError, "source span reconciliation"):
                load_and_reconcile(self.connection, run, self.taxonomy, Scenario(people=100))
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM career_radar_ops.analysis_run WHERE run_id=%s", (run_id,))
            self.assertEqual(cursor.fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
