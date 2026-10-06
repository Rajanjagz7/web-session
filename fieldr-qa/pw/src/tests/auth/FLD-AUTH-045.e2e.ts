// FLD-AUTH-045 | P1 | Security
// Preconditions: Logged in
// Expected: Dashboard content is not shown after Back
import { test, expect } from '@fixtures';
import { config } from '@config/index';

test.describe("FLD-AUTH-045", () => {
  test("FLD-AUTH-045 Back button after logout does not reveal the dashboard", { tag: ["@P1", "@regression", "@auth", "@session", "@security"] }, async ({ loginModule, page, loggedIn }) => {
    await test.step("Log out from the user menu", async () => {
      await loginModule.logout();
    });
    await test.step("Press the browser Back button", async () => {
      await page.goBack();
    });
    await test.step("Verify the dashboard heading is not shown", async () => {
      await expect(page.getByRole('heading', { name: 'Dashboard', level: 1 })).toBeHidden({ timeout: config.timeouts.ui });
    });
  });
});
