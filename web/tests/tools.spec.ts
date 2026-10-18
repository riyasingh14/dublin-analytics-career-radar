import { test, expect } from "@playwright/test";

test("landing navigates to all four tools and labels public data", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Evidence for your next career move." }),
  ).toBeVisible();
  await expect(
    page.getByText("30 fictional postings", { exact: true }),
  ).toBeVisible();
  for (const [route, title] of [
    ["constellation", "Skill Constellation"],
    ["readiness", "Opportunity Readiness Studio"],
    ["mobility", "Career Mobility Lab"],
    ["diagnostic", "Job Description Diagnostic"],
  ]) {
    await page.goto("/#/" + route);
    await expect(
      page.getByRole("heading", { name: title, exact: true }),
    ).toBeVisible();
  }
  expect(errors).toEqual([]);
});

test("constellation recomputes a sparse geography and exports labelled metrics", async ({
  page,
}) => {
  await page.goto("/#/constellation");
  await expect(page.getByText("30", { exact: true }).first()).toBeVisible();
  await page
    .getByLabel("Geography", { exact: true })
    .selectOption("Rest of Ireland");
  await expect(
    page.getByText("A little more evidence is needed."),
  ).toBeVisible();
  await expect(
    page.getByText("This selection has 10.", { exact: false }),
  ).toBeVisible();
  await page
    .getByText("Calculation definitions and complete pair table")
    .click();
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download pair metrics" }).click();
  expect((await download).suggestedFilename()).toBe(
    "synthetic-skill-pairs.json",
  );
});

test("diagnostic analyses, reviews, clears and retains no rendered report", async ({
  page,
}) => {
  await page.goto("/#/diagnostic");
  await page.getByRole("button", { name: "Try a synthetic example" }).click();
  await page.getByRole("button", { name: "Analyse description" }).click();
  await expect(
    page.getByRole("heading", { name: "Clarity starts with specifics." }),
  ).toBeVisible();
  await expect(
    page.getByRole("cell", { name: "SQL", exact: true }).first(),
  ).toBeVisible();
  await page.getByRole("button", { name: "Clear all", exact: true }).click();
  await expect(page.getByLabel("Job description", { exact: true })).toHaveValue(
    "",
  );
  await expect(
    page.getByRole("heading", { name: "Clarity starts with specifics." }),
  ).toHaveCount(0);
});

test("readiness needs evidence, keeps scenario separate and clears notes", async ({
  page,
}) => {
  await page.goto("/#/readiness");
  await page.getByRole("button", { name: "Try a synthetic example" }).click();
  await page.getByRole("button", { name: "Extract requirements" }).click();
  await expect(
    page.getByRole("heading", {
      name: "Review the requirement. Add your evidence.",
    }),
  ).toBeVisible();
  for (const label of ["SQL", "Python", "Excel"]) {
    await page
      .getByLabel("Evidence status for " + label, { exact: true })
      .selectOption("supported");
    await page
      .getByLabel("Evidence note for " + label, { exact: true })
      .fill("Coursework project with tested outputs");
  }
  await page.getByRole("button", { name: "Assess my evidence" }).click();
  await expect(page.getByText("100 / 100", { exact: true })).toBeVisible();
  await page
    .getByLabel("Evidence status for SQL", { exact: true })
    .selectOption("missing");
  await page.getByRole("button", { name: "Assess my evidence" }).click();
  await page
    .getByLabel("Requirement to explore")
    .selectOption({ label: "SQL · required" });
  await page
    .getByLabel("Planned evidence", { exact: true })
    .fill("Build a tested SQL analysis");
  await page
    .getByRole("button", { name: "Compare hypothetical evidence" })
    .click();
  await expect(
    page.getByRole("heading", {
      name: "Hypothetical — not completed or verified",
    }),
  ).toBeVisible();
  await expect(
    page.getByText("Your submitted evidence is unchanged.", { exact: false }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Clear all", exact: true }).click();
  await expect(page.getByLabel("Job description", { exact: true })).toHaveValue(
    "",
  );
  await expect(
    page.getByRole("heading", { name: "Evidence you can explain." }),
  ).toHaveCount(0);
});

test("mobility renders synthetic flows, switches views and filters empty cohorts safely", async ({
  page,
}) => {
  await page.goto("/#/mobility");
  await expect(page.getByText("2,000", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Flow", exact: true }).click();
  await expect(
    page.getByRole("img", {
      name: "Synthetic origin to destination flows, widths indicate event counts",
    }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Matrix", exact: true }).click();
  await expect(
    page.getByText("Synthetic transition counts · all filtered flows", {
      exact: true,
    }),
  ).toBeVisible();
  await page
    .getByLabel("Origin occupation", { exact: true })
    .selectOption("Data Analyst");
  await expect(page.getByText("2,000", { exact: true })).toHaveCount(0);
  await expect(page.getByText("CAREER MOVES", { exact: true })).toHaveCount(0);
});

test("mobile navigation and layouts do not overflow the viewport", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByRole("button", { name: "Toggle navigation" }).click();
  await page
    .getByRole("navigation")
    .getByRole("link", { name: "JD Diagnostic", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Job Description Diagnostic" }),
  ).toBeVisible();
  for (const route of [
    "",
    "constellation",
    "readiness",
    "mobility",
    "diagnostic",
  ]) {
    await page.goto("/#/" + route);
    await page.waitForTimeout(200);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      route,
    ).toBeTruthy();
  }
});

test("invalid mobility parameters show an error without stale scenario results", async ({
  page,
}) => {
  await page.goto("/#/mobility");
  await expect(page.getByText("2,000", { exact: true })).toBeVisible();
  await page
    .getByText("Scenario controls and generator assumptions", { exact: true })
    .click();
  await page.getByLabel("Seed", { exact: true }).fill("-1");
  await page.getByRole("button", { name: "Apply scenario" }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page.getByText("2,000", { exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Reset baseline" }).click();
  await expect(page.getByText("2,000", { exact: true })).toBeVisible();
});
