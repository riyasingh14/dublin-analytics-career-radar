import { useRef, useState } from "react";
import { Compass, Download, ArrowRight, RotateCcw } from "lucide-react";
import { api, Bootstrap, DEMO_TEXT, downloadJSON, format } from "../lib/api";
import EvidencePlanner, { ActionPlan, EvidenceAction, EvidenceBreakdown } from "../components/EvidencePlanner";
type Entry = { status: string; note: string };
function Summary({ result }: { result: any }) {
  return (
    <>
      <div className="metrics three">
        <div className="metric">
          <span>Assessed-weight coverage</span>
          <strong>{format(result.coverage_pct, 1, "%")}</strong>
          <small>Unknowns excluded and reported</small>
        </div>
        <div className="metric">
          <span>Evidence alignment index</span>
          <strong>
            {result.alignment_pct == null
              ? "Suppressed"
              : format(result.alignment_pct, 1) + " / 100"}
          </strong>
          <small>Not a hiring prediction</small>
        </div>
        <div className="metric">
          <span>Unassessed requirement weight</span>
          <strong>
            {result.unassessed_weight} / {result.total_weight}
          </strong>
          <small>Required = 3 · preferred = 1</small>
        </div>
      </div>
      {result.alignment_pct == null && (
        <p className="notice">
          The index needs confirmed requirements and at least 80%
          assessed-weight coverage. Unknown is not failure.
        </p>
      )}
    </>
  );
}
export default function Readiness({
  bootstrap,
}: {
  bootstrap: Bootstrap | null;
}) {
  const [text, setText] = useState(""),
    [requirements, setRequirements] = useState<any[]>([]),
    [entries, setEntries] = useState<Record<string, Entry>>({}),
    [kinds, setKinds] = useState<Record<string, string>>({}),
    [result, setResult] = useState<any>(null),
    [scenario, setScenario] = useState<any>(null),
    [report, setReport] = useState<any>(null),
    [actionPlan, setActionPlan] = useState<ActionPlan | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [gap, setGap] = useState(""),
    [plan, setPlan] = useState(""),
    [example, setExample] = useState(false);
  const request = useRef<AbortController | null>(null);
  const invalidate = () => {
    setRequirements([]);
    setEntries({});
    setKinds({});
    setResult(null);
    setReport(null);
    setActionPlan(null);
    setScenario(null);
    setGap("");
    setPlan("");
  };
  const clear = () => {
    request.current?.abort();
    setBusy(false);
    setError("");
    setText("");
    setExample(false);
    invalidate();
  };
  async function send(mode: "extract" | "assess" | "scenario") {
    request.current?.abort();
    const c = new AbortController();
    request.current = c;
    setBusy(true);
    setError("");
    try {
      const data = await api(
        "readiness",
        {
          text,
          ...(mode !== "extract"
            ? { evidence: entries, classifications: kinds }
            : {}),
          ...(mode === "scenario"
            ? { hypothetical: { requirement_id: gap, note: plan } }
            : {}),
        },
        c.signal,
      );
      if (mode === "extract") {
        setRequirements(data.requirements);
        setKinds(
          Object.fromEntries(
            data.requirements.map((r: any) => [
              r.requirement_id,
              r.requirement_type,
            ]),
          ),
        );
        setEntries({});
        setResult(null);
        setScenario(null);
        setReport(null);
        setActionPlan(null);
      } else if (mode === "assess") {
        setResult(data.assessment);
        setReport(data.report);
        setActionPlan(data.action_plan);
        setScenario(null);
        setGap("");
        setPlan("");
      } else {
        setScenario(data.scenario);
      }
    } catch (e: any) {
      if (e.name !== "AbortError") setError(e.message);
    } finally {
      if (!c.signal.aborted) setBusy(false);
    }
  }
  const update = (id: string, key: keyof Entry, value: string) => {
    setEntries({
      ...entries,
      [id]: {
        ...(entries[id] || { status: "unknown", note: "" }),
        [key]: value,
      },
    });
    setResult(null);
    setScenario(null);
    setReport(null);
    setActionPlan(null);
  };
  const reviewAction = (action: EvidenceAction) => {
    const row = result.rows.find((r: any) => action.requirement_ids.includes(r.requirement_id) && r.status === "unknown");
    document.getElementById("evidence-status-" + (row?.requirement_id || action.requirement_ids[0]))?.focus();
  };
  const exploreAction = (action: EvidenceAction) => {
    const row = result.rows.find((r: any) => action.requirement_ids.includes(r.requirement_id) && r.status !== "supported");
    setGap(row?.requirement_id || "");
    setPlan(action.project_brief || "");
    setScenario(null);
    requestAnimationFrame(() => document.getElementById("planned-evidence")?.focus());
  };
  const gaps = (result?.rows || []).filter(
    (r: any) => r.weight && r.status !== "supported" &&
      result.skill_summary.some((s: any) => s.requirement_ids.includes(r.requirement_id)),
  );
  return (
    <section className="tool-page">
      <div className="tool-header">
        <div>
          <p className="eyebrow">02 / SELF-REPORTED EVIDENCE</p>
          <h1>Opportunity Readiness Studio</h1>
          <p className="lede">
            Make your evidence visible. Keep the unknowns visible, too.
          </p>
        </div>
        <div className="tool-symbol">
          <Compass size={38} />
        </div>
      </div>
      <div className="notice">
        Evidence alignment is not a callback probability. Grades, degree,
        location and work eligibility are outside this skill index. Check
        explicit conditions in the original listing.
      </div>
      <article className="panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">STEP 01</p>
            <h2>Understand the requirements.</h2>
          </div>
          <button className="button-small" onClick={clear}>
            <RotateCcw size={14} />
            Clear all
          </button>
        </div>
        <label className="field">
          Job description
          <textarea
            rows={7}
            value={text}
            maxLength={30000}
            disabled={busy}
            onChange={(e) => {
              setText(e.target.value);
              invalidate();
            }}
            placeholder="Paste the description you want to compare. Leave out names and contact details."
          />
        </label>
        {example && (
          <p className="caption">
            Started from a synthetic example; edits are your own. No real
            vacancy is implied.
          </p>
        )}
        <div className="action-row">
          <button
            className="button"
            disabled={busy || !text.trim()}
            onClick={() => send("extract")}
          >
            {busy ? "Working…" : "Extract requirements"}
            <ArrowRight size={16} />
          </button>
          <button
            className="button-secondary"
            disabled={busy}
            onClick={() => {
              setText(bootstrap?.example_description || DEMO_TEXT);
              setExample(true);
              invalidate();
            }}
          >
            Try a synthetic example
          </button>
        </div>
      </article>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {requirements.length > 0 && (
        <article className="panel">
          <p className="eyebrow">STEP 02</p>
          <h2>Review the requirement. Add your evidence.</h2>
          <p>
            Correct the rule’s classification where necessary. Supported or
            partial claims need a concrete coursework, project or experience
            note. These are self-reported, not independently verified.
          </p>
          <div className="requirement-list">
            {requirements.map((r: any) => (
              <div className="requirement-card" key={r.requirement_id}>
                <div className="requirement-head">
                  <h3>{r.skill_name}</h3>
                  <span className="badge">RULE: {r.requirement_type}</span>
                </div>
                <blockquote>{r.source_text}</blockquote>
                <div className="grid-two">
                  <label className="field">
                    Confirm classification for {r.skill_name}
                    <select
                      aria-label={"Confirm classification for " + r.skill_name}
                      value={kinds[r.requirement_id]}
                      disabled={busy}
                      onChange={(e) => {
                        setKinds({
                          ...kinds,
                          [r.requirement_id]: e.target.value,
                        });
                        setResult(null);
                        setScenario(null);
                        setReport(null);
                        setActionPlan(null);
                      }}
                    >
                      {["required", "preferred", "uncertain", "negated"].map(
                        (k) => (
                          <option key={k}>{k}</option>
                        ),
                      )}
                    </select>
                  </label>
                  <label className="field">
                    Evidence status for {r.skill_name}
                    <select
                      id={"evidence-status-" + r.requirement_id}
                      aria-label={"Evidence status for " + r.skill_name}
                      value={entries[r.requirement_id]?.status || "unknown"}
                      disabled={busy}
                      onChange={(e) =>
                        update(r.requirement_id, "status", e.target.value)
                      }
                    >
                      {["unknown", "supported", "partial", "missing"].map(
                        (k) => (
                          <option key={k}>{k}</option>
                        ),
                      )}
                    </select>
                  </label>
                </div>
                <label className="field">
                  Evidence note for {r.skill_name}
                  <input
                    maxLength={500}
                    value={entries[r.requirement_id]?.note || ""}
                    disabled={busy}
                    onChange={(e) =>
                      update(r.requirement_id, "note", e.target.value)
                    }
                    placeholder="A specific project, assessed activity or experience — no personal identifiers."
                  />
                </label>
              </div>
            ))}
          </div>
          <p className="caption">
            Uncertain and negated mentions are excluded. Repeated skills count
            once at the strongest requirement level. Submitting confirms your
            reviewed classifications.
          </p>
          <button
            className="button"
            disabled={busy}
            onClick={() => send("assess")}
          >
            Assess my evidence <ArrowRight size={16} />
          </button>
        </article>
      )}
      {requirements.length === 0 && result === null && text && (
        <p className="caption">
          Extract requirements first. A description with no recognised skills
          cannot support an alignment index.
        </p>
      )}
      {result && (
        <>
          <article className="panel">
            <p className="eyebrow">YOUR SUBMITTED BASELINE</p>
            <h2>Evidence you can explain.</h2>
            <Summary result={result} />
            <EvidenceBreakdown breakdown={result.evidence_breakdown} totalWeight={result.total_weight} />
            <p className="caption">{result.formula}</p>
            {result.rows
              .filter((r: any) => r.issue)
              .map((r: any) => (
                <p className="notice" key={r.requirement_id}>
                  {r.skill_name}: {r.issue}
                </p>
              ))}
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Skill</th>
                    <th>Reviewed requirement</th>
                    <th>Status</th>
                    <th>Your evidence</th>
                  </tr>
                </thead>
                <tbody>
                  {result.rows.map((r: any) => (
                    <tr key={r.requirement_id}>
                      <td>{r.skill_name}</td>
                      <td>{r.requirement_type}</td>
                      <td>{r.status}</td>
                      <td>{r.evidence_note || "Not supplied"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="caption">
              {result.limitation} {result.eligibility_status}
            </p>
          </article>
          {actionPlan && <EvidencePlanner plan={actionPlan} rows={result.rows} busy={busy}
            onExplore={exploreAction} onReview={reviewAction} />}
          {gaps.length > 0 && (
            <article className="panel">
              <p className="eyebrow">WHAT IF?</p>
              <h2>Explore one next step.</h2>
              <p>
                Compare hypothetical completed evidence without changing your
                submitted baseline. This changes one source requirement only;
                repeated contexts may still limit the skill's assessed evidence.
              </p>
              <div className="grid-two">
                <label className="field">
                  Requirement to explore
                  <select
                    aria-label="Requirement to explore"
                    value={gap}
                    onChange={(e) => {
                      setGap(e.target.value);
                      setScenario(null);
                    }}
                  >
                    <option value="">Choose a gap</option>
                    {gaps.map((r: any) => (
                      <option value={r.requirement_id} key={r.requirement_id}>
                        {r.skill_name} · {r.requirement_type}
                        {(result.rows.filter((row: any) => row.skill_id === r.skill_id).length > 1)
                          ? ` · mention ${result.rows.filter((row: any) => row.skill_id === r.skill_id).findIndex((row: any) => row.requirement_id === r.requirement_id) + 1}` : ""}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="field">
                  Planned evidence
                  <input
                    id="planned-evidence"
                    maxLength={500}
                    value={plan}
                    onChange={(e) => {
                      setPlan(e.target.value);
                      setScenario(null);
                    }}
                    placeholder="What would you build or demonstrate?"
                  />
                </label>
              </div>
              <button
                className="button-secondary"
                disabled={!gap || !plan.trim() || busy}
                onClick={() => send("scenario")}
              >
                Compare hypothetical evidence
              </button>
              {scenario && (
                <>
                  <h3>Hypothetical — not completed or verified</h3>
                  <Summary result={scenario} />
                  <p className="caption">
                    Baseline index: {format(result.alignment_pct, 1)}. Your
                    submitted evidence is unchanged. This does not establish a
                    hiring outcome.
                  </p>
                </>
              )}
            </article>
          )}
          <div className="export-panel">
            <div>
              <h3>A report without personal notes.</h3>
              <p>
                The download excludes your evidence notes and original job text.
                Clear all removes browser inputs and results.
              </p>
            </div>
            <button
              className="button-secondary"
              onClick={() =>
                downloadJSON("readiness-evidence-report.json", report)
              }
            >
              <Download size={16} />
              Download analysis
            </button>
          </div>
        </>
      )}
    </section>
  );
}
