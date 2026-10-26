import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("data passport explains its purpose and expands by keyboard", async ({ page }) => {
  await page.goto("/");
  const passport = page.locator(".coverage-passport");
  const summary = passport.locator(":scope > summary");
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

test("skill strip loops continuously without local controls or hover pauses", async ({ page }) => {
  await page.goto("/");
  const tour = page.getByRole("region", { name: "Analytical skills and their purpose" });
  await tour.scrollIntoViewIfNeeded();
  await expect(tour).toHaveAttribute("data-running", "true");
  await expect(tour.getByRole("button")).toHaveCount(0);
  await expect(tour.locator(".skill-tour-group").first().locator("strong")).toHaveCount(13);
  const track = tour.locator(".skill-tour-track");
  const before = await track.evaluate(el => getComputedStyle(el).transform);
  await expect.poll(() => track.evaluate(el => getComputedStyle(el).transform)).not.toBe(before);
  await tour.hover();
  await expect(tour).toHaveAttribute("data-running", "true");
  expect(await track.evaluate(el => getComputedStyle(el).animationTimingFunction)).toBe("linear");
  expect(await track.evaluate(el => getComputedStyle(el).animationIterationCount)).toBe("infinite");
  const widths = await tour.locator(".skill-tour-group").evaluateAll(els => els.map(el => el.getBoundingClientRect().width));
  expect(widths[0]).toBeCloseTo(widths[1], 2);
  await page.getByRole("button", { name: "Pause motion", exact: true }).click();
  await expect(tour).toHaveAttribute("data-running", "false");
  expect(await track.evaluate(el => getComputedStyle(el).animationName)).toBe("none");
});

test("reduced motion offers scrollable skills without controls or mobile overflow", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  const tour = page.getByRole("region", { name: "Analytical skills and their purpose" });
  await tour.scrollIntoViewIfNeeded();
  await expect(tour).toHaveAttribute("data-running", "false");
  await expect(tour.getByRole("button")).toHaveCount(0);
  expect(await tour.locator(".skill-tour-track").evaluate(el => getComputedStyle(el).animationName)).toBe("none");
  const window = tour.locator(".skill-tour-window");
  await window.evaluate(el => { el.scrollLeft = 320; });
  expect(await window.evaluate(el => el.scrollLeft)).toBeGreaterThan(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test("passport animates both directions, stays home-only, and the intention is personal", async ({ page }) => {
  await page.goto("/");
  const passport = page.locator(".coverage-passport");
  const summary = passport.locator(":scope > summary");
  const closedHeight = (await passport.boundingBox())!.height;
  await summary.click();
  await expect.poll(() => passport.evaluate(el => el.getAnimations().length)).toBe(0);
  const openHeight = (await passport.boundingBox())!.height;
  expect(openHeight).toBeGreaterThan(closedHeight);
  await summary.click();
  await expect(passport).not.toHaveAttribute("open", "");
  expect((await passport.boundingBox())!.height).toBeCloseTo(closedHeight, 0);
  await expect(page.getByRole("heading", { name: "WHY I BUILT THIS" })).toBeVisible();
  await expect(page.locator(".intention-copy")).toContainText("building a career in business and data analytics");
  await expect(page.getByText("PUBLIC DEMONSTRATION", { exact: true })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Explore the analytical tool", exact: true })).toHaveCount(0);
  for (const route of ["builder", "methodology", "constellation", "readiness", "diagnostic", "mobility"]) {
    await page.goto("/#/" + route);
    await expect(page.locator("main h1")).toBeVisible();
    await expect(passport).toHaveCount(0);
  }
});

test("passport filters icon-led details and explains the chosen parameter", async ({ page }) => {
  await page.goto("/");
  const passport = page.locator(".coverage-passport");
  await passport.locator(":scope > summary").click();
  await expect(passport.locator(".passport-fact")).toHaveCount(9);
  await expect(passport.locator(".passport-fact-icon svg")).toHaveCount(9);
  await passport.getByRole("button", { name: /^Methods & review/ }).click();
  await expect(passport.locator(".passport-fact")).toHaveCount(2);
  const review = passport.locator(".passport-fact").filter({ has: page.getByText("Review status", { exact: true }) });
  await review.locator("summary").click();
  await expect(review.getByText("Passing software tests does not measure extraction accuracy", { exact: false })).toBeVisible();
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
  await passport.getByRole("button", { name: /^Other inputs/ }).click();
  await expect(passport.locator(".passport-fact")).toHaveCount(2);
  await expect(passport.getByText("Description examples", { exact: true })).toBeVisible();
  await passport.getByRole("button", { name: /^All details/ }).click();
  await expect(passport.locator(".passport-fact")).toHaveCount(9);
});
