# Four-tool prototype — implementation status

Date: 18 October 2026. This records working code and validation, not a public launch
or a claim that every future enhancement in the master specification is complete.

## What works

The primary entry point is `app.py`: a responsive landing page with four working
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

All 72 automated tests passed in this iteration. The suite covers legacy ingestion/extraction, snapshot allowlisting,
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
.venv/bin/python -m pip install -r requirements.txt
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

Import and review the broader Ireland sample; audit extraction and requirement
rules on human-labelled examples; confirm source display permissions; measure
usability and performance; execute the SQL pipeline against its intended database;
and configure permitted, budget-capped weekly refresh. Public deployment, recurring
paid services, automatic collection and a real hiring-outcome model are not part
of this iteration.
