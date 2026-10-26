import { useEffect, useRef } from "react";
import { ChevronDown, ShieldCheck } from "lucide-react";
import { Bootstrap } from "../lib/api";

export default function DataCoverage({ bootstrap }: { bootstrap: Bootstrap | null }) {
  const snapshot = bootstrap?.snapshot;
  const disclosure = useRef<HTMLDetailsElement>(null);
  const animation = useRef<Animation | null>(null);
  const targetOpen = useRef(false);
  useEffect(() => () => { animation.current?.cancel(); }, []);
  function toggle(event: React.MouseEvent<HTMLElement>) {
    const element = disclosure.current;
    if (!element) return;
    // Native keyboard toggles remain immediate; pointer toggles animate both ways.
    const animate = event.detail > 0 && document.documentElement.dataset.motion === "active" && !matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!animate) {
      animation.current?.cancel();
      animation.current = null;
      element.style.overflow = "";
      return;
    }
    event.preventDefault();
    const next = !(animation.current ? targetOpen.current : element.open);
    const startHeight = element.getBoundingClientRect().height;
    animation.current?.cancel();
    targetOpen.current = next;
    element.open = next;
    const endHeight = element.getBoundingClientRect().height;
    // Keep the content rendered through a closing transition.
    element.open = true;
    element.style.overflow = "hidden";
    const current = element.animate([{ height: `${startHeight}px` }, { height: `${endHeight}px` }], {
      duration: 240, easing: "cubic-bezier(0.23, 1, 0.32, 1)",
    });
    animation.current = current;
    current.onfinish = () => {
      element.open = next;
      element.style.overflow = "";
      animation.current = null;
      current.cancel();
    };
  }
  return (
    <details className="coverage-passport" ref={disclosure}>
      <summary onClick={toggle}>
        <span className="passport-symbol" aria-hidden="true"><ShieldCheck size={24} /></span>
        <span className="passport-intro"><span className="passport-title">Data passport <span className="passport-badge">DEMO DATA</span></span><span className="passport-purpose">Know what’s behind the numbers: sources, sample sizes and limits.</span></span>
        <span className="passport-toggle"><span className="passport-closed-label">View data details</span><span className="passport-open-label">Hide data details</span><ChevronDown size={17} aria-hidden="true" /></span>
      </summary>
      <div className="passport-content"><p className="passport-explainer">A good chart starts with knowing its evidence. This passport tells you which examples are fictional, which descriptions come from archived employers, and how to interpret the results.</p>
      <dl className="coverage-grid">
        <div><dt>Public skill sample</dt><dd>{snapshot ? `${snapshot.market.sample_size} postings · fictional` : "Waiting for the API"}</dd></div>
        <div><dt>Source coverage</dt><dd>Authored fixture; no observed job-feed coverage</dd></div>
        <div><dt>Geography</dt><dd>Dublin and rest of Ireland; generated locations</dd></div>
        <div><dt>Collection window</dt><dd>Not applicable — generated, not collected</dd></div>
        <div><dt>Fixture built</dt><dd>{snapshot?.metadata?.generated_at ? new Date(snapshot.metadata.generated_at).toLocaleString("en-IE", { timeZone: "Europe/Dublin", dateStyle: "medium", timeStyle: "short" }) + " · Dublin time" : "Not available"}</dd></div>
        <div><dt>Extraction</dt><dd>Exact alias rules · taxonomy-v2-tech</dd></div>
        <div><dt>Review status</dt><dd>Demonstration fixture; no human-reviewed market release</dd></div>
        <div><dt>Description examples</dt><dd>{bootstrap?.description_samples?.length || 0} attributed, archived US employer descriptions · CC0 · not live vacancies</dd></div>
        <div><dt>Other inputs</dt><dd>Pasted descriptions: source unverified. Candidate evidence: self-reported. Mobility: synthetic.</dd></div>
      </dl>
      <p className="caption">Fixture generation time is not a collection date. Role comparison has its own labelled fixture and denominators. No complete Irish-market coverage or hiring outcomes are implied.</p>
      <a className="text-link" href="#/methodology">Read the full methods and limitations</a>
      </div>
    </details>
  );
}
