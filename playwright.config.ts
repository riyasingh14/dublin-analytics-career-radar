import { defineConfig } from "@playwright/test";
const deployedURL = process.env.CAREER_RADAR_BASE_URL;
export default defineConfig({
  testDir: "./web/tests",
  timeout: 45000,
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: deployedURL || "http://127.0.0.1:5173",
    actionTimeout: 15000,
    trace: "retain-on-failure",
    launchOptions: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE
      ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE }
      : {},
  },
  webServer: deployedURL ? undefined : [
    {
      command: `${process.env.CAREER_RADAR_PYTHON || ".venv/bin/python"} api/index.py`,
      url: "http://127.0.0.1:8000/api/index?action=health",
      reuseExistingServer: !process.env.CI,
    },
    {
      command: "npm run dev -- --host 127.0.0.1",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: !process.env.CI,
    },
  ],
});
