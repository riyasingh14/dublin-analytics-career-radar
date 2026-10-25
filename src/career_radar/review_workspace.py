"""Private manual annotation, resumable only against the same immutable queue."""
from __future__ import annotations

import csv
from copy import deepcopy
import hashlib
import io
import json

from career_radar.validation import ACCEPTED_LABELS, REJECTED_LABELS, evaluate_review

MAX_BYTES = 4 * 1024 * 1024
MAX_ROWS = 1000
STATUSES = {"unreviewed", "accepted", "rejected", "uncertain"}
SOURCE_FIELDS = ("review_id", "dataset_fingerprint", "population_extraction_versions",
                 "population_categories", "canonical_url", "job_title", "employer_name",
                 "skill_id", "skill_name", "category", "source_phrase", "context",
                 "extraction_method", "extraction_version", "confidence")
REQUIRED_FIELDS = {"review_id", "canonical_url", "skill_id", "skill_name", "category",
                   "source_phrase", "context", "extraction_version"}


def _decode(content: bytes) -> str:
    if not isinstance(content, bytes) or len(content) > MAX_BYTES:
        raise ValueError("Review files must be at most 4 MiB.")
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise ValueError("Review files must use UTF-8 encoding.") from None


def _status(row: dict) -> str:
    label = str(row.get("reviewer_label") or "").strip().lower()
    decision = str(row.get("review_status") or "").strip().lower()
    canonical = "accepted" if label in ACCEPTED_LABELS else "rejected" if label in REJECTED_LABELS else "unreviewed"
    if label and canonical == "unreviewed":
        raise ValueError("Review labels must be accepted, rejected or blank.")
    if decision and decision not in STATUSES:
        raise ValueError("Unknown review decision.")
    if decision and ((canonical in {"accepted", "rejected"} and decision != canonical) or
                     (canonical == "unreviewed" and decision in {"accepted", "rejected"})):
        raise ValueError("Review status and label disagree.")
    return decision or canonical


def load_queue_csv(content: bytes) -> list[dict[str, str]]:
    try:
        return _load_queue_csv(content)
    except csv.Error:
        raise ValueError("CSV fields are malformed or exceed the supported field size.") from None


def _load_queue_csv(content: bytes) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(_decode(content)), strict=True)
    if not reader.fieldnames or not REQUIRED_FIELDS <= set(reader.fieldnames):
        raise ValueError("The CSV must be an extraction review queue with source context and record IDs.")
    if len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise ValueError("Duplicate CSV columns are not supported.")
    queue, seen_ids, seen_evidence = [], set(), set()
    for source in reader:
        if len(queue) >= MAX_ROWS:
            raise ValueError("Review queues are limited to 1,000 records; split the source review into documented batches.")
        if None in source or any(value is None for value in source.values()):
            raise ValueError("Every CSV row must match its header.")
        row = {key: str(source.get(key) or "") for key in SOURCE_FIELDS}
        for key in ("review_id", "canonical_url", "skill_id", "extraction_version"):
            row[key] = row[key].strip()
        if any(not row[key].strip() for key in REQUIRED_FIELDS - {"context"}):
            raise ValueError("A review record is missing its identity or source evidence.")
        identity = (row["canonical_url"], row["skill_id"], row["extraction_version"])
        if row["review_id"] in seen_ids or identity in seen_evidence:
            raise ValueError("Duplicate review IDs or evidence records are not independent reviews.")
        seen_ids.add(row["review_id"])
        seen_evidence.add(identity)
        status = _status(source)
        notes = source.get("review_notes", "")
        if len(notes) > 1000:
            raise ValueError("Review notes are limited to 1,000 characters per record.")
        row.update(reviewer_label=status if status in {"accepted", "rejected"} else "",
                   review_status=status, review_notes=notes)
        queue.append(row)
    if not queue:
        raise ValueError("The review queue has no records.")
    return queue


def queue_fingerprint(queue: list[dict]) -> str:
    immutable = [{key: str(row.get(key) or "") for key in SOURCE_FIELDS} for row in queue]
    immutable.sort(key=lambda row: row["review_id"])
    return hashlib.sha256(json.dumps(immutable, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def initial_annotations(queue: list[dict]) -> dict:
    return {row["review_id"]: {"status": _status(row), "notes": row.get("review_notes", "")}
            for row in queue}


def _checked_annotations(queue: list[dict], annotations: dict) -> dict:
    identifiers = {row["review_id"] for row in queue}
    if not isinstance(annotations, dict) or set(annotations) != identifiers:
        raise ValueError("Annotation record IDs do not match this queue.")
    for item in annotations.values():
        if not isinstance(item, dict) or set(item) != {"status", "notes"}:
            raise ValueError("Invalid annotation structure.")
        if not isinstance(item["status"], str) or item["status"] not in STATUSES or not isinstance(item["notes"], str) or len(item["notes"]) > 1000:
            raise ValueError("Unknown decision or notes exceeding 1,000 characters.")
    return annotations


def annotate(queue: list[dict], annotations: dict, identifier: str, status: str, notes: str) -> dict:
    result = deepcopy(_checked_annotations(queue, annotations))
    if identifier not in result:
        raise ValueError("Choose a record from this queue.")
    result[identifier] = {"status": status, "notes": notes}
    return _checked_annotations(queue, result)


def materialise_review(queue: list[dict], annotations: dict) -> list[dict]:
    _checked_annotations(queue, annotations)
    return [{**row, "reviewer_label": annotations[row["review_id"]]["status"]
             if annotations[row["review_id"]]["status"] in {"accepted", "rejected"} else "",
             "review_status": annotations[row["review_id"]]["status"],
             "review_notes": annotations[row["review_id"]]["notes"]} for row in queue]


def review_progress(queue: list[dict], annotations: dict) -> dict:
    _checked_annotations(queue, annotations)
    def count(rows):
        counts = {status: sum(annotations[row["review_id"]]["status"] == status for row in rows) for status in STATUSES}
        return {**counts, "total": len(rows), "completed": counts["accepted"] + counts["rejected"]}
    return {**count(queue), "by_category": {category: count([r for r in queue if r["category"] == category])
            for category in sorted({row["category"] for row in queue})}}


def evaluate_workspace(queue: list[dict], annotations: dict) -> dict:
    evaluation = evaluate_review(materialise_review(queue, annotations))
    return {**evaluation, "uncertain_count": review_progress(queue, annotations)["uncertain"],
            "queue_fingerprint": queue_fingerprint(queue),
            "label_origin": "User-supplied manual decisions; identity and independence are not authenticated.",
            "limitation": "Precision measures reviewed extracted mentions, not recall, market coverage, requirement accuracy or source display permission. No automatic publication is performed."}


def export_review_csv(queue: list[dict], annotations: dict) -> bytes:
    rows = materialise_review(queue, annotations)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=[*SOURCE_FIELDS, "reviewer_label", "review_status", "review_notes"])
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def export_checkpoint(queue: list[dict], annotations: dict) -> bytes:
    _checked_annotations(queue, annotations)
    return json.dumps({"checkpoint_version": "review-workspace-v1", "queue_fingerprint": queue_fingerprint(queue),
                       "annotations": annotations}, ensure_ascii=False, indent=2).encode("utf-8")


def restore_checkpoint(queue: list[dict], content: bytes) -> dict:
    try:
        checkpoint = json.loads(_decode(content))
    except (ValueError, TypeError, RecursionError):
        raise ValueError("Checkpoint must be a valid UTF-8 JSON review file.") from None
    if (not isinstance(checkpoint, dict) or set(checkpoint) != {"checkpoint_version", "queue_fingerprint", "annotations"} or
        checkpoint.get("checkpoint_version") != "review-workspace-v1" or
        checkpoint.get("queue_fingerprint") != queue_fingerprint(queue)):
        raise ValueError("This checkpoint belongs to a different queue or source/rule version.")
    return deepcopy(_checked_annotations(queue, checkpoint["annotations"]))
