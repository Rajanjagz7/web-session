import { test, expect } from '@fixtures/auth.fixture';
import { products } from '@testdata/users';

test.describe('@P1 @Inventory Inventory', () => {
  test.beforeEach(async ({ authenticatedInventoryPage }) => {
    void authenticatedInventoryPage;
  });

  test('should add a product to the cart and update the badge @Smoke', async ({
    inventoryModule,
  }) => {
    await test.step('Verify cart starts empty', async () => {
      await inventoryModule.verifyCartCount(0);
    });

    await test.step('Add backpack to cart', async () => {
      await inventoryModule.addProductsToCart([products.backpack]);
    });

    await test.step('Verify cart badge shows 1', async () => {
      await inventoryModule.verifyCartCount(1);
    });
  });

  test('should add multiple products and remove one', async ({ inventoryModule }) => {
    await test.step('Add two products', async () => {
      await inventoryModule.addProductsToCart([products.backpack, products.bikeLight]);
      await inventoryModule.verifyCartCount(2);
    });

    await test.step('Remove one product', async () => {
      await inventoryModule.removeProductsFromCart([products.backpack]);
      await inventoryModule.verifyCartCount(1);
    });
  });

  test('should sort products by name A to Z', async ({ inventoryModule }) => {
    const names = await test.step('Sort by name A-Z', async () => {
      return inventoryModule.sortBy('az');
    });

    await test.step('Verify alphabetical order', async () => {
      const sorted = [...names].sort((a, b) => a.localeCompare(b));
      expect(names).toEqual(sorted);
    });
  });

  test('should sort products by price low to high', async ({ inventoryModule }) => {
    const prices = await test.step('Sort by price low-high', async () => {
      return inventoryModule.getSortedPrices('lohi');
    });

    await test.step('Verify ascending price order', async () => {
      const sorted = [...prices].sort((a, b) => a - b);
      expect(prices).toEqual(sorted);
    });
  });
});
