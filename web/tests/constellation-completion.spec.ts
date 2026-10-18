import { test, expect } from "@playwright/test";
import { boundedGraph } from "../src/tools/constellationModel";

test("bounded constellation preserves every endpoint under adversarial density", () => {
  const nodes = Array.from({length: 65}, (_, index) => ({skill_id: `skill-${index}`}));
  const pairs = nodes.flatMap((a, i) => nodes.slice(i + 1).map((b) => ({skill_a: a.skill_id, skill_b: b.skill_id, support: 1})));
  const result = boundedGraph(nodes, pairs, "support", "");
  const ids = new Set(result.nodes.map((node) => node.skill_id));
  expect(result.nodes.length).toBeLessThanOrEqual(40);
  expect(result.edges.length).toBeLessThanOrEqual(80);
  expect(result.edges.every((pair) => ids.has(pair.skill_a) && ids.has(pair.skill_b))).toBe(true);
  const focused = boundedGraph(nodes, pairs, "support", "skill-64");
  expect(focused.edges.every((pair) => [pair.skill_a, pair.skill_b].includes("skill-64"))).toBe(true);
  expect(boundedGraph(nodes, [...pairs].reverse(), "support", "")).toEqual(result);
});

test("constellation search focuses a skill without losing sample disclosure", async ({page}) => {
  await page.goto("/#/constellation");
  await expect(page.getByRole("heading", {name: "Know what this view can support."})).toBeVisible();
  await page.getByLabel("Search skills", {exact: true}).fill("python");
  await expect(page.getByLabel("Focus skill", {exact: true}).locator("option")).toHaveCount(2);
  await page.getByLabel("Focus skill", {exact: true}).selectOption("python");
  await expect(page.locator(".selected-pair")).toContainText("Python");
  await expect(page.getByLabel("Taxonomy category legend")).toContainText("Data");
  await expect(page.getByText("Collection date", {exact: true})).toBeVisible();
});

test("fictional role comparison reconciles denominator changes and exposes exact heatmap counts", async ({page}) => {
  await page.goto("/#/constellation");
  const table = page.getByRole("table", {name: "Accessible role skill heatmap and exact comparison table"});
  await expect(table).toBeVisible();
  await page.getByLabel("Search comparison skills", {exact: true}).fill("sql");
  await expect(table.getByRole("row")).toHaveCount(2);
  await expect(table.getByRole("columnheader", {name: /Data Analyst/})).toContainText("N = 30");
  await expect(table.getByRole("columnheader", {name: /BI Analyst/})).toContainText("N = 30");
  await page.getByLabel("Geography", {exact: true}).selectOption("Rest of Ireland");
  await expect(table.getByRole("columnheader", {name: /BI Analyst/})).toContainText("N = 10; with skill evidence = 9");
  await expect(table.getByRole("columnheader", {name: /Data Analyst/})).toContainText("N = 10");
  await page.getByLabel("Second comparison role", {exact: true}).selectOption("Data Analyst");
  await expect(page.getByText("Choose two different roles to compare their shares.")).toBeVisible();
  await expect(table.getByRole("columnheader")).toHaveCount(2);
});
