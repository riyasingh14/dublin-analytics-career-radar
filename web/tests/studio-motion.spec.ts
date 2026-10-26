import { test, expect } from "@playwright/test";

test("studio motion can be paused while analytical sculpture remains keyboard usable", async ({ page }) => {
  await page.goto("/");
  const sculpture = page.getByTestId("analytical-sculpture");
  await expect(sculpture).toHaveAttribute("data-motion", "running");
  const angle = await sculpture.getAttribute("data-angle");
  await expect.poll(() => sculpture.getAttribute("data-angle")).not.toBe(angle);
  await page.getByRole("button", { name: "Pause motion", exact: true }).click();
  await expect(sculpture).toHaveAttribute("data-motion", "paused");
  const stopped = await sculpture.getAttribute("data-angle");
  await page.mouse.move(700, 350);
  await page.waitForTimeout(180);
  expect(await sculpture.getAttribute("data-angle")).toBe(stopped);
  const python = sculpture.getByRole("button", { name: "Explore Python", exact: true });
  await python.focus();
  await page.keyboard.press("Enter");
  await expect(python).toHaveAttribute("aria-pressed", "true");
  await expect(sculpture.getByRole("status")).toContainText("Python.");
});

test("system reduced motion stops decorative movement and keeps every tool reachable", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Reduced motion", exact: true })).toBeDisabled();
  await expect(page.getByTestId("analytical-sculpture")).toHaveAttribute("data-motion", "paused");
  const card = page.locator(".tool-card").first();
  await card.hover();
  expect(await card.evaluate((el) => getComputedStyle(el).transform)).toBe("none");
  await card.click();
  await expect(page.getByRole("heading", { name: "Skill Constellation", exact: true })).toBeVisible();
});

test("mouse movement adds bounded depth to editorial tool cards", async ({ page }) => {
  await page.goto("/");
  const card = page.locator(".tool-card").first();
  await card.scrollIntoViewIfNeeded();
  const box = (await card.boundingBox())!;
  await page.mouse.move(box.x + box.width * .8, box.y + box.height * .3);
  await expect.poll(() => card.evaluate((el) => el.style.transform)).not.toBe("");
  await page.getByRole("button", { name: "Pause motion", exact: true }).click();
  expect(await card.evaluate((el) => el.style.transform)).toBe("");
});
