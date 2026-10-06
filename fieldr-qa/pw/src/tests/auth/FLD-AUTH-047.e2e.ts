// FLD-AUTH-047 | P1 | Flaky
// Preconditions: Logged in
// Expected: Redirect to /login after the idle window
import { test, expect } from '@fixtures';

test.describe("FLD-AUTH-047", () => {
  test("FLD-AUTH-047 Idle session times out", { tag: ["@P1", "@regression", "@auth"] }, async ({  }) => {
    test.fixme(true, "Idle-timeout length not documented; needs PO input and a controllable clock");
    await test.step("Stay idle for the configured window", async () => {
      // Idle timeout duration is unknown (ask PO).
    });
  });
});
