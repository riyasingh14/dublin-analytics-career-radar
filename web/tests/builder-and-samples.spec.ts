import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";

test("home sculpture is immersive and Riya’s builder introduction is reachable", async ({ page }) => {
  await page.goto("/");
  const sculpture = page.getByTestId("analytical-sculpture");
  await expect(sculpture).toBeVisible();
  expect(await sculpture.evaluate((el) => getComputedStyle(el).backgroundColor)).toBe("rgba(0, 0, 0, 0)");
  await page.getByRole("link", { name: "Meet Riya", exact: true }).click();
  await expect(page.getByRole("heading", { name: "The human behind the radar." })).toBeInViewport();
  expect(new URL(page.url()).hash).not.toBe("#builder");
  await expect(page.getByRole("link", { name: "Connect on LinkedIn" })).toHaveAttribute("href", "https://www.linkedin.com/in/riya-singh-business-analyst/");
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test("Diagnostic uses a complete real archived description and preserves its provenance after edits", async ({ page }) => {
  await page.goto("/#/diagnostic");
  const library = page.getByLabel("Real description examples", { exact: true });
  await expect(library.locator("option")).toHaveCount(5);
  await library.selectOption("tts-fedramp-cyber-data-analyst");
  const input = page.getByLabel("Job description", { exact: true });
  const original = await input.inputValue();
  expect(original.length).toBeGreaterThan(6000);
  await expect(page.getByRole("note", { name: "Description source and status" })).toContainText("not a current vacancy");
  await expect(page.getByRole("link", { name: "Read the original source" })).toHaveAttribute("href", /github.com\/18F\/join.tts.gsa.gov\/blob\/5dfa66/);
  await input.fill(original + "\nPRIVATE_EDIT_MARKER");
  await expect(page.getByText("Edited from the archived source.", { exact: false })).toBeVisible();
  await page.getByRole("button", { name: "Analyse description" }).click();
  await expect(page.getByRole("heading", { name: "Clarity starts with specifics." })).toBeVisible();
  const pending = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download report", exact: true }).click();
  const download = await pending;
  const content = await readFile((await download.path())!, "utf8");
  const report = JSON.parse(content);
  expect(report.description_source.modified_from_source).toBe(true);
  expect(report.description_source.license).toBe("CC0-1.0");
  expect(content).not.toContain("PRIVATE_EDIT_MARKER");
  await page.getByRole("button", { name: "Restore source text" }).click();
  await expect(input).toHaveValue(original);
  await page.getByRole("button", { name: "Clear all", exact: true }).click();
  await expect(page.getByRole("note", { name: "Description source and status" })).toHaveCount(0);
});

test("Readiness exposes real listing conditions without assuming candidate eligibility", async ({ page }) => {
  await page.goto("/#/readiness");
  await page.getByLabel("Real description examples", { exact: true }).selectOption("tts-fedramp-cyber-data-analyst");
  await page.getByRole("button", { name: "Extract requirements" }).click();
  await expect(page.getByRole("heading", { name: "Conditions to check with the source." })).toBeVisible();
  await expect(page.getByLabel("Your private checklist: Work eligibility or sponsorship", { exact: true }).first()).toHaveValue("unknown");
  await page.getByRole("button", { name: "Clear all", exact: true }).click();
  await expect(page.getByLabel("Job description", { exact: true })).toHaveValue("");
  await expect(page.getByRole("note", { name: "Description source and status" })).toHaveCount(0);
});
