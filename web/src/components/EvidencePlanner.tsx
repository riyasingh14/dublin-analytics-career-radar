import { useState } from "react";
import { ArrowRight, Download } from "lucide-react";
import { downloadJSON, format } from "../lib/api";

type Status = "supported" | "partial" | "missing" | "unknown";
type Breakdown = Record<Status, { skill_count: number; weight: number }>;
export type EvidenceAction = {
  skill_id: string;
  skill_name: string;
  requirement_type: string;
  requirement_ids: string[];
  status: Status;
  weight: number;
  rank: number;
  kind: "clarify_evidence" | "build_evidence";
  title: string;
  reason: string;
  project_brief: string | null;
  deliverables: string[];
  completion_checks: string[];
};
export type ActionPlan = {
  version: string;
  label: string;
  priority_method: string;
  actions: EvidenceAction[];
  limitation: string;
};
const statusLabels: Record<Status, string> = {
  supported: "Supported",
  partial: "Partial evidence",
  missing: "Missing evidence",
  unknown: "Unassessed",
};
const statuses = Object.keys(statusLabels) as Status[];

export function EvidenceBreakdown({ breakdown, totalWeight }: {
  breakdown: Breakdown;
  totalWeight: number;
}) {
  return (
    <div className="evidence-breakdown">
      <h3>Where the evidence stands.</h3>
      <p className="caption">Each confirmed skill counts once at its strongest requirement level.
        Bar widths show requirement weight, not hiring probability.</p>
      {totalWeight > 0 && (
        <div className="evidence-weight-bar" role="img" aria-label={statuses.map((s) =>
          `${statusLabels[s]}: ${breakdown[s].weight} of ${totalWeight} requirement weight`).join("; ")}>
          {statuses.filter((s) => breakdown[s].weight > 0).map((s) => (
            <span key={s} className={`evidence-segment evidence-${s}`}
              style={{ width: `${100 * breakdown[s].weight / totalWeight}%` }} />
          ))}
        </div>
      )}
      <dl className="evidence-legend">
        {statuses.map((s) => (
          <div key={s}>
            <dt><span className={`evidence-dot evidence-${s}`} />{statusLabels[s]}</dt>
            <dd><strong>{breakdown[s].skill_count}</strong> skills · {format(breakdown[s].weight)} weight</dd>
          </div>
        ))}
      </dl>
      <p className="caption">Unassessed is an information gap, not a confirmed skill deficit.
        Uncertain and negated requirements are outside this breakdown.</p>
    </div>
  );
}

export default function EvidencePlanner({ plan, rows, busy, onExplore, onReview }: {
  plan: ActionPlan;
  rows: { requirement_id: string; source_text: string }[];
  busy: boolean;
  onExplore: (action: EvidenceAction) => void;
  onReview: (action: EvidenceAction) => void;
}) {
  const [showAll, setShowAll] = useState(false);
  return (
    <article className="panel evidence-planner">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">FROM GAP TO PROOF</p>
          <h2>Your next evidence action.</h2>
        </div>
        <span className="badge">PROPOSED · NOT VERIFIED</span>
      </div>
      <p>Start with what the description requires. Review unknowns before committing
        to a new project; then build something you can explain and test.</p>
      <details className="plan-method">
        <summary>How actions are prioritised</summary>
        <p>{plan.priority_method}</p>
      </details>
      {plan.actions.length === 0 ? (
        <div className="notice">
          No new project is suggested from this assessment. Confirmed skills may
          already have supported evidence, or no confirmed skill requirements were found.
          Check the source and other eligibility conditions separately.
        </div>
      ) : (
        <div className="evidence-actions">
          {plan.actions.slice(0, showAll ? plan.actions.length : 3).map((action) => (
            <section className="evidence-action" key={action.skill_id}>
              <div className="requirement-head">
                <h3>{action.rank}. {action.title}</h3>
                <span className="badge">{action.requirement_type} · {action.weight} weight</span>
              </div>
              <p>{action.reason}</p>
              {action.project_brief && (
                <div className="project-brief">
                  <p className="eyebrow">AUTHORED PROJECT BRIEF</p>
                  <p>{action.project_brief}</p>
                </div>
              )}
              <details>
                <summary>{action.kind === "clarify_evidence" ? "Evidence review checklist" : "Deliverables and completion checks"}</summary>
                {action.deliverables.length > 0 && <>
                  <h4>What to produce</h4>
                  <ul>{action.deliverables.map((d) => <li key={d}>{d}</li>)}</ul>
                </>}
                <h4>{action.kind === "clarify_evidence" ? "What to check" : "How to check your work"}</h4>
                <ul>{action.completion_checks.map((c) => <li key={c}>{c}</li>)}</ul>
              </details>
              <details>
                <summary>Trace to {action.requirement_ids.length} source context{action.requirement_ids.length === 1 ? "" : "s"}</summary>
                {rows.filter((r) => action.requirement_ids.includes(r.requirement_id)).map((r) => (
                  <blockquote key={r.requirement_id}>{r.source_text}</blockquote>
                ))}
              </details>
              <button className="button-secondary" disabled={busy} onClick={() =>
                action.kind === "clarify_evidence" ? onReview(action) : onExplore(action)}>
                {action.kind === "clarify_evidence" ? `Review ${action.skill_name} evidence` : `Explore ${action.skill_name} project hypothetically`}
                <ArrowRight size={16} />
              </button>
            </section>
          ))}
        </div>
      )}
      {plan.actions.length > 3 && <button className="button-small" onClick={() => setShowAll(!showAll)}>
        {showAll ? "Show first 3 actions" : `Show all ${plan.actions.length} actions`}
      </button>}
      <p className="caption">{plan.limitation} Creating a plan changes no evidence status or score.</p>
      <button className="button-secondary" onClick={() => downloadJSON("proposed-evidence-actions.json", plan)}>
        <Download size={16} /> Download action plan
      </button>
    </article>
  );
}
