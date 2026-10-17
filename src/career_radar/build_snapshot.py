"""Build a web-ready, provenance-labelled Career Radar snapshot."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from career_radar.analytics import build_market_summary, read_csv


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
    args = parser.parse_args()

    summary = build_market_summary(read_csv(args.jobs), read_csv(args.evidence))
    snapshot = {
        "metadata": {
            "dataset_label": args.dataset_label,
            "data_status": args.data_status,
            "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
            "publish_allowed": args.data_status == "validated",
            "disclosure": (
                "Sample-based signals only. Coverage depends on documented sources and collection dates."
            ),
        },
        "market": summary,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(f"Built {args.data_status} snapshot for {summary['sample_size']} postings.")
    print(f"Public publishing allowed: {snapshot['metadata']['publish_allowed']}")


if __name__ == "__main__":
    main()
