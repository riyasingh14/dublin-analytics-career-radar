# Platform completion and review — 18 October 2026

This release completes the four-tool **synthetic public demonstration**, adds an
executable private operations path, and applies the reviewed light editorial
visual system. It does not release the unreviewed job sample, establish real
hiring predictions, activate paid collection, or certify human-reviewed accuracy.

## Review sequence and findings

Independent agents completed separate features, then cross-reviewed features they
had not built. A further read-only release review examined the integrated HTTP,
privacy, metric and operational boundaries. Functional and accessibility checks
preceded the visual redesign; the redesigned build then repeated regression checks.

| Finding | Resolution / evidence |
|---|---|
| Untouched extracted classifications were marked user-confirmed | Only actual manual overrides receive that provenance; downloaded report regression |
| An uppercase source token could enter an exported default suggestion | Generic clarification wording; name-like-token fixture; source text omitted from defaults |
| Full-time wording incorrectly established contract tenure | Hours-only wording remains unknown; explicit tenure fixtures |
| A training budget could count as salary disclosure | A nearby explicit pay label is needed; budget/allowance fixture |
| Repetition could amplify a small request to a multi-megabyte response | Explicit 200-mention/finding limits, bounded exact context slices and resource tests |
| Extreme JSON integers could overflow to an HTML 500 error | Range validation before float finiteness checks; safe JSON 400 regressions |
| Reciprocal career paths overlapped and flow widths were schematic | Directional paths and conserving Sankey allocation; independent geometry checks |
| An exact move selection eliminated the stayer comparator | Origin-state reference retains origin bands and releases incompatible destination constraints; scope disclosed |
| Refresh interruption/corruption could leave an unrecovered pointer | Artefact verification, idempotent recovery, newest-run preservation and failure tests |
| Low-contrast text and accessible-name mismatches | Corrected labels/palette; axe WCAG A/AA scans on all six routes |

No blocking/high-severity code defect remained in the independent review after
these fixes. This is a scoped engineering review, not an external security audit.

## Feature acceptance trace

| Criteria | Implemented evidence | Data / evaluation boundary |
|---|---|---|
| SC-01–02 | Unique-posting formulas, zero/no-skill denominators, filtered recomputation and SQL reconciliation | Counts describe selected samples |
| SC-03–05 | Search, bounded graph, category legend, selected-pair exact source phrases, accessible comparison heatmap/table and exports | Public network has 30 fictional postings; separate three-role comparison has 90 before geography filters |
| OR-01–02 | Exact source spans, reviewed classifications, private evidence notes/provenance, weighted breakdown, separate listing-condition checklist | Candidate evidence is self-reported; conditions are cues for manual checking |
| OR-03–04 | Side-by-side baseline/scenario, authored project handoff, explicit score coverage and limitations | No callback model, verified credentials or company likelihood |
| OR-05–06 | No account/upload requirement, reset/invalidation, minimal exports, hand-reconciled scores and conservative repeated mentions | No persistent candidate profile |
| CM-01–04 | Deterministic histories, adjacent transitions, career breaks/cuts/stayers, category flags and SQL/Python reconciliation | Generated assumptions; transition-weighted statistics, not causal results |
| CM-05–06 | Persistent synthetic labels, linked directional network/Sankey/matrix, filters, cohort rows, distributions and person timelines | Salary comparisons suppressed below 20 valid pairs; event rows explicitly capped at 200 |
| JD-01–03 | Exact Unicode source highlights, absent fields, rule/rationale, category filters and additive clarification diff | Proposed additions preserve the original; unknown facts remain questions/placeholders |
| JD-04–05 | Explicit unavailable benchmark, accept/dismiss/uncertain workflow and privacy-safe report identifiers | No reviewed comparable observed sample is connected; no fabricated benchmark |

Observed time-window analysis remains unavailable without comparable observations.
Industry/seniority filters for advertisements require populated, validated fields.
The public comparison fixture is three roles, not an observed sample of all 21
supported rule-classified occupations.

## Validation evidence

- **130 Python tests passed**, including **four actual PostgreSQL 17.11** integration
  tests; none skipped in the configured final local run.
- **30 browser/interaction/geometry checks passed** in Chromium, including one
  multi-route axe WCAG A/AA scan, source/edit flows, privacy/reset, linked filters,
  graph/Sankey geometry, pointer depth and pause/system reduced-motion behaviour.
- Production TypeScript/Vite build passed. The lightweight Flask-only environment
  passed the nine HTTP-boundary tests without research/SQL dependencies.
- Desktop 1440px and mobile 390px layouts were inspected; expanded mobile flows
  have automated overflow checks. This is not a complete assistive-technology or
  independent usability study.
- Four workflow YAML files parsed locally. Remote GitHub Actions outcomes and
  hosted Vercel acceptance still require observation after push.

The PostgreSQL fixture reconciled three postings, 21 skill pairs, 12 requirements,
500 synthetic spells, 400 transitions and 12 cohort aggregates. Repeat loading,
tamper rejection, no-skill denominators and transactional rollback were exercised.
See [operations runbook](operations-runbook.md).

`scripts/benchmark-platform.py` reproduces local synthetic Flask-client timings and
stores its report under ignored `data/validation/`. It measures first requests and
ten repeats, nearest-rank p95, and response sizes. It excludes browser paint,
network, Python startup and hosted cold starts; it cannot establish hosted UX
targets. See the release status for measured values.

Final benchmark, 18 October 2026 at 17:17 Dublin time, Python 3.12.14 on Linux
x86_64: bootstrap p95 1.73 ms; constellation 2.42 ms; Dublin-filtered constellation
2.23 ms; diagnostic 5.16 ms; readiness 1.69 ms; 500-person/five-year synthetic
mobility 80.00 ms; filtered mobility 84.21 ms. These are ten repeated local
test-client requests per workload, with nearest-rank p95. The largest default
response was 402,245 bytes; these timings do not include browser paint or hosting.

## Remaining release gates

1. Supply the broader authorised Ireland export and confirm collection/retention/
   display permission. The existing 32-job pilot remains private and unreviewed.
2. Complete applicable human extraction, requirement and diagnostic evaluation.
   Do not invent labels or infer human precision from authored unit tests.
3. Verify the actual Vercel deployment and GitHub checks. The owner supplied a
   URL, but this workspace's network previously blocked its inspection; plugin
   installation is not an OAuth/account connection.
4. Approve and configure any real recurring collection, remaining budget, durable
   database, alerts and public publication policy. The fixture schedule is dormant
   and makes no live collection calls even when manually rehearsed.
5. Run recruiter/user comprehension walkthroughs before claiming usability,
   adoption or competitive superiority.

These are external data/operating/evaluation gates, rather than missing buttons
disguised as completed live capabilities. The public demonstration stays usable
without them.
