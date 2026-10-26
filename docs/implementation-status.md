# Four-tool prototype — implementation status

Date: 18 October 2026. This records working code and validation, not a public launch
or a claim that every future enhancement in the master specification is complete.

## Latest review — 26 October 2026

The homepage visual changes and cross-page motion pass are complete for local
review. The full production build, 157 Python tests (including PostgreSQL) and
44 browser checks pass. See the [current tool-readiness review](tool-readiness-review-2026-10-26.md)
for the remaining Irish-data, human-evaluation, user-journey and hosted-release
gaps. Earlier counts and implementation descriptions below record their original
iterations; the operations runbook supersedes historical SQL-only limitations.

## Current release: integrated tools, review and editorial redesign

**25 October homepage/reference update:** the hero sculpture now has a transparent
background, and a compact Riya Singh builder section near the hero links to her
supplied LinkedIn profile, source code and methods. Four complete, CC0-licensed
historical US employer descriptions are selectable in Diagnostic and Readiness,
with source/region/archive labels, edit provenance and licence links. They are
reference inputs, not current Irish vacancies or market data. See
[source research and transformations](job-description-reference-library.md).
Real-document checks also fixed literal citizenship, wrapped prose, decimal grade
and explicit location cues. Local validation: 157 Python checks (including four
actual PostgreSQL checks), production build and 33 browser/interaction checks
passed. Real-world rule accuracy and hosted deployment remain separately unverified.

**25 October addition:** private `review_app.py` provides manual extraction review,
checkpoint resume, category progress and private exports. V2 evaluations reject
duplicate evidence, inconsistent statuses, rounded-below-threshold precision and
reuse against a changed dataset or displayed source evidence. A fresh 100-record
queue was prepared from the existing 32-job pilot; all labels remain blank and
publication remains disabled. See [human review](human-review-workbench.md).
Validation for this addition: 148 Python tests passed, including four actual
PostgreSQL checks and five private-review AppTest flows; public build and nine
Flask-only HTTP checks passed. The private service also rendered its actual
100-pending-record queue and download controls in Chromium without entering any
decisions. Its labels remain blank. Earlier public-browser counts below describe
the prior visual release; the public frontend did not change in this addition.

All four public demonstration tools now include the functional gaps identified
in the master-plan review: Constellation search/category legend/bounded graph and
role-comparison heatmap; Readiness source selection/provenance/condition checklist
and baseline comparison; Mobility linked cohorts, directional network, conserving
Sankey, matrix, bands and timeline; Diagnostic highlighted source spans, review
states, additive diff and unavailable observed benchmark. The shared data passport
exposes fixture lineage and absent collection dates. A five-minute walkthrough is
included on the Methods page.

The private saved-file refresh and PostgreSQL warehouse are implemented and
executed locally. The public app remains independent and synthetic. No live paid
collector or observed-data publication is enabled. See the
[operations runbook](operations-runbook.md).

Independent cross-review and an additional release review preceded the new light
editorial design. Cobalt/ivory/ink typography, a projected orbital skill sculpture,
pointer-responsive cards and global/system motion controls are implemented.
Analytical values and chart layouts stay stable while inspected.

Final local validation: **130 Python tests passed with no skips**, including four
actual PostgreSQL checks; **30 browser/interaction checks passed**, including all
six routes under axe WCAG A/AA rules; production build passed. Separate Flask-only
HTTP tests passed without SQL/research dependencies. See the
[platform review and acceptance trace](platform-review.md) and
[visual system](visual-system.md). Older iteration counts below are historical.

## Vercel web version

The React/Vite frontend under `web/` and Flask function under `api/` now implement
the four public-demo workflows using the same Python analytical core. This is a
separate hosting interface; it does not attempt to run Streamlit on Vercel. Public
bootstrap data is always synthetic. Root deployment dependencies are Flask-only;
research dependencies moved to `requirements-local.txt`. See
[Vercel deployment](vercel-deployment.md) for account linking and verification.

The Vercel iteration passed 80 Python tests, seven Playwright browser flows, the
production frontend build and an isolated deployment-only Python runtime check.
A successful local build/test does not establish an actual hosted deployment. The
CLI is logged out and its login attempt failed with a network fetch error. The
owner subsequently supplied the deployed website URL. Independent hosted checks
remain blocked by proxy HTTP 403 / direct DNS failure in this workspace. The
official Vercel plugin is installed in the user configuration; tool restart and
OAuth are still required before claiming an authenticated Vercel connection.

The subsequent evidence/release iteration adds keyboard-selectable network edges,
visible selection, exact matched source phrases with rule versions, and access to
every supporting fictional posting. Changing focus clears incompatible pair
selection. Filter recalculation clears stale results. The release runner targets
an explicit hosted origin without local fallback; GitHub workflows configure
local checks and deployment-event/manual hosted checks. Workflow execution and
actual hosted acceptance are still unverified.

Validation for this subsequent iteration: all 80 Python tests, all 10 browser/API
checks and the TypeScript/production build passed locally. The graph check covers
both pointer and keyboard selection, exact phrases, rule versions, expansion to
all supporting examples and clearing incompatible selection on skill focus.
Both workflow YAML files parsed locally; this is not evidence of GitHub execution.

## Readiness evidence-action iteration

The public web Readiness Studio now has a weighted, deduplicated evidence breakdown
and a versioned evidence-action planner. It reuses the score's strongest-confirmed
skill grouping, preventing repeated mentions from increasing priority or weight.
Unknown evidence prompts review rather than an invented skill deficit. Missing
and partial evidence receive authored taxonomy-linked project briefs, deliverables
and completion checks. Supported skills produce no unnecessary project action.

Each action exposes its source contexts. Project actions prepare a separate
what-if for an unresolved occurrence, including when an earlier repeated mention
already has supported evidence. Planning does not change baseline notes, statuses
or scores. The scenario selector omits weaker repeated mentions that do not affect
the score. Exports include the plan and weight breakdown while omitting candidate
notes and advert text. This is a web enhancement; the internal Streamlit interface
retains its previous presentation.

Validation: 86 Python tests, 14 browser/API checks and the production build passed
locally. Nine HTTP-boundary tests also passed using the Flask-only deployment
environment. New checks reconcile a hand-calculated repeated-skill example,
unknowns, corrected classifications, immutable plans, source tracing, private
downloads, hypothetical isolation and an expanded 390px mobile layout. These do
not establish real-world rule accuracy, verified proficiency or hosted acceptance.
See [evidence planner](evidence-planner.md) for the worked calculation and limits.

## What works

The internal Streamlit entry point is `app.py`: a responsive landing page with four working
cards, shared navigation, honest dataset status and a Methodology route. Independent
tools remain usable when the observed snapshot is missing or malformed.

| Tool | Implemented in this iteration | Limitations |
|---|---|---|
| Skill Constellation | Unique-posting co-mentions; support, Jaccard and lift; role/geography filters; bounded stable network; pair tables, heatmap, role comparison, source drill-down and CSV export | Current real sample has 32 postings; sparse role filters suppress network display. No historical filtering without actual comparable observations. |
| Opportunity Readiness Studio | Posting/paste/explicit-demo input; shared requirement extraction; user-correctable classification; self-reported evidence notes; transparent weights and 80% coverage guard; baseline/what-if comparison; session reset and minimal export | No callback model, credential verification, résumé parsing or company likelihood ranking. Eligibility is explicitly unassessed. Matching rules require human evaluation. |
| Career Mobility Lab | Seeded annual histories for technical and adjacent occupations; breaks, stayers, cuts and promotions; transition flags/exclusive groups; radial, Sankey, heatmap, distributions and timelines; cohort filters; baseline/scenario comparison; labelled export | Entirely synthetic, with disclosed illustrative assumptions. Annual observations simplify real job spells; no real salary inference or causal estimate. Small salary cohorts are suppressed. |
| Job Description Diagnostic | Exact requirement spans; required/preferred/uncertain/negated rules; completeness, clarity, consistency and data-quality findings; editable clarification proposals and diffs; dismissal/reset; minimal JSON report | Conservative authored rules, not independently measured document-quality accuracy. No employer score, legal opinion, live benchmark or external LLM rewrite. Edited source text is labelled user-modified. |

The former market dashboard remains available independently as `market_app.py`
for market/evidence/regression work. It is a supporting workbench, not a fifth
flagship on the landing page.

## Shared implementation

- `requirements_model.py` is used by both Diagnostic and Readiness, so fixes to
  negation, explicit preferences and section scope apply consistently.
- Snapshot schema v2 contains allowlisted posting records, including description
  text needed by the two requirement tools. Profile fields and arbitrary imported
  metadata are excluded. This private snapshot still needs personal-data review.
- The real pilot was rebuilt locally; publication remains disabled. No additional
  paid source calls or external AI requests were made.
- Python analytics power the current application. The constellation SQL reference
  was exercised with an equivalent SQLite fixture; this does not establish an
  operational PostgreSQL pipeline. The PostgreSQL mobility worksheet is supplied
  as a reference and has not been executed against PostgreSQL.
- Raw/processed/review data, candidate evidence and generated histories are not
  committed. Candidate evidence is session-scoped; resetting clears the tool's
  inputs, corrections, results and scenarios. Downloaded files cannot be revoked.

## Validation

The initial Streamlit iteration passed 72 automated tests; the newer web iteration
counts are recorded above. The suite covers legacy ingestion/extraction, snapshot allowlisting,
unique denominators, co-mention formulas, requirement language regressions,
user corrections, evidence coverage, hypothetical isolation, deterministic histories,
career breaks and invalid salary pairs, SQL fixtures, session reset, malformed
snapshots and composed app navigation. Diagnostic rules have authored test cases,
not a completed human-audited accuracy study.

Chromium/Playwright checks exercised each route at 1440px desktop and 390px mobile
widths, selected the explicit examples, rendered both graph modules, and checked
browser exceptions and horizontal overflow. These are viewport/interaction checks,
not a completed independent accessibility audit. Source URLs were rendered safely;
opening third-party job pages is outside the local functional check.

## Local operation

```bash
cd /workspace/dublin-analytics-career-radar
python -m venv .venv
.venv/bin/python -m pip install -r requirements-local.txt
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python -m streamlit run app.py --server.headless=true
```

Use `CAREER_RADAR_SNAPSHOT=/absolute/path/to/market_snapshot.json` to select a
private dataset. The default is `data/processed/market_snapshot.json`. Without one,
the home page explains the missing sample; the Diagnostic, Readiness paste/demo
flow and synthetic Mobility Lab continue to work. The Constellation needs a v2
snapshot with posting records to preserve jobs without extracted skills in N. Without
a snapshot, its explicit demonstration toggle loads 30 fictional postings in memory;
these remain labelled synthetic and never replace the real dataset.
Rebuild older snapshots with the tracked `career_radar.build_snapshot` command;
its new schema is emitted automatically.

## Next release gates

Import/review the broader Ireland sample; audit rules on human-labelled examples;
confirm public source permissions; verify hosted deployment and remote CI; measure
user comprehension and hosted performance; and configure authorised, budget-capped
live collection if approved. PostgreSQL reconciliation and a saved-file fixture
refresh now work locally. A real hiring-outcome model remains outside scope.
