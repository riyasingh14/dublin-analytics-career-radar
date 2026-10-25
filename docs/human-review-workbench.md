# Private human evidence review

This workbench closes the manual annotation gap in the data-release workflow.
It is an internal Streamlit tool, separate from the four public website tools.
It makes no source API calls, writes no labels for the reviewer, and never
publishes or changes the status of a snapshot.

## Start a review

The prepared private pilot queue is:
`data/validation/pilot-review-2026-10-25/extraction_review.csv`.
It contains 100 unlabelled evidence records from the existing 32-job pilot. No new
jobs were collected and no human review has been completed by this build. The
queue, quality report and initial evaluation are ignored by Git and excluded from
Vercel uploads. They exist only in this workspace; a fresh checkout needs its own
authorised data or the synthetic test fixtures.

From the repository root:

```bash
CAREER_RADAR_REVIEW_QUEUE=data/validation/pilot-review-2026-10-25/extraction_review.csv \
PYTHONPATH=src .venv/bin/python -m streamlit run review_app.py \
  --server.address=127.0.0.1 --server.port=8504 --server.maxUploadSize=4 \
  --server.headless=true --browser.gatherUsageStats=false
```

Alternatively, start the workbench without the variable and upload a prepared
review CSV. Keep this process private; it has no multiuser authentication. The
cloud onboarding UI does not provide a supported localhost preview, so use your
own local checkout for interactive access or download/review the CSV offline.

1. Inspect the skill name, exact extracted phrase, context, source identity,
   extraction method and version.
2. Record **accepted** for a correctly extracted skill mention, **rejected** for
   an incorrect extraction, or **uncertain** when context is insufficient. A
   correct mention is not necessarily a mandatory job requirement.
3. Press **Save decision**. There is no batch-accept control. Unsaved form inputs
   are not included in exports; save before navigating or filtering.
4. Inspect completed counts, category coverage, precision and the Wilson interval.
   Uncertain and unreviewed records are excluded from the precision denominator.
5. Download a checkpoint before ending the session. Resume by loading the original
   queue and restoring its checkpoint. A source/rule/context change invalidates
   the checkpoint; reordering an unchanged queue does not.

The CSV includes source excerpts and notes. Checkpoints include decisions and
notes. The evaluation JSON contains counts, versions and hashes, without source
excerpts or review notes. All should be handled as private working artefacts.
Clear session removes the tool's state and does not reload a configured file
automatically. Downloaded files remain on the reviewer's device.

## Prepare another dataset

```bash
PYTHONPATH=src .venv/bin/python -m career_radar.validation prepare \
  --jobs data/processed/your-jobs.csv \
  --evidence data/processed/your-evidence.csv \
  --output-dir data/validation/your-review --sample-size 100 --seed 42
```

Sampling is deterministic and category-balanced. The queue records a fingerprint
of its complete input dataset and the population's extraction versions/categories.
The private UI supports UTF-8 CSV up to 4 MiB, 1,000 records and 1,000-character
notes. Only known review fields are retained. No arbitrary imported profile/token
fields enter exports.

For offline review, fill `reviewer_label` with accepted/rejected or leave it blank.
If an exported file has `review_status`, keep it consistent with the label:
uncertain/unreviewed must have a blank label. Keep immutable source columns intact.

```bash
PYTHONPATH=src .venv/bin/python -m career_radar.validation score \
  --review-file data/validation/completed-review.csv \
  --output data/validation/extraction_evaluation.json
```

## What the release gate now checks

- At least 100 distinct labelled evidence records; duplicate review IDs or
  posting/skill/version identities cannot inflate the count.
- At least 90% accepted records **before rounding**. A displayed 90.0% that is
  actually below 90% does not pass.
- At least one completed review for every extraction version and category listed
  in the queue's population metadata. This minimum coverage does not establish
  accuracy for every category, skill or role.
- A v2 evaluation with complete lineage and a matching dataset fingerprint.
- Distinct reviewed evidence hashes/counts must belong to the actual snapshot
  inputs, including the displayed skill label, source phrase, context and method.
  Copying a dataset token onto edited evidence cannot make it applicable.
- The snapshot still needs an explicit `validated` status. An unreviewed snapshot
  remains unpublished even when an applicable numeric threshold is met.

A bare `publication_threshold_met: true` flag or an evaluation from another
dataset cannot unlock a snapshot. Older labelled CSVs can still be inspected and
scored, but incomplete lineage keeps their publication gate closed. Regenerate a
queue from the intended inputs and recheck applicability rather than adding a
passing flag. Existing immutable refresh runs retain their original queue;
`validation prepare` creates a new review workspace without recollecting jobs or
modifying that run.

These checks detect accidental reuse and inconsistent evidence, not forged human
decisions by an owner who can edit local files. Reviewer identity is not
authenticated. Wilson intervals assume independent records; category balancing
and multiple skills from one posting limit population generalisation. Precision
does not measure recall, market coverage, requirement accuracy, source display
permission, or hiring outcomes. Permission and other release checks remain
separate, and the public API continues to use its synthetic fixtures.
