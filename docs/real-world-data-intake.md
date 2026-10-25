# Move from demonstration to useful Irish evidence

The product has four tools with different evidence needs. An authentic description
is useful for text analysis, but does not by itself establish a market trend or a
salary outcome. The existing archived US reference library remains labelled as
historical and outside the Irish market.

| Tool | Next useful data | What it enables |
| --- | --- | --- |
| JD Diagnostic | 10–20 complete current Irish descriptions across analyst, product, engineering and BI roles, including ambiguous and well-written examples | Human review of requirement extraction, missing information and suggested clarifications against real writing |
| Readiness | The same descriptions plus user-entered skill evidence | Requirement-by-requirement preparation plans; never an estimated callback probability |
| Skill Constellation | Approximately 200 unique Ireland-wide postings with full descriptions, Dublin separately tagged, from a documented collection window | Reviewed sample-level skill relationships and role comparisons; collection dates, coverage and uncertainty visible |
| Career Mobility | Consented, de-identified longitudinal records of roles, employers, dates and comparable salaries | Observed transition summaries only when cohort sizes support them; job advertisements cannot reveal individual salary gains |

## A useful first handoff

Provide five complete current Ireland job descriptions first, as text or CSV, with
job title, employer, location, original URL, posting date if known, and the date you
collected them. State whether you have permission to reuse the text and whether
that permission covers public display or private evaluation only. Do not include
applicant contact details, CVs, account cookies, API keys or other personal data.
A missing posting date stays unknown; the collection date is not substituted.

For a larger authorised export, the existing saved-file pipeline accepts these
normalized fields:

```csv
source_job_id,canonical_url,title,employer_name,location_text,description_text,posted_at
```

Use a stable source ID and quote description cells containing commas/newlines.
Store observed exports only under ignored `data/raw/` paths; retain collection
time and source/permission notes separately in the local run policy. Never commit
a full observed export to Git. See [the operations runbook](operations-runbook.md)
for validation, source policy and zero-request refresh commands.

## Review before release

1. Check source permission, scope, collection time, full-text completeness and geography.
2. Ingest and deduplicate; inspect missingness, role coverage, employer concentration
   and exact skill-evidence coverage. Keep the dataset `unreviewed`.
3. Generate and complete the existing human-review queue. Preserve exact source
   phrases and mark unsupported classifications rather than inventing labels.
4. Require the existing publication evaluation (at least 100 reviewed records,
   at least 90% extraction precision, version and dataset lineage checks). Passing
   this evaluation does not itself authorize publication.
5. Release only an explicitly reviewed, display-authorised snapshot with its sample
   size, dates, source coverage and limitations. Keep synthetic and observed views distinct.

No new paid collection or automatic weekly spend is enabled by this plan. Existing
Adzuna and Apify limits remain in place. Mobility stays synthetic until an appropriate
longitudinal source exists; a polished animation must not imply observed outcomes.
