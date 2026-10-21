# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: product-wishlist.spec.ts >> Product page — wishlist (PW-01..PW-03) >> PW-02 an out-of-stock product can still be wishlisted
- Location: tests\product-wishlist.spec.ts:20:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.waitForLoadState: Test timeout of 30000ms exceeded.
=========================== logs ===========================
  "load" event fired
  "domcontentloaded" event fired
============================================================
```

# Page snapshot

```yaml
- generic [active] [ref=f6e1]:
  - banner [ref=f6e5]:
    - generic [ref=f6e8]:
      - group [ref=f6e10]:
        - button "Menu" [ref=f6e11] [cursor=pointer]
      - heading [level=1] [ref=f6e14]:
        - link [ref=f6e15] [cursor=pointer]:
          - /url: /
          - img "ZeroGap Supply Co" [ref=f6e16]
      - generic [ref=f6e17]:
        - generic [ref=f6e18] [cursor=pointer]
        - link [ref=f6e22] [cursor=pointer]:
          - /url: /pages/wishlist
        - button [ref=f6e26] [cursor=pointer]
  - main [ref=f6e33]:
    - navigation "breadcrumbs product" [ref=f6e38]:
      - link "All" [ref=f6e39]:
        - /url: /collections/all
      - generic [ref=f6e43]: Andis Clipper Oil 118ml
    - generic [ref=f6e47]:
      - generic [ref=f6e49]:
        - region "Gallery Viewer" [ref=f6e51]:
          - list [ref=f6e53]:
            - listitem [ref=f6e54]:
              - link [ref=f6e56]:
                - /url: //bcppqf-4m.myshopify.com/cdn/shop/files/12108-andis-4oz-oil-bottle-straight-1-web.webp?v=1782345444&width=2489
                - img "Andis Clipper Oil 118ml" [ref=f6e57]
        - generic [ref=f6e59]:
          - heading "Andis Clipper Oil 118ml" [level=1] [ref=f6e61]
          - status [ref=f6e62]:
            - generic [ref=f6e65]:
              - generic [ref=f6e66]: Regular price
              - text: $9.05 AUD
          - generic [ref=f6e67]: Blade lubricant for regular clipper and trimmer maintenance.
          - status [ref=f6e68]:
            - paragraph [ref=f6e69]:
              - generic [ref=f6e72]: Hurry! Only 12 left in stock
          - generic [ref=f6e73]:
            - generic [ref=f6e74]:
              - group [ref=f6e76]:
                - button "Share" [ref=f6e77] [cursor=pointer]
              - generic [ref=f6e86]:
                - generic [ref=f6e88]:
                  - button "Decrease quantity for Andis Clipper Oil 118ml" [ref=f6e89] [cursor=pointer]
                  - spinbutton "Quantity" [ref=f6e91]: "1"
                  - button "Increase quantity for Andis Clipper Oil 118ml" [ref=f6e92] [cursor=pointer]
                - button "Add To Cart" [ref=f6e94] [cursor=pointer]
                - generic "Add to wishlist" [ref=f6e99] [cursor=pointer]
            - generic [ref=f6e101]:
              - generic [ref=f6e102]:
                - paragraph [ref=f6e103]: Express checkout with Shop Pay · Apple Pay · Google Pay
                - paragraph [ref=f6e104]: Ships from Australia in 1–2 business days
              - generic [ref=f6e110]:
                - generic [ref=f6e111]: 12 MONTH WARRANTY
                - generic [ref=f6e112]: Every Andis product is crafted to a premium standard.
      - generic [ref=f6e113]:
        - heading "WHY YOU'LL LIKE IT" [level=6] [ref=f6e114]
        - group [ref=f6e115]:
          - heading "Description" [level=3] [ref=f6e118] [cursor=pointer]
      - generic [ref=f6e121]:
        - heading "GOOD TO KNOW" [level=6] [ref=f6e122]
        - group [ref=f6e123]:
          - heading "SHIPPING & RETURNS" [level=3] [ref=f6e126] [cursor=pointer]
  - link "To top" [ref=f6e130]:
    - /url: "#andis-clipper-oil-118ml"
  - generic [ref=f6e136]:
    - link "Home" [ref=f6e137] [cursor=pointer]:
      - /url: /
    - link "Shop" [ref=f6e142] [cursor=pointer]:
      - /url: /collections
    - link "Wishlist" [ref=f6e147] [cursor=pointer]:
      - /url: /pages/wishlist
    - link "Log in" [ref=f6e152] [cursor=pointer]:
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