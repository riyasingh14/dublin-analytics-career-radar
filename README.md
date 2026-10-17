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
