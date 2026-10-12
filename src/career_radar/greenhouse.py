"""Connector for explicitly approved public Greenhouse job-board feeds.

The connector is disabled by default because each source must be reviewed and added
to data/reference/greenhouse_sources.csv before collection.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        return " ".join(" ".join(self.parts).split())


def html_to_text(value: str) -> str:
    parser = TextExtractor()
    parser.feed(value or "")
    return html.unescape(parser.text())


def normalise_greenhouse_job(job: dict[str, object], source_name: str) -> dict[str, str]:
    location = job.get("location") or {}
    location_name = location.get("name", "") if isinstance(location, dict) else ""
    return {
        "source_job_id": str(job["id"]),
        "canonical_url": str(job["absolute_url"]),
        "title": str(job["title"]),
        "employer_name": source_name,
        "location_text": str(location_name),
        "description_text": html_to_text(str(job.get("content", ""))),
        "posted_at": str(job.get("updated_at", "")),
    }


def fetch_board(board_token: str) -> list[dict[str, object]]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
    request = Request(url, headers={"User-Agent": "DublinAnalyticsCareerRadar/0.1 (portfolio project)"})
    with urlopen(request, timeout=30) as response:
        payload = json.load(response)
    jobs = payload.get("jobs")
    if not isinstance(jobs, list):
        raise ValueError(f"Unexpected response for Greenhouse board: {board_token}")
    return jobs


def approved_sources(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    return [
        row
        for row in rows
        if row.get("active", "").strip().lower() == "true"
        and row.get("terms_checked_on", "").strip()
        and row.get("board_token", "").strip()
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Export postings from approved Greenhouse boards.")
    parser.add_argument("--sources", type=Path, default=Path("data/reference/greenhouse_sources.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/raw/greenhouse_jobs.csv"))
    args = parser.parse_args()

    sources = approved_sources(args.sources)
    if not sources:
        raise SystemExit(
            "No approved sources configured. Record a board token, terms check date, and active=true first."
        )

    rows: list[dict[str, str]] = []
    for source in sources:
        for job in fetch_board(source["board_token"]):
            normalised = normalise_greenhouse_job(job, source["source_name"])
            if "dublin" in normalised["location_text"].lower():
                rows.append(normalised)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=[
            "source_job_id", "canonical_url", "title", "employer_name",
            "location_text", "description_text", "posted_at",
        ])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Exported {len(rows)} Dublin postings from {len(sources)} approved Greenhouse sources.")
    print(f"Collection timestamp: {datetime.now(UTC).replace(microsecond=0).isoformat()}")


if __name__ == "__main__":
    main()
