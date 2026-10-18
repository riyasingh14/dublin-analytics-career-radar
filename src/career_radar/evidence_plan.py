"""Authored evidence-building briefs; never a prediction or proficiency check."""
from __future__ import annotations

PLAN_VERSION = "evidence-plan-v1"
PRIORITY_METHOD = (
    "Required skills before preferred skills. Within each level, clarify unknown "
    "evidence first, then address missing and partial evidence. Ties use skill ID. "
    "Each skill counts once at its strongest confirmed requirement level. "
    "This is a planning heuristic, not market demand or estimated hiring benefit."
)

SKILL_CHECKS = {
    "sql": [
        "Document table grain and joins; reconcile row counts before and after joins.",
        "Include a CTE and window calculation with a hand-checked expected result.",
        "Test nulls, duplicate keys and a boundary case; explain their business impact.",
    ],
    "python": [
        "Run the workflow from a clean environment using documented dependencies.",
        "Test a key transformation with missing, duplicate and invalid inputs.",
        "Reconcile output totals to input data and document assumptions.",
    ],
    "excel": [
        "Keep raw input separate from transformations and presentation.",
        "Reconcile pivot/KPI totals and test filters against a hand-calculated case.",
        "Document refresh steps, validation rules and a decision supported by the workbook.",
    ],
    "power_bi": [
        "Document the model grain, relationships and KPI definitions.",
        "Reconcile one DAX measure to a hand-calculated filtered example.",
        "Demonstrate filter behaviour and explain an actionable finding with limitations.",
    ],
}
GENERIC_CHECKS = [
    "Define the task, expected result and how success will be checked.",
    "Demonstrate the artefact on a normal case and a failure or boundary case.",
    "Explain the business decision, trade-offs and limitations in a short readout.",
]


def build_evidence_plan(assessment: dict, recommendations: dict[str, str]) -> dict:
    """Use assessed skill groups; never embed evidence notes or advert text.

    Unknown is an information gap, not a skill deficit. Repeated requirements
    inherit the same conservative aggregation as the index. All briefs are
    authored templates and remain proposals until the user builds/reviews them.
    """
    order = {"unknown": 0, "missing": 1, "partial": 2}
    skills = sorted(
        (row for row in assessment["skill_summary"] if row["status"] in order),
        key=lambda row: (-row["weight"], order[row["status"]], row["skill_id"]),
    )
    actions = []
    for rank, skill in enumerate(skills, 1):
        unknown = skill["status"] == "unknown"
        brief = recommendations.get(skill["skill_id"],
            f"Create a reproducible {skill['skill_name']} artefact answering a defined business question.")
        actions.append({
            **skill, "requirement_ids": list(skill["requirement_ids"]), "rank": rank,
            "kind": "clarify_evidence" if unknown else "build_evidence",
            "title": (f"Review your {skill['skill_name']} evidence" if unknown
                      else f"Build evidence for {skill['skill_name']}"),
            "reason": (
                "This confirmed requirement has unassessed evidence. Review what you can already show before deciding to build something new."
                if unknown else
                f"This {skill['requirement_type']} skill has {skill['status']} self-reported evidence at its strongest requirement level."
            ),
            "project_brief": None if unknown else brief,
            "deliverables": [] if unknown else [
                "A short business brief: stakeholder, decision question, input data and success criteria.",
                "A reproducible artefact with a README, permitted or synthetic inputs and documented assumptions.",
                "Validation results and an executive readout connecting findings to a decision and limitations.",
            ],
            "completion_checks": ([
                "Review existing coursework, projects or experience against every listed source context.",
                "Record a concrete evidence note, or explicitly mark the evidence missing or partial.",
                "Reassess before choosing a new project; unknown is not a confirmed weakness.",
            ] if unknown else list(SKILL_CHECKS.get(skill["skill_id"], GENERIC_CHECKS))),
        })
    return {
        "version": PLAN_VERSION, "label": "Proposed evidence actions — not completed or verified",
        "priority_method": PRIORITY_METHOD, "actions": actions,
        "limitation": "Authored project templates do not verify proficiency, satisfy mandatory credentials or promise interviews. No paid services or external model are used.",
    }
