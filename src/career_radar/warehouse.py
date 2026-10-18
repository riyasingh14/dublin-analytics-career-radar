"""Transactional PostgreSQL loader and SQL/Python reconciliation for saved runs.

Optional dependency: requirements-sql.txt. The public app never imports psycopg or
connects to this warehouse. Credentials come from a named environment variable.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
import os
from pathlib import Path

from career_radar.constellation import build_constellation
from career_radar.mobility import Scenario, derive_transitions, generate_histories, metadata, salary_metrics
from career_radar.normalise import geography_group, load_taxonomy
from career_radar.requirements_model import extract_requirements

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ("jobs.csv", "evidence.csv", "review_queue.csv", "quality.json", "snapshot.json")


def verified_run(run_dir: Path) -> tuple[dict, list[dict], list[dict], dict]:
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("publish_allowed") is not False or manifest.get("data_status") not in {"fixture", "unreviewed"}:
        raise ValueError("Only private fixture/unreviewed refresh runs are supported")
    for name in ARTIFACTS:
        digest = hashlib.sha256((run_dir / name).read_bytes()).hexdigest()
        if digest != manifest.get("artifact_sha256", {}).get(name):
            raise ValueError("Refresh artifact integrity check failed")
    def rows(name):
        with (run_dir / name).open(newline="", encoding="utf-8") as file:
            return list(csv.DictReader(file))
    jobs, evidence = rows("jobs.csv"), rows("evidence.csv")
    snapshot = json.loads((run_dir / "snapshot.json").read_text(encoding="utf-8"))
    if len(jobs) != manifest["unique_job_count"] or len(evidence) != manifest["skill_evidence_count"]:
        raise ValueError("Refresh manifest counts do not reconcile")
    if snapshot["metadata"]["refresh_run_id"] != manifest["run_id"]:
        raise ValueError("Refresh snapshot identity does not reconcile")
    return manifest, jobs, evidence, snapshot


def _close(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return math.isclose(float(a), float(b), abs_tol=1e-8, rel_tol=1e-8)


def load_and_reconcile(connection, run_dir: Path, taxonomy_path: Path,
                       scenario: Scenario = Scenario(people=100)) -> dict:
    """Load once, verify on every call, commit only when every metric agrees.

    Snapshot and synthetic-scenario identities are independent; there is no join
    between job postings and salaries. The caller supplies an open psycopg3
    connection. All operations happen inside one transaction/savepoint.
    """
    manifest, jobs, evidence, snapshot = verified_run(run_dir)
    taxonomy = load_taxonomy(taxonomy_path)
    taxonomy_hash = hashlib.sha256(taxonomy_path.read_bytes()).hexdigest()
    if taxonomy_hash != manifest["taxonomy_sha256"]:
        raise ValueError("Taxonomy differs from the extraction run")
    run_id = manifest["run_id"]
    requirements = [(job["canonical_url"], item) for job in jobs
                    for item in extract_requirements(job["description_text"], taxonomy)]
    scenario_metadata = metadata(scenario)
    scenario_id = hashlib.sha256(json.dumps(scenario_metadata, sort_keys=True).encode()).hexdigest()[:24]
    spells = generate_histories(scenario)
    transitions = derive_transitions(spells)
    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute((ROOT / "sql/30_operations_schema.sql").read_text())
            cursor.execute("SELECT input_sha256, manifest FROM career_radar_ops.analysis_run WHERE run_id=%s", (run_id,))
            existing = cursor.fetchone()
            # Local rebuilds can change generated-at timestamps and derived-file
            # byte hashes without changing this input/taxonomy/policy/week identity.
            identity_fields = ("run_id", "source_name", "input_sha256", "taxonomy_sha256", "data_status",
                               "collection_week_dublin", "pipeline_version", "source_row_count",
                               "unique_job_count", "duplicates_removed", "skill_evidence_count",
                               "extraction_version", "role_classification_version")
            if existing and (existing[0] != manifest["input_sha256"] or any(
                    existing[1].get(key) != manifest.get(key) for key in identity_fields)):
                raise ValueError("Immutable warehouse run identity conflict")
            inserted = existing is None
            if inserted:
                cursor.execute("""INSERT INTO career_radar_ops.analysis_run
                    (run_id, source_name, input_sha256, data_status, collection_timestamp, manifest)
                    VALUES (%s,%s,%s,%s,%s,%s::jsonb)""", (run_id, manifest["source_name"],
                    manifest["input_sha256"], manifest["data_status"], manifest["collection_timestamp"], json.dumps(manifest)))
                cursor.executemany("""INSERT INTO career_radar_ops.posting
                    (run_id, canonical_url, source_job_id, title, employer_name, location_text, geography,
                     role_name, work_pattern, description_text, deduplication_key)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", [
                        (run_id, job["canonical_url"], job["source_job_id"], job["title"], job["employer_name"],
                         job["location_text"], geography_group(job["location_text"]), job["role_name"],
                         job["work_pattern"], job["description_text"], job["deduplication_key"]) for job in jobs])
                # Multiple same-phrase extractor records still count only once per posting/skill.
                cursor.executemany("""INSERT INTO career_radar_ops.skill_evidence
                    (run_id, canonical_url, skill_id, source_phrase, extraction_version)
                    VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""", [
                        (run_id, row["canonical_url"], row["skill_id"], row["source_phrase"], row["extraction_version"])
                        for row in evidence])
                cursor.executemany("""INSERT INTO career_radar_ops.requirement
                    (run_id, canonical_url, requirement_id, skill_id, requirement_type, source_phrase,
                     start_offset, end_offset, extraction_version) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""", [
                        (run_id, url, row["requirement_id"], row["skill_id"], row["requirement_type"],
                         row["source_phrase"], row["start"], row["end"], row["extraction_version"])
                        for url, row in requirements])
            cursor.execute("SELECT count(*) FROM career_radar_ops.posting WHERE run_id=%s", (run_id,))
            sql_postings = cursor.fetchone()[0]
            if sql_postings != len(jobs):
                raise ValueError("Posting-grain reconciliation failed")
            graph = build_constellation(snapshot, min_pair_count=1, min_sample_size=1)
            cursor.execute("""SELECT skill_a, skill_b, joint_count, skill_a_count, skill_b_count,
                sample_size, support, jaccard, lift FROM career_radar_ops.pair_metrics
                WHERE run_id=%s ORDER BY skill_a, skill_b""", (run_id,))
            sql_pairs = cursor.fetchall()
            python_pairs = {(row["skill_a"], row["skill_b"]): row for row in graph["pairs"]}
            if len(sql_pairs) != len(python_pairs):
                raise ValueError("Skill-pair grain reconciliation failed")
            for a, b, joint, count_a, count_b, sample, support, jaccard, lift in sql_pairs:
                expected = python_pairs[a, b]
                if (joint, count_a, count_b, sample) != (expected["pair_count"], expected["count_a"], expected["count_b"], graph["sample_size"]):
                    raise ValueError("Skill-pair denominator reconciliation failed")
                if not all(_close(value, expected[key]) for value, key in ((support,"support"), (jaccard,"jaccard"), (lift,"lift"))):
                    raise ValueError("Skill-pair metric reconciliation failed")
            cursor.execute("""SELECT requirement_type, count(*) FROM career_radar_ops.requirement
                WHERE run_id=%s GROUP BY requirement_type""", (run_id,))
            sql_requirements = dict(cursor.fetchall())
            if sql_requirements != dict(Counter(row["requirement_type"] for _, row in requirements)):
                raise ValueError("Requirement-category reconciliation failed")
            cursor.execute("""SELECT count(*) FROM career_radar_ops.requirement r JOIN career_radar_ops.posting p
                USING (run_id, canonical_url) WHERE r.run_id=%s AND
                substring(p.description_text FROM r.start_offset + 1 FOR r.end_offset - r.start_offset) <> r.source_phrase""", (run_id,))
            if cursor.fetchone()[0]:
                raise ValueError("Requirement-source span reconciliation failed")
            cursor.execute("SELECT metadata FROM career_radar_ops.synthetic_scenario WHERE scenario_id=%s", (scenario_id,))
            existing_scenario = cursor.fetchone()
            if existing_scenario and existing_scenario[0] != scenario_metadata:
                raise ValueError("Synthetic scenario identity conflict")
            if not existing_scenario:
                cursor.execute("INSERT INTO career_radar_ops.synthetic_scenario VALUES (%s,%s::jsonb)",
                               (scenario_id, json.dumps(scenario_metadata)))
                fields = ("person_id", "spell_id", "start_date", "end_date", "occupation", "employer_id", "industry",
                          "seniority", "experience_years", "geography", "salary_eur_annual_fte", "currency", "salary_basis",
                          "fte", "data_label", "generator_version")
                columns = ",".join(fields)
                placeholders = ",".join(["%s"] * (len(fields) + 1))
                cursor.executemany(f"INSERT INTO career_radar_ops.synthetic_spell (scenario_id,{columns}) VALUES ({placeholders})",
                                   [(scenario_id, *(row[key] for key in fields)) for row in spells])
            cursor.execute("""SELECT count(*) FROM career_radar_ops.synthetic_spell a
                JOIN career_radar_ops.synthetic_spell b ON a.scenario_id=b.scenario_id AND a.person_id=b.person_id
                AND a.spell_id < b.spell_id WHERE a.scenario_id=%s
                AND a.start_date < b.end_date AND b.start_date < a.end_date""", (scenario_id,))
            if cursor.fetchone()[0]:
                raise ValueError("Synthetic spell overlap check failed")
            cursor.execute("""SELECT transition_id, origin, destination, geography, category,
                valid_pair, before_salary, after_salary, individual_pct_change
                FROM career_radar_ops.synthetic_transition WHERE scenario_id=%s""", (scenario_id,))
            sql_transitions = cursor.fetchall()
            expected_transitions = {row["transition_id"]: row for row in transitions}
            if len(sql_transitions) != len(expected_transitions):
                raise ValueError("Synthetic transition-grain reconciliation failed")
            for identity, origin, destination, geography, category, valid, before, after, change in sql_transitions:
                expected = expected_transitions[identity]
                if (origin, destination, geography, category, valid) != tuple(expected[key] for key in
                        ("origin", "destination", "geography", "category", "valid_pair")):
                    raise ValueError("Synthetic transition-definition reconciliation failed")
                if not all(_close(value, expected[key]) for value, key in
                           ((before,"before_salary"), (after,"after_salary"), (change,"individual_pct_change"))):
                    raise ValueError("Synthetic salary-pair reconciliation failed")
            by_category = defaultdict(list)
            for transition in transitions:
                by_category[transition["category"]].append(transition)
            cursor.execute("""SELECT category, events, people, valid_pairs, excluded_pairs,
                median_individual_pct_change, change_between_cohort_medians_pct, share_decreased
                FROM career_radar_ops.synthetic_cohort_metrics WHERE scenario_id=%s""", (scenario_id,))
            sql_cohorts = cursor.fetchall()
            if len(sql_cohorts) != len(by_category):
                raise ValueError("Synthetic cohort-grain reconciliation failed")
            for category, events, people, valid_pairs, excluded_pairs, individual, cohort, decreased in sql_cohorts:
                expected = salary_metrics(by_category[category])
                if (events, people, valid_pairs, excluded_pairs) != tuple(expected[key] for key in
                        ("events", "people", "valid_pairs", "excluded_pairs")):
                    raise ValueError("Synthetic cohort-denominator reconciliation failed")
                for value, key in ((individual,"median_individual_pct_change"),
                                   (cohort,"change_between_cohort_medians_pct"), (decreased,"share_decreased")):
                    target = expected[key] if expected["comparison_available"] else None
                    if not _close(value, target):
                        raise ValueError("Synthetic sparse-cohort/metric reconciliation failed")
            cursor.execute("SELECT version()")
            database_version = cursor.fetchone()[0].split(" on ")[0]
    return {"run_id": run_id, "outcome": "inserted" if inserted else "already_loaded",
            "database": database_version, "posting_count": len(jobs), "skill_pairs_reconciled": len(sql_pairs),
            "requirements_reconciled": len(requirements), "requirement_categories": sql_requirements,
            "synthetic_scenario_id": scenario_id, "synthetic_spell_count": len(spells),
            "synthetic_transitions_reconciled": len(sql_transitions), "synthetic_cohorts_reconciled": len(sql_cohorts),
            "reconciliation_passed": True, "publish_allowed": False, "public_demo_changed": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--taxonomy", type=Path, default=Path("data/reference/skills.csv"))
    parser.add_argument("--dsn-env", default="CAREER_RADAR_DATABASE_URL", help="Environment variable name; never pass secrets as arguments")
    parser.add_argument("--people", type=int, default=100)
    parser.add_argument("--years", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        import psycopg
        dsn = os.environ.get(args.dsn_env)
        if not dsn:
            parser.exit(1, "Named database connection environment variable is absent.\n")
        with psycopg.connect(dsn, connect_timeout=10) as connection:
            result = load_and_reconcile(connection, args.run_dir, args.taxonomy,
                                        Scenario(seed=args.seed, people=args.people, years=args.years))
    except ImportError:
        parser.exit(1, "Install optional requirements-sql.txt for PostgreSQL integration.\n")
    except Exception:
        # Database exceptions can contain DSNs, hostnames or source snippets.
        parser.exit(1, "Warehouse load/reconciliation failed; transaction rolled back. Check local configuration and verified artefacts.\n")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
