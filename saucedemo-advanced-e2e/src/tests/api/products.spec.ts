import { test, expect } from '@fixtures';

test.describe('@P1 @Api Products API', () => {
  test('should return a list of products @Smoke', async ({ productApi }) => {
    const result = await test.step('GET /products', async () => {
      return productApi.getProducts();
    });

    await test.step('Verify response', async () => {
      expect(result.status).toBe(200);
      expect(result.body.length).toBeGreaterThan(0);
      expect(result.body[0]).toHaveProperty('id');
      expect(result.body[0]).toHaveProperty('price');
    });
  });

  test('should return a single product by id', async ({ productApi }) => {
    const result = await test.step('GET /products/1', async () => {
      return productApi.getProductById(1);
    });

    await test.step('Verify product details', async () => {
      expect(result.status).toBe(200);
      expect(result.body.id).toBe(1);
      expect(result.body.price).toBeGreaterThan(0);
    });
  });

  test('should return the known product categories', async ({ productApi }) => {
    const result = await test.step('GET /products/categories', async () => {
      return productApi.getCategories();
    });

    await test.step('Verify categories', async () => {
      expect(result.status).toBe(200);
      expect(result.body).toEqual(
        expect.arrayContaining(['electronics', 'jewelery', "men's clothing", "women's clothing"]),
      );
    });
  });

  test('should filter products by category', async ({ productApi }) => {
    const result = await test.step('GET /products/category/electronics', async () => {
      return productApi.getProductsByCategory('electronics');
    });

    await test.step('Verify all results belong to electronics', async () => {
      expect(result.status).toBe(200);
      expect(result.body.length).toBeGreaterThan(0);
      for (const product of result.body) {
        expect(product.category).toBe('electronics');
      }
    });
  });
});
