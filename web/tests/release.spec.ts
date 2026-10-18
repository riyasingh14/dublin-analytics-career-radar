import { test, expect } from "@playwright/test";

test("release API is healthy, private and exclusively synthetic", async ({ request }) => {
  const health = await request.get("/api/index?action=health");
  expect(health.status()).toBe(200);
  expect(await health.json()).toMatchObject({ status: "ok", data_mode: "synthetic-demo" });
  expect(health.headers()["cache-control"]).toContain("no-store");

  const response = await request.get("/api/index?action=bootstrap");
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data.data_mode).toBe("synthetic-demo");
  expect(data.snapshot.market.sample_size).toBe(30);
  expect(data.snapshot.postings).toHaveLength(30);
  expect(data.snapshot.postings.every((p: any) =>
    p.canonical_url.startsWith("fixture://") && p.employer_name.startsWith("Fictional"),
  )).toBe(true);
});

test("release API reconciles filters and rejects invalid requests safely", async ({ request }) => {
  const full = await request.post("/api/index", { data: { action: "constellation" } });
  const dublin = await request.post("/api/index", {
    data: { action: "constellation", geography: "Dublin" },
  });
  const rest = await request.post("/api/index", {
    data: { action: "constellation", geography: "Rest of Ireland" },
  });
  for (const response of [full, dublin, rest]) expect(response.status()).toBe(200);
  const [a, b, c] = await Promise.all([full.json(), dublin.json(), rest.json()]);
  expect(a.sample_size).toBe(b.sample_size + c.sample_size);
  expect(c.network_eligible).toBe(false);
  const invalid = await request.post("/api/index", {
    data: { action: "readiness", text: "SQL required.",
      evidence: { forged: { status: "supported", note: "DO_NOT_ECHO_TEST_NOTE" } } },
  });
  expect(invalid.status()).toBe(400);
  expect(await invalid.text()).not.toContain("DO_NOT_ECHO_TEST_NOTE");
});
