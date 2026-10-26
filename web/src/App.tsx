import { lazy, Suspense, useEffect, useState } from "react";
import {
  ArrowUpRight,
  ArrowRight,
  Radar,
  Network,
  Compass,
  Route,
  ScanText,
  Menu,
  X,
  Github,
  Pause,
  Play,
} from "lucide-react";
import { api, Bootstrap } from "./lib/api";
import DataCoverage from "./components/DataCoverage";
import { useStudioMotion } from "./components/StudioMotion";
import AnalyticalSculpture from "./components/AnalyticalSculpture";
import BuilderNote from "./components/BuilderNote";
import Builder from "./pages/Builder";
const Constellation = lazy(() => import("./tools/Constellation"));
const Readiness = lazy(() => import("./tools/Readiness"));
const Mobility = lazy(() => import("./tools/Mobility"));
const Diagnostic = lazy(() => import("./tools/Diagnostic"));

const tools = [
  {
    id: "constellation",
    number: "01",
    name: "Skill Constellation",
    title: "Find the connections.",
    text: "See which skills travel together. Follow a connection all the way back to its evidence.",
    tag: "SKILL RELATIONSHIPS",
    icon: Network,
  },
  {
    id: "readiness",
    number: "02",
    name: "Readiness Studio",
    title: "Know what you can show.",
    text: "Turn a job description into an evidence checklist. See strengths, gaps and what remains unknown.",
    tag: "SELF-REPORTED EVIDENCE",
    icon: Compass,
  },
  {
    id: "mobility",
    number: "03",
    name: "Career Mobility Lab",
    title: "Explore a different path.",
    text: "Investigate simulated career moves, salary trajectories and the assumptions behind them.",
    tag: "SYNTHETIC SCENARIOS",
    icon: Route,
  },
  {
    id: "diagnostic",
    number: "04",
    name: "JD Diagnostic",
    title: "Read beyond the title.",
    text: "Find unclear requirements and missing information in a job description, with the source text in view.",
    tag: "DESCRIPTION ANALYSIS",
    icon: ScanText,
  },
];
function currentRoute() {
  return location.hash.startsWith("#/")
    ? location.hash.slice(2) || "home"
    : "home";
}
function Home({ bootstrap, motionEnabled }: { bootstrap: Bootstrap | null; motionEnabled: boolean }) {
  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <BuilderNote />
          <p className="eyebrow">
            <span className="status-dot" />
            DUBLIN ROOTS. IRELAND-WIDE QUESTIONS.
          </p>
          <h1>
            Evidence for your
            <br />
            <em>next career move.</em>
          </h1>
          <p className="lede">
            Four analytical tools. One clearer perspective on skills,
            opportunities and the paths between them.
          </p>
          <div className="hero-actions">
            <a className="button" href="#/constellation">
              Explore the tools <ArrowRight size={17} />
            </a>
            <a className="text-link" href="#/methodology">
              How the evidence works <ArrowUpRight size={15} />
            </a>
          </div>
          <p className="hero-note">
            Built for curious candidates, thoughtful recruiters and better
            questions.
            {" "}<a href="#/builder">Meet Riya <ArrowUpRight size={12} /></a>
          </p>
        </div>
        <div className="hero-art">
          <AnalyticalSculpture motionEnabled={motionEnabled} />
        </div>
      </section>
      <section className="intro-strip intention-strip" aria-labelledby="project-intention">
        <div><p className="eyebrow">WHY I BUILT THIS</p><h2 id="project-intention">A portfolio you can put to work.</h2></div>
        <div className="intention-copy"><p>I’m building a career in business and data analytics, and I wanted a place where you could see how I approach a question: working through the data, checking my assumptions and explaining what I find.</p><p>Career Radar brings that work into tools you can try for yourself. My aim is to help people make sense of job requirements, recognise the skills they can demonstrate and figure out what to work on next.</p></div>
        <a className="intention-signature" href="#/builder"><span className="intention-initials" aria-hidden="true">RS</span><span><strong>Riya Singh</strong><span>Builder · Business &amp; Data Analytics</span><span className="intention-link">A little more about me <ArrowUpRight size={14} /></span></span></a>
      </section>
      <section className="tools-section">
        <div className="section-heading">
          <div>
            <p className="eyebrow">YOUR ANALYTICAL WORKSPACE</p>
            <h2>
              Choose a question.
              <br />
              Follow the evidence.
            </h2>
          </div>
          <p>
            Start with the question that matters to you.
            <br />
            Each tool offers a different way to investigate.
          </p>
        </div>
        <div className="tool-grid">
          {tools.map((tool) => (
            <a
              href={`#/${tool.id}`}
              className={`tool-card tool-card-${tool.id}`}
              key={tool.id}
            >
              <div className="card-top">
                <span>
                  {tool.number} / {tool.name.toUpperCase()}
                </span>
                <tool.icon size={26} strokeWidth={1.3} />
              </div>
              <h3>{tool.title}</h3>
              <p>{tool.text}</p>
              <div className="card-bottom">
                <span className="badge">{tool.tag}</span>
                <ArrowUpRight size={22} />
              </div>
            </a>
          ))}
        </div>
      </section>
      <section className="evidence-band">
        <div>
          <p className="eyebrow">WHAT YOU’RE LOOKING AT</p>
          <h2>
            A working demo.
            <br />
            No hidden assumptions.
          </h2>
          <p>
            The analytical views use generated examples. Description tools also
            offer attributed, archived employer-written examples. The private research
            pipeline stays separate until source permissions and human review
            are complete.
          </p>
          <a href="#/methodology" className="text-link">
            Inspect the methodology <ArrowUpRight size={16} />
          </a>
        </div>
        <div className="evidence-facts">
          <div>
            <span>Skill sample</span>
            <strong>
              {bootstrap
                ? bootstrap.snapshot.market.sample_size + " fictional postings"
                : "Loading demonstration…"}
            </strong>
          </div>
          <div>
            <span>Mobility histories</span>
            <strong>Synthetic, reproducible</strong>
          </div>
          <div>
            <span>Readiness inputs</span>
            <strong>Self-reported, transient</strong>
          </div>
          <div>
            <span>Hiring predictions</span>
            <strong>None</strong>
          </div>
        </div>
      </section>
    </>
  );
}
function Methodology() {
  return (
    <section className="tool-page">
      <p className="eyebrow">METHODS / LIMITATIONS</p>
      <h1>
        Evidence, with its
        <br />
        limits in view.
      </h1>
      <p className="lede">
        The public website is a demonstration of analytical methods, not a
        census of Irish employment.
      </p>
      <div className="grid-two">
        <article className="panel">
          <p className="eyebrow">THE FIVE-MINUTE PORTFOLIO WALKTHROUGH</p>
          <h2>One question. A traceable decision.</h2>
          <ol className="walkthrough-list">
            <li><a href="#/constellation">Find a skill pair</a> and trace its count to exact source phrases.</li>
            <li><a href="#/diagnostic">Diagnose a description</a> and inspect the source behind one clarification.</li>
            <li><a href="#/readiness">Assess an evidence gap</a>, inspect the arithmetic and prepare a proof-of-work brief.</li>
            <li><a href="#/mobility">Explore a synthetic career flow</a>, then inspect the cohort, salary variation and assumptions.</li>
          </ol>
          <p>Each step demonstrates a different analytical skill: data modelling,
            quality checks, requirements analysis, scenario design and communication.</p>
        </article>
        <article className="panel">
          <h2>Keep the data types distinct</h2>
          <p>
            <strong>Synthetic:</strong> the constellation examples and career
            histories are generated, not real vacancies or observed salary
            outcomes.
          </p>
          <p>
            <strong>Self-reported:</strong> readiness evidence is supplied by
            you, not verified by an employer.
          </p>
          <p>
            <strong>User-provided:</strong> a pasted description is analysed as
            supplied; source claims are not independently verified.
          </p>
          <p><strong>Archived employer descriptions:</strong> complete public-domain
            US examples are attributed in the description tools. They are not
            current vacancies, Irish-market observations or validated benchmarks.</p>
        </article>
        <article className="panel">
          <h2>Data and privacy</h2>
          <p>
            Descriptions and evidence are sent transiently to the same-site
            Python API when you request analysis. They are not saved by the
            application, placed in URLs or sent to an external language model.
          </p>
          <p>
            Avoid personal identifiers and confidential documents. Clearing a
            tool removes browser state; downloaded files remain on your device.
            Hosting platforms may retain operational request metadata under
            their policies.
          </p>
        </article>
        <article className="panel">
          <h2>Interpret the calculations</h2>
          <p>
            Co-mention does not establish causation. Alignment is an inspectable
            index, not callback probability. Scenario salary changes follow
            disclosed generator assumptions, not real career returns.
          </p>
          <p>
            Small groups are flagged or suppressed. Required/preferred
            classifications can be corrected before assessment.
          </p>
        </article>
        <article className="panel">
          <h2>From research to public data</h2>
          <p>
            The private pipeline supports Ireland-wide posting imports,
            deduplication and 64 controlled skills. Public real-data release
            needs source/display permissions and applicable human extraction
            evaluation.
          </p>
          <p>
            The extraction baseline gate is 100 reviews at 90% precision. It
            does not establish market representativeness or validate every
            downstream score.
          </p>
          <a
            href="https://github.com/riyasingh14/dublin-analytics-career-radar"
            target="_blank"
            rel="noreferrer"
            className="text-link"
          >
            Inspect the project <Github size={16} />
          </a>
        </article>
      </div>
    </section>
  );
}
export default function App() {
  const motion = useStudioMotion();
  const [route, setRoute] = useState(currentRoute),
    [menu, setMenu] = useState(false),
    [bootstrap, setBootstrap] = useState<Bootstrap | null>(null),
    [error, setError] = useState(""),
    [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const change = () => {
      setRoute(currentRoute());
      setMenu(false);
      window.scrollTo(0, 0);
      // A mobile route change hides navigation: move focus back into visible content.
      document.getElementById("main")?.focus({ preventScroll: true });
    };
    window.addEventListener("hashchange", change);
    return () => window.removeEventListener("hashchange", change);
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    setError("");
    api<Bootstrap>("bootstrap", {}, controller.signal)
      .then(setBootstrap)
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => controller.abort();
  }, [attempt]);
  const active = tools.find((t) => t.id === route);
  return (
    <>
      <a
        href="#main"
        className="skip-link"
        onClick={(e) => {
          e.preventDefault();
          document.getElementById("main")?.focus();
        }}
      >
        Skip to content
      </a>
      <header className="site-header">
        <a href="#/" className="brand" title="Career Radar home">
          <span className="brand-mark">
            <Radar size={25} />
          </span>
          <span>
            CAREER <b>RADAR</b>
            <small>IRELAND / ANALYTICAL STUDIO</small>
          </span>
        </a>
        <button
          className="menu-toggle"
          aria-expanded={menu}
          aria-controls="site-nav"
          aria-label="Toggle navigation"
          onClick={() => setMenu(!menu)}
        >
          {menu ? <X /> : <Menu />}
        </button>
        <nav
          id="site-nav"
          className={menu ? "open" : ""}
          aria-label="Main navigation"
          onKeyDown={(event) => {
            if (event.key === "Escape" && menu) {
              setMenu(false);
              document.querySelector<HTMLButtonElement>(".menu-toggle")?.focus();
            }
          }}
        >
          <a href="#/" aria-current={route === "home" ? "page" : undefined}>
            Overview
          </a>
          {tools.map((t) => (
            <a
              key={t.id}
              href={`#/${t.id}`}
              aria-current={route === t.id ? "page" : undefined}
            >
              {t.name}
            </a>
          ))}
          <a href="#/builder" aria-current={route === "builder" ? "page" : undefined}>Builder</a>
          <a
            href="#/methodology"
            aria-current={route === "methodology" ? "page" : undefined}
          >
            Methods
          </a>
        </nav>
        <button className="motion-control" onClick={motion.toggle} disabled={motion.reduced} aria-pressed={motion.enabled}>
          {motion.enabled ? <Pause size={12} /> : <Play size={12} />}
          {motion.reduced ? "Reduced motion" : motion.enabled ? "Pause motion" : "Enable motion"}
        </button>
      </header>
      <main id="main" tabIndex={-1}>
        {route === "home" && <DataCoverage bootstrap={bootstrap} />}
        {error && (
          <div className="error" role="alert">
            {error}{" "}
            <button
              className="button-small"
              onClick={() => setAttempt((x) => x + 1)}
            >
              Retry connection
            </button>
          </div>
        )}
        {route === "home" ? (
          <Home bootstrap={bootstrap} motionEnabled={motion.enabled} />
        ) : route === "builder" ? (
          <Builder />
        ) : route === "methodology" ? (
          <Methodology />
        ) : active ? (
          <>
            <div className="breadcrumb">
              <a href="#/">Studio</a>
              <span>/</span>
              {active.name}
            </div>
            <Suspense
              fallback={
                <p className="notice" role="status">
                  Opening analytical tool…
                </p>
              }
            >
              {route === "constellation" ? (
                <Constellation bootstrap={bootstrap} />
              ) : route === "readiness" ? (
                <Readiness bootstrap={bootstrap} />
              ) : route === "mobility" ? (
                <Mobility bootstrap={bootstrap} />
              ) : (
                <Diagnostic bootstrap={bootstrap} />
              )}
            </Suspense>
          </>
        ) : (
          <section className="tool-page">
            <h1>That page is not here.</h1>
            <a href="#/" className="button">
              Return to the studio
            </a>
          </section>
        )}
      </main>
      <footer>
        <a href="#/" className="brand-footer">
          CAREER RADAR
        </a>
        <p>
          Evidence before inference.
          <br />A data and business analysis portfolio project.
        </p>
        <a href="#/methodology">
          Methods & data notes <ArrowUpRight size={15} />
        </a>
        <span>IRELAND · 2026</span>
      </footer>
    </>
  );
}
