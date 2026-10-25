import { ArrowUpRight } from "lucide-react";
import { DescriptionSample } from "../lib/api";

export function descriptionProvenance(sample: DescriptionSample | null, modified: boolean) {
  return sample ? {
    kind: "archived-employer-description",
    sample_id: sample.id,
    title: sample.title,
    organisation: sample.organisation,
    geography: sample.geography,
    vacancy_status: "Archived; not a current vacancy",
    source_url: sample.source_url,
    source_commit: sample.source_commit,
    retrieved_on: sample.retrieved_on,
    license: sample.license,
    license_url: sample.license_url,
    modified_from_source: modified,
  } : null;
}

export default function DescriptionLibrary({ samples, selected, modified, disabled, onSelect }: {
  samples: DescriptionSample[];
  selected: DescriptionSample | null;
  modified: boolean;
  disabled: boolean;
  onSelect: (sample: DescriptionSample) => void;
}) {
  if (!samples.length) return null;
  return (
    <div className="description-library">
      <p className="eyebrow">TRY A COMPLETE EMPLOYER-WRITTEN DESCRIPTION</p>
      <label className="field">
        Real description examples
        <select aria-label="Real description examples" disabled={disabled} value={selected?.id || ""}
          onChange={(event) => {
            const sample = samples.find((item) => item.id === event.target.value);
            if (sample) onSelect(sample);
          }}>
          <option value="">Choose an archived example…</option>
          {samples.map((sample) => <option key={sample.id} value={sample.id}>{sample.title} · US · archived</option>)}
        </select>
      </label>
      <p className="caption">Complete, employer-written US examples from a public-domain archive.
        They are historical reference inputs, not current Irish vacancies or market benchmarks.</p>
      {selected && <div className="description-source" role="note" aria-label="Description source and status">
        <strong>{selected.title} · {selected.organisation}</strong>
        <p>{selected.geography} · Archived; not a current vacancy · {selected.license}</p>
        <p>{modified ? "Edited from the archived source. This is your modified input, not the original wording." : "Loaded from the archived employer description; the full text is available below."}</p>
        <div className="action-row">
          <a className="text-link" href={selected.source_url} target="_blank" rel="noreferrer">Read the original source <ArrowUpRight size={14} /></a>
          <a className="text-link" href={selected.license_url} target="_blank" rel="noreferrer">Reuse licence <ArrowUpRight size={14} /></a>
          {modified && <button className="button-small" disabled={disabled} onClick={() => onSelect(selected)}>Restore source text</button>}
        </div>
        <p className="caption">Plain-text reference · retrieved {selected.retrieved_on}; this is not a posting date.</p>
        <details className="description-preparation"><summary>How this example was prepared</summary>
          <p className="caption">{selected.derivation}</p>
        </details>
      </div>}
    </div>
  );
}
