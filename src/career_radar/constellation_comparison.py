"""Shared-axis role comparisons; denominators include jobs with no skill evidence."""
from career_radar.constellation import build_constellation


def build_role_comparison(snapshot, taxonomy, *, geography=None):
    snapshot = {**snapshot, "postings": [{**posting, "role_name": posting.get("role_name") or "Unclassified"}
                                       for posting in snapshot["postings"]]}
    roles = sorted({p.get("role_name") or "Unclassified" for p in snapshot["postings"]})
    results = {role: build_constellation(snapshot, role=role, geography=geography) for role in roles}
    labels = {skill.skill_id: skill for skill in taxonomy}
    ids = sorted({node["skill_id"] for result in results.values() for node in result["nodes"]})
    counts = {role: {node["skill_id"]: node["job_count"] for node in result["nodes"]}
              for role, result in results.items()}
    return {
        "data_label": snapshot.get("metadata", {}).get("dataset_label", "Role comparison sample"),
        "data_status": snapshot.get("metadata", {}).get("data_status", "unreviewed"),
        "geography": geography or "All locations",
        "roles": [{"role": role, "sample_size": result["sample_size"],
                   "jobs_with_skills": result["jobs_with_skills"]} for role, result in results.items()],
        "skills": [{"skill_id": skill, "skill_name": labels[skill].skill_name if skill in labels else skill,
                    "category": labels[skill].category if skill in labels else "Uncategorised",
                    "values": [{"role": role, "job_count": counts[role].get(skill, 0),
                                "sample_size": result["sample_size"],
                                "share": counts[role].get(skill, 0) / result["sample_size"] if result["sample_size"] else None}
                               for role, result in results.items()]} for skill in ids],
    }
