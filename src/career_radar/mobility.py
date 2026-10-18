"""Deterministic, in-memory career scenarios; never observed salary estimates."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import math
import random
from statistics import median, quantiles

VERSION = "mobility-v1"
LABEL = "Synthetic scenario — not observed labour-market outcomes"
OCCUPATIONS = (
    "Data Analyst", "Business Analyst", "Software Engineer", "Data Engineer", "Product Analyst",
    "Operations Coordinator", "Finance Associate", "Customer Support Specialist",
)
INDUSTRIES = ("Technology", "Financial services", "Healthcare", "Retail")
LEVELS = ("Junior", "Mid", "Senior", "Lead")
MIN_PAIRS = 20


@dataclass(frozen=True)
class Scenario:
    seed: int = 42
    people: int = 500
    years: int = 5
    start_year: int = 2021
    employer_change_pct: float = 4.0
    promotion_pct: float = 8.0
    occupation_change_pct: float = 2.0

    def __post_init__(self):
        if not 1 <= self.people <= 5000 or not 2 <= self.years <= 10:
            raise ValueError("Use 1–5000 people and 2–10 years.")
        if not 1900 <= self.start_year <= 2080:
            raise ValueError("Start year must be between 1900 and 2080.")
        if any(not math.isfinite(v) or not -30 <= v <= 30 for v in (
            self.employer_change_pct, self.promotion_pct, self.occupation_change_pct
        )):
            raise ValueError("Assumed changes must be finite percentages between -30 and 30.")


def metadata(scenario: Scenario) -> dict:
    return {"data_label": LABEL, "generator_version": VERSION, **asdict(scenario),
            "salary_convention": "EUR annual full-time-equivalent base; FTE=1; no bonus",
            "weighting": "transition-weighted; people may contribute multiple events"}


def generate_histories(scenario: Scenario = Scenario()) -> list[dict]:
    """Annual observation spells, including unchanged employment and explicit breaks.

    Each annual employed observation has a synthetic noise shock (-12 to +8%),
    sometimes exactly zero, plus the disclosed change assumptions. Moves and initial
    states are sampled with fixed probabilities; assumptions never alter random draws.
    Employer industry is fixed by employer ID. Experience excludes break years.
    """
    rng = random.Random(scenario.seed)
    rows = []
    for person in range(scenario.people):
        occupation = rng.choice(OCCUPATIONS)
        level = rng.randrange(3)
        employer = rng.randrange(80)
        experience = rng.randrange(1, 15)
        geography = rng.choice(("Dublin", "Cork", "Galway", "Rest of Ireland"))
        salary = float(32000 + level * 15000 + experience * 900 + rng.randrange(-4000, 7000))
        previous_break = False
        for year in range(scenario.years):
            is_break = False
            if year:
                employer_move = rng.random() < .24
                role_move = rng.random() < .12
                promote = rng.random() < .14 and level < 3
                is_break = rng.random() < .045 and not previous_break
                new_employer = (employer + rng.randrange(1, 80)) % 80
                new_role = rng.choice([o for o in OCCUPATIONS if o != occupation])
                shock = rng.choice((0., 0., -12., -6., -3., 2., 4., 8.))
                if employer_move:
                    employer = new_employer
                if role_move:
                    occupation = new_role
                if promote:
                    level += 1
                change = (shock + employer_move * scenario.employer_change_pct
                          + role_move * scenario.occupation_change_pct
                          + promote * scenario.promotion_pct)
                salary = round(max(18000., salary * (1 + change / 100)), 2)
            rows.append({
                "person_id": f"P{person:05d}", "spell_id": f"P{person:05d}-Y{year}",
                "start_date": date(scenario.start_year + year, 1, 1).isoformat(),
                "end_date": date(scenario.start_year + year + 1, 1, 1).isoformat(),
                "occupation": "Career break" if is_break else occupation,
                "employer_id": None if is_break else f"E{employer:03d}",
                "industry": "Not employed" if is_break else INDUSTRIES[employer % len(INDUSTRIES)],
                "seniority": "Not employed" if is_break else LEVELS[level],
                "experience_years": experience, "geography": geography,
                "salary_eur_annual_fte": None if is_break else salary,
                "currency": "EUR", "fte": 1., "salary_basis": "annual base FTE",
                "data_label": LABEL, "generator_version": VERSION,
            })
            experience += int(not is_break)
            previous_break = is_break
    return rows


def derive_transitions(spells: list[dict]) -> list[dict]:
    groups = {}
    for spell in spells:
        groups.setdefault(spell["person_id"], []).append(spell)
    output = []
    for person, history in sorted(groups.items()):
        history.sort(key=lambda r: r["start_date"])
        for before, after in zip(history, history[1:]):
            if before["end_date"] > after["start_date"]:
                raise ValueError("Overlapping career spells")
            break_event = "Career break" in (before["occupation"], after["occupation"])
            flags = {
                "employer_change": before["employer_id"] != after["employer_id"] and not break_event,
                "occupation_change": before["occupation"] != after["occupation"] and not break_event,
                "industry_change": before["industry"] != after["industry"] and not break_event,
                "level_change": before["seniority"] != after["seniority"] and not break_event,
                "promotion": not break_event and LEVELS.index(after["seniority"]) > LEVELS.index(before["seniority"]),
            }
            categories = [name.replace("_change", "") for name, value in flags.items() if value and name != "level_change"]
            if flags["level_change"] and not flags["promotion"]:
                categories.append("demotion")
            category = "Career break / return" if break_event else " + ".join(categories) or "Stayer"
            baseline, outcome = before["salary_eur_annual_fte"], after["salary_eur_annual_fte"]
            comparable = (before.get("currency") == after.get("currency") == "EUR"
                          and before.get("salary_basis") == after.get("salary_basis") == "annual base FTE"
                          and before.get("fte", 0) > 0 and after.get("fte", 0) > 0)
            valid = comparable and all(isinstance(v, (int, float)) and math.isfinite(v) and v > 0
                                       for v in (baseline, outcome))
            output.append({"transition_id": f"{before['spell_id']}->{after['spell_id']}",
                "person_id": person, "before_spell_id": before["spell_id"], "after_spell_id": after["spell_id"],
                "date": after["start_date"], "origin": before["occupation"], "destination": after["occupation"],
                "origin_state": f"{before['occupation']} / {before['seniority']}",
                "destination_state": f"{after['occupation']} / {after['seniority']}",
                "origin_industry": before["industry"], "destination_industry": after["industry"],
                "origin_seniority": before["seniority"], "destination_seniority": after["seniority"],
                "experience_years": before["experience_years"], "geography": after["geography"],
                "category": category, **flags, "valid_pair": bool(valid),
                "before_salary": baseline, "after_salary": outcome,
                "absolute_change": outcome - baseline if valid else None,
                "individual_pct_change": (outcome / baseline - 1) * 100 if valid else None,
                "data_label": LABEL, "generator_version": VERSION})
    return output


def salary_metrics(transitions: list[dict]) -> dict:
    valid = [r for r in transitions if r["valid_pair"]]
    changes = [r["individual_pct_change"] for r in valid]
    before = [r["before_salary"] for r in valid]
    after = [r["after_salary"] for r in valid]
    quartiles = quantiles(changes, n=4, method="inclusive") if len(changes) > 1 else None
    return {"events": len(transitions), "people": len({r["person_id"] for r in transitions}),
            "valid_pairs": len(valid), "excluded_pairs": len(transitions) - len(valid),
            "valid_people": len({r["person_id"] for r in valid}),
            "comparison_available": len(valid) >= MIN_PAIRS,
            "median_individual_pct_change": median(changes) if changes else None,
            "individual_change_iqr": quartiles[2] - quartiles[0] if quartiles else None,
            "median_before_salary": median(before) if before else None,
            "median_after_salary": median(after) if after else None,
            "change_between_cohort_medians_pct": (median(after) / median(before) - 1) * 100 if valid else None,
            "share_decreased": sum(v < 0 for v in changes) / len(changes) if changes else None}
