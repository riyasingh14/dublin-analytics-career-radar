"""Export Dublin analytics-role postings from the official Adzuna Ireland API.

Credentials are read only from ADZUNA_APP_ID and ADZUNA_APP_KEY environment
variables. They are never written to files or logs.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_QUERIES = ("data analyst", "business analyst", "bi analyst", "product analyst")
DEFAULT_MAX_REQUESTS = 4


def planned_request_count(queries: tuple[str, ...], pages: int) -> int:
    if pages < 1:
        raise ValueError("pages must be at least 1")
    return len(queries) * pages


def normalise_adzuna_job(job: dict[str, object]) -> dict[str, str]:
    company = job.get("company") or {}
    location = job.get("location") or {}
    company_name = company.get("display_name", "") if isinstance(company, dict) else ""
    location_name = location.get("display_name", "") if isinstance(location, dict) else ""
    return {
        "source_job_id": str(job["id"]),
        "canonical_url": str(job["redirect_url"]),
        "title": str(job["title"]),
        "employer_name": str(company_name),
        "location_text": str(location_name),
        "description_text": str(job.get("description", "")),
        "posted_at": str(job.get("created", "")),
    }


def fetch_page(query: str, page: int, app_id: str, app_key: str) -> list[dict[str, object]]:
    params = urlencode(
        {
            "app_id": app_id,
            "app_key": app_key,
            "what": query,
            "where": "Dublin",
            "results_per_page": 50,
            "content-type": "application/json",
        }
    )
    url = f"https://api.adzuna.com/v1/api/jobs/ie/search/{page}?{params}"
    request = Request(url, headers={"User-Agent": "DublinAnalyticsCareerRadar/0.1 (portfolio project)"})
    with urlopen(request, timeout=30) as response:
        payload = json.load(response)
    results = payload.get("results")
    if not isinstance(results, list):
        raise ValueError("Unexpected response from Adzuna API")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Dublin postings from the official Adzuna Ireland API.")
    parser.add_argument("--output", type=Path, default=Path("data/raw/adzuna_dublin_jobs.csv"))
    parser.add_argument(
        "--pages",
        type=int,
        default=1,
        help="Pages per target role query; defaults to one for the free-tier collection policy",
    )
    parser.add_argument(
        "--max-requests",
        type=int,
        default=DEFAULT_MAX_REQUESTS,
        help="Hard request ceiling for this run (default: 4)",
    )
    parser.add_argument(
        "--terms-checked-on",
        required=True,
        help="Date on which the API terms and permitted portfolio use were reviewed (YYYY-MM-DD)",
    )
    parser.add_argument("--query", action="append", dest="queries", help="Add or replace a role query")
    args = parser.parse_args()

    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        raise SystemExit("Set ADZUNA_APP_ID and ADZUNA_APP_KEY securely before running this connector.")
    queries = tuple(args.queries) if args.queries else DEFAULT_QUERIES
    try:
        request_count = planned_request_count(queries, args.pages)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    if args.max_requests < 1:
        raise SystemExit("--max-requests must be at least 1")
    if request_count > args.max_requests:
        raise SystemExit(
            f"Planned run needs {request_count} API requests, exceeding the "
            f"--max-requests limit of {args.max_requests}."
        )

    rows_by_source_id: dict[str, dict[str, str]] = {}
    for query in queries:
        for page in range(1, args.pages + 1):
            for job in fetch_page(query, page, app_id, app_key):
                normalised = normalise_adzuna_job(job)
                if "dublin" in normalised["location_text"].lower():
                    rows_by_source_id[normalised["source_job_id"]] = normalised

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=[
            "source_job_id", "canonical_url", "title", "employer_name",
            "location_text", "description_text", "posted_at",
        ])
        writer.writeheader()
        writer.writerows(rows_by_source_id.values())

    print(f"Exported {len(rows_by_source_id)} unique Dublin postings from {len(queries)} role queries.")
    print(f"API requests used: {request_count} of the {args.max_requests} run limit.")
    print(f"Terms reviewed on: {args.terms_checked_on}")
    print(f"Collection timestamp: {datetime.now(UTC).replace(microsecond=0).isoformat()}")


if __name__ == "__main__":
    main()
