"""Controlled, explainable normalisation for Career Radar job postings."""

from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

TAXONOMY_VERSION = "taxonomy-v2-tech"
ROLE_CLASSIFICATION_VERSION = "roles-v2-tech"

@dataclass(frozen=True)
class Skill:
    skill_id: str
    skill_name: str
    category: str
    aliases: tuple[str, ...]


def load_taxonomy(path: Path) -> list[Skill]:
    with path.open(newline="", encoding="utf-8") as file:
        rows = csv.DictReader(file)
        return [
            Skill(
                skill_id=row["skill_id"],
                skill_name=row["skill_name"],
                category=row["category"],
                aliases=tuple(alias.strip() for alias in row["aliases"].split("|") if alias.strip()),
            )
            for row in rows
        ]


def extract_skills(description: str, taxonomy: list[Skill]) -> list[dict[str, str | float]]:
    """Return one evidence record per skill, retaining the exact matched phrase.

    This deterministic baseline is intentionally auditable. A future LLM extractor can
    add records with extraction_method='llm', rather than replacing this evidence.
    """
    evidence: list[dict[str, str | float]] = []
    text = description or ""
    for skill in taxonomy:
        matches: list[tuple[int, str]] = []
        for alias in skill.aliases:
            match = re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", text, flags=re.IGNORECASE)
            if match:
                matches.append((match.start(), match.group(0)))
        if matches:
            _, phrase = min(matches, key=lambda item: item[0])
            evidence.append(
                {
                    "skill_id": skill.skill_id,
                    "skill_name": skill.skill_name,
                    "category": skill.category,
                    "source_phrase": phrase,
                    "extraction_method": "rule",
                    "extraction_version": TAXONOMY_VERSION,
                    "confidence": 0.98,
                }
            )
    return evidence


ROLE_RULES = {
    # Specific titles precede broad software terms to resolve overlapping titles.
    "Machine Learning Engineer": ("machine learning engineer", "ml engineer", "ai engineer"),
    "Data Engineer": ("data engineer", "analytics engineer"),
    "Data Scientist": ("data scientist", "research scientist"),
    "Frontend Developer": ("frontend developer", "front end developer", "front-end developer", "frontend engineer", "front end engineer", "front-end engineer"),
    "Backend Developer": ("backend developer", "back end developer", "back-end developer", "backend engineer", "back end engineer", "back-end engineer"),
    "Full Stack Developer": ("full stack developer", "full-stack developer", "fullstack developer", "full stack engineer", "full-stack engineer", "full stack software engineer"),
    "Mobile Developer": ("mobile developer", "mobile engineer", "ios developer", "ios engineer", "android developer", "android engineer"),
    "Embedded Engineer": ("embedded engineer", "embedded software engineer", "firmware engineer"),
    "QA Engineer": ("qa engineer", "qa analyst", "test engineer", "automation test engineer", "software tester", "quality assurance engineer", "sdet"),
    "DevOps / SRE": ("devops engineer", "site reliability engineer", "platform engineer"),
    "Cloud Engineer": ("cloud engineer", "cloud infrastructure engineer"),
    "Security Engineer": ("security engineer", "cybersecurity analyst", "cyber security analyst", "security analyst", "soc analyst"),
    "Network Engineer": ("network engineer", "network administrator"),
    "IT Support": ("it support", "technical support engineer", "service desk analyst", "desktop support"),
    "Solutions Architect": ("solutions architect", "solution architect", "cloud architect", "software architect", "technical architect"),
    "Software Engineer": ("software engineer", "software developer", "application developer"),
    "Product Manager": ("product manager", "technical product manager", "product owner"),
    "Data Analyst": ("data analyst", "analytics analyst"),
    "Business Analyst": ("business analyst", "business systems analyst"),
    "BI Analyst": ("bi analyst", "business intelligence analyst", "reporting analyst", "power bi consultant"),
    "Product Analyst": ("product analyst",),
}


def geography_group(location: str) -> str:
    """Conservative Republic of Ireland grouping from explicit location text."""
    text = (location or "").lower()
    if "northern ireland" in text or "united kingdom" in text or re.search(r"\b(uk|belfast)\b", text):
        return "Outside scope / unknown"
    if not re.search(r"\bireland\b", text):
        return "Outside scope / unknown"
    if re.search(r"\bdublin\b", text):
        return "Dublin"
    # Country-only or remote listings cannot be assigned to the rest of Ireland.
    place = re.sub(r"\b(ireland|remote|hybrid|onsite|on-site|on site)\b", "", text)
    if not re.search(r"\w", place):
        return "Ireland — location unspecified"
    return "Rest of Ireland"


def classify_role(title: str) -> tuple[str | None, float]:
    lower_title = (title or "").lower()
    for role, terms in ROLE_RULES.items():
        if any(re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", lower_title) for term in terms):
            return role, 0.99
    return None, 0.0


def classify_work_pattern(text: str) -> str:
    lower_text = (text or "").lower()
    if "hybrid" in lower_text:
        return "hybrid"
    if "remote" in lower_text or "work from home" in lower_text:
        return "remote"
    if "on-site" in lower_text or "onsite" in lower_text or "on site" in lower_text:
        return "onsite"
    return "unknown"


def deduplication_key(title: str, employer_name: str, location_text: str, description: str) -> str:
    normalised = "|".join(
        re.sub(r"\s+", " ", value.lower()).strip()
        for value in (title or "", employer_name or "", location_text or "", description or "")
    )
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()
