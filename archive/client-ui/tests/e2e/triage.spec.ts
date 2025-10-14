import { test, expect } from "@playwright/test";

const runE2E = process.env.RUN_E2E === "true";

if (!runE2E) {
  test.describe.configure({ mode: "skip" });
}

test.describe("triage flow", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/dashboard");
  });

  test("shows empty state when no pending actions", async ({ page }) => {
    await expect(page.getByText("No pending actions right now.")).toBeVisible();
  });
});
