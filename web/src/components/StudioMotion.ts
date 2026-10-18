import { useEffect, useState } from "react";

/** Only decorative movement. Chart coordinates and analytical values stay stable. */
export function useStudioMotion() {
  const [reduced, setReduced] = useState(() => matchMedia("(prefers-reduced-motion: reduce)").matches);
  const [paused, setPaused] = useState(false);
  const enabled = !reduced && !paused;
  useEffect(() => {
    const preference = matchMedia("(prefers-reduced-motion: reduce)");
    const changed = () => setReduced(preference.matches);
    preference.addEventListener("change", changed);
    return () => preference.removeEventListener("change", changed);
  }, []);
  useEffect(() => {
    document.documentElement.dataset.motion = enabled ? "active" : reduced ? "reduced" : "paused";
    if (!enabled) return;
    let frame = 0;
    let card: HTMLElement | null = null;
    let pending: PointerEvent | null = null;
    const reset = () => {
      card?.style.removeProperty("--tilt-x");
      card?.style.removeProperty("--tilt-y");
      card?.style.removeProperty("--spot-x");
      card?.style.removeProperty("--spot-y");
      card = null;
    };
    const move = (event: PointerEvent) => {
      if (event.pointerType !== "mouse") return;
      pending = event;
      if (frame) return;
      frame = requestAnimationFrame(() => {
        frame = 0;
        const e = pending!;
        const next = e.target instanceof Element ? e.target.closest<HTMLElement>(".tool-card") : null;
        if (next !== card) { reset(); card = next; }
        if (!card) return;
        const box = card.getBoundingClientRect();
        const x = (e.clientX - box.left) / box.width;
        const y = (e.clientY - box.top) / box.height;
        card.style.setProperty("--tilt-x", `${(y - .5) * -5}deg`);
        card.style.setProperty("--tilt-y", `${(x - .5) * 5}deg`);
        card.style.setProperty("--spot-x", `${x * 100}%`);
        card.style.setProperty("--spot-y", `${y * 100}%`);
      });
    };
    document.addEventListener("pointermove", move, { passive: true });
    document.addEventListener("pointerleave", reset);
    return () => {
      document.removeEventListener("pointermove", move);
      document.removeEventListener("pointerleave", reset);
      cancelAnimationFrame(frame);
      reset();
    };
  }, [enabled, reduced]);
  return { enabled, reduced, toggle: () => setPaused((value) => !value) };
}
