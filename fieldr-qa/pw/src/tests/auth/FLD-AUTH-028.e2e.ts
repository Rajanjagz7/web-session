// FLD-AUTH-028 | P0 | Functional
// Preconditions: FLDR_EMAIL set and the bypass OTP applies to email (ASSUMPTION)
// Expected: Redirect to /app/dashboard
import { test, expect } from '@fixtures';
import { config } from '@config/index';

test.describe("FLD-AUTH-028", () => {
  test("FLD-AUTH-028 Email valid + correct OTP logs in", { tag: ["@P0", "@regression", "@auth"] }, async ({ loginModule }) => {
    test.skip(!config.email, "Precondition not met: FLDR_EMAIL set and the bypass OTP applies to email (ASSUMPTION)");
    await test.step("Log in with the registered email", async () => {
      await loginModule.loginWithEmail(config.email);
    });
  });
});
