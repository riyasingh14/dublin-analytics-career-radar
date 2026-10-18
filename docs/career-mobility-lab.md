# Career Mobility Lab — planned portfolio module

The [master project specification](../PROJECT_DESCRIPTION.md#6-feature-3--career-mobility-lab)
defines the selected scope and acceptance criteria. This document supplies supporting design rationale.

Status: supporting design brief. An initial in-memory generator and interactive lab are implemented; see [implementation status](implementation-status.md). The PostgreSQL worksheet remains unexecuted. All career-history and compensation data in
this module will be synthetic. It is independent of the observed job-posting sample.

## Purpose and audience

The project's primary goal is to demonstrate data/business analyst capability to
recruiters and senior decision-makers. The lab should show problem framing, data
modelling, SQL analysis, cohort design, visual communication and recommendations.
Commercial potential is a secondary hypothesis, not a reason to invent market claims.

Decision question: in a simulated workforce, how do compensation trajectories
differ when people change employers, occupations, sectors or seniority levels?
These comparisons describe the generated scenario. They do not establish what a
real person will earn, actual transition likelihood, or a causal effect of switching.

## Data design

Create deterministic, seeded synthetic career histories with person IDs, dated job
spells, employer IDs, occupation family, employer industry, seniority, location,
annual full-time-equivalent base salary in EUR, and working-time assumptions.
No real names, CVs or personal profiles are required. Publish generator parameters,
assumptions, seed, data dictionary, generator version and known limitations.

Model job spells first and derive a transition fact table. Explicitly distinguish
occupation (e.g. Data Analyst) from industry (e.g. financial services): a software
engineer moving to a bank has not necessarily left a technology occupation.
Keep employer change, occupation change, industry change and promotion as separate
flags; an event can have several. For exclusive comparisons, report combined-event
groups explicitly instead of counting one transition several times.

Include stayers, promotions, lateral moves, pay cuts, zero change and career breaks.
Keep salary conventions comparable; exclude incomparable or missing before/after
salary pairs from uplift denominators and report exclusions. Validate chronological
order, non-overlapping spells, salary units and transition identities. Simulated
results should vary by multiple disclosed factors instead of forcing all switchers
to earn more. Assumptions remain assumptions even if charts look plausible.

## Analytical views

1. Executive overview: valid paired-transition count, median before/after salary,
   median individual percentage change, share with a decrease, and cohort size.
2. Mobility explorer: filter by origin/destination occupation, employer industry,
   seniority, experience, geography, time period and transition type.
3. Compensation trajectories: show salary distributions and individual or cohort
   timelines rather than only an average uplift. Compare within relevant experience
   and seniority bands and include stayer baselines; these remain descriptive.
4. Scenario workbench: change disclosed generator assumptions, rerun a scenario,
   and compare it with a named baseline. Never present assumed effects as fitted
   salary predictions or real-world confidence intervals.
5. Analyst findings: concise observations, counterexamples, sensitivity to cohort
   choices, exclusions and recommended next questions.

Distinguish median of individual percentage changes from the percentage change
between cohort median salaries. Neither should be labelled as the other. Avoid
ranking sparse cohorts; show their size and apply a documented minimum threshold.

## Visual signature

Use an interactive radial career network as the distinctive view. Nodes represent
occupation/seniority states; edges represent observed transitions in the synthetic
histories. Edge width encodes event count and edge colour encodes median simulated
salary change, with labelled units and a colour-blind-friendly scale. Hover/click
reveals counts, salary distributions and the exact cohort definition. Limit visible
edges and provide search so dense data does not become an unreadable network.

Provide a Sankey alternative for readable origin-to-destination flows, a transition
heatmap for precise comparisons, and linked distribution/timeline panels. Support
keyboard-accessible controls and an equivalent table/download. A globe is only
appropriate for actual geographic moves; do not imply that career states occupy
geographic coordinates. Three-dimensional rendering is optional and follows a
usable two-dimensional implementation, rather than replacing it.

## Relationship to the market radar

The market radar uses observed job advertisements for skill mentions and evidence.
The lab uses generated career histories for mobility and compensation analysis.
Do not join simulated salaries onto real postings or blend their metrics. Each lab
page, chart tooltip and export must say **Synthetic scenario — not observed labour-
market outcomes** and show the scenario version. Real job descriptions do not supply
longitudinal person-level salary histories.

## Delivery and portfolio evidence

Build in this order: data contract and generator; SQL transition/cohort models;
verified metrics and quality checks; a readable Sankey/heatmap; the linked radial
explorer; scenario controls; accessibility and performance checks; a short demo.
Use the existing stack first. Introduce a new frontend or service only if a working
prototype demonstrates that it is needed for interaction or performance.

Acceptance evidence: reproducible data generation, meaningful analytical tests,
documented SQL, baseline/scenario comparison, inspectable cohort denominators,
visible synthetic labels and a three-minute executive walkthrough. Add architecture,
requirements and acceptance criteria, findings, trade-offs and limitations to the
case study. Describe only implemented/measured results in the CV and demo. Do not
claim competitor superiority without a documented feature comparison and user tests.
