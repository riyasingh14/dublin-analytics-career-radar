# Data contract

The product is designed so every published insight can be traced to a source, collection date, normalised skill, and original evidence phrase.

## Core entities

| Entity | Grain | Purpose |
|---|---|---|
| `job_source` | One authorised source | Source terms, type, and collection configuration |
| `job_posting` | One canonical advertised job | Deduplicated job identity and public metadata |
| `job_snapshot` | One job seen on one collection date | Enables trend analysis without claiming a live census |
| `skill` | One controlled taxonomy skill | Canonical skill and category |
| `job_skill_evidence` | One extracted skill occurrence in one posting | Original phrase, method, confidence, and review status |
| `role_taxonomy` | One target role group | Controlled Data/BI/Business/Product Analyst scope |

## Required job fields

- Canonical job URL and source ID
- Title, employer, location text, source, and collection timestamp
- Posted date where the source supplies it
- Role taxonomy and classification confidence
- Raw job-description text or a permitted source excerpt
- Deduplication key and record status

## Required AI evidence fields

- Canonical skill ID
- Exact source phrase
- Extraction method and version
- Confidence score from 0 to 1
- Human-review status

## Trend rules

The dashboard reports counts by collection week and source coverage. It does not describe a count as “all Dublin jobs.” A trend requires at least two comparable collection windows and displays its denominator.

## Candidate privacy rule

The MVP stores no candidate profile. Skill selections are used in-session only. Any later account or portfolio-import feature requires a separate privacy review and explicit retention design.
