# Approved public-data releases

This operator workflow prepares a bounded, immutable bundle from already ingested
and human-reviewed Irish job postings. It makes no network calls, spends no money,
creates no review decisions and does not publish or deploy anything. Default public
operation remains the fictional demo until the explicit release selector is set.

## Before preparation

1. Use only approved sources and retain the actual collection window, terms-review
   date and permission to display full descriptions and exact evidence publicly.
   Collection permission alone does not imply redistribution permission.
2. Deduplicate the normalized postings. Preserve all unique jobs, including jobs
   without extracted skills, so the denominator remains correct. Do not replace
   unknown posting dates with collection or generation dates.
3. Produce a human-labelled extraction evaluation for this exact posting/evidence
   dataset and rule version. The current gate is at least 100 distinct reviewed
   evidence records, at least 90% precision before rounding and review coverage of
   every extraction version and skill category. Dataset and evidence fingerprints
   must match. These are evidence records, not a requirement for 100 separate jobs.
4. Have the owner explicitly approve the release and its source/display scope.
   Keep permission correspondence and private reviewer notes outside the bundle.

The gate validates dataset applicability and numeric policy. It cannot establish
that supplied human labels are genuine, that an operator has legal authority, or
that a source sample represents the whole Irish market. Those remain review tasks.
Hashes detect changed artefacts, not a malicious operator who rewrites all evidence
and approvals. The runtime must read only a deployment-owned approved directory.

## Input contract

Normalized posting CSV fields:

```text
source_job_id,canonical_url,title,employer_name,location_text,description_text,posted_at,source_name,role_name,work_pattern
```

`posted_at` may be empty. All other fields must be nonempty; use `Unclassified`
for an explicitly unknown role and `unknown` for a work pattern. Roles otherwise
must match the current controlled role taxonomy. Every location must explicitly
identify Ireland; Dublin, other named Irish locations and country-only Irish
listings are retained as separate geography groups. Belfast/outside/unknown
locations are rejected from this Ireland-scoped release.

Evidence CSV fields:

```text
canonical_url,skill_id,skill_name,category,source_phrase,extraction_method,extraction_version
```

Evidence must point to a released posting and match the current controlled
extractor's exact phrase, skill ID/name/category/method/version. No duplicate
posting IDs/URLs/content or duplicate posting/skill/version identities are allowed.
Input extras such as imported profile fields and reviewer notes are discarded at
preparation; extras added to the resulting public snapshot/manifest are rejected
at verification. Descriptions themselves still require an appropriate content and
privacy review; a field allowlist is not a personal-data detector.

The policy JSON has exactly this shape. This deliberately incomplete template
**will fail** until actual dates, permitted sources and owner approvals are supplied:

```json
{
  "schema_version": "approved-public-release-v1",
  "release_id": "ireland-weekly-REPLACE",
  "dataset_label": "REPLACE WITH AN ACCURATE SAMPLE LABEL",
  "published_at": null,
  "collected_from": null,
  "collected_through": null,
  "expires_at": null,
  "geographic_scope": "Ireland",
  "owner_approved": false,
  "sources": [{
    "source_name": "EXACT SOURCE NAME USED BY POSTINGS",
    "homepage_url": "https://REPLACE.invalid/",
    "terms_url": "https://REPLACE.invalid/terms",
    "terms_reviewed_on": null,
    "collected_from": null,
    "collected_through": null,
    "collection_authorized": false,
    "public_display_authorized": false,
    "permission_basis": "REPLACE WITH A NONPRIVATE, FACTUAL PERMISSION SUMMARY"
  }]
}
```

Use a lowercase letters/numbers/hyphens release ID, at most 63 characters. Use
ISO timestamps **with a timezone** for all timestamp fields, and `YYYY-MM-DD` for
the real terms-review date. Source terms dates must not follow collection. Source
names must exactly cover all released source names, without duplicates or unused
sources; the top-level collection window must equal the union of source windows.
Publication cannot precede collection or lie in the future. Expiry must follow the
current time and be no later than 31 days after publication. It is rechecked on
every load. Stated collection dates remain visible even during that interval.

Source/posting/terms URLs must use ordinary HTTPS and contain no embedded login,
control characters, localhost/private IP targets or known API credential parameters
in queries or fragments. Do not paste tokens,
passwords or private owner identity details into the policy.

## Prepare and verify locally

Keep actual inputs and bundles in ignored local paths. Run from the repository
root after replacing the policy with reviewed facts:

```bash
PYTHONPATH=src .venv/bin/python -m career_radar.approved_release prepare \
  --jobs data/processed/chosen-run/jobs.csv \
  --evidence data/processed/chosen-run/skill_evidence.csv \
  --evaluation data/validation/chosen-run/extraction_evaluation.json \
  --policy data/validation/chosen-run/public_release_policy.json \
  --output data/releases/ireland-weekly-2026-REPLACE

PYTHONPATH=src .venv/bin/python -m career_radar.approved_release verify \
  --bundle data/releases/ireland-weekly-2026-REPLACE
```

Adjust filenames to the actual saved run. The preparer refuses existing output,
writes into a temporary sibling, verifies it, then promotes the whole directory.
Each directory contains exactly two fixed files:

- `manifest.json`: policy plus `snapshot_sha256` and `dataset_fingerprint`.
- `snapshot.json`: allowlisted v2 snapshot with canonical postings/evidence,
  dataset-bound evaluation and freshly recomputed market/quality/geography totals.

Both files are needed. Arbitrary relative/absolute artifact paths are unsupported.
The manifest's `release_id` should equal its deployed directory basename. Choose a
new ID for corrected data rather than overwriting an existing bundle. CLI output
reports only the release ID, sample size, `verified: true` and `published: false`.

Bounds: 20 MiB snapshot/source input, 512 KiB manifest/policy, at most 10,000 jobs,
100,000 evidence rows and 100 documented sources, with bounded text fields.
Malformed/duplicate-key/nonfinite JSON, symlinked directories/files, extra files,
changed hashes, stale review fingerprints, source omissions, missing permissions,
future/expired timestamps and inconsistent metrics all fail closed.

## Runtime integration

The implementation contract is:

```python
from career_radar.approved_release import load_approved_release
bundle = load_approved_release(approved_bundle_directory)
snapshot = bundle["snapshot"]
release = bundle["release"]
```

An invalid bundle raises `ValueError`; missing/unreadable filesystem objects may
raise `OSError`. The API boundary should use a generic service-unavailable message,
not echo raw descriptions, filesystem paths or permission correspondence.

The calling application constrains the operator-selected ID to a fixed approved
root, verifies the selected ID equals `release.release_id`, and uses the **same
snapshot** for network and role comparison. It must check expiry on every request;
a forever-cached manifest cannot enforce freshness. An explicitly configured but
invalid release must not silently become a demo or an unreviewed local snapshot.

The parent implementation uses the explicit `CAREER_RADAR_PUBLIC_RELEASE` slug
under `data/releases/`. An absent selector retains demo mode. Preparing a bundle
alone never enables that selector or deploys anything. GitHub-triggered builds
cannot read ignored files on this workspace: supply the reviewed bundle through
a controlled build artefact or an explicitly authorised deployment of the prepared
workspace. Both fixed files must be included under the selected release directory
in the serverless function. Setting the selector without those files produces an
unavailable-data response, not a working observed release. Do not enable the selector
until the actual source/display approvals and human review are complete.

## Validation

`tests/test_approved_release.py` uses explicitly artificial jobs, test-authored
labels and mock permission attestations. It does not create a real reviewed release.
Tests cover denominator retention for a zero-skill job, private-field stripping,
bare/old/duplicate review rejection, source permissions, dates/expiry, URL safety,
Irish scope, role/identity validation, exact evidence, rehashed metric tampering,
symlinks/extra files and size limits. No real dataset or generated release is
committed by this workflow.
