"""Conservative, source-preserving listing-condition cues; never candidate inference.

A matched sentence is a review cue, not an eligibility determination. Negations,
optional language and alternatives are deliberately preserved for manual review.
"""
import re

_CUES = {
    "degree": re.compile(r"\b(?:degree|bachelor(?:['’]?s)?|master(?:['’]?s)?|PhD|doctorate|qualification|minimum grade|GPA)\b", re.I),
    "experience": re.compile(r"\b(?:(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*(?:[-–]\s*\d+\s*)?\+?\s*years?\b.{0,35}\bexperience|experience\b.{0,35}\b\d+\s*\+?\s*years?)", re.I),
    "location": re.compile(r"\blocation\s*:|\b(?:based in|located in|relocat\w*|on[- ]site|hybrid|remote|Dublin|Cork|Ireland)\b", re.I),
    "work_eligibility": re.compile(r"\b(?:right to work|authori[sz](?:ed|ation) to work|work (?:permit|visa|authori[sz]ation|eligibility)|visa sponsorship|sponsor(?:ship)?\b.{0,25}\bvisa|citizenship|U\.?S\.? citizens?|citizens or nationals)\b", re.I),
}


def extract_listing_conditions(text: str) -> list[dict]:
    """Return literal sentence spans with conservative categories and no scoring.

    No match means no detected cue, not absence of a requirement. The caller must
    retain the manual-review caveat, including for negated and optional phrases.
    """
    conditions = []
    # Protect abbreviations and decimal points without changing Unicode offsets.
    masked = re.sub(r"\b(?:U\.S\.|U\.K\.|e\.g\.|i\.e\.|Ph\.D\.)",
                    lambda match: match.group().replace('.', '\u2024'), text, flags=re.I)
    masked = re.sub(r"(?<=\d)\.(?=\d)", '\u2024', masked)
    # Single newlines may be wrapped prose, not sentence boundaries. Blank lines
    # delimit paragraphs while all returned ranges still slice the original text.
    for paragraph in re.finditer(r"\S[\s\S]*?(?=\n[ \t]*\n|$)", masked):
        for match in re.finditer(r"[^.!?]+(?:[.!?]|$)", paragraph.group()):
            absolute = paragraph.start() + match.start()
            raw = text[absolute:paragraph.start() + match.end()]
            leading = len(raw) - len(raw.lstrip())
            source = raw.strip()
            if not source:
                continue
            start = absolute + leading
            for category, pattern in _CUES.items():
                if pattern.search(source):
                    conditions.append({
                        "condition_id": f"{category}:{start}",
                        "category": category,
                        "source_text": source,
                        "start": start,
                        "end": start + len(source),
                        "status": "unknown",
                        "needs_manual_review": True,
                        "excluded_from_index": True,
                    })
    return conditions
