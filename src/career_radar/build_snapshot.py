"""Build a web-ready, provenance-labelled Career Radar snapshot."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from career_radar.analytics import build_evidence_records, build_market_summary, read_csv
from career_radar.validation import build_quality_profile
from career_radar.normalise import geography_group


def build_snapshot_payload(
    jobs: list[dict[str, str]],
    evidence: list[dict[str, str]],
    dataset_label: str,
    data_status: str,
    source_row_count: int | None = None,
    evaluation: dict[str, object] | None = None,
    provenance: dict[str, object] | None = None,
) -> dict[str, object]:
    summary = build_market_summary(jobs, evidence)
    quality = build_quality_profile(jobs, evidence, source_row_count)
    threshold_met = bool(evaluation and evaluation.get("publication_threshold_met"))
    publish_allowed = data_status == "validated" and threshold_met
    return {
        "schema_version": 2,
        "metadata": {
            "dataset_label": dataset_label,
            "data_status": data_status,
            "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
            "publish_allowed": publish_allowed,
            "disclosure": (
                "Sample-based signals only. Coverage depends on documented sources and collection dates."
            ),
        },
        "quality": quality,
        "evaluation": evaluation,
        "market": summary,
        "geography_markets": {
            geography: build_market_summary(
                [job for job in jobs if geography_group(job.get("location_text", "")) == geography],
                evidence,
            )
            for geography in sorted({geography_group(job.get("location_text", "")) for job in jobs})
        },
        "evidence": build_evidence_records(jobs, evidence),
        # Explicit allowlist: no recruiter profiles or arbitrary imported metadata.
        # Descriptions support local diagnostic/readiness; public data still needs review.
        "postings": [
            {
                **{key: str(job.get(key, "")) for key in (
                    "source_job_id", "canonical_url", "title", "employer_name", "location_text",
                    "role_name", "work_pattern", "description_text", "posted_at", "source_name",
                )},
                "geography": geography_group(job.get("location_text", "")),
            }
            for job in jobs
        ],
        "provenance": {
            "geographic_scope": (provenance or {}).get("geographic_scope", "not supplied"),
            "collection_timestamp": (provenance or {}).get("collection_timestamp"),
            "actor": (provenance or {}).get("actor"),
            "export_sha256": (provenance or {}).get("export_sha256"),
            "source_counts": quality["source_counts"],
            "extraction_versions": sorted({row.get("extraction_version", "unknown") for row in evidence}),
            "role_classification_versions": sorted({row.get("role_classification_version", "unknown") for row in jobs}),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Career Radar market metrics.")
    parser.add_argument("--jobs", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/processed/market_snapshot.json"))
    parser.add_argument("--dataset-label", required=True)
    parser.add_argument(
        "--data-status",
        choices=("fixture", "unreviewed", "validated"),
        default="unreviewed",
        help="Controls whether the snapshot is eligible for public claims",
    )
    parser.add_argument(
        "--source-row-count",
        type=int,
        help="Raw source rows before deduplication, recorded in the ingestion manifest",
    )
    parser.add_argument(
        "--evaluation",
        type=Path,
        help="JSON output from career_radar.validation score",
    )
    parser.add_argument("--provenance", type=Path, help="Source-import provenance JSON, if available")
    args = parser.parse_args()

    jobs = read_csv(args.jobs)
    evidence = read_csv(args.evidence)
    evaluation = (
        json.loads(args.evaluation.read_text(encoding="utf-8")) if args.evaluation else None
    )
    snapshot = build_snapshot_payload(
        jobs,
        evidence,
        args.dataset_label,
        args.data_status,
        args.source_row_count,
        evaluation,
        json.loads(args.provenance.read_text(encoding="utf-8")) if args.provenance else None,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(f"Built {args.data_status} snapshot for {snapshot['market']['sample_size']} postings.")
    print(f"Public publishing allowed: {snapshot['metadata']['publish_allowed']}")


if __name__ == "__main__":
    main()
