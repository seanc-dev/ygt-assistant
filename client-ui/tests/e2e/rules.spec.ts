import { test, expect } from "@playwright/test";

const runE2E = process.env.RUN_E2E === "true";

if (!runE2E) {
  test.describe.configure({ mode: "skip" });
}

test.describe("rules management", () => {
  test("shows new rule button", async ({ page }) => {
    await page.goto("/rules");
    await expect(page.getByRole("button", { name: "New rule" })).toBeVisible();
  });
});
