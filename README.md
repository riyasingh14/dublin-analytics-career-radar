# Dublin Analytics Career Radar

An AI-assisted labour-market intelligence tool for Dublin Data Analyst, Business Analyst, BI Analyst, and Product Analyst roles.

It does not try to replace a job board. It answers a different question: **which skills are in demand now, what evidence supports that conclusion, and what is the most valuable proof-of-work a candidate should build next?**

## The product gap

Job boards list vacancies. Enterprise labour-market platforms are expensive and opaque. This project focuses on a transparent, candidate-facing middle ground:

- Dublin-specific analytics-role demand and trends;
- AI-normalised skills with source evidence and confidence;
- comparison of target role, seniority, industry, and work pattern;
- a skill-gap view that turns a missing skill into a concrete portfolio or interview-proof action;
- published data freshness, coverage, and limitations.

## MVP features

1. **Market signal dashboard** — role counts, top skills, industries, work patterns, and skill trends.
2. **Role comparison** — Data Analyst, Business Analyst, BI Analyst, and Product Analyst requirements side by side.
3. **Skills evidence explorer** — normalised skills with example source language, frequency, and confidence.
4. **Proof-of-work planner** — candidate-selected skills are compared to market demand; the product recommends the next portfolio artefact rather than merely saying a skill is missing.
5. **Methodology page** — sources, collection date, deduplication, AI evaluation, coverage, and privacy limitations.

## Data strategy

Only authorised, documented sources will be used: official job-board APIs where permitted, public company careers APIs/feed endpoints, and user-provided CSV imports. The project will not scrape LinkedIn or Indeed pages. Every observation will retain source, URL, and collection timestamp so the dashboard never claims comprehensive market coverage.

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

The implementation roadmap and completion criteria are tracked in [PROJECT_PLAN.md](PROJECT_PLAN.md).

## Current engine

The current implementation can ingest authorised job exports, deduplicate postings, classify the four target roles, preserve exact skill evidence, calculate sample-based demand metrics, and convert missing role skills into proof-of-work recommendations. Public publishing remains disabled until a real source snapshot has been manually reviewed and marked `validated`.

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

### Run the web app

```bash
python -m pip install -r requirements.txt
PYTHONPATH=src streamlit run app.py
```

The app shows an empty setup state when no snapshot exists and a prominent non-public warning for `fixture` or `unreviewed` data.
