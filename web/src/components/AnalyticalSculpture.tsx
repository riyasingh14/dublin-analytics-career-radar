import { useEffect, useId, useRef, useState } from "react";
import "./sculpture.css";

type Point = { x: number; y: number; z: number };
type Skill = { id: string; label: string; note: string; orbit: number; phase: number };
const TAU = Math.PI * 2;
const SKILLS: Skill[] = [
  { id: "sql", label: "SQL", note: "Ask structured questions of data. Inspect skill co-mentions and their exact source phrases in the Constellation tool.", orbit: -1, phase: 0 },
  { id: "python", label: "Python", note: "Turn a question into a reproducible workflow. A skill mention is an invitation to inspect its context, not proof of a requirement.", orbit: 0, phase: .1 },
  { id: "excel", label: "Excel", note: "Make analysis inspectable through a familiar interface. The analytical tools separate counted mentions from candidate evidence.", orbit: 0, phase: 1.45 },
  { id: "power-bi", label: "Power BI", note: "Connect models, measures and decisions. Use the actual Constellation table to inspect sample counts and denominators.", orbit: 0, phase: 2.8 },
  { id: "statistics", label: "Statistics", note: "Keep uncertainty visible. Descriptive associations in a selected sample are not causal findings.", orbit: 0, phase: 4.3 },
  { id: "git", label: "Git", note: "Make your process reproducible. Readiness Studio connects self-reported evidence to requirements without predicting a hiring outcome.", orbit: 1, phase: .5 },
  { id: "apis", label: "APIs", note: "Connect authorised sources to reproducible analysis. This sculpture makes no external data requests.", orbit: 1, phase: 1.85 },
  { id: "data-quality", label: "Data quality", note: "Check what is missing before explaining what is present. Coverage and extraction limitations belong beside every result.", orbit: 1, phase: 3.1 },
  { id: "modelling", label: "Modelling", note: "Choose a structure that answers the decision question. Decorative connections here are not calculated associations.", orbit: 1, phase: 4.8 },
  { id: "communication", label: "Communication", note: "Make the reasoning legible. A useful analysis lets another person follow its assumptions, source and limitations.", orbit: 2, phase: .3 },
  { id: "product", label: "Product thinking", note: "Start with the decision. The platform turns analytical methods into tools that can be explored and checked.", orbit: 2, phase: 1.7 },
  { id: "experiments", label: "Experiments", note: "Distinguish a hypothesis from an observed result. Synthetic scenarios demonstrate methods, rather than real career outcomes.", orbit: 2, phase: 3.2 },
  { id: "storytelling", label: "Storytelling", note: "Connect a result to its implication. Inspectable evidence gives a compelling visual an accountable foundation.", orbit: 2, phase: 4.8 },
];

function orbitPoint(orbit: number, phase: number): Point {
  const x = Math.cos(phase) * 191, y = Math.sin(phase) * 191;
  const tilt = [-.43, .88, 1.93][orbit];
  return { x, y: y * Math.cos(tilt), z: y * Math.sin(tilt) };
}

/** Conceptual SVG data art. No coordinates, links or sizes encode market data. */
export default function AnalyticalSculpture({ motionEnabled }: { motionEnabled: boolean }) {
  const container = useRef<HTMLElement>(null);
  const [onScreen, setOnScreen] = useState(true);
  const [pageVisible, setPageVisible] = useState(() => typeof document === "undefined" || !document.hidden);
  const [frame, setFrame] = useState({ angle: -.38, x: 0, y: 0 });
  const current = useRef(frame), target = useRef({ x: 0, y: 0 });
  const [selected, setSelected] = useState("sql");
  const [focusWithin, setFocusWithin] = useState(false);
  const [announcement, setAnnouncement] = useState("");
  const tourRunning = motionEnabled && onScreen && pageVisible;
  function chooseSkill(id: string) {
    setSelected(id);
    const skill = SKILLS.find(skill => skill.id === id)!;
    setAnnouncement(`${skill.label}. ${skill.note}`);
  }
  const unique = useId().replace(/:/g, "");
  const active = motionEnabled && onScreen && pageVisible && !focusWithin;
  useEffect(() => {
    const update = () => setPageVisible(!document.hidden);
    document.addEventListener("visibilitychange", update);
    const observer = typeof IntersectionObserver === "undefined" ? null : new IntersectionObserver(([entry]) => setOnScreen(entry.isIntersecting), { threshold: .05 });
    if (container.current) observer?.observe(container.current);
    return () => { document.removeEventListener("visibilitychange", update); observer?.disconnect(); };
  }, []);
  useEffect(() => {
    if (!active) return;
    let animation = 0, last = 0;
    function tick(time: number) {
      if (!last) last = time;
      const elapsed = time - last;
      if (elapsed >= 1000 / 30) {
        const seconds = Math.min(elapsed, 100) / 1000;
        const previous = current.current;
        const next = { angle: (previous.angle + seconds * .065) % TAU,
          x: previous.x + (target.current.x - previous.x) * .08,
          y: previous.y + (target.current.y - previous.y) * .08 };
        current.current = next;
        setFrame(next);
        last = time;
      }
      animation = requestAnimationFrame(tick);
    }
    animation = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animation);
  }, [active]);

  function project(point: Point) {
    const yaw = frame.angle + frame.x, pitch = -.17 + frame.y;
    const x = point.x * Math.cos(yaw) + point.z * Math.sin(yaw);
    const depth = -point.x * Math.sin(yaw) + point.z * Math.cos(yaw);
    const y = point.y * Math.cos(pitch) - depth * Math.sin(pitch);
    const z = point.y * Math.sin(pitch) + depth * Math.cos(pitch);
    const scale = 660 / (660 - z);
    return { x: 310 + x * scale, y: 242 + y * scale, depth: z, scale };
  }
  const points = SKILLS.map((skill) => ({ ...skill, ...project(skill.orbit < 0 ? { x: 0, y: 0, z: 0 } : orbitPoint(skill.orbit, skill.phase)) }));
  const byId = Object.fromEntries(points.map((point) => [point.id, point]));
  const edges = SKILLS.slice(1).map((skill, index) => [skill.id, index % 3 === 0 ? "sql" : SKILLS[1 + (index + 1) % (SKILLS.length - 1)].id]);
  // Keep the conceptual labels legible while the projected planes rotate.
  const labelPositions = new Map<string, { x: number; y: number }>();
  const boxes = points.map((point) => {
    const radius = point.id === "sql" ? 31 : 12 + 3.5 * point.scale;
    return { x: point.x - radius, y: point.y - radius, w: 2 * radius, h: 2 * radius };
  });
  for (const point of [...points].filter((p) => p.id !== "sql").sort((a, b) =>
    Number(b.id === selected) - Number(a.id === selected) || b.depth - a.depth)) {
    if (labelPositions.size >= 8) break;
    const width = point.label.length * 7.8;
    const candidates = [[point.x, point.y - 26], [point.x, point.y + 32],
      [point.x + 24 + width / 2, point.y + 5], [point.x - 24 - width / 2, point.y + 5]];
    for (const [x, y] of candidates) {
      const box = { x: x - width / 2 - 4, y: y - 16, w: width + 8, h: 22 };
      if (box.x < 14 || box.x + box.w > 606 || y < 70 || y > 422) continue;
      if (boxes.some((b) => box.x < b.x + b.w && box.x + box.w > b.x && box.y < b.y + b.h && box.y + box.h > b.y)) continue;
      boxes.push(box);
      labelPositions.set(point.id, { x, y });
      break;
    }
  }
  return <figure className="analytical-sculpture" ref={container} data-testid="analytical-sculpture" data-angle={frame.angle.toFixed(5)} data-motion={active ? "running" : "paused"}
    onFocusCapture={() => setFocusWithin(true)}
    onBlurCapture={(event) => { if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setFocusWithin(false); }}
    onPointerMove={(event) => {
      if (!active || event.pointerType === "touch") return;
      const bounds = event.currentTarget.getBoundingClientRect();
      target.current = { x: ((event.clientX - bounds.left) / bounds.width - .5) * .36,
        y: ((event.clientY - bounds.top) / bounds.height - .5) * .22 };
    }} onPointerLeave={() => { if (active) target.current = { x: 0, y: 0 }; }}>
    <div className="sculpture-overline"><span>FIG. 01 / A CONNECTED PRACTICE</span></div>
    <svg className="sculpture-canvas" viewBox="0 0 620 490" role="group" aria-label="Illustrative orbital skill sculpture. Select a skill for its analytical perspective. This is not a market graph.">
      <defs><radialGradient id={`${unique}-node`} cx="32%" cy="24%"><stop offset="0" stopColor="#3258d6" /><stop offset="1" stopColor="#2146ed" /></radialGradient></defs>
      <g aria-hidden="true">
        <path d="M42 242H578M310 26V458" className="sculpture-axis" />
        <circle cx="310" cy="242" r="226" className="sculpture-boundary" />
        {[0, 1, 2].map((orbit) => <path key={orbit} className={`sculpture-orbit sculpture-orbit-${orbit}`} d={Array.from({length: 97}, (_, index) => { const point = project(orbitPoint(orbit, index / 96 * TAU)); return `${index === 0 ? "M" : "L"}${point.x.toFixed(2)},${point.y.toFixed(2)}`; }).join(" ")} />)}
        {edges.map(([a, b]) => <line key={`${a}-${b}`} x1={byId[a].x} y1={byId[a].y} x2={byId[b].x} y2={byId[b].y} className={selected === a || selected === b ? "sculpture-link is-selected" : "sculpture-link"} />)}
      </g>
      {[...points].sort((a, b) => a.depth - b.depth).map((point) => {
        const isSelected = selected === point.id;
        const radius = point.id === "sql" ? 23 : 7.5 + 3.5 * point.scale;
        const colour = point.id === "sql" || isSelected ? `url(#${unique}-node)` : point.orbit === 1 ? "#ddf38b" : "var(--sculpture-paper)";
        return <g key={point.id} className={`sculpture-skill${isSelected ? " is-selected" : ""}`} role="button" tabIndex={0} aria-label={`Explore ${point.label}`} aria-pressed={isSelected}
          onClick={() => chooseSkill(point.id)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); chooseSkill(point.id); } }}>
          <circle className="sculpture-hit" cx={point.x} cy={point.y} r="23" />
          {isSelected && <circle cx={point.x} cy={point.y} r={radius + 7} className="sculpture-selection-ring" />}
          <circle cx={point.x} cy={point.y} r={radius} fill={colour} stroke={isSelected || point.id === "sql" ? "#2146ed" : "#25312b"} strokeWidth={isSelected ? 1.5 : 1} />
          {point.id === "sql" ? <text x={point.x} y={point.y + 4.5} className="sculpture-centre-label" textAnchor="middle">SQL</text> : labelPositions.has(point.id) && <text x={labelPositions.get(point.id)!.x} y={labelPositions.get(point.id)!.y} className="sculpture-label" textAnchor="middle" paintOrder="stroke" stroke="var(--sculpture-paper)" strokeWidth="4" strokeLinejoin="round">{point.label}</text>}
        </g>;
      })}
    </svg>
    <figcaption className="sculpture-caption">
      <div className="skill-tour" role="region" aria-label="Analytical skills and their purpose" data-running={tourRunning ? "true" : "false"}>
        <div className="skill-tour-heading">THE SKILLS BEHIND THE WORK</div>
        <div className="skill-tour-window" tabIndex={0} aria-label="Skills and descriptions; scroll to browse when motion is off">
          <div className="skill-tour-track">
            {[false, true].map(copy => <div className={`skill-tour-group${copy ? " skill-tour-copy" : ""}`} key={String(copy)} aria-hidden={copy ? true : undefined}>
              {SKILLS.map((skill, index) => <div className="sculpture-selected" key={skill.id}>
                <span className="sculpture-index">{String(index + 1).padStart(2, "0")}</span><div><strong>{skill.label}</strong><p>{skill.note}</p></div>
              </div>)}
            </div>)}
          </div>
        </div>
      </div>
      <span className="sr-only" role="status">{announcement}</span>
    </figcaption>
  </figure>;
}
