import { test, expect } from '@fixtures';
import { fakeStoreUsers } from '@testdata/users';

test.describe('@P0 @Api Auth + Cart API', () => {
  test('should log in and receive a JWT token @Smoke', async ({ authApi }) => {
    const user = fakeStoreUsers[0];

    const result = await test.step(`POST /auth/login as ${user.username}`, async () => {
      return authApi.login(user.username, user.password);
    });

    await test.step('Verify token issued', async () => {
      expect(result.status).toBe(201);
      expect(result.body.token).toBeTruthy();
    });
  });

  test('should add a product to the cart with an auth token', async ({ authApi, cartApi }) => {
    const user = fakeStoreUsers[1];

    const token = await test.step('Log in to get a token', async () => {
      const loginResult = await authApi.login(user.username, user.password);
      return loginResult.body.token;
    });

    const cartResult = await test.step('POST /carts with Bearer token', async () => {
      return cartApi.addToCart(user.userId, [{ productId: 1, quantity: 2 }], token);
    });

    await test.step('Verify cart response echoes the request', async () => {
      expect(cartResult.status).toBe(201);
      expect(cartResult.body.userId).toBe(user.userId);
      expect(cartResult.body.products).toHaveLength(1);
      expect(cartResult.body.products[0].productId).toBe(1);
      expect(cartResult.body.products[0].quantity).toBe(2);
    });
  });

  test('should retrieve seeded order history for a user', async ({ cartApi }) => {
    const result = await test.step('GET /carts/user/1', async () => {
      return cartApi.getCartsByUser(1);
    });

    await test.step('Verify at least one historical cart', async () => {
      expect(result.status).toBe(200);
      expect(result.body.length).toBeGreaterThan(0);
      expect(result.body[0]).toHaveProperty('products');
    });
  });
});
