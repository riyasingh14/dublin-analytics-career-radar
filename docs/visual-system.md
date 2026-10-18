# Light editorial analytical studio

The selected direction combines warm paper, analytical ink, electric cobalt and
chartreuse accents. Large sans-serif headings, serif emphasis, fine rules and
monospaced labels organise the experience. The tools retain explicit counts,
units, sources and data-type labels rather than becoming decorative dashboards.

## Motion grammar

- The landing sculpture projects three native-SVG orbital planes into perspective.
  Its 13 skill nodes are conceptual; positions, edges and sizes encode no market
  measure. Selected notes explain analytical practice and link to the actual tool.
- Autonomous rotation is bounded to 30 updates per second. Pointer movement adds
  damped depth. Label collision checks reduce clutter; every node keeps its
  accessible name whether or not its decorative label is displayed.
- Tool cards respond to mouse position with at most 2.5 degrees of tilt per axis
  and a restrained light response. They remain ordinary navigable links.
- Analytical chart positions and metric values do not move continuously. Hover,
  selection, directional paths and linked evidence provide the analytical depth.
- A visible global Pause motion control stops decorative motion and clears card
  transforms. The operating system's reduced-motion preference takes precedence.
- The sculpture stops offscreen, in hidden tabs and while focus is inside it.
  Keyboard users inspect stationary targets. Observers/listeners/frames clean up
  when their components unmount.

There is no WebGL requirement, external font fetch, video or additional animation
framework. Chart semantics, keyboard use, table alternatives and mobile layouts
remain available with all movement disabled.

## Verification

Chromium checks cover autonomous movement, pause, keyboard skill selection,
system reduced motion, pointer tilt/reset, mobile navigation and overflow. Axe
WCAG A/AA checks run against all six public routes, including populated forms.
Desktop and mobile screenshots are reviewed locally. This is automated and visual
engineering verification, not a complete external accessibility certification.
