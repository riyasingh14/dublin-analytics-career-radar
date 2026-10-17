"""Transparent market metrics and proof-of-work recommendations."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def load_proof_recommendations(taxonomy_path: Path) -> dict[str, str]:
    return {
        row["skill_id"]: row["proof_of_work_recommendation"]
        for row in read_csv(taxonomy_path)
    }


def build_market_summary(
    jobs: list[dict[str, str]], evidence: list[dict[str, str]]
) -> dict[str, object]:
    """Calculate sample-based counts without implying full market coverage."""
    valid_urls = {job["canonical_url"] for job in jobs}
    role_by_url = {job["canonical_url"]: job["role_name"] for job in jobs}
    skill_name_by_id: dict[str, str] = {}
    skill_jobs: dict[str, set[str]] = defaultdict(set)
    role_skill_jobs: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))

    for row in evidence:
        url = row["canonical_url"]
        if url not in valid_urls:
            continue
        skill_id = row["skill_id"]
        skill_name_by_id[skill_id] = row["skill_name"]
        skill_jobs[skill_id].add(url)
        role_skill_jobs[role_by_url[url]][skill_id].add(url)

    total_jobs = len(jobs)
    role_counts = Counter(job["role_name"] for job in jobs)
    work_pattern_counts = Counter(job["work_pattern"] for job in jobs)
    top_skills = [
        {
            "skill_id": skill_id,
            "skill_name": skill_name_by_id[skill_id],
            "job_count": len(urls),
            "sample_share_pct": round(100 * len(urls) / total_jobs, 1) if total_jobs else 0.0,
        }
        for skill_id, urls in skill_jobs.items()
    ]
    top_skills.sort(key=lambda row: (-int(row["job_count"]), str(row["skill_name"])))

    role_skills: dict[str, list[dict[str, object]]] = {}
    for role_name, skills in role_skill_jobs.items():
        denominator = role_counts[role_name]
        rows = [
            {
                "skill_id": skill_id,
                "skill_name": skill_name_by_id[skill_id],
                "job_count": len(urls),
                "role_share_pct": round(100 * len(urls) / denominator, 1) if denominator else 0.0,
            }
            for skill_id, urls in skills.items()
        ]
        role_skills[role_name] = sorted(
            rows, key=lambda row: (-int(row["job_count"]), str(row["skill_name"]))
        )

    return {
        "sample_size": total_jobs,
        "role_counts": dict(sorted(role_counts.items())),
        "work_pattern_counts": dict(sorted(work_pattern_counts.items())),
        "top_skills": top_skills,
        "role_skills": role_skills,
    }


def recommend_proof_of_work(
    summary: dict[str, object],
    target_role: str,
    current_skill_ids: set[str],
    proof_recommendations: dict[str, str],
    limit: int = 5,
) -> list[dict[str, object]]:
    """Rank missing skills using only demand within the selected role sample."""
    role_skills = summary.get("role_skills", {})
    if not isinstance(role_skills, dict):
        return []
    rows = role_skills.get(target_role, [])
    if not isinstance(rows, list):
        return []
    recommendations: list[dict[str, object]] = []
    for row in rows:
        skill_id = str(row["skill_id"])
        if skill_id in current_skill_ids or skill_id not in proof_recommendations:
            continue
        recommendations.append(
            {
                **row,
                "reason": (
                    f"Requested by {row['job_count']} of the {target_role} postings "
                    f"in this sample ({row['role_share_pct']}%)."
                ),
                "proof_of_work": proof_recommendations[skill_id],
            }
        )
        if len(recommendations) == limit:
            break
    return recommendations
