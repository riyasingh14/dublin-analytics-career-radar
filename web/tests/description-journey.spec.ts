import { test, expect } from "@playwright/test";

test("a private description moves from Diagnostic to Readiness without storage or URL text", async ({ page }) => {
  const text = "PRIVATE_JOURNEY_MARKER\nData Analyst — Dublin, Ireland. SQL is required. Python is preferred. Permanent role. You will prepare weekly reports.";
  await page.goto("/#/diagnostic");
  await page.getByLabel("Job description", { exact: true }).fill(text);
  await page.getByRole("button", { name: "Analyse description", exact: true }).click();
  await page.getByRole("button", { name: "Assess this role", exact: true }).click();
  await expect(page.getByRole("note", { name: "Description carried from Diagnostic" })).toBeVisible();
  await expect(page.getByLabel("Job description", { exact: true })).toHaveValue(text);
  expect(page.url()).not.toContain("PRIVATE_JOURNEY_MARKER");
  expect(await page.evaluate(() => JSON.stringify({ local: { ...localStorage }, session: { ...sessionStorage } }))).not.toContain("PRIVATE_JOURNEY_MARKER");
  await page.getByRole("button", { name: "Extract requirements", exact: true }).click();
  await expect(page.getByLabel("Evidence status for SQL", { exact: true })).toHaveValue("unknown");
  await expect(page.getByLabel("Evidence status for Python", { exact: true })).toHaveValue("unknown");
  await page.getByRole("button", { name: "Discard carried description", exact: true }).click();
  await expect(page.getByLabel("Job description", { exact: true })).toHaveValue("");
  await expect(page.getByRole("note", { name: "Description carried from Diagnostic" })).toHaveCount(0);
});

test("archived description source and edit provenance survive the handoff", async ({ page }) => {
  await page.goto("/#/diagnostic");
  await page.getByLabel("Real description examples", { exact: true }).selectOption("tts-fedramp-cyber-data-analyst");
  const input = page.getByLabel("Job description", { exact: true });
  const original = await input.inputValue();
  await input.fill(original + "\nUSER_EDIT_IN_MEMORY");
  await page.getByRole("button", { name: "Analyse description", exact: true }).click();
  await page.getByRole("button", { name: "Assess this role", exact: true }).click();
  await expect(page.getByRole("note", { name: "Description source and status" })).toContainText("Edited from the archived source");
  await expect(page.getByLabel("Job description", { exact: true })).toHaveValue(original + "\nUSER_EDIT_IN_MEMORY");
  await page.getByRole("button", { name: "Restore source text", exact: true }).click();
  await expect(page.getByLabel("Job description", { exact: true })).toHaveValue(original);
  await page.getByRole("navigation").getByRole("link", { name: "Overview", exact: true }).click();
  await page.getByRole("navigation").getByRole("link", { name: "Readiness Studio", exact: true }).click();
  await expect(page.getByLabel("Job description", { exact: true })).toHaveValue("");
  await expect(page.getByRole("note", { name: "Description carried from Diagnostic" })).toHaveCount(0);
});
