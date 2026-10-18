import { Bootstrap } from "../lib/api";

export default function DataCoverage({ bootstrap }: { bootstrap: Bootstrap | null }) {
  const snapshot = bootstrap?.snapshot;
  return (
    <details className="coverage-passport">
      <summary>Data passport <span>Generated examples · inspect coverage & provenance</span></summary>
      <dl className="coverage-grid">
        <div><dt>Public skill sample</dt><dd>{snapshot ? `${snapshot.market.sample_size} postings · fictional` : "Waiting for the API"}</dd></div>
        <div><dt>Source coverage</dt><dd>Authored fixture; no observed job-feed coverage</dd></div>
        <div><dt>Geography</dt><dd>Dublin and rest of Ireland; generated locations</dd></div>
        <div><dt>Collection window</dt><dd>Not applicable — generated, not collected</dd></div>
        <div><dt>Fixture built</dt><dd>{snapshot?.metadata?.generated_at ? new Date(snapshot.metadata.generated_at).toLocaleString("en-IE", { timeZone: "Europe/Dublin", dateStyle: "medium", timeStyle: "short" }) + " · Dublin time" : "Not available"}</dd></div>
        <div><dt>Extraction</dt><dd>Exact alias rules · taxonomy-v2-tech</dd></div>
        <div><dt>Review status</dt><dd>Demonstration fixture; no human-reviewed market release</dd></div>
        <div><dt>Other inputs</dt><dd>Pasted descriptions: source unverified. Candidate evidence: self-reported. Mobility: synthetic.</dd></div>
      </dl>
      <p className="caption">Fixture generation time is not a collection date. Role comparison has its own labelled fixture and denominators. No complete Irish-market coverage or hiring outcomes are implied.</p>
    </details>
  );
}
