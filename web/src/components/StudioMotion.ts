import { useEffect, useState } from "react";

/** Only decorative movement. Chart coordinates and analytical values stay stable. */
export function useStudioMotion() {
  const [reduced, setReduced] = useState(() => matchMedia("(prefers-reduced-motion: reduce)").matches);
  const [paused, setPaused] = useState(false);
  const enabled = !reduced && !paused;
  useEffect(() => {
    const keyboard = () => { document.documentElement.dataset.input = "keyboard"; };
    const pointer = () => { document.documentElement.dataset.input = "pointer"; };
    document.addEventListener("keydown", keyboard, true);
    document.addEventListener("pointerdown", pointer, true);
    return () => {
      document.removeEventListener("keydown", keyboard, true);
      document.removeEventListener("pointerdown", pointer, true);
    };
  }, []);
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
    let light: HTMLElement | null = null;
    let pending: PointerEvent | null = null;
    const reset = () => {
      card?.style.removeProperty("transform");
      light?.style.removeProperty("transform");
      light?.style.removeProperty("opacity");
      light = null;
      card = null;
    };
    const move = (event: PointerEvent) => {
      if (event.pointerType !== "mouse" || !matchMedia("(hover: hover) and (pointer: fine)").matches) return;
      document.documentElement.dataset.input = "pointer";
      pending = event;
      if (frame) return;
      frame = requestAnimationFrame(() => {
        frame = 0;
        const e = pending!;
        const next = e.target instanceof Element ? e.target.closest<HTMLElement>(".tool-card") : null;
        if (next !== card) { reset(); card = next; light = card?.querySelector<HTMLElement>(".card-spotlight") || null; }
        if (!card) return;
        const box = card.getBoundingClientRect();
        const x = (e.clientX - box.left) / box.width;
        const y = (e.clientY - box.top) / box.height;
        // Write to the animated element; inherited variables would restyle its children.
        card.style.transform = `perspective(900px) rotateX(${(y - .5) * -5}deg) rotateY(${(x - .5) * 5}deg) translateY(-2px)`;
        if (light) {
          light.style.transform = `translate3d(${x * box.width - 160}px, ${y * box.height - 160}px, 0)`;
          light.style.opacity = "1";
        }
      });
    };
    const keyboard = () => { pending = null; cancelAnimationFrame(frame); frame = 0; reset(); };
    document.addEventListener("keydown", keyboard);
    window.addEventListener("blur", keyboard);
    document.addEventListener("visibilitychange", keyboard);
    document.addEventListener("pointermove", move, { passive: true });
    document.addEventListener("pointerleave", keyboard);
    return () => {
      document.removeEventListener("keydown", keyboard);
      window.removeEventListener("blur", keyboard);
      document.removeEventListener("visibilitychange", keyboard);
      document.removeEventListener("pointermove", move);
      document.removeEventListener("pointerleave", keyboard);
      cancelAnimationFrame(frame);
      reset();
    };
  }, [enabled, reduced]);
  return { enabled, reduced, toggle: () => setPaused((value) => !value) };
}
