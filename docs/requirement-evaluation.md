# Private requirement-extraction evaluation

This harness evaluates the shared rule-based requirement extractor used by
Diagnostic and Readiness. It prepares private annotation cases and scores
**human-written gold labels** against exact source spans. It never creates gold
labels, marks cases complete, approves a market release or claims a general
Diagnostic quality score.

A description can be analysed by working software without its extraction quality
having been measured. This workflow supplies the separate accuracy study once
current, authorised Irish descriptions and human annotations are available.

## Prepare a curated study

Choose a varied set of descriptions, initially around 10–20, with role families,
writing styles, explicit requirements/preferences, uncertain mentions, negations,
headings and descriptions with no recognised skills. Keep development and held-out
cases in separate files; do not tune rules on the held-out set and then describe
the same set as independent validation. Sampling choices and annotation guidance
must accompany any interpretation of the metrics.

Prepare reads a normalized UTF-8 CSV or JSON array. Required input fields are:

```text
source_job_id,title,description_text
```

An optional `role_name` must be a controlled role or `Unclassified`. If absent,
preparation uses the existing title classifier, falling back to `Unclassified`.
Role coverage therefore follows these supplied/derived role labels; it is not an
independent measurement of role-classification accuracy. Provide curated role
labels before preparation if that distinction matters to the study.

Only source ID, title, role and description are retained. Arbitrary imported
profile fields, candidate identifiers and private metadata are discarded.
Descriptions themselves are retained in full, so **do not use CVs, candidate
accounts, confidential documents or personal identifiers as inputs**. Use approved
job descriptions and keep source permission records separately.

From the repository root:

```bash
PYTHONPATH=src .venv/bin/python -m career_radar.requirement_evaluation prepare \
  --input data/validation/irish-requirement-study/jobs.csv \
  --output data/validation/irish-requirement-study/pending-cases.json
```

Every generated case starts with:

```json
{
  "review_status": "pending",
  "expected_requirements": []
}
```

Preparation does not call the extractor unless the optional, separate prediction
output is requested:

```bash
PYTHONPATH=src .venv/bin/python -m career_radar.requirement_evaluation prepare \
  --input data/validation/irish-requirement-study/jobs.json \
  --output data/validation/irish-requirement-study/pending-cases.json \
  --predictions-output data/validation/irish-requirement-study/machine-aid.json
```

The aid is explicitly `not_gold: true`, uses a different schema and cannot be
passed to `score` as ground truth. To reduce anchoring, annotate independently
before consulting machine predictions. Do not bulk-copy predictions and describe
those copies as a human accuracy study.

## Annotate complete descriptions

The gold document schema is `requirement-gold-v1`. Its annotation unit is
`all-skill-mentions`: label the recognised skill mentions and their context,
including preferred, uncertain and negated mentions, not just mandatory skills.
Each case freezes the original source ID, title, role, text and SHA-256 text hash.
Its deterministic case ID binds those source fields. Changing source text or
identity requires preparing a new case and reviewing its applicability again.

A human writes `expected_requirements` entries with **only** these fields:

```json
{
  "skill_id": "sql",
  "requirement_type": "required",
  "start": 2,
  "end": 5
}
```

This example refers to the fictional text `📊 SQL required. Python preferred.`:
`text[2:5]` is `SQL`. Offsets are **Python/Unicode code-point offsets**, with an
inclusive start and exclusive end. JavaScript UTF-16 offsets differ after emoji
or other supplementary characters; byte offsets differ too.

Use a skill ID from `data/reference/skills.csv` and one of:

- `required`: explicitly mandatory in context.
- `preferred`: explicitly desirable or optional.
- `uncertain`: mentioned without an unambiguous requirement classification.
- `negated`: explicitly not required in context.

Annotate the exact skill mention span, not an entire sentence or surrounding
qualifier. A gold span may identify a phrasing the current alias rules miss; the
harness deliberately does not require a machine-known alias, because doing so
would hide false negatives. Human judgement must still justify that skill label.
Repeated mentions at different offsets remain separate. Duplicate/conflicting
labels for one skill at the same span are rejected.

A case can retain working labels while `pending`; they are validated but excluded
from accuracy and category denominators. Set `review_status` to `completed` only
when the entire description has been checked, including potential misses. An
empty completed label list means the reviewer found **no relevant skill mentions**;
it does not mean the case has not been reviewed.

The harness cannot verify who performed the annotation, whether it was independent
or whether the labels are correct. Document the review process separately.

## Score a manually annotated copy

Save human work in a new private file, then run:

```bash
PYTHONPATH=src .venv/bin/python -m career_radar.requirement_evaluation score \
  --input data/validation/irish-requirement-study/annotated-cases.json \
  --output data/validation/irish-requirement-study/requirements-score-v1.json
```

Reports identify the current extraction/taxonomy versions and the source schema.
They include completed/pending case counts, completion fraction, exact-match
metrics, a requirement-type confusion table, role/category coverage and per-case
missed/spurious labels. Reports omit original descriptions, source phrases and
private imported metadata. The source gold file is still sensitive local input.

An exact true positive requires all four to agree:

```text
skill ID + start offset + end offset + requirement type
```

An unmatched prediction is a false positive; an unmatched gold label is a false
negative. A wrong type or span for the same mention therefore contributes one
false positive **and** one false negative. The type-confusion table compares
expected versus predicted types only where the skill and exact span match; span
misses/spurious mentions remain visible through FP/FN and per-case label lists.

Precision is `TP / (TP + FP)`, recall is `TP / (TP + FN)`, and F1 is
`2TP / (2TP + FP + FN)`. Metrics are ratios between 0 and 1, not percentages.
An undefined denominator produces JSON `null`, never an invented perfect score.
For example, with zero completed cases, counts are zero and all three accuracy
metrics are `null`. A completed zero-gold/zero-prediction case is still completed,
but its accuracy ratios are undefined rather than 100%.

Pending cases never affect accuracy. Per-role coverage includes their pending
counts; per-category coverage comes only from completed gold labels/predictions.
All controlled categories appear, including categories with zero reviewed gold.
The aggregate is micro-averaged over completed cases, not an average of per-case
percentages. Results describe the annotated sample, not every Irish description.

This score is **not**:

- The market publication gate for reviewed skill co-mentions.
- A validated score for Diagnostic clarity/completeness/consistency findings.
- A readiness callback probability or hiring-outcome estimate.
- Evidence that the chosen descriptions represent the Irish labour market.

`publication_approval` always remains `false`. A separate study would be needed to
measure broader Diagnostic findings, their severity, proposed clarifications or
candidate usefulness.

## File and resource boundaries

Use ignored `data/validation/` paths for inputs, annotations, aids and reports.
Nothing is sent to an external model, source API, analytics service or public
application. No network, paid collection or automatic publication occurs.

Inputs/outputs are bounded to 16 MiB, 200 cases, 30,000 Unicode characters per
description and 200 labels per case. Extractor resource limits still apply;
unsupported oversized cases fail rather than being silently truncated or skipped.
Use a curated study rather than pointing preparation at an entire large warehouse.

Unknown/future schema versions, extra gold fields, changed hashes/identities,
unknown skills/types/roles, duplicated cases/source IDs/text, invalid spans,
nonfinite or duplicate-key JSON, malformed CSV and future/naive creation timestamps
are rejected. Case/source duplicates are rejected to avoid treating repeated text
as independent study evidence. Symlinked input/output paths are rejected; existing
outputs are never overwritten. New JSON files use atomic no-replace promotion.
Gold and prediction aids must be separate files. These are integrity safeguards,
not authentication of human work.

## Python contract and checks

```python
from career_radar.requirement_evaluation import (
    prepare_requirement_cases,
    requirement_prediction_aid,
    score_requirement_cases,
)

pending = prepare_requirement_cases(normalized_job_rows)
# Human edits a private copy; no automated labels are supplied here.
report = score_requirement_cases(manually_annotated_document)
```

All tests in `tests/test_requirement_evaluation.py` use fictional descriptions and
explicitly test-authored labels. They cover no-auto-label preparation, Unicode
spans, exact TP/FP/FN, type confusion, empty/pending denominators, role/category
coverage, malformed inputs, source integrity, separate aids, CLI execution,
resource limits, symlinks and no-overwrite behaviour. Passing these software tests
does not supply any real annotated Irish examples.
