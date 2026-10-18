import { useEffect, useMemo, useState } from "react";
import { Download, Network, ArrowRight } from "lucide-react";
import { api, Bootstrap, downloadJSON, format } from "../lib/api";

export default function Constellation({
  bootstrap,
}: {
  bootstrap: Bootstrap | null;
}) {
  const [role, setRole] = useState(""),
    [geography, setGeography] = useState(""),
    [minimum, setMinimum] = useState(5),
    [focus, setFocus] = useState(""),
    [metric, setMetric] = useState("support"),
    [result, setResult] = useState<any>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [pairKey, setPairKey] = useState("");
  useEffect(() => {
    if (!bootstrap) return;
    const c = new AbortController();
    setBusy(true);
    setError("");
    api("constellation", { role, geography, min_pair_count: minimum }, c.signal)
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
  }, [bootstrap, role, geography, minimum]);
  const nodes: any[] = result?.nodes || [],
    pairs: any[] = result?.pairs || [],
    eligible: any[] = result?.eligible_pairs || [];
  const labels = Object.fromEntries(
    nodes.map((n: any) => [n.skill_id, n.skill_name]),
  );
  const universe = useMemo(
    () =>
      [...(bootstrap?.snapshot.market.top_skills || [])].sort(
        (a: any, b: any) => a.skill_id.localeCompare(b.skill_id),
      ),
    [bootstrap],
  );
  const position = (id: string) => {
    const i = universe.findIndex((n: any) => n.skill_id === id),
      theta = (2 * Math.PI * i) / Math.max(universe.length, 1) - Math.PI / 2;
    return [300 + 205 * Math.cos(theta), 225 + 165 * Math.sin(theta)];
  };
  const graphEdges = eligible
    .filter((p: any) => !focus || [p.skill_a, p.skill_b].includes(focus))
    .sort((a: any, b: any) => b[metric] - a[metric])
    .slice(0, 80);
  const connected = new Set(
    graphEdges.flatMap((p: any) => [p.skill_a, p.skill_b]),
  );
  const selected =
    pairs.find((p: any) => p.skill_a + "|" + p.skill_b === pairKey) ||
    pairs.find((p: any) => !focus || [p.skill_a, p.skill_b].includes(focus));
  const supportJobs = selected
    ? (result?.postings || []).filter((job: any) => {
        const ids = new Set(
          (result?.evidence || [])
            .filter((e: any) => e.canonical_url === job.canonical_url)
            .map((e: any) => e.skill_id),
        );
        return ids.has(selected.skill_a) && ids.has(selected.skill_b);
      })
    : [];
  return (
    <section className="tool-page">
      <div className="tool-header">
        <div>
          <p className="eyebrow">01 / SKILL RELATIONSHIPS</p>
          <h1>Skill Constellation</h1>
          <p className="lede">
            Find the combinations behind the keywords. Inspect every connection.
          </p>
        </div>
        <div className="tool-symbol">
          <Network size={38} />
        </div>
      </div>
      <div className="notice">
        Synthetic demonstration: all postings, employers and skill combinations
        in this public sample are fictional. They illustrate the method, not
        Irish market demand.
      </div>
      <div className="filter-bar">
        <label className="field">
          Role sample
          <select
            aria-label="Role sample"
            value={role}
            onChange={(e) => {
              setRole(e.target.value);
              setPairKey("");
            }}
          >
            <option value="">All roles</option>
            {Array.from(
              new Set<string>(
                (bootstrap?.snapshot.postings || []).map(
                  (p: any) => p.role_name,
                ),
              ),
            ).map((r) => (
              <option key={r}>{r}</option>
            ))}
          </select>
        </label>
        <label className="field">
          Geography
          <select
            aria-label="Geography"
            value={geography}
            onChange={(e) => {
              setGeography(e.target.value);
              setPairKey("");
            }}
          >
            <option value="">All locations</option>
            <option>Dublin</option>
            <option>Rest of Ireland</option>
          </select>
        </label>
        <label className="field">
          Minimum pair count
          <input
            type="number"
            min={1}
            max={30}
            value={minimum}
            onChange={(e) =>
              setMinimum(Math.min(30, Math.max(1, Number(e.target.value) || 1)))
            }
          />
        </label>
        <label className="field">
          Focus skill
          <select
            aria-label="Focus skill"
            value={focus}
            onChange={(e) => {
              setFocus(e.target.value);
              setPairKey("");
            }}
          >
            <option value="">All skills</option>
            {nodes.map((n: any) => (
              <option value={n.skill_id} key={n.skill_id}>
                {n.skill_name}
              </option>
            ))}
          </select>
        </label>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {busy && (
        <p role="status" className="muted">
          Recalculating the selected sample…
        </p>
      )}
      {result && (
        <>
          <div className="metrics">
            <div className="metric">
              <span>Unique postings · N</span>
              <strong>{result.sample_size}</strong>
              <small>Including postings without skills</small>
            </div>
            <div className="metric">
              <span>Postings with evidence</span>
              <strong>{result.jobs_with_skills}</strong>
              <small>Unique posting identities</small>
            </div>
            <div className="metric">
              <span>Distinct skills</span>
              <strong>{nodes.length}</strong>
              <small>Controlled taxonomy</small>
            </div>
            <div className="metric">
              <span>Visible connections</span>
              <strong>{graphEdges.length}</strong>
              <small>After sample and pair guards</small>
            </div>
          </div>
          <div className="graph-layout">
            <article className="panel">
              <div className="panel-heading">
                <div>
                  <p className="eyebrow">EXPLORE THE NETWORK</p>
                  <h2>Skills travel together.</h2>
                </div>
                <label className="field compact">
                  Edge order
                  <select
                    aria-label="Edge order"
                    value={metric}
                    onChange={(e) => setMetric(e.target.value)}
                  >
                    <option value="support">Pair support</option>
                    <option value="jaccard">Jaccard similarity</option>
                    <option value="lift">Lift</option>
                  </select>
                </label>
              </div>
              {!result.network_eligible ? (
                <div className="empty-state">
                  <h3>A little more evidence is needed.</h3>
                  <p>
                    The network needs 20 postings. This selection has{" "}
                    {result.sample_size}. Counts remain available, but do not
                    support a connection ranking.
                  </p>
                </div>
              ) : graphEdges.length === 0 ? (
                <div className="empty-state">
                  No connections meet the current pair-count guard. Try another
                  focus or lower the guard for exploratory inspection.
                </div>
              ) : (
                <svg
                  className="constellation-chart"
                  viewBox="0 0 600 450"
                  role="img"
                  aria-label="Skill co-mention network; equivalent metrics are in the table below"
                >
                  <circle
                    cx="300"
                    cy="225"
                    r="170"
                    fill="none"
                    stroke="#d7e0db"
                    strokeDasharray="3 7"
                  />
                  {graphEdges.map((p: any) => {
                    const a = position(p.skill_a),
                      b = position(p.skill_b);
                    return (
                      <line
                        key={p.skill_a + p.skill_b}
                        x1={a[0]}
                        y1={a[1]}
                        x2={b[0]}
                        y2={b[1]}
                        stroke="#80aa9c"
                        strokeOpacity=".45"
                        strokeWidth={1 + 3 * p.support}
                      >
                        <title>
                          {labels[p.skill_a]} + {labels[p.skill_b]}:{" "}
                          {p.pair_count} postings; lift {p.lift.toFixed(2)}
                        </title>
                      </line>
                    );
                  })}
                  {nodes
                    .filter((n: any) => connected.has(n.skill_id))
                    .slice(0, 40)
                    .map((n: any) => {
                      const [x, y] = position(n.skill_id);
                      return (
                        <g
                          key={n.skill_id}
                          role="button"
                          tabIndex={0}
                          aria-label={`Focus ${n.skill_name}`}
                          onClick={() =>
                            setFocus(focus === n.skill_id ? "" : n.skill_id)
                          }
                          onKeyDown={(e) => {
                            if (e.key === "Enter" || e.key === " ") {
                              e.preventDefault();
                              setFocus(focus === n.skill_id ? "" : n.skill_id);
                            }
                          }}
                          className="graph-node"
                        >
                          <circle
                            cx={x}
                            cy={y}
                            r={9 + 16 * Math.sqrt(n.sample_share)}
                            fill={focus === n.skill_id ? "#b85b38" : "#246b59"}
                            stroke="#f8f7f2"
                            strokeWidth="3"
                          />
                          <text x={x} y={y - 32} textAnchor="middle">
                            {n.skill_name}
                          </text>
                          <title>
                            {n.skill_name}: {n.job_count} fictional postings
                          </title>
                        </g>
                      );
                    })}
                </svg>
              )}
              <p className="caption">
                Node size: unique posting count. Fixed positions. Maximum 40
                nodes / 80 edges. Co-mention is association, not causation.
              </p>
            </article>
            <aside className="panel dark-panel">
              <p className="eyebrow">BEHIND THE CONNECTION</p>
              <h2>Evidence, not just an edge.</h2>
              <label className="field">
                Inspect a pair
                <select
                  value={
                    selected ? selected.skill_a + "|" + selected.skill_b : ""
                  }
                  onChange={(e) => setPairKey(e.target.value)}
                >
                  {pairs
                    .filter(
                      (p: any) =>
                        !focus || [p.skill_a, p.skill_b].includes(focus),
                    )
                    .map((p: any) => (
                      <option
                        key={p.skill_a + p.skill_b}
                        value={p.skill_a + "|" + p.skill_b}
                      >
                        {labels[p.skill_a]} + {labels[p.skill_b]}
                      </option>
                    ))}
                </select>
              </label>
              {selected ? (
                <>
                  <div className="pair-stat">
                    <strong>{selected.pair_count}</strong>
                    <span>
                      of {result.sample_size} fictional postings
                      <br />
                      mention both skills
                    </span>
                  </div>
                  <dl className="definition-list">
                    <div>
                      <dt>Support</dt>
                      <dd>{format(selected.support * 100, 1, "%")}</dd>
                    </div>
                    <div>
                      <dt>Jaccard</dt>
                      <dd>{format(selected.jaccard, 3)}</dd>
                    </div>
                    <div>
                      <dt>Lift</dt>
                      <dd>{format(selected.lift, 2)}×</dd>
                    </div>
                  </dl>
                  <p className="caption">
                    Display guards are product heuristics, not significance
                    tests. High lift from a small count needs caution.
                  </p>
                </>
              ) : (
                <p>No pair evidence in this selection.</p>
              )}
            </aside>
          </div>
          <details className="panel">
            <summary>Calculation definitions and complete pair table</summary>
            <p>
              N includes every selected unique posting. Mentions are counted
              once per skill per posting.
            </p>
            <code>
              Support = n(A,B)/N · Jaccard = n(A,B)/(n(A)+n(B)−n(A,B)) · Lift =
              n(A,B)×N/(n(A)×n(B))
            </code>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Skill A</th>
                    <th>Skill B</th>
                    <th>Co-mentions</th>
                    <th>Support</th>
                    <th>Jaccard</th>
                    <th>Lift</th>
                  </tr>
                </thead>
                <tbody>
                  {pairs.map((p: any) => (
                    <tr key={p.skill_a + p.skill_b}>
                      <td>{labels[p.skill_a]}</td>
                      <td>{labels[p.skill_b]}</td>
                      <td>{p.pair_count}</td>
                      <td>{format(p.support * 100, 1, "%")}</td>
                      <td>{format(p.jaccard, 3)}</td>
                      <td>{format(p.lift, 2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <button
              className="button-secondary"
              onClick={() =>
                downloadJSON("synthetic-skill-pairs.json", {
                  data_label: "Synthetic demonstration",
                  sample_size: result.sample_size,
                  filters: { role, geography },
                  pairs,
                })
              }
            >
              <Download size={16} />
              Download pair metrics
            </button>
          </details>
          <article className="panel">
            <p className="eyebrow">SOURCE DRILL-DOWN</p>
            <h2>
              Inspect the supporting examples <ArrowRight size={20} />
            </h2>
            <p>
              {supportJobs.length} fictional postings support the selected pair.
              These examples have no external job URLs.
            </p>
            {supportJobs.slice(0, 8).map((job: any) => (
              <details key={job.canonical_url} className="source-row">
                <summary>
                  {job.title} · {job.employer_name} · {job.location_text}
                </summary>
                <p>{job.description_text}</p>
                <p className="caption">
                  Generated example · {job.source_job_id} · not a real vacancy
                </p>
              </details>
            ))}
          </article>
        </>
      )}
    </section>
  );
}
