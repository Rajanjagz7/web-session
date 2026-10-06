// FLD-AUTH-020 | P1 | Negative
// Preconditions: Logged out
// Expected: The OTP step is not shown and the user stays on /login
import { test, expect } from '@fixtures';
import { AU } from '@testdata/au';

test.describe("FLD-AUTH-020", () => {
  test("FLD-AUTH-020 Whitespace-only mobile does not request an OTP", { tag: ["@P1", "@regression", "@auth"] }, async ({ loginPage, loginModule }) => {
    await test.step("Open the login page", async () => {
      await loginPage.open();
    });
    await test.step("Click the Mobile Number tab", async () => {
      await loginPage.clickMobileTab();
    });
    await test.step("Enter the invalid value and click Send OTP only if it is enabled", async () => {
      await loginModule.trySendIdentifier(AU.mobile.whitespace);
    });
    await test.step("Verify the OTP step is not shown", async () => {
      await loginModule.expectStillOnIdentifierStep();
    });
  });
});
