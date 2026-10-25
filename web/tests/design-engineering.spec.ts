import { test, expect } from "@playwright/test";

test("keyboard navigation stays instant and mobile Escape returns focus to the menu", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  const menu = page.getByRole("button", { name: "Toggle navigation" });
  await menu.focus();
  await page.keyboard.press("Enter");
  await expect(menu).toHaveAttribute("aria-expanded", "true");
  await page.getByRole("navigation", { name: "Main navigation" }).getByRole("link", { name: "JD Diagnostic", exact: true }).focus();
  await page.keyboard.press("Escape");
  await expect(menu).toHaveAttribute("aria-expanded", "false");
  await expect(menu).toBeFocused();
  await page.keyboard.press("Enter");
  const link = page.getByRole("navigation").getByRole("link", { name: "JD Diagnostic", exact: true });
  await link.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: "Job Description Diagnostic", exact: true })).toBeVisible();
  expect(await page.locator(".tool-page").evaluate(el => getComputedStyle(el).animationName)).toBe("none");
  expect(await page.getByRole("button", { name: "Analyse description", exact: true }).evaluate(el => getComputedStyle(el).transitionDuration)).toBe("0s");
});

test("description work announces progress and the pause control also stops its indicator", async ({ page }) => {
  let release!: () => void;
  const held = new Promise<void>(resolve => { release = resolve; });
  await page.route("**/api/index", async route => {
    if (route.request().postDataJSON()?.action === "diagnostic") await held;
    await route.continue();
  });
  await page.goto("/#/diagnostic");
  await page.getByRole("button", { name: "Try a synthetic example" }).click();
  await page.getByRole("button", { name: "Analyse description", exact: true }).click();
  await expect(page.locator(".tool-status")).toContainText("Analysing the description");
  await expect(page.getByRole("button", { name: "Analysing…", exact: false })).toBeDisabled();
  const indicator = page.locator(".work-indicator");
  expect(await indicator.evaluate(el => getComputedStyle(el).animationName)).toBe("working");
  await page.getByRole("button", { name: "Pause motion", exact: true }).click();
  expect(await indicator.evaluate(el => getComputedStyle(el).animationName)).toBe("none");
  release();
  await expect(page.getByRole("heading", { name: "Clarity starts with specifics." })).toBeVisible();
  await expect(page.locator(".tool-status")).toBeEmpty();
  await page.getByRole("button", { name: "Analyse description", exact: true }).focus();
  await expect(page.getByRole("button", { name: "Analyse description", exact: true })).toBeEnabled();
});

test("touch does not tilt cards and description inputs avoid mobile focus zoom", async ({ browser }) => {
  const context = await browser.newContext({ hasTouch: true, isMobile: true, viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  await page.goto("/");
  const card = page.locator(".tool-card").first();
  await card.scrollIntoViewIfNeeded();
  const box = (await card.boundingBox())!;
  await page.mouse.move(box.x + box.width * .8, box.y + box.height * .3);
  expect(await card.evaluate(el => getComputedStyle(el).transform)).toBe("none");
  await page.goto("/#/readiness");
  const input = page.getByLabel("Job description", { exact: true });
  await expect(input).toBeVisible();
  expect(await input.evaluate(el => parseFloat(getComputedStyle(el).fontSize))).toBeGreaterThanOrEqual(16);
  await context.close();
});
