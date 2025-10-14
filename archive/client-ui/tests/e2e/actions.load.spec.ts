import { test, expect } from "@playwright/test";

const runE2E = process.env.RUN_E2E === "true";
const API_BASE =
  process.env.PLAYWRIGHT_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://localhost:8000";

test.describe(runE2E ? "actions loading" : "actions loading (skipped)", () => {
  test.skip(!runE2E, "RUN_E2E is not true");

  test("loads actions after login and returns 200s (no 401s)", async ({
    page,
    request,
  }) => {
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

    // Arrive at dashboard
    await page.waitForURL(/\/dashboard$/, { timeout: 5000 });

    // Wait for first fetches and assert non-401
    const actionsResp = await page.waitForResponse(
      (resp) =>
        resp.url().includes("/api/actions?") &&
        resp.request().method() === "GET",
      { timeout: 8000 }
    );
    const profileResp = await page.waitForResponse(
      (resp) =>
        resp.url().includes("/api/profile") &&
        resp.request().method() === "GET",
      { timeout: 8000 }
    );
    expect(
      actionsResp.status(),
      `actions status ${actionsResp.status()} body: ${await actionsResp
        .text()
        .catch(() => "")}`
    ).toBeLessThan(400);
    expect(
      profileResp.status(),
      `profile status ${profileResp.status()} body: ${await profileResp
        .text()
        .catch(() => "")}`
    ).toBeLessThan(400);
  });
});
