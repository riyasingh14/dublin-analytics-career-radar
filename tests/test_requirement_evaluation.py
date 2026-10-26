"""All gold labels below are test-authored, never a real human evaluation."""
import contextlib
import copy
from datetime import UTC, datetime, timedelta
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from career_radar.requirement_evaluation import (MAX_BYTES, MAX_CASES, MAX_TEXT,
    main, prepare_requirement_cases, requirement_prediction_aid, score_requirement_cases,
    _read_jobs, _read_json, _write_new)

NOW = datetime(2026, 10, 26, 12, tzinfo=UTC)


def job(text="📊 SQL required. Python preferred.", identifier="fixture-1", title="Data Analyst", role="Data Analyst"):
    return {"source_job_id": identifier, "title": title, "role_name": role,
            "description_text": text, "candidate_email": "DO_NOT_KEEP_PRIVATE", "arbitrary_private_notes": "DO_NOT_KEEP_PRIVATE"}


def label(text, phrase, skill, kind):
    start = text.index(phrase)
    return {"skill_id": skill, "requirement_type": kind, "start": start, "end": start + len(phrase)}


def completed(text="📊 SQL required. Python preferred.", labels=None):
    document = prepare_requirement_cases([job(text)], now=NOW)
    case = document["cases"][0]
    case["review_status"] = "completed"
    case["expected_requirements"] = labels if labels is not None else [label(text, "SQL", "sql", "required"), label(text, "Python", "python", "preferred")]
    return document


class RequirementEvaluationTests(unittest.TestCase):
    def test_prepare_keeps_source_exactly_and_never_assigns_labels(self):
        row = job()
        result = prepare_requirement_cases([row], now=NOW)
        case = result["cases"][0]
        self.assertEqual(case["text"], row["description_text"])
        self.assertEqual(case["text_sha256"], hashlib.sha256(row["description_text"].encode()).hexdigest())
        self.assertEqual(case["review_status"], "pending")
        self.assertEqual(case["expected_requirements"], [])
        self.assertNotIn("DO_NOT_KEEP_PRIVATE", json.dumps(result))
        self.assertNotIn("predicted_requirements", json.dumps(result))

    def test_none_complete_has_null_accuracy_not_perfect(self):
        result = score_requirement_cases(prepare_requirement_cases([job()], now=NOW), now=NOW)
        self.assertEqual((result["completed_cases"], result["pending_cases"]), (0, 1))
        self.assertEqual(result["metrics"], {"true_positives": 0, "false_positives": 0, "false_negatives": 0,
                                           "precision": None, "recall": None, "f1": None})
        self.assertEqual(result["case_results"], [])
        self.assertFalse(result["publication_approval"])

    def test_exact_unicode_spans_score_two_matches(self):
        result = score_requirement_cases(completed(), now=NOW)
        self.assertEqual(result["metrics"]["true_positives"], 2)
        self.assertEqual([result["metrics"][key] for key in ("precision", "recall", "f1")], [1, 1, 1])
        self.assertEqual(result["type_confusion_counts"]["required"]["required"], 1)
        self.assertEqual(result["type_confusion_counts"]["preferred"]["preferred"], 1)
        self.assertEqual(result["category_coverage"]["by_category"]["Data"]["gold_requirements"], 2)
        self.assertNotIn("📊", json.dumps(result))
        self.assertNotIn("SQL required", json.dumps(result))

    def test_exact_matching_counts_type_errors_missing_and_spurious_mentions(self):
        text = "SQL required. Python preferred. Excel optional. Familiarity with a query language."
        gold = [label(text, "SQL", "sql", "required"), label(text, "Python", "python", "required"),
                label(text, "query language", "power_bi", "uncertain")]
        result = score_requirement_cases(completed(text, gold), now=NOW)
        metrics = result["metrics"]
        self.assertEqual((metrics["true_positives"], metrics["false_positives"], metrics["false_negatives"]), (1, 2, 2))
        self.assertAlmostEqual(metrics["precision"], 1 / 3)
        self.assertAlmostEqual(metrics["recall"], 1 / 3)
        self.assertAlmostEqual(metrics["f1"], 1 / 3)
        self.assertEqual(result["type_confusion_counts"]["required"]["preferred"], 1)
        self.assertEqual(len(result["case_results"][0]["missed_requirements"]), 2)
        self.assertEqual(len(result["case_results"][0]["spurious_requirements"]), 2)

    def test_span_boundary_error_is_a_false_positive_and_false_negative(self):
        text = "📊 SQL required."
        gold = label(text, "SQL", "sql", "required")
        gold["end"] += 1
        result = score_requirement_cases(completed(text, [gold]), now=NOW)
        self.assertEqual(result["metrics"]["true_positives"], 0)
        self.assertEqual(result["metrics"]["false_positives"], 1)
        self.assertEqual(result["metrics"]["false_negatives"], 1)

    def test_empty_completed_case_and_one_sided_metrics_stay_mathematically_defined(self):
        result = score_requirement_cases(completed("A fictional role description.", []), now=NOW)
        self.assertEqual(result["completed_cases"], 1)
        self.assertIsNone(result["metrics"]["precision"])
        self.assertIsNone(result["metrics"]["recall"])
        self.assertIsNone(result["metrics"]["f1"])
        result = score_requirement_cases(completed("SQL required.", []), now=NOW)
        self.assertEqual(result["metrics"]["precision"], 0)
        self.assertIsNone(result["metrics"]["recall"])
        self.assertEqual(result["metrics"]["f1"], 0)
        text = "A fictional role description."
        result = score_requirement_cases(completed(text, [label(text, "role", "sql", "uncertain")]), now=NOW)
        self.assertIsNone(result["metrics"]["precision"])
        self.assertEqual(result["metrics"]["recall"], 0)

    def test_pending_working_labels_are_excluded_from_accuracy_and_coverage(self):
        rows = [job(), job("Excel preferred.", "fixture-2", "BI Analyst", "BI Analyst")]
        document = prepare_requirement_cases(rows, now=NOW)
        data = next(case for case in document["cases"] if case["role_name"] == "Data Analyst")
        data["review_status"] = "completed"
        data["expected_requirements"] = [label(data["text"], "SQL", "sql", "required"), label(data["text"], "Python", "python", "preferred")]
        pending = next(case for case in document["cases"] if case["role_name"] == "BI Analyst")
        pending["expected_requirements"] = [label(pending["text"], "Excel", "excel", "required")]
        result = score_requirement_cases(document, now=NOW)
        self.assertEqual(result["metrics"]["true_positives"], 2)
        self.assertEqual(result["completion_fraction"], .5)
        self.assertEqual(result["role_coverage"]["BI Analyst"]["pending_cases"], 1)
        self.assertEqual(result["category_coverage"]["by_category"]["BI"]["gold_requirements"], 0)

    def test_preparation_derives_missing_role_but_rejects_unknown_role(self):
        row = job(); row.pop("role_name")
        self.assertEqual(prepare_requirement_cases([row], now=NOW)["cases"][0]["role_name"], "Data Analyst")
        for role in ["Invented role", [], False]:
            with self.subTest(role=role), self.assertRaises(ValueError): prepare_requirement_cases([job(role=role)], now=NOW)

    def test_schema_future_timestamp_hashes_and_frozen_identities_are_validated(self):
        original = completed()
        changes = [("schema_version", "requirement-gold-v99"), ("created_at", (NOW + timedelta(days=1)).isoformat()),
                   ("taxonomy_version", "unknown-v99"), ("created_at", "2026-10-26T12:00:00")]
        for key, value in changes:
            document = copy.deepcopy(original); document[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError): score_requirement_cases(document, now=NOW)
        for key, value in [("text", "Different description"), ("text_sha256", "0" * 64), ("case_id", "0" * 64),
                           ("title", "Changed title"), ("review_status", []), ("candidate_email", "private")]:
            document = copy.deepcopy(original); document["cases"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): score_requirement_cases(document, now=NOW)

    def test_labels_reject_unknown_skills_types_extra_fields_duplicates_and_bad_spans(self):
        original = completed()
        for changes in [{"skill_id": "invented"}, {"requirement_type": "mandatory"}, {"start": True},
                        {"start": -1}, {"end": 99999}, {"end": 0}, {"start": "2"}, {"source_phrase": "SQL"}]:
            document = copy.deepcopy(original); document["cases"][0]["expected_requirements"][0].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError): score_requirement_cases(document, now=NOW)
        document = copy.deepcopy(original)
        document["cases"][0]["expected_requirements"].append({**document["cases"][0]["expected_requirements"][0], "requirement_type": "preferred"})
        with self.assertRaises(ValueError): score_requirement_cases(document, now=NOW)

    def test_duplicate_sources_text_and_case_records_are_not_independent_cases(self):
        for rows in [[job(), job()], [job(), job(identifier="other")], [job(), job("SQL preferred.")]]:
            with self.subTest(rows=rows), self.assertRaises(ValueError): prepare_requirement_cases(rows, now=NOW)
        document = completed(); document["cases"].append(copy.deepcopy(document["cases"][0]))
        with self.assertRaises(ValueError): score_requirement_cases(document, now=NOW)

    def test_predictions_are_separate_and_cannot_be_scored_as_gold(self):
        document = prepare_requirement_cases([job()], now=NOW)
        before = copy.deepcopy(document)
        aid = requirement_prediction_aid(document, now=NOW)
        self.assertTrue(aid["not_gold"])
        self.assertEqual(len(aid["cases"][0]["predicted_requirements"]), 2)
        self.assertEqual(document, before)
        with self.assertRaises(ValueError): score_requirement_cases(aid, now=NOW)

    def test_size_case_and_annotation_limits_reject_instead_of_truncating(self):
        with self.assertRaises(ValueError): prepare_requirement_cases([job("x" * (MAX_TEXT + 1))], now=NOW)
        with self.assertRaises(ValueError): prepare_requirement_cases([job()] * (MAX_CASES + 1), now=NOW)
        document = completed(); document["cases"][0]["expected_requirements"] *= 101
        with self.assertRaises(ValueError): score_requirement_cases(document, now=NOW)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "large.json"
            with path.open("wb") as file: file.truncate(MAX_BYTES + 1)
            with self.assertRaises(ValueError): _read_json(path)

    def test_private_file_boundaries_reject_symlinks_overwrites_and_malformed_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); source = base / "jobs.json"
            source.write_text(json.dumps([job()]))
            self.assertEqual(len(_read_jobs(source)), 1)
            linked = base / "linked.json"; linked.symlink_to(source)
            with self.assertRaises(ValueError): _read_jobs(linked)
            linked_dir = base / "linked-dir"; linked_dir.symlink_to(base, target_is_directory=True)
            with self.assertRaises(ValueError): _write_new(linked_dir / "output.json", {})
            output = base / "output.json"; _write_new(output, {"first": True})
            with self.assertRaises(ValueError): _write_new(output, {"overwrite": True})
            self.assertEqual(json.loads(output.read_text()), {"first": True})
            source.write_text('{"cases":[],"cases":[]}')
            with self.assertRaises(ValueError): _read_json(source)
            source.write_text('{"bad":NaN}')
            with self.assertRaises(ValueError): _read_json(source)
            csv_path = base / "jobs.csv"; csv_path.write_text("source_job_id,source_job_id\na,b\n")
            with self.assertRaises(ValueError): _read_jobs(csv_path)

    def test_cli_scaffold_and_score_keep_gold_pending_and_refuse_existing_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory); source = base / "jobs.json"; gold = base / "gold.json"; aid = base / "aid.json"; report = base / "report.json"
            source.write_text(json.dumps([job()]))
            with patch("sys.argv", ["evaluate", "prepare", "--input", str(source), "--output", str(gold), "--predictions-output", str(aid)]), patch("career_radar.requirement_evaluation._now", return_value=NOW), contextlib.redirect_stdout(io.StringIO()) as output:
                main()
            self.assertEqual(json.loads(output.getvalue())["gold_labels_created"], 0)
            self.assertEqual(json.loads(gold.read_text())["cases"][0]["expected_requirements"], [])
            with patch("sys.argv", ["evaluate", "score", "--input", str(gold), "--output", str(report)]), patch("career_radar.requirement_evaluation._now", return_value=NOW), contextlib.redirect_stdout(io.StringIO()):
                main()
            result = json.loads(report.read_text())
            self.assertEqual(result["completed_cases"], 0)
            self.assertIsNone(result["metrics"]["precision"])
            with patch("sys.argv", ["evaluate", "prepare", "--input", str(source), "--output", str(gold)]), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                main()
            self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
