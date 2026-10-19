import { test, expect } from '@fixtures/auth.fixture';
import { products } from '@testdata/users';
import type { ShippingInfo } from '@modules/CheckoutModule';

const validShippingInfo: ShippingInfo = {
  firstName: 'Jane',
  lastName: 'Doe',
  postalCode: '2000',
};

test.describe('@P0 @Checkout Checkout', () => {
  test.beforeEach(async ({ authenticatedInventoryPage, inventoryModule, cartModule }) => {
    void authenticatedInventoryPage;
    await test.step('Seed cart and start checkout', async () => {
      await inventoryModule.addProductsToCart([products.backpack, products.boltTShirt]);
      await inventoryModule.goToCart();
      await cartModule.proceedToCheckout();
    });
  });

  test('should complete an order end to end @Smoke', async ({ checkoutModule }) => {
    await test.step('Fill shipping info and continue', async () => {
      await checkoutModule.fillShippingInfo(validShippingInfo);
      await checkoutModule.continueToOverview();
      await checkoutModule.verifyOnOverviewStep();
    });

    const confirmation = await test.step('Finish the order', async () => {
      return checkoutModule.completeOrder();
    });

    await test.step('Verify order confirmation', async () => {
      expect(confirmation).toBe('Thank you for your order!');
    });
  });

  test('should block checkout when first name is missing', async ({ checkoutModule }) => {
    await test.step('Submit with empty first name', async () => {
      await checkoutModule.fillShippingInfo({ ...validShippingInfo, firstName: '' });
      await checkoutModule.continueToOverview();
    });

    await test.step('Verify validation error', async () => {
      await checkoutModule.verifyValidationError('First Name is required');
    });
  });

  test('should block checkout when postal code is missing', async ({ checkoutModule }) => {
    await test.step('Submit with empty postal code', async () => {
      await checkoutModule.fillShippingInfo({ ...validShippingInfo, postalCode: '' });
      await checkoutModule.continueToOverview();
    });

    await test.step('Verify validation error', async () => {
      await checkoutModule.verifyValidationError('Postal Code is required');
    });
  });

  test('should return to the cart when cancelling', async ({ page, checkoutModule }) => {
    await test.step('Cancel checkout', async () => {
      await checkoutModule.cancel();
    });

    await test.step('Verify back on cart page', async () => {
      await expect(page).toHaveURL(/cart\.html/);
    });
  });

  test('should calculate total as subtotal plus tax', async ({ checkoutModule }) => {
    await test.step('Fill shipping info and continue', async () => {
      await checkoutModule.fillShippingInfo(validShippingInfo);
      await checkoutModule.continueToOverview();
    });

    await test.step('Verify totals are consistent', async () => {
      await checkoutModule.verifyTotalsConsistent();
    });
  });
});
