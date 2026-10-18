# Saved-file refresh and executable PostgreSQL warehouse

This is an analyst operations path, separate from the public synthetic Vercel demo.
It makes **no network collection calls**, spends **US$0**, creates **no human review
labels** and never promotes observed data to public release. The existing public
application continues to load its synthetic fixtures; it does not read
`latest_good.json` or connect to PostgreSQL.

## Reproduce the saved-file run

From the repository root (Python 3.12; standard library only):

```bash
PYTHONPATH=src .venv/bin/python -m career_radar.refresh \
  --input tests/fixtures/authorised_sample_jobs.csv \
  --policy config/refresh-fixture.json \
  --output-dir data/processed/refresh-rehearsal
```

The committed fixture is fictional, with one duplicate: four input rows become
three unique postings. The policy is explicitly `fixture`, not a source permission
claim. An immutable `runs/<run_id>/` directory contains normalized jobs, exact
skill evidence, an unlabelled review queue, quality profile, provenance-labelled
snapshot and manifest with SHA-256 artefact hashes. The atomic `latest_good.json`
pointer changes only after every artefact is complete and quality gates pass.

The manifest records source/input/taxonomy hashes, collection week in
`Europe/Dublin`, pipeline/extraction versions, counts, duplicate removals,
`human_review_status=not_completed`, zero requests, zero spend and
`publish_allowed=false`. The quality profile includes missingness, role coverage,
employer concentration, skill-evidence coverage and conservative geography counts.
Locations without an explicit Ireland country indication remain unknown/outside
scope; the runner does not silently infer Dublin from an incomplete field.

Repeated identical source/input/taxonomy/policy/week is a no-op after verifying all
artefact hashes. A retry recovers a crash between completed-directory promotion
and pointer replacement. It selects the newest verified collection, so retrying an
older run cannot roll the pointer back. Local wall-clock generation timestamps and
byte hashes may differ when rebuilding the same semantic run in a fresh directory;
the warehouse retains its original immutable load and rechecks the metrics.

## Observed saved exports

Supported inputs are UTF-8 CSV or a JSON array using the normalized CSV columns:
`source_job_id`, `canonical_url`, `title`, `employer_name`, `location_text`,
`description_text`, optional `posted_at`. This is not a universal actor-response
parser: first use the existing reviewed import adapter for an approved source.
Unknown input metadata is dropped. Input is capped at 20 MiB and 10,000 rows.

Create an **ignored local** copy of the policy under `data/validation/`, set
`dataset_kind=observed`, the source name/homepage, actual terms review date, and
the owner's collection permission attestation. Pass the actual source collection
timestamp via `--collected-at`, including its timezone. The runner does not review
terms itself or fill the terms date automatically. Review applicability to reuse
and public display remains an owner responsibility.

The runner rejects missing permission, missing/future terms dates, future/naive
collection timestamps, missing identity fields, inconsistent IDs, unknown input
types, and quality failures. Explicit quality policy controls minimum unique
postings, maximum description missingness and maximum employer share. Changed
observed input for the same source/Dublin ISO week is rejected; identical input is
idempotent. Changing a source name to bypass this guard is not permitted policy.

Both `max_live_requests` and `max_spend_usd` must be zero;
`live_collection_enabled` must be false. There is no HTTP client or live connector
invocation. A future live integration needs separate source/display permission,
confirmed remaining credit, price and request caps, and recurring spend approval.
The existing Adzuna four-request limit and overall Apify US$10 cap are unaffected.

Observed data always stays **unreviewed**, even when `display_authorized=true` is
attested. A completed human review and applicable publication evaluation remain
separate gates. Never commit raw/processed/review data or set review labels just to
clear a release gate.

## PostgreSQL setup and loader

Use a dedicated PostgreSQL 17 analyst/test database. Install the optional client
dependency; it is deliberately excluded from the public Vercel dependency file:

```bash
.venv/bin/python -m pip install -r requirements-sql.txt
```

Set `CAREER_RADAR_DATABASE_URL` through your environment/secret manager. Never
paste a real DSN into chat, commit it, or put it in command-line arguments.
For a remote database require TLS certificate and hostname verification
(`sslmode=verify-full` plus the provider's trusted root certificate). This runner
passes connection options through unchanged and never disables hosted TLS.

```bash
PYTHONPATH=src .venv/bin/python -m career_radar.warehouse \
  --run-dir data/processed/refresh-rehearsal/runs/REPLACE_WITH_RUN_ID \
  --people 100 --years 5 --seed 42 \
  --report data/processed/refresh-rehearsal/warehouse-report.json
```

The entire load and SQL/Python reconciliation is one transaction. A mismatch
rolls back the load. Identical runs/scenarios are loaded once and reconciled on
each repeat. The loader verifies every derived artefact's hash and the extraction
taxonomy hash before opening a write transaction. SQL parameters are bound;
the connection value and database exception text are not printed by the CLI.

SQL objects are created by `sql/30_operations_schema.sql` in the independent
`career_radar_ops` schema. The older reference schema/worksheets in `sql/00`, `10`
and `20` are retained; the operational loader does not mutate their tables.

| Object | Grain / responsibility |
| --- | --- |
| `analysis_run` | One immutable source/input/taxonomy/policy/week identifier; private status and original load manifest |
| `posting` | One unique canonical URL per run; includes postings with no extracted skills; run/source ID and dedup key constrained |
| `skill_evidence` | One run, posting, skill, exact phrase and extraction version; every record unreviewed |
| `posting_skill` | Distinct posting/skill projection, preventing mention multiplication |
| `pair_metrics` | One run and lexically ordered skill pair; support, Jaccard and lift use all postings in that run |
| `requirement` | One run/posting/requirement ID; required/preferred/uncertain/negated classification and exact source offsets |
| `synthetic_scenario` | One independent deterministic scenario hash; assumptions and synthetic label |
| `synthetic_spell` | One scenario/person/spell; positive-duration annual intervals; EUR annual base FTE |
| `synthetic_transition` | One adjacent spell pair per scenario/person, with employer/occupation/industry/level changes and career breaks |
| `synthetic_cohort_metrics` | One scenario/transition category; transition-weighted metrics, suppressing salary comparisons below 20 valid pairs |

Posting runs and synthetic scenarios have **no joining key**. Salary movements
are fictional scenario outputs, not observed Irish salaries or causal estimates.
Every event and cohort retains its synthetic label and generator version.
The two salary measures remain separate: median individual percentage change
versus percentage change between cohort medians. Careers can contribute multiple
events; people counts and event counts are reported separately. Career-break
pairs and invalid/nonfinite salaries are excluded from salary comparisons.

The loader reconciles posting sample size; every skill pair's joint and marginal
counts, support, Jaccard and lift; requirement-type counts and exact SQL substring
offsets; all synthetic transition identities, categories, source/destination,
geography, valid-pair flags, before/after salaries and individual changes; and
cohort denominators, medians, decreases and sparse-cohort suppression.

## Verification performed

On 18 October 2026, an actual PostgreSQL **17.11** instance was initialized from
the official Debian 13 server/client packages extracted inside the writable
workspace. It ran with **Unix socket only and no TCP listener**. No hosted database,
paid infrastructure or external collection was used. Package downloads retained
HTTPS certificate checks. The application dependency remained optional psycopg3.

For a restored task in **this existing cloud workspace**, the initialized cluster
and extracted binaries are outside the repository. Restart only that existing
cluster with:

```bash
bash /workspace/.onboarding/career-radar/postgresql/start.sh
```

The helper first checks `pg_ctl status`; an already-running server is left alone.
Its startup command uses the extracted `root/usr/lib/postgresql/17/bin/pg_ctl`,
cluster directory `/workspace/.onboarding/career-radar/postgresql/cluster`, Unix
socket directory `/workspace/.onboarding/career-radar/postgresql/socket` (mode
0700), port 55432, empty listen address (`-h ''`) and
`dynamic_library_path=/workspace/.onboarding/career-radar/postgresql/root/usr/lib/postgresql/17/lib`.
Debian 13 runtime libraries resolve normally; no custom dynamic loader is needed.
It does not download packages, initialize a new cluster or alter authentication.
The matching local test connection is:

```bash
export CAREER_RADAR_TEST_DATABASE_URL='host=/workspace/.onboarding/career-radar/postgresql/socket port=55432 user=career_radar dbname=postgres'
```

That connection contains no password and is only for the isolated local fixture
database. A fresh clone elsewhere needs its own PostgreSQL instance; the helper
and ignored cluster are workspace setup artefacts, not repository dependencies.

The fictional fixture reconciled **3 postings, 21 skill pairs, 12 requirement
spans**, plus **500 synthetic spells, 400 adjacent transitions and 12 transition
cohorts** for 100 people/five years/seed 42. The following meaningful checks passed:

- 13 refresh tests: deduplication, idempotence, zero requests/spend, unlabelled
  reviews, safe failure logs, quality failure retaining last good, crash recovery,
  corruption rejection, no rollback to older runs, locking, Dublin week boundary,
  required permission/terms/timestamps, weekly guard and normalized JSON import.
- 4 actual PostgreSQL integration tests: metric and repeat-load reconciliation;
  no-skill denominator, required/preferred/negated spans and sparse salary cohorts;
  rejection of tampered artefacts before database writes; forced source-span
  reconciliation failure rolling back an otherwise new database load.

Reproduce in a dedicated database with `CAREER_RADAR_TEST_DATABASE_URL` configured:

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -p test_refresh.py -v
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -p test_postgres_integration.py -v
```

The PostgreSQL tests skip explicitly when that variable is absent; a skipped test
must not be reported as an executed PostgreSQL check. The separate
`warehouse.yml` GitHub Actions workflow provisions an ephemeral PostgreSQL 17
service and executes both suites. Remote CI completion still needs verification
after push. Its test-only password and `sslmode=disable` apply solely to its
localhost service; they are not hosted database configuration.

## Weekly rehearsal and failures

`saved-refresh-rehearsal.yml` provides a manual synthetic-fixture rehearsal.
Its Monday 08:00 UTC schedule is dormant unless the owner sets repository variable
`ENABLE_FIXTURE_REFRESH=true`. That means 08:00 Dublin winter or 09:00 Dublin
summer. It uploads only a fictional fixture artefact, expires it after seven
days, and never commits files, calls a source API, runs an actor, updates a hosted
database, deploys the website or changes a public data pointer. This rehearses
pipeline health; it is **not a weekly current-vacancy feed**. The workflow schedule
has been configured but not enabled or remotely verified in this build.

For a rejected refresh, inspect the safe reason in `failures/*.json`, fix the
source/policy/quality issue and rerun. Last-good files remain in place. Corrupt
artefacts must be investigated rather than manually editing manifest hashes.
A lock prevents simultaneous writers. Following a hard process crash, confirm
no refresh process is active before removing the empty `.refresh.lock` directory;
staging folders may be removed after that check. The runner does not guess a lock
is stale. A backfill does not replace a newer valid pointer.

All local outputs belong under ignored `data/processed/` or `data/validation/`.
Promotion to a public observed-data release, durable managed PostgreSQL hosting,
real weekly collection, budget monitoring/alerts and source authorization remain
external operational prerequisites. This implementation does not claim those
services are live.
