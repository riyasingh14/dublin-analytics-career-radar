# Source onboarding

## Approved input paths

1. A CSV export that the user is authorised to use.
2. An official job-board API used according to its terms.
3. A public company careers API/feed after its reuse terms are checked and recorded.

Do not use LinkedIn or Indeed page scraping.

## Required CSV columns

```text
source_job_id,canonical_url,title,employer_name,location_text,description_text,posted_at
```

`posted_at` is optional. All other fields are required. Keep the source export unchanged in `data/raw/`, which is intentionally excluded from version control.

## First-run command

```bash
PYTHONPATH=src python -m career_radar.ingest \
  --input data/raw/authorised_jobs.csv \
  --source-name "Documented authorised source"
```

This writes normalised jobs and evidence records to `data/processed/`. The output includes source ID, URL, collection timestamp, exact matched phrase, rule version, and confidence.

## Approved Greenhouse sources

The project includes a connector for Greenhouse's public job-board feed. It is intentionally disabled until a reviewer records each approved source in `data/reference/greenhouse_sources.csv`:

```text
source_name,source_home_url,board_token,terms_checked_on,active
Example company,https://careers.example.com,example-board-token,2026-10-12,true
```

Only add a board after confirming its public careers feed and reuse terms are suitable for this portfolio project. Then export Dublin postings and process them:

```bash
PYTHONPATH=src python -m career_radar.greenhouse
PYTHONPATH=src python -m career_radar.ingest \
  --input data/raw/greenhouse_jobs.csv \
  --source-name "Approved Greenhouse sources"
```

## Validation before publishing insights

- Verify source reuse permission and log the check date.
- Review the source count, Dublin coverage, and duplicate rate.
- Manually check at least 100 extracted skills before reporting precision.
- Display collection date, source coverage, and sample size beside all dashboard metrics.
