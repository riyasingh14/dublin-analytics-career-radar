# Dublin Analytics Career Radar

An evidence-backed labour-market intelligence tool for technology careers across Ireland, with Dublin shown separately. The expanded scope covers 21 role families and retains the original analytics workflow.

It does not try to replace a job board. It answers a different question: **which skills are in demand now, what evidence supports that conclusion, and what is the most valuable proof-of-work a candidate should build next?**

## The product gap

Job boards list vacancies. Enterprise labour-market platforms are expensive and opaque. This project focuses on a transparent, candidate-facing middle ground:

- Ireland-wide technology skill evidence, with Dublin shown separately;
- AI-normalised skills with source evidence and confidence;
- comparison of target role, seniority, industry, and work pattern;
- a skill-gap view that turns a missing skill into a concrete portfolio or interview-proof action;
- published data freshness, coverage, and limitations.

## Selected product scope

The complete specification is in **[PROJECT_DESCRIPTION.md](PROJECT_DESCRIPTION.md)**.
It defines four flagship experiences, their calculations, user journeys, visual
requirements, data controls and acceptance criteria. The existing market dashboard
is their shared analytical foundation.

1. **Skill Constellation** — inspect skill co-mentions and associations with source evidence.
2. **Opportunity Readiness Studio** — compare candidate evidence with explicit job requirements; no callback probabilities.
3. **Career Mobility Lab** — explore clearly labelled synthetic career transitions and salary scenarios.
4. **Job Description Diagnostic** — inspect clarity, completeness and consistency with traceable findings.

These complete flagship experiences are planned. The baseline features below
provide reusable components; they are not claims that the four modules are finished.

## Existing baseline features

1. **Market signal dashboard** — role counts, top skills, industries, work patterns, and skill trends.
2. **Role comparison** — Data Analyst, Business Analyst, BI Analyst, and Product Analyst requirements side by side.
3. **Skills evidence explorer** — normalised skills with example source language, frequency, and confidence.
4. **Proof-of-work planner** — candidate-selected skills are compared to market demand; the product recommends the next portfolio artefact rather than merely saying a skill is missing.
5. **Methodology page** — sources, collection date, deduplication, AI evaluation, coverage, and privacy limitations.

## Data strategy

Only authorised, documented sources will be used: official job-board APIs where permitted, public company careers APIs/feed endpoints, and user-provided CSV imports. The project does not directly scrape LinkedIn or Indeed pages. A user-approved Apify job export can be imported for private validation; see the source-onboarding guide for provenance, privacy and budget limits. Every observation will retain source, URL, and collection timestamp so the dashboard never claims comprehensive market coverage.

## Architecture

```text
Authorised job feeds / CSV imports
        ↓
Python ingestion + deduplication
        ↓
AI skill extraction and taxonomy normalisation
        ↓
PostgreSQL analytical model + weekly snapshots
        ↓
Streamlit web app: signals, evidence, and proof-of-work plans
```

See [product strategy](docs/product-strategy.md) and [data governance](docs/data-governance.md).

The [master project description](PROJECT_DESCRIPTION.md) defines the scope and
acceptance criteria; [PROJECT_PLAN.md](PROJECT_PLAN.md) tracks delivery milestones.

## Current engine

The current implementation can ingest authorised job exports, deduplicate postings, classify 21 technology role families, preserve exact skill evidence, calculate sample-based demand metrics, and convert missing role skills into proof-of-work recommendations. Public publishing remains disabled until a real source snapshot has been manually reviewed and marked `validated`.

The validation workbench profiles missingness, duplicate rate, role coverage,
skill-evidence coverage, and employer concentration. It creates a reproducible
100-record human-review queue and reports extraction precision with a 95% confidence
interval. A `validated` label alone cannot unlock publication; the documented review
threshold must also pass.

Live Adzuna collection defaults to a zero-budget four-request weekly run. A hard
request ceiling prevents accidental high-volume API use; local fixtures and saved
snapshots are used for development.

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
python -m pip install -r requirements.txt
PYTHONPATH=src streamlit run app.py
```

The app shows an empty setup state when no snapshot exists and a prominent non-public warning for `fixture` or `unreviewed` data.
