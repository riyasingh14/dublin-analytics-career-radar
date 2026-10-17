# Dublin Analytics Career Radar — Delivery Plan

## Product statement

Dublin Analytics Career Radar is an AI-assisted career intelligence product that analyses current Dublin analytics-role demand and converts a candidate's most important skill gaps into concrete, evidence-backed portfolio actions.

It is a separate repository, application, data pipeline, and deployment from the Telco Churn Analysis project.

## MVP audience and scope

- Primary user: early- and mid-career analytics candidates in Dublin.
- Target roles: Data Analyst, Business Analyst, BI Analyst, and Product Analyst.
- Geography: roles explicitly located in Dublin or advertised as Dublin-hybrid.
- Industry: a comparison/filter dimension, not a collection restriction.
- Initial data sources: authorised APIs, approved public company careers feeds, and documented user-provided exports.

## The differentiator

The product must go beyond a list of popular skills:

```text
Current job-market evidence
          ↓
Normalised skills and confidence
          ↓
Role-specific demand and trends
          ↓
Candidate skill/evidence gap
          ↓
One concrete proof-of-work recommendation
```

Every published market claim must expose its collection window, sample size, source coverage, and extraction method.

## Delivery phases

### Phase 1 — Foundation (complete)

- Product strategy and responsible-data policy.
- Controlled taxonomy of 35 skills across 11 categories.
- PostgreSQL source, posting, snapshot, and skill-evidence model.
- Authorised CSV, Greenhouse, and Adzuna connectors.
- Deterministic evidence-preserving extraction baseline.
- Automated tests for extraction, deduplication, and connectors.

### Phase 2 — Real-data validation

- Connect at least one authorised live source.
- Collect the first dated Dublin snapshot.
- [Implemented] Profile role coverage, duplicate rate, missingness, and employer concentration.
- [Implemented] Generate a reproducible, category-balanced queue for at least 100 reviews.
- [Implemented] Publish overall/category precision and a 95% confidence interval.
- [Pilot imported] 32 user-provided Apify records; skill extraction review remains pending.
- [Pending human review] Complete the review and document taxonomy gaps before showing AI insights.

Exit criterion: a documented, reproducible dataset with enough coverage to support labelled sample-based insights.

### Phase 3 — Analytics and AI layer

- SQL models for role, skill, employer, industry, seniority, and work-pattern demand.
- Skill co-occurrence and cross-role comparisons.
- Evidence-preserving LLM extraction only where the deterministic baseline is insufficient.
- Evaluation by category, confidence threshold, and extraction version.
- Proof-of-work recommendation rules linked to market demand and the controlled taxonomy.

Exit criterion: every recommendation can be traced to market evidence and a reviewed rule.

### Phase 4 — Public product

- Market overview with freshness and coverage labels.
- Role comparison.
- [Implemented] Skills evidence explorer with exact phrases, job links, employer and role filters.
- Candidate skill-gap assessment.
- Proof-of-work planner.
- Methodology, privacy, and limitations pages.

Exit criterion: a candidate can select a target role and current skills, then receive one evidence-backed portfolio action in under three minutes.

### Phase 5 — Independent deployment and portfolio launch

- Dedicated GitHub repository and deployment.
- Automated tests and scheduled data-refresh workflow where source terms allow it.
- Accessibility, mobile, empty-state, error-state, and source-link checks.
- Architecture diagram, screenshots, short demo, CV bullet, and LinkedIn launch post.

## Success measures

- At least 90% precision on 100 manually reviewed skill extractions before public AI claims.
- No dashboard metric without sample size and collection window.
- No source without provenance and a recorded terms review.
- No candidate account or stored CV in the MVP.
- One useful proof-of-work action produced in under three minutes.

## Explicit non-goals

- Building another general job-search site.
- Direct scraping of LinkedIn or Indeed pages. A user-approved Apify export may be imported for private validation with recorded provenance.
- Claiming comprehensive coverage of the Dublin labour market.
- Automatically rejecting, ranking, or making adverse decisions about candidates.
- Adding a chatbot before the evidence and evaluation layers work.

## Separate deployment boundary

The Telco project will not be imported, embedded, or reused as this application's deployment. It may later be referenced only as an example portfolio artefact in a proof-of-work recommendation.
