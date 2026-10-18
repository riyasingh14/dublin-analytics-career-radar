export type ListingCondition = {
  condition_id: string;
  category: string;
  source_text: string;
  start: number;
  end: number;
};
const labels: Record<string, string> = {
  degree: "Qualification or grade", experience: "Experience duration",
  location: "Location or attendance", work_eligibility: "Work eligibility or sponsorship",
};
export default function ListingConditions({ conditions, responses, onChange }: {
  conditions: ListingCondition[];
  responses: Record<string, string>;
  onChange: (id: string, value: string) => void;
}) {
  return <article className="panel listing-conditions">
    <p className="eyebrow">SEPARATE LISTING CHECKLIST</p>
    <h2>Conditions to check with the source.</h2>
    <p>Literal phrases only. These cues do not decide your eligibility and never enter the skill index.
      Check alternatives, optional language and negations yourself. Do not enter immigration details or other sensitive information.</p>
    {conditions.length === 0 ? <p className="notice">No condition cues detected. This does not establish that no conditions apply; manually review the full listing.</p>
      : conditions.map((condition) => <section className="requirement-card" key={condition.condition_id}>
        <h3>{labels[condition.category] || condition.category}</h3>
        <blockquote>{condition.source_text}</blockquote>
        <p className="caption">Exact source characters {condition.start}–{condition.end} · rule cue · needs manual review</p>
        <label className="field">Your private checklist: {labels[condition.category] || condition.category}
          <select aria-label={"Your private checklist: " + (labels[condition.category] || condition.category)} value={responses[condition.condition_id] || "unknown"}
            onChange={(e) => onChange(condition.condition_id, e.target.value)}>
            <option value="unknown">Unknown / needs review</option>
            <option value="appears_met">Appears met — self-checked</option>
            <option value="clarify">Clarify with the employer</option>
            <option value="not_applicable">Not applicable after reviewing the phrase</option>
          </select>
        </label>
      </section>)}
    <p className="caption">Checklist responses stay in this page’s memory, are excluded from API requests and downloads,
      and are cleared with Clear all or when the source changes. No credential is verified.</p>
  </article>;
}
