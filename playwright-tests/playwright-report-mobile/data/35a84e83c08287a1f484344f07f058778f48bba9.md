# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: product-wishlist.spec.ts >> Product page — wishlist (PW-01..PW-03) >> PW-03 wishlist state persists across a page reload
- Location: tests\product-wishlist.spec.ts:35:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.waitForLoadState: Test timeout of 30000ms exceeded.
```

# Page snapshot

```yaml
- generic [active] [ref=f8e1]:
  - banner [ref=f8e5]:
    - generic [ref=f8e8]:
      - group [ref=f8e10]:
        - generic "Menu" [ref=f8e11] [cursor=pointer]
      - heading [level=1] [ref=f8e14]:
        - link [ref=f8e15] [cursor=pointer]:
          - /url: /
          - img "ZeroGap Supply Co" [ref=f8e16]
      - generic [ref=f8e17]:
        - generic [ref=f8e18] [cursor=pointer]
        - link [ref=f8e22] [cursor=pointer]:
          - /url: /pages/wishlist
        - link [ref=f8e26] [cursor=pointer]:
          - /url: /cart
  - main [ref=f8e33]:
    - navigation "breadcrumbs product" [ref=f8e38]:
      - link "All" [ref=f8e39]:
        - /url: /collections/all
      - generic [ref=f8e43]: Andis Clipper Oil 118ml
    - generic [ref=f8e47]:
      - generic [ref=f8e49]:
        - region "Gallery Viewer" [ref=f8e51]:
          - list [ref=f8e53]:
            - listitem [ref=f8e54]:
              - link [ref=f8e56]:
                - /url: //bcppqf-4m.myshopify.com/cdn/shop/files/12108-andis-4oz-oil-bottle-straight-1-web.webp?v=1782345444&width=2489
                - img "Andis Clipper Oil 118ml" [ref=f8e57]
        - generic [ref=f8e59]:
          - heading "Andis Clipper Oil 118ml" [level=1] [ref=f8e61]
          - status [ref=f8e62]:
            - generic [ref=f8e65]:
              - generic [ref=f8e66]: Regular price
              - text: $9.05 AUD
          - generic [ref=f8e67]: Blade lubricant for regular clipper and trimmer maintenance.
          - status [ref=f8e68]:
            - paragraph [ref=f8e69]:
              - generic [ref=f8e72]: Hurry! Only 12 left in stock
          - generic [ref=f8e73]:
            - generic [ref=f8e74]:
              - group [ref=f8e76]:
                - generic "Share" [ref=f8e77] [cursor=pointer]
              - generic [ref=f8e86]:
                - generic [ref=f8e88]:
                  - button "Decrease quantity for Andis Clipper Oil 118ml" [ref=f8e89] [cursor=pointer]
                  - spinbutton "Quantity" [ref=f8e91]: "1"
                  - button "Increase quantity for Andis Clipper Oil 118ml" [ref=f8e92] [cursor=pointer]
                - button "Add To Cart" [ref=f8e94] [cursor=pointer]
                - generic "Add to wishlist" [ref=f8e99] [cursor=pointer]
            - generic [ref=f8e101]:
              - generic [ref=f8e102]:
                - paragraph [ref=f8e103]: Express checkout with Shop Pay · Apple Pay · Google Pay
                - paragraph [ref=f8e104]: Ships from Australia in 1–2 business days
              - generic [ref=f8e110]:
                - generic [ref=f8e111]: 12 MONTH WARRANTY
                - generic [ref=f8e112]: Every Andis product is crafted to a premium standard.
      - generic [ref=f8e113]:
        - heading "WHY YOU'LL LIKE IT" [level=6] [ref=f8e114]
        - group [ref=f8e115]:
          - heading "Description" [level=3] [ref=f8e118] [cursor=pointer]
      - generic [ref=f8e121]:
        - heading "GOOD TO KNOW" [level=6] [ref=f8e122]
        - group [ref=f8e123]:
          - heading "SHIPPING & RETURNS" [level=3] [ref=f8e126] [cursor=pointer]
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