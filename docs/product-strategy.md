# Product strategy

The authoritative feature specification is [PROJECT_DESCRIPTION.md](../PROJECT_DESCRIPTION.md).
This document summarises the product rationale rather than duplicating its requirements.

## Primary objective

Demonstrate data and business analyst capability to recruiters, hiring managers and
senior executives through a coherent decision workflow. The project should make
problem framing, reliable data modelling, SQL, evaluation and stakeholder
communication visible. Commercial adoption and competitor superiority are
hypotheses requiring separate evidence.

## Product and users

Dublin Analytics Career Radar explores technology-career requirements across the
Republic of Ireland, with Dublin shown separately. Students and career changers
inspect skills and evidence gaps; recruiters and hiring managers inspect job
requirements; portfolio reviewers inspect the quality of the analytical work.

## Four flagship experiences

| Feature | Decision question | Analytical contribution |
|---|---|---|
| Skill Constellation | Which skills appear together in a selected role sample? | Co-occurrence, association measures and source drill-down |
| Opportunity Readiness Studio | Which requirements can a candidate evidence, and what is unknown? | Explainable requirement matching and sensitivity |
| Career Mobility Lab | How do simulated transition outcomes differ under disclosed assumptions? | Longitudinal SQL, cohort analysis and salary scenarios |
| Job Description Diagnostic | What is clear, missing or inconsistent in a description? | Text evidence, deterministic rules and requirements quality |

The market dashboard, coverage panel and methodology are shared foundations.
A basic proof-of-work planner exists but is not a separate fifth flagship.

## Product principles

- Lead with a decision question and expose detail progressively.
- Keep observed job evidence, self-reported candidate evidence and synthetic career
  outcomes separate and clearly labelled.
- Prefer inspectable calculations and readable visuals over unsupported scores.
- Keep source data replaceable and show collection uncertainty and sampling limits.
- Validate the expanded taxonomy and each feature before public claims.
- Avoid callback probabilities without suitable outcomes and real-world salary
  claims from synthetic data.
- Introduce new technology only to satisfy an actual analytical or interaction need.

## Delivery and success

Use the milestone sequence in [PROJECT_PLAN.md](../PROJECT_PLAN.md): broader data
and SQL foundation, Skill Constellation, Diagnostic, Readiness, Mobility, then
presentation/operation. The full feature acceptance criteria are in the master
specification. A successful portfolio demo lets a reviewer trace a finding to its
evidence, reproduce a calculation, understand its limitations and see a useful
next action within a short walkthrough.
