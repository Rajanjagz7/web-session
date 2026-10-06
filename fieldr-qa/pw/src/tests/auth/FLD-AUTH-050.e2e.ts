// FLD-AUTH-050 | P1 | Security
// Preconditions: Logged out
// Expected: No 5xx response; OTP step not shown
import { test, expect } from '@fixtures';
import { AU } from '@testdata/au';

test.describe("FLD-AUTH-050", () => {
  test("FLD-AUTH-050 SQL-injection payload in the email field causes no server error", { tag: ["@P1", "@regression", "@auth", "@security"] }, async ({ loginPage, loginModule, page }) => {
    await test.step("Open the login page", async () => {
      await loginPage.open();
    });
    await test.step("Click the Email Address tab", async () => {
      await loginPage.clickEmailTab();
    });
    await test.step("Collect server errors", async () => {
      const serverErrors: number[] = [];
      page.on('response', (r) => { if (r.status() >= 500) serverErrors.push(r.status()); });
    });
    await test.step("Enter the payload and click Send OTP only if it is enabled", async () => {
      await loginModule.trySendIdentifier(AU.email.sqli);
    });
    await test.step("Verify no 5xx occurred", async () => {
      expect(serverErrors).toEqual([]);
    });
    await test.step("Verify the OTP step is not shown", async () => {
      await loginModule.expectStillOnIdentifierStep();
    });
  });
});
