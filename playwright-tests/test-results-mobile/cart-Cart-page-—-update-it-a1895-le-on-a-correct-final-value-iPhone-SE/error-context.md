# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: cart.spec.ts >> Cart page — update items (UC-01..UC-05) >> UC-05 rapid successive quantity changes settle on a correct final value
- Location: tests\cart.spec.ts:54:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.waitForTimeout: Test timeout of 30000ms exceeded.
```

# Page snapshot

```yaml
- generic [ref=f5e1]:
  - banner [ref=f5e4]:
    - generic [ref=f5e7]:
      - group [ref=f5e9]:
        - button "Menu" [ref=f5e10] [cursor=pointer]
      - heading [level=1] [ref=f5e13]:
        - link [ref=f5e14] [cursor=pointer]:
          - /url: /
          - img "ZeroGap Supply Co" [ref=f5e15]
      - generic [ref=f5e16]:
        - generic [ref=f5e17] [cursor=pointer]
        - link [ref=f5e21] [cursor=pointer]:
          - /url: /pages/wishlist
        - button [ref=f5e24] [cursor=pointer]
  - main [active] [ref=f5e31]:
    - navigation "breadcrumbs product" [ref=f5e36]:
      - link "All" [ref=f5e37]:
        - /url: /collections/all
      - generic [ref=f5e41]: Andis Clipper Oil 118ml
    - generic [ref=f5e45]:
      - generic [ref=f5e47]:
        - region "Gallery Viewer" [ref=f5e49]:
          - list [ref=f5e51]:
            - listitem [ref=f5e52]:
              - link [ref=f5e54]:
                - /url: //bcppqf-4m.myshopify.com/cdn/shop/files/12108-andis-4oz-oil-bottle-straight-1-web.webp?v=1782345444&width=2489
                - img "Andis Clipper Oil 118ml" [ref=f5e55]
        - generic [ref=f5e57]:
          - heading "Andis Clipper Oil 118ml" [level=1] [ref=f5e59]
          - status [ref=f5e60]:
            - generic [ref=f5e63]:
              - generic [ref=f5e64]: Regular price
              - text: $9.05 AUD
          - generic [ref=f5e65]: Blade lubricant for regular clipper and trimmer maintenance.
          - status [ref=f5e66]:
            - paragraph [ref=f5e67]:
              - generic [ref=f5e70]: Hurry! Only 12 left in stock
          - generic [ref=f5e71]:
            - generic [ref=f5e72]:
              - group [ref=f5e74]:
                - button "Share" [ref=f5e75] [cursor=pointer]
              - generic [ref=f5e84]:
                - generic [ref=f5e86]:
                  - button "Decrease quantity for Andis Clipper Oil 118ml" [ref=f5e87] [cursor=pointer]
                  - spinbutton "Quantity" [ref=f5e89]: "1"
                  - button "Increase quantity for Andis Clipper Oil 118ml" [ref=f5e90] [cursor=pointer]
                - button "Add To Cart" [disabled] [ref=f5e92] [cursor=pointer]
                - generic "Add to wishlist" [ref=f5e100] [cursor=pointer]
            - generic [ref=f5e102]:
              - generic [ref=f5e103]:
                - paragraph [ref=f5e104]: Express checkout with Shop Pay · Apple Pay · Google Pay
                - paragraph [ref=f5e105]: Ships from Australia in 1–2 business days
              - generic [ref=f5e111]:
                - generic [ref=f5e112]: 12 MONTH WARRANTY
                - generic [ref=f5e113]: Every Andis product is crafted to a premium standard.
      - generic [ref=f5e114]:
        - heading "WHY YOU'LL LIKE IT" [level=6] [ref=f5e115]
        - group [ref=f5e116]:
          - heading "Description" [level=3] [ref=f5e119] [cursor=pointer]
      - generic [ref=f5e122]:
        - heading "GOOD TO KNOW" [level=6] [ref=f5e123]
        - group [ref=f5e124]:
          - heading "SHIPPING & RETURNS" [level=3] [ref=f5e127] [cursor=pointer]
  - contentinfo [ref=f5e131]:
    - generic [ref=f5e134]:
      - generic [ref=f5e136]:
        - link:
          - /url: /
        - paragraph [ref=f5e138]: Professional-grade grooming and barbering tools, built for sharp cuts and clean fades. Australia-wide shipping.
        - generic [ref=f5e143]:
          - textbox "Your email address" [ref=f5e144]
          - button "Subscribe" [ref=f5e145] [cursor=pointer]
      - generic [ref=f5e146]:
        - heading "Useful links" [level=2] [ref=f5e147] [cursor=pointer]
        - generic [ref=f5e148] [cursor=pointer]
      - generic [ref=f5e151]:
        - heading "Help & Support" [level=2] [ref=f5e152] [cursor=pointer]
        - generic [ref=f5e153] [cursor=pointer]
      - generic [ref=f5e156]:
        - heading "Resources" [level=2] [ref=f5e157] [cursor=pointer]
        - generic [ref=f5e158] [cursor=pointer]
      - list [ref=f5e163]:
        - listitem [ref=f5e164]:
          - link "TW" [ref=f5e165] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f5e169]:
          - link "FB" [ref=f5e170] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f5e174]:
          - link "IN" [ref=f5e175] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f5e179]:
          - link "Snapchat" [ref=f5e180] [cursor=pointer]:
            - /url: "#"
        - listitem [ref=f5e183]:
          - link "Vimeo" [ref=f5e184] [cursor=pointer]:
            - /url: "#"
    - generic [ref=f5e190]:
      - generic [ref=f5e191]:
        - generic [ref=f5e192]: Payment methods
        - list [ref=f5e193]:
          - listitem [ref=f5e194]:
            - img "American Express" [ref=f5e195]
          - listitem [ref=f5e200]:
            - img "Apple Pay" [ref=f5e201]
          - listitem [ref=f5e212]:
            - img "Google Pay" [ref=f5e213]
          - listitem [ref=f5e221]:
            - img "Mastercard" [ref=f5e222]
          - listitem [ref=f5e229]:
            - img "PayPal" [ref=f5e230]
          - listitem [ref=f5e236]:
            - img "Union Pay" [ref=f5e237]
          - listitem [ref=f5e243]:
            - img "Visa" [ref=f5e244]
      - paragraph [ref=f5e251]: © 2026 ZeroGap Supply Co.
  - link "To top" [ref=f5e252]:
    - /url: "#andis-clipper-oil-118ml"
  - generic [ref=f5e258]:
    - link "Home" [ref=f5e259] [cursor=pointer]:
      - /url: /
    - link "Shop" [ref=f5e264] [cursor=pointer]:
      - /url: /collections
    - link "Wishlist" [ref=f5e269] [cursor=pointer]:
      - /url: /pages/wishlist
    - link "Log in" [ref=f5e274] [cursor=pointer]:
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
  37 |   await addButton.click();
> 38 |   await page.waitForTimeout(1000);
     |              ^ Error: page.waitForTimeout: Test timeout of 30000ms exceeded.
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