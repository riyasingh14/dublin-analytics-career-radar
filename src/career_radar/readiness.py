"""Transparent, session-only evidence alignment; no hiring-outcome prediction.

The index weights are product assumptions, not learned estimates. Unknown and
unconfirmed requirements must never silently become demonstrated skills.
"""

from __future__ import annotations

from copy import deepcopy

READINESS_VERSION = "readiness-v1"
WEIGHTS = {"required": 3, "preferred": 1}
STATUS_VALUES = {"supported": 1.0, "partial": 0.5, "missing": 0.0}
MIN_COVERAGE = 0.8


def assess_readiness(requirements: list[dict], evidence: dict[str, dict] | None = None) -> dict:
    """Assess evidence keyed by requirement ID; never mutate either input.

    Supported/partial evidence needs a nonempty concrete evidence note. Without
    one it remains unknown. Multiple source occurrences may be shown, but each
    confirmed skill receives one index weight (required takes precedence).
    """
    evidence = evidence or {}
    rows, seen_ids = [], set()
    for requirement in requirements:
        row = deepcopy(requirement)
        identifier = row["requirement_id"]
        if identifier in seen_ids:
            raise ValueError("Requirement IDs must be unique")
        seen_ids.add(identifier)
        item = evidence.get(identifier, {})
        status = item.get("status", "unknown")
        if status not in {*STATUS_VALUES, "unknown"}:
            raise ValueError(f"Unsupported evidence status: {status}")
        note = str(item.get("note", "")).strip()
        row.update(status=status, evidence_note=note, evidence_provenance="self-reported", issue=None)
        if status in {"supported", "partial"} and not note:
            row.update(status="unknown", issue="Add a concrete project, coursework or experience note.")
        row["weight"] = WEIGHTS.get(row.get("requirement_type"), 0)
        rows.append(row)

    # An advert repeating SQL must not outweigh all other skills. Required
    # evidence wins over preferred, and repeated contexts use conservative status.
    skills: dict[str, list[dict]] = {}
    for row in rows:
        if row["weight"]:
            skills.setdefault(row["skill_id"], []).append(row)
    total_weight = assessed_weight = earned_weight = 0.0
    for contexts in skills.values():
        weight = max(row["weight"] for row in contexts)
        relevant = [row for row in contexts if row["weight"] == weight]
        total_weight += weight
        # Every occurrence at the strongest requirement level must be assessed.
        if any(row["status"] == "unknown" for row in relevant):
            continue
        assessed_weight += weight
        earned_weight += weight * min(STATUS_VALUES[row["status"]] for row in relevant)
    coverage = assessed_weight / total_weight if total_weight else None
    alignment = (
        100 * earned_weight / assessed_weight
        if assessed_weight and coverage is not None and coverage >= MIN_COVERAGE else None
    )
    return {
        "version": READINESS_VERSION,
        "label": "Self-reported evidence alignment",
        "rows": rows,
        "confirmed_skill_count": len(skills),
        "total_weight": total_weight,
        "assessed_weight": assessed_weight,
        "unassessed_weight": total_weight - assessed_weight,
        "earned_weight": earned_weight,
        "coverage_pct": None if coverage is None else coverage * 100,
        "alignment_pct": alignment,
        "excluded_requirements": [row for row in rows if not row["weight"]],
        "eligibility_status": "Not assessed — manually check the original listing; unknown is not failure.",
        "formula": "100 × earned weight / assessed weight; required=3, preferred=1; supported=1, partial=0.5, missing=0; unknown excluded. Repeated skills counted once at strongest requirement level.",
        "limitation": "Design assumptions, not a validated prediction. Index hidden below 80% assessed-weight coverage.",
    }


def hypothetical_readiness(requirements: list[dict], evidence: dict[str, dict], requirement_id: str, note: str) -> dict:
    """A separate, labelled scenario replacing one confirmed gap's evidence."""
    baseline = assess_readiness(requirements, evidence)
    chosen = next((row for row in baseline["rows"] if row["requirement_id"] == requirement_id), None)
    if not chosen or not chosen["weight"] or chosen["status"] not in {"missing", "partial", "unknown"}:
        raise ValueError("Choose one confirmed missing, partial or unknown requirement")
    if not note.strip():
        raise ValueError("Describe the hypothetical evidence")
    scenario_evidence = deepcopy(evidence)
    scenario_evidence[requirement_id] = {"status": "supported", "note": note.strip()}
    scenario = assess_readiness(requirements, scenario_evidence)
    scenario["label"] = "Hypothetical evidence alignment — not completed or verified"
    for row in scenario["rows"]:
        if row["requirement_id"] == requirement_id:
            row["evidence_provenance"] = "hypothetical"
    return scenario


def export_analysis(assessment: dict) -> dict:
    """Minimal report excludes free-text candidate notes and raw advert text.

    Keep notes inspectable in-session; excluding them from this export avoids
    accidentally including contact details embedded in user-provided evidence.
    """
    fields = ("version", "label", "confirmed_skill_count", "total_weight", "assessed_weight", "unassessed_weight", "earned_weight", "coverage_pct", "alignment_pct", "eligibility_status", "formula", "limitation")
    report = {key: assessment[key] for key in fields}
    report["requirements"] = [
        {key: row.get(key) for key in ("skill_id", "skill_name", "requirement_type", "extracted_requirement_type", "classification_provenance", "classification_corrected", "status", "weight", "evidence_provenance")}
        for row in assessment["rows"]
    ]
    report["privacy"] = "Candidate notes and original job text omitted; no identity or contact fields collected."
    return report
