# From requirement to evidence action

Readiness Studio now connects its evidence matrix to an authored project planner.
The output is a proposed activity, not verified proficiency or an estimated
chance of getting hired. It requires no account, paid data or external AI model.

## Consistent aggregation

The score, status breakdown and plan share one skill-level aggregation. Each
confirmed skill counts once. Required weight is 3 and preferred weight is 1;
required takes precedence over a weaker repeated mention. At the strongest level,
every source occurrence must be assessed. Any unknown occurrence leaves that
skill unassessed; otherwise the least-supported occurrence determines its status.
Uncertain and negated mentions are excluded.

The breakdown reports both distinct skill count and requirement weight for
supported, partial, missing and unknown evidence. Its bar uses weight divided by
total confirmed weight. The four weights sum to the score's total denominator;
unknown weight equals unassessed weight. Supported weight plus half the partial
weight equals earned weight. These weights are product assumptions.

For example:

| Skill | Requirement | Weight | Self-reported status | Earned weight |
|---|---|---:|---|---:|
| SQL | Required | 3 | Missing | 0 |
| Python | Preferred | 1 | Partial, with a concrete note | 0.5 |

Assessed-weight coverage is 100%; alignment is `100 × 0.5 / 4 = 12.5`.
Marking SQL unknown instead would reduce coverage to 25% and suppress the index
under the existing 80% coverage guard. Unknown is an information gap, not failure.

## Explainable action order

The planner sorts required skills before preferred skills, then unknown, missing
and partial evidence within each level. Ties use skill ID for a stable result.
Supported skills produce no new project. This prioritisation does not estimate
labour-market demand, effort, financial return or hiring benefit.

Unknown evidence prompts the user to review existing projects, coursework or
experience. It does not receive a fabricated skill deficit or project brief.
Missing and partial evidence receive the controlled taxonomy's authored
proof-of-work recommendation, a reproducibility/business-readout deliverable list
and completion checks. SQL, Python, Excel and Power BI have specific validation
checks; other skills use a general task/result/boundary-case rubric.

The first three actions are visible initially; users can expand the full plan.
Source contexts are inspectable in-session. Review actions focus the unresolved
evidence control. Project actions prefill one unresolved source requirement and
an authored brief in the what-if form. Repeated mentions are distinguished there.

Planning does not mark work complete. A what-if request updates one selected
occurrence in a separate scenario; other repeated contexts can still limit the
skill's result. For the table above, hypothetical supported SQL raises alignment
to 87.5, while the submitted baseline remains 12.5. This is arithmetic under the
chosen assumptions, not an expected hiring outcome.

## Privacy and implementation

- The shared Python assessment returns skill groups and weighted status buckets.
- `evidence_plan.py` constructs versioned, nonmutating proposals from those groups
  and the controlled skill recommendations. No candidate notes or source text
  enter the plan object.
- The stateless API returns the baseline plan separately from any hypothetical
  scenario. It does not persist candidate evidence.
- Plan downloads omit candidate notes and advert text. The analysis download
  includes the plan, breakdown and opaque requirement IDs for reconciliation.
- Changing evidence or classifications invalidates results and plans. Clear all
  removes inputs, notes, assessments and scenarios from the current tool.

Users remain responsible for checking source classifications, choosing permitted
project data and reviewing exports. Completion criteria guide self-review; they
are not an automated credential check. Published private job data and real hiring
prediction remain outside this implementation.
