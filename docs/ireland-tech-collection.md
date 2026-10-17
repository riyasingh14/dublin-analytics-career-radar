# Ireland tech pilot: approximately 200 unique postings

The product now covers a broader technology-career sample across the Republic of
Ireland. Dublin is a separate view; country-only/remote Ireland listings remain
location-unspecified rather than being assigned outside Dublin. Northern Ireland
is outside this pilot's geographic scope. Keep the repository name for continuity.

## One bounded collection

Use `config/apify-ireland-tech-pilot.json` as the JSON input to
`bebity/linkedin-jobs-scraper`. It specifies 21 job-title searches, Ireland as the
single location, the past month, 15 results per search, and no company or paid
contact enrichment. Confirm the actor form shows **Past month** before starting.
The maximum requested result count is 315, before cross-search deduplication.
This is deliberate headroom toward approximately 200 unique postings, not a
promise of 200 results or 200 distinct occupations. Some searches may be empty.

The queries cover software, frontend, backend, full stack, mobile, embedded,
QA/testing, DevOps/SRE/platform, cloud, security, networks, IT support, architecture,
data engineering, data science, machine learning, data analysis, business analysis,
BI and product management/analysis. They do not exhaust every tech occupation.

Set the run's **maximum total charge to US$1** in Apify run options (not the Actor
input). Check the current pricing panel and remaining account credit first. At the
advertised starting base price of US$1 per 1,000 results, 315 results would be about
US$0.315; actual prices may differ. The overall user budget remains US$10 including
the earlier pilot, whose cost has not been supplied. Do not schedule repeat runs or
retry automatically. Export the completed dataset as JSON, and record the actual
run ID, collection timestamp with timezone, actual result count and actual charge.
No paid run is started by this repository configuration or by the import commands.

## Import and review

```bash
PYTHONPATH=src python -m career_radar.apify_import \
  --input /path/to/ireland-export.json \
  --scope ireland --output-dir data/raw/ireland_tech_pilot
PYTHONPATH=src python -m career_radar.ingest \
  --input data/raw/ireland_tech_pilot/jobs.csv \
  --source-name "LinkedIn via user-provided Apify export" \
  --output-dir data/processed/ireland_tech_pilot
```

Add `--collected-at` and `--run-id` to the first command only when known from the
actual run. The import validates location and job fields and excludes recruiter
profiles. A rejected record stops import for location/data review rather than
silently expanding geography. Duplicate URLs and identical job content are removed
by ingestion; the manifest reports raw rows and duplicates.

Use the timestamped files written above in the validation and snapshot commands:

```bash
PYTHONPATH=src python -m career_radar.validation prepare \
  --jobs data/processed/ireland_tech_pilot/jobs_normalised_TIMESTAMP.csv \
  --evidence data/processed/ireland_tech_pilot/job_skill_evidence_TIMESTAMP.csv \
  --source-row-count ACTUAL_EXPORTED_ROWS --sample-size 100 \
  --output-dir data/validation/ireland_tech_pilot
PYTHONPATH=src python -m career_radar.build_snapshot \
  --jobs data/processed/ireland_tech_pilot/jobs_normalised_TIMESTAMP.csv \
  --evidence data/processed/ireland_tech_pilot/job_skill_evidence_TIMESTAMP.csv \
  --source-row-count ACTUAL_EXPORTED_ROWS \
  --provenance data/raw/ireland_tech_pilot/provenance.json \
  --dataset-label "Ireland tech pilot; selected title searches" \
  --data-status unreviewed \
  --output data/processed/ireland_tech_pilot/market_snapshot.json
CAREER_RADAR_SNAPSHOT=data/processed/ireland_tech_pilot/market_snapshot.json \
  PYTHONPATH=src streamlit run app.py
```

Use actual paths/counts in place of TIMESTAMP and ACTUAL_EXPORTED_ROWS. Keep raw,
processed, and validation artifacts out of Git. Source authorisation is based on
the user's review; independent LinkedIn authorisation has not been established.

## What the sample can support

A title-capped convenience sample is useful for comparing observed skill mentions
and portfolio requirements across roles. It cannot estimate occupation prevalence
or rank Ireland's most common tech jobs: search choices, caps, ranking, employers
and posting dates affect the result. Report classified counts, unclassified titles,
location, extraction version, employer concentration, source coverage and missing
fields before deciding whether any targeted follow-up collection is useful.

The expanded 64-skill taxonomy is a deterministic baseline, not a complete list of
tech skills. Its version is `taxonomy-v2-tech`; role rules are `roles-v2-tech`.
Numerical rule confidence is a heuristic, not measured probability. Rebuild and
review the new evidence rather than reusing a precision score from the old taxonomy.
At least 100 human-labelled skill-evidence records and 90% precision remain the
minimum publication gate. Rare role groups with only a few postings cannot support
strong role-specific conclusions even if that overall threshold is met. Keep all
new snapshots unreviewed until review is complete; do not deploy the data yet.
