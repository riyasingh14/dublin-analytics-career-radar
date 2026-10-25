import { ArrowUpRight, Github, Linkedin, Mail, Sparkles } from "lucide-react";

export default function BuilderNote() {
  return (
    <section className="builder-note" id="builder" aria-labelledby="builder-title" tabIndex={-1}>
      <div className="builder-topline">
        <span><span className="builder-beacon" /> MEET THE BUILDER</span>
        <Sparkles size={19} aria-hidden="true" />
      </div>
      <div className="builder-identity">
        <span className="builder-monogram" aria-hidden="true">RS<span>↗</span></span>
        <div>
          <h2 id="builder-title">Riya Singh<span>.</span></h2>
          <p>Business &amp; Data Analytics</p>
        </div>
      </div>
      <p className="builder-intro">Curious mind. Analytical instincts.<br />The human turning this radar into reality.</p>
      <div className="builder-method" aria-label="My approach">
        <span>Ask sharply</span><span>Build carefully</span><span>Make it useful</span>
      </div>
      <div className="builder-actions">
        <a href="https://www.linkedin.com/in/riya-singh-business-analyst/" target="_blank" rel="noreferrer" aria-label="Connect on LinkedIn">
          <Linkedin size={16} /> LinkedIn <ArrowUpRight size={14} />
        </a>
        <a href="https://github.com/riyasingh14" target="_blank" rel="noreferrer" aria-label="Riya’s GitHub profile">
          <Github size={16} /> GitHub <ArrowUpRight size={14} />
        </a>
        <a href="mailto:kashyapriya2020@gmail.com" aria-label="Email Riya at kashyapriya2020@gmail.com">
          <Mail size={16} /> Email <ArrowUpRight size={14} />
        </a>
      </div>
      <div className="builder-footer"><span>FROM QUESTIONS → TO DECISIONS</span><span>Built with curiosity ↗</span></div>
    </section>
  );
}
