import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("all analytical routes pass automated WCAG A/AA checks", async ({ page }) => {
  test.setTimeout(120000);
  const issues: unknown[] = [];
  for (const route of ["", "constellation", "readiness", "diagnostic", "mobility", "methodology"]) {
    await page.goto("/#/" + route);
    await expect(page.locator("main h1")).toBeVisible();
    if (route === "constellation") await expect(page.locator(".graph-layout")).toBeVisible();
    if (route === "readiness" || route === "diagnostic") {
      await page.getByRole("button", { name: "Try a synthetic example" }).click();
      await page.getByRole("button", { name: route === "readiness" ? "Extract requirements" : "Analyse description" }).click();
      if (route === "readiness") {
        await page.getByRole("button", { name: "Assess my evidence" }).click();
        await expect(page.locator(".evidence-planner")).toBeVisible();
      } else await expect(page.getByRole("heading", { name: "Clarity starts with specifics." })).toBeVisible();
    }
    if (route === "mobility") await expect(page.locator(".mobility-network")).toBeVisible();
    const review = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
    if (review.violations.length) issues.push({ route, violations: review.violations.map((v) => ({ id: v.id, impact: v.impact,
      nodes: v.nodes.map((n) => ({ target: n.target, summary: n.failureSummary })) })) });
  }
  expect(issues).toEqual([]);
});
