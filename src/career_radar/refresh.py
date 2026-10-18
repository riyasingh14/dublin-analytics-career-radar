"""Saved-file refresh runner. No network, paid calls, publication or invented reviews.

Run ``python -m career_radar.refresh --help``. A completed run is immutable; only
an atomic pointer is replaced after ingestion, quality and review artefacts succeed.
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
import csv
from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from urllib.parse import urlparse
import uuid
from zoneinfo import ZoneInfo

from career_radar.build_snapshot import build_snapshot_payload
from career_radar.ingest import REQUIRED_COLUMNS, write_csv
from career_radar.normalise import (
    ROLE_CLASSIFICATION_VERSION, TAXONOMY_VERSION, classify_role,
    classify_work_pattern, deduplication_key, extract_skills, geography_group, load_taxonomy,
)
from career_radar.validation import build_quality_profile, build_review_queue

VERSION = "saved-refresh-v1"
MAX_BYTES = 20 * 1024 * 1024
MAX_ROWS = 10_000
DUBLIN = ZoneInfo("Europe/Dublin")


class RefreshRejected(ValueError):
    """A safe reason code, without input text or credentials."""


def _json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _verified_manifest(run_dir: Path) -> dict:
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    names = ("jobs.csv", "evidence.csv", "review_queue.csv", "quality.json", "snapshot.json")
    if manifest.get("run_id") != run_dir.name or manifest.get("publish_allowed") is not False:
        raise RefreshRejected("completed_run_identity_invalid")
    for name in names:
        digest = hashlib.sha256((run_dir / name).read_bytes()).hexdigest()
        if digest != manifest.get("artifact_sha256", {}).get(name):
            raise RefreshRejected("completed_run_artifact_corrupt")
    return manifest


def _recover_pointer(output_dir: Path, candidate: dict) -> None:
    """Recover interrupted promotion, preserving the newest valid collection.

    Completed immutable runs survive a crash before pointer replacement. A retry
    verifies every candidate's hashes and never promotes an older collection over
    a newer valid run. Corrupt runs are retained for investigation, not published.
    """
    valid = [candidate]
    for directory in (output_dir / "runs").iterdir():
        if directory.name == candidate["run_id"] or directory.name.startswith("."):
            continue
        try:
            valid.append(_verified_manifest(directory))
        except (OSError, ValueError, KeyError):
            continue
    winner = max(valid, key=lambda item: (_instant(item["collection_timestamp"]),
                                         item.get("completed_at", ""), item["run_id"]))
    pointer = {"run_id": winner["run_id"], "relative_path": f"runs/{winner['run_id']}/snapshot.json",
               "data_status": winner["data_status"], "publish_allowed": False,
               "collection_timestamp": winner["collection_timestamp"],
               "collection_week_dublin": winner["collection_week_dublin"]}
    pointer_path = output_dir / "latest_good.json"
    if pointer_path.exists():
        try:
            if json.loads(pointer_path.read_text()) == pointer:
                return
        except (ValueError, OSError):
            pass
    handle, temporary = tempfile.mkstemp(prefix=".pointer-", dir=output_dir)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            json.dump(pointer, file, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, pointer_path)
    finally:
        if Path(temporary).exists():
            Path(temporary).unlink()


def _instant(value: str | datetime | None) -> datetime:
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
        moment = moment or datetime.now(timezone.utc)
        if moment.tzinfo is None:
            raise ValueError
        return moment.astimezone(timezone.utc)
    except (ValueError, TypeError, AttributeError) as error:
        raise RefreshRejected("collection_timestamp_requires_timezone") from error


def _policy(raw: object, today: date) -> dict:
    if not isinstance(raw, dict):
        raise RefreshRejected("invalid_policy")
    policy = dict(raw)
    if policy.get("dataset_kind") not in {"fixture", "observed"}:
        raise RefreshRejected("dataset_kind_required")
    if policy.get("collection_authorized") is not True:
        raise RefreshRejected("collection_permission_required")
    if not isinstance(policy.get("source_name"), str) or not policy["source_name"].strip():
        raise RefreshRejected("source_name_required")
    # There is deliberately no live connector in this process, even with a budget.
    if policy.get("live_collection_enabled", False) is not False:
        raise RefreshRejected("live_collection_disabled")
    for key in ("max_live_requests", "max_spend_usd"):
        if policy.get(key, 0) != 0 or isinstance(policy.get(key), bool):
            raise RefreshRejected("saved_file_budget_must_be_zero")
    if policy["dataset_kind"] == "observed":
        try:
            reviewed = date.fromisoformat(policy.get("terms_reviewed_on", ""))
        except (ValueError, TypeError) as error:
            raise RefreshRejected("terms_review_date_required") from error
        if reviewed > today:
            raise RefreshRejected("terms_review_date_in_future")
        source_url = urlparse(policy.get("source_home_url", ""))
        if source_url.scheme != "https" or not source_url.netloc or source_url.username or source_url.password:
            raise RefreshRejected("https_source_home_required")
    limits = {"min_job_count": (1, 1, MAX_ROWS), "max_missing_description_pct": (0, 0, 100),
              "max_employer_share_pct": (100, 0, 100)}
    for key, (default, low, high) in limits.items():
        value = policy.get(key, default)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= value <= high:
            raise RefreshRejected("invalid_quality_policy")
        policy[key] = value
    return policy


def read_saved_rows(path: Path) -> tuple[bytes, list[dict[str, str]]]:
    if path.stat().st_size > MAX_BYTES:
        raise RefreshRejected("input_too_large")
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
        if path.suffix.lower() == ".json":
            rows = json.loads(text)
            if not isinstance(rows, list):
                raise RefreshRejected("json_must_be_normalized_posting_array")
        elif path.suffix.lower() == ".csv":
            reader = csv.DictReader(text.splitlines(keepends=True))
            if REQUIRED_COLUMNS.difference(reader.fieldnames or []):
                raise RefreshRejected("required_columns_missing")
            rows = list(reader)
        else:
            raise RefreshRejected("only_csv_or_json_saved_files")
    except (UnicodeError, json.JSONDecodeError, csv.Error) as error:
        raise RefreshRejected("invalid_saved_file") from error
    if not rows or len(rows) > MAX_ROWS:
        raise RefreshRejected("invalid_row_count")
    output = []
    for row in rows:
        if not isinstance(row, dict) or REQUIRED_COLUMNS.difference(row):
            raise RefreshRejected("required_columns_missing")
        clean = {}
        for key in REQUIRED_COLUMNS | {"posted_at"}:
            value = row.get(key, "")
            if value is None:
                value = ""
            if not isinstance(value, str) or len(value) > 100_000:
                raise RefreshRejected("invalid_posting_field")
            clean[key] = value.strip()
        if any(not clean[key] for key in ("source_job_id", "canonical_url", "title", "location_text")):
            raise RefreshRejected("posting_identity_missing")
        parsed = urlparse(clean["canonical_url"])
        if parsed.scheme not in {"https", "fixture"} or not parsed.netloc:
            raise RefreshRejected("posting_url_invalid")
        output.append(clean)
    return raw, output


def normalize_rows(rows: list[dict[str, str]], source_name: str, collected_at: str, taxonomy: list) -> tuple[list, list]:
    jobs, evidence = [], []
    seen_keys, seen_urls, identities = set(), set(), {}
    for row in rows:
        key = deduplication_key(row["title"], row["employer_name"], row["location_text"], row["description_text"])
        identity = row["source_job_id"]
        if identity in identities and identities[identity] != row["canonical_url"]:
            raise RefreshRejected("source_job_id_conflict")
        identities[identity] = row["canonical_url"]
        if key in seen_keys or row["canonical_url"] in seen_urls:
            continue
        seen_keys.add(key)
        seen_urls.add(row["canonical_url"])
        role_name, confidence = classify_role(row["title"])
        jobs.append({**row, "source_name": source_name,
                     "role_name": role_name or "Unclassified", "role_confidence": confidence,
                     "role_classification_version": ROLE_CLASSIFICATION_VERSION,
                     "work_pattern": classify_work_pattern(row["location_text"] + " " + row["description_text"]),
                     "collection_timestamp": collected_at, "deduplication_key": key})
        evidence.extend({**item, "source_job_id": identity, "canonical_url": row["canonical_url"],
                         "collection_timestamp": collected_at}
                        for item in extract_skills(row["description_text"], taxonomy))
    return jobs, evidence


@contextmanager
def _locked(root: Path):
    lock = root / ".refresh.lock"
    try:
        lock.mkdir()
    except FileExistsError as error:
        raise RefreshRejected("refresh_locked") from error
    try:
        yield
    finally:
        lock.rmdir()


def refresh(input_path: Path, policy_path: Path, output_dir: Path, taxonomy_path: Path,
            collected_at: str | datetime | None = None) -> dict:
    """Create private, unreviewed artefacts and advance last-good only on success.

    Observed sources require their actual collection timestamp. Identical same-week
    input is a no-op; a different observed export in the same source/week is blocked.
    A source policy is the owner's attestation, not an independent permission check.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    with _locked(output_dir):
        try:
            policy = _policy(json.loads(policy_path.read_text(encoding="utf-8")), datetime.now(DUBLIN).date())
            if policy["dataset_kind"] == "observed" and collected_at is None:
                raise RefreshRejected("observed_collection_timestamp_required")
            moment = _instant(collected_at)
            if moment > datetime.now(timezone.utc):
                raise RefreshRejected("collection_timestamp_in_future")
            stamp = moment.isoformat()
            week = moment.astimezone(DUBLIN).strftime("%G-W%V")
            raw, rows = read_saved_rows(input_path)
            taxonomy = load_taxonomy(taxonomy_path)
            input_hash = hashlib.sha256(raw).hexdigest()
            taxonomy_hash = hashlib.sha256(taxonomy_path.read_bytes()).hexdigest()
            fingerprint = {"input_sha256": input_hash, "taxonomy_sha256": taxonomy_hash,
                           "policy": policy, "collection_week_dublin": week, "pipeline_version": VERSION}
            run_id = hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest()[:24]
            run_dir = output_dir / "runs" / run_id
            if (run_dir / "manifest.json").exists():
                previous = _verified_manifest(run_dir)
                _recover_pointer(output_dir, previous)
                return {**previous, "outcome": "already_processed"}
            if policy["dataset_kind"] == "observed":
                for manifest_path in (output_dir / "runs").glob("*/manifest.json"):
                    previous = json.loads(manifest_path.read_text())
                    if previous["source_name"] == policy["source_name"] and previous["collection_week_dublin"] == week:
                        raise RefreshRejected("observed_source_week_already_processed")
            jobs, evidence = normalize_rows(rows, policy["source_name"], stamp, taxonomy)
            quality = build_quality_profile(jobs, evidence, len(rows))
            quality["geography_counts"] = dict(Counter(geography_group(job["location_text"]) for job in jobs))
            if len(jobs) < policy["min_job_count"]:
                raise RefreshRejected("quality_min_job_count")
            if quality["missingness"]["description_text"]["missing_pct"] > policy["max_missing_description_pct"]:
                raise RefreshRejected("quality_missing_description")
            if quality["top_employer_share_pct"] > policy["max_employer_share_pct"]:
                raise RefreshRejected("quality_employer_concentration")
            status = "fixture" if policy["dataset_kind"] == "fixture" else "unreviewed"
            manifest = {**{key: value for key, value in fingerprint.items() if key != "policy"},
                        "run_id": run_id, "source_name": policy["source_name"], "data_status": status,
                        "collection_timestamp": stamp, "source_row_count": len(rows),
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "unique_job_count": len(jobs), "duplicates_removed": len(rows) - len(jobs),
                        "skill_evidence_count": len(evidence), "publish_allowed": False,
                        "live_requests": 0, "spend_usd": 0, "human_review_status": "not_completed",
                        "terms_reviewed_on": policy.get("terms_reviewed_on"),
                        "display_authorized_attestation": policy.get("display_authorized") is True,
                        "extraction_version": TAXONOMY_VERSION,
                        "role_classification_version": ROLE_CLASSIFICATION_VERSION}
            snapshot = build_snapshot_payload(jobs, evidence, policy["source_name"], status, len(rows),
                provenance={"collection_timestamp": stamp, "export_sha256": input_hash,
                            "geographic_scope": "Source-declared locations; unknown/outside-scope records retained and labelled"})
            # Never use fixture mode or an owner attestation to bypass human review.
            snapshot["metadata"]["publish_allowed"] = False
            snapshot["metadata"]["refresh_run_id"] = run_id
            (output_dir / "runs").mkdir(exist_ok=True)
            stage = Path(tempfile.mkdtemp(prefix=".staging-", dir=output_dir / "runs"))
            try:
                write_csv(stage / "jobs.csv", jobs, list(jobs[0]))
                write_csv(stage / "evidence.csv", evidence, list(evidence[0]) if evidence else ["canonical_url", "skill_id"])
                queue = build_review_queue(jobs, evidence)
                write_csv(stage / "review_queue.csv", queue, list(queue[0]) if queue else ["reviewer_label"])
                _json(stage / "quality.json", quality)
                _json(stage / "snapshot.json", snapshot)
                manifest["artifact_sha256"] = {
                    name: hashlib.sha256((stage / name).read_bytes()).hexdigest()
                    for name in ("jobs.csv", "evidence.csv", "review_queue.csv", "quality.json", "snapshot.json")
                }
                _json(stage / "manifest.json", manifest)
                os.replace(stage, run_dir)
            finally:
                if stage.exists():
                    shutil.rmtree(stage)
            _recover_pointer(output_dir, manifest)
            return {**manifest, "outcome": "completed"}
        except Exception as error:
            failures = output_dir / "failures"
            failures.mkdir(exist_ok=True)
            _json(failures / f"{uuid.uuid4().hex}.json", {
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "reason": str(error) if isinstance(error, RefreshRejected) else "invalid_input_or_internal_failure",
                "live_requests": 0, "spend_usd": 0, "last_good_retained": True,
            })
            raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed/refresh"))
    parser.add_argument("--taxonomy", type=Path, default=Path("data/reference/skills.csv"))
    parser.add_argument("--collected-at", help="Actual source collection timestamp with timezone")
    args = parser.parse_args()
    try:
        result = refresh(args.input, args.policy, args.output_dir, args.taxonomy, args.collected_at)
    except (RefreshRejected, OSError, ValueError) as error:
        parser.exit(1, f"Refresh rejected: {error if isinstance(error, RefreshRejected) else 'invalid input or local filesystem'}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
