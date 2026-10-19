import { test, expect } from '../../../fixtures/pages.fixture';
import { products, checkoutInfo } from '../../../utils/test-data';

test.describe('Checkout', () => {
  test.beforeEach(async ({ loggedInPage, cartPage }) => {
    await loggedInPage.addToCart(products.backpack);
    await loggedInPage.addToCart(products.boltTShirt);
    await loggedInPage.goToCart();
    await cartPage.checkout();
  });

  test('should complete an order end to end @smoke @critical', async ({
    page,
    checkoutPage,
  }) => {
    const info = checkoutInfo();
    await checkoutPage.fillInformation(info.firstName, info.lastName, info.postalCode);
    await checkoutPage.continueToOverview();

    await expect(page).toHaveURL(/checkout-step-two\.html/);
    await expect(checkoutPage.totalLabel).toBeVisible();

    await checkoutPage.finish();

    await expect(page).toHaveURL(/checkout-complete\.html/);
    await checkoutPage.expectOrderComplete();
  });

  test('should block checkout when first name is missing', async ({ checkoutPage }) => {
    const info = checkoutInfo();
    await checkoutPage.fillInformation('', info.lastName, info.postalCode);
    await checkoutPage.continueToOverview();
    await checkoutPage.expectErrorMessage('First Name is required');
  });

  test('should block checkout when postal code is missing', async ({ checkoutPage }) => {
    const info = checkoutInfo();
    await checkoutPage.fillInformation(info.firstName, info.lastName, '');
    await checkoutPage.continueToOverview();
    await checkoutPage.expectErrorMessage('Postal Code is required');
  });

  test('should block checkout when last name is missing', async ({ checkoutPage }) => {
    const info = checkoutInfo();
    await checkoutPage.fillInformation(info.firstName, '', info.postalCode);
    await checkoutPage.continueToOverview();
    await checkoutPage.expectErrorMessage('Last Name is required');
  });

  test('should block checkout when all fields are empty', async ({ checkoutPage }) => {
    await checkoutPage.continueToOverview();
    await checkoutPage.expectErrorMessage('First Name is required');
  });

  test('should not advance to the overview step on validation failure', async ({
    page,
    checkoutPage,
  }) => {
    await checkoutPage.continueToOverview();
    await expect(page).toHaveURL(/checkout-step-one\.html/);
    await expect(page).not.toHaveURL(/checkout-step-two\.html/);
  });

  test('should return to the cart when cancelling step one', async ({ page, checkoutPage }) => {
    await checkoutPage.cancel();
    await expect(page).toHaveURL(/cart\.html/);
  });

  test('should return to inventory when cancelling step two', async ({ page, checkoutPage }) => {
    const info = checkoutInfo();
    await checkoutPage.fillInformation(info.firstName, info.lastName, info.postalCode);
    await checkoutPage.continueToOverview();
    await checkoutPage.cancel();
    await expect(page).toHaveURL(/inventory\.html/);
  });

  test('should calculate total as subtotal plus tax', async ({ checkoutPage }) => {
    const info = checkoutInfo();
    await checkoutPage.fillInformation(info.firstName, info.lastName, info.postalCode);
    await checkoutPage.continueToOverview();

    const subtotalText = await checkoutPage.subtotalLabel.textContent();
    const taxText = await checkoutPage.taxLabel.textContent();
    const totalText = await checkoutPage.totalLabel.textContent();

    const subtotal = parseFloat(subtotalText!.replace(/[^0-9.]/g, ''));
    const tax = parseFloat(taxText!.replace(/[^0-9.]/g, ''));
    const total = parseFloat(totalText!.replace(/[^0-9.]/g, ''));

    expect(total).toBeCloseTo(subtotal + tax, 2);
  });
});
