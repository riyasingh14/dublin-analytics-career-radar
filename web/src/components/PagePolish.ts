import { useEffect, useRef } from "react";

const ENTRIES = ".hero-copy > .builder-note, .hero-copy > .eyebrow, .hero-copy > h1, .hero-copy > .lede, .hero-copy > .hero-actions, .hero-art, .intention-strip, .tools-section > .section-heading, .tool-grid > .tool-card, .tool-header, .tool-page > .panel, .tool-page > .metrics, .graph-layout > .panel, .builder-page-hero, .builder-story, .builder-practices .panel, .builder-invitation, .tool-page > .grid-two > .panel";

/** One-time entrances and native disclosures; charts retain their exact coordinates. */
export function usePagePolish(route: string, enabled: boolean) {
  const seen = useRef(new WeakSet<Element>());
  useEffect(() => {
    const root = document.getElementById("main");
    if (!root) return;
    const animations = new Set<Animation>();
    const disclosures = new Map<HTMLDetailsElement, { animation: Animation; open: boolean }>();
    const canAnimate = () => enabled && !document.hidden && document.documentElement.dataset.input !== "keyboard" && !matchMedia("(prefers-reduced-motion: reduce)").matches;
    const observer = new IntersectionObserver(entries => {
      let stagger = 0;
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        observer.unobserve(entry.target);
        if (seen.current.has(entry.target)) continue;
        seen.current.add(entry.target);
        if (!canAnimate()) continue;
        const fadeOnly = entry.target.matches(".hero-art, .metrics, .graph-layout > .panel") || !matchMedia("(hover: hover) and (pointer: fine)").matches;
        const animation = entry.target.animate(
          fadeOnly ? [{ opacity: .4 }, { opacity: 1 }] : [{ opacity: 0, transform: "translateY(8px)" }, { opacity: 1, transform: "translateY(0)" }],
          { duration: 220, delay: Math.min(stagger++ * 40, 120), easing: "cubic-bezier(0.23, 1, 0.32, 1)" },
        );
        animations.add(animation);
        animation.onfinish = () => animations.delete(animation);
      }
    }, { threshold: .08 });
    const watch = (element: HTMLElement) => {
      if (element.matches(ENTRIES) && !seen.current.has(element)) observer.observe(element);
      element.querySelectorAll(ENTRIES).forEach(candidate => {
        if (!seen.current.has(candidate)) observer.observe(candidate);
      });
    };
    watch(root);
    const mutations = new MutationObserver(records => {
      for (const record of records) for (const node of record.addedNodes) {
        // SVG projection and text updates do not require a new page scan.
        if (node instanceof HTMLElement) watch(node);
      }
    });
    mutations.observe(root, { childList: true, subtree: true });
    const toggle = (event: MouseEvent) => {
      if (event.target instanceof Element && event.target.closest("a, button, input, select, textarea")) return;
      const summary = event.target instanceof Element ? event.target.closest("summary") : null;
      const element = summary?.parentElement;
      if (!(element instanceof HTMLDetailsElement) || element.querySelector(":scope > summary") !== summary) return;
      const prior = disclosures.get(element);
      if (event.defaultPrevented || event.detail === 0 || !canAnimate()) {
        if (prior) {
          prior.animation.cancel();
          element.open = prior.open;
          element.style.overflow = "";
          disclosures.delete(element);
        }
        return;
      }
      event.preventDefault();
      const open = !(prior ? prior.open : element.open);
      const start = element.getBoundingClientRect().height;
      prior?.animation.cancel();
      element.open = open;
      const end = element.getBoundingClientRect().height;
      element.open = true;
      element.style.overflow = "hidden";
      const animation = element.animate([{ height: `${start}px` }, { height: `${end}px` }], { duration: 240, easing: "cubic-bezier(0.23, 1, 0.32, 1)" });
      disclosures.set(element, { animation, open });
      animation.onfinish = () => {
        element.open = open;
        element.style.overflow = "";
        disclosures.delete(element);
        animation.cancel();
      };
    };
    const settle = () => {
      animations.forEach(animation => animation.cancel());
      animations.clear();
      disclosures.forEach(({ animation, open }, element) => {
        animation.cancel(); element.open = open; element.style.overflow = "";
      });
      disclosures.clear();
    };
    root.addEventListener("keydown", settle, true);
    root.addEventListener("click", toggle);
    return () => {
      observer.disconnect(); mutations.disconnect(); root.removeEventListener("click", toggle);
      root.removeEventListener("keydown", settle, true);
      settle();
    };
  }, [route, enabled]);
}
