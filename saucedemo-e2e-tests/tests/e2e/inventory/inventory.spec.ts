import { test, expect } from '../../../fixtures/pages.fixture';
import { products } from '../../../utils/test-data';

test.describe('Inventory', () => {
  test('should add a product to the cart and update the badge @smoke', async ({ loggedInPage }) => {
    await loggedInPage.expectCartCount(0);
    await loggedInPage.addToCart(products.backpack);
    await loggedInPage.expectCartCount(1);
  });

  test('should add multiple products and remove one', async ({ loggedInPage }) => {
    await loggedInPage.addToCart(products.backpack);
    await loggedInPage.addToCart(products.bikeLight);
    await loggedInPage.expectCartCount(2);

    await loggedInPage.removeFromCart(products.backpack);
    await loggedInPage.expectCartCount(1);
  });

  const sortCases = [
    { option: 'az' as const, description: 'name A to Z' },
    { option: 'za' as const, description: 'name Z to A' },
  ];

  for (const { option, description } of sortCases) {
    test(`should sort products by ${description}`, async ({ loggedInPage }) => {
      await loggedInPage.sortBy(option);
      const names = await loggedInPage.getProductNames();
      const sorted = [...names].sort((a, b) =>
        option === 'az' ? a.localeCompare(b) : b.localeCompare(a),
      );
      expect(names).toEqual(sorted);
    });
  }

  test('should sort products by price low to high', async ({ loggedInPage }) => {
    await loggedInPage.sortBy('lohi');
    const prices = await loggedInPage.getProductPrices();
    const sorted = [...prices].sort((a, b) => a - b);
    expect(prices).toEqual(sorted);
  });

  test('should sort products by price high to low', async ({ loggedInPage }) => {
    await loggedInPage.sortBy('hilo');
    const prices = await loggedInPage.getProductPrices();
    const sorted = [...prices].sort((a, b) => b - a);
    expect(prices).toEqual(sorted);
  });
});
