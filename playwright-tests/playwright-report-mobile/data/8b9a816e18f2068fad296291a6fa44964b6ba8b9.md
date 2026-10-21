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
Error: page.waitForLoadState: Test timeout of 30000ms exceeded.
```

# Page snapshot

```yaml
- generic [active] [ref=f5e1]:
  - generic [ref=f5e3]:
    - dialog "Search" [ref=f5e4]:
      - generic [ref=f5e5]:
        - button "Close" [ref=f5e6] [cursor=pointer]
        - search [ref=f5e13]:
          - heading "What are you looking for ?" [level=2] [ref=f5e14]
          - generic [ref=f5e15]:
            - combobox "Search" [ref=f5e16]
            - button "Search" [ref=f5e17] [cursor=pointer]
          - list [ref=f5e22]:
            - listitem [ref=f5e23]: "Popular searches:"
            - listitem [ref=f5e24]:
              - link "featured" [ref=f5e25]:
                - /url: /search?q=featured&product=product
            - listitem [ref=f5e26]:
              - link "trendy" [ref=f5e27]:
                - /url: /search?q=trendy&product=product
            - listitem [ref=f5e28]:
              - link "sale" [ref=f5e29]:
                - /url: /search?q=sale&product=product
            - listitem [ref=f5e30]:
              - link "new" [ref=f5e31]:
                - /url: /search?q=new&product=product
          - status [ref=f5e36]
    - banner [ref=f5e38]:
      - generic [ref=f5e41]:
        - group [ref=f5e43]:
          - generic "Menu" [ref=f5e44] [cursor=pointer]
        - heading [level=1] [ref=f5e47]:
          - link [ref=f5e48] [cursor=pointer]:
            - /url: /
            - img "ZeroGap Supply Co" [ref=f5e49]
        - generic [ref=f5e50]:
          - generic [ref=f5e51] [cursor=pointer]
          - link [ref=f5e55] [cursor=pointer]:
            - /url: /pages/wishlist
          - link [ref=f5e59] [cursor=pointer]:
            - /url: /cart
  - main [ref=f5e66]:
    - navigation "breadcrumbs product" [ref=f5e71]:
      - link "All" [ref=f5e72]:
        - /url: /collections/all
      - generic [ref=f5e76]: Andis Clipper Oil 118ml
    - generic [ref=f5e80]:
      - generic [ref=f5e82]:
        - region "Gallery Viewer" [ref=f5e84]:
          - list [ref=f5e86]:
            - listitem [ref=f5e87]:
              - link [ref=f5e89]:
                - /url: //bcppqf-4m.myshopify.com/cdn/shop/files/12108-andis-4oz-oil-bottle-straight-1-web.webp?v=1782345444&width=2489
                - img "Andis Clipper Oil 118ml" [ref=f5e90]
        - generic [ref=f5e92]:
          - heading "Andis Clipper Oil 118ml" [level=1] [ref=f5e94]
          - status [ref=f5e95]:
            - generic [ref=f5e98]:
              - generic [ref=f5e99]: Regular price
              - text: $9.05 AUD
          - generic [ref=f5e100]: Blade lubricant for regular clipper and trimmer maintenance.
          - status [ref=f5e101]:
            - paragraph [ref=f5e102]:
              - generic [ref=f5e105]: Hurry! Only 12 left in stock
          - generic [ref=f5e106]:
            - generic [ref=f5e107]:
              - group [ref=f5e109]:
                - generic "Share" [ref=f5e110] [cursor=pointer]
              - generic [ref=f5e119]:
                - generic [ref=f5e121]:
                  - button "Decrease quantity for Andis Clipper Oil 118ml" [ref=f5e122] [cursor=pointer]
                  - spinbutton "Quantity" [ref=f5e124]: "1"
                  - button "Increase quantity for Andis Clipper Oil 118ml" [ref=f5e125] [cursor=pointer]
                - button "Add To Cart" [ref=f5e127] [cursor=pointer]
                - generic "Add to wishlist" [ref=f5e132] [cursor=pointer]
            - generic [ref=f5e134]:
              - generic [ref=f5e135]:
                - paragraph [ref=f5e136]: Express checkout with Shop Pay · Apple Pay · Google Pay
                - paragraph [ref=f5e137]: Ships from Australia in 1–2 business days
              - generic [ref=f5e143]:
                - generic [ref=f5e144]: 12 MONTH WARRANTY
                - generic [ref=f5e145]: Every Andis product is crafted to a premium standard.
      - generic [ref=f5e146]:
        - heading "WHY YOU'LL LIKE IT" [level=6] [ref=f5e147]
        - group [ref=f5e148]:
          - heading "Description" [level=3] [ref=f5e151] [cursor=pointer]
      - generic [ref=f5e154]:
        - heading "GOOD TO KNOW" [level=6] [ref=f5e155]
        - group [ref=f5e156]:
          - heading "SHIPPING & RETURNS" [level=3] [ref=f5e159] [cursor=pointer]
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