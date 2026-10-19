import { test, expect } from '@fixtures/auth.fixture';
import { products } from '@testdata/users';

test.describe('@P1 @Cart Cart', () => {
  test.beforeEach(async ({ authenticatedInventoryPage, inventoryModule }) => {
    void authenticatedInventoryPage;
    await test.step('Seed cart with two products', async () => {
      await inventoryModule.addProductsToCart([products.backpack, products.bikeLight]);
      await inventoryModule.goToCart();
    });
  });

  test('should list all items added from inventory @Smoke', async ({ page, cartModule }) => {
    await test.step('Verify on cart page', async () => {
      await expect(page).toHaveURL(/cart\.html/);
    });

    await test.step('Verify both items present', async () => {
      await cartModule.verifyItemCount(2);
      await cartModule.verifyItemPresent(products.backpack);
      await cartModule.verifyItemPresent(products.bikeLight);
    });
  });

  test('should remove an item from the cart', async ({ cartModule }) => {
    await test.step('Remove backpack', async () => {
      await cartModule.removeItems([products.backpack]);
    });

    await test.step('Verify one item remains', async () => {
      await cartModule.verifyItemCount(1);
    });
  });

  test('should proceed to checkout', async ({ cartModule }) => {
    await test.step('Click checkout', async () => {
      await cartModule.proceedToCheckout();
    });
  });

  test('should return to inventory via continue shopping', async ({ cartModule }) => {
    await test.step('Click continue shopping', async () => {
      await cartModule.continueShopping();
    });
  });
});
