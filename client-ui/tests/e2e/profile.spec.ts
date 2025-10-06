import { test, expect } from "@playwright/test";

const runE2E = process.env.RUN_E2E === "true";

if (!runE2E) {
  test.describe.configure({ mode: "skip" });
}

test("profile page shows integrations", async ({ page }) => {
  await page.goto("/profile");
  await expect(page.getByRole("heading", { name: "Integrations" })).toBeVisible();
});
