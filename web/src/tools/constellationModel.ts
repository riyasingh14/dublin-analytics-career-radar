export const CATEGORY_COLOURS: Record<string, string> = {
  Data: "#246b59", BI: "#4756a5", Analytics: "#9c491d", "Engineering Practice": "#63508f",
  "Business Analysis": "#97552e", Product: "#9c3f68", "Data Engineering": "#236b87",
};
export const categoryColour = (category: string) => CATEGORY_COLOURS[category] || "#53656a";

/** Enforce both caps before rendering so no edge can point to a hidden node. */
export function boundedGraph(nodes: any[], pairs: any[], metric: string, focus: string, maxNodes = 40, maxEdges = 80) {
  const candidates = pairs.filter((p) => !focus || [p.skill_a, p.skill_b].includes(focus))
    .sort((a, b) => b[metric] - a[metric] || a.skill_a.localeCompare(b.skill_a) || a.skill_b.localeCompare(b.skill_b));
  const available = new Set(nodes.map((n) => n.skill_id));
  const selected = new Set<string>(), edges: any[] = [];
  for (const pair of candidates) {
    if (!available.has(pair.skill_a) || !available.has(pair.skill_b)) continue;
    const additions = [pair.skill_a, pair.skill_b].filter((id) => !selected.has(id));
    if (selected.size + additions.length > maxNodes) continue;
    additions.forEach((id) => selected.add(id));
    edges.push(pair);
    if (edges.length >= maxEdges) break;
  }
  return { edges, nodes: nodes.filter((n) => selected.has(n.skill_id)) };
}
