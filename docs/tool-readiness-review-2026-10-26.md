# Tool readiness and visual review — 26 October 2026

The platform is a working analytics portfolio with four interactive tools. The
next useful milestone is a validated Irish job-description case study and a
connected user journey. A finished visual pass does not establish real-market
coverage or measured document-analysis accuracy.

## Visual and interaction review

The requested homepage edits are implemented: no extra hero note/link; no visible
“ILLUSTRATIVE”, “METHOD / EVIDENCE” or “CONTEXT / DECISION” graph labels; one proper
“WHY I BUILT THIS” heading with four bullets; and a small builder byline in the
bottom-right of that section. The native Data Passport stays home-only. Skills
continue to move horizontally without local controls; the global motion and
system reduced-motion settings still work.

Reviewed scope includes all seven routes, desktop/mobile layouts, header links,
focus return, touch hover behaviour, reduced motion, continuous skill motion,
interruptible expansion/collapse and dynamically loaded result panels. Analytical
values remain stable; charts use their existing coordinates rather than animated
numerical counters. Source/example labels inside each analytical tool remain.

Verification for this revision:

- Production TypeScript/Vite build passed.
- All 44 browser/interaction checks passed, including automated axe WCAG A/AA
  checks across all seven routes.
- All 157 Python checks passed, including four checks against actual local
  PostgreSQL. No skipped or invented human-review decisions.
- A separate responsive inspection covers seven routes at 390, 768, 1024 and
  1440 pixels, including generated Diagnostic/Readiness results and both graph
  tools. Its local evidence is retained outside Git under the onboarding review
  directory. This is viewport validation, not physical-phone performance testing.

Hosted Vercel completion, hosting latency, real-device Safari motion and usability
with independent people remain outside the local readiness claim. The supplied
website exists in the project context; Git pushes only trigger the owner's linked
integration and do not independently confirm a successful production build.

## What each tool can honestly do today

| Tool | Working value | Remaining evidence gap | Next acceptance criterion |
| --- | --- | --- | --- |
| JD Diagnostic | Analyse pasted descriptions, locate exact source spans, inspect findings, accept/dismiss/mark uncertain, edit additive clarifications and export a report | Four complete licensed examples are archived US descriptions; there is no independently labelled current Irish evaluation set | Review 10–20 complete current Irish descriptions across several role families; record correct/incorrect/missed findings and evaluate held-out examples |
| Readiness | Extract/correct requirements, enter skill evidence, separate work conditions from scoring, explain weights, create a project brief and compare hypothetical evidence | Evidence is self-reported, and requirement extraction has not been measured on current Irish examples | Use the same reviewed Irish descriptions; reconcile every requirement to source text and demonstrate a candidate's baseline → evidence gap → actionable project brief |
| Skill Constellation | Filter samples, inspect counts/Jaccard/lift, focus a skill, follow source phrases and compare roles in a separately labelled fixture | Public network and role comparison use separate fictional datasets; the real-data release path is not connected to the public API | Prepare an authorised, deduplicated sample of about 200 Ireland-wide postings, distinguish Dublin, finish human review and build a fail-closed approved-release loader with matching lineage and coverage metadata |
| Career Mobility | Reproducible histories, directional graph, conserving Sankey, matrix, distributions, cohort cuts and person timelines | Outcomes are synthetic, not estimates of actual career-switch returns | Keep the simulation label; review whether a first-time user can explain the assumptions, cohort and salary-pair denominator from one worked scenario |

The normalisation code already includes 21 tech/analytics role rules and the
64-skill taxonomy. The public comparison fixture covers a narrower role set;
expanded role/geography filters still need adequate denominators and validation.
Missing industry/seniority data must not be inferred just to populate controls.

## Prioritised next build

1. **One current Irish role, end to end.** Start with five complete descriptions
   for initial analysis, then expand to the evaluation set. Preserve employer,
   title, location, original URL, posting date when known, collection time and
   private/public reuse scope. Do not substitute collection time for posting date.
2. **A transient handoff between Diagnostic and Readiness.** The current pages
   keep their own state; inspecting one description does not carry it into the
   next tool. Add an explicit “Assess this role” journey with source/edit provenance
   and an obvious clear action, without local storage, URLs containing source text
   or candidate accounts. Validate the journey on one realistic analyst example.
3. **Human-labelled accuracy and review evidence.** The prepared private
   extraction queue has 100 records and zero completed reviews. It must be labelled
   by a human. The 100-record/90%-precision publication evaluation remains closed;
   it does not replace a separate Diagnostic/Readiness quality study.
4. **Reviewed Irish market release.** The public API deliberately calls demo
   generators in `web_api.public_snapshot()` and
   `public_comparison_snapshot()`. This is a deliberate boundary, not a missing
   environment variable. A new approved-release loader needs source/display
   permissions, validated artefacts, versioned hashes, sample dates and quality
   metadata, fallback behaviour and tests before any observed release.
5. **An operator-owned refresh and hosted review.** The saved-file refresh,
   manifests and PostgreSQL reconciliation already work. Weekly real collection,
   budget monitoring and production deployment verification still need their
   explicit integrations and source policy. The existing scheduled workflow is
   fixture-only; do not enable it as though it refreshed public Irish jobs.
6. **Independent task-based usability.** Have a candidate, an analytical reviewer
   and a recruiter try a short task. Record where they get stuck and whether they
   correctly distinguish observed evidence, self-reported evidence and simulation.
   Use those observations to prioritise further features rather than adding more
   visual effects.

Riya's supplied portrait remains a pending personal asset; the current monogram
is intentional. Accounts, CV retention, callback probabilities, employer rankings
and an external LLM are not missing launch requirements for this portfolio scope.

## What we need from the owner

For the first five descriptions: full text, employer/title/location, original URL,
posting date if available, collection date/time, and whether reuse covers private
evaluation or public display. Text or an authorised saved CSV/JSON export is enough.
See [the data intake guide](real-world-data-intake.md) and
[human review workbench](human-review-workbench.md). Candidate identifiers and
credentials are unnecessary.

No new source API calls, paid actors, recurring spending or public observed-data
release were performed in this review. Existing collection limits remain in place.
