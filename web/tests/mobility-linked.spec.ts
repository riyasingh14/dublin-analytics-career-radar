import { expect, test } from "@playwright/test";

test("career state selection links graph, exact events and timeline without losing flow context", async ({ page }) => {
  await page.goto("/#/mobility");
  await expect(page.getByText("2,000", { exact: true })).toBeVisible();
  const flowSelector = page.getByLabel("Inspect a flow", { exact: true });
  const optionCount = await flowSelector.locator("option").count();
  expect(optionCount).toBeGreaterThan(20);
  await page.getByRole("button", {name: "Matrix", exact: true}).click();
  const firstCell = page.getByRole("button", {name: /^Inspect .*synthetic events$/}).first();
  const label = await firstCell.getAttribute("aria-label");
  const selectedCount = Number(label?.match(/: (\d+) synthetic events$/)?.[1]);
  await firstCell.click();
  await expect(flowSelector).not.toHaveValue("");
  await expect(page.getByText(`Showing the first ${Math.min(selectedCount, 200)} of ${selectedCount} events`, {exact:false})).toBeVisible();
  await expect(flowSelector.locator("option")).toHaveCount(optionCount);
  const event = page.getByRole("button", {name: /^Inspect timeline /}).first();
  const person = await event.innerText();
  await event.click();
  await expect(page.getByLabel("Person", {exact:true})).toHaveValue(person);
  await page.getByRole("button", {name:"Clear flow selection", exact:true}).click();
  await expect(page.getByText("2,000", {exact:true})).toBeVisible();
});

test("mobility search and experience-period cuts retain an explicit coherent cohort", async ({page}) => {
  await page.goto("/#/mobility");
  await expect(page.getByText("2,000", {exact:true})).toBeVisible();
  await page.getByLabel("Find a career state", {exact:true}).fill("No occupation matches");
  await expect(page.getByText("No career states match this search. Clear it to restore the graph.")).toBeVisible();
  await page.getByLabel("Find a career state", {exact:true}).fill("");
  await page.getByText("Compare within seniority, industry, experience and period", {exact:true}).click();
  await page.getByLabel("From transition year", {exact:true}).fill("2023");
  await page.getByLabel("Through transition year", {exact:true}).fill("2023");
  await expect(page.getByText("Showing the first 200 of 500 events", {exact:false})).toBeVisible();
  const cohort = page.getByRole("heading", {name:"Inspect the transition events."}).locator("..");
  await expect(cohort.getByRole("row")).toHaveCount(201);
  await expect(cohort.getByRole("cell", {name:"2023", exact:true})).toHaveCount(200);
  await page.getByLabel("Origin seniority", {exact:true}).selectOption("Junior");
  await expect(page.getByText("Showing the first 200 of 500 events", {exact:false})).toHaveCount(0);
  await expect(page.getByRole("alert")).toHaveCount(0);
});
