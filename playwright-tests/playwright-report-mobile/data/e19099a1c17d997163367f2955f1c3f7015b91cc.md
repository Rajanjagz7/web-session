# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: product-cart.spec.ts >> Product page — add to cart (PA-01..PA-08) >> PA-01 quantity zero blocks add to cart
- Location: tests\product-cart.spec.ts:8:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.waitForLoadState: Test timeout of 30000ms exceeded.
=========================== logs ===========================
  "domcontentloaded" event fired
  "load" event fired
============================================================
```

# Page snapshot

```yaml
- generic [active] [ref=f5e1]:
  - banner [ref=f5e5]:
    - generic [ref=f5e8]:
      - group [ref=f5e10]:
        - button "Menu" [ref=f5e11] [cursor=pointer]
      - heading [level=1] [ref=f5e14]:
        - link [ref=f5e15] [cursor=pointer]:
          - /url: /
          - img "ZeroGap Supply Co" [ref=f5e16]
      - generic [ref=f5e17]:
        - generic [ref=f5e18] [cursor=pointer]
        - link [ref=f5e22] [cursor=pointer]:
          - /url: /pages/wishlist
        - button [ref=f5e25] [cursor=pointer]
  - main [ref=f5e32]:
    - navigation "breadcrumbs product" [ref=f5e37]:
      - link "All" [ref=f5e38]:
        - /url: /collections/all
      - generic [ref=f5e42]: Andis Clipper Oil 118ml
    - generic [ref=f5e46]:
      - generic [ref=f5e48]:
        - region "Gallery Viewer" [ref=f5e50]:
          - list [ref=f5e52]:
            - listitem [ref=f5e53]:
              - link [ref=f5e55]:
                - /url: //bcppqf-4m.myshopify.com/cdn/shop/files/12108-andis-4oz-oil-bottle-straight-1-web.webp?v=1782345444&width=2489
                - img "Andis Clipper Oil 118ml" [ref=f5e56]
        - generic [ref=f5e58]:
          - heading "Andis Clipper Oil 118ml" [level=1] [ref=f5e60]
          - status [ref=f5e61]:
            - generic [ref=f5e64]:
              - generic [ref=f5e65]: Regular price
              - text: $9.05 AUD
          - generic [ref=f5e66]: Blade lubricant for regular clipper and trimmer maintenance.
          - status [ref=f5e67]:
            - paragraph [ref=f5e68]:
              - generic [ref=f5e71]: Hurry! Only 12 left in stock
          - generic [ref=f5e72]:
            - generic [ref=f5e73]:
              - group [ref=f5e75]:
                - button "Share" [ref=f5e76] [cursor=pointer]
              - generic [ref=f5e85]:
                - generic [ref=f5e87]:
                  - button "Decrease quantity for Andis Clipper Oil 118ml" [ref=f5e88] [cursor=pointer]
                  - spinbutton "Quantity" [ref=f5e90]: "1"
                  - button "Increase quantity for Andis Clipper Oil 118ml" [ref=f5e91] [cursor=pointer]
                - button "Add To Cart" [ref=f5e93] [cursor=pointer]
                - generic "Add to wishlist" [ref=f5e98] [cursor=pointer]
            - generic [ref=f5e100]:
              - generic [ref=f5e101]:
                - paragraph [ref=f5e102]: Express checkout with Shop Pay · Apple Pay · Google Pay
                - paragraph [ref=f5e103]: Ships from Australia in 1–2 business days
              - generic [ref=f5e109]:
                - generic [ref=f5e110]: 12 MONTH WARRANTY
                - generic [ref=f5e111]: Every Andis product is crafted to a premium standard.
      - generic [ref=f5e112]:
        - heading "WHY YOU'LL LIKE IT" [level=6] [ref=f5e113]
        - group [ref=f5e114]:
          - heading "Description" [level=3] [ref=f5e117] [cursor=pointer]
      - generic [ref=f5e120]:
        - heading "GOOD TO KNOW" [level=6] [ref=f5e121]
        - group [ref=f5e122]:
          - heading "SHIPPING & RETURNS" [level=3] [ref=f5e125] [cursor=pointer]
  - link "To top" [ref=f5e129]:
    - /url: "#andis-clipper-oil-118ml"
  - generic [ref=f5e135]:
    - link "Home" [ref=f5e136] [cursor=pointer]:
      - /url: /
    - link "Shop" [ref=f5e141] [cursor=pointer]:
      - /url: /collections
    - link "Wishlist" [ref=f5e146] [cursor=pointer]:
      - /url: /pages/wishlist
    - link "Log in" [ref=f5e151] [cursor=pointer]:
      - /url: https://shopify.com/74156900421/account?locale=en&region_country=AU&buyer_flags=eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJiY3BwcWYtNG0ubXlzaG9waWZ5LmNvbSIsImZsYWdzIjpbXSwiZXhwIjoxNzkzMTgyODk3LCJuYmYiOjE3OTI1NzgwOTd9.xYvok5PZx3INUORDmzTnfmPlGCU1XX1bDtN7WVqiH-E
```

# Test source

```ts
  1  | import { Page, expect } from '@playwright/test';
  2  | 
  3  | /** Opens a real product page, either from PRODUCT_URL env var or the first product on /collections/all. */
  4  | export async function openFirstProduct(page: Page) {
  5  |   if (process.env.PRODUCT_URL) {
  6  |     await page.goto(process.env.PRODUCT_URL);
  7  |     return;
  8  |   }
  9  |   await page.goto('/collections/all');
  10 |   const firstProductLink = page.locator('a[href*="/products/"]').first();
  11 |   await expect(firstProductLink, 'expected at least one product on /collections/all').toBeVisible();
  12 |   await firstProductLink.click();
> 13 |   await page.waitForLoadState('networkidle');
     |              ^ Error: page.waitForLoadState: Test timeout of 30000ms exceeded.
  14 | }
  15 | 
  16 | /** Opens a real category/collection page, either from CATEGORY_URL env var or the first link under /collections. */
  17 | export async function openFirstCategory(page: Page) {
  18 |   if (process.env.CATEGORY_URL) {
  19 |     await page.goto(process.env.CATEGORY_URL);
  20 |     return;
  21 |   }
  22 |   await page.goto('/collections');
  23 |   const firstCollectionLink = page.locator('a[href*="/collections/"]').first();
  24 |   await expect(firstCollectionLink, 'expected at least one collection link on /collections').toBeVisible();
  25 |   await firstCollectionLink.click();
  26 |   await page.waitForLoadState('networkidle');
  27 | }
  28 | 
  29 | /** Opens a product and adds it to cart, leaving the browser on that product page afterwards. */
  30 | export async function addFirstProductToCart(page: Page, qty?: string) {
  31 |   await openFirstProduct(page);
  32 |   const qtyInput = page.locator('input[type="number"][name="quantity"], input[name="quantity"]').first();
  33 |   if (qty && (await qtyInput.isVisible().catch(() => false))) {
  34 |     await qtyInput.fill(qty);
  35 |   }
  36 |   const addButton = page.getByRole('button', { name: /add to cart/i });
  37 |   await addButton.click();
  38 |   await page.waitForTimeout(1000);
  39 | }
  40 | 
  41 | export function cartLineItems(page: Page) {
  42 |   return page.locator('[class*="cart-item"], [class*="line-item"], tr[class*="cart"]');
  43 | }
  44 | 
  45 | export function couponInput(page: Page) {
  46 |   return page.getByPlaceholder(/discount|coupon|promo/i).first();
  47 | }
  48 | 
  49 | export function quantityInput(page: Page) {
  50 |   return page.locator('input[type="number"][name="quantity"], input[name="quantity"]').first();
  51 | }
  52 | 
```