import { test, expect } from "@playwright/test";

const runE2E = process.env.RUN_E2E === "true";
const API_BASE =
  process.env.PLAYWRIGHT_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://localhost:8000";

test.describe(runE2E ? "auth submit" : "auth submit (skipped)", () => {
  test.skip(!runE2E, "RUN_E2E is not true");

  test("user can log in and reach dashboard", async ({ page, request }) => {
    const email = "test.user+local@example.com";
    const password = "localpass123!";
    // Seed user via dev endpoint (no-op if already exists)
    await request.post(`${API_BASE.replace(/\/$/, "")}/dev/users`, {
      data: { email, password, name: "Local Test" },
    });

    await page.goto("/login");
    await expect(page.getByLabel("Email")).toBeVisible();
    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(password);
    await page.getByRole("button", { name: "Sign in" }).click();

    await page.waitForURL(/\/(dashboard|$)/, { timeout: 5000 });
    // Either redirected to /dashboard or root (if dashboard not implemented)
    const url = page.url();
    expect(
      url.includes("/dashboard") ||
        url.endsWith(":3000/") ||
        url.endsWith(":3002/")
    ).toBeTruthy();
  });
});
