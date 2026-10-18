/** Geometry only: count-conserving synthetic flows, with no salary inference. */
export type CareerFlow = { origin: string; destination: string; events: number };
export function radialPath(origin: [number, number], destination: [number, number], loop = false) {
  const [x, y] = origin, [u, v] = destination;
  if (loop) return `M${x} ${y} c-35 -45 35 -45 0 0`;
  const length = Math.hypot(u-x, v-y) || 1;
  // The directed normal reverses for B→A, so reciprocal paths remain distinct.
  return `M${x} ${y} Q${400 - (v-y)/length*45} ${280 + (u-x)/length*45} ${u} ${v}`;
}
export function sankeyLayout(flows: CareerFlow[]) {
  const origins = [...new Set(flows.map(f => f.origin))].sort();
  const destinations = [...new Set(flows.map(f => f.destination))].sort();
  const count = Math.max(origins.length, destinations.length, 1);
  const total = flows.reduce((sum, f) => sum + f.events, 0);
  const gap = 16, height = Math.max(500, count * 40 + 40);
  const scale = total ? (height - 40 - (count - 1) * gap) / total : 0;
  const nodes = (names: string[], side: 'origin' | 'destination') => {
    let y = 20;
    return names.map(name => {
      const events = flows.filter(f => f[side] === name).reduce((sum, f) => sum + f.events, 0);
      const node = {name, y, height: events * scale, events};
      y += node.height + gap;
      return node;
    });
  };
  const left = nodes(origins, 'origin'), right = nodes(destinations, 'destination');
  const leftOffset = new Map(left.map(n => [n.name, n.y]));
  const rightOffset = new Map(right.map(n => [n.name, n.y]));
  const links = flows.map(flow => {
    const width = flow.events * scale;
    const sy = leftOffset.get(flow.origin)!, dy = rightOffset.get(flow.destination)!;
    leftOffset.set(flow.origin, sy + width); rightOffset.set(flow.destination, dy + width);
    return {flow, width, sourceY: sy, destinationY: dy,
      path: `M245 ${sy + width/2} C350 ${sy + width/2},450 ${dy + width/2},555 ${dy + width/2}`};
  });
  return {left, right, links, height, scale, total};
}
