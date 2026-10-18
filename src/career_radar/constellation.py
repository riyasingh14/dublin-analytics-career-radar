"""Auditable skill co-mentions in a filtered sample of unique job postings.

Snapshots without posting records must be rebuilt: evidence alone cannot recover
postings with no skills and therefore cannot supply valid filtered denominators.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations
from typing import Any
from urllib.parse import urlsplit

from career_radar.normalise import geography_group


def safe_source_url(value: str) -> str | None:
    """Only expose ordinary HTTPS/HTTP links, never script or credential URLs."""
    try:
        parsed = urlsplit(value)
        if parsed.scheme in {"https", "http"} and parsed.hostname and not parsed.username and not parsed.password:
            return value
    except ValueError:
        pass
    return None


def association_metrics(n_a: int, n_b: int, n_ab: int, sample_size: int) -> dict[str, float]:
    """Unrounded shares; zero denominators produce zero (no evidence)."""
    if min(n_a, n_b, n_ab, sample_size) < 0 or n_ab > min(n_a, n_b) or max(n_a, n_b) > sample_size:
        raise ValueError("Counts must be nonnegative and consistent with the sample")
    union = n_a + n_b - n_ab
    if union > sample_size:
        raise ValueError("The skill union cannot exceed the sample")
    return {
        "support": n_ab / sample_size if sample_size else 0.0,
        "jaccard": n_ab / union if union else 0.0,
        "lift": n_ab * sample_size / (n_a * n_b) if n_a and n_b else 0.0,
    }


def build_constellation(
    snapshot: dict[str, Any],
    *,
    role: str | None = None,
    geography: str | None = None,
    min_pair_count: int = 5,
    min_sample_size: int = 20,
) -> dict[str, Any]:
    """Count skills once per canonical URL; omit orphan evidence.

    Geography accepts the stored groups or 'Ireland' (all explicitly Irish
    location groups, including country-only listings). All evidence rows remain available for source phrase inspection.
    Thresholds govern display eligibility only; full pair counts are retained.
    """
    if "postings" not in snapshot:
        raise ValueError("Rebuild this snapshot with posting records to include jobs without extracted skills.")
    if min_pair_count < 1 or min_sample_size < 1:
        raise ValueError("Display thresholds must be at least one")
    postings = {}
    for posting in snapshot["postings"]:
        url = posting.get("canonical_url", "")
        if url:
            postings.setdefault(url, dict(posting))
    for posting in postings.values():
        posting["geography"] = posting.get("geography") or geography_group(posting.get("location_text", ""))
    selected = {
        url: posting for url, posting in postings.items()
        if (role is None or posting.get("role_name") == role)
        and (geography is None or posting["geography"] == geography or
             (geography == "Ireland" and posting["geography"] in {"Dublin", "Rest of Ireland", "Ireland — location unspecified"}))
    }
    skills_by_job: dict[str, set[str]] = defaultdict(set)
    skill_labels = {}
    evidence = []
    for item in snapshot.get("evidence", []):
        url, skill_id = item.get("canonical_url"), item.get("skill_id")
        if url not in selected or not skill_id:
            continue
        skills_by_job[url].add(skill_id)
        skill_labels[skill_id] = item.get("skill_name") or skill_id
        # Posting metadata is authoritative for filtering and source identity.
        evidence.append({**item, **selected[url], "skill_id": skill_id,
                         "skill_name": item.get("skill_name") or skill_id})
    n = len(selected)
    counts = Counter(skill for skills in skills_by_job.values() for skill in skills)
    pair_counts = Counter(pair for skills in skills_by_job.values() for pair in combinations(sorted(skills), 2))
    nodes = [{"skill_id": skill, "skill_name": skill_labels[skill], "job_count": count,
              "sample_share": count / n if n else 0.0}
             for skill, count in sorted(counts.items(), key=lambda row: (-row[1], row[0]))]
    pairs = [{"skill_a": a, "skill_b": b, "count_a": counts[a], "count_b": counts[b],
              "pair_count": count, **association_metrics(counts[a], counts[b], count, n)}
             for (a, b), count in sorted(pair_counts.items(), key=lambda row: (-row[1], row[0]))]
    return {
        "sample_size": n, "postings": list(selected.values()), "nodes": nodes, "pairs": pairs,
        "evidence": evidence, "jobs_with_skills": len(skills_by_job),
        "network_eligible": n >= min_sample_size,
        "eligible_pairs": [pair for pair in pairs if n >= min_sample_size and pair["pair_count"] >= min_pair_count],
        "min_pair_count": min_pair_count, "min_sample_size": min_sample_size,
    }


def pair_evidence(result: dict[str, Any], skill_a: str, skill_b: str) -> list[dict[str, Any]]:
    """Return one source entry per posting supporting both skills, with phrases."""
    if skill_a == skill_b:
        return []
    by_url: dict[str, dict[str, Any]] = {}
    for row in result["evidence"]:
        if row["skill_id"] not in {skill_a, skill_b}:
            continue
        url = row["canonical_url"]
        entry = by_url.setdefault(url, {"posting": {key: row.get(key, "") for key in (
            "canonical_url", "title", "employer_name", "location_text", "posted_at", "source_name", "geography")},
            "skills": defaultdict(list)})
        phrase = {key: row.get(key, "") for key in ("source_phrase", "extraction_method", "extraction_version")}
        if phrase not in entry["skills"][row["skill_id"]]:
            entry["skills"][row["skill_id"]].append(phrase)
    return [entry for entry in by_url.values() if {skill_a, skill_b} <= entry["skills"].keys()]
