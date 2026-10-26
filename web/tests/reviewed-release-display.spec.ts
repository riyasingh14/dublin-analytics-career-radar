import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";

// UI-contract fixture only. This mock does not create an approved dataset or human review.
const release = {
  release_id: "ui-contract-fixture", dataset_label: "Artificial UI contract sample",
  published_at: "2026-10-26T12:00:00+00:00", collected_from: "2026-10-25T12:00:00+00:00",
  collected_through: "2026-10-26T10:00:00+00:00", expires_at: "2026-11-02T12:00:00+00:00", snapshot_sha256: "test-only",
  sources: [{ source_name: "Artificial UI fixture", homepage_url: "https://fixtures.example.test", terms_url: "https://fixtures.example.test/terms", terms_reviewed_on: "2026-10-24" }],
};

test("approved-mode UI uses its actual roles, release labels and export provenance", async ({ page }) => {
  await page.route("**/api/index*", async route => {
    const response = await route.fetch();
    const data = await response.json();
    const bootstrap = route.request().url().includes("action=bootstrap");
    const constellation = route.request().method() === "POST" && route.request().postDataJSON()?.action === "constellation";
    if (bootstrap || constellation) {
      data.data_mode = "reviewed-sample"; data.release = release;
      if (bootstrap) {
        data.snapshot.metadata.dataset_label = release.dataset_label;
        data.snapshot.evaluation = { reviewed_count: 100, precision_pct: 95 };
        data.snapshot.postings.forEach((posting: any) => { posting.role_name = "Data Engineer"; posting.geography = "Ireland — location unspecified"; });
      } else {
        data.role_comparison = { data_label: release.dataset_label, geography: "All locations", roles: [
          { role: "Data Engineer", sample_size: 20, jobs_with_skills: 20 },
          { role: "QA Engineer", sample_size: 10, jobs_with_skills: 10 },
        ], skills: [] };
      }
    }
    await route.fulfill({ response, json: data });
  });
  await page.goto("/");
  await page.locator(".coverage-passport > summary").click();
  await expect(page.getByText("REVIEWED SAMPLE", { exact: true })).toBeVisible();
  await expect(page.getByText("100 reviewed evidence records · 95% extraction precision", { exact: true })).toBeVisible();
  await page.getByRole("navigation").getByRole("link", { name: "Skill Constellation", exact: true }).click();
  await expect(page.locator(".constellation-coverage")).toContainText(release.release_id);
  await expect(page.getByLabel("Geography", { exact: true }).locator("option")).toHaveCount(2);
  await expect(page.getByLabel("First comparison role", { exact: true })).toHaveValue("Data Engineer");
  await expect(page.getByLabel("Second comparison role", { exact: true })).toHaveValue("QA Engineer");
  await page.getByText("Calculation definitions and complete pair table", { exact: true }).click();
  const file = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download pair metrics", exact: true }).click();
  const download = await file;
  const report = JSON.parse(await readFile((await download.path())!, "utf8"));
  expect(download.suggestedFilename()).toBe("reviewed-skill-pairs.json");
  expect(report.release.release_id).toBe(release.release_id);
});
