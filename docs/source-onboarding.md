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

This writes normalised jobs and evidence records to `data/processed/`. The output includes source ID, URL, collection timestamp, exact matched phrase, rule version, and confidence. It also writes an ingestion manifest containing the source-row count, duplicate count, unique-job count, and extraction version.

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

## Adzuna Ireland API

The project also supports the official Adzuna Ireland API. Create an Adzuna developer application, review the current API terms for your intended portfolio use, then save the application values as secure environment variables—not in a file or Git history:

```bash
export ADZUNA_APP_ID="..."
export ADZUNA_APP_KEY="..."
PYTHONPATH=src python -m career_radar.adzuna --terms-checked-on 2026-10-12
PYTHONPATH=src python -m career_radar.ingest \
  --input data/raw/adzuna_dublin_jobs.csv \
  --source-name "Adzuna Ireland API"
```

The connector targets Dublin and the four MVP role queries, deduplicates repeated results across queries, and writes the original source URL and collection timestamp into downstream outputs.

### Zero-budget collection policy

The default run fetches one page for each of the four target roles: four API requests
in total, with up to 50 results returned per request. The connector enforces a hard
`--max-requests 4` ceiling so increasing the page count fails before any request is
made. Run the collection weekly, keep the dated processed snapshot, and use fixtures
for development rather than repeatedly calling the live API. If the account's current
Adzuna allowance is lower, reduce the queries or ceiling to match it.

Greenhouse company career feeds are the preferred no-cost supplementary source, but
only boards recorded in `data/reference/greenhouse_sources.csv` after a terms review
may be collected. We do not scrape general job sites to increase volume.

## Validation before publishing insights

- Verify source reuse permission and log the check date.
- Review the source count, Dublin coverage, and duplicate rate.
- Manually check at least 100 extracted skills before reporting precision.
- Display collection date, source coverage, and sample size beside all dashboard metrics.

Prepare a reproducible, category-balanced review queue and quality profile:

```bash
PYTHONPATH=src python -m career_radar.validation prepare \
  --jobs data/processed/jobs_normalised_TIMESTAMP.csv \
  --evidence data/processed/job_skill_evidence_TIMESTAMP.csv \
  --source-row-count SOURCE_ROWS \
  --sample-size 100
```

Open `data/validation/extraction_review.csv` and label each row `accepted` or
`rejected`. Use the source phrase, surrounding context, and source URL rather than
guessing from the normalised skill alone. Then calculate the evaluation:

```bash
PYTHONPATH=src python -m career_radar.validation score \
  --review-file data/validation/extraction_review.csv
```

The result reports overall and category precision, a 95% Wilson confidence interval,
and whether the project's minimum of 100 reviews at 90% precision has been met. A
snapshot is publishable only when this evaluation is attached and the dataset is
explicitly labelled `validated`.

```bash
PYTHONPATH=src python -m career_radar.build_snapshot \
  --jobs data/processed/jobs_normalised_TIMESTAMP.csv \
  --evidence data/processed/job_skill_evidence_TIMESTAMP.csv \
  --evaluation data/validation/extraction_evaluation.json \
  --source-row-count SOURCE_ROWS \
  --dataset-label "Source and collection window" \
  --data-status validated
```
