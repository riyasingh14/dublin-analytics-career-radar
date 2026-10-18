"""Separate fictional role-comparison sample, never merged with the graph fixture."""
from career_radar.build_snapshot import build_snapshot_payload
from career_radar.demo import constellation_demo
from career_radar.normalise import extract_skills


def comparison_demo(taxonomy):
    original = constellation_demo(taxonomy)
    jobs, evidence = list(original["postings"]), list(original["evidence"])
    templates = {
        "BI Analyst": ("SQL, Power BI, Excel and data modelling", "Power BI, communication and data quality", "SQL, Excel and stakeholder management"),
        "Product Analyst": ("SQL, statistics and experimentation", "Python, SQL and communication", "SQL, product analytics and statistics"),
    }
    for role, phrases in templates.items():
        slug = role.lower().replace(" ", "-")
        for index in range(30):
            url = f"fixture://role-comparison/{slug}/{index}"
            # Deliberate no-skill records expose why N differs from evidence coverage.
            description = "Synthetic example only. " + ("No controlled skill named." if index == 29 else phrases[index % 3] + ".")
            jobs.append({"canonical_url": url, "source_job_id": f"comparison-{slug}-{index}",
                         "work_pattern": "unknown",
                         "role_name": role, "title": f"Synthetic {role} example", "description_text": description,
                         "employer_name": f"Fictional comparison employer {index % 5 + 1}",
                         "location_text": "Dublin, Ireland" if index < 20 else "Cork, Ireland",
                         "source_name": "Generated demonstration fixture — not observed vacancies"})
            evidence.extend({**row, "canonical_url": url} for row in extract_skills(description, taxonomy))
    return build_snapshot_payload(jobs, evidence, "Separate fictional role-comparison demonstration (90 postings)", "fixture")
