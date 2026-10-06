// FLD-AUTH-049 | P1 | Security
// Preconditions: Logged out
// Expected: window.__xss stays undefined; no dialog
import { test, expect } from '@fixtures';
import { AU } from '@testdata/au';

test.describe("FLD-AUTH-049", () => {
  test("FLD-AUTH-049 XSS payload in the email field is not executed", { tag: ["@P1", "@regression", "@auth", "@security"] }, async ({ loginPage, loginModule, page }) => {
    await test.step("Open the login page", async () => {
      await loginPage.open();
    });
    await test.step("Click the Email Address tab", async () => {
      await loginPage.clickEmailTab();
    });
    await test.step("Enter the payload and click Send OTP only if it is enabled", async () => {
      await loginModule.trySendIdentifier(AU.email.xss);
    });
    await test.step("Verify the payload did not execute", async () => {
      expect(await page.evaluate(() => (window as unknown as { __xss?: number }).__xss)).toBeUndefined();
    });
  });
});
