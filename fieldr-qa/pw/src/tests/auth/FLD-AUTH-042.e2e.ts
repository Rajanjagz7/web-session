// FLD-AUTH-042 | P0 | Functional
// Preconditions: Logged in
// Expected: Redirect to /login; /app/dashboard redirects to /login again (logout label: NEEDS UI INSPECTION)
import { test, expect } from '@fixtures';
import { config } from '@config/index';

test.describe("FLD-AUTH-042", () => {
  test("FLD-AUTH-042 Logout ends the session", { tag: ["@P0", "@regression", "@auth", "@session"] }, async ({ dashboardPage, loginModule, page, loggedIn }) => {
    await test.step("Log out from the user menu", async () => {
      await loginModule.logout();
    });
    await test.step("Open /app/dashboard", async () => {
      await dashboardPage.open();
    });
    await test.step("Verify the URL is /login", async () => {
      await expect(page).toHaveURL(/\/login/, { timeout: config.timeouts.network });
    });
  });
});
