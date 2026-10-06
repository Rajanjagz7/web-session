// FLD-AUTH-034 | P1 | Responsive
// Preconditions: Logged out
// Expected: document scrollWidth <= viewport width; Send OTP inside the viewport
import { test, expect } from '@fixtures';
import { config } from '@config/index';

test.describe("FLD-AUTH-034", () => {
  test("FLD-AUTH-034 Login page has no horizontal scroll at 375x667", { tag: ["@P1", "@regression", "@auth"] }, async ({ loginPage, page }) => {
    await test.step("Set the viewport to 375x667", async () => {
      await page.setViewportSize({ width: 375, height: 667 });
    });
    await test.step("Open the login page", async () => {
      await loginPage.open();
    });
    await test.step("Verify there is no horizontal scroll", async () => {
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    });
    await test.step("Verify Send OTP is visible", async () => {
      await expect(loginPage.sendOtpBtn()).toBeVisible({ timeout: config.timeouts.ui });
    });
  });
});
