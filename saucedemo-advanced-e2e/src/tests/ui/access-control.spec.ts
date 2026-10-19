import { test } from '@fixtures';
import { test as authTest } from '@fixtures/auth.fixture';

const protectedPaths = [
  '/inventory.html',
  '/cart.html',
  '/checkout-step-one.html',
  '/checkout-step-two.html',
  '/checkout-complete.html',
] as const;

test.describe('@P0 @AccessControl Unauthorized access', () => {
  for (const path of protectedPaths) {
    test(`should block direct navigation to ${path} when not logged in`, async ({
      accessControlModule,
    }) => {
      await test.step(`Navigate directly to ${path} without a session`, async () => {
        await accessControlModule.verifyBlockedWhenUnauthenticated(path);
      });
    });
  }
});

authTest.describe('@P0 @AccessControl Post-logout access', () => {
  authTest.beforeEach(async ({ authenticatedInventoryPage }) => {
    void authenticatedInventoryPage;
  });

  authTest(
    'should block access to a protected page after logging out',
    async ({ navModule, accessControlModule }) => {
      await authTest.step('Log out', async () => {
        await navModule.logout();
      });

      await authTest.step('Verify direct navigation is blocked post-logout', async () => {
        await accessControlModule.verifyBlockedWhenUnauthenticated('/inventory.html');
      });
    },
  );
});
