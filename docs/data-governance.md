# Data governance and responsible AI

## Data provenance

The product stores the source, canonical job URL, collection timestamp, and extraction version for every posting. Public insights always show the collection window and sample size.

## Responsible collection

- Use official APIs, public company careers endpoints where their terms permit reuse, or user-provided files.
- Do not scrape LinkedIn or Indeed pages.
- Remove duplicate jobs using canonical URL, employer, title, location, and text similarity.
- Respect source removal requests and expired postings.

## AI controls

- AI extracts skills into a controlled taxonomy; it does not invent job requirements.
- Retain the source phrase, confidence, and model/extraction version.
- Validate a random sample manually and publish precision by skill group.
- Use human-reviewed rules for all candidate recommendations.

## Privacy

The MVP does not require accounts or CV uploads. Candidate skill selections can remain in the browser session. If profiles are added later, apply data minimisation, a documented lawful basis, retention limits, access controls, deletion handling, and a DPIA assessment where profiling risk warrants it.

## Interpretation limits

This is a sample-based signal tool, not a complete description of the Irish labour market. A mention of a skill in a job description does not prove salary, hiring likelihood, or candidate suitability.
