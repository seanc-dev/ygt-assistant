import { defineConfig, devices } from "@playwright/test";

process.env.RUN_E2E ??= "true";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 60_000,
  expect: {
    timeout: 5_000,
  },
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3002",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: "npm run dev -- --hostname 0.0.0.0 --port 3002",
    port: 3002,
    reuseExistingServer: !process.env.CI,
    cwd: __dirname,
    env: {
      RUN_E2E: "true",
      NEXTAUTH_URL: "http://localhost:3002",
      NEXTAUTH_SECRET: process.env.NEXTAUTH_SECRET || "test-secret",
      AUTH_SECRET: process.env.AUTH_SECRET || "test-secret",
      NEXT_PUBLIC_API_BASE_URL:
        process.env.PLAYWRIGHT_API_BASE_URL ||
        process.env.NEXT_PUBLIC_API_BASE_URL ||
        "http://localhost:8000",
    },
  },
});
