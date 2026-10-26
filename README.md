# Dublin Analytics Career Radar

An evidence-backed labour-market intelligence tool for technology careers across Ireland, with Dublin shown separately. The expanded scope covers 21 role families and retains the original analytics workflow.

A four-tool research studio for exploring skill relationships, assessing candidate evidence, analysing synthetic career moves and diagnosing job descriptions. It is built as an inspectable data/business analyst portfolio project.

## The product gap

Job boards list vacancies. Enterprise labour-market platforms are expensive and opaque. This project focuses on a transparent, candidate-facing middle ground:

- Ireland-wide technology skill evidence, with Dublin shown separately;
- Rule-normalised skills with exact source evidence and versioned assumptions;
- comparison of target role, seniority, industry, and work pattern;
- a skill-gap view that turns a missing skill into a concrete portfolio or interview-proof action;
- published data freshness, coverage, and limitations.

## Web app and Vercel deployment

A React/Vite website and lightweight Python API now provide the public-demo version
of all four tools. Analytical views use generated examples; Diagnostic and Readiness
also offer [complete, licensed archived employer descriptions](docs/job-description-reference-library.md).
The private job sample is not exposed. The homepage introduces builder Riya Singh,
her analytical approach and her LinkedIn profile.
See **[Vercel deployment](docs/vercel-deployment.md)** for GitHub linking, local setup,
validation and hosted smoke checks. The owner selected the shorter production address
[ireland-career-radar.vercel.app](https://ireland-career-radar.vercel.app/).
Workspace network restrictions currently prevent independent hosted verification.

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements-local.txt
npm ci
# terminal 1
.venv/bin/python api/index.py
# terminal 2
npm run dev
```

`npm run build` creates the static site. `npm test` runs the browser flows (requires
Playwright Chromium; see the deployment guide). The Vercel project root must be the
repository root; framework Vite, output `dist`. No API keys are needed for the demo.

Run the browser/API release suite against the actual website with
`npm run test:deployed -- https://ireland-career-radar.vercel.app/`.
The default hosted check validates the current data mode and opens all four tools;
it supports both synthetic and reviewed releases. Pass an explicit test file to
run a broader suite. GitHub Actions checks builds, Python and browser regressions on pushes/PRs. A
separate hosted workflow runs when Vercel emits a successful production deployment
event, or manually from Actions. Its results must be inspected before claiming a
hosted release is verified.

## Selected product scope

The complete specification is in **[PROJECT_DESCRIPTION.md](PROJECT_DESCRIPTION.md)**.
It defines four flagship experiences, their calculations, user journeys, visual
requirements, data controls and acceptance criteria. The existing market dashboard
is their shared analytical foundation.

1. **Skill Constellation** — inspect skill co-mentions and associations with source evidence.
2. **Opportunity Readiness Studio** — compare candidate evidence with explicit job requirements; inspect weighted status breakdowns and turn gaps into authored proof-of-work plans with completion checks. No callback probabilities. See the [evidence-planner design](docs/evidence-planner.md).
3. **Career Mobility Lab** — explore clearly labelled synthetic career transitions and salary scenarios.
4. **Job Description Diagnostic** — inspect clarity, completeness and consistency with traceable findings.

Initial working versions of all four tools and a landing page are implemented.
See [implementation status](docs/implementation-status.md) for tested capabilities,
limits and remaining release gates. Human review and the broader dataset remain pending.

The integrated release adds source-linked comparisons, editable diagnostic diffs,
private condition checklists and linked synthetic career cohorts. It has undergone
independent cross-review and a light editorial redesign with an orbital skill
sculpture, pointer-responsive depth and accessible motion controls. See the
[full review/acceptance trace](docs/platform-review.md) and
[visual system](docs/visual-system.md). Local verification passed 130 Python tests
(including actual PostgreSQL integration) and 30 browser/interaction checks.

The [Emil design-engineering pass](docs/design-engineering-pass.md) records the
installed skills and changes across the homepage, all four tools and methods.
Its production build and 36 browser checks passed, including accessibility,
keyboard, touch and loading-state coverage.

The [operations runbook](docs/operations-runbook.md) documents a real transactional
PostgreSQL reconciliation path and an idempotent saved-file refresh with quality,
hash and failure-recovery gates. This is separate from the public synthetic app;
live collection and public observed data remain disabled.

A [private human-review workbench](docs/human-review-workbench.md) now supports
per-record decisions, queue-bound checkpoint resume, category coverage, Wilson
intervals and private exports. Its publication checks require distinct reviewed
evidence and matching dataset/rule lineage. The prepared 100-record pilot queue
still has zero completed human decisions; no labels or real-market results are
invented. This workbench is excluded from the public deployment.

## Existing baseline features

1. **Market signal dashboard** — role counts, top skills, industries, work patterns, and skill trends.
2. **Role comparison** — Data Analyst, Business Analyst, BI Analyst, and Product Analyst requirements side by side.
3. **Skills evidence explorer** — normalised skills with example source language, frequency, and confidence.
4. **Proof-of-work planner** — candidate-selected skills are compared to market demand; the product recommends the next portfolio artefact rather than merely saying a skill is missing.
5. **Methodology page** — sources, collection date, deduplication, AI evaluation, coverage, and privacy limitations.

## Data strategy

Only authorised, documented sources will be used: official job-board APIs where permitted, public company careers APIs/feed endpoints, and user-provided CSV imports. The project does not directly scrape LinkedIn or Indeed pages. A user-approved Apify job export can be imported for private validation; see the source-onboarding guide for provenance, privacy and budget limits. Every observation retains source and URL, with source collection time when known and an explicit unknown otherwise. The dashboard does not claim comprehensive market coverage.

## Architecture

```text
Authorised job feeds / CSV imports
        ↓
Python ingestion + deduplication
        ↓
Evidence-preserving rule extraction and taxonomy normalisation
        ↓
Versioned CSV/JSON snapshots + reference SQL models
        ↓
React/Vite public demo + Python API; Streamlit internal workbench
```

The private PostgreSQL loader and SQL/Python reconciliation are now executable and
tested locally. A saved-fixture refresh and dormant rehearsal workflow are provided;
managed hosting and real scheduled collection remain pending. See [product strategy](docs/product-strategy.md),
[implementation status](docs/implementation-status.md), and [data governance](docs/data-governance.md).

The [master project description](PROJECT_DESCRIPTION.md) defines the scope and
acceptance criteria; [PROJECT_PLAN.md](PROJECT_PLAN.md) tracks delivery milestones.

## Current engine

The current implementation can ingest authorised job exports, deduplicate postings, classify 21 technology role families, preserve exact skill evidence, calculate sample-based demand metrics, and convert missing role skills into proof-of-work recommendations. Public publishing remains disabled until a real source snapshot has been manually reviewed and marked `validated`.

The validation workbench profiles missingness, duplicate rate, role coverage,
skill-evidence coverage, and employer concentration. It creates a reproducible
100-record human-review queue and reports extraction precision with a 95% confidence
interval. A `validated` label alone cannot unlock publication; the documented review
threshold must also pass.

The optional Adzuna connector retains a four-request ceiling, but its Ireland
endpoint returned HTTP 404 and coverage remains unverified. No live collection
runs automatically; local fixtures and saved snapshots support development.

### Run the automated checks

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

### Build a labelled market snapshot

After processing an authorised export, provide the generated job and evidence files:

```bash
PYTHONPATH=src python -m career_radar.build_snapshot \
  --jobs data/processed/jobs_normalised_TIMESTAMP.csv \
  --evidence data/processed/job_skill_evidence_TIMESTAMP.csv \
  --dataset-label "Source and collection-window description" \
  --data-status unreviewed
```

Use `validated` only after completing and documenting the manual extraction review described in [source onboarding](docs/source-onboarding.md).

See the source-onboarding guide for the `career_radar.validation prepare` and
`career_radar.validation score` workflow used to create and evaluate the review sample.

### Collect a broader Ireland tech sample

The next dataset targets approximately 200 unique postings across 21 tech role
families. Use the [bounded collection plan](docs/ireland-tech-collection.md) and
[Apify JSON input](config/apify-ireland-tech-pilot.json). No paid run is automatic.
Role-capped samples support skills comparisons, not estimates of occupation prevalence.

### Import a saved Apify pilot

```bash
PYTHONPATH=src python -m career_radar.apify_import \
  --input /path/to/export.json --output-dir data/raw/apify_pilot
```

This is a local import and spends no Apify credits. Follow
[source onboarding](docs/source-onboarding.md#user-provided-apify-json-exports)
for ingestion, review, snapshot creation and optional known collection-time metadata.
The dashboard includes a source-linked skills evidence explorer. Unclassified jobs
remain in sample-wide counts but are excluded from target-role recommendations.

### Run the web app

```bash
python -m pip install -r requirements-local.txt
PYTHONPATH=src streamlit run app.py
```

The app shows an empty setup state when no snapshot exists and a prominent non-public warning for `fixture` or `unreviewed` data.

The original market/evidence workbench remains available with `PYTHONPATH=src streamlit run market_app.py`. The Streamlit workbench entry is `app.py`; the Vercel web frontend is under `web/`.
