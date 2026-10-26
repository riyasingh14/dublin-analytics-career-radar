import { ArrowUpRight, ArrowRight, Database, ScanText, Network, Compass } from "lucide-react";
import BuilderContacts from "../components/BuilderContacts";

const practices = [
  { number: "01", title: "Start with the decision.", text: "What does someone need to understand or do next? I use that question to shape the analysis, rather than starting with a chart.", icon: Compass },
  { number: "02", title: "Get close to the data.", text: "Trace the source, inspect what is missing, remove duplicates and make the model explicit. A useful result needs a foundation someone else can inspect.", icon: Database },
  { number: "03", title: "Make the evidence visible.", text: "Connect a finding to the words, counts and assumptions behind it. Keep uncertainty in the story, even when it makes the answer less tidy.", icon: ScanText },
  { number: "04", title: "Build something useful.", text: "Turn the analysis into an experience: a clearer requirement, a visible evidence gap, or a concrete next step. Then test how it works for the person using it.", icon: Network },
];

export default function Builder() {
  return <section className="tool-page builder-page">
    <div className="builder-page-hero">
      <div>
        <p className="eyebrow">MEET THE BUILDER / RIYA SINGH</p>
        <h1>Curiosity in.<br /><em>Clarity out.</em></h1>
        <p className="lede">Hi, I’m Riya Singh. I’m building a career in business and data analytics—and Career Radar is where I put that curiosity to work.</p>
        <p>I like the part where an open question becomes something you can investigate: a dataset, a model, a visual and, eventually, a decision you can explain.</p>
        <div className="builder-page-contact"><BuilderContacts /></div>
      </div>
      <figure className="builder-portrait" aria-label="Riya Singh monogram">
        <span className="portrait-overline">THE HUMAN BEHIND THE RADAR <ArrowUpRight size={20} /></span>
        <span className="portrait-initials" aria-hidden="true">RS<span>✳</span></span>
        <figcaption><strong>Riya Singh</strong><span>Business &amp; Data Analytics</span><small>Questions welcome. Assumptions checked.</small></figcaption>
      </figure>
    </div>
    <section className="builder-story" aria-labelledby="why-radar">
      <p className="eyebrow">WHY I BUILT THIS</p>
      <div><h2 id="why-radar">A portfolio you can actually explore.</h2><p>Job descriptions contain plenty of signals, but a list of keywords rarely tells the full story. I wanted to explore what happens when you connect those signals: which skills appear together, what a role is asking for, and what evidence a candidate can show.</p><p>Career Radar is my way of bringing business questions and analytical methods into one usable product. It connects Python pipelines, SQL modelling, data-quality checks, rule-based text analysis and interactive visualisation.</p><p>The limits are part of the work. Market samples identify their source and coverage. Career histories are labelled synthetic. Archived employer descriptions are identified as historical. Readiness is an inspectable evidence checklist, not a promise of an interview.</p><a className="text-link" href="#/methodology">See the methods and limitations <ArrowUpRight size={16} /></a></div>
    </section>
    <section className="builder-practices" aria-labelledby="builder-approach"><div className="section-heading"><div><p className="eyebrow">HOW I APPROACH THE WORK</p><h2 id="builder-approach">From a better question<br />to a useful next step.</h2></div></div><div className="grid-two">{practices.map(({ number, title, text, icon: Icon }) => <article className="panel" key={number}><div className="builder-practice-number"><span>{number}</span><Icon size={23} aria-hidden="true" /></div><h3>{title}</h3><p>{text}</p></article>)}</div></section>
    <section className="builder-invitation" aria-labelledby="builder-connect"><div><p className="eyebrow">LET’S TALK</p><h2 id="builder-connect">Have a question behind your data?</h2><p>I’m interested in business analyst and data analyst opportunities where I can keep learning, work through real problems and help people make clearer decisions.</p></div><a className="button" href="mailto:kashyapriya2020@gmail.com">Say hello to Riya <ArrowRight size={17} /></a></section>
  </section>;
}
