import { test, expect } from '@fixtures';
import { fakeStoreUsers } from '@testdata/users';

/**
 * fakestoreapi.com is a mock backend: it echoes back whatever it's sent and
 * does not persist writes. These tests document its ACTUAL behavior around
 * quantity, removal, and stock/delivery -- there is no real inventory or
 * shipping system to validate against. Several "negative" cases here are
 * gap-coverage: they assert the (lack of) validation that exists today, so
 * the suite fails loudly if that behavior ever changes.
 */
test.describe('@P1 @Api Cart quantity & lifecycle', () => {
  const user = fakeStoreUsers[0];

  test.describe('@Positive Adding and removing quantities', () => {
    test('should add a product with quantity 100 to the cart @Smoke', async ({ cartApi }) => {
      const result = await test.step('POST /carts with quantity 100', async () => {
        return cartApi.addToCart(user.userId, [{ productId: 1, quantity: 100 }]);
      });

      await test.step('Verify the cart echoes quantity 100 back', async () => {
        expect(result.status).toBe(201);
        expect(result.body.products[0].quantity).toBe(100);
      });
    });

    test('should remove one product from a cart by omitting it on update', async ({
      cartApi,
    }) => {
      const cart = await test.step('Seed a cart with two products', async () => {
        const result = await cartApi.addToCart(user.userId, [
          { productId: 1, quantity: 2 },
          { productId: 2, quantity: 3 },
        ]);
        return result.body;
      });

      const updated = await test.step('Update the cart without productId 1', async () => {
        const result = await cartApi.updateCart(cart.id, user.userId, [
          { productId: 2, quantity: 3 },
        ]);
        return result.body;
      });

      await test.step('Verify only the remaining product is present', async () => {
        expect(updated.products).toHaveLength(1);
        expect(updated.products[0].productId).toBe(2);
      });
    });

    test('should empty a cart by updating it with an empty products array', async ({
      cartApi,
    }) => {
      const cart = await test.step('Seed a cart with one product', async () => {
        const result = await cartApi.addToCart(user.userId, [{ productId: 1, quantity: 1 }]);
        return result.body;
      });

      const updated = await test.step('Update the cart with products: []', async () => {
        const result = await cartApi.updateCart(cart.id, user.userId, []);
        return result.body;
      });

      await test.step('Verify the cart is empty', async () => {
        expect(updated.products).toHaveLength(0);
      });
    });
  });

  test.describe('@Negative No server-side quantity validation', () => {
    test('should accept a negative quantity with no validation', async ({ cartApi }) => {
      const result = await test.step('POST /carts with quantity -5', async () => {
        return cartApi.addToCart(user.userId, [{ productId: 1, quantity: -5 }]);
      });

      await test.step('Verify the API accepts it unvalidated', async () => {
        expect(result.status).toBe(201);
        expect(result.body.products[0].quantity).toBe(-5);
      });
    });

    test('should accept quantity 0 with no validation', async ({ cartApi }) => {
      const result = await test.step('POST /carts with quantity 0', async () => {
        return cartApi.addToCart(user.userId, [{ productId: 1, quantity: 0 }]);
      });

      await test.step('Verify the API accepts it unvalidated', async () => {
        expect(result.status).toBe(201);
        expect(result.body.products[0].quantity).toBe(0);
      });
    });

    test('should accept an unrealistically large quantity with no upper bound', async ({
      cartApi,
    }) => {
      const hugeQuantity = 999_999_999;
      const result = await test.step(`POST /carts with quantity ${hugeQuantity}`, async () => {
        return cartApi.addToCart(user.userId, [{ productId: 1, quantity: hugeQuantity }]);
      });

      await test.step('Verify the API accepts it unvalidated', async () => {
        expect(result.status).toBe(201);
        expect(result.body.products[0].quantity).toBe(hugeQuantity);
      });
    });

    test('should accept a nonexistent product id with no referential check', async ({
      cartApi,
    }) => {
      const result = await test.step('POST /carts with productId 99999', async () => {
        return cartApi.addToCart(user.userId, [{ productId: 99999, quantity: 1 }]);
      });

      await test.step('Verify the API does not validate productId exists', async () => {
        expect(result.status).toBe(201);
        expect(result.body.products[0].productId).toBe(99999);
      });
    });
  });

  test.describe('@Negative DELETE does not follow REST semantics', () => {
    test('DELETE on a nonexistent cart id returns 200, not 404', async ({ cartApi }) => {
      const result = await test.step('DELETE /carts/999999', async () => {
        return cartApi.deleteCart(999999);
      });

      await test.step('Verify the API returns 200 with a null body instead of 404', async () => {
        expect(result.status).toBe(200);
        expect(result.body).toBeNull();
      });
    });

    test('a cart is still readable after being "deleted" -- writes are not persisted', async ({
      cartApi,
    }) => {
      await test.step('DELETE /carts/1', async () => {
        const result = await cartApi.deleteCart(1);
        expect(result.status).toBe(200);
      });

      await test.step('Verify GET /carts/1 still returns the cart', async () => {
        const result = await cartApi.getCartById(1);
        expect(result.status).toBe(200);
        expect(result.body.id).toBe(1);
      });
    });
  });

  test.describe('@Negative Out of stock / deliverability is unsupported', () => {
    test('product schema has no stock or availability field', async ({ productApi }) => {
      const result = await test.step('GET /products/1', async () => {
        return productApi.getProductById(1);
      });

      await test.step('Verify no stock/availability field exists to represent out-of-stock', async () => {
        expect(result.body).not.toHaveProperty('stock');
        expect(result.body).not.toHaveProperty('availability');
        expect(result.body).not.toHaveProperty('inStock');
      });
    });

    test('product schema has no delivery or shipping field', async ({ productApi }) => {
      const result = await test.step('GET /products/1', async () => {
        return productApi.getProductById(1);
      });

      await test.step('Verify no delivery/shipping field exists to represent non-deliverable', async () => {
        expect(result.body).not.toHaveProperty('deliverable');
        expect(result.body).not.toHaveProperty('shipping');
        expect(result.body).not.toHaveProperty('deliveryZones');
      });
    });
  });
});
