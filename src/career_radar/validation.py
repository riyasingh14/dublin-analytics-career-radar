"""Quality profiling and human evaluation for extracted job skills."""

from __future__ import annotations

import argparse
import csv
import json
import hashlib
import math
import random
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

from career_radar.analytics import read_csv


PROFILE_FIELDS = (
    "source_job_id",
    "canonical_url",
    "title",
    "employer_name",
    "location_text",
    "description_text",
    "posted_at",
)
ACCEPTED_LABELS = {"accepted", "correct", "true", "yes", "1"}
REJECTED_LABELS = {"rejected", "incorrect", "false", "no", "0"}
EVALUATION_VERSION = "extraction-evaluation-v2"


def review_dataset_fingerprint(jobs: list[dict], evidence: list[dict]) -> str:
    """Bind review applicability to exact posting/evidence inputs, independent of order.

    This detects accidental reuse, not forged human labels or file tampering by
    an owner. Candidate data and arbitrary imported profile fields are excluded.
    """
    job_fields = (*PROFILE_FIELDS, "source_name", "role_name", "work_pattern")
    evidence_fields = ("canonical_url", "skill_id", "skill_name", "category",
                       "source_phrase", "extraction_method", "extraction_version")
    def records(rows, fields):
        return sorted((tuple(str(row.get(key) or "") for key in fields) for row in rows))
    payload = {"jobs": records(jobs, job_fields), "evidence": records(evidence, evidence_fields)}
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def _percentage(numerator: int, denominator: int) -> float:
    return round(100 * numerator / denominator, 1) if denominator else 0.0


def build_quality_profile(
    jobs: list[dict[str, str]],
    evidence: list[dict[str, str]],
    source_row_count: int | None = None,
) -> dict[str, object]:
    """Profile coverage and quality risks without making market-wide claims."""
    total_jobs = len(jobs)
    urls = {row.get("canonical_url", "") for row in jobs}
    evidence_urls = {row.get("canonical_url", "") for row in evidence} & urls
    role_counts = Counter(row.get("role_name", "Unclassified") or "Unclassified" for row in jobs)
    source_counts = Counter(row.get("source_name", "Unknown") or "Unknown" for row in jobs)
    employer_counts = Counter(
        row.get("employer_name", "Unknown") or "Unknown" for row in jobs
    )

    missingness = {
        field: {
            "missing_count": sum(not (row.get(field) or "").strip() for row in jobs),
            "missing_pct": _percentage(
                sum(not (row.get(field) or "").strip() for row in jobs), total_jobs
            ),
        }
        for field in PROFILE_FIELDS
    }
    classified_jobs = total_jobs - role_counts.get("Unclassified", 0)
    unique_employers = len(employer_counts)
    top_employer, top_employer_count = (
        employer_counts.most_common(1)[0] if employer_counts else (None, 0)
    )
    duplicates_removed = (
        max(source_row_count - total_jobs, 0) if source_row_count is not None else None
    )

    return {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "sample_size": total_jobs,
        "source_row_count": source_row_count,
        "duplicates_removed": duplicates_removed,
        "duplicate_rate_pct": (
            _percentage(duplicates_removed, source_row_count)
            if duplicates_removed is not None and source_row_count is not None
            else None
        ),
        "classified_role_pct": _percentage(classified_jobs, total_jobs),
        "jobs_with_skill_evidence_pct": _percentage(len(evidence_urls), total_jobs),
        "evidence_record_count": len(evidence),
        "unique_skill_count": len({row.get("skill_id", "") for row in evidence}),
        "unique_employer_count": unique_employers,
        "top_employer": top_employer,
        "top_employer_share_pct": _percentage(top_employer_count, total_jobs),
        "role_counts": dict(sorted(role_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "missingness": missingness,
    }


def _context(description: str, phrase: str, width: int = 220) -> str:
    lower_description = description.lower()
    index = lower_description.find(phrase.lower()) if phrase else -1
    if index < 0:
        return " ".join(description.split())[:width]
    start = max(0, index - width // 2)
    end = min(len(description), index + len(phrase) + width // 2)
    return " ".join(description[start:end].split())


def review_record_fingerprint(row: dict) -> str:
    """Hash the immutable evidence actually presented to a reviewer, not their notes."""
    fields = ("canonical_url", "skill_id", "skill_name", "extraction_version", "source_phrase", "category",
              "extraction_method", "context", "job_title", "employer_name")
    values = [str(row.get(key) or "") for key in fields]
    return hashlib.sha256(json.dumps(values, ensure_ascii=False).encode()).hexdigest()


def build_review_queue(
    jobs: list[dict[str, str]],
    evidence: list[dict[str, str]],
    sample_size: int = 100,
    seed: int = 42,
) -> list[dict[str, object]]:
    """Return a reproducible category-balanced extraction review queue."""
    if sample_size < 1:
        raise ValueError("sample_size must be at least 1")
    jobs_by_url = {row.get("canonical_url", ""): row for row in jobs}
    by_category: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in evidence:
        if row.get("canonical_url", "") in jobs_by_url:
            by_category[row.get("category", "Uncategorised") or "Uncategorised"].append(row)

    randomiser = random.Random(seed)
    for rows in by_category.values():
        randomiser.shuffle(rows)

    selected: list[dict[str, str]] = []
    categories = sorted(by_category)
    target_size = min(sample_size, sum(map(len, by_category.values())))
    while len(selected) < target_size:
        added = False
        for category in categories:
            if by_category[category] and len(selected) < sample_size:
                selected.append(by_category[category].pop())
                added = True
        if not added:
            break

    queue: list[dict[str, object]] = []
    fingerprint = review_dataset_fingerprint(jobs, evidence)
    versions = json.dumps(sorted({str(row.get("extraction_version") or "") for row in evidence}))
    population_categories = json.dumps(sorted({str(row.get("category") or "Uncategorised") for row in evidence}))
    for index, row in enumerate(selected, start=1):
        job = jobs_by_url[row["canonical_url"]]
        queue.append(
            {
                "review_id": index,
                "dataset_fingerprint": fingerprint,
                "population_extraction_versions": versions,
                "population_categories": population_categories,
                "canonical_url": row["canonical_url"],
                "job_title": job.get("title", ""),
                "employer_name": job.get("employer_name", ""),
                "skill_id": row.get("skill_id", ""),
                "skill_name": row.get("skill_name", ""),
                "category": row.get("category", ""),
                "source_phrase": row.get("source_phrase", ""),
                "context": _context(
                    job.get("description_text", ""), row.get("source_phrase", "")
                ),
                "extraction_method": row.get("extraction_method", ""),
                "extraction_version": row.get("extraction_version", ""),
                "confidence": row.get("confidence", ""),
                "reviewer_label": "",
                "review_notes": "",
            }
        )
    return queue


def _wilson_interval(correct: int, reviewed: int) -> tuple[float, float]:
    if reviewed == 0:
        return 0.0, 0.0
    z = 1.96
    proportion = correct / reviewed
    denominator = 1 + z * z / reviewed
    centre = (proportion + z * z / (2 * reviewed)) / denominator
    margin = z * math.sqrt(
        proportion * (1 - proportion) / reviewed + z * z / (4 * reviewed * reviewed)
    ) / denominator
    return round(100 * (centre - margin), 1), round(100 * (centre + margin), 1)


def evaluate_review(rows: list[dict[str, str]]) -> dict[str, object]:
    """Score completed review labels and retain unreviewed rows in the denominator report."""
    reviewed: list[tuple[dict[str, str], bool]] = []
    invalid_labels: list[str] = []
    seen_ids, seen_evidence = set(), set()
    for row in rows:
        identifier = str(row.get("review_id") or "").strip()
        identity = tuple(str(row.get(key) or "").strip() for key in ("canonical_url", "skill_id", "extraction_version"))
        if identifier and identifier in seen_ids:
            raise ValueError("Duplicate review IDs are not independent reviews.")
        if all(identity) and identity in seen_evidence:
            raise ValueError("Duplicate evidence records are not independent reviews.")
        if identifier:
            seen_ids.add(identifier)
        if all(identity):
            seen_evidence.add(identity)
        label = (row.get("reviewer_label") or "").strip().lower()
        status = str(row.get("review_status") or "").strip().lower()
        if status:
            canonical = "accepted" if label in ACCEPTED_LABELS else "rejected" if label in REJECTED_LABELS else "unreviewed"
            if status not in {"accepted", "rejected", "uncertain", "unreviewed"} or (
                canonical in {"accepted", "rejected"} and status != canonical) or (
                canonical == "unreviewed" and status in {"accepted", "rejected"}):
                raise ValueError("Review status and label disagree.")
        if not label:
            continue
        if label in ACCEPTED_LABELS:
            reviewed.append((row, True))
        elif label in REJECTED_LABELS:
            reviewed.append((row, False))
        else:
            invalid_labels.append(label)
    if invalid_labels:
        raise ValueError(f"Invalid reviewer labels: {', '.join(sorted(set(invalid_labels)))}")

    correct = sum(is_correct for _, is_correct in reviewed)
    reviewed_count = len(reviewed)
    category_results: dict[str, dict[str, object]] = {}
    categories = sorted({row.get("category") or "Uncategorised" for row, _ in reviewed})
    for category in categories:
        category_rows = [result for row, result in reviewed if (row.get("category") or "Uncategorised") == category]
        category_correct = sum(category_rows)
        category_results[category] = {
            "reviewed": len(category_rows),
            "accepted": category_correct,
            "precision_pct": _percentage(category_correct, len(category_rows)),
        }
    low, high = _wilson_interval(correct, reviewed_count)
    precision = _percentage(correct, reviewed_count)
    fingerprints = {row.get("dataset_fingerprint", "") for row in rows}
    lineage_valid = bool(rows) and len(fingerprints) == 1 and all(
        len(str(row.get("dataset_fingerprint") or "")) == 64 and
        all(char in "0123456789abcdef" for char in str(row.get("dataset_fingerprint") or "")) and
        all(row.get(key) for key in ("review_id", "canonical_url", "skill_id", "skill_name", "source_phrase", "extraction_method", "extraction_version"))
        for row in rows)
    def population(field):
        values = {str(row.get(field) or "") for row in rows}
        if len(values) != 1:
            return None
        try:
            parsed = json.loads(next(iter(values)))
        except (ValueError, StopIteration):
            return None
        return set(parsed) if isinstance(parsed, list) and parsed and all(isinstance(v, str) and v for v in parsed) else None
    required_versions = population("population_extraction_versions")
    required_categories = population("population_categories")
    lineage_valid = lineage_valid and bool(required_versions and required_categories)
    reviewed_versions = {row.get("extraction_version") for row, _ in reviewed}
    reviewed_categories = {row.get("category") or "Uncategorised" for row, _ in reviewed}
    reasons = []
    if not lineage_valid or not required_versions or not required_categories:
        reasons.append("Review lineage is incomplete. Regenerate the queue from the intended dataset before using its publication gate.")
    if reviewed_count < 100:
        reasons.append("At least 100 distinct labelled evidence records are required.")
    if not reviewed_count or correct / reviewed_count < .9:
        reasons.append("Extraction precision must be at least 90% before rounding.")
    if required_versions and not required_versions <= reviewed_versions:
        reasons.append("At least one extraction version in the population has no completed review.")
    if required_categories and not required_categories <= reviewed_categories:
        reasons.append("At least one skill category in the population has no completed review.")
    return {
        "evaluation_version": EVALUATION_VERSION,
        "dataset_fingerprint": next(iter(fingerprints)) if lineage_valid else None,
        "review_lineage_valid": lineage_valid,
        "extraction_versions": sorted(v for v in reviewed_versions if v),
        "reviewed_record_fingerprints": sorted(review_record_fingerprint(row) for row, _ in reviewed),
        "unreviewed_population_categories": sorted(required_categories - reviewed_categories) if required_categories else [],
        "gate_reasons": reasons,
        "sampling_limitation": "Wilson intervals assume independent reviewed records. Category-balanced sampling and multiple skills from one posting limit generalisation to the population. The 100-review/90% gate is a product policy, not a confidence-bound guarantee.",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "queue_size": len(rows),
        "reviewed_count": reviewed_count,
        "unreviewed_count": len(rows) - reviewed_count,
        "accepted_count": correct,
        "rejected_count": reviewed_count - correct,
        "precision_pct": precision,
        "precision_95_ci_pct": [low, high],
        "target": {"minimum_reviews": 100, "minimum_precision_pct": 90.0},
        "publication_threshold_met": not reasons,
        "category_results": category_results,
    }


def review_matches_dataset(evaluation: dict | None, jobs: list[dict], evidence: list[dict]) -> bool:
    """Check applicable v2 review and numeric gate; a bare boolean cannot release data."""
    if not isinstance(evaluation, dict):
        return False
    reviewed, accepted = evaluation.get("reviewed_count"), evaluation.get("accepted_count")
    valid = bool(
        evaluation.get("evaluation_version") == EVALUATION_VERSION and
        evaluation.get("review_lineage_valid") is True and
        evaluation.get("publication_threshold_met") is True and
        evaluation.get("gate_reasons") == [] and
        type(reviewed) is int and type(accepted) is int and
        reviewed >= 100 and 0 <= accepted <= reviewed and accepted / reviewed >= .9 and
        evaluation.get("dataset_fingerprint") == review_dataset_fingerprint(jobs, evidence)
    )
    if not valid:
        return False
    fingerprints = evaluation.get("reviewed_record_fingerprints")
    if not isinstance(fingerprints, list) or len(fingerprints) != reviewed or not all(isinstance(v, str) for v in fingerprints) or len(set(fingerprints)) != reviewed:
        return False
    by_url = {row.get("canonical_url"): row for row in jobs}
    population = set()
    for row in evidence:
        job = by_url.get(row.get("canonical_url"))
        if job is not None:
            population.add(review_record_fingerprint({**row,
                "context": _context(job.get("description_text", ""), row.get("source_phrase", "")),
                "job_title": job.get("title", ""), "employer_name": job.get("employer_name", "")}))
    return set(fingerprints) <= population


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError("No skill evidence is available for review")
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a Career Radar extraction run.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare", help="Profile data and create a review queue")
    prepare.add_argument("--jobs", type=Path, required=True)
    prepare.add_argument("--evidence", type=Path, required=True)
    prepare.add_argument("--output-dir", type=Path, default=Path("data/validation"))
    prepare.add_argument("--sample-size", type=int, default=100)
    prepare.add_argument("--seed", type=int, default=42)
    prepare.add_argument("--source-row-count", type=int)

    score = subparsers.add_parser("score", help="Score a completed human-review queue")
    score.add_argument("--review-file", type=Path, required=True)
    score.add_argument(
        "--output", type=Path, default=Path("data/validation/extraction_evaluation.json")
    )
    args = parser.parse_args()

    if args.command == "prepare":
        jobs = read_csv(args.jobs)
        evidence = read_csv(args.evidence)
        profile = build_quality_profile(jobs, evidence, args.source_row_count)
        queue = build_review_queue(jobs, evidence, args.sample_size, args.seed)
        _write_json(args.output_dir / "quality_profile.json", profile)
        _write_csv(args.output_dir / "extraction_review.csv", queue)
        print(f"Profiled {len(jobs)} jobs and created {len(queue)} review records.")
        print("Complete reviewer_label with accepted/rejected, then run the score command.")
    else:
        evaluation = evaluate_review(read_csv(args.review_file))
        _write_json(args.output, evaluation)
        precision_display = (str(evaluation['precision_pct']) + '%' if evaluation['reviewed_count'] else 'not available (no completed decisions)')
        print(
            f"Reviewed {evaluation['reviewed_count']} records; "
            f"precision: {precision_display}."
        )
        print(f"Publication threshold met: {evaluation['publication_threshold_met']}")


if __name__ == "__main__":
    main()
