import { test, expect } from "@playwright/test";

test("home explains the four tools with distinct colours, audiences and useful outcomes", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("BASED IN DUBLIN, IRELAND", { exact: true })).toBeVisible();
  const cards = page.locator(".tool-card");
  await expect(cards).toHaveCount(4);
  const colours = await cards.evaluateAll(elements => elements.map(element => getComputedStyle(element).backgroundColor));
  expect(new Set(colours).size).toBe(4);
  for (let index = 0; index < 4; index++) {
    const card = cards.nth(index);
    await expect(card.locator(".tool-audience")).not.toBeEmpty();
    await expect(card.locator(".tool-takeaway")).toContainText("WHAT YOU GET");
    await expect(card.locator(".tool-craft")).toContainText("HOW IT WORKS");
  }
  await expect(cards.nth(2)).toContainText("Synthetic scenarios");
  await page.screenshot({ path: test.info().outputPath("colourful-home.png"), fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: test.info().outputPath("colourful-home-mobile.png"), fullPage: true });
});

test("tool disclosures share interruptible motion and keyboard toggles remain immediate", async ({ page }) => {
  await page.goto("/#/mobility");
  const details = page.locator("details").first();
  const summary = details.locator(":scope > summary");
  await expect(summary).toBeVisible();
  const opening = await summary.evaluate(element => {
    element.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, detail: 1 }));
    return element.parentElement!.getAnimations().some(animation => animation.effect?.getKeyframes().some(frame => "height" in frame));
  });
  expect(opening).toBe(true);
  // Reverse while the opening animation is still running.
  await summary.click();
  await expect(details).not.toHaveAttribute("open", "");
  await summary.focus();
  await page.keyboard.press("Enter");
  await expect(details).toHaveAttribute("open", "");
  expect(await details.evaluate(element => element.getAnimations().length)).toBe(0);
});

test("page entrances are brief and reduced motion has no entrance animations", async ({ page }) => {
  await page.goto("/#/builder");
  await expect(page.locator(".builder-page-hero")).toBeVisible();
  const duration = await page.locator(".builder-page-hero").evaluate(element => element.getAnimations().map(animation => Number(animation.effect?.getTiming().duration)));
  expect(duration.every(value => value <= 300)).toBe(true);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/#/methodology");
  await expect(page.locator("main h1")).toBeVisible();
  expect(await page.locator("main").evaluate(element => element.getAnimations({ subtree: true }).filter(animation => animation.playState === "running").length)).toBe(0);
});

test("hero mesh has equal peer connections and cards track cursor light", async ({ page }) => {
  await page.goto("/");
  const sculpture = page.getByTestId("analytical-sculpture");
  const mesh = await sculpture.locator("line[data-skill-a]").evaluateAll(lines => {
    const degrees: Record<string, number> = {};
    for (const line of lines) for (const key of ["data-skill-a", "data-skill-b"]) {
      const id = line.getAttribute(key)!;
      degrees[id] = (degrees[id] || 0) + 1;
    }
    return degrees;
  });
  expect(Object.keys(mesh)).toHaveLength(13);
  expect(new Set(Object.values(mesh))).toEqual(new Set([4]));
  await expect(sculpture.locator('[aria-pressed="true"]')).toHaveCount(0);
  const sql = sculpture.locator('.sculpture-node[data-skill-id="sql"]');
  const cx = Number(await sql.getAttribute("cx")), cy = Number(await sql.getAttribute("cy"));
  expect(Math.hypot(cx - 310, cy - 242)).toBeGreaterThan(40);
  await expect(page.getByRole("heading", { name: "Our four tools.", exact: true })).toBeVisible();
  const card = page.locator(".tool-card").first();
  await card.scrollIntoViewIfNeeded();
  const box = (await card.boundingBox())!;
  await page.mouse.move(box.x + box.width * .3, box.y + box.height * .4);
  const light = card.locator(".card-spotlight");
  await expect.poll(() => light.evaluate(element => element.style.opacity)).toBe("1");
  const initial = await light.evaluate(element => element.style.transform);
  await page.mouse.move(box.x + box.width * .7, box.y + box.height * .6);
  await expect.poll(() => light.evaluate(element => element.style.transform)).not.toBe(initial);
  await page.getByRole("button", { name: "Pause motion", exact: true }).click();
  expect(await light.evaluate(element => element.style.opacity)).toBe("");
});
