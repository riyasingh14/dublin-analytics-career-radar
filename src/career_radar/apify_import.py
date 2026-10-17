"""Convert a user-provided Apify jobs export into a minimal, traceable CSV.

This command imports an existing export; it never starts a paid Actor run.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

from career_radar.ingest import write_csv
from career_radar.normalise import geography_group


FIELDS = {
    "source_job_id": "id",
    "canonical_url": "jobUrl",
    "title": "title",
    "employer_name": "companyName",
    "location_text": "location",
    "description_text": "description",
    "posted_at": "publishedAt",
}


def normalise_export(items: object, scope: str = "dublin") -> list[dict[str, str]]:
    """Validate the selected geography and allowlist job fields, excluding profiles."""
    if scope not in {"dublin", "ireland"}:
        raise ValueError("Scope must be dublin or ireland.")
    if not isinstance(items, list) or not items:
        raise ValueError("Expected a nonempty JSON array of job records.")
    rows = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Record {index} must be a JSON object.")
        row = {}
        for target, source in FIELDS.items():
            value = item.get(source)
            if value is None:
                value = ""
            if not isinstance(value, (str, int)) or isinstance(value, bool):
                raise ValueError(f"Record {index}: {source} must be text or an ID.")
            row[target] = str(value).strip()
        missing = [key for key, value in row.items() if not value and key != "posted_at"]
        if missing:
            raise ValueError(f"Record {index}: missing {', '.join(missing)}.")
        url = urlsplit(row["canonical_url"])
        if url.scheme != "https" or url.hostname not in {"linkedin.com", "www.linkedin.com", "ie.linkedin.com"} or not url.path.startswith("/jobs/view/") or url.username or url.password:
            raise ValueError(f"Record {index}: expected an HTTPS LinkedIn job URL.")
        geography = geography_group(row["location_text"])
        if geography == "Outside scope / unknown" or (scope == "dublin" and geography != "Dublin"):
            raise ValueError(f"Record {index}: location needs {scope} scope review.")
        # Queries and fragments are unnecessary for source evidence and may carry tracking.
        row["canonical_url"] = f"https://www.linkedin.com{url.path.rstrip('/')}"
        rows.append(row)
    return rows


def import_export(
    input_path: Path,
    output_dir: Path,
    collected_at: str | None = None,
    run_id: str | None = None,
    scope: str = "dublin",
) -> Path:
    if collected_at:
        timestamp = datetime.fromisoformat(collected_at.replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise ValueError("Collection timestamp must include a timezone.")
    raw = input_path.read_bytes()
    items = json.loads(raw)
    rows = normalise_export(items, scope)
    # A fresh directory prevents accidental replacement of a previous dataset.
    output_dir.mkdir(parents=True, exist_ok=False)
    output = output_dir / "jobs.csv"
    write_csv(output, rows, list(FIELDS))
    provenance = {
        "source": "LinkedIn via user-provided Apify export",
        "actor": "bebity/linkedin-jobs-scraper",
        "export_sha256": hashlib.sha256(raw).hexdigest(),
        "collection_timestamp": collected_at,
        "apify_run_id": run_id,
        "source_row_count": len(rows),
        "distinct_source_ids": len({row["source_job_id"] for row in rows}),
        "data_status": "unreviewed",
        "geographic_scope": scope,
        "job_searches": [
            {
                "source_job_id": row["source_job_id"],
                "searched_title": (item.get("scrapingInfo") or {}).get("title", ""),
                "searched_location": (item.get("scrapingInfo") or {}).get("location", ""),
            }
            for row, item in zip(rows, items)
            if isinstance(item.get("scrapingInfo") or {}, dict)
        ],
        "limitations": [
            "User-provided source; platform authorisation was not independently verified.",
            "Search terms are not evidence of a posting's classified role.",
            "Recruiter profile fields are excluded; descriptions still require personal-data review.",
        ],
    }
    (output_dir / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True, help="A new directory under data/raw/")
    parser.add_argument("--collected-at", help="Actual Actor collection timestamp, with timezone; omit if unknown")
    parser.add_argument("--run-id", help="Optional non-secret Apify run ID")
    parser.add_argument("--scope", choices=("dublin", "ireland"), default="dublin")
    args = parser.parse_args()
    try:
        output = import_export(args.input, args.output_dir, args.collected_at, args.run_id, args.scope)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Import failed: {error}\n")
    print(f"Wrote minimal job CSV: {output}")


if __name__ == "__main__":
    main()
