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

## Homepage guide and shared motion pass — 26 October 2026

The homepage now says “BASED IN DUBLIN, IRELAND”. Each tool card answers a plain
question and names its audience, useful output, analytical method and scope.
Blue identifies Constellation, lilac Readiness, peach Mobility and lime Diagnostic.
These colours also identify the corresponding page's header symbol; charts retain
neutral surfaces and their existing analytical colour encodings.

| Before | After | Why |
| --- | --- | --- |
| Generic tool slogans with similar panels | A question, intended user, output and method on four coloured cards | Explain practical value and expose the analytical work behind it |
| Data Passport had its own motion implementation | One native-details handler shared across all seven pages | Consistent opening, closing and reversal, including dynamically loaded findings and evidence checklists |
| Immediate page content with isolated profile motion | One-time 220ms text/card entrances, up to 120ms stagger; diagram surfaces fade without changing coordinates | Introduce hierarchy while keeping analytical values stable |
| No shared cancellation for keyboard input | Keyboard input settles current animations and toggles details immediately | Keep keyboard navigation responsive |

`web/src/components/PagePolish.ts` uses IntersectionObserver and WAAPI without a new
runtime dependency. It never hides content in base CSS. Each element is introduced
once, and only when visible; a MutationObserver registers newly mounted panels
without scanning the page on every SVG projection frame. Entry effects animate
transform/opacity; touch devices use opacity-only entrances to keep content in place. Native disclosures use a 240ms height transition, the explicit
accordion exception where actual document space must open/close. Rapid reversals
start at the current displayed height. Nested links and buttons keep their native
actions. Cleanup settles disclosure state and cancels animations on navigation,
pause or reduced-motion changes.

Coverage: home text/cards/hero diagram; Constellation header, metrics, graph panels
and source disclosures; Readiness header, input/results and evidence checklists;
Diagnostic header, results and finding disclosures; Mobility header, metrics,
scenario/cohort controls; Builder introduction/story/practice cards; Methods panels.
Continuous hero art and the horizontal skill strip retain their existing global
motion controls. This pass does not add chart sweeps, animated numerical counters,
or a claim of physical-device frame-rate validation.

## Fluorescent homepage refinement — 26 October 2026

The hero now presents 13 equal peers on a rotating spherical mesh. A Fibonacci
sphere distributes their positions; a regular four-neighbour topology creates
26 connections. Every skill has the same base node sizing and degree. Initial
selection is empty; a chosen skill receives a ring and connected-edge highlight.
The graph remains an illustration of connected analytical practices.

The tools heading is “Our four tools.” Purple, acid lime, cyan and hot pink cards
use ink text, offset shadows and a numbered watermark. A separate radial light
layer follows the pointer through direct transform/opacity writes alongside the
existing bounded card tilt. Pointer motion is frame-batched, mouse/fine-pointer
only, and cleared on leave, keyboard input, blur and global motion pause.

“Why I built this” retains the four intentions and small bottom-right byline,
now in a dark-purple build-note panel with a subtle grid, numbered lime markers
and a question → evidence → decision line. Text contrast and mobile overflow are
checked alongside the graph and pointer interaction checks.

## Tool-opening introduction — 26 October 2026

At the owner's request, each entry to one of the four tools now includes an
intentional minimum 2,000ms introduction, including cached tools. `ToolEntrance`
mounts the lazy tool behind the introduction so imports and analytical requests
can proceed concurrently. Content becomes available after both the timer and
component readiness; slower imports retain the loading screen. This presentation
minimum is not an API latency measurement.

The viewport-centred purple/lime orbital loader fades over 200ms into a 220ms
content reveal. Pending content is inert and hidden from assistive technology.
Header navigation remains available, and route keys plus effect cleanup prevent
old timers from revealing a previous tool. Reduced-motion and keyboard use keep
the status static and bypass positional transitions while retaining the requested
minimum duration. Timing, centring, cached revisits, rapid route changes and
reduced-motion usability have dedicated browser checks.
