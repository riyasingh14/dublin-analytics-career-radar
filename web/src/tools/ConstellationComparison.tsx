import { useState } from "react";
import { Download } from "lucide-react";
import { downloadJSON, format } from "../lib/api";
import { categoryColour } from "./constellationModel";

export default function ConstellationComparison({ comparison }: { comparison: any }) {
  const [left, setLeft] = useState("Data Analyst"), [right, setRight] = useState("BI Analyst"), [query, setQuery] = useState("");
  if (!comparison) return <article className="panel"><h2>Role comparison unavailable</h2><p>The comparison sample has not loaded. The network above remains a separate sample.</p></article>;
  const roles: any[] = comparison.roles || [];
  const selected = [left, right].filter((role, index, all) => roles.some((r) => r.role === role) && all.indexOf(role) === index);
  const rows: any[] = (comparison.skills || []).filter((skill: any) => `${skill.skill_name} ${skill.category}`.toLowerCase().includes(query.toLowerCase()));
  return <article className="panel constellation-comparison">
    <p className="eyebrow">COMPARE LIKE WITH LIKE</p><h2>One skill axis. Separate role samples.</h2>
    <p>Separate fictional comparison sample: 90 examples across three roles before geography filters. These generated differences demonstrate analysis; they are not measured Irish demand. The 30-posting network above is unchanged.</p>
    <div className="filter-bar">
      {[{ label: "First comparison role", value: left, change: setLeft }, { label: "Second comparison role", value: right, change: setRight }].map(({label, value, change}) => <label className="field" key={label}>{label}<select aria-label={label} value={value} onChange={(e) => change(e.target.value)}>{roles.map((role) => <option key={role.role}>{role.role}</option>)}</select></label>)}
      <label className="field">Search comparison skills<input type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Skill or taxonomy category" /></label>
    </div>
    <p className="caption">Geography: {comparison.geography}. Each cell is unique postings mentioning the skill / all unique postings in that role sample. Colour intensity encodes this share. Zero means no match; unavailable means no denominator. The printed counts carry the same information.</p>
    {left === right && <p role="status">Choose two different roles to compare their shares.</p>}
    <div className="table-wrap"><table className="skill-heatmap"><caption>Accessible role skill heatmap and exact comparison table</caption><thead><tr><th scope="col">Skill / category</th>{selected.map((role) => <th scope="col" key={role}>{role}<br /><small>N = {roles.find((r) => r.role === role)?.sample_size}; with skill evidence = {roles.find((r) => r.role === role)?.jobs_with_skills}</small></th>)}{selected.length === 2 && <th scope="col">Share difference<br /><small>First − second, percentage points</small></th>}</tr></thead>
      <tbody>{rows.map((skill) => { const values = selected.map((role) => skill.values.find((value: any) => value.role === role)); return <tr key={skill.skill_id}><th scope="row">{skill.skill_name}<small className="skill-category" style={{color: categoryColour(skill.category)}}>{skill.category}</small></th>{values.map((value: any) => <td key={value.role} style={{backgroundColor: `rgba(36, 107, 89, ${value.share == null ? 0 : .06 + value.share * .25})`}}>{value.sample_size ? `${value.job_count} / ${value.sample_size} · ${format(value.share * 100, 1, "%")}` : "Unavailable · N = 0"}</td>)}{selected.length === 2 && <td>{values.every((value: any) => value.share != null) ? `${format((values[0].share - values[1].share) * 100, 1)} pp` : "Unavailable"}</td>}</tr>; })}</tbody></table></div>
    {!rows.length && <p role="status">No comparison skills match your search.</p>}
    <p className="caption">A zero extraction count does not establish that a skill is unnecessary. The taxonomy and rule coverage limit what can be counted. These are descriptive sample shares without significance or generalisation claims.</p>
    <button className="button-secondary" onClick={() => downloadJSON("fictional-role-skill-comparison.json", { ...comparison, selected_roles: selected, interpretation: "Fictional descriptive comparison, not market evidence; shares use all unique postings in each selected role." })}><Download size={16} />Download role comparison</button>
  </article>;
}
