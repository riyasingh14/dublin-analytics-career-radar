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
const LABEL = "Synthetic scenario — not observed labour-market outcomes";
const defaults = {
  seed: 42,
  people: 500,
  years: 5,
  employer_change_pct: 4,
  promotion_pct: 8,
  occupation_change_pct: 2,
};
function NetworkChart({
  flows,
  occupations,
}: {
  flows: any[];
  occupations: string[];
}) {
  const states = occupations
    .filter((o) => o !== "Career break")
    .flatMap((o) =>
      ["Junior", "Mid", "Senior", "Lead"].map((l) => o + " / " + l),
    )
    .concat("Career break / Not employed")
    .sort();
  const point = (n: string) => {
    const a = (2 * Math.PI * states.indexOf(n)) / states.length - Math.PI / 2;
    return [320 + 220 * Math.cos(a), 230 + 170 * Math.sin(a)];
  };
  const nodes = Array.from(
    new Set<string>(flows.flatMap((f) => [f.origin, f.destination])),
  );
  return (
    <svg
      viewBox="0 0 640 470"
      className="mobility-network"
      role="img"
      aria-label="Synthetic career state transitions; use the flow selector and table for exact values"
    >
      <circle cx="320" cy="230" r="65" fill="#f1f3ed" />
      <text x="320" y="225" textAnchor="middle" className="center-label">
        CAREER MOVES
      </text>
      <text x="320" y="246" textAnchor="middle" className="diagram-note">
        SYNTHETIC
      </text>
      {flows.map((f: any) => {
        const a = point(f.origin),
          b = point(f.destination),
          v = f.median_individual_pct_change;
        return (
          <path
            key={f.origin + f.destination}
            d={
              f.origin === f.destination
                ? `M${a[0]} ${a[1]} c-25 -30 25 -30 0 0`
                : `M${a[0]} ${a[1]} Q320 230 ${b[0]} ${b[1]}`
            }
            fill="none"
            stroke={v == null ? "#acb4ad" : v >= 0 ? "#36826b" : "#c6754d"}
            strokeOpacity=".55"
            strokeWidth={Math.min(12, 1 + Math.sqrt(f.events))}
          >
            <title>
              {f.origin} → {f.destination}: {f.events} synthetic events. Median
              individual salary change: {format(v, 1, "%")}
            </title>
          </path>
        );
      })}
      {nodes.map((n) => {
        const [x, y] = point(n);
        return (
          <g key={n}>
            <circle
              cx={x}
              cy={y}
              r="8"
              fill="#214f43"
              stroke="#f8f7f2"
              strokeWidth="3"
            />
            <text x={x} y={y < 230 ? y - 15 : y + 24} textAnchor="middle">
              {n
                .split(" / ")[0]
                .replace("Specialist", "Spec.")
                .replace("Coordinator", "Coord.")
                .replace("Engineer", "Eng.")}
              <tspan x={x} dy="11">
                {n.split(" / ")[1]}
              </tspan>
            </text>
            <title>
              {n} · {LABEL}
            </title>
          </g>
        );
      })}
    </svg>
  );
}
function FlowChart({ flows }: { flows: any[] }) {
  const origins = Array.from(new Set<string>(flows.map((f) => f.origin))),
    destinations = Array.from(new Set<string>(flows.map((f) => f.destination))),
    h = Math.max(450, Math.max(origins.length, destinations.length) * 30 + 30),
    left = (n: string) =>
      25 + (origins.indexOf(n) * (h - 50)) / Math.max(origins.length - 1, 1),
    right = (n: string) =>
      25 +
      (destinations.indexOf(n) * (h - 50)) /
        Math.max(destinations.length - 1, 1);
  return (
    <svg
      viewBox={`0 0 740 ${h}`}
      className="flow-chart"
      role="img"
      aria-label="Synthetic origin to destination flows, widths indicate event counts"
    >
      {flows.map((f) => (
        <path
          key={f.origin + f.destination}
          d={`M215 ${left(f.origin)} C340 ${left(f.origin)},400 ${right(f.destination)},525 ${right(f.destination)}`}
          fill="none"
          stroke="#4c937b"
          strokeOpacity=".35"
          strokeWidth={Math.min(24, 2 + Math.sqrt(f.events))}
        >
          <title>
            {f.origin} → {f.destination}: {f.events} synthetic events
          </title>
        </path>
      ))}
      {origins.map((n) => (
        <g key={n}>
          <rect
            x="208"
            y={left(n) - 8}
            width="7"
            height="16"
            rx="2"
            fill="#1d5f4e"
          />
          <text x="200" y={left(n) + 4} textAnchor="end">
            {n.replace("Specialist", "Spec.").replace("Coordinator", "Coord.")}
          </text>
        </g>
      ))}
      {destinations.map((n) => (
        <g key={n}>
          <rect
            x="525"
            y={right(n) - 8}
            width="7"
            height="16"
            rx="2"
            fill="#bc704b"
          />
          <text x="541" y={right(n) + 4}>
            {n.replace("Specialist", "Spec.").replace("Coordinator", "Coord.")}
          </text>
        </g>
      ))}
    </svg>
  );
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
    [chart, setChart] = useState("network");
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
  const shown = (result?.flows || []).slice(0, 20),
    metrics = result?.metrics;
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
        <p className="error" role="alert">
          {error}
        </p>
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
                    {result.flows.map((f: any) => (
                      <option
                        key={f.origin + f.destination}
                        value={f.origin + " → " + f.destination}
                      >
                        {f.origin} → {f.destination}
                      </option>
                    ))}
                  </select>
                </label>
                {chart === "network" ? (
                  <NetworkChart
                    flows={shown}
                    occupations={result.occupation_options}
                  />
                ) : chart === "flow" ? (
                  <FlowChart flows={shown} />
                ) : (
                  <div className="table-wrap">
                    <table>
                      <caption>
                        Synthetic transition counts · all filtered flows
                      </caption>
                      <thead>
                        <tr>
                          <th>Origin state</th>
                          <th>Destination state</th>
                          <th>Events</th>
                          <th>Valid pairs</th>
                          <th>Median individual change</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.flows.map((f: any) => (
                          <tr key={f.origin + f.destination}>
                            <td>{f.origin}</td>
                            <td>{f.destination}</td>
                            <td>
                              <span
                                className="heat-cell"
                                style={{
                                  background: `rgba(36,107,89,${0.06 + Math.min(0.5, f.events / 200)})`,
                                }}
                              >
                                {f.events}
                              </span>
                            </td>
                            <td>{f.valid_pairs}</td>
                            <td>
                              {f.comparison_available
                                ? format(f.median_individual_pct_change, 1, "%")
                                : "Suppressed"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
                <p className="caption">
                  Synthetic · top 20 flows in graph views. Width = event count.
                  Green = non-negative median change, terracotta = negative,
                  grey = insufficient pairs. Self-loops are unchanged career
                  states. All counts remain in the matrix.
                </p>
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
                  Stayers replace the transition-type filter and retain the
                  other cohort filters. Comparisons are descriptive; they are
                  not causal estimates.
                </p>
              </article>
              <article className="panel">
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
