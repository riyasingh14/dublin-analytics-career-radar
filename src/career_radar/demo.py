"""Explicit, deterministic fixtures for demonstrating the graph without private data."""
from career_radar.build_snapshot import build_snapshot_payload
from career_radar.normalise import Skill, extract_skills


def constellation_demo(taxonomy: list[Skill]) -> dict:
    templates = (
        "SQL, Python, data quality and Git",
        "SQL, Excel, Power BI and communication",
        "Python, statistics, machine learning and Git",
        "SQL, Python, Excel and communication",
        "SQL, Power BI, data modelling and data quality",
        "Python, SQL, APIs and Git",
    )
    jobs, evidence = [], []
    for index in range(30):
        description = "Synthetic example only. Skills mentioned: " + templates[index % len(templates)] + "."
        url = f"fixture://synthetic-posting/{index}"
        job = {
            "source_job_id": f"synthetic-{index}", "canonical_url": url,
            "title": "Synthetic Data Analyst example", "role_name": "Data Analyst",
            "employer_name": f"Fictional employer {index % 5 + 1}",
            "location_text": "Dublin, Ireland" if index < 20 else "Cork, Ireland",
            "work_pattern": "unknown", "description_text": description,
            "source_name": "Generated demonstration fixture — not observed vacancies",
        }
        jobs.append(job)
        evidence.extend({**row, "canonical_url": url} for row in extract_skills(description, taxonomy))
    return build_snapshot_payload(jobs, evidence, "Synthetic Skill Constellation demonstration", "fixture")
