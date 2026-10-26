import { test, expect } from "@playwright/test";

test("tool opening is centred and lasts two seconds before the page appears", async ({ page }) => {
  const now = new Date();
  await page.clock.install({ time: now });
  await page.clock.pauseAt(now);
  await page.goto("/#/diagnostic");
  const loader = page.getByTestId("tool-opening");
  await expect(loader).toBeVisible();
  const centre = (await page.locator(".tool-loader-centre").boundingBox())!;
  const size = page.viewportSize()!;
  expect(Math.abs(centre.x + centre.width / 2 - size.width / 2)).toBeLessThan(2);
  expect(Math.abs(centre.y + centre.height / 2 - size.height / 2)).toBeLessThan(2);
  await expect(page.locator(".tool-entrance-content")).toHaveAttribute("aria-hidden", "true");
  await expect(page.locator(".tool-entrance-content")).toHaveAttribute("inert", "");
  await page.clock.fastForward(1999);
  await expect(loader).toBeVisible();
  await expect(page.locator(".tool-entrance-content")).toHaveAttribute("aria-hidden", "true");
  await page.clock.fastForward(1);
  await expect(page.getByRole("heading", { name: "Job Description Diagnostic", exact: true })).toBeVisible();
  await page.clock.fastForward(250);
  await expect(loader).toHaveCount(0);
});

test("cached tools repeat the introduction and rapid navigation cancels the previous timer", async ({ page }) => {
  const now = new Date();
  await page.clock.install({ time: now });
  await page.clock.pauseAt(now);
  await page.goto("/#/diagnostic");
  await expect(page.getByTestId("tool-opening")).toBeVisible();
  await page.clock.fastForward(2250);
  await expect(page.getByRole("heading", { name: "Job Description Diagnostic", exact: true })).toBeVisible();
  const nav = page.getByRole("navigation", { name: "Main navigation" });
  await nav.getByRole("link", { name: "Builder", exact: true }).click();
  await expect(page.getByTestId("tool-opening")).toHaveCount(0);
  await nav.getByRole("link", { name: "JD Diagnostic", exact: true }).click();
  await expect(page.getByTestId("tool-opening")).toBeVisible();
  await page.clock.fastForward(1000);
  await nav.getByRole("link", { name: "Skill Constellation", exact: true }).click();
  await expect(page.getByTestId("tool-opening")).toHaveAttribute("aria-label", "Opening Skill Constellation");
  await page.clock.fastForward(1000);
  await expect(page.locator(".tool-entrance-content")).toHaveAttribute("aria-hidden", "true");
  await page.clock.fastForward(1250);
  await expect(page.getByRole("heading", { name: "Skill Constellation", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Job Description Diagnostic", exact: true })).toHaveCount(0);
});

test("reduced-motion opening stays static and reveals a usable tool", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/#/readiness");
  await expect(page.getByTestId("tool-opening")).toBeVisible();
  expect(await page.locator(".tool-loader-orbit").evaluate(element => getComputedStyle(element).animationName)).toBe("none");
  await expect(page.getByRole("heading", { name: "Opportunity Readiness Studio", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Try a synthetic example", exact: true })).toBeEnabled();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
