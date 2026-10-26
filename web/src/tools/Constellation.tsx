import ToolStatus from "../components/ToolStatus";
import { useEffect, useMemo, useState } from "react";
import { Download, Network, ArrowRight } from "lucide-react";
import { api, Bootstrap, downloadJSON, format } from "../lib/api";
import ConstellationComparison from "./ConstellationComparison";
import { boundedGraph, categoryColour } from "./constellationModel";
import "./constellation.css";

export default function Constellation({
  bootstrap,
}: {
  bootstrap: Bootstrap | null;
}) {
  const reviewed = bootstrap?.data_mode === "reviewed-sample";
  const release = bootstrap?.release;
  const postingLabel = reviewed ? "reviewed postings" : "fictional postings";
  const geographies = reviewed ? Array.from(new Set<string>((bootstrap?.snapshot.postings || []).map((posting: any) => posting.geography))).sort() : ["Dublin", "Rest of Ireland"];
  const [attempt, setAttempt] = useState(0);
  const [role, setRole] = useState(""),
    [geography, setGeography] = useState(""),
    [minimum, setMinimum] = useState(5),
    [focus, setFocus] = useState(""),
    [metric, setMetric] = useState("support"),
    [result, setResult] = useState<any>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [pairKey, setPairKey] = useState(""),
    [skillSearch, setSkillSearch] = useState("");
  useEffect(() => {
    if (!bootstrap) return;
    const c = new AbortController();
    setBusy(true);
    setError("");
    setResult(null);
    api("constellation", { role, geography, min_pair_count: minimum }, c.signal)
      .then((data) => {
        if ((data.data_mode || "synthetic-demo") !== bootstrap.data_mode || data.release?.release_id !== bootstrap.release?.release_id) {
          throw new Error("The dataset changed. Reload this page to use the current release.");
        }
        setResult(data);
      })
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
  }, [bootstrap, role, geography, minimum, attempt]);
  const nodes: any[] = result?.nodes || [],
    pairs: any[] = result?.pairs || [],
    eligible: any[] = result?.eligible_pairs || [];
  const labels = Object.fromEntries(
    nodes.map((n: any) => [n.skill_id, n.skill_name]),
  );
  const universe = useMemo(
    () =>
      [...new Map<string, any>((bootstrap?.snapshot.evidence || []).map((row: any) => [row.skill_id, row])).values()].sort(
        (a: any, b: any) => a.skill_id.localeCompare(b.skill_id),
      ),
    [bootstrap],
  );
  const position = (id: string) => {
    const i = universe.findIndex((n: any) => n.skill_id === id),
      theta = (2 * Math.PI * i) / Math.max(universe.length, 1) - Math.PI / 2;
    return [300 + 205 * Math.cos(theta), 225 + 165 * Math.sin(theta)];
  };
  const graph = boundedGraph(nodes, eligible, metric, focus);
  const graphEdges = graph.edges;
  const categoryById = Object.fromEntries((bootstrap?.taxonomy || []).map((skill: any) => [skill.skill_id, skill.category]));
  const categories = [...new Set<string>(graph.nodes.map((node: any) => categoryById[node.skill_id] || "Uncategorised"))].sort();
  const searchableNodes = nodes.filter((node: any) => `${node.skill_name} ${categoryById[node.skill_id] || ""}`.toLowerCase().includes(skillSearch.toLowerCase()));
  useEffect(() => {
    if (result && focus && !result.nodes.some((node: any) => node.skill_id === focus)) {
      setFocus("");
      setPairKey("");
    }
  }, [result, focus]);
  const inspectionPairs = pairs.filter(
    (p: any) => !focus || [p.skill_a, p.skill_b].includes(focus),
  );
  const selected =
    inspectionPairs.find((p: any) => p.skill_a + "|" + p.skill_b === pairKey) ||
    inspectionPairs[0];
  const selectedKey = selected ? selected.skill_a + "|" + selected.skill_b : "";
  const [showAllEvidence, setShowAllEvidence] = useState(false);
  useEffect(() => setShowAllEvidence(false), [selectedKey, role, geography]);
  const focusSkill = (id: string) => {
    setFocus(focus === id ? "" : id);
    setPairKey("");
  };
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
        {reviewed ? `Reviewed posting sample: ${release?.dataset_label}. This is limited to its documented sources and collection window; it is not complete Irish-market coverage.` : "Synthetic demonstration: all postings, employers and skill combinations in this public sample are fictional. They illustrate the method, not Irish market demand."}
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
            {geographies.map(value => <option key={value}>{value}</option>)}
          </select>
        </label>
        <label className="field">
          Minimum pair count
          <input
            type="number"
            min={1}
            max={reviewed ? 100 : 30}
            value={minimum}
            onChange={(e) =>
              setMinimum(Math.min(reviewed ? 100 : 30, Math.max(1, Number(e.target.value) || 1)))
            }
          />
        </label>
        <label className="field">
          Search skills
          <input type="search" aria-label="Search skills" value={skillSearch} onChange={(e) => setSkillSearch(e.target.value)} placeholder="Skill or category" />
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
            {focus && !searchableNodes.some((node: any) => node.skill_id === focus) && <option value={focus}>{labels[focus]}</option>}
            {searchableNodes.map((n: any) => (
              <option value={n.skill_id} key={n.skill_id}>
                {n.skill_name}
              </option>
            ))}
          </select>
        </label>
      </div>
      {error && (
        <div className="error" role="alert">
          <p>{error}</p>
          <button className="button-secondary" disabled={busy} onClick={() => error.startsWith("The dataset changed.") ? location.reload() : setAttempt(value => value + 1)}>{error.startsWith("The dataset changed.") ? "Reload current dataset" : "Retry sample"}</button>
        </div>
      )}
      <ToolStatus busy={busy}>Recalculating the selected sample…</ToolStatus>
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
          <article className="panel constellation-coverage">
            <p className="eyebrow">SAMPLE COVERAGE & LIMITS</p><h2>Know what this view can support.</h2>
            <dl>
              <div><dt>Data source</dt><dd>{reviewed ? release?.sources.map(source => source.source_name).join(", ") : "Generated fictional fixture; no live feed"}</dd></div>
              <div><dt>Evidence coverage</dt><dd>{result.jobs_with_skills} / {result.sample_size} selected postings{result.sample_size ? ` · ${format(100 * result.jobs_with_skills / result.sample_size, 1, "%")}` : " · unavailable"}</dd></div>
              <div><dt>Collection date</dt><dd>{reviewed ? `${release?.collected_from} to ${release?.collected_through}` : "Not applicable: no vacancies collected"}</dd></div>
              <div><dt>Extraction method</dt><dd>Controlled phrase rules · {[...new Set<string>((result.evidence || []).map((row: any) => row.extraction_version))].join(", ") || "No extracted evidence"}</dd></div>
              <div><dt>Observation window</dt><dd>{reviewed ? `Release ${release?.release_id} · valid until ${release?.expires_at}` : "Single fictional fixture; no historical trend available"}</dd></div>
              <div><dt>Unprovided filters</dt><dd>Industry and seniority are unavailable in this sample</dd></div>
            </dl>
            <p className="caption">{reviewed ? "This release passed the configured extraction review and source-display checks. That does not establish market representativeness. Postings without a skill match still count in N; counts describe this sample and not all Irish vacancies." : "No observed market coverage or extraction precision is claimed. A fixture is not a human-reviewed live dataset. Postings without an extracted match still count in N. Source mix, collection bias and human validation must be assessed before real-data publication."}</p>
          </article>
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
                  role="group"
                  aria-label="Interactive skill co-mention network; select a connection to inspect its evidence"
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
                    const a = position(p.skill_a), b = position(p.skill_b);
                    const key = p.skill_a + "|" + p.skill_b;
                    return (
                      <g key={key} className="graph-line" aria-hidden="true"
                        onClick={() => setPairKey(key)}>
                        <line x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]}
                          stroke="transparent" strokeWidth="12" />
                        <line className="edge-mark" x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]}
                          stroke={key === selectedKey ? "#b85b38" : "#80aa9c"}
                          strokeOpacity={key === selectedKey ? 1 : .45}
                          strokeWidth={key === selectedKey ? 4 : 1 + 3 * p.support}
                          pointerEvents="none" />
                      </g>
                    );
                  })}
                  {graphEdges.map((p: any) => {
                    const a = position(p.skill_a),
                      b = position(p.skill_b);
                    const key = p.skill_a + "|" + p.skill_b;
                    return (
                      <g
                        key={p.skill_a + p.skill_b}
                        className="graph-edge"
                        role="button"
                        tabIndex={0}
                        aria-label={`Inspect ${labels[p.skill_a]} and ${labels[p.skill_b]}: ${p.pair_count} ${postingLabel}`}
                        aria-pressed={key === selectedKey}
                        onClick={() => setPairKey(key)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" || e.key === " ") {
                            e.preventDefault();
                            setPairKey(key);
                          }
                        }}
                      >
                        <circle cx={(a[0] + b[0]) / 2} cy={(a[1] + b[1]) / 2}
                          r={key === selectedKey ? 6 : 4}
                          stroke="#f8f7f2" strokeWidth="1.5"
                          fill={key === selectedKey ? "#b85b38" : "#80aa9c"} />
                        <title>
                          {labels[p.skill_a]} + {labels[p.skill_b]}:{" "}
                          {p.pair_count} postings; lift {p.lift.toFixed(2)}
                        </title>
                      </g>
                    );
                  })}
                  {graph.nodes
                    .map((n: any) => {
                      const [x, y] = position(n.skill_id);
                      return (
                        <g
                          key={n.skill_id}
                          role="button"
                          tabIndex={0}
                          aria-label={`Focus ${n.skill_name}`}
                          aria-pressed={focus === n.skill_id}
                          onClick={() => focusSkill(n.skill_id)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" || e.key === " ") {
                              e.preventDefault();
                              focusSkill(n.skill_id);
                            }
                          }}
                          className="graph-node"
                        >
                          <circle
                            cx={x}
                            cy={y}
                            r={9 + 16 * Math.sqrt(n.sample_share)}
                            fill={categoryColour(categoryById[n.skill_id] || "Uncategorised")}
                            stroke={focus === n.skill_id ? "#151f1b" : "#f8f7f2"}
                            strokeWidth={focus === n.skill_id ? 5 : 3}
                          />
                          <text x={x} y={y - 32} textAnchor="middle">
                            {n.skill_name}
                          </text>
                          <title>
                            {n.skill_name} · {categoryById[n.skill_id] || "Uncategorised"}: {n.job_count} {postingLabel}
                          </title>
                        </g>
                      );
                    })}
                </svg>
              )}
              <div className="constellation-legend" aria-label="Taxonomy category legend">{categories.map((category) => <span key={category}><i aria-hidden="true" style={{background: categoryColour(category)}} />{category}</span>)}</div>
              <p className="caption">
                Node size: unique posting count. Fixed positions. Maximum 40
                nodes / 80 edges. Select a line to inspect its source phrases;
                select a node to focus. Keyboard: Tab, then Enter or Space.
                Co-mention is association, not causation.
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
                  <p role="status" className="selected-pair">
                    Selected: {labels[selected.skill_a]} + {labels[selected.skill_b]}
                  </p>
                  <div className="pair-stat">
                    <strong>{selected.pair_count}</strong>
                    <span>
                      of {result.sample_size} {postingLabel}
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
          <ConstellationComparison comparison={result.role_comparison} reviewed={reviewed} />
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
                downloadJSON(reviewed ? "reviewed-skill-pairs.json" : "synthetic-skill-pairs.json", {
                  data_label: reviewed ? release?.dataset_label : "Synthetic demonstration",
                  release: release || null,
                  sample_size: result.sample_size,
                  filters: { role, geography },
                  definitions: { support: "n(A,B)/N", jaccard: "n(A,B)/(n(A)+n(B)-n(A,B))", lift: "n(A,B)*N/(n(A)*n(B))" },
                  interpretation: `${reviewed ? "Reviewed source sample" : "Fictional sample"}; co-mention is association, not causation; display guards are heuristics.`,
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
              {supportJobs.length} {postingLabel} support the selected pair.
              {reviewed ? "Open a record for its source text and original URL." : "These examples have no external job URLs."}
            </p>
            {supportJobs.slice(0, showAllEvidence ? supportJobs.length : 8).map((job: any) => (
              <details key={job.canonical_url} className="source-row">
                <summary>
                  {job.title} · {job.employer_name} · {job.location_text}
                </summary>
                <dl className="phrase-evidence">
                  {(result.evidence || [])
                    .filter((e: any) => e.canonical_url === job.canonical_url &&
                      [selected?.skill_a, selected?.skill_b].includes(e.skill_id))
                    .map((e: any) => (
                      <div key={e.skill_id}>
                        <dt>{e.skill_name} · exact matched phrase</dt>
                        <dd><q>{e.source_phrase}</q></dd>
                        <dd className="caption">Method: {e.extraction_method} · Version: {e.extraction_version}</dd>
                      </div>
                    ))}
                </dl>
                <p className="eyebrow">{reviewed ? "RELEASED SOURCE DESCRIPTION" : "COMPLETE SYNTHETIC DESCRIPTION"}</p>
                <p>{job.description_text}</p>
                {reviewed && /^https:\/\//.test(job.canonical_url) && <a className="text-link" href={job.canonical_url} target="_blank" rel="noreferrer">Open original posting</a>}
                <p className="caption">
                  {reviewed ? `Released record · ${job.source_job_id} · availability may have changed since collection` : `Generated example · ${job.source_job_id} · not a real vacancy`}
                </p>
              </details>
            ))}
            {supportJobs.length > 8 && (
              <button className="button-secondary" onClick={() => setShowAllEvidence(!showAllEvidence)}>
                {showAllEvidence ? "Show first 8 examples" : `Show all ${supportJobs.length} supporting examples`}
              </button>
            )}
          </article>
        </>
      )}
    </section>
  );
}
