# Skill Constellation readiness — 26 October 2026

**Verdict:** the local analytical demo is functional. It is not yet a service that
can answer current Irish job-market questions from observed vacancies. Additional
licenced/authorised data, human evaluation and an approved public-data release
integration are needed. Buying another service is not a prerequisite for the demo.

## What was checked

- Production React/TypeScript build and the existing browser/API/core tests.
- Role and geography filtering; denominators include zero-skill postings.
- Skill search/focus, category legend, support/Jaccard/lift edge ordering,
  exact phrase inspection, source rows and labelled JSON downloads.
- Separate role-comparison denominator handling and heatmap counts.
- Sparse/empty results, bounded graph endpoints, keyboard controls, mobile
  overflow and automated accessibility.
- A new explicit **Retry sample** action after a temporary analytical API failure.
- An independent reconciliation of 12 role/geography combinations: unique posting
  identities, evidence coverage, pair counts, support, Jaccard and lift recomputed
  directly from the returned evidence; all matched.

The Python suites `test_constellation*.py` passed 11 tests and `test_web_api.py`
passed nine. Browser evidence includes the Constellation completion checks,
source inspection, sparse geography, export, role comparison, recovery after a
503 response, and automated WCAG checks. These are software checks, not a measured
extraction-accuracy study on Irish vacancies.

## The data users actually see

| View | Current contents | What that means |
| --- | --- | --- |
| Skill network, all locations | 30 fictional Data Analyst postings | It demonstrates associations, not observed Irish demand. The network's role filter has only this role in its current fixture. |
| Network, Dublin | 20 fictional postings | Meets the default network display floor. |
| Network, rest of Ireland | 10 fictional postings | Network correctly suppressed below the 20-posting floor; the counted evidence is still inspectable. |
| Role comparison | Separate 90-record fictional fixture, three role samples before geography filters | Comparisons are demonstrations and must not be read as measured differences between Irish roles. The network role filter does not filter this separate comparison sample. |
| Source/date coverage | Generated fixtures, no live collection window | A generation timestamp is not a posting or collection date. |
| Human evaluation | Existing private pilot queue has zero completed reviews | No observed-data publication gate has been passed. |

Industry/seniority filtering, observed trends, salary demand and live job alerts
are not supported by these datasets. Four archived US descriptions in the other
tools do not add current Irish vacancies to this network.

## What is needed for target users

1. **An authorised Irish posting sample.** Aim initially for about 200 unique
   postings, Ireland-wide with Dublin identified separately. Retain title,
   employer, full description, source/job ID, canonical URL, location, posting date
   if known, collection timestamp and source/public-display scope. Approved employer
   ATS feeds or authorised saved exports can support a zero-budget start.
2. **A sensible role mix.** Prioritise the analyst roles users need first, then
   extend the 21-role taxonomy with adequate examples. Two hundred jobs across
   21 roles and several locations is not automatically enough: many slices will
   fall below the existing 20-posting network floor. Keep sparse slices suppressed
   and show counts. Twenty is a display policy, not proof of representativeness.
3. **A reviewed release with matching lineage.** Deduplicate and profile the chosen
   release for missing descriptions/dates/locations, skill coverage and employer
   concentration. Generate a review queue for that exact dataset and extraction
   version. At least 100 distinct reviewed evidence rows and 90% precision are
   required by the current publication evaluation, with category/version coverage
   and matching fingerprints. A completed review of a different pilot cannot be
   reused to unlock the new dataset. Source/display permission is a separate gate.
4. **A public approved-release loader.** `web_api.public_snapshot()` and
   `public_comparison_snapshot()` deliberately generate fictional data. A reviewed
   CSV on disk will not update the site. Implement a versioned, fail-closed release
   adapter, preserve source phrases and no-skill postings, and test provenance,
   geography/role options, graph capacity, guard behaviour and exports. Make the
   dataset boundary between network and role comparison explicit.
5. **Repeatable refresh and freshness.** The private saved-file refresh already
   builds manifests, quality profiles and review artefacts. It does not collect
   live jobs or update Vercel. Choose a permitted weekly source and spending cap
   before connecting collection, review and last-good public release. Adzuna
   should not be counted as an Irish source until Ireland coverage and account
   access are verified. Do not pay merely to try to solve a country-coverage gap.
6. **Hosted and user validation.** Verify the production API, loaded release ID,
   source links, mobile use and errors on the deployed website. Ask candidates and
   recruiters to complete concrete tasks and explain a metric back in their own
   words before treating the tool as validated for them.

## Deployment and access limit

A read-only check of the supplied production API was blocked by this workspace's
network proxy (`Tunnel connection failed: 403 Forbidden`). This does not establish
that the public site is broken, and local success does not establish that it is
healthy. Hosted readiness remains unverified; the Vercel integration's build and
function logs need an accessible session or an owner-side check.

## Next concrete handoff

Supply an authorised saved export or identify approved employer feeds for the
Irish sample. See [the intake guide](real-world-data-intake.md) for normalized
CSV fields and private storage. No passwords, candidate CVs or secret values are
needed in chat. We can build and test the approved-release adapter with fixtures
while collection permissions and human review are completed.

No paid actors, external job-source calls, invented review labels or public
observed-data release were used in this audit.
