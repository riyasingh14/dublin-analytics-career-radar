# Emil Kowalski skills: first page-by-page implementation

Installed at the user's request on 25 October 2026 using the official `skills`
CLI, scoped to Codex and this repository:

```bash
npm --cache /workspace/.cache/npm exec --yes --package skills@latest -- \
  skills add emilkowalski/skills --agent codex --yes
```

The cache override uses the writable workspace rather than the unavailable default
home cache. All 15 upstream skills are in `.agents/skills/`; `skills-lock.json`
records their source paths and content hashes. These are agent instructions,
not browser dependencies. They are excluded from the Vercel deployment upload.
No animation package was added to the application.

Applied guidance: [Design Engineering](../.agents/skills/emil-design-eng/SKILL.md),
[Animate](../.agents/skills/animate/SKILL.md), and
[Animation Performance](../.agents/skills/animation-performance/SKILL.md).
Native/Swift/Expo skills are installed but do not apply to this React website.
The audit-only skill is not used as the implementation workflow.

## Page order and changes

| Page | Before | After | Why |
| --- | --- | --- | --- |
| Home | Card tilt used four inherited variables; hover transforms also applied on touch | Direct transform on the card; static spotlight; fine-pointer gating; bounded tilt resets on keyboard, blur and visibility change | Avoid descendant style updates and accidental touch motion |
| Home | Profile links had independent timings | Shared press feedback and custom ease-out, with subtle profile entry when supported | Make contact actions feel consistent while keeping the profile prominent |
| Skill Constellation | Whole tool moved on entry; conditional loading text shifted nearby content | Instant analytical entry and a reserved, accessible progress region | Keep source counts and evidence positions stable |
| Readiness | Busy button was the primary progress signal; assessment label remained unchanged | Live progress region, busy extraction state and explicit assessment feedback | Make the requested action clear without implying a score exists before completion |
| JD Diagnostic | Busy state communicated chiefly through the disabled button | Live progress region with a small work indicator; static when motion is paused or reduced | Confirm processing without disabling the global motion control |
| Career Mobility | Default Recharts transitions could replay when cohorts changed | Explicitly disabled bar/line animation; consistent progress region | Values are ready to inspect immediately; no motion implies a new outcome |
| Methods and shared navigation | Broad tool-entry movement, inconsistent focus affordances; menu lacked Escape return | Instant entry, visible focus, mobile Escape closes navigation and returns focus to its trigger | Support rapid keyboard exploration of the portfolio |

## Motion contract

- Purpose: feedback for presses and work in progress; rare identity introduction.
- CSS uses the upstream `cubic-bezier(0.23, 1, 0.32, 1)` curve with 120ms press
  and 180ms interaction tokens; profile entry uses 200ms.
- Decorative transform/opacity effects do not change analytical layout or values.
- Keyboard actions bypass transitions. Hover movement requires a fine pointer
  with hover capability. System reduced motion and the app pause control remove
  movement, while labels and focus states still communicate state immediately.
- Description input text is at least 16px to avoid automatic iOS focus zoom.
- The existing illustrative hero sculpture retains its deliberately bounded 30fps
  projection and offscreen/visibility/focus pause. This pass does not claim it was
  converted to compositor-only animation or benchmarked on physical phones.
- The existing ivory editorial theme and contrasting purple builder card remain.

## Verification

Run `npm run build`, then
`PLAYWRIGHT_CHROMIUM_EXECUTABLE=/usr/bin/chromium npm test` in this environment.
Verified for this pass: production build passed; all 36 browser checks passed,
including automated WCAG A/AA checks across six routes.

The browser suite covers the four tools, source provenance, exports, accessibility,
keyboard controls, pointer depth, reduced motion, loading feedback and mobile
navigation. The explicit browser path reuses installed Chromium; it is not needed
when Playwright's bundled browser is installed.

Desktop/mobile screenshots and browser emulation check layout and interaction.
Physical-phone Safari behaviour and subjective timing still benefit from a manual
feel check; browser emulation is not a device performance benchmark.
