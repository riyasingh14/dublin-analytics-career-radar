import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";

test("project plan hands off to what-if without claiming completed evidence", async ({ page }) => {
  await page.goto("/#/readiness");
  await page.getByRole("button", { name: "Try a synthetic example" }).click();
  await page.getByRole("button", { name: "Extract requirements" }).click();
  for (const skill of ["SQL", "Python", "Excel"]) {
    await page.getByLabel(`Evidence status for ${skill}`, { exact: true }).selectOption("missing");
  }
  await page.getByRole("button", { name: "Assess my evidence" }).click();
  await expect(page.getByText("0 / 100", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Your next evidence action." })).toBeVisible();
  await expect(page.locator(".evidence-weight-bar")).toHaveAccessibleName(/Missing evidence: 7 of 7/);
  const sql = page.locator(".evidence-action").filter({ has: page.getByRole("heading", { name: /Build evidence for SQL/ }) });
  await sql.getByText("Deliverables and completion checks", { exact: true }).click();
  await expect(sql.getByText(/Include a CTE and window calculation/)).toBeVisible();
  await sql.getByText("Trace to 1 source context", { exact: true }).click();
  await expect(sql.locator("blockquote")).toContainText("SQL is required");
  await sql.getByRole("button", { name: "Explore SQL project hypothetically" }).click();
  await expect(page.getByLabel("Planned evidence", { exact: true })).toHaveValue(/joins, CTEs, window functions/);
  await expect(page.getByLabel("Evidence status for SQL", { exact: true })).toHaveValue("missing");
  await expect(page.getByText("0 / 100", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Compare hypothetical evidence" }).click();
  await expect(page.getByRole("heading", { name: "Hypothetical — not completed or verified" })).toBeVisible();
  await expect(page.getByText("42.9 / 100", { exact: true })).toBeVisible();
  await expect(page.getByRole("region", { name: "Submitted baseline comparison", exact: true }).getByText("0 / 100", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Clear all", exact: true }).click();
  await expect(page.locator(".evidence-planner")).toHaveCount(0);
  await expect(page.locator(".evidence-breakdown")).toHaveCount(0);
});

test("unknown evidence is reviewed first and private notes stay out of plans and reports", async ({ page }) => {
  await page.goto("/#/readiness");
  await page.getByLabel("Job description", { exact: true }).fill("SQL is required. Python is preferred.");
  await page.getByRole("button", { name: "Extract requirements" }).click();
  await page.getByLabel("Evidence status for Python", { exact: true }).selectOption("partial");
  await page.getByLabel("Evidence note for Python", { exact: true }).fill("PRIVATE_CANDIDATE_NOTE_DO_NOT_EXPORT");
  await page.getByRole("button", { name: "Assess my evidence" }).click();
  const first = page.locator(".evidence-action").first();
  await expect(first.getByRole("heading")).toHaveText("1. Review your SQL evidence");
  await expect(first.locator(".project-brief")).toHaveCount(0);
  await first.getByRole("button", { name: "Review SQL evidence" }).click();
  await expect(page.getByLabel("Evidence status for SQL", { exact: true })).toBeFocused();
  await expect(page.getByLabel("Evidence status for SQL", { exact: true })).toHaveValue("unknown");
  for (const button of ["Download action plan", "Download analysis"]) {
    const pending = page.waitForEvent("download");
    await page.getByRole("button", { name: button, exact: true }).click();
    const file = await pending;
    const content = await readFile((await file.path())!, "utf8");
    expect(content).not.toContain("PRIVATE_CANDIDATE_NOTE_DO_NOT_EXPORT");
    expect(content).not.toContain("SQL is required");
    expect(content).toContain("evidence-plan-v1");
  }
  await page.getByLabel("Confirm classification for SQL", { exact: true }).selectOption("negated");
  await expect(page.locator(".evidence-planner")).toHaveCount(0);
  await page.getByRole("button", { name: "Assess my evidence" }).click();
  await expect(page.locator(".evidence-action")).toHaveCount(1);
  await expect(page.locator(".evidence-action")).toContainText("Build evidence for Python");
});

test("repeated requirements choose an unresolved context and preserve conservative scoring", async ({ page }) => {
  await page.goto("/#/readiness");
  await page.getByLabel("Job description", { exact: true }).fill("SQL is required. SQL is essential.");
  await page.getByRole("button", { name: "Extract requirements" }).click();
  const statuses = page.getByLabel("Evidence status for SQL", { exact: true });
  await expect(statuses).toHaveCount(2);
  await statuses.nth(0).selectOption("supported");
  await page.getByLabel("Evidence note for SQL", { exact: true }).nth(0).fill("Tested SQL analysis");
  await statuses.nth(1).selectOption("missing");
  await page.getByRole("button", { name: "Assess my evidence" }).click();
  await expect(page.locator(".evidence-action")).toHaveCount(1);
  await page.getByRole("button", { name: "Explore SQL project hypothetically" }).click();
  await page.getByRole("button", { name: "Compare hypothetical evidence" }).click();
  await expect(page.getByText("100 / 100", { exact: true })).toBeVisible();
  await expect(page.getByRole("region", { name: "Submitted baseline comparison", exact: true }).getByText("0 / 100", { exact: true })).toBeVisible();
  await expect(statuses.nth(1)).toHaveValue("missing");
});

test("supported evidence needs no new project and expanded partial-evidence plans fit mobile", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/#/readiness");
  await page.getByLabel("Job description", { exact: true }).fill("SQL is required. Python is preferred.");
  await page.getByRole("button", { name: "Extract requirements" }).click();
  for (const skill of ["SQL", "Python"]) {
    await page.getByLabel(`Evidence status for ${skill}`, { exact: true }).selectOption("supported");
    await page.getByLabel(`Evidence note for ${skill}`, { exact: true }).fill("Tested analysis with a documented decision");
  }
  await page.getByRole("button", { name: "Assess my evidence" }).click();
  await expect(page.locator(".evidence-action")).toHaveCount(0);
  await expect(page.getByText("No new project is suggested from this assessment.", { exact: false })).toBeVisible();
  await page.getByLabel("Evidence status for SQL", { exact: true }).selectOption("partial");
  await expect(page.locator(".evidence-planner")).toHaveCount(0);
  await page.getByRole("button", { name: "Assess my evidence" }).click();
  await expect(page.getByText("62.5 / 100", { exact: true })).toBeVisible();
  await page.getByText("Deliverables and completion checks", { exact: true }).click();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
