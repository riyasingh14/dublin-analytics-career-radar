"""Conservative requirement extraction with exact, inspectable source spans."""
from __future__ import annotations

import hashlib
import re

from career_radar.normalise import Skill

EXTRACTION_VERSION = "requirements-v2-bounded"
MAX_REQUIREMENTS = 200
MAX_CONTEXT_CHARS = 600


class AnalysisLimitError(ValueError):
    """Known public input error; never embed supplied text in this message."""


class RequirementLimitError(AnalysisLimitError):
    """The repeated skill-mention ceiling was exceeded."""
_REQUIRED = r"\b(?:required|essential|mandatory|must(?: have)?|need(?:ed)?|requirements)\b"
_PREFERRED = r"\b(?:preferred|desirable|optional|nice[- ]to[- ]have|advantage|bonus)\b"
_NEGATED = r"\b(?:not\s+(?:strictly\s+)?(?:required|essential|necessary|mandatory)|no\s+(?:prior\s+)?(?:experience|knowledge|proficiency)(?:\s+\w+){0,6}\s+(?:required|necessary)|do(?:es)?\s+not\s+require|no\s+(?:prior\s+)?(?:\w+\s+){1,4}experience\s+(?:is\s+)?required)\b"


def _kind(context: str) -> str:
    if re.search(_NEGATED, context, re.I):
        return "negated"
    required = bool(re.search(_REQUIRED, context, re.I))
    preferred = bool(re.search(_PREFERRED, context, re.I))
    if required and preferred:
        return "uncertain"
    if preferred:
        return "preferred"
    return "required" if required else "uncertain"


def extract_requirements(text: str, taxonomy: list[Skill]) -> list[dict]:
    """Extract mentions, never interpreting a contextual mention as mandatory.

    IDs are deterministic for the same text, skill and offsets. Multiple mentions
    remain distinct. Sentence/line evidence and phrase offsets refer to input text.
    Explicit requirement headings apply to following lines until another heading.
    This is a rule baseline, not a language understanding or eligibility model.
    """
    text = text or ""
    results = []
    heading_kind = "uncertain"
    for sentence in re.finditer(r"[^\n]+?(?:[.!?](?=\s|$)|(?=\n|$))", text):
        source = sentence.group()
        stripped = source.strip()
        if re.fullmatch(r"(?:essential(?: skills)?|requirements|required(?: skills)?|must have|preferred(?: skills)?|desirable(?: skills)?|nice to have)\s*:", stripped, re.I):
            heading_kind = _kind(stripped)
            continue
        if re.fullmatch(r"(?:benefits|about us|about the company|responsibilities|duties|what we offer|our offer|the role|about you|company overview|compensation|salary)\s*:?", stripped, re.I):
            heading_kind = "uncertain"
            continue
        if stripped.endswith(":"):
            heading_kind = "uncertain"
        # Commas/semicolons and contrast words delimit independent assertions.
        for clause in re.finditer(r"[^,;]+", source):
            clause_text = clause.group()
            parts = re.split(r"\b(?:but|however|whereas)\b", clause_text, flags=re.I)
            cursor = 0
            for part in parts:
                part_start = clause_text.find(part, cursor)
                cursor = part_start + len(part)
                # An assertion before 'and' has ended; plain skill lists stay together.
                segments = []
                start = 0
                for conjunction in re.finditer(r"\band\b", part, re.I):
                    if re.search(r"\b(?:required|essential|mandatory|preferred|desirable|optional|bonus)\s*$", part[start:conjunction.start()], re.I):
                        segments.append((start, part[start:conjunction.start()]))
                        start = conjunction.end()
                segments.append((start, part[start:]))
                for segment_start, segment in segments:
                    matches = []
                    for skill in taxonomy:
                        aliases = sorted(set(skill.aliases), key=len, reverse=True)
                        if not aliases:
                            continue
                        pattern = r"(?<!\w)(?:" + "|".join(re.escape(a) for a in aliases) + r")(?!\w)"
                        matches.extend((m, skill) for m in re.finditer(pattern, segment, re.I))
                    matches.sort(key=lambda row: row[0].start())
                    for index, (match, skill) in enumerate(matches):
                        left = matches[index - 1][0].end() if index else 0
                        right = matches[index + 1][0].start() if index + 1 < len(matches) else len(segment)
                        local = segment[left:right]
                        # A leading 'No ... experience ... required' scopes over the
                        # entire coordinated list, not just its first skill.
                        coordinated_negation = bool(re.match(r"\s*(?:[-•*]\s*)?no\b", segment, re.I)) and _kind(segment) == "negated"
                        kind = "negated" if coordinated_negation else _kind(local)
                        if kind == "uncertain":
                            kind = _kind(segment)
                        if kind == "uncertain" and "," in source:
                            # Propagate a single explicit designation over a plain
                            # comma-separated skill list, never over prose clauses.
                            residue = segment
                            for candidate in taxonomy:
                                for alias in sorted(candidate.aliases, key=len, reverse=True):
                                    residue = re.sub(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", "", residue, flags=re.I)
                            residue = re.sub(r"\b(?:and|or)\b|[\s&/().:-]", "", residue, flags=re.I)
                            if not residue and not re.search(r"\b(?:but|however|whereas)\b", source, re.I):
                                kind = _kind(source)
                        if kind == "uncertain":
                            kind = heading_kind
                        # Quoted examples are evidence of a mention, not an obligation.
                        before = segment[:match.start()]
                        if re.search(r"\b(?:for example|e\.g\.?|such as)\b", before, re.I) or any(before.count(q) % 2 for q in ('"', '“')):
                            kind = "uncertain"
                        offset = sentence.start() + clause.start() + part_start + segment_start
                        begin, end = offset + match.start(), offset + match.end()
                        if len(results) >= MAX_REQUIREMENTS:
                            raise RequirementLimitError("This description contains more than 200 skill mentions. Shorten it or remove repeated sections before analysing again.")
                        context_start = max(sentence.start(), begin - 250)
                        context_end = min(sentence.end(), context_start + MAX_CONTEXT_CHARS)
                        if len(source) <= MAX_CONTEXT_CHARS:
                            context_start, context_end = sentence.start(), sentence.end()
                        identity = f"{EXTRACTION_VERSION}|{text}|{skill.skill_id}|{begin}|{end}"
                        results.append({
                            "requirement_id": hashlib.sha256(identity.encode()).hexdigest()[:20],
                            "skill_id": skill.skill_id, "skill_name": skill.skill_name,
                            "source_phrase": text[begin:end], "source_text": text[context_start:context_end],
                            "context_start": context_start, "context_end": context_end,
                            "context_truncated": context_start != sentence.start() or context_end != sentence.end(),
                            "requirement_type": kind, "start": begin, "end": end,
                            "extraction_version": EXTRACTION_VERSION,
                        })
    return sorted(results, key=lambda row: (row["start"], row["skill_id"]))
