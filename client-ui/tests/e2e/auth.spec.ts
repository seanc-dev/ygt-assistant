import { test, expect } from "@playwright/test";

const runE2E = process.env.RUN_E2E === "true";

if (!runE2E) {
  test.describe.configure({ mode: "skip" });
}

test("user can view login form", async ({ page }) => {
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: "Welcome back" })).toBeVisible();
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByLabel("Password")).toBeVisible();
});

test("user can view register form", async ({ page }) => {
  await page.goto("/register");
  await expect(page.getByRole("heading", { name: "Create an account" })).toBeVisible();
});
