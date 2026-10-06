// FLD-AUTH-040 | P0 | Functional
// Preconditions: Logged in
// Expected: Still on /app/dashboard after reload
import { test, expect } from '@fixtures';

test.describe("FLD-AUTH-040", () => {
  test("FLD-AUTH-040 Session survives a page reload", { tag: ["@P0", "@regression", "@auth", "@session"] }, async ({ loginModule, page, loggedIn }) => {
    await test.step("Reload the dashboard", async () => {
      await page.reload();
    });
    await test.step("Verify the dashboard is shown", async () => {
      await loginModule.expectOnDashboard();
    });
  });
});
