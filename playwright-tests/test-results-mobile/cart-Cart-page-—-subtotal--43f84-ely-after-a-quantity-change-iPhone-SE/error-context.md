# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: cart.spec.ts >> Cart page — subtotal (ST-01..ST-04) >> ST-01 subtotal updates immediately after a quantity change
- Location: tests\cart.spec.ts:102:7

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
- generic [active] [ref=f7e1]:
  - generic [ref=f7e3]:
    - dialog "Search" [ref=f7e4]:
      - generic [ref=f7e5]:
        - button "Close" [ref=f7e6] [cursor=pointer]
        - search [ref=f7e13]:
          - heading "What are you looking for ?" [level=2] [ref=f7e14]
          - generic [ref=f7e15]:
            - combobox "Search" [ref=f7e16]
            - button "Search" [ref=f7e17] [cursor=pointer]
          - list [ref=f7e22]:
            - listitem [ref=f7e23]: "Popular searches:"
            - listitem [ref=f7e24]:
              - link "featured" [ref=f7e25]:
                - /url: /search?q=featured&product=product
            - listitem [ref=f7e26]:
              - link "trendy" [ref=f7e27]:
                - /url: /search?q=trendy&product=product
            - listitem [ref=f7e28]:
              - link "sale" [ref=f7e29]:
                - /url: /search?q=sale&product=product
            - listitem [ref=f7e30]:
              - link "new" [ref=f7e31]:
                - /url: /search?q=new&product=product
          - status [ref=f7e36]
    - banner [ref=f7e38]:
      - generic [ref=f7e41]:
        - group [ref=f7e43]:
          - generic "Menu" [ref=f7e44] [cursor=pointer]
        - heading [level=1] [ref=f7e47]:
          - link [ref=f7e48] [cursor=pointer]:
            - /url: /
            - img "ZeroGap Supply Co" [ref=f7e49]
        - generic [ref=f7e50]:
          - generic [ref=f7e51] [cursor=pointer]
          - link [ref=f7e55] [cursor=pointer]:
            - /url: /pages/wishlist
          - link [ref=f7e59] [cursor=pointer]:
            - /url: /cart
  - main [ref=f7e66]:
    - navigation "breadcrumbs product" [ref=f7e71]:
      - link "All" [ref=f7e72]:
        - /url: /collections/all
      - generic [ref=f7e76]: Andis Clipper Oil 118ml
    - generic [ref=f7e80]:
      - generic [ref=f7e82]:
        - region "Gallery Viewer" [ref=f7e84]:
          - list [ref=f7e86]:
            - listitem [ref=f7e87]:
              - link [ref=f7e89]:
                - /url: //bcppqf-4m.myshopify.com/cdn/shop/files/12108-andis-4oz-oil-bottle-straight-1-web.webp?v=1782345444&width=2489
                - img "Andis Clipper Oil 118ml" [ref=f7e90]
        - generic [ref=f7e92]:
          - heading "Andis Clipper Oil 118ml" [level=1] [ref=f7e94]
          - status [ref=f7e95]:
            - generic [ref=f7e98]:
              - generic [ref=f7e99]: Regular price
              - text: $9.05 AUD
          - generic [ref=f7e100]: Blade lubricant for regular clipper and trimmer maintenance.
          - status [ref=f7e101]:
            - paragraph [ref=f7e102]:
              - generic [ref=f7e105]: Hurry! Only 12 left in stock
          - generic [ref=f7e106]:
            - generic [ref=f7e107]:
              - group [ref=f7e109]:
                - generic "Share" [ref=f7e110] [cursor=pointer]
              - generic [ref=f7e119]:
                - generic [ref=f7e121]:
                  - button "Decrease quantity for Andis Clipper Oil 118ml" [ref=f7e122] [cursor=pointer]
                  - spinbutton "Quantity" [ref=f7e124]: "1"
                  - button "Increase quantity for Andis Clipper Oil 118ml" [ref=f7e125] [cursor=pointer]
                - button "Add To Cart" [ref=f7e127] [cursor=pointer]
                - generic "Add to wishlist" [ref=f7e132] [cursor=pointer]
            - generic [ref=f7e134]:
              - generic [ref=f7e135]:
                - paragraph [ref=f7e136]: Express checkout with Shop Pay · Apple Pay · Google Pay
                - paragraph [ref=f7e137]: Ships from Australia in 1–2 business days
              - generic [ref=f7e143]:
                - generic [ref=f7e144]: 12 MONTH WARRANTY
                - generic [ref=f7e145]: Every Andis product is crafted to a premium standard.
      - generic [ref=f7e146]:
        - heading "WHY YOU'LL LIKE IT" [level=6] [ref=f7e147]
        - group [ref=f7e148]:
          - heading "Description" [level=3] [ref=f7e151] [cursor=pointer]
      - generic [ref=f7e154]:
        - heading "GOOD TO KNOW" [level=6] [ref=f7e155]
        - group [ref=f7e156]:
          - heading "SHIPPING & RETURNS" [level=3] [ref=f7e159] [cursor=pointer]
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