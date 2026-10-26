"""Artificial reviewed fixtures exercise gates; these are not human-reviewed data."""
import copy
import contextlib
import csv
import io
from datetime import UTC, datetime, timedelta
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from career_radar.approved_release import (MAX_BYTES, load_approved_release,
                                           prepare_approved_release, _read_csv, main)
from career_radar.normalise import extract_skills, load_taxonomy
from career_radar.validation import build_review_queue, evaluate_review

NOW = datetime(2026, 10, 26, 12, tzinfo=UTC)
ROOT = Path(__file__).resolve().parents[1]


def fixture():
    # Deliberately fictional rows and test-authored labels, never shipped as a release.
    taxonomy = load_taxonomy(ROOT / "data/reference/skills.csv")
    jobs, evidence = [], []
    for index in range(101):
        job = {"source_job_id": str(index), "canonical_url": f"https://fixtures.example.test/jobs/{index}",
               "title": "Data Analyst", "employer_name": f"Fictional fixture employer {index % 4}",
               "location_text": "Dublin, Ireland", "role_name": "Data Analyst", "work_pattern": "unknown",
               "source_name": "Test fixture", "posted_at": "2026-10-24",
               "description_text": f"Fictional vacancy record {index}: " + ("SQL is essential." if index < 100 else "No listed technologies.")}
        jobs.append(job)
        evidence.extend({**item, "canonical_url": job["canonical_url"]} for item in extract_skills(job["description_text"], taxonomy))
    rows = build_review_queue(jobs, evidence, sample_size=100)
    for row in rows:
        row["reviewer_label"] = "accepted"
    evaluation = evaluate_review(rows)
    assert evaluation["publication_threshold_met"], evaluation
    policy = {"schema_version": "approved-public-release-v1", "release_id": "test-only-2026-10-26",
              "dataset_label": "Artificial test-only release", "published_at": "2026-10-26T11:00:00+00:00",
              "collected_from": "2026-10-26T10:00:00+00:00", "collected_through": "2026-10-26T10:30:00+00:00",
              "expires_at": "2026-11-02T11:00:00+00:00", "geographic_scope": "Ireland", "owner_approved": True,
              "sources": [{"source_name": "Test fixture", "homepage_url": "https://fixtures.example.test/",
                           "terms_url": "https://fixtures.example.test/test-only-terms", "terms_reviewed_on": "2026-10-25",
                           "collected_from": "2026-10-26T10:00:00+00:00", "collected_through": "2026-10-26T10:30:00+00:00",
                           "collection_authorized": True, "public_display_authorized": True,
                           "permission_basis": "Artificial test attestation; no real permission or human approval is claimed."}]}
    return jobs, evidence, evaluation, policy


class ApprovedReleaseTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.output = Path(self.directory.name) / "bundle"
        self.jobs, self.evidence, self.evaluation, self.policy = fixture()

    def prepare(self, **changes):
        values = {"jobs": self.jobs, "evidence": self.evidence, "evaluation": self.evaluation,
                  "policy": self.policy, "output_dir": self.output, "now": NOW}
        values.update(changes)
        return prepare_approved_release(**values)

    def change_snapshot(self, change, update_hash=False):
        path = self.output / "snapshot.json"
        value = json.loads(path.read_text())
        change(value)
        raw = json.dumps(value).encode()
        path.write_bytes(raw)
        if update_hash:
            manifest = json.loads((self.output / "manifest.json").read_text())
            manifest["snapshot_sha256"] = hashlib.sha256(raw).hexdigest()
            (self.output / "manifest.json").write_text(json.dumps(manifest))

    def test_roundtrip_keeps_no_skill_postings_and_recomputed_totals(self):
        result = self.prepare()
        loaded = load_approved_release(self.output, now=NOW)
        self.assertEqual(loaded, result)
        self.assertEqual(loaded["snapshot"]["market"]["sample_size"], 101)
        self.assertEqual(loaded["snapshot"]["quality"]["evidence_record_count"], 100)
        self.assertEqual(loaded["snapshot"]["market"]["top_skills"][0]["job_count"], 100)
        self.assertEqual(len(loaded["snapshot"]["postings"]), 101)
        self.assertEqual(loaded["snapshot"]["evaluation"]["precision_pct"], 100)
        self.assertEqual(set(self.output.iterdir()), {self.output / "manifest.json", self.output / "snapshot.json"})

    def test_preparation_strips_private_arbitrary_fields(self):
        jobs, evidence, evaluation = copy.deepcopy((self.jobs, self.evidence, self.evaluation))
        jobs[0]["candidate_email"] = "DO_NOT_EXPORT_PRIVATE"
        evidence[0]["private_notes"] = "DO_NOT_EXPORT_PRIVATE"
        evaluation["review_notes"] = "DO_NOT_EXPORT_PRIVATE"
        self.prepare(jobs=jobs, evidence=evidence, evaluation=evaluation)
        self.assertNotIn("DO_NOT_EXPORT_PRIVATE", (self.output / "snapshot.json").read_text())

    def test_unreviewed_bare_flag_and_reused_review_fail_closed(self):
        for evaluation in [None, {"publication_threshold_met": True}, {**self.evaluation, "reviewed_count": 99},
                           {**self.evaluation, "dataset_fingerprint": "0" * 64}]:
            with self.subTest(evaluation=evaluation), self.assertRaises(ValueError):
                self.prepare(evaluation=evaluation)
        changed = copy.deepcopy(self.jobs)
        changed[0]["description_text"] += " Changed context."
        with self.assertRaises(ValueError):
            self.prepare(jobs=changed)

    def test_duplicate_review_fingerprints_and_missing_category_coverage_fail(self):
        evaluation = copy.deepcopy(self.evaluation)
        evaluation["reviewed_record_fingerprints"][-1] = evaluation["reviewed_record_fingerprints"][0]
        with self.assertRaises(ValueError): self.prepare(evaluation=evaluation)
        evaluation = copy.deepcopy(self.evaluation)
        evaluation["unreviewed_population_categories"] = ["Data"]
        with self.assertRaises(ValueError): self.prepare(evaluation=evaluation)
        evaluation = copy.deepcopy(self.evaluation)
        evaluation["extraction_versions"] = []
        with self.assertRaises(ValueError): self.prepare(evaluation=evaluation)

    def test_explicit_permissions_inventory_and_owner_approval_are_required(self):
        for field in ["owner_approved", "collection_authorized", "public_display_authorized"]:
            policy = copy.deepcopy(self.policy)
            (policy if field == "owner_approved" else policy["sources"][0])[field] = False
            with self.subTest(field=field), self.assertRaises(ValueError): self.prepare(policy=policy)
        policy = copy.deepcopy(self.policy)
        policy["sources"][0]["source_name"] = "Different source"
        with self.assertRaises(ValueError): self.prepare(policy=policy)
        policy = copy.deepcopy(self.policy)
        policy["sources"].append(copy.deepcopy(policy["sources"][0]))
        with self.assertRaises(ValueError): self.prepare(policy=policy)

    def test_collection_terms_expiry_and_timezones_are_checked_on_each_load(self):
        for field, value in [("published_at", "2026-10-27T11:00:00+00:00"),
                             ("collected_from", "2026-10-26T10:00:00"),
                             ("expires_at", "2026-10-25T11:00:00+00:00"),
                             ("expires_at", "2027-10-26T11:00:00+00:00")]:
            policy = copy.deepcopy(self.policy); policy[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError): self.prepare(policy=policy)
        policy = copy.deepcopy(self.policy); policy["sources"][0]["terms_reviewed_on"] = "2026-10-27"
        with self.assertRaises(ValueError): self.prepare(policy=policy)
        self.prepare()
        with self.assertRaises(ValueError): load_approved_release(self.output, now=NOW + timedelta(days=8))

    def test_source_urls_reject_credentials_script_and_secret_parameters(self):
        for url in ["javascript:alert(1)", "https://user:password@example.test/", "https://example.test/?app_key=secret", "file:///tmp/private", "https://127.0.0.1/jobs", "https://localhost/jobs", "https://example.test/#access_token=secret"]:
            policy = copy.deepcopy(self.policy); policy["sources"][0]["terms_url"] = url
            with self.subTest(url=url), self.assertRaises(ValueError): self.prepare(policy=policy)
        jobs = copy.deepcopy(self.jobs); jobs[0]["canonical_url"] = "https://example.test/?access_token=secret"
        with self.assertRaises(ValueError): self.prepare(jobs=jobs)

    def test_irish_scope_unique_identities_and_explicit_roles_are_required(self):
        for changes in [{"location_text": "Belfast, Northern Ireland"}, {"role_name": ""},
                        {"source_job_id": self.jobs[1]["source_job_id"]}, {"canonical_url": self.jobs[1]["canonical_url"]},
                        {"posted_at": "2026-10-27"}]:
            jobs = copy.deepcopy(self.jobs); jobs[0].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError): self.prepare(jobs=jobs)

    def test_evidence_requires_exact_source_taxonomy_and_identity(self):
        for changes in [{"source_phrase": "SQL injected"}, {"category": "Forged category"},
                        {"skill_name": "Invented name"}, {"extraction_version": "old-v1"}]:
            evidence = copy.deepcopy(self.evidence); evidence[0].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError): self.prepare(evidence=evidence)
        with self.assertRaises(ValueError): self.prepare(evidence=self.evidence + [self.evidence[0]])

    def test_modified_bytes_and_modified_metrics_fail_even_with_rehashed_manifest(self):
        self.prepare()
        self.change_snapshot(lambda value: value["market"].update(sample_size=999))
        with self.assertRaisesRegex(ValueError, "checksum"): load_approved_release(self.output, now=NOW)
        self.change_snapshot(lambda value: None, update_hash=True)
        with self.assertRaisesRegex(ValueError, "metrics"): load_approved_release(self.output, now=NOW)

    def test_private_fields_in_published_snapshot_and_manifest_are_rejected(self):
        self.prepare()
        self.change_snapshot(lambda value: value["postings"][0].update(candidate_email="private"), update_hash=True)
        with self.assertRaises(ValueError): load_approved_release(self.output, now=NOW)
        manifest = json.loads((self.output / "manifest.json").read_text())
        manifest["arbitrary_private_metadata"] = "private"
        (self.output / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaises(ValueError): load_approved_release(self.output, now=NOW)

    def test_existing_releases_symlinks_extra_files_and_oversized_artifacts_rejected(self):
        self.prepare()
        with self.assertRaises(ValueError): self.prepare()
        linked = Path(self.directory.name) / "linked"
        linked.symlink_to(self.output, target_is_directory=True)
        with self.assertRaises(ValueError): load_approved_release(linked, now=NOW)
        (self.output / "private.json").write_text("{}")
        with self.assertRaises(ValueError): load_approved_release(self.output, now=NOW)
        (self.output / "private.json").unlink()
        with (self.output / "snapshot.json").open("wb") as file: file.truncate(MAX_BYTES + 1)
        with self.assertRaises(ValueError): load_approved_release(self.output, now=NOW)

    def test_cli_prepare_and_verify_report_no_publication(self):
        base = Path(self.directory.name)
        for name, rows in [("jobs", self.jobs), ("evidence", self.evidence)]:
            with (base / f"{name}.csv").open("w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=list(rows[0]))
                writer.writeheader(); writer.writerows(rows)
        (base / "evaluation.json").write_text(json.dumps(self.evaluation))
        (base / "policy.json").write_text(json.dumps(self.policy))
        commands = [["release", "prepare", "--jobs", str(base / "jobs.csv"), "--evidence", str(base / "evidence.csv"),
                     "--evaluation", str(base / "evaluation.json"), "--policy", str(base / "policy.json"), "--output", str(self.output)],
                    ["release", "verify", "--bundle", str(self.output)]]
        for command in commands:
            output = io.StringIO()
            with patch("sys.argv", command), patch("career_radar.approved_release._now", return_value=NOW), contextlib.redirect_stdout(output):
                main()
            result = json.loads(output.getvalue())
            self.assertEqual(result, {"release_id": self.policy["release_id"], "sample_size": 101, "verified": True, "published": False})

    def test_cli_csv_reader_stops_at_row_limit_and_rejects_bad_headers(self):
        path = Path(self.directory.name) / "input.csv"
        path.write_text("a,b\n1,2\n3,4\n")
        with self.assertRaises(ValueError): _read_csv(path, 1)
        path.write_text("a,a\n1,2\n")
        with self.assertRaises(ValueError): _read_csv(path, 2)

    def test_duplicate_json_fields_are_rejected_before_manifest_validation(self):
        self.prepare()
        path = self.output / "manifest.json"
        path.write_text('{"release_id":"first","release_id":"second"}')
        with self.assertRaisesRegex(ValueError, "Duplicate JSON"):
            load_approved_release(self.output, now=NOW)


if __name__ == "__main__":
    unittest.main()
