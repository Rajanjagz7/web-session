// FLD-AUTH-033 | P1 | Negative
// Preconditions: Logged out
// Expected: The OTP step is not shown and the user stays on /login
import { test, expect } from '@fixtures';
import { AU } from '@testdata/au';

test.describe("FLD-AUTH-033", () => {
  test("FLD-AUTH-033 Whitespace-only email does not request an OTP", { tag: ["@P1", "@regression", "@auth"] }, async ({ loginPage, loginModule }) => {
    await test.step("Open the login page", async () => {
      await loginPage.open();
    });
    await test.step("Click the Email Address tab", async () => {
      await loginPage.clickEmailTab();
    });
    await test.step("Enter the invalid email and click Send OTP only if it is enabled", async () => {
      await loginModule.trySendIdentifier(AU.email.whitespace);
    });
    await test.step("Verify the OTP step is not shown", async () => {
      await loginModule.expectStillOnIdentifierStep();
    });
  });
});
