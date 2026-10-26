import { useState } from "react";
import { ChevronDown, ShieldCheck, Database, Layers, MapPin, CalendarDays, Clock, ScanText, FileText, UserRound } from "lucide-react";
import { Bootstrap } from "../lib/api";

const GROUPS = [{ id: "all", label: "All details" }, { id: "dataset", label: "Dataset" }, { id: "method", label: "Methods & review" }, { id: "inputs", label: "Other inputs" }];

export default function DataCoverage({ bootstrap }: { bootstrap: Bootstrap | null }) {
  const [group, setGroup] = useState("all");
  const snapshot = bootstrap?.snapshot;
  const generated = snapshot?.metadata?.generated_at ? new Date(snapshot.metadata.generated_at) : null;
  const fields = [
    { title: "Public skill sample", group: "dataset", icon: Database, value: snapshot ? `${snapshot.market.sample_size} postings · fictional` : "Waiting for the API", why: "This is the network’s denominator. It includes postings with no extracted skills, so missing matches do not inflate the shares." },
    { title: "Source coverage", group: "dataset", icon: Layers, value: "Authored fixture; no observed job-feed coverage", why: "A source tells you what a sample can represent. These examples demonstrate the method; they cannot establish current Irish hiring demand." },
    { title: "Geography", group: "dataset", icon: MapPin, value: "Dublin and rest of Ireland; generated locations", why: "Location filters change which examples are counted. These generated locations are not evidence of geographic market coverage." },
    { title: "Collection window", group: "dataset", icon: CalendarDays, value: "Not applicable — generated, not collected", why: "A real snapshot needs a collection window to explain how current it is. The demo has no collection date to report." },
    { title: "Fixture built", group: "dataset", icon: Clock, value: generated && !Number.isNaN(generated.getTime()) ? generated.toLocaleString("en-IE", { timeZone: "Europe/Dublin", dateStyle: "medium", timeStyle: "short" }) + " · Dublin time" : "Not available", why: "Generation time identifies the demo fixture. It is separate from a job’s posting date and from any future collection timestamp." },
    { title: "Extraction", group: "method", icon: ScanText, value: "Exact alias rules · taxonomy-v2-tech", why: "Controlled phrases make a match traceable to source text. A mention still needs its context checked before it is treated as a requirement." },
    { title: "Review status", group: "method", icon: ShieldCheck, value: "Demonstration fixture; no human-reviewed market release", why: "Passing software tests does not measure extraction accuracy on real vacancies. Human review is a separate requirement for a real-data release." },
    { title: "Description examples", group: "inputs", icon: FileText, value: bootstrap ? `${bootstrap.description_samples?.length || 0} attributed, archived US employer descriptions · CC0 · not live vacancies` : "Waiting for the reference library", why: "These historical employer-written examples let you try document analysis. Their source, licence and country are shown separately from the fictional market sample." },
    { title: "Other inputs", group: "inputs", icon: UserRound, value: "Pasted descriptions: source unverified. Candidate evidence: self-reported. Mobility: synthetic.", why: "Different inputs support different conclusions. A self-reported skill is not verified candidate evidence, and a simulated salary change is not an observed career outcome." },
  ];
  const visible = fields.filter(field => group === "all" || field.group === group);
  return <details className="coverage-passport">
    <summary>
      <span className="passport-symbol" aria-hidden="true"><ShieldCheck size={24} /></span>
      <span className="passport-intro"><span className="passport-title">Data passport <span className="passport-badge">DEMO DATA</span></span><span className="passport-purpose">Know what’s behind the numbers: sources, sample sizes and limits.</span></span>
      <span className="passport-toggle"><span className="passport-closed-label">View data details</span><span className="passport-open-label">Hide data details</span><ChevronDown size={17} aria-hidden="true" /></span>
    </summary>
    <div className="passport-content">
      <p className="passport-explainer">A good chart starts with knowing its evidence. Explore a category, then open “Why this matters” to see how each detail affects the analysis.</p>
      <div className="passport-filters" role="group" aria-label="Filter data passport details">{GROUPS.map(item => <button type="button" key={item.id} aria-pressed={group === item.id} aria-controls="passport-fields" onClick={() => setGroup(item.id)}>{item.label}<span>{item.id === "all" ? fields.length : fields.filter(field => field.group === item.id).length}</span></button>)}</div>
      <p className="passport-result-count" role="status" aria-live="polite">Showing {visible.length} of {fields.length} details</p>
      <dl className="coverage-grid" id="passport-fields">{visible.map(({ title, icon: Icon, value, why, group: category }) => <div className={`passport-fact passport-fact-${category}`} key={title}>
        <dt><span className="passport-fact-icon" aria-hidden="true"><Icon size={20} /></span><span>{title}</span></dt>
        <dd>{value}</dd>
        <dd className="passport-why"><details><summary>Why this matters <ChevronDown size={13} aria-hidden="true" /></summary><p>{why}</p></details></dd>
      </div>)}</dl>
      <p className="caption">Fixture generation time is not a collection date. Role comparison has its own labelled fixture and denominators. No complete Irish-market coverage or hiring outcomes are implied.</p>
      <a className="text-link" href="#/methodology">Read the full methods and limitations</a>
    </div>
  </details>;
}
