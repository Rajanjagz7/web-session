// FLD-AUTH-043 | P0 | Security
// Preconditions: Logged in
// Expected: Redirect to /login
import { test, expect } from '@fixtures';
import { config } from '@config/index';

test.describe("FLD-AUTH-043", () => {
  test("FLD-AUTH-043 Tampered session cookie is rejected on the next request", { tag: ["@P0", "@regression", "@auth", "@session", "@security"] }, async ({ dashboardPage, page, context, loggedIn }) => {
    await test.step("Read all cookies", async () => {
      const cookies = await context.cookies();
    });
    await test.step("Verify a session cookie exists", async () => {
      expect(cookies.length).toBeGreaterThan(0);
    });
    await test.step("Replace every cookie value with a corrupted one", async () => {
      await context.clearCookies();
      await context.addCookies(cookies.map((c) => ({ ...c, value: `${c.value.split('').reverse().join('')}x` })));
    });
    await test.step("Open /app/dashboard", async () => {
      await dashboardPage.open();
    });
    await test.step("Verify the URL is /login", async () => {
      await expect(page).toHaveURL(/\/login/, { timeout: config.timeouts.network });
    });
  });
});
