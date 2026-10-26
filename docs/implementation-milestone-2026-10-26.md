# Connected tools and reviewed-release implementation — 26 October 2026

The software now supports the next stage without requiring an Irish export today.
The public deployment remains in demo mode until a separately reviewed release is
explicitly selected. No live collector, paid source call or public observed-data
release was enabled.

## Completed user journey

1. Paste a description or choose a labelled archived example in JD Diagnostic.
2. Analyse the wording and inspect exact source findings.
3. Select **Assess this role**. The analysed description moves to Readiness Studio
   with its archived-source and edit labels when applicable. Suggested clarifications
   are not substituted into the original text.
4. Review the description, extract requirements, enter evidence statuses, assess
   the baseline and use the existing project planner/what-if comparison.
5. **Discard carried description** or **Clear all** removes the transferred text
   and all assessment inputs. Leaving the tool discards the in-memory tool state.

The transfer is consumed once and held only in React memory. Descriptions and
candidate notes are not added to URLs, localStorage, sessionStorage or accounts.
Readiness does not automatically submit the carried text to the API; extraction
still requires the user's action. In-flight description requests abort on unmount.

## Reviewed source release path

- `career_radar.approved_release prepare/verify` builds immutable fixed-name
  bundles after checking exact dataset/review lineage, source permissions,
  collection dates, expiry, schema, resource limits and public fields. Metrics
  are recomputed from posting/evidence rows, including zero-skill postings.
- `CAREER_RADAR_PUBLIC_RELEASE=<release-id>` selects only a bounded slug under
  the fixed `data/releases/` root. No selector keeps the demo. Invalid, expired,
  missing or tampered selected releases return a generic HTTP 503; private paths
  and silent fallback are excluded.
- Both network and role comparison use the same approved snapshot. Roles,
  locations, sources, collection dates, review counts and export provenance follow
  the loaded release. Industry/seniority values are not invented.
- UI detects a release change between bootstrap and network requests and asks for
  a reload rather than mixing labelled datasets.
- Reviewed-source links are shown in evidence drill-down. Record availability is
  not assumed to be current after its collection time.
- Release artefacts are ignored by Git. Vercel function packaging supports approved
  artefacts supplied by the deployment workflow, but a local bundle alone is not
  present in a GitHub-triggered build. Preparing a bundle does not activate it.

See [the operator runbook](approved-release-runbook.md). The public demo remains
usable without credentials or any release artefact.

## Human accuracy study preparation

The private [requirement evaluation harness](requirement-evaluation.md) prepares
empty, pending gold-label cases and scores manually completed exact Unicode spans,
skills and requirement types. Pending cases are excluded; undefined precision or
recall is reported as unavailable. Test-authored fixtures only prove the scoring
implementation. They are not a real accuracy study or publication approval.

This requirement study and the existing skill-extraction publication evaluation
answer different questions. Diagnostic finding quality still needs a human rubric
review on supplied descriptions; neither study should be represented as an employer
rating or validated hiring prediction.

## Hosting checks

The hosted runner now defaults to a mode-aware release contract: API health,
no-store behaviour, snapshot identity, data labels/release bounds and navigation
through all four tools. It supports demo and reviewed modes. Local CI still runs
the complete regression suite. An explicit test file can broaden a hosted run.
The owner-selected shorter URL is `https://ireland-career-radar.vercel.app/`;
actual Vercel completion and network accessibility remain separately unverified.

## Local verification

The production build passed, as did 192 Python tests (including PostgreSQL
integration) and 55 browser tests against a freshly started API. Fourteen API
and release checks also passed in the lightweight Vercel-style Python environment.
These checks use fixtures and do not validate real Irish market data or a hosted
deployment.

## Work that requires the later data/human phase

- Supply authorised Irish descriptions/postings and documented source/display
  scope; profile and deduplicate the intended release.
- Human-label an evaluation set and the dataset-bound extraction queue. No labels
  or accuracy results have been fabricated for the existing private pilot.
- Review the resulting source coverage and approve a public release, then supply
  its artefacts to the deployment and select its ID.
- Choose permitted weekly collection sources and confirm their request/spend caps
  before enabling a live refresh. The current refresh path is saved-file based.
- Run task-based checks with real candidates/recruiters and physical devices.
- Add Riya's portrait when supplied.

These are pending inputs and validation tasks. They are not silently marked
complete by software tests, an approved-release test fixture or a Git push.
