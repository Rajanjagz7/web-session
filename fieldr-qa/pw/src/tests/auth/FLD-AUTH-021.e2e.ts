// FLD-AUTH-021 | P1 | Validation
// Preconditions: Logged out
// Expected: Field value has only digits, spaces, +, ( and )
import { test, expect } from '@fixtures';
import { AU } from '@testdata/au';

test.describe("FLD-AUTH-021", () => {
  test("FLD-AUTH-021 Emoji in the mobile field is not accepted", { tag: ["@P1", "@regression", "@auth"] }, async ({ loginPage }) => {
    await test.step("Open the login page", async () => {
      await loginPage.open();
    });
    await test.step("Click the Mobile Number tab", async () => {
      await loginPage.clickMobileTab();
    });
    await test.step("Type an emoji", async () => {
      await loginPage.identifierInput().pressSequentially(AU.mobile.emoji);
    });
    await test.step("Verify no emoji remains", async () => {
      expect(await loginPage.identifierInput().inputValue()).toMatch(/^[+\d\s()-]*$/);
    });
  });
});
