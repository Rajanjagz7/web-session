import { test, expect } from '../../../fixtures/pages.fixture';

test.describe('Unauthorized access', () => {
  const protectedPaths = [
    '/inventory.html',
    '/cart.html',
    '/checkout-step-one.html',
    '/checkout-step-two.html',
    '/checkout-complete.html',
  ];

  for (const path of protectedPaths) {
    test(`should block direct navigation to ${path} when not logged in`, async ({ page }) => {
      await page.goto(path);
      await expect(page.getByTestId('error')).toContainText(
        `You can only access '${path}' when you are logged in.`,
      );
    });
  }

  test('should block access to a protected page after logging out', async ({
    page,
    loggedInPage,
    navMenu,
  }) => {
    await navMenu.logout();
    await expect(page).toHaveURL('https://www.saucedemo.com/');

    await page.goto('/inventory.html');
    await expect(page.getByTestId('error')).toContainText(
      "You can only access '/inventory.html' when you are logged in.",
    );
  });
});
