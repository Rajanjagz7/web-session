// FLD-AUTH-046 | P1 | Security
// Preconditions: No session cookie
// Expected: Redirect to /login
import { test, expect } from '@fixtures';
import { config } from '@config/index';

test.describe("FLD-AUTH-046", () => {
  test("FLD-AUTH-046 Unauthenticated deep link /app/job/list redirects to login", { tag: ["@P1", "@regression", "@auth", "@security"] }, async ({ dashboardPage, page }) => {
    await test.step("Open /app/job/list without a session", async () => {
      await dashboardPage.openDeepLink('/app/job/list');
    });
    await test.step("Verify the URL is /login", async () => {
      await expect(page).toHaveURL(/\/login/, { timeout: config.timeouts.network });
    });
  });
});
