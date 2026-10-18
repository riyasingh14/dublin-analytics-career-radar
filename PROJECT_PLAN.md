# Dublin Analytics Career Radar — Delivery Plan

The authoritative scope, feature requirements, metrics and acceptance criteria are
in [PROJECT_DESCRIPTION.md](PROJECT_DESCRIPTION.md). This plan tracks delivery;
older brainstorming proposals are not additional release requirements.

## Objective and selected scope

Build a portfolio-quality data/business analyst project for recruiters, hiring
managers and senior executives. Commercial potential is secondary. The four
flagship experiences are **Skill Constellation**, **Opportunity Readiness Studio**,
**Career Mobility Lab**, and **Job Description Diagnostic**. A landing page and all four tool routes are implemented. The job-market dashboard
and methodology are shared foundations. The existing proof-of-work planner can
supply supporting logic but is not a fifth flagship.

The observed-data scope covers 21 tech role families across the Republic of Ireland,
with Dublin, rest of Ireland and location-unspecified listings distinguished.
Synthetic mobility histories are separate from observed advertisements and
self-reported candidate evidence. This remains separate from Telco Churn Analysis.

## Current baseline

- Implemented: local ingestion, canonical-URL/content deduplication, 21 role families,
  64 controlled skills, source phrases, quality profiling and snapshot creation.
- Implemented: source-linked evidence tab, geography filters and a basic legacy
  skill-gap/proof-of-work planner. These do not constitute the full planned modules.
- Imported: 32 unique Dublin postings from a user-provided Apify export; unreviewed.
- Prepared: a bounded Ireland collection input targeting approximately 200 unique
  postings, with up to 315 candidate results. The broader export is not yet available.
- Generated: a 100-record extraction review queue; human review is pending.
- The previous baseline had 28 passing tests; the expanded suite now exercises the four tool prototypes and their integration. See docs/implementation-status.md.
- PostgreSQL schema exists; an operational SQL/database pipeline is still planned.
- No automatic weekly collection is operational. The owner reports the React/Vite + Flask demo deployed on Vercel. Hosted checks are blocked by this workspace's network; the installed Vercel plugin needs tool restart and OAuth. Build/browser/API CI and deployment-event/manual hosted checks are configured; remote execution is unverified.

## Milestones

| Milestone | Deliverable | Completion evidence | State |
|---|---|---|---|
| M0 | Master specification for the four selected features | Description, definitions, flows, scope and acceptance criteria | Documented; implementation work follows |
| M1 | Reviewed broader dataset and executable SQL foundation | Import, quality report, relevant human evaluation, reconciled SQL | In progress; broader export and review pending |
| M2 | Skill Constellation | SC-01 through SC-05 in the master specification | Initial prototype implemented; human validation pending |
| M3 | Job Description Diagnostic | JD-01 through JD-05 and evaluated rule examples | Initial prototype implemented; human evaluation pending |
| M4 | Opportunity Readiness Studio | OR-01 through OR-06, inspectable scoring and session privacy | Initial prototype implemented; usability/evaluation pending |
| M5 | Career Mobility Lab | CM-01 through CM-06 and reproducible synthetic scenarios | Initial in-memory prototype implemented; PostgreSQL path pending |
| M6 | Consistent presentation, optional permitted refresh and portfolio launch | Accessibility, performance evidence, runbook and five-minute demo | Planned |

The diagnostic precedes readiness because both need a reliable requirement model.
Develop readable analytical views before adding complex network interactions.
Revisit weights and cohort thresholds after evaluation rather than presenting
provisional design choices as validated science.

## Release controls

- Keep raw, processed, review, résumé and personal-profile data out of Git.
- Record source review, collection-time status, sample denominators and rule versions.
- At least 100 human-labelled skill-evidence records and 90% precision are the
  existing minimum extraction gate; each new module needs its own validation.
- Do not publish the current unreviewed sample or invent human review results.
- Make synthetic, hypothetical, self-reported and observed data visibly distinct.
- Do not predict callback likelihood, rank candidates for employers or claim causal
  salary effects from generated data.
- Apify budget remains US$10 overall; check actual spend before another paid run.
- Public display permissions, recurring spending and refresh prerequisites remain
  unresolved decisions, not completed capabilities.

## Portfolio deliverables

A requirements/acceptance trace, data dictionary, architecture, working SQL models,
quality/evaluation report, meaningful tests, accessible interactive demo, screenshots,
measured performance and an executive case study. CV claims must describe actual
implemented contributions and measured results.
