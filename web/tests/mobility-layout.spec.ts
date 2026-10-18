import { expect, test } from "@playwright/test";
import { radialPath, sankeyLayout } from "../src/tools/mobilityLayout";

test("Sankey link widths reconcile exactly to both node totals", () => {
  const flows = [{origin:"A",destination:"B",events:30}, {origin:"A",destination:"C",events:10}, {origin:"B",destination:"A",events:20}];
  const layout = sankeyLayout(flows);
  expect(layout.total).toBe(60);
  for (const [nodes, side] of [[layout.left, "origin"], [layout.right, "destination"]] as const) {
    for (const node of nodes) {
      const links = layout.links.filter(link => link.flow[side] === node.name);
      expect(links.reduce((sum, link) => sum + link.width, 0)).toBeCloseTo(node.height, 10);
      expect(node.height / node.events).toBeCloseTo(layout.scale, 10);
    }
  }
  expect(layout.links[0].width / layout.links[1].width).toBeCloseTo(3, 10);
});

test("reciprocal radial paths use different control points and stay deterministic", () => {
  const forward = radialPath([100,100], [600,400]);
  const reverse = radialPath([600,400], [100,100]);
  expect(forward.match(/Q([^ ]+) ([^ ]+)/)?.[0]).not.toBe(reverse.match(/Q([^ ]+) ([^ ]+)/)?.[0]);
  expect(radialPath([100,100], [600,400])).toBe(forward);
  expect(radialPath([100,100], [100,100], true)).toContain(" c");
});
