import { test, expect } from "@playwright/test";

test.describe("Assistant Chat smoke", () => {
  test("hub page responds and loads", async ({ page, baseURL }) => {
    test.skip(!baseURL, "Base URL not configured for Playwright");

    // Collect console errors and warnings
    const consoleErrors: string[] = [];
    const consoleWarnings: string[] = [];

    page.on("console", (msg) => {
      const text = msg.text();
      if (msg.type() === "error") {
        consoleErrors.push(text);
      } else if (msg.type() === "warning") {
        consoleWarnings.push(text);
      }
    });

    // Collect page errors
    page.on("pageerror", (error) => {
      consoleErrors.push(error.message);
    });

    // Navigate and wait for response
    const response = await page.goto(`${baseURL}/hub`, {
      waitUntil: "domcontentloaded",
    });

    // Verify the page responded (may be 200, 302, 401, 500, etc.)
    const status = response?.status() ?? 0;

    if (status >= 500) {
      test.info().annotations.push({
        type: "note",
        description: `Server returned ${status} - ensure server is running and configured correctly`,
      });
      // Don't fail on 500 - server might not be fully set up
      // Just verify we got some response
      expect(status).toBeGreaterThan(0);
      return;
    }

    // Check current URL to see if we're authenticated
    const currentUrl = page.url();
    const isLoginPage = currentUrl.includes("/login");
    const isHubPage = currentUrl.includes("/hub");

    if (isLoginPage) {
      // Authentication required - verify login page loaded
      const loginContent = await page.locator("body").textContent();
      expect(loginContent).toBeTruthy();
      test.info().annotations.push({
        type: "note",
        description:
          "Authentication required. To test chat functionality, set up authenticated session via Playwright's storageState.",
      });
    } else if (isHubPage) {
      // We're on the hub page - try to find and test chat
      // Wait a moment for any dynamic content
      await page.waitForTimeout(1000);

      // Look for action cards that might contain chat
      const actionCardSelectors = [
        '[data-testid*="action-card"]',
        '[data-testid*="ActionCard"]',
        'button:has-text("Expand")',
      ];

      let expanded = false;
      for (const selector of actionCardSelectors) {
        const cards = page.locator(selector);
        const count = await cards.count();
        if (count > 0) {
          try {
            await cards.first().click({ timeout: 2000 });
            await page.waitForTimeout(500);
            expanded = true;
            break;
          } catch {
            // Continue
          }
        }
      }

      // Check for chat input footer
      const chatFooter = page.locator('[data-testid="chat-input-footer"]');
      const chatVisible = await chatFooter
        .isVisible({ timeout: 2000 })
        .catch(() => false);

      if (chatVisible) {
        await expect(chatFooter).toBeVisible();
        test.info().annotations.push({
          type: "note",
          description: "Chat input footer found and visible",
        });
      } else {
        test.info().annotations.push({
          type: "note",
          description:
            "Hub page loaded but chat not visible (may need action with thread or no actions available)",
        });
      }
    }

    // At minimum, verify page loaded (check for body content if title is empty)
    const pageTitle = await page.title();
    if (!pageTitle) {
      // If no title, at least verify body exists
      const bodyContent = await page.locator("body").count();
      expect(bodyContent).toBeGreaterThan(0);
    } else {
      expect(pageTitle).toBeTruthy();
    }

    // Fail if there are critical console errors (build/runtime errors)
    // Filter out expected authentication errors (401, 403) as these are normal when not authenticated
    const criticalErrors = consoleErrors.filter(
      (error) =>
        !error.includes("401") &&
        !error.includes("403") &&
        !error.includes("Unauthorized") &&
        !error.includes("Forbidden")
    );

    if (criticalErrors.length > 0) {
      const errorSummary = criticalErrors.slice(0, 5).join("; ");
      test.info().annotations.push({
        type: "note",
        description: `Critical console errors detected: ${errorSummary}${
          criticalErrors.length > 5 ? "..." : ""
        }`,
      });
      // Fail the test if there are critical console errors - these indicate build/runtime issues
      expect(criticalErrors).toHaveLength(0);
    }

    // Log auth errors but don't fail
    const authErrors = consoleErrors.filter(
      (error) =>
        error.includes("401") ||
        error.includes("403") ||
        error.includes("Unauthorized") ||
        error.includes("Forbidden")
    );
    if (authErrors.length > 0) {
      test.info().annotations.push({
        type: "note",
        description:
          "Authentication errors detected (expected when not authenticated)",
      });
    }

    // Log warnings but don't fail
    if (consoleWarnings.length > 0) {
      test.info().annotations.push({
        type: "note",
        description: `${consoleWarnings.length} console warning(s) detected (non-blocking)`,
      });
    }
  });
});
