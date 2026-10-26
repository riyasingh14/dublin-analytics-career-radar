"""Private, human-annotated evaluation of source-grounded skill requirements.

Preparation never creates gold labels. Scoring is independent of market release
approval and does not validate broader Diagnostic findings or hiring outcomes.
"""
from __future__ import annotations

import argparse
import csv
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from career_radar.normalise import ROLE_RULES, TAXONOMY_VERSION, classify_role, load_taxonomy
from career_radar.requirements_model import EXTRACTION_VERSION, MAX_REQUIREMENTS, extract_requirements

SCHEMA = "requirement-gold-v1"
REPORT_SCHEMA = "requirement-evaluation-v1"
PREDICTION_SCHEMA = "requirement-predictions-v1"
MAX_BYTES = 16 * 1024 * 1024
MAX_CASES = 200
MAX_TEXT = 30000
KINDS = ("required", "preferred", "uncertain", "negated")
ROOT = Path(__file__).resolve().parents[2]
DOCUMENT_FIELDS = {"schema_version", "created_at", "taxonomy_version", "annotation_unit", "cases"}
CASE_FIELDS = {"case_id", "source_job_id", "title", "role_name", "text", "text_sha256", "review_status", "expected_requirements"}
LABEL_FIELDS = {"skill_id", "requirement_type", "start", "end"}


def _now(now=None):
    value = now or datetime.now(UTC)
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("Evaluation time requires a timezone")
    return value.astimezone(UTC)


def _stamp(now):
    return _now(now).replace(microsecond=0).isoformat()


def _text(value, field, maximum, *, empty=False):
    if not isinstance(value, str) or len(value) > maximum or "\x00" in value or (not empty and not value.strip()):
        raise ValueError(f"Invalid {field}")
    return value


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _identity(source_id, title, role, text_hash):
    return _sha(json.dumps([source_id, title, role, text_hash], ensure_ascii=False))


def _taxonomy():
    return load_taxonomy(ROOT / "data/reference/skills.csv")


def _exact_fields(value, fields, name):
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{name} has missing or unsupported fields")


def _validate_document(document, *, now=None):
    _exact_fields(document, DOCUMENT_FIELDS, "Gold document")
    if document["schema_version"] != SCHEMA or document["taxonomy_version"] != TAXONOMY_VERSION or document["annotation_unit"] != "all-skill-mentions":
        raise ValueError("Unsupported gold schema, taxonomy or annotation unit")
    _text(document["created_at"], "gold creation timestamp", 50)
    try:
        created = datetime.fromisoformat(document["created_at"].replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as error:
        raise ValueError("Invalid gold creation timestamp") from error
    if created.tzinfo is None or created > _now(now):
        raise ValueError("Gold creation timestamp must be timezone-aware and not in the future")
    cases = document["cases"]
    if not isinstance(cases, list) or not 1 <= len(cases) <= MAX_CASES:
        raise ValueError("Gold document must contain between 1 and 200 cases")
    skills = {skill.skill_id: skill for skill in _taxonomy()}
    seen_ids, seen_sources, seen_texts = set(), set(), set()
    for case in cases:
        _exact_fields(case, CASE_FIELDS, "Gold case")
        source = _text(case["source_job_id"], "source job ID", 200)
        title = _text(case["title"], "source title", 300)
        text = _text(case["text"], "description", MAX_TEXT)
        role = _text(case["role_name"], "role", 100)
        if role not in {*ROLE_RULES, "Unclassified"}:
            raise ValueError("Unknown role; use an explicit controlled role or Unclassified")
        digest = case["text_sha256"]
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest) or digest != _sha(text):
            raise ValueError("Source description hash does not match")
        expected_id = _identity(source, title, role, digest)
        if case["case_id"] != expected_id or expected_id in seen_ids or source in seen_sources or digest in seen_texts:
            raise ValueError("Case identity, source ID or source text is inconsistent or duplicated")
        seen_ids.add(expected_id); seen_sources.add(source); seen_texts.add(digest)
        if not isinstance(case["review_status"], str) or case["review_status"] not in {"pending", "completed"}:
            raise ValueError("Review status must be pending or completed")
        labels = case["expected_requirements"]
        if not isinstance(labels, list) or len(labels) > MAX_REQUIREMENTS:
            raise ValueError("Expected requirements must be a bounded list")
        seen_labels = set()
        for label in labels:
            _exact_fields(label, LABEL_FIELDS, "Gold requirement")
            skill_id = label["skill_id"]
            if not isinstance(skill_id, str) or skill_id not in skills:
                raise ValueError("Gold requirement uses an unknown skill ID")
            if label["requirement_type"] not in KINDS:
                raise ValueError("Gold requirement has an unknown requirement type")
            start, end = label["start"], label["end"]
            if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text) or not text[start:end].strip():
                raise ValueError("Gold requirement must have valid nonempty Unicode code-point spans")
            anchor = (skill_id, start, end)
            if anchor in seen_labels:
                raise ValueError("Duplicate or conflicting requirement labels at one skill/span")
            seen_labels.add(anchor)
    return document


def prepare_requirement_cases(rows: list[dict], *, now=None) -> dict:
    """Scaffold private cases without extracting or assigning any gold labels."""
    if not isinstance(rows, list) or not 1 <= len(rows) <= MAX_CASES:
        raise ValueError("Prepare a curated set of between 1 and 200 normalized jobs")
    cases = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Normalized job input must contain objects")
        source = _text(row.get("source_job_id"), "source job ID", 200)
        title = _text(row.get("title"), "source title", 300)
        text = _text(row.get("description_text"), "description", MAX_TEXT)
        provided_role = row.get("role_name")
        role = ((classify_role(title)[0] or "Unclassified")
                if provided_role is None or provided_role == ""
                else _text(provided_role, "role", 100))
        digest = _sha(text)
        cases.append({"case_id": _identity(source, title, role, digest), "source_job_id": source,
                      "title": title, "role_name": role, "text": text, "text_sha256": digest,
                      "review_status": "pending", "expected_requirements": []})
    document = {"schema_version": SCHEMA, "created_at": _stamp(now), "taxonomy_version": TAXONOMY_VERSION,
                "annotation_unit": "all-skill-mentions", "cases": sorted(cases, key=lambda case: case["case_id"])}
    return _validate_document(document, now=now)


def _label(value):
    return {key: value[key] for key in ("skill_id", "requirement_type", "start", "end")}


def _key(value):
    return (value["skill_id"], value["start"], value["end"], value["requirement_type"])


def _metrics(tp, fp, fn):
    return {"true_positives": tp, "false_positives": fp, "false_negatives": fn,
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None}


def _compare(gold, predictions):
    expected, actual = {_key(label) for label in gold}, {_key(label) for label in predictions}
    return _metrics(len(expected & actual), len(actual - expected), len(expected - actual))


def _aggregate(rows):
    return _metrics(*(sum(row[name] for row in rows) for name in ("true_positives", "false_positives", "false_negatives")))


def requirement_prediction_aid(document: dict, *, now=None) -> dict:
    """Separate optional machine output; deliberately incompatible with gold schema."""
    _validate_document(document, now=now)
    taxonomy = _taxonomy()
    return {"schema_version": PREDICTION_SCHEMA, "created_at": _stamp(now), "not_gold": True,
            "extraction_version": EXTRACTION_VERSION, "taxonomy_version": TAXONOMY_VERSION,
            "cases": [{"case_id": case["case_id"], "text_sha256": case["text_sha256"],
                       "predicted_requirements": [{**_label(row), "source_phrase": row["source_phrase"]}
                                                  for row in extract_requirements(case["text"], taxonomy)]}
                      for case in document["cases"]]}


def score_requirement_cases(document: dict, *, now=None) -> dict:
    """Micro-average exact skill/span/type agreement on completed human cases only."""
    _validate_document(document, now=now)
    taxonomy = _taxonomy()
    categories = {skill.skill_id: skill.category for skill in taxonomy}
    all_categories = sorted(set(categories.values()))
    confusion = {expected: {actual: 0 for actual in KINDS} for expected in KINDS}
    per_role, per_category, results = {}, {}, []
    for category in all_categories:
        per_category[category] = {"completed_cases_with_gold": 0, "completed_cases_with_predictions": 0,
                                  "gold_requirements": 0, "predicted_requirements": 0, "_metrics": []}
    for case in document["cases"]:
        role = per_role.setdefault(case["role_name"], {"cases": 0, "completed_cases": 0,
                                                       "pending_cases": 0, "gold_requirements": 0,
                                                       "predicted_requirements": 0, "_metrics": []})
        role["cases"] += 1
        if case["review_status"] == "pending":
            role["pending_cases"] += 1
            continue
        role["completed_cases"] += 1
        gold = case["expected_requirements"]
        predictions = [_label(row) for row in extract_requirements(case["text"], taxonomy)]
        metrics = _compare(gold, predictions)
        role["_metrics"].append(metrics)
        role["gold_requirements"] += len(gold)
        role["predicted_requirements"] += len(predictions)
        expected_by_anchor = {(row["skill_id"], row["start"], row["end"]): row["requirement_type"] for row in gold}
        for prediction in predictions:
            expected = expected_by_anchor.get((prediction["skill_id"], prediction["start"], prediction["end"]))
            if expected is not None:
                confusion[expected][prediction["requirement_type"]] += 1
        for category in all_categories:
            expected = [row for row in gold if categories[row["skill_id"]] == category]
            actual = [row for row in predictions if categories[row["skill_id"]] == category]
            record = per_category[category]
            record["completed_cases_with_gold"] += bool(expected)
            record["completed_cases_with_predictions"] += bool(actual)
            record["gold_requirements"] += len(expected)
            record["predicted_requirements"] += len(actual)
            record["_metrics"].append(_compare(expected, actual))
        gold_keys, predicted_keys = {_key(row) for row in gold}, {_key(row) for row in predictions}
        results.append({"case_id": case["case_id"], "role_name": case["role_name"],
                        "gold_requirements": len(gold), "predicted_requirements": len(predictions),
                        "metrics": metrics,
                        "missed_requirements": [_label(row) for row in gold if _key(row) not in predicted_keys],
                        "spurious_requirements": [row for row in predictions if _key(row) not in gold_keys]})
    for record in [*per_role.values(), *per_category.values()]:
        record["metrics"] = _aggregate(record.pop("_metrics"))
    complete = len(results)
    return {"schema_version": REPORT_SCHEMA, "scored_at": _stamp(now), "source_schema": SCHEMA,
            "extraction_version": EXTRACTION_VERSION, "taxonomy_version": TAXONOMY_VERSION,
            "matching": "Exact Unicode code-point start/end + skill ID + requirement type",
            "metric_unit": "ratio", "case_count": len(document["cases"]), "completed_cases": complete,
            "pending_cases": len(document["cases"]) - complete,
            "completion_fraction": complete / len(document["cases"]),
            "metrics": _aggregate([row["metrics"] for row in results]),
            "type_confusion_counts": confusion,
            "type_confusion_scope": "Expected versus predicted type only where skill ID and exact span both match; span misses/spurious mentions are reflected in false negatives/positives.",
            "role_coverage": dict(sorted(per_role.items())),
            "category_coverage": {"taxonomy_categories": len(all_categories),
                                  "categories_with_completed_gold": sum(record["gold_requirements"] > 0 for record in per_category.values()),
                                  "by_category": per_category},
            "case_results": results,
            "limitations": ["Pending cases are excluded from all accuracy denominators.",
                            "Gold labels must be supplied by a human; this tool cannot authenticate their independence or correctness.",
                            "A type or span error counts as one false positive and one false negative under exact matching.",
                            "This evaluates requirement extraction, not general Diagnostic finding quality, labour-market publication approval or hiring outcomes.",
                            "Results describe the annotated cases, not all Irish job descriptions."],
            "publication_approval": False}


def _checked_path(path):
    value = Path(path).absolute()
    if any(part.is_symlink() for part in [value, *value.parents]):
        raise ValueError("Symlinked evaluation paths are not supported")
    return value


def _read_json(path):
    path = _checked_path(path)
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError("Missing or oversized evaluation input")
    raw = path.read_bytes()
    if len(raw) > MAX_BYTES:
        raise ValueError("Oversized evaluation input")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON fields are not supported")
            result[key] = value
        return result
    def finite(value):
        raise ValueError("Nonfinite JSON is not supported")
    try:
        return json.loads(raw, object_pairs_hook=unique, parse_constant=finite)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError("Malformed evaluation JSON") from error


def _read_jobs(path):
    path = _checked_path(path)
    if path.suffix.lower() == ".json":
        value = _read_json(path)
        if not isinstance(value, list):
            raise ValueError("Normalized job JSON must be an array")
        return value
    if path.suffix.lower() != ".csv" or not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError("Expected a bounded normalized CSV or JSON input")
    rows = []
    try:
        with path.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
                raise ValueError("Source CSV requires unique column names")
            for row in reader:
                if len(rows) >= MAX_CASES or None in row:
                    raise ValueError("Too many jobs or malformed source CSV columns")
                rows.append(row)
    except (UnicodeDecodeError, csv.Error) as error:
        raise ValueError("Malformed source CSV") from error
    return rows


def _check_new_output(path):
    value = _checked_path(path)
    if value.exists():
        raise ValueError("Evaluation output already exists; choose a new filename")
    return value


def _write_new(path, document):
    path = _check_new_output(path)
    raw = (json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
    if len(raw) > MAX_BYTES:
        raise ValueError("Evaluation output exceeds its size limit")
    path.parent.mkdir(parents=True, exist_ok=True)
    _checked_path(path)
    descriptor, temporary = tempfile.mkstemp(prefix=".requirement-evaluation-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as file:
            file.write(raw)
        # Hard-link promotion is atomic and cannot replace an existing output.
        os.link(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Private, human-gold requirement evaluation; no auto-labels or publication approval")
    sub = parser.add_subparsers(dest="action", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--input", type=Path, required=True)
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--predictions-output", type=Path)
    score = sub.add_parser("score")
    score.add_argument("--input", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        _check_new_output(args.output)
        if args.action == "prepare":
            if args.predictions_output:
                _check_new_output(args.predictions_output)
                if args.predictions_output.absolute() == args.output.absolute():
                    raise ValueError("Gold and prediction aid outputs must be separate files")
            result = prepare_requirement_cases(_read_jobs(args.input))
            aid = requirement_prediction_aid(result) if args.predictions_output else None
            _write_new(args.output, result)
            if aid is not None:
                _write_new(args.predictions_output, aid)
            print(json.dumps({"cases": len(result["cases"]), "completed_cases": 0, "gold_labels_created": 0}))
        else:
            result = score_requirement_cases(_read_json(args.input))
            _write_new(args.output, result)
            print(json.dumps({"case_count": result["case_count"], "completed_cases": result["completed_cases"], "metrics": result["metrics"], "publication_approval": False}))
    except OSError:
        parser.exit(2, "Requirement evaluation rejected: could not read or create the private files.\n")
    except ValueError as error:
        parser.exit(2, f"Requirement evaluation rejected: {error}\n")


if __name__ == "__main__":
    main()
