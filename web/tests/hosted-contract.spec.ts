import { test, expect } from "@playwright/test";

// Runs locally in regression CI, and against the explicit HTTPS target in test:deployed.
test("release contract exposes a coherent labelled dataset and a healthy API", async ({ request }) => {
  const health = await request.get("/api/index?action=health");
  expect(health.status()).toBe(200);
  const state = await health.json();
  expect(state.status).toBe("ok");
  const response = await request.get("/api/index?action=bootstrap");
  expect(response.status()).toBe(200);
  expect(response.headers()["cache-control"]).toContain("no-store");
  const data = await response.json();
  expect(["synthetic-demo", "reviewed-sample"]).toContain(data.data_mode);
  expect(state.data_mode).toBe(data.data_mode);
  const identities = new Set(data.snapshot.postings.map((posting: any) => posting.canonical_url));
  expect(identities.size).toBe(data.snapshot.market.sample_size);
  if (data.data_mode === "synthetic-demo") {
    expect(data.snapshot.metadata.data_status).toBe("fixture");
    expect(data.snapshot.metadata.publish_allowed).toBe(false);
    expect(data.release).toBeNull();
  } else {
    expect(data.snapshot.metadata.data_status).toBe("validated");
    expect(data.snapshot.metadata.publish_allowed).toBe(true);
    expect(state.release_id).toBe(data.release.release_id);
    expect(Date.parse(data.release.expires_at)).toBeGreaterThan(Date.now());
    expect(data.snapshot.evaluation.reviewed_count).toBeGreaterThanOrEqual(100);
    expect(data.snapshot.evaluation.precision_pct).toBeGreaterThanOrEqual(90);
    expect(data.release.sources.length).toBeGreaterThan(0);
    expect(data.release).not.toHaveProperty("owner_approved");
  }
  const result = await request.post("/api/index", { data: { action: "constellation" } });
  expect(result.status()).toBe(200);
  const network = await result.json();
  expect(network.sample_size).toBe(identities.size);
  expect(network.data_mode).toBe(data.data_mode);
  expect(network.release?.release_id).toBe(data.release?.release_id);
  if (data.data_mode === "reviewed-sample") expect(network.role_comparison.roles.reduce((sum: number, role: any) => sum + role.sample_size, 0)).toBe(network.sample_size);
});

test("release navigation opens all four tools without browser failures", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", error => errors.push(error.message));
  for (const [route, title] of [["constellation", "Skill Constellation"], ["diagnostic", "Job Description Diagnostic"], ["readiness", "Opportunity Readiness Studio"], ["mobility", "Career Mobility Lab"]]) {
    await page.goto("/#/" + route);
    await expect(page.getByRole("heading", { name: title, exact: true })).toBeVisible();
  }
  expect(errors).toEqual([]);
});
