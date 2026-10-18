from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from career_radar.refresh import RefreshRejected, refresh
from career_radar.warehouse import verified_run

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/authorised_sample_jobs.csv"
TAXONOMY = ROOT / "data/reference/skills.csv"


class SavedRefreshTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root / "output"
        self.policy = self.root / "policy.json"
        self.config = json.loads((ROOT / "config/refresh-fixture.json").read_text())
        self.save_policy()

    def save_policy(self):
        self.policy.write_text(json.dumps(self.config))

    def run_refresh(self, input_path=FIXTURE, timestamp="2026-10-12T08:00:00+01:00"):
        return refresh(input_path, self.policy, self.output, TAXONOMY, timestamp)

    def test_repeatable_dedup_manifest_and_empty_review_labels(self):
        first = self.run_refresh()
        self.assertEqual((first["source_row_count"], first["unique_job_count"], first["duplicates_removed"]), (4, 3, 1))
        self.assertEqual((first["live_requests"], first["spend_usd"], first["publish_allowed"]), (0, 0, False))
        self.assertEqual(first["human_review_status"], "not_completed")
        pointer_before = (self.output / "latest_good.json").read_bytes()
        second = self.run_refresh()
        self.assertEqual(second["outcome"], "already_processed")
        self.assertEqual(first["run_id"], second["run_id"])
        self.assertEqual(pointer_before, (self.output / "latest_good.json").read_bytes())
        directory = self.output / "runs" / first["run_id"]
        manifest, jobs, evidence, snapshot = verified_run(directory)
        self.assertEqual(len(jobs), 3)
        self.assertEqual(len(evidence), manifest["skill_evidence_count"])
        self.assertFalse(snapshot["metadata"]["publish_allowed"])
        import csv
        with (directory / "review_queue.csv").open(newline="") as file:
            self.assertTrue(all(not row["reviewer_label"] for row in csv.DictReader(file)))

    def test_bad_input_retains_last_good_and_records_safe_reason(self):
        self.run_refresh()
        before = (self.output / "latest_good.json").read_bytes()
        bad = self.root / "bad.json"
        bad.write_text('{"secret":"do-not-log-this-text"}')
        with self.assertRaisesRegex(RefreshRejected, "json_must_be"):
            self.run_refresh(bad)
        self.assertEqual(before, (self.output / "latest_good.json").read_bytes())
        failures = list((self.output / "failures").glob("*.json"))
        self.assertEqual(len(failures), 1)
        self.assertNotIn("do-not-log", failures[0].read_text())

    def test_quality_gate_retains_last_good(self):
        self.run_refresh()
        before = (self.output / "latest_good.json").read_bytes()
        self.config["min_job_count"] = 4
        self.save_policy()
        with self.assertRaisesRegex(RefreshRejected, "quality_min_job_count"):
            self.run_refresh()
        self.assertEqual(before, (self.output / "latest_good.json").read_bytes())

    def test_recovery_after_pointer_crash_restores_completed_run(self):
        from career_radar import refresh as module
        original = module.os.replace
        def broken_pointer(source, destination):
            if Path(destination).name == "latest_good.json":
                raise OSError("simulated interrupted pointer promotion")
            original(source, destination)
        with patch.object(module.os, "replace", side_effect=broken_pointer):
            with self.assertRaises(OSError):
                self.run_refresh()
        self.assertFalse((self.output / "latest_good.json").exists())
        self.assertEqual(len(list((self.output / "runs").glob("*/manifest.json"))), 1)
        recovered = self.run_refresh()
        self.assertEqual(recovered["outcome"], "already_processed")
        self.assertEqual(json.loads((self.output / "latest_good.json").read_text())["run_id"], recovered["run_id"])

    def test_idempotent_retry_does_not_roll_back_newer_pointer(self):
        older = self.run_refresh(timestamp="2026-10-05T08:00:00+01:00")
        newer = self.run_refresh(timestamp="2026-10-12T08:00:00+01:00")
        self.run_refresh(timestamp="2026-10-05T08:00:00+01:00")
        self.assertNotEqual(older["run_id"], newer["run_id"])
        self.assertEqual(json.loads((self.output / "latest_good.json").read_text())["run_id"], newer["run_id"])
        (self.output / "latest_good.json").unlink()
        self.run_refresh(timestamp="2026-10-05T08:00:00+01:00")
        self.assertEqual(json.loads((self.output / "latest_good.json").read_text())["run_id"], newer["run_id"])

    def test_corrupt_completed_run_never_promoted(self):
        completed = self.run_refresh()
        directory = self.output / "runs" / completed["run_id"]
        (directory / "snapshot.json").write_text("{}")
        (self.output / "latest_good.json").unlink()
        with self.assertRaisesRegex(RefreshRejected, "completed_run_artifact_corrupt"):
            self.run_refresh()
        self.assertFalse((self.output / "latest_good.json").exists())
        with self.assertRaisesRegex(ValueError, "integrity"):
            verified_run(directory)

    def test_lock_rejects_overlapping_runner(self):
        self.output.mkdir()
        (self.output / ".refresh.lock").mkdir()
        with self.assertRaisesRegex(RefreshRejected, "refresh_locked"):
            self.run_refresh()

    def test_live_collection_or_nonzero_budget_rejected(self):
        for key, value in (("live_collection_enabled", True), ("max_live_requests", 1), ("max_spend_usd", .01)):
            with self.subTest(key=key):
                self.config = json.loads((ROOT / "config/refresh-fixture.json").read_text())
                self.config[key] = value
                self.save_policy()
                with self.assertRaises(RefreshRejected):
                    self.run_refresh()
        self.assertFalse((self.output / "latest_good.json").exists())

    def test_observed_requires_terms_and_actual_timestamp(self):
        self.config["dataset_kind"] = "observed"
        self.save_policy()
        with self.assertRaisesRegex(RefreshRejected, "terms_review_date_required"):
            self.run_refresh()
        self.config["terms_reviewed_on"] = "2026-10-01"
        self.save_policy()
        with self.assertRaisesRegex(RefreshRejected, "observed_collection_timestamp_required"):
            refresh(FIXTURE, self.policy, self.output, TAXONOMY)
        self.config["terms_reviewed_on"] = "2099-01-01"
        self.save_policy()
        with self.assertRaisesRegex(RefreshRejected, "terms_review_date_in_future"):
            self.run_refresh()

    def test_observed_same_week_changed_file_blocked_and_unreviewed(self):
        self.config.update(dataset_kind="observed", terms_reviewed_on="2026-10-01", display_authorized=True)
        self.save_policy()
        first = self.run_refresh()
        self.assertEqual(first["data_status"], "unreviewed")
        self.assertFalse(first["publish_allowed"])
        changed = self.root / "changed.csv"
        changed.write_bytes(FIXTURE.read_bytes().replace(b"Example Analytics", b"Example Testing"))
        with self.assertRaisesRegex(RefreshRejected, "observed_source_week_already_processed"):
            self.run_refresh(changed)
        self.assertEqual(self.run_refresh()["outcome"], "already_processed")

    def test_dublin_week_boundary_uses_local_time(self):
        result = self.run_refresh(timestamp="2026-10-11T23:30:00+00:00")
        self.assertEqual(result["collection_week_dublin"], "2026-W42")

    def test_missing_permission_and_naive_timestamp_rejected(self):
        self.config["collection_authorized"] = False
        self.save_policy()
        with self.assertRaisesRegex(RefreshRejected, "collection_permission_required"):
            self.run_refresh()
        self.config["collection_authorized"] = True
        self.save_policy()
        with self.assertRaisesRegex(RefreshRejected, "collection_timestamp_requires_timezone"):
            self.run_refresh(timestamp="2026-10-12T08:00:00")

    def test_json_saved_export_matches_csv(self):
        import csv
        with FIXTURE.open(newline="") as file:
            records = list(csv.DictReader(file))
        path = self.root / "saved.json"
        path.write_text(json.dumps(records))
        result = self.run_refresh(path)
        self.assertEqual((result["unique_job_count"], result["duplicates_removed"]), (3, 1))


if __name__ == "__main__":
    unittest.main()
