# Complete, source-attributed job-description examples

The Diagnostic and Readiness tools now offer four complete employer-written
reference documents. They are **historical, closed US government opportunities**,
not current vacancies, Irish-market observations or hiring recommendations.
Users can also paste their own job description or use the small synthetic fixtures.

## Verified sources

All four come from the official 18F / U.S. General Services Administration
Technology Transformation Services hiring repository, pinned to commit
`5dfa66db0f4ba784dd39ebbe1b05f81f4a1c41df`. Its
[licence](https://github.com/18F/join.tts.gsa.gov/blob/5dfa66db0f4ba784dd39ebbe1b05f81f4a1c41df/LICENSE.md)
explicitly dedicates the work to the public domain worldwide through CC0 1.0.
The source licence is also retained in
`data/reference/job-description-samples-LICENSE.md`. No employer endorsement is implied.

| Complete reference | Source / geography | Text characters | Preparation |
|---|---|---:|---|
| [Data & Analytics Specialist](https://github.com/18F/join.tts.gsa.gov/blob/5dfa66db0f4ba784dd39ebbe1b05f81f4a1c41df/archive/coe-data-and-analytics-specialist/index.html) | GSA/TTS Centers of Excellence; Washington, DC, US | 15,191 | Full archived rendered main content |
| [Open Data Specialist](https://github.com/18F/join.tts.gsa.gov/blob/5dfa66db0f4ba784dd39ebbe1b05f81f4a1c41df/archive/data.gov-open-data-specialist/index.html) | GSA/TTS Data.gov; US locations/remote | 14,471 | Full archived rendered main content |
| [Login.gov Product Manager](https://github.com/18F/join.tts.gsa.gov/blob/5dfa66db0f4ba784dd39ebbe1b05f81f4a1c41df/archive/login.gov-product-manager/index.html) | GSA/TTS Login.gov; remote US | 7,994 | Full archived rendered main content |
| [FedRAMP Cyber Data Analyst](https://github.com/18F/join.tts.gsa.gov/blob/5dfa66db0f4ba784dd39ebbe1b05f81f4a1c41df/positions/ttg-fedramp-cyberdata-analyst-2024.md) | GSA/TTS FedRAMP; remote US | 7,034 | Full role body with disclosed source-metadata/template expansion |

Research retrieval date is **25 October 2026**, not the date these roles were posted.
The first three rendered pages explicitly say the posting has closed; original
posting dates were not established and are not invented. The fourth source's
frontmatter records opening 18 April 2024 and closure 25 April 2024.

An incomplete Login.gov Data Analyst draft was excluded. Current Greenhouse,
Lever and employer-careers hosts returned network proxy HTTP 403 in this cloud
environment. No current Irish job description was verified in this research run.
No Adzuna request, paid actor run, LinkedIn scrape or API key was used.

## Full text and transformations

The curated public reference catalogue is
`data/reference/job_description_samples.json`. This deliberately licensed example
library is separate from raw/private job collections and analytical snapshots.
Original research downloads remain outside Git. Every reference carries its
source URL, pinned commit, licence, geography, archived status, retrieval date,
text SHA-256 and transformation description.

For the first three sources, the full rendered `<main>` content was converted to
plain text, preserving role details, responsibilities, qualifications, conditions
and application wording. Navigation back to the job index was omitted; markup
whitespace was normalised and link labels retained. These are not short summaries.

The fourth is explicitly a **normalised adaptation**, not a byte-identical rendered
page. Its title and permanent appointment come from source frontmatter. Salary
values come from the same pinned repository's
[`_data/pay_ranges.yml`](https://github.com/18F/join.tts.gsa.gov/blob/5dfa66db0f4ba784dd39ebbe1b05f81f4a1c41df/_data/pay_ranges.yml),
key `15` (`low` / `high`). The permanent-position wording follows the `perm`
branch of
[`_includes/job/appointment_type.html`](https://github.com/18F/join.tts.gsa.gov/blob/5dfa66db0f4ba784dd39ebbe1b05f81f4a1c41df/_includes/job/appointment_type.html).
It preserves duties and qualifications; author-only template comments and the
interactive apply-button UI are omitted. No requirement or salary was invented.
The UI exposes this derivation alongside the source and licence links.

## Tool behaviour

- Choosing a reference loads its entire text into the editable input.
- Source status, US geography and licence remain visible. The references never
  become Irish-market sample rows or comparable-posting benchmarks.
- Editing the text marks it as user-modified. Restoring the source or clearing
  the tool resets that state. Exported reports retain provenance but omit the
  original document and private evidence notes.
- Real descriptions exposed parsing gaps around wrapped US citizenship wording,
  spelled-out experience duration, decimal grades and explicit location headers.
  These now preserve literal source ranges and appear only as unassessed manual
  conditions, outside the skill index.
- All four documents fit the description/requirement resource limits. Authored
  tests check exact requirement spans, content integrity, source/region labels,
  editing/reset and the separation from synthetic market metrics. They do not
  establish measured real-world extraction accuracy.

Further tool iterations should use documented task-based evaluation: what a user
is trying to decide, whether the source supports the output, what is ambiguous,
and whether the next step is actionable. A live Ireland collection remains a
separate source-permission, network and human-review task.
