# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: cart.spec.ts >> Cart page — update items (UC-01..UC-05) >> UC-02 negative quantity is rejected
- Location: tests\cart.spec.ts:41:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.click: Test timeout of 30000ms exceeded.
Call log:
  - waiting for getByRole('button', { name: /add to cart/i })

```

# Page snapshot

```yaml
- generic [active] [ref=f8e1]:
  - banner [ref=f8e5]:
    - generic [ref=f8e8]:
      - group [ref=f8e10]:
        - button "Menu" [ref=f8e11] [cursor=pointer]
      - heading [level=1] [ref=f8e14]:
        - link [ref=f8e15] [cursor=pointer]:
          - /url: /
          - img "ZeroGap Supply Co" [ref=f8e16]
      - generic [ref=f8e17]:
        - generic [ref=f8e18] [cursor=pointer]
        - link [ref=f8e22] [cursor=pointer]:
          - /url: /pages/wishlist
        - button [ref=f8e25] [cursor=pointer]
  - main [ref=f8e32]:
    - navigation "breadcrumbs product" [ref=f8e37]:
      - link "All" [ref=f8e38]:
        - /url: /collections/all
      - generic [ref=f8e42]: Andis Clipper Oil 118ml
    - generic [ref=f8e46]:
      - generic [ref=f8e48]:
        - region "Gallery Viewer" [ref=f8e50]:
          - list [ref=f8e52]:
            - listitem [ref=f8e53]:
              - link [ref=f8e55]:
                - /url: //bcppqf-4m.myshopify.com/cdn/shop/files/12108-andis-4oz-oil-bottle-straight-1-web.webp?v=1782345444&width=2489
                - img "Andis Clipper Oil 118ml" [ref=f8e56]
        - generic [ref=f8e58]:
          - heading "Andis Clipper Oil 118ml" [level=1] [ref=f8e60]
          - status [ref=f8e61]:
            - generic [ref=f8e64]:
              - generic [ref=f8e65]: Regular price
              - text: $9.05 AUD
          - generic [ref=f8e66]: Blade lubricant for regular clipper and trimmer maintenance.
          - status [ref=f8e67]:
            - paragraph [ref=f8e68]:
              - generic [ref=f8e71]: Hurry! Only 12 left in stock
          - generic [ref=f8e72]:
            - generic [ref=f8e73]:
              - group [ref=f8e75]:
                - button "Share" [ref=f8e76] [cursor=pointer]
              - generic [ref=f8e85]:
                - generic [ref=f8e87]:
                  - button "Decrease quantity for Andis Clipper Oil 118ml" [ref=f8e88] [cursor=pointer]
                  - spinbutton "Quantity" [ref=f8e90]: "1"
                  - button "Increase quantity for Andis Clipper Oil 118ml" [ref=f8e91] [cursor=pointer]
                - button "Add To Cart" [ref=f8e93] [cursor=pointer]
                - generic "Add to wishlist" [ref=f8e98] [cursor=pointer]
            - generic [ref=f8e100]:
              - generic [ref=f8e101]:
                - paragraph [ref=f8e102]: Express checkout with Shop Pay · Apple Pay · Google Pay
                - paragraph [ref=f8e103]: Ships from Australia in 1–2 business days
              - generic [ref=f8e109]:
                - generic [ref=f8e110]: 12 MONTH WARRANTY
                - generic [ref=f8e111]: Every Andis product is crafted to a premium standard.
      - generic [ref=f8e112]:
        - heading "WHY YOU'LL LIKE IT" [level=6] [ref=f8e113]
        - group [ref=f8e114]:
          - heading "Description" [level=3] [ref=f8e117] [cursor=pointer]
      - generic [ref=f8e120]:
        - heading "GOOD TO KNOW" [level=6] [ref=f8e121]
        - group [ref=f8e122]:
          - heading "SHIPPING & RETURNS" [level=3] [ref=f8e125] [cursor=pointer]
  - contentinfo [ref=f8e129]:
    - generic [ref=f8e132]:
      - paragraph [ref=f8e136]: Professional-grade grooming and barbering tools, built for sharp cuts and clean fades. Australia-wide shipping.
      - list [ref=f8e147]:
        - listitem [ref=f8e148]
        - listitem [ref=f8e149]
        - listitem [ref=f8e150]
        - listitem [ref=f8e151]
        - listitem [ref=f8e152]
    - generic [ref=f8e156]:
      - generic [ref=f8e157]:
        - generic [ref=f8e158]: Payment methods
        - list [ref=f8e159]:
          - listitem [ref=f8e160]:
            - img "American Express" [ref=f8e161]
          - listitem [ref=f8e166]:
            - img "Apple Pay" [ref=f8e167]
          - listitem [ref=f8e178]:
            - img "Google Pay" [ref=f8e179]
          - listitem [ref=f8e187]:
            - img "Mastercard" [ref=f8e188]
          - listitem [ref=f8e195]:
            - img "PayPal" [ref=f8e196]
          - listitem [ref=f8e202]:
            - img "Union Pay" [ref=f8e203]
          - listitem [ref=f8e209]:
            - img "Visa" [ref=f8e210]
      - paragraph [ref=f8e217]: © 2026 ZeroGap Supply Co.
  - link "To top" [ref=f8e218]:
    - /url: "#andis-clipper-oil-118ml"
  - generic [ref=f8e224]:
    - link "Home" [ref=f8e225] [cursor=pointer]:
      - /url: /
    - link "Shop" [ref=f8e230] [cursor=pointer]:
      - /url: /collections
    - link "Wishlist" [ref=f8e235] [cursor=pointer]:
      - /url: /pages/wishlist
    - link "Log in" [ref=f8e240] [cursor=pointer]:
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
  13 |   await page.waitForLoadState('networkidle');
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
> 37 |   await addButton.click();
     |                   ^ Error: locator.click: Test timeout of 30000ms exceeded.
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