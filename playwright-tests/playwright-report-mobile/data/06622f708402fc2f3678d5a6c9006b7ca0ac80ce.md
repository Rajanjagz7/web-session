# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: product-wishlist.spec.ts >> Product page — wishlist (PW-01..PW-03) >> PW-01 rapid add/remove toggle ends in a consistent state
- Location: tests\product-wishlist.spec.ts:8:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.click: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('[class*="wishlist"], [aria-label*="wishlist" i], button[data-wishlist]').first()

```

# Page snapshot

```yaml
- generic [active] [ref=f11e1]:
  - banner [ref=f11e5]:
    - generic [ref=f11e8]:
      - group [ref=f11e10]:
        - button "Menu" [ref=f11e11] [cursor=pointer]
      - heading [level=1] [ref=f11e14]:
        - link [ref=f11e15] [cursor=pointer]:
          - /url: /
          - img "ZeroGap Supply Co" [ref=f11e16]
      - generic [ref=f11e17]:
        - generic [ref=f11e18] [cursor=pointer]
        - link [ref=f11e22] [cursor=pointer]:
          - /url: /pages/wishlist
        - button [ref=f11e26] [cursor=pointer]
  - navigation "breadcrumbs page" [ref=f11e37]:
    - heading "Wishlist" [level=2] [ref=f11e38]
    - link "Home" [ref=f11e39]:
      - /url: /
    - generic [ref=f11e43]: Wishlist
  - main [ref=f11e44]:
    - paragraph [ref=f11e50]: Loading...
  - link "To top" [ref=f11e52]:
    - /url: "#wishlist"
  - generic [ref=f11e58]:
    - link "Home" [ref=f11e59] [cursor=pointer]:
      - /url: /
    - link "Shop" [ref=f11e64] [cursor=pointer]:
      - /url: /collections
    - link "Wishlist" [ref=f11e69] [cursor=pointer]:
      - /url: /pages/wishlist
    - link "Log in" [ref=f11e74] [cursor=pointer]:
      - /url: https://shopify.com/74156900421/account?locale=en&region_country=AU&buyer_flags=eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJiY3BwcWYtNG0ubXlzaG9waWZ5LmNvbSIsImZsYWdzIjpbXSwiZXhwIjoxNzkzMTg0MzI4LCJuYmYiOjE3OTI1Nzk1Mjh9.vtLzlw8eNjjtzZNpG1dm5x-_U3C93xANYo1k0Ac3Rzc
```

# Test source

```ts
  1  | import { test, expect } from './fixtures';
  2  | import { openFirstProduct } from './helpers';
  3  | 
  4  | const wishlistIcon = (page: import('@playwright/test').Page) =>
  5  |   page.locator('[class*="wishlist"], [aria-label*="wishlist" i], button[data-wishlist]').first();
  6  | 
  7  | test.describe('Product page — wishlist (PW-01..PW-03)', () => {
  8  |   test('PW-01 rapid add/remove toggle ends in a consistent state', async ({ unlockedPage: page }) => {
  9  |     await openFirstProduct(page);
  10 |     const icon = wishlistIcon(page);
  11 |     if (!(await icon.isVisible().catch(() => false))) {
  12 |       test.skip(true, 'No wishlist control on this product page for this theme.');
  13 |       return;
  14 |     }
> 15 |     for (let i = 0; i < 10; i++) await icon.click();
     |                                             ^ Error: locator.click: Test timeout of 30000ms exceeded.
  16 |     await page.waitForTimeout(500);
  17 |     await expect(icon).toBeVisible();
  18 |   });
  19 | 
  20 |   test('PW-02 an out-of-stock product can still be wishlisted', async ({ unlockedPage: page }) => {
  21 |     await openFirstProduct(page);
  22 |     const soldOutLabel = page.locator('text=/sold out/i').first();
  23 |     if (!(await soldOutLabel.isVisible().catch(() => false))) {
  24 |       test.skip(true, 'Product in view is in stock — point PRODUCT_URL at a sold-out product to run this check.');
  25 |       return;
  26 |     }
  27 |     const icon = wishlistIcon(page);
  28 |     if (!(await icon.isVisible().catch(() => false))) {
  29 |       test.skip(true, 'No wishlist control on this product page for this theme.');
  30 |       return;
  31 |     }
  32 |     await expect(icon).toBeEnabled();
  33 |   });
  34 | 
  35 |   test('PW-03 wishlist state persists across a page reload', async ({ unlockedPage: page }) => {
  36 |     await openFirstProduct(page);
  37 |     const icon = wishlistIcon(page);
  38 |     if (!(await icon.isVisible().catch(() => false))) {
  39 |       test.skip(true, 'No wishlist control on this product page for this theme.');
  40 |       return;
  41 |     }
  42 |     await icon.click();
  43 |     await page.waitForTimeout(300);
  44 |     const stateBefore = await icon.getAttribute('aria-pressed').catch(() => null);
  45 |     await page.reload();
  46 |     const stateAfter = await icon.getAttribute('aria-pressed').catch(() => null);
  47 |     expect(stateAfter).toBe(stateBefore);
  48 |   });
  49 | });
  50 | 
```