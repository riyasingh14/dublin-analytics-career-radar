import { useEffect, useMemo, useRef, useState } from "react";
import { Route, Download, ArrowRight } from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  BarChart,
  Bar,
  Legend,
} from "recharts";
import { api, Bootstrap, downloadJSON, format } from "../lib/api";
import { radialPath, sankeyLayout } from "./mobilityLayout";
const LABEL = "Synthetic scenario — not observed labour-market outcomes";
const defaults = {
  seed: 42,
  people: 500,
  years: 5,
  employer_change_pct: 4,
  promotion_pct: 8,
  occupation_change_pct: 2,
};
type Flow = { origin: string; destination: string; events: number; valid_pairs: number;
  median_individual_pct_change: number | null; comparison_available: boolean };
const flowKey = (flow: Flow) => flow.origin + " → " + flow.destination;
const flowColor = (flow: Flow) => flow.median_individual_pct_change == null ? "#8a948e" : flow.median_individual_pct_change >= 0 ? "#36826b" : "#c6754d";
function FlowPath({ flow, path, selected, onSelect, width, directed = false }: { flow: Flow; path: string; selected: string; onSelect: (value: string) => void; width?: number; directed?: boolean }) {
  const key = flowKey(flow);
  return <path d={path} fill="none" stroke={flowColor(flow)} strokeOpacity={selected && selected !== key ? .15 : .7}
    strokeWidth={width ?? Math.min(15, 2 + Math.sqrt(flow.events))} markerEnd={directed ? `url(#mobility-arrow-${flow.median_individual_pct_change == null ? "neutral" : flow.median_individual_pct_change >= 0 ? "positive" : "negative"})` : undefined} role="button" tabIndex={0}
    aria-label={`Inspect ${key}: ${flow.events} synthetic events`} aria-pressed={selected === key}
    onClick={() => onSelect(key)} onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSelect(key); } }}
    style={{ cursor: "pointer" }}>
    <title>{key}: {flow.events} synthetic events; {flow.valid_pairs} valid salary pairs. Median individual change: {flow.comparison_available ? format(flow.median_individual_pct_change, 1, "%") : "suppressed below 20 pairs"}. {LABEL}</title>
  </path>;
}
function NetworkChart({ flows, occupations, selected, onSelect }: { flows: Flow[]; occupations: string[]; selected: string; onSelect: (value: string) => void }) {
  const states = occupations.filter(o => o !== "Career break").flatMap(o => ["Junior", "Mid", "Senior", "Lead"].map(l => o + " / " + l)).concat("Career break / Not employed").sort();
  const point = (state: string): [number, number] => { const angle = 2 * Math.PI * states.indexOf(state) / states.length - Math.PI / 2; return [400 + 265 * Math.cos(angle), 280 + 205 * Math.sin(angle)]; };
  const nodes = Array.from(new Set(flows.flatMap(f => [f.origin, f.destination])));
  return <svg viewBox="0 0 800 580" className="mobility-network" role="group" aria-label="Synthetic career state transitions; select an edge to inspect its cohort">
    <defs>{[["neutral", "#8a948e"], ["positive", "#36826b"], ["negative", "#c6754d"]].map(([id,color]) => <marker key={id} id={`mobility-arrow-${id}`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" fill={color} /></marker>)}</defs>
    <circle cx="400" cy="280" r="70" fill="#f1f3ed" />
    <text x="400" y="275" textAnchor="middle" className="center-label">CAREER MOVES</text><text x="400" y="296" textAnchor="middle" className="diagram-note">SYNTHETIC</text>
    {flows.map(f => { const a = point(f.origin), b = point(f.destination); return <FlowPath key={flowKey(f)} flow={f} path={radialPath(a,b,f.origin === f.destination)} directed selected={selected} onSelect={onSelect} />; })}
    {nodes.map(n => { const [x, y] = point(n); return <g key={n} style={{ pointerEvents: "none" }}><circle cx={x} cy={y} r="6" fill="#214f43" /><text x={x} y={y < 280 ? y - 17 : y + 19} textAnchor="middle" style={{fontSize: 9}}>{n.split(" / ")[0].replace("Specialist", "Spec.").replace("Coordinator", "Coord.").replace("Engineer", "Eng.")}<tspan x={x} dy="11">{n.split(" / ")[1]}</tspan></text><title>{n} · {LABEL}</title></g>; })}
  </svg>;
}
function FlowChart({ flows, selected, onSelect }: { flows: Flow[]; selected: string; onSelect: (value: string) => void }) {
  const layout = sankeyLayout(flows);
  return <svg viewBox={`0 0 800 ${layout.height}`} className="flow-chart" role="group" aria-label="Synthetic origin to destination flows, widths indicate event counts">
    <text x="230" y="12" textAnchor="end">ORIGIN · {layout.total} EVENTS</text><text x="566" y="12">DESTINATION</text>
    {layout.links.map(link => <FlowPath key={flowKey(link.flow as Flow)} flow={link.flow as Flow} path={link.path} width={link.width} selected={selected} onSelect={onSelect} />)}
    {layout.left.map(n => <g key={n.name}><rect x="238" y={n.y} width="7" height={n.height} fill="#1d5f4e" data-events={n.events} data-side="origin" /><text x="230" y={n.y+n.height/2+4} textAnchor="end">{n.name.replace("Specialist", "Spec.").replace("Coordinator", "Coord.")}</text><title>{n.name}: {n.events} outgoing synthetic events</title></g>)}
    {layout.right.map(n => <g key={n.name}><rect x="555" y={n.y} width="7" height={n.height} fill="#bc704b" data-events={n.events} data-side="destination" /><text x="566" y={n.y+n.height/2+4}>{n.name.replace("Specialist", "Spec.").replace("Coordinator", "Coord.")}</text><title>{n.name}: {n.events} incoming synthetic events</title></g>)}
  </svg>;
}
function TransitionMatrix({ flows, selected, onSelect }: { flows: Flow[]; selected: string; onSelect: (value: string) => void }) {
  const origins = [...new Set(flows.map(f => f.origin))].sort(), destinations = [...new Set(flows.map(f => f.destination))].sort();
  const lookup = new Map(flows.map(f => [flowKey(f), f]));
  const maximum = Math.max(1, ...flows.map(f => f.events));
  return <div className="table-wrap" style={{maxHeight: 560, overflow: "auto"}} tabIndex={0} role="region" aria-label="Scrollable transition matrix"><table><caption>Synthetic transition counts · all filtered flows</caption><thead><tr><th>Origin ↓ / Destination →</th>{destinations.map(n => <th key={n}>{n}</th>)}</tr></thead><tbody>{origins.map(origin => <tr key={origin}><th scope="row">{origin}</th>{destinations.map(destination => { const key = origin + " → " + destination, f = lookup.get(key); return <td key={destination}>{f ? <button className="button-secondary" aria-label={`Inspect ${key}: ${f.events} synthetic events`} aria-pressed={selected === key} onClick={() => onSelect(key)} style={{ background: `rgba(36,107,89,${.07 + .45 * f.events/maximum})`, minWidth: 56 }} title={`${f.events} events; ${f.valid_pairs} valid pairs; median ${f.comparison_available ? format(f.median_individual_pct_change, 1, "%") : "suppressed"}. ${LABEL}`}>{f.events}</button> : <span aria-label="No events">—</span>}</td>; })}</tr>)}</tbody></table></div>;
}
export default function Mobility(_props: { bootstrap: Bootstrap | null }) {
  const [scenario, setScenario] = useState(defaults),
    [active, setActive] = useState(defaults),
    [filters, setFilters] = useState<Record<string, string>>({}),
    [flow, setFlow] = useState(""),
    [person, setPerson] = useState(""),
    [result, setResult] = useState<any>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [chart, setChart] = useState("network"),
    [focus, setFocus] = useState(""),
    [edgeLimit, setEdgeLimit] = useState(20);
  const controller = useRef<AbortController | null>(null);
  useEffect(() => {
    controller.current?.abort();
    const c = new AbortController();
    controller.current = c;
    setBusy(true);
    setError("");
    api(
      "mobility",
      { scenario: active, filters, flow, person_id: person },
      c.signal,
    )
      .then(setResult)
      .catch((e) => {
        if (e.name !== "AbortError") {
          setError(e.message);
          setResult(null);
        }
      })
      .finally(() => {
        if (!c.signal.aborted) setBusy(false);
      });
    return () => c.abort();
  }, [active, filters, flow, person]);
  const hist = useMemo(() => {
    const bins = new Map<number, any>();
    for (const name of ["before", "after"])
      for (const value of result?.distributions?.[name] || []) {
        const bin = Math.floor(value / 10000) * 10000;
        const row = bins.get(bin) || {
          salary: bin,
          label: "€" + bin / 1000 + "k",
          before: 0,
          after: 0,
        };
        row[name]++;
        bins.set(bin, row);
      }
    return [...bins.values()].sort((a, b) => a.salary - b.salary);
  }, [result]);
  const setFilter = (name: string, value: string) => {
    setFilters({ ...filters, [name]: value });
    setFlow("");
    setPerson("");
  };
  const allFlows: Flow[] = result?.context_flows || result?.flows || [];
  const focusFlows = allFlows.filter(f => !focus || (f.origin + " " + f.destination).toLowerCase().includes(focus.toLowerCase()));
  const shown = focusFlows.slice(0, edgeLimit),
    metrics = result?.metrics;
  const inspectFlow = (value: string) => { setFlow(value); setPerson(""); };
  const currency = (n: number) => "€" + Math.round(n / 1000) + "k";
  return (
    <section className="tool-page">
      <div className="tool-header">
        <div>
          <p className="eyebrow">03 / SYNTHETIC SCENARIOS</p>
          <h1>Career Mobility Lab</h1>
          <p className="lede">
            Explore the paths between roles. Examine the assumptions behind each
            result.
          </p>
        </div>
        <div className="tool-symbol">
          <Route size={38} />
        </div>
      </div>
      <div className="notice">
        <strong>{LABEL}.</strong> Generated histories demonstrate analytical
        methods. They do not predict real salaries, actual transition likelihood
        or causal effects.
      </div>
      <details className="panel">
        <summary>Scenario controls and generator assumptions</summary>
        <p>
          Annual full-time-equivalent base salary in EUR, no bonus or inflation
          adjustment. Every person has one annual observation, including
          explicit career breaks. Initial pay depends on level, experience and a
          seeded random offset. The model includes unchanged pay and pay cuts.
        </p>
        <p>
          Annual move probabilities are illustrative: employer change 24%,
          occupation change 12%, promotion 14% below Lead, break 4.5%. Annual
          noise is drawn from 0, 0, −12, −6, −3, 2, 4, 8 percentage points. The
          increments below are added when a move occurs. These assumptions are
          not calibrated Irish rates.
        </p>
        <div className="filter-bar">
          <label className="field">
            Synthetic people
            <select
              value={scenario.people}
              onChange={(e) =>
                setScenario({ ...scenario, people: Number(e.target.value) })
              }
            >
              <option value={500}>500 people</option>
              <option value={1000}>1,000 people</option>
            </select>
          </label>
          <label className="field">
            Seed
            <input
              type="number"
              min={0}
              max={999999}
              value={scenario.seed}
              onChange={(e) =>
                setScenario({ ...scenario, seed: Number(e.target.value) })
              }
            />
          </label>
          <label className="field">
            Years
            <input
              type="number"
              min={3}
              max={8}
              value={scenario.years}
              onChange={(e) =>
                setScenario({ ...scenario, years: Number(e.target.value) })
              }
            />
          </label>
        </div>
        <div className="grid-three">
          {[
            ["employer_change_pct", "Employer-change increment"],
            ["promotion_pct", "Promotion increment"],
            ["occupation_change_pct", "Occupation-change increment"],
          ].map(([key, label]) => (
            <label className="field" key={key}>
              {label} · {scenario[key as keyof typeof scenario]} pp
              <input
                type="range"
                min={-15}
                max={20}
                value={scenario[key as keyof typeof scenario]}
                onChange={(e) =>
                  setScenario({ ...scenario, [key]: Number(e.target.value) })
                }
              />
            </label>
          ))}
        </div>
        <div className="action-row">
          <button
            className="button"
            onClick={() => {
              setActive({ ...scenario });
              setFilters({});
              setFlow("");
              setPerson("");
            }}
            disabled={busy}
          >
            Apply scenario <ArrowRight size={16} />
          </button>
          <button
            className="button-secondary"
            onClick={() => {
              setScenario(defaults);
              setActive(defaults);
              setFilters({});
              setFlow("");
              setPerson("");
            }}
          >
            Reset baseline
          </button>
        </div>
        <p className="caption">
          Same seed preserves structural events across scenarios; changed
          increments affect pay. Geography is fixed per person. Industry belongs
          to the employer; it is not an occupation.
        </p>
      </details>
      {error && (
        <div><p className="error" role="alert">{error}</p><button className="button-secondary" onClick={() => { setFilters({}); setFlow(""); setPerson(""); }}>Clear cohort filters</button></div>
      )}
      {busy && (
        <p role="status" className="muted">
          Generating the scenario and recalculating cohorts…
        </p>
      )}
      {result && (
        <>
          <div className="filter-bar">
            <label className="field">
              Origin occupation
              <select
                aria-label="Origin occupation"
                value={filters.origin || ""}
                onChange={(e) => setFilter("origin", e.target.value)}
              >
                <option value="">All origins</option>
                {result.occupation_options.map((n: string) => (
                  <option key={n}>{n}</option>
                ))}
              </select>
            </label>
            <label className="field">
              Destination occupation
              <select
                aria-label="Destination occupation"
                value={filters.destination || ""}
                onChange={(e) => setFilter("destination", e.target.value)}
              >
                <option value="">All destinations</option>
                {result.occupation_options.map((n: string) => (
                  <option key={n}>{n}</option>
                ))}
              </select>
            </label>
            <label className="field">
              Geography
              <select
                aria-label="Geography"
                value={filters.geography || ""}
                onChange={(e) => setFilter("geography", e.target.value)}
              >
                <option value="">All locations</option>
                {result.geography_options.map((n: string) => (
                  <option key={n}>{n}</option>
                ))}
              </select>
            </label>
            <label className="field">
              Transition type
              <select
                aria-label="Transition type"
                value={filters.category || ""}
                onChange={(e) => setFilter("category", e.target.value)}
              >
                <option value="">All groups</option>
                {result.category_options.map((n: string) => (
                  <option key={n}>{n}</option>
                ))}
              </select>
            </label>
          </div>
          <details className="panel"><summary>Compare within seniority, industry, experience and period</summary><div className="filter-bar">
            {[["origin_seniority", "Origin seniority"], ["destination_seniority", "Destination seniority"], ["origin_industry", "Origin employer industry"], ["destination_industry", "Destination employer industry"]].map(([key, label]) => <label className="field" key={key}>{label}<select aria-label={label} value={filters[key] || ""} onChange={e => setFilter(key, e.target.value)}><option value="">All</option>{(key.includes("seniority") ? ["Junior", "Mid", "Senior", "Lead", "Not employed"] : result.industry_options).map((value: string) => <option key={value}>{value}</option>)}</select></label>)}
            {[["experience_min", "Minimum experience years"], ["experience_max", "Maximum experience years"], ["year_min", "From transition year"], ["year_max", "Through transition year"]].map(([key, label]) => <label className="field" key={key}>{label}<input aria-label={label} type="number" min={key.startsWith("year") ? 2022 : 0} max={key.startsWith("year") ? 2028 : 100} value={filters[key] || ""} onChange={e => setFilter(key, e.target.value)} /></label>)}
          </div><p className="caption">Experience is measured before each transition; period uses the destination spell start year. Every metric, distribution and event table uses these same cuts.</p></details>
          <div className="metrics">
            <div className="metric">
              <span>Transition events</span>
              <strong>{format(metrics.events, 0)}</strong>
              <small>Events, not independent people</small>
            </div>
            <div className="metric">
              <span>Distinct people</span>
              <strong>{format(metrics.people, 0)}</strong>
              <small>In the selected synthetic cohort</small>
            </div>
            <div className="metric">
              <span>Valid salary pairs</span>
              <strong>{format(metrics.valid_pairs, 0)}</strong>
              <small>{metrics.excluded_pairs} excluded pairs</small>
            </div>
            <div className="metric">
              <span>Median individual change</span>
              <strong>
                {metrics.comparison_available
                  ? format(metrics.median_individual_pct_change, 1, "%")
                  : "Suppressed"}
              </strong>
              <small>Minimum 20 valid pairs</small>
            </div>
          </div>
          {metrics.events === 0 ? (
            <div className="empty-state">
              <h2>No events in this cohort.</h2>
              <p>Broaden the filters to explore another scenario.</p>
              <button
                className="button-secondary"
                onClick={() => {
                  setFilters({});
                  setFlow("");
                  setPerson("");
                }}
              >
                Clear cohort filters
              </button>
            </div>
          ) : (
            <>
              <article className="panel">
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">THE PATHS BETWEEN STATES</p>
                    <h2>Every move has a context.</h2>
                  </div>
                  <div
                    className="tabs"
                    role="group"
                    aria-label="Mobility visualisation"
                  >
                    {[
                      ["network", "Radial"],
                      ["flow", "Flow"],
                      ["heatmap", "Matrix"],
                    ].map(([id, label]) => (
                      <button
                        aria-pressed={chart === id}
                        onClick={() => setChart(id)}
                        key={id}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>
                <label className="field">
                  Inspect a flow
                  <select
                    aria-label="Inspect a flow"
                    value={flow}
                    onChange={(e) => {
                      setFlow(e.target.value);
                      setPerson("");
                    }}
                  >
                    <option value="">All filtered flows</option>
                    {allFlows.map((f: any) => (
                      <option
                        key={f.origin + f.destination}
                        value={f.origin + " → " + f.destination}
                      >
                        {f.origin} → {f.destination}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="filter-bar"><label className="field">Find a career state<input aria-label="Find a career state" placeholder="Occupation or seniority" value={focus} onChange={e => setFocus(e.target.value)} /></label><label className="field">Visible graph edges<select aria-label="Visible graph edges" value={edgeLimit} onChange={e => setEdgeLimit(Number(e.target.value))}><option value={10}>10</option><option value={20}>20</option><option value={40}>40</option></select></label><button className="button-secondary" onClick={() => { inspectFlow(""); setFocus(""); }}>Clear flow selection</button></div>
                {chart === "network" ? <NetworkChart flows={shown} occupations={result.occupation_options} selected={flow} onSelect={inspectFlow} /> : chart === "flow" ? <FlowChart flows={shown} selected={flow} onSelect={inspectFlow} /> : <TransitionMatrix flows={focusFlows} selected={flow} onSelect={inspectFlow} />}
                {!focusFlows.length && <p role="status">No career states match this search. Clear it to restore the graph.</p>}
                <p className="caption">{LABEL}. {result.metadata.generator_version}; {metrics.events} selected events. Graph shows {shown.length} of {focusFlows.length} matching flows; matrix contains all matching flows. Nodes stay in fixed occupation/seniority positions. Sankey link widths and node heights share one count scale and conserve the visible event total; radial width uses a square-root scale. Arrowheads show radial direction and reciprocal paths bend apart. Green = non-negative median change, terracotta = negative, grey = fewer than 20 valid pairs. Select a path or matrix cell to link the cohort metrics, distributions and timeline. Self-loops retain the same occupation and seniority; employer changes may still occur.</p>
              </article>
              {metrics.comparison_available ? (
                <div className="grid-two">
                  <article className="panel">
                    <p className="eyebrow">COMPENSATION DISTRIBUTIONS</p>
                    <h2>Look beyond the median.</h2>
                    <div className="chart-box">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={hist}>
                          <CartesianGrid
                            strokeDasharray="3 3"
                            vertical={false}
                          />
                          <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                          <YAxis tick={{ fontSize: 11 }} />
                          <Tooltip />
                          <Legend />
                          <Bar
                            dataKey="before"
                            name="Before"
                            fill="#2a6d59"
                            radius={[3, 3, 0, 0]}
                          />
                          <Bar
                            dataKey="after"
                            name="After"
                            fill="#bf784f"
                            radius={[3, 3, 0, 0]}
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                    <p className="caption">
                      Synthetic annual FTE salary in €10k bins.
                      Transition-weighted, not person-weighted. Before median{" "}
                      {currency(metrics.median_before_salary)}; after median{" "}
                      {currency(metrics.median_after_salary)}.
                    </p>
                  </article>
                  <article className="panel">
                    <p className="eyebrow">OUTCOMES IN THIS SCENARIO</p>
                    <h2>Changes include decreases.</h2>
                    <dl className="definition-list">
                      <div>
                        <dt>Individual change IQR</dt>
                        <dd>{format(metrics.individual_change_iqr, 1)} pp</dd>
                      </div>
                      <div>
                        <dt>Share with a decrease</dt>
                        <dd>{format(metrics.share_decreased * 100, 1, "%")}</dd>
                      </div>
                      <div>
                        <dt>Change between cohort medians</dt>
                        <dd>
                          {format(
                            metrics.change_between_cohort_medians_pct,
                            1,
                            "%",
                          )}
                        </dd>
                      </div>
                      <div>
                        <dt>Distinct people with valid pairs</dt>
                        <dd>{metrics.valid_people}</dd>
                      </div>
                    </dl>
                    <p className="caption">
                      The change between cohort medians differs from the median
                      of individual percentage changes. Neither is a real-world
                      salary return.
                    </p>
                  </article>
                </div>
              ) : (
                <p className="notice">
                  Salary comparisons are suppressed below 20 valid pairs.
                  Individual synthetic examples remain inspectable.
                </p>
              )}
              <article className="panel">
                <h2>Compare assumptions, not promises.</h2>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Scenario</th>
                        <th>Events</th>
                        <th>People</th>
                        <th>Valid pairs</th>
                        <th>Median individual change</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.comparisons.map((c: any) => (
                        <tr key={c.name}>
                          <td>{c.name}</td>
                          <td>{c.events}</td>
                          <td>{c.people}</td>
                          <td>{c.valid_pairs}</td>
                          <td>
                            {format(c.median_individual_pct_change, 1, "%")}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="caption">
                  The origin-state stayer reference retains origin occupation/seniority, origin employer industry, geography, experience and period cuts. It releases destination, selected flow and transition-type constraints so promotion and occupation-change flows can have a relevant stayer reference. Only origin states represented in your selected cohort are included. This is a different descriptive cohort, not a matched control group or causal estimate.
                </p>
              </article>
              <article className="panel"><p className="eyebrow">LINKED COHORT EVIDENCE</p><h2>Inspect the transition events.</h2><p className="caption">{LABEL}. Showing the first {result.transition_rows?.length || 0} of {result.transition_rows_total ?? metrics.events} events, ordered by date and transition ID. Select a synthetic person to inspect their full timeline. Aggregate salary comparisons remain suppressed below 20 pairs; these rows are individual fictional examples.</p><div className="table-wrap" style={{maxHeight: 440, overflow: "auto"}} tabIndex={0} role="region" aria-label="Scrollable synthetic event evidence"><table><thead><tr><th>Person / event</th><th>Year</th><th>Origin</th><th>Destination</th><th>Move flags</th><th>Before EUR</th><th>After EUR</th><th>Individual change</th></tr></thead><tbody>{(result.transition_rows || []).map((r: any) => <tr key={r.transition_id}><td><button className="button-secondary" onClick={() => setPerson(r.person_id)} aria-label={`Inspect timeline ${r.transition_id}`}>{r.person_id}</button><small>{r.transition_id}</small></td><td>{r.date.slice(0,4)}</td><td>{r.origin_state}</td><td>{r.destination_state}</td><td>{r.category}</td><td>{format(r.before_salary,0)}</td><td>{format(r.after_salary,0)}</td><td>{format(r.individual_pct_change,1,"%")}{!r.valid_pair && "Excluded pair"}</td></tr>)}</tbody></table></div></article>
              <article className="panel" aria-busy={busy}>
                <div className="panel-heading">
                  <div>
                    <p className="eyebrow">ONE SYNTHETIC HISTORY</p>
                    <h2>A trajectory, not a prediction.</h2>
                  </div>
                  <label className="field compact">
                    Person
                    <select
                      aria-label="Person"
                      value={result.selected_person}
                      onChange={(e) => setPerson(e.target.value)}
                    >
                      {result.people_ids.map((id: string) => (
                        <option key={id}>{id}</option>
                      ))}
                    </select>
                  </label>
                </div>
                <div className="chart-box">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={result.trajectory}>
                      <CartesianGrid vertical={false} strokeDasharray="3 3" />
                      <XAxis
                        dataKey="start_date"
                        tickFormatter={(v) => String(v).slice(0, 4)}
                      />
                      <YAxis tickFormatter={currency} />
                      <Tooltip
                        formatter={(v) => format(Number(v), 0, " EUR")}
                      />
                      <Line
                        type="linear"
                        dataKey="salary_eur_annual_fte"
                        name="Synthetic annual FTE salary"
                        connectNulls={false}
                        stroke="#276d59"
                        strokeWidth={3}
                        dot={{ r: 5 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Year</th>
                        <th>Occupation</th>
                        <th>Seniority</th>
                        <th>Industry</th>
                        <th>Annual FTE EUR</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.trajectory.map((s: any) => (
                        <tr key={s.spell_id}>
                          <td>{s.start_date.slice(0, 4)}</td>
                          <td>{s.occupation}</td>
                          <td>{s.seniority}</td>
                          <td>{s.industry}</td>
                          <td>{format(s.salary_eur_annual_fte, 0)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="caption">
                  Breaks are gaps, not zero salaries. This full example history
                  can extend beyond the currently selected transition cohort.
                </p>
              </article>
              <div className="export-panel">
                <div>
                  <h3>Reproduce the scenario.</h3>
                  <p>
                    Download the generator parameters, cohort metrics and data
                    labels. All outputs remain synthetic.
                  </p>
                </div>
                <button
                  className="button-secondary"
                  onClick={() =>
                    downloadJSON("synthetic-mobility-analysis.json", {
                      ...result,
                      data_label: LABEL,
                    })
                  }
                >
                  <Download size={16} />
                  Download scenario
                </button>
              </div>
            </>
          )}
        </>
      )}
    </section>
  );
}
