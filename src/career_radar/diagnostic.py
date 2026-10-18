"""Evidence-linked checks: document review, never employer/hiring quality."""
from __future__ import annotations
import hashlib
import re
from career_radar.normalise import Skill, classify_role
from career_radar.requirements_model import extract_requirements, AnalysisLimitError

RULE_VERSION = "diagnostic-v2"
LIMITATIONS = ("Deterministic document review only; not an employer, legal or hiring-effectiveness assessment. "
               "Missing means not stated in this text. Unknown means wording needs human interpretation. "
               "No external model or comparable-posting benchmark is used.")

def analyze_description(text: str, taxonomy: list[Skill]) -> dict:
    text = text or ""
    requirements = extract_requirements(text, taxonomy)
    findings = []

    def finding(rule, category, rationale, suggestion, match=None, absent_field=None, severity="review"):
        if len(findings) >= 200:
            raise AnalysisLimitError("This description produces more than 200 review findings. Shorten it or remove repeated sections before analysing again.")
        start, end = (match.start(), match.end()) if match else (None, None)
        findings.append({
            "finding_id": hashlib.sha256(f"{RULE_VERSION}|{rule}|{start}|{text}".encode()).hexdigest()[:16],
            "rule": rule, "category": category, "severity": severity,
            "source_phrase": match.group() if match else "", "start": start, "end": end,
            "absent_field": absent_field, "rationale": rationale, "suggestion": suggestion,
        })

    checks = {
        "salary": (r"(?:€|£|\$|\bEUR\b|\bGBP\b|\bUSD\b)\s*\d[\d,.]*(?:\s*[kK])?", r"\b(?:salary|pay|compensation|remuneration)\b", "What is the salary range, currency and pay period?"),
        "work_arrangement": (r"\b(?:hybrid|remote|on[- ]?site|office[- ]based)\b", r"\b(?:flexible working|work arrangement)\b", "What are the office attendance and remote-location requirements?"),
        "location": (r"\b(?:Dublin|Cork|Galway|Limerick|Waterford|Belfast|Ireland)\b|\blocation\s*:\s*\w+", r"\b(?:location|based in|office)\b", "Where is the role based, and are there location restrictions?"),
        "contract_type": (r"\b(?:permanent|fixed[- ]term|temporary|contractor|internship)\b", r"\b(?:contract|employment type|full[- ]time|part[- ]time)\b", "What are the contract duration and working hours?"),
        "responsibilities": (r"\b(?:responsibilities|duties|you will|you'll|your role|what you(?:'|’)ll do)\b", r"\b(?:role|work|responsibility)\b", "What outcomes and day-to-day responsibilities will this role own?"),
    }
    completeness = {}
    for name, (present_pattern, unknown_pattern, question) in checks.items():
        present = re.search(present_pattern, text, re.I)
        if name == "salary":
            # Currency alone also matches training budgets and expense allowances.
            # Require an explicit pay label in the same short sentence/clause.
            present = next((amount for amount in re.finditer(present_pattern, text, re.I)
                            if re.search(r"\b(?:salary|pay|compensation|remuneration)\b",
                                         re.split(r"[.;\n]", text[max(0, amount.start()-65):amount.start()])[-1], re.I)
                            and not re.search(r"\b(?:budget|allowance|expenses|training|equipment)\b",
                                              text[max(0, amount.start()-35):amount.start()], re.I)), None)
        unknown = re.search(unknown_pattern, text, re.I)
        match = present or unknown
        status = "present" if present else "unknown" if unknown else "missing"
        completeness[name] = {"status": status, "source_phrase": match.group() if match else "",
                              "start": match.start() if match else None, "end": match.end() if match else None}
        if status != "present":
            finding(f"completeness.{name}", "Completeness",
                    "Information is not explicitly stated." if status == "missing" else "A related phrase appears, but the detail needs confirmation.",
                    question, match=unknown, absent_field=name if not unknown else None,
                    severity="not stated" if status == "missing" else "review")

    for match in re.finditer(r"\b(?:competitive salary|excellent communication|strong knowledge|expert[- ]level|rockstar|ninja|fast[- ]paced)\b", text, re.I):
        finding("clarity.vague_phrase", "Clarity",
                "This phrase does not specify an observable expectation or measurable detail.",
                "Clarify with an example or explicit expectation: [author to supply detail].", match)
    known_terms = {alias.upper() for skill in taxonomy for alias in skill.aliases}
    known_terms.update({"EUR", "GBP", "USD", "EU", "UK", "US", "CV", "HR", "IT"})
    for match in re.finditer(r"\b[A-Z]{2,5}\b", text):
        term = match.group()
        if term in known_terms:
            continue
        expansion = r"[A-Za-z]+(?:[ -][A-Za-z]+){1,8}\s*\(" + re.escape(term) + r"\)"
        if not re.search(expansion, text):
            finding("clarity.possible_abbreviation", "Clarity",
                    "This uppercase term may be an abbreviation, name or code. The limited rule found no preceding parenthesised expansion.",
                    "If this term is an unfamiliar abbreviation, expand it on first use; otherwise dismiss this flag.", match)
    first_line = next((line for line in text.splitlines() if line.strip()), "")
    title_role = classify_role(first_line)[0]
    if title_role:
        for match in re.finditer(r"\b(?:work|serve|act) as (?:an? )?[^.\n;]+", text, re.I):
            body_role = classify_role(match.group())[0]
            if body_role and body_role != title_role:
                finding("alignment.role_wording", "Role alignment",
                        f"The first line matches {title_role}, while this phrase matches {body_role}. A cross-functional role may be intentional.",
                        "Clarify the primary role and which responsibilities belong to collaborating teams.", match)
    entry = re.search(r"\b(?:entry[- ]level|graduate|junior)\b", text, re.I)
    substantial = re.search(r"\b(?:[3-9]|[1-9]\d)\+?\s*(?:years?|yrs?)\b", text, re.I)
    if entry and substantial:
        span = re.search(re.escape(text[min(entry.start(), substantial.start()):max(entry.end(), substantial.end())]), text)
        finding("consistency.entry_experience", "Internal consistency",
                "An early-career label and three or more years appear together. Confirm whether the experience is required and relevant to this level.",
                "Clarify which experience is essential and how it relates to the stated level.", span)
    remote = re.search(r"\bfully remote\b", text, re.I)
    office = re.search(r"\b(?:on[- ]?site|office)\s+(?:every day|five days|5 days)\b", text, re.I)
    if remote and office:
        span = re.search(re.escape(text[min(remote.start(), office.start()):max(remote.end(), office.end())]), text)
        finding("consistency.workplace", "Internal consistency",
                "Fully remote work and daily office attendance appear together; these may concern different contexts.",
                "Explain which attendance arrangement applies and any exceptions.", span)
    for row in requirements:
        if row["requirement_type"] == "uncertain":
            match = re.compile(re.escape(row["source_phrase"])).search(text, row["start"], row["end"])
            finding("structure.unprioritised_skill", "Requirement structure",
                    "This skill is mentioned without an unambiguous essential/preferred designation.",
                    f"Is {row['skill_name']} essential, preferred, or contextual? [author to confirm]", match)
    if not text.strip():
        finding("quality.empty", "Data quality", "No description was supplied; content cannot be assessed.",
                "Provide the original description before interpreting these checks.", absent_field="description")
    for match in re.finditer(r"(?:€|£|\$|\bEUR\b)\s*\d[\d,.]*(?:\s*[kK])?", text, re.I):
        context = text[max(0, match.start()-35):match.end()+50]
        if not re.search(r"\b(?:annual|annum|year|yearly|month|monthly|hour|hourly|day|daily|pa)\b|/\s*(?:yr|hr|mo)\b", context, re.I):
            finding("quality.salary_period", "Data quality",
                    "A monetary figure appears without a nearby explicit pay period; it may not be salary.",
                    "Confirm what the amount represents and specify its period where applicable.", match)
    seen = set()
    for match in re.finditer(r"[^\n]+", text):
        line = match.group().strip()
        if len(line) > 40 and line in seen:
            finding("quality.duplicate_line", "Data quality",
                    "This exact line appears more than once; inspect for export/parsing duplication.",
                    "Review the repetition before removing anything from the original.", match)
        seen.add(line)
    # Preserve malformed source exactly; a flag is a parsing warning, not a repair.
    for match in re.finditer(r"\ufffd|[\x00-\x08\x0b\x0c\x0e-\x1f]|</?[A-Za-z][^>\n]{0,250}>", text):
        finding("quality.possible_export_artifact", "Data quality",
                "A replacement character, control character or HTML-like tag appears in the source. It may be an export artifact or intentional example code.",
                "Compare with the authorised original; correct only confirmed export errors. Keep intentional code unchanged.", match)
    return {"requirements": requirements, "findings": findings, "completeness": completeness,
            "rule_version": RULE_VERSION, "limitations": LIMITATIONS, "benchmark": None,
            "benchmark_status": {"available": False, "comparable_observed_postings": 0,
                                 "minimum_sample": 20,
                                 "reason": "No reviewed, comparable observed postings are connected to this analysis. Synthetic examples are excluded."}}
