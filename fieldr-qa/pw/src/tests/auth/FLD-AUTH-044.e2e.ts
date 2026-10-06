// FLD-AUTH-044 | P0 | Security
// Preconditions: Logged in
// Expected: Redirect to /login
import { test, expect } from '@fixtures';
import { config } from '@config/index';

test.describe("FLD-AUTH-044", () => {
  test("FLD-AUTH-044 Deleting all cookies ends the session", { tag: ["@P0", "@regression", "@auth", "@session", "@security"] }, async ({ dashboardPage, page, context, loggedIn }) => {
    await test.step("Clear all cookies", async () => {
      await context.clearCookies();
    });
    await test.step("Open /app/dashboard", async () => {
      await dashboardPage.open();
    });
    await test.step("Verify the URL is /login", async () => {
      await expect(page).toHaveURL(/\/login/, { timeout: config.timeouts.network });
    });
  });
});
