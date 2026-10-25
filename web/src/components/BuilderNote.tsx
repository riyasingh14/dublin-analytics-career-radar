import { ArrowUpRight, Github, Linkedin, Sparkles } from "lucide-react";

export default function BuilderNote() {
  return (
    <section className="builder-note" id="builder" aria-labelledby="builder-title" tabIndex={-1}>
      <div className="builder-monogram" aria-hidden="true">
        <span>RS</span><Sparkles size={23} />
        <small>CURIOSITY: ALWAYS ON</small>
      </div>
      <div className="builder-copy">
        <p className="eyebrow">BUILT BY RIYA SINGH</p>
        <h2 id="builder-title">The human behind the radar.</h2>
        <p>Hi, I’m Riya. I’m building a career in business and data analytics—and
          this is where I turn the methods into something you can actually use.</p>
        <p>I like following a question all the way through: messy inputs, SQL models,
          a clear visual, an honest limitation and a useful next step.</p>
        <div className="builder-actions">
          <a className="text-link" href="https://www.linkedin.com/in/riya-singh-business-analyst/" target="_blank" rel="noreferrer">
            <Linkedin size={15} /> Connect on LinkedIn <ArrowUpRight size={15} />
          </a>
          <a className="text-link" href="https://github.com/riyasingh14/dublin-analytics-career-radar" target="_blank" rel="noreferrer">
            <Github size={15} /> Explore the build <ArrowUpRight size={15} />
          </a>
          <a className="text-link" href="#/methodology">Follow the method <ArrowUpRight size={15} /></a>
        </div>
      </div>
      <div className="builder-process" aria-label="Riya’s analytical approach">
        <span>01 <strong>Ask a better question.</strong></span>
        <span>02 <strong>Make the evidence visible.</strong></span>
        <span>03 <strong>Help someone decide.</strong></span>
        <p>A little curiosity.<br />A lot of checking the denominator.</p>
      </div>
    </section>
  );
}
