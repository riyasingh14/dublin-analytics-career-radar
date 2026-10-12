"""CSV ingestion CLI for authorised Career Radar job sources.

Usage:
    PYTHONPATH=src python -m career_radar.ingest \
      --input path/to/authorised_jobs.csv --source-name "Approved source"
"""

from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime
from pathlib import Path

from career_radar.normalise import (
    classify_role,
    classify_work_pattern,
    deduplication_key,
    extract_skills,
    load_taxonomy,
)


REQUIRED_COLUMNS = {
    "source_job_id",
    "canonical_url",
    "title",
    "employer_name",
    "location_text",
    "description_text",
}


def read_jobs(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        missing = REQUIRED_COLUMNS.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Input is missing required columns: {', '.join(sorted(missing))}")
        return list(reader)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalise authorised Career Radar job data.")
    parser.add_argument("--input", type=Path, required=True, help="Authorised CSV export to process")
    parser.add_argument("--source-name", required=True, help="Documented source name")
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--taxonomy", type=Path, default=Path("data/reference/skills.csv"))
    args = parser.parse_args()

    collection_time = datetime.now(UTC).replace(microsecond=0).isoformat()
    taxonomy = load_taxonomy(args.taxonomy)
    jobs = read_jobs(args.input)
    normalised_jobs: list[dict[str, object]] = []
    evidence_rows: list[dict[str, object]] = []
    seen_keys: set[str] = set()

    for row in jobs:
        description = row["description_text"]
        key = deduplication_key(row["title"], row["employer_name"], row["location_text"], description)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        role_name, role_confidence = classify_role(row["title"])
        job = {
            "source_name": args.source_name,
            "source_job_id": row["source_job_id"],
            "canonical_url": row["canonical_url"],
            "title": row["title"],
            "employer_name": row["employer_name"],
            "location_text": row["location_text"],
            "posted_at": row.get("posted_at", ""),
            "work_pattern": classify_work_pattern(" ".join([row["location_text"], description])),
            "role_name": role_name or "Unclassified",
            "role_confidence": role_confidence,
            "collection_timestamp": collection_time,
            "deduplication_key": key,
            "description_text": description,
        }
        normalised_jobs.append(job)
        for evidence in extract_skills(description, taxonomy):
            evidence_rows.append(
                {
                    "source_job_id": row["source_job_id"],
                    "canonical_url": row["canonical_url"],
                    "collection_timestamp": collection_time,
                    **evidence,
                }
            )

    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    write_csv(
        args.output_dir / f"jobs_normalised_{stamp}.csv",
        normalised_jobs,
        list(normalised_jobs[0]) if normalised_jobs else ["source_name", "source_job_id"],
    )
    write_csv(
        args.output_dir / f"job_skill_evidence_{stamp}.csv",
        evidence_rows,
        list(evidence_rows[0]) if evidence_rows else ["source_job_id", "skill_id"],
    )
    print(f"Imported {len(normalised_jobs)} unique jobs from {len(jobs)} source rows.")
    print(f"Extracted {len(evidence_rows)} skill-evidence records using taxonomy-v1.")


if __name__ == "__main__":
    main()
