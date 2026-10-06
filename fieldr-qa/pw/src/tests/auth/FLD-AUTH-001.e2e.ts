// FLD-AUTH-001 | P0 | Security
// Preconditions: No session cookie
// Expected: 302 to /login and the Welcome to Fieldr heading is shown
import { test, expect } from '@fixtures';
import { config } from '@config/index';

test.describe("FLD-AUTH-001", () => {
  test("FLD-AUTH-001 Unauthenticated /app/dashboard redirects to Secure Login", { tag: ["@P0", "@regression", "@auth", "@smoke", "@security"] }, async ({ loginPage, dashboardPage, page }) => {
    await test.step("Open /app/dashboard without a session", async () => {
      await dashboardPage.open();
    });
    await test.step("Verify the URL is /login", async () => {
      await expect(page).toHaveURL(/\/login/, { timeout: config.timeouts.network });
    });
    await test.step("Verify the Welcome to Fieldr heading", async () => {
      await expect(loginPage.heading()).toBeVisible({ timeout: config.timeouts.ui });
    });
  });
});
