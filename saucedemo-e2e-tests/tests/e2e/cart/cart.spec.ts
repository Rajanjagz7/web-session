import { test, expect } from '../../../fixtures/pages.fixture';
import { products } from '../../../utils/test-data';

test.describe('Cart', () => {
  test.beforeEach(async ({ loggedInPage }) => {
    await loggedInPage.addToCart(products.backpack);
    await loggedInPage.addToCart(products.bikeLight);
    await loggedInPage.goToCart();
  });

  test('should list all items added from inventory @smoke', async ({ page, cartPage }) => {
    await expect(page).toHaveURL(/cart\.html/);
    await cartPage.expectItemCount(2);
    await cartPage.expectItemVisible(products.backpack);
    await cartPage.expectItemVisible(products.bikeLight);
  });

  test('should remove an item from the cart', async ({ cartPage }) => {
    await cartPage.removeItem(products.backpack);
    await cartPage.expectItemCount(1);
  });

  test('should proceed to checkout', async ({ page, cartPage }) => {
    await cartPage.checkout();
    await expect(page).toHaveURL(/checkout-step-one\.html/);
  });

  test('should return to inventory unchanged via continue shopping', async ({
    page,
    cartPage,
  }) => {
    await cartPage.continueShoppingButton.click();
    await expect(page).toHaveURL(/inventory\.html/);
  });

  test('should remove all items and show an empty cart', async ({ cartPage }) => {
    await cartPage.removeItem(products.backpack);
    await cartPage.removeItem(products.bikeLight);
    await cartPage.expectItemCount(0);
  });
});
