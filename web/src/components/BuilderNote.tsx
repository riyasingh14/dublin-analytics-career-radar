import { ArrowUpRight } from "lucide-react";
import BuilderContacts from "./BuilderContacts";

export default function BuilderNote() {
  return <section className="builder-note" id="builder" aria-labelledby="builder-title" tabIndex={-1}>
    <div className="builder-cell-heading">
      <span className="builder-avatar" aria-hidden="true">RS</span>
      <div><p className="builder-kicker">BUILT BY</p><h2 id="builder-title">Riya Singh<span>.</span></h2><p className="builder-focus">Business &amp; Data Analytics</p></div>
      <a className="builder-about" href="#/builder" aria-label="About Riya Singh"><ArrowUpRight size={19} /></a>
    </div>
    <BuilderContacts />
  </section>;
}
