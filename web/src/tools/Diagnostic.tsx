import { useRef, useState } from "react";
import { Download, ScanText, ArrowRight, RotateCcw } from "lucide-react";
import { api, Bootstrap, DEMO_TEXT, downloadJSON } from "../lib/api";
export default function Diagnostic({
  bootstrap,
}: {
  bootstrap: Bootstrap | null;
}) {
  const [text, setText] = useState(""),
    [result, setResult] = useState<any>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [example, setExample] = useState(false),
    [reviews, setReviews] = useState<Record<string, string>>({}),
    [edits, setEdits] = useState<Record<string, string>>({}),
    [selected, setSelected] = useState<string | null>(null),
    [category, setCategory] = useState("All categories");
  const request = useRef<AbortController | null>(null);
  const clear = () => {
    request.current?.abort();
    setText("");
    setResult(null);
    setBusy(false);
    setError("");
    setExample(false);
    setReviews({});
    setEdits({});
    setSelected(null);
    setCategory("All categories");
  };
  async function analyze() {
    request.current?.abort();
    const c = new AbortController();
    request.current = c;
    setBusy(true);
    setError("");
    try {
      const data = await api("diagnostic", { text }, c.signal);
      setResult(data);
      setReviews({});
      setEdits({});
      setSelected(null);
      setCategory("All categories");
    } catch (e: any) {
      if (e.name !== "AbortError") setError(e.message);
    } finally {
      if (!c.signal.aborted) setBusy(false);
    }
  }
  function report() {
    return {
      rule_version: result.rule_version,
      scope: example
        ? "User-editable synthetic example"
        : "User-supplied description; source unverified",
      limitations: result.limitations,
      benchmark_status: result.benchmark_status,
      review_summary: { accepted: result.findings.filter((f: any) => reviews[f.finding_id] === "Accepted for clarification").length, dismissed: result.findings.filter((f: any) => reviews[f.finding_id] === "Dismissed").length, uncertain: result.findings.filter((f: any) => reviews[f.finding_id] === "Uncertain").length },
      completeness: Object.fromEntries(
        Object.entries(result.completeness).map(([key, v]: [string, any]) => [
          key,
          { status: v.status },
        ]),
      ),
      requirements: result.requirements.map((r: any) => ({
        skill_id: r.skill_id,
        skill_name: r.skill_name,
        requirement_type: r.requirement_type,
        extraction_version: r.extraction_version,
      })),
      findings: result.findings.map((f: any) => ({
        finding_id: f.finding_id,
        rule: f.rule,
        absent_field: f.absent_field,
        start: f.start,
        end: f.end,
        category: f.category,
        severity: f.severity,
        rationale: f.rationale,
        review_status: reviews[f.finding_id] || "Unreviewed",
        edited_suggestion: edits[f.finding_id] ?? f.suggestion,
      })),
      privacy:
        "Original description and source phrases omitted. Review edited suggestions before sharing.",
    };
  }
  const selectedFinding = result?.findings.find((f: any) => f.finding_id === selected);
  // Python spans count Unicode code points, while JavaScript string offsets count UTF-16.
  // Slice code points so an emoji before a finding cannot move its evidence highlight.
  const sourcePoints = Array.from(text);
  const accepted = result?.findings.filter((f: any) => reviews[f.finding_id] === "Accepted for clarification") || [];
  const visibleFindings = result?.findings.filter((f: any) => category === "All categories" || f.category === category) || [];
  return (
    <section className="tool-page">
      <div className="tool-header">
        <div>
          <p className="eyebrow">04 / DESCRIPTION ANALYSIS</p>
          <h1>Job Description Diagnostic</h1>
          <p className="lede">
            What is clear? What is missing? What needs a better question?
          </p>
        </div>
        <div className="tool-symbol">
          <ScanText size={38} />
        </div>
      </div>
      <div className="notice">
        Rule-based document analysis, not an employer rating or legal
        assessment. Your text is processed transiently; no external language
        model is used.
      </div>
      <article className="panel">
        <div className="panel-heading">
          <h2>Start with the description.</h2>
          <button className="button-small" onClick={clear}>
            <RotateCcw size={14} />
            Clear all
          </button>
        </div>
        {bootstrap?.snapshot?.postings?.length > 0 && <label className="field">Or select a fictional source posting
          <select disabled={busy} value="" onChange={e => {
            const posting = bootstrap?.snapshot?.postings?.find((p: any) => p.source_job_id === e.target.value);
            if (!posting) return;
            setText(`${posting.title}\n${posting.location_text}\n${posting.description_text}`);
            setExample(true); setResult(null); setError(""); setReviews({}); setEdits({}); setSelected(null);
          }}><option value="">Choose a synthetic example…</option>{bootstrap?.snapshot?.postings?.map((p: any) => <option key={p.source_job_id} value={p.source_job_id}>{p.source_job_id} · {p.title} · {p.location_text}</option>)}</select>
        </label>}
        <label className="field">
          Job description
          <textarea
            aria-label="Job description"
            rows={9}
            maxLength={30000}
            value={text}
            disabled={busy}
            onChange={(e) => {
              setText(e.target.value);
              setResult(null);
              setReviews({});
              setEdits({});
            }}
            placeholder="Paste a job description, without personal identifiers or confidential information."
          />
        </label>
        {example && (
          <p className="caption">
            Loaded from a synthetic example. Any edits are your own; no real
            vacancy is implied.
          </p>
        )}
        <div className="action-row">
          <button
            className="button"
            disabled={busy || !text.trim()}
            onClick={analyze}
          >
            {busy ? "Analysing…" : "Analyse description"}
            <ArrowRight size={16} />
          </button>
          <button
            className="button-secondary"
            disabled={busy}
            onClick={() => {
              setText(bootstrap?.example_description || DEMO_TEXT);
              setExample(true);
              setResult(null);
              setError("");
            }}
          >
            Try a synthetic example
          </button>
          <span className="caption">
            {text.length.toLocaleString()} / 30,000 characters
          </span>
        </div>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
      </article>
      {result && (
        <>
          <div className="section-heading compact-heading">
            <div>
              <p className="eyebrow">THE DOCUMENT, EXAMINED</p>
              <h2>Clarity starts with specifics.</h2>
            </div>
            <span className="badge">
              {result.rule_version} · HUMAN REVIEW NEEDED
            </span>
          </div>
          <div className="metrics">
            {Object.entries(result.completeness).map(
              ([field, value]: [string, any]) => (
                <div className="metric checklist-metric" key={field}>
                  <span>{field.replaceAll("_", " ")}</span>
                  <strong className={`status-${value.status}`}>
                    {value.status === "present"
                      ? "Stated"
                      : value.status === "missing"
                        ? "Not stated"
                        : "Unclear"}
                  </strong>
                  <small>
                    {value.source_phrase || "No explicit disclosure found"}
                  </small>
                </div>
              ),
            )}
          </div>
          <p className="caption">
            A matching phrase does not validate its accuracy. Missing
            information is not proof that an employer lacks a policy or benefit.
          </p>
          <article className="panel">
            <div className="panel-heading">
              <div><p className="eyebrow">EXACT SOURCE, KEPT INTACT</p><h2>Document and findings.</h2></div>
              <button className="button-small" disabled={!selected} onClick={() => setSelected(null)}>Clear highlight</button>
            </div>
            <p className="caption">Select a finding below to highlight its exact phrase. “Not stated” identifies absent information; “review” asks for interpretation. Neither is an employer rating.</p>
            <div className="grid-two">
              <div>
                <h3>Original description</h3>
                <div className="notice" data-testid="diagnostic-source" style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere", maxHeight: "32rem", overflow: "auto", display: "block" }}>
                  {selectedFinding?.start != null ? <>{sourcePoints.slice(0, selectedFinding.start).join("")}<mark data-testid="diagnostic-highlight">{sourcePoints.slice(selectedFinding.start, selectedFinding.end).join("")}</mark>{sourcePoints.slice(selectedFinding.end).join("")}</> : text}
                </div>
              </div>
              <div aria-live="polite">
                <h3>Selected evidence</h3>
                {selectedFinding ? <>
                  <p><strong>{selectedFinding.category}</strong> · {selectedFinding.severity}</p>
                  <p>{selectedFinding.rationale}</p>
                  {selectedFinding.start != null ? <p className="caption">Exact source span [{selectedFinding.start}:{selectedFinding.end}], in Unicode characters.</p> : <p className="notice">Absent field: {selectedFinding.absent_field}. There is no source span to highlight.</p>}
                  <p className="caption">Review status: {reviews[selectedFinding.finding_id] || "Unreviewed"}</p>
                </> : <p>Select “Locate evidence” on any finding to inspect the document. Missing fields remain explicitly absent.</p>}
              </div>
            </div>
          </article>
          <article className="panel">
            <h2>Requirements, with their context.</h2>
            {result.requirements.length ? (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Skill</th>
                      <th>Designation</th>
                      <th>Exact phrase</th>
                      <th>Source context</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.requirements.map((r: any) => (
                      <tr key={r.requirement_id}>
                        <td>
                          <strong>{r.skill_name}</strong>
                        </td>
                        <td>
                          <span className="badge">{r.requirement_type}</span>
                        </td>
                        <td>{r.source_phrase}</td>
                        <td>{r.source_text}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p>
                No controlled skills were found. This does not establish that
                the role has no requirements.
              </p>
            )}
          </article>
          <article className="panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">REVIEW, DON’T JUST ACCEPT</p>
                <h2>{result.findings.length} points to inspect.</h2>
              </div>
            </div>
            <p className="caption">
              Each finding is a review prompt. Suggestions ask for
              clarification; they do not invent salary, benefits or company
              policy.
            </p>
            <label className="field">Finding category
              <select value={category} onChange={(e) => setCategory(e.target.value)}>
                <option>All categories</option>
                {Array.from(new Set<string>(result.findings.map((f: any) => f.category))).sort().map(c => <option key={c}>{c}</option>)}
              </select>
            </label>
            <p className="caption">{visibleFindings.length} shown · {accepted.length} accepted for clarification. Dismissal keeps the source and the finding in your report.</p>
            {visibleFindings.map((f: any) => (
              <details key={f.finding_id} className="finding">
                <summary>
                  <span className="badge">{f.category}</span>
                  <strong>
                    {f.rule.replaceAll(".", " / ").replaceAll("_", " ")}
                  </strong>
                  <span className="muted">{f.severity}</span>
                </summary>
                <button className="button-small" aria-pressed={selected === f.finding_id} onClick={() => { setSelected(f.finding_id); document.querySelector('[data-testid="diagnostic-source"]')?.scrollIntoView({ behavior: "auto", block: "center" }); }}>Locate evidence</button>
                <p>{f.rationale}</p>
                {f.source_phrase ? (
                  <blockquote>
                    {f.source_phrase}
                    <small>
                      Exact span [{f.start}:{f.end}] in the supplied text
                    </small>
                  </blockquote>
                ) : (
                  <p className="notice">Absent field: {f.absent_field}</p>
                )}
                <div className="grid-two">
                  <label className="field">
                    Your review
                    <select
                      value={reviews[f.finding_id] || "Unreviewed"}
                      onChange={(e) =>
                        setReviews({
                          ...reviews,
                          [f.finding_id]: e.target.value,
                        })
                      }
                    >
                      <option>Unreviewed</option>
                      <option>Accepted for clarification</option>
                      <option>Dismissed</option>
                      <option>Uncertain</option>
                    </select>
                  </label>
                  <label className="field">
                    Editable clarification proposal
                    <textarea
                      rows={3}
                      value={edits[f.finding_id] ?? f.suggestion}
                      onChange={(e) =>
                        setEdits({ ...edits, [f.finding_id]: e.target.value })
                      }
                    />
                  </label>
                </div>
                <p className="caption">
                  The original text is unchanged. Confirm facts before using
                  this proposal.
                </p>
              </details>
            ))}
          </article>
          <article className="panel">
            <p className="eyebrow">ORIGINAL → PROPOSED</p>
            <h2>Clarification change review.</h2>
            <p className="caption">Only accepted proposals appear here. They add review questions; they do not silently replace facts. Dismissed, uncertain and unreviewed findings add nothing. Confirm every answer before publishing a revised description.</p>
            {accepted.length ? <div className="grid-two">
              <div><h3>Original, unchanged</h3><pre style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere", fontFamily: "inherit" }}>{text}</pre></div>
              <div><h3>Proposed additions</h3><p>All original wording is retained.</p>
                {accepted.map((f: any, i: number) => <div className="finding" key={f.finding_id}>
                  <p><strong>{i + 1}. {f.category}</strong></p>
                  <p className="caption">{f.source_phrase ? <>After: <q>{f.source_phrase}</q></> : <>Add disclosure for: {f.absent_field}</>}</p>
                  <ins style={{ display: "block", whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>+ [Author clarification requested] {edits[f.finding_id] ?? f.suggestion}</ins>
                </div>)}
              </div>
            </div> : <p className="notice">No accepted proposals yet. Review a finding and choose “Accepted for clarification” to inspect its proposed addition beside the original.</p>}
          </article>
          <article className="panel">
            <h2>Comparable-posting benchmark</h2>
            <p className="notice">Unavailable: no reviewed comparable observed sample is connected. Synthetic examples are excluded.</p>
            <p className="caption">0 comparable observed postings · minimum 20 within the same role family and relevant scope. No salary-disclosure percentage or employer comparison is inferred. These deterministic checks have not been independently human-evaluated.</p>
          </article>
          <div className="export-panel">
            <div>
              <h3>Keep the reasoning.</h3>
              <p>
                Export the reviewed findings without the original description or
                exact source phrases. Check edited suggestions for personal
                information.
              </p>
            </div>
            <button
              className="button-secondary"
              onClick={() =>
                downloadJSON("job-description-diagnostic.json", report())
              }
            >
              <Download size={16} />
              Download report
            </button>
          </div>
          <p className="caption">{result.limitations}</p>
        </>
      )}
    </section>
  );
}
