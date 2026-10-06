// FLD-AUTH-041 | P0 | Functional
// Preconditions: Logged in
// Expected: New tab opens /app/dashboard without asking for login
import { test, expect } from '@fixtures';
import { config } from '@config/index';

test.describe("FLD-AUTH-041", () => {
  test("FLD-AUTH-041 Session is shared with a second tab", { tag: ["@P0", "@regression", "@auth", "@session"] }, async ({ context, loggedIn }) => {
    await test.step("Open a second tab", async () => {
      const second = await context.newPage();
    });
    await test.step("Open the dashboard in the second tab", async () => {
      await second.goto('/app/dashboard');
    });
    await test.step("Verify the second tab shows Dashboard", async () => {
      await expect(second.getByRole('heading', { name: 'Dashboard', level: 1 })).toBeVisible({ timeout: config.timeouts.network });
    });
  });
});
