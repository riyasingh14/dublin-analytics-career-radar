import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("data passport explains its purpose and expands by keyboard", async ({ page }) => {
  await page.goto("/");
  const passport = page.locator(".coverage-passport");
  const summary = passport.locator("summary");
  await expect(summary).toContainText("sources, sample sizes and limits");
  await expect(summary.getByText("View data details", { exact: true })).toBeVisible();
  await expect(passport.locator(".passport-content")).not.toBeVisible();
  await summary.focus();
  await page.keyboard.press("Enter");
  await expect(passport).toHaveAttribute("open", "");
  await expect(summary.getByText("Hide data details", { exact: true })).toBeVisible();
  await expect(passport.getByText("Collection window", { exact: true })).toBeVisible();
  await expect(passport.getByText("Not applicable — generated, not collected", { exact: true })).toBeVisible();
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
  await page.keyboard.press("Enter");
  await expect(passport.locator(".passport-content")).not.toBeVisible();
});

test("skill tour advances horizontally, pauses for reading, and follows node selection", async ({ page }) => {
  await page.clock.install();
  await page.goto("/");
  const tour = page.getByRole("region", { name: "Analytical skills and their purpose" });
  await tour.scrollIntoViewIfNeeded();
  await page.mouse.move(0, 0);
  await expect(tour).toHaveAttribute("data-running", "true");
  const current = tour.locator('.sculpture-selected[aria-hidden="false"] strong');
  await expect(current).toHaveText("SQL");
  await page.clock.fastForward(7100);
  await expect(current).toHaveText("Python");
  expect(await tour.locator(".skill-tour-track").evaluate(el => el.getAttribute("style"))).toContain("translateX(-100%)");
  await tour.hover();
  await expect(tour).toHaveAttribute("data-running", "false");
  await page.clock.fastForward(14000);
  await expect(current).toHaveText("Python");
  await tour.getByRole("button", { name: "Next skill", exact: true }).click();
  await expect(current).toHaveText("Excel");
  await page.getByRole("button", { name: "Explore Git", exact: true }).focus();
  await page.keyboard.press("Enter");
  await expect(current).toHaveText("Git");
  await expect(tour.getByRole("button", { name: "Play skill tour", exact: true })).toBeVisible();
});

test("reduced motion keeps the skill tour manual and the passport fits mobile", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  const tour = page.getByRole("region", { name: "Analytical skills and their purpose" });
  await tour.scrollIntoViewIfNeeded();
  await expect(tour).toHaveAttribute("data-running", "false");
  await expect(tour.getByText("Motion paused. Use the arrows to explore.")).toBeVisible();
  await tour.getByRole("button", { name: "Next skill", exact: true }).click();
  await expect(tour.locator('.sculpture-selected[aria-hidden="false"] strong')).toHaveText("Python");
  expect(await tour.locator(".skill-tour-track").evaluate(el => getComputedStyle(el).transitionDuration)).toBe("0s");
  await page.locator(".coverage-passport summary").click();
  await expect(page.locator(".passport-content")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
