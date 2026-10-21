# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: cart.spec.ts >> Cart page — sidebar display (SC-01..SC-03) >> SC-02 cart with exactly 1 item renders cleanly
- Location: tests\cart.spec.ts:15:7

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
        - button [ref=f11e25] [cursor=pointer]
  - main [ref=f11e31]:
    - navigation "breadcrumbs product" [ref=f11e36]:
      - link "All" [ref=f11e37] [cursor=pointer]:
        - /url: /collections/all
      - generic [ref=f11e41]: Andis Clipper Oil 118ml
    - generic [ref=f11e45]:
      - generic [ref=f11e47]:
        - region "Gallery Viewer" [ref=f11e49]:
          - list [ref=f11e51]:
            - listitem [ref=f11e52]:
              - link [ref=f11e54] [cursor=pointer]:
                - /url: //bcppqf-4m.myshopify.com/cdn/shop/files/12108-andis-4oz-oil-bottle-straight-1-web.webp?v=1782345444&width=2489
                - img "Andis Clipper Oil 118ml" [ref=f11e55]
        - generic [ref=f11e57]:
          - heading "Andis Clipper Oil 118ml" [level=1] [ref=f11e59]
          - status [ref=f11e60]:
            - generic [ref=f11e63]:
              - generic [ref=f11e64]: Regular price
              - text: $9.05 AUD
          - generic [ref=f11e65]: Blade lubricant for regular clipper and trimmer maintenance.
          - status [ref=f11e66]:
            - paragraph [ref=f11e67]:
              - generic [ref=f11e70]: Hurry! Only 12 left in stock
          - generic [ref=f11e71]:
            - generic [ref=f11e72]:
              - group [ref=f11e74]:
                - button "Share" [ref=f11e75] [cursor=pointer]
              - generic [ref=f11e84]:
                - generic [ref=f11e86]:
                  - button "Decrease quantity for Andis Clipper Oil 118ml" [ref=f11e87] [cursor=pointer]
                  - spinbutton "Quantity" [ref=f11e89]: "1"
                  - button "Increase quantity for Andis Clipper Oil 118ml" [ref=f11e90] [cursor=pointer]
                - button "Add To Cart" [ref=f11e92] [cursor=pointer]
                - generic "Add to wishlist" [ref=f11e97] [cursor=pointer]
            - generic [ref=f11e99]:
              - generic [ref=f11e100]:
                - paragraph [ref=f11e101]: Express checkout with Shop Pay · Apple Pay · Google Pay
                - paragraph [ref=f11e102]: Ships from Australia in 1–2 business days
              - generic [ref=f11e108]:
                - generic [ref=f11e109]: 12 MONTH WARRANTY
                - generic [ref=f11e110]: Every Andis product is crafted to a premium standard.
      - generic [ref=f11e111]:
        - heading "WHY YOU'LL LIKE IT" [level=6] [ref=f11e112]
        - group [ref=f11e113]:
          - heading "Description" [level=3] [ref=f11e116] [cursor=pointer]
      - generic [ref=f11e119]:
        - heading "GOOD TO KNOW" [level=6] [ref=f11e120]
        - group [ref=f11e121]:
          - heading "SHIPPING & RETURNS" [level=3] [ref=f11e124] [cursor=pointer]
  - contentinfo [ref=f11e128]:
    - generic [ref=f11e131]:
      - generic [ref=f11e133]:
        - link [ref=f11e134] [cursor=pointer]:
          - /url: /
        - paragraph [ref=f11e136]: Professional-grade grooming and barbering tools, built for sharp cuts and clean fades. Australia-wide shipping.
        - generic [ref=f11e141]:
          - textbox "Your email address" [ref=f11e142]
          - button "Subscribe" [ref=f11e143] [cursor=pointer]
      - generic [ref=f11e144]:
        - heading "Useful links" [level=2] [ref=f11e145] [cursor=pointer]
        - generic [ref=f11e146] [cursor=pointer]
      - generic [ref=f11e149]:
        - heading "Help & Support" [level=2] [ref=f11e150] [cursor=pointer]
        - generic [ref=f11e151] [cursor=pointer]
      - generic [ref=f11e154]:
        - heading "Resources" [level=2] [ref=f11e155] [cursor=pointer]
        - generic [ref=f11e156] [cursor=pointer]
      - list [ref=f11e161]:
        - listitem [ref=f11e162]:
          - link "TW" [ref=f11e163] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f11e165]:
          - link "FB" [ref=f11e166] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f11e168]:
          - link "IN" [ref=f11e169] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f11e171]:
          - link "Snapchat" [ref=f11e172] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f11e174]:
          - link "Vimeo" [ref=f11e175] [cursor=pointer]:
            - /url: "#"
    - generic [ref=f11e180]:
      - generic [ref=f11e181]:
        - generic [ref=f11e182]: Payment methods
        - list [ref=f11e183]:
          - listitem [ref=f11e184]:
            - img "American Express" [ref=f11e185]
          - listitem [ref=f11e190]:
            - img "Apple Pay" [ref=f11e191]
          - listitem [ref=f11e202]:
            - img "Google Pay" [ref=f11e203]
          - listitem [ref=f11e211]:
            - img "Mastercard" [ref=f11e212]
          - listitem [ref=f11e219]:
            - img "PayPal" [ref=f11e220]
          - listitem [ref=f11e226]:
            - img "Union Pay" [ref=f11e227]
          - listitem [ref=f11e233]:
            - img "Visa" [ref=f11e234]
      - paragraph [ref=f11e241]: © 2026 ZeroGap Supply Co.
  - link "To top" [ref=f11e242] [cursor=pointer]:
    - /url: "#andis-clipper-oil-118ml"
  - generic [ref=f11e248]:
    - link "Home" [ref=f11e249] [cursor=pointer]:
      - /url: /
    - link "Shop" [ref=f11e254] [cursor=pointer]:
      - /url: /collections
    - link "Wishlist" [ref=f11e259] [cursor=pointer]:
      - /url: /pages/wishlist
    - link "Log in" [ref=f11e264] [cursor=pointer]:
      - /url: https://shopify.com/74156900421/account?locale=en&region_country=AU&buyer_flags=eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJiY3BwcWYtNG0ubXlzaG9waWZ5LmNvbSIsImZsYWdzIjpbXSwiZXhwIjoxNzkzMTgxMDAzLCJuYmYiOjE3OTI1NzYyMDN9.hv0KCcg2EYyleY9rt8PK7SMgVjauoqGjJTuNWRbYB14
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