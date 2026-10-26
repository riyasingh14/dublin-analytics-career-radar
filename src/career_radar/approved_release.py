"""Prepare and verify explicitly approved, immutable public-data bundles.

No collection, automatic approval, environment lookup or publication occurs here.
Hashes detect changed artefacts; permission attestations and human labels remain
operator-supplied evidence, not cryptographic proof of a person's authority.
"""
from __future__ import annotations

import argparse
import csv
from datetime import UTC, date, datetime, timedelta
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import parse_qsl, urlsplit

from career_radar.analytics import build_market_summary
from career_radar.normalise import (ROLE_RULES, deduplication_key,
                                    extract_skills, geography_group, load_taxonomy)
from career_radar.validation import (build_quality_profile, build_review_queue,
                                     review_dataset_fingerprint, review_matches_dataset,
                                     review_record_fingerprint, _wilson_interval)

SCHEMA = "approved-public-release-v1"
MAX_BYTES = 20 * 1024 * 1024
MAX_JOBS = 10000
MAX_EVIDENCE = 100000
JOB_FIELDS = ("source_job_id", "canonical_url", "title", "employer_name", "location_text",
              "description_text", "posted_at", "source_name", "role_name", "work_pattern")
EVIDENCE_FIELDS = ("canonical_url", "skill_id", "skill_name", "category", "source_phrase",
                   "extraction_method", "extraction_version")
POLICY_FIELDS = {"schema_version", "release_id", "dataset_label", "published_at", "collected_from",
                 "collected_through", "expires_at", "geographic_scope", "owner_approved", "sources"}
MANIFEST_FIELDS = POLICY_FIELDS | {"snapshot_sha256", "dataset_fingerprint"}
SOURCE_FIELDS = {"source_name", "homepage_url", "terms_url", "terms_reviewed_on", "collected_from",
                 "collected_through", "collection_authorized", "public_display_authorized", "permission_basis"}
EVALUATION_FIELDS = {"evaluation_version", "dataset_fingerprint", "review_lineage_valid",
                     "publication_threshold_met", "gate_reasons", "reviewed_count", "accepted_count",
                     "extraction_versions", "reviewed_record_fingerprints", "unreviewed_population_categories"}
ROOT = Path(__file__).resolve().parents[2]


def _object(value, fields, name):
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{name} must contain exactly the documented fields")
    return value


def _text(value, name, maximum=1000, *, empty=False):
    if not isinstance(value, str) or len(value) > maximum or (not empty and not value.strip()) or "\x00" in value:
        raise ValueError(f"Invalid {name}")
    return value


def _instant(value, name):
    _text(value, name, 50)
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"Invalid {name} timestamp") from error
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError(f"{name} requires a timezone")
    return result.astimezone(UTC)


def _url(value):
    _text(value, "public source URL", 2000)
    try:
        parsed = urlsplit(value)
        invalid = parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
        secret_parameters = {"app_key", "app_id", "api_key", "apikey", "access_token", "authorization", "token", "auth", "secret", "signature", "x-amz-signature", "x-amz-credential"}
        parameters = [*parse_qsl(parsed.query), *parse_qsl(parsed.fragment)]
        invalid = invalid or bool({key.lower() for key, _ in parameters} & secret_parameters)
        host = (parsed.hostname or "").lower()
        invalid = invalid or host == "localhost" or host.endswith((".localhost", ".local"))
        try:
            invalid = invalid or not ipaddress.ip_address(host).is_global
        except ValueError:
            invalid = invalid or "." not in host
        invalid = invalid or any(ord(character) < 33 for character in value)
        if invalid:
            raise ValueError("unsafe")
        parsed.port
    except ValueError as error:
        raise ValueError("A public source URL must be HTTPS without credentials") from error
    return value


def _now(now):
    value = now or datetime.now(UTC)
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("now must be a timezone-aware datetime")
    return value.astimezone(UTC)


def _policy(policy, now):
    _object(policy, POLICY_FIELDS, "Release policy")
    if policy["schema_version"] != SCHEMA or policy["geographic_scope"] != "Ireland":
        raise ValueError("Unsupported release schema or geography")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,62}", _text(policy["release_id"], "release ID", 63)):
        raise ValueError("Release ID must be a bounded lowercase slug")
    _text(policy["dataset_label"], "dataset label", 160)
    if policy["owner_approved"] is not True:
        raise ValueError("Explicit owner approval is required")
    published = _instant(policy["published_at"], "published_at")
    start = _instant(policy["collected_from"], "collected_from")
    end = _instant(policy["collected_through"], "collected_through")
    expires = _instant(policy["expires_at"], "expires_at")
    if not start <= end <= published <= now < expires or expires > published + timedelta(days=31):
        raise ValueError("Release timestamps are future, expired or inconsistent")
    sources = policy["sources"]
    if not isinstance(sources, list) or not 1 <= len(sources) <= 100:
        raise ValueError("A bounded, nonempty source inventory is required")
    names, starts, ends = set(), [], []
    for source in sources:
        _object(source, SOURCE_FIELDS, "Source permission")
        name = _text(source["source_name"], "source name", 120)
        if name in names:
            raise ValueError("Duplicate source names")
        names.add(name)
        _url(source["homepage_url"]); _url(source["terms_url"])
        _text(source["permission_basis"], "permission basis", 1200)
        if source["collection_authorized"] is not True or source["public_display_authorized"] is not True:
            raise ValueError("Collection and public-display authorization are required for every source")
        begin = _instant(source["collected_from"], "source collected_from")
        finish = _instant(source["collected_through"], "source collected_through")
        try:
            reviewed = date.fromisoformat(source["terms_reviewed_on"])
        except (TypeError, ValueError) as error:
            raise ValueError("A real terms-review date is required") from error
        if not start <= begin <= finish <= end or reviewed > begin.date():
            raise ValueError("Source collection and terms-review dates are inconsistent")
        starts.append(begin); ends.append(finish)
    if min(starts) != start or max(ends) != end:
        raise ValueError("The release collection window must equal its source coverage")
    return policy


def _canonical_rows(jobs, evidence, policy):
    if not isinstance(jobs, list) or not 1 <= len(jobs) <= MAX_JOBS:
        raise ValueError("Release jobs must be a bounded nonempty list")
    if not isinstance(evidence, list) or not 1 <= len(evidence) <= MAX_EVIDENCE:
        raise ValueError("Release evidence must be a bounded nonempty list")
    canonical_jobs, identities, urls, dedup_keys = [], set(), set(), set()
    sources = {source["source_name"]: source for source in policy["sources"]}
    for row in jobs:
        if not isinstance(row, dict):
            raise ValueError("Invalid posting record")
        job = {key: _text(row.get(key, ""), key, 30000 if key == "description_text" else 2000,
                          empty=key == "posted_at") for key in JOB_FIELDS}
        _url(job["canonical_url"])
        if job["source_name"] not in sources:
            raise ValueError("A posting has no documented source permission")
        identity = (job["source_name"], job["source_job_id"])
        dedup_key = deduplication_key(job["title"], job["employer_name"], job["location_text"], job["description_text"])
        if identity in identities or job["canonical_url"] in urls or dedup_key in dedup_keys:
            raise ValueError("Release must contain unique posting identities and deduplicated content")
        identities.add(identity); urls.add(job["canonical_url"]); dedup_keys.add(dedup_key)
        geography = geography_group(job["location_text"])
        if geography == "Outside scope / unknown":
            raise ValueError("Every released posting must explicitly be in Ireland")
        if job["role_name"] not in {*ROLE_RULES, "Unclassified"} or job["work_pattern"] not in {"unknown", "remote", "hybrid", "onsite"}:
            raise ValueError("Invalid role or work-pattern classification")
        if job["posted_at"]:
            value = job["posted_at"]
            try:
                posted = datetime.combine(date.fromisoformat(value), datetime.min.time(), UTC) if len(value) == 10 else _instant(value, "posted_at")
            except ValueError as error:
                raise ValueError("Invalid posting date") from error
            if posted > _instant(sources[job["source_name"]]["collected_through"], "source collected_through"):
                raise ValueError("Posting dates cannot follow their source collection")
        job["geography"] = geography
        canonical_jobs.append(job)
    if {job["source_name"] for job in canonical_jobs} != set(sources):
        raise ValueError("Source inventory must exactly cover the released postings")
    taxonomy = load_taxonomy(ROOT / "data/reference/skills.csv")
    by_url = {job["canonical_url"]: job for job in canonical_jobs}
    extracted = {url: {item["skill_id"]: item for item in extract_skills(job["description_text"], taxonomy)}
                 for url, job in by_url.items()}
    canonical_evidence, seen = [], set()
    for row in evidence:
        if not isinstance(row, dict):
            raise ValueError("Invalid evidence record")
        item = {key: _text(row.get(key, ""), key, 2000 if key in {"canonical_url", "source_phrase"} else 160)
                for key in EVIDENCE_FIELDS}
        expected = extracted.get(item["canonical_url"], {}).get(item["skill_id"])
        identity = (item["canonical_url"], item["skill_id"], item["extraction_version"])
        if identity in seen:
            raise ValueError("Duplicate evidence identity")
        seen.add(identity)
        if expected is None or any(item[key] != expected[key] for key in EVIDENCE_FIELDS if key != "canonical_url"):
            raise ValueError("Evidence must match the current controlled extractor and exact source phrase")
        canonical_evidence.append(item)
    return sorted(canonical_jobs, key=lambda job: job["canonical_url"]), sorted(canonical_evidence, key=lambda item: (item["canonical_url"], item["skill_id"]))


def _evaluation(value, jobs, evidence):
    if not isinstance(value, dict):
        raise ValueError("A dataset-bound human evaluation is required")
    result = {key: value.get(key) for key in EVALUATION_FIELDS}
    if not review_matches_dataset(result, jobs, evidence):
        raise ValueError("The applicable 100-record/90%-precision review gate has not passed")
    if result["unreviewed_population_categories"] != []:
        raise ValueError("Every evidence category requires completed review coverage")
    expected_versions = sorted({row["extraction_version"] for row in evidence})
    if result["extraction_versions"] != expected_versions:
        raise ValueError("Every extraction version requires completed review coverage")
    population = build_review_queue(jobs, evidence, sample_size=len(evidence), seed=0)
    reviewed = set(result["reviewed_record_fingerprints"])
    categories = {row["category"] for row in population if review_record_fingerprint(row) in reviewed}
    if categories != {row["category"] for row in evidence}:
        raise ValueError("Review fingerprints do not cover the released skill categories")
    count, accepted = result["reviewed_count"], result["accepted_count"]
    result["precision_pct"] = round(100 * accepted / count, 1)
    result["precision_95_ci_pct"] = list(_wilson_interval(accepted, count))
    result["target"] = {"minimum_reviews": 100, "minimum_precision_pct": 90.0}
    return result


def _snapshot(jobs, evidence, evaluation, policy):
    jobs, evidence = _canonical_rows(jobs, evidence, policy)
    evaluation = _evaluation(evaluation, jobs, evidence)
    quality = build_quality_profile(jobs, evidence)
    quality["generated_at"] = policy["published_at"]
    source_counts = quality["source_counts"]
    return {"schema_version": 2,
            "metadata": {"dataset_label": policy["dataset_label"], "data_status": "validated",
                         "data_kind": "observed", "generated_at": policy["published_at"],
                         "publish_allowed": True, "disclosure": "Reviewed observed sample; source coverage and collection dates limit generalisation."},
            "market": build_market_summary(jobs, evidence), "quality": quality,
            "geography_markets": {group: build_market_summary([job for job in jobs if job["geography"] == group], evidence)
                                  for group in sorted({job["geography"] for job in jobs})},
            "evaluation": evaluation, "postings": jobs, "evidence": evidence,
            "provenance": {"geographic_scope": "Ireland", "collection_timestamp": policy["collected_through"],
                           "collection_from": policy["collected_from"], "source_counts": source_counts,
                           "extraction_versions": sorted({item["extraction_version"] for item in evidence})}}


def _bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def _read_json(path, maximum=MAX_BYTES):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > maximum:
        raise ValueError("Missing, oversized or symlinked release artefact")
    raw = path.read_bytes()
    if len(raw) > maximum:
        raise ValueError("Oversized release artefact")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON field")
            result[key] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=unique, parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Nonfinite JSON"))), raw
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError("Invalid release JSON") from error


def _directory(path):
    path = Path(path)
    if any(part.is_symlink() for part in [path, *path.parents]):
        raise ValueError("Symlinked release directories are not supported")
    if not path.is_dir():
        raise ValueError("Release directory does not exist")
    return path


def load_approved_release(bundle_dir: Path, *, now: datetime | None = None) -> dict:
    """Load a fixed-name bundle, rechecking review, permissions, dates and metrics.

    Caller must constrain the operator-selected path to its approved deployment
    directory. This function deliberately does not read any environment variable.
    """
    directory = _directory(bundle_dir)
    if {path.name for path in directory.iterdir()} != {"manifest.json", "snapshot.json"}:
        raise ValueError("A release contains only manifest.json and snapshot.json")
    manifest, _ = _read_json(directory / "manifest.json", 512 * 1024)
    _object(manifest, MANIFEST_FIELDS, "Release manifest")
    policy = _policy({key: manifest[key] for key in POLICY_FIELDS}, _now(now))
    snapshot, raw = _read_json(directory / "snapshot.json")
    if manifest["snapshot_sha256"] != hashlib.sha256(raw).hexdigest():
        raise ValueError("Snapshot checksum does not match the release manifest")
    if not isinstance(snapshot, dict):
        raise ValueError("Invalid release snapshot")
    canonical = _snapshot(snapshot.get("postings"), snapshot.get("evidence"), snapshot.get("evaluation"), policy)
    if snapshot != canonical or manifest["dataset_fingerprint"] != review_dataset_fingerprint(canonical["postings"], canonical["evidence"]):
        raise ValueError("Release content, metrics or dataset lineage are inconsistent")
    return {"snapshot": canonical, "release": manifest}


def prepare_approved_release(jobs: list[dict], evidence: list[dict], evaluation: dict,
                             policy: dict, output_dir: Path, *, now: datetime | None = None) -> dict:
    """Write a new immutable bundle after all explicitly supplied gates pass."""
    policy = _policy(policy, _now(now))
    snapshot = _snapshot(jobs, evidence, evaluation, policy)
    raw = _bytes(snapshot)
    if len(raw) > MAX_BYTES:
        raise ValueError("Approved snapshot exceeds the public release size limit")
    manifest = {**policy, "snapshot_sha256": hashlib.sha256(raw).hexdigest(),
                "dataset_fingerprint": review_dataset_fingerprint(snapshot["postings"], snapshot["evidence"])}
    output = Path(output_dir)
    if output.exists() or output.is_symlink():
        raise ValueError("Release output already exists; releases cannot be overwritten")
    output.parent.mkdir(parents=True, exist_ok=True)
    if any(part.is_symlink() for part in [output.parent, *output.parent.parents]):
        raise ValueError("Symlinked release parents are not supported")
    temporary = Path(tempfile.mkdtemp(prefix=".release-", dir=output.parent))
    try:
        (temporary / "snapshot.json").write_bytes(raw)
        (temporary / "manifest.json").write_bytes(_bytes(manifest))
        load_approved_release(temporary, now=now)
        # Refuse a concurrent writer instead of replacing an existing directory.
        if output.exists():
            raise ValueError("Release output already exists")
        os.rename(temporary, output)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return load_approved_release(output, now=now)


def _read_csv(path, maximum_rows):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError("Missing, oversized or symlinked source input")
    rows = []
    try:
        with path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
                raise ValueError("Source CSV needs unique column names")
            for row in reader:
                if len(rows) >= maximum_rows or None in row:
                    raise ValueError("Source CSV exceeds row limits or has malformed columns")
                rows.append(row)
    except (UnicodeDecodeError, csv.Error) as error:
        raise ValueError("Invalid source CSV") from error
    return rows


def main():
    parser = argparse.ArgumentParser(description="Prepare or verify an explicitly approved public-data release")
    sub = parser.add_subparsers(dest="action", required=True)
    prepare = sub.add_parser("prepare")
    for name in ("jobs", "evidence", "evaluation", "policy", "output"):
        prepare.add_argument("--" + name, type=Path, required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--bundle", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.action == "prepare":
            evaluation, _ = _read_json(args.evaluation)
            policy, _ = _read_json(args.policy, 512 * 1024)
            result = prepare_approved_release(_read_csv(args.jobs, MAX_JOBS), _read_csv(args.evidence, MAX_EVIDENCE), evaluation, policy, args.output)
        else:
            result = load_approved_release(args.bundle)
        print(json.dumps({"release_id": result["release"]["release_id"], "sample_size": result["snapshot"]["market"]["sample_size"],
                          "verified": True, "published": False}))
    except (ValueError, OSError) as error:
        parser.exit(2, f"Release rejected: {error}\n")


if __name__ == "__main__":
    main()
