# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: category.spec.ts >> Category page — brand & type filters (FB-01..FB-04, FA-01..FA-05) >> FA-03 clearing all filters restores the full listing
- Location: tests\category.spec.ts:106:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: expected at least one collection link on /collections

expect(locator).toBeVisible() failed

Locator:  locator('a[href*="/collections/"]').first()
Expected: visible
Received: undefined

Call log:
  - expected at least one collection link on /collections with timeout 5000ms
  - waiting for locator('a[href*="/collections/"]').first()
  - 

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
        - link [ref=f5e32] [cursor=pointer]:
          - /url: /account
  - main [ref=f5e36]:
    - heading [level=1] [ref=f5e37]
    - generic [ref=f5e43]:
      - generic [ref=f5e44]: SHOP BY CATEGORY
      - heading "FIND YOUR CATEGORY" [level=2] [ref=f5e45]
      - paragraph [ref=f5e47]: From strong-hold pomades to post-shave care — browse the full ZeroGap range by category and find exactly what your routine needs.
      - generic [ref=f5e48]:
        - generic [ref=f5e49]:
          - generic [ref=f5e50]: "13"
          - generic [ref=f5e51]: CATEGORIES
        - generic [ref=f5e52]:
          - generic [ref=f5e53]: "38"
          - generic [ref=f5e54]: PRODUCTS
        - generic [ref=f5e55]:
          - generic [ref=f5e56]: 100%
          - generic [ref=f5e57]: BARBER-GRADE
    - generic [ref=f5e60]:
      - list [ref=f5e61]:
        - listitem [ref=f5e62]:
          - generic [ref=f5e64]:
            - link [ref=f5e68]:
              - /url: /collections/barber-essentials
              - img "Barber Essentials" [ref=f5e69]
            - generic [ref=f5e71]:
              - heading [level=3] [ref=f5e72]:
                - link "Barber Essentials" [ref=f5e73]:
                  - /url: /collections/barber-essentials
              - paragraph [ref=f5e74]: 11 Items
        - listitem [ref=f5e75]:
          - generic [ref=f5e77]:
            - link [ref=f5e81]:
              - /url: /collections/barbercon
              - img "BarberCon" [ref=f5e82]
            - generic [ref=f5e84]:
              - heading [level=3] [ref=f5e85]:
                - link "BarberCon" [ref=f5e86]:
                  - /url: /collections/barbercon
              - paragraph [ref=f5e87]: 1 Item
              - paragraph [ref=f5e88]: BarberCON produces a core range of essential salon accessories, sanitation equipment, and...
        - listitem [ref=f5e89]:
          - generic [ref=f5e93]:
            - heading [level=3] [ref=f5e94]:
              - link "Bundles" [ref=f5e95]:
                - /url: /collections/bundles
            - paragraph [ref=f5e96]: 0 Items
        - listitem [ref=f5e97]:
          - generic [ref=f5e101]:
            - heading [level=3] [ref=f5e102]:
              - link "Bundles & Kits" [ref=f5e103]:
                - /url: /collections/bundles-kits
            - paragraph [ref=f5e104]: 0 Items
        - listitem [ref=f5e105]:
          - generic [ref=f5e109]:
            - heading [level=3] [ref=f5e110]:
              - link "Clippers, Trimmers & Shavers" [ref=f5e111]:
                - /url: /collections/clippers-trimmers-shavers
            - paragraph [ref=f5e112]: 0 Items
        - listitem [ref=f5e113]:
          - generic [ref=f5e115]:
            - link [ref=f5e119]:
              - /url: /collections/hair-2-beauty-imports
              - img "Hair 2 Beauty Imports" [ref=f5e120]
            - generic [ref=f5e122]:
              - heading [level=3] [ref=f5e123]:
                - link "Hair 2 Beauty Imports" [ref=f5e124]:
                  - /url: /collections/hair-2-beauty-imports
              - paragraph [ref=f5e125]: 0 Items
              - paragraph [ref=f5e126]: Hair 2 Beauty Imports serves as a trusted wholesale distributor for beauty...
        - listitem [ref=f5e127]:
          - generic [ref=f5e131]:
            - heading [level=3] [ref=f5e132]:
              - link "Hair Products" [ref=f5e133]:
                - /url: /collections/hair-products
            - paragraph [ref=f5e134]: 0 Items
        - listitem [ref=f5e135]:
          - generic [ref=f5e137]:
            - link [ref=f5e141]:
              - /url: /collections/frontpage
              - img "Home page" [ref=f5e142]
            - generic [ref=f5e144]:
              - heading [level=3] [ref=f5e145]:
                - link "Home page" [ref=f5e146]:
                  - /url: /collections/frontpage
              - paragraph [ref=f5e147]: 1 Item
      - link "Loading More" [ref=f5e150] [cursor=pointer]:
        - /url: /collections?page=2
    - generic [ref=f5e158]:
      - heading "BUNDLE" [level=6] [ref=f5e159]
      - heading "CAN'T DECIDE? BUILD YOUR KIT" [level=2] [ref=f5e160]
      - generic [ref=f5e161]: Tell us your routine and save up to 15% when you bundle pomade, beard and shave essentials together.
      - generic [ref=f5e162]:
        - link "Shop Now" [disabled] [ref=f5e163] [cursor=pointer]
        - link "View Bundles" [disabled] [ref=f5e165] [cursor=pointer]
    - generic [ref=f5e171]:
      - paragraph [ref=f5e173]: NEWSLETTER
      - heading "JOIN THE ZEROGAP LIST" [level=2] [ref=f5e174]
      - paragraph [ref=f5e176]: Get grooming tips, product drops, and exclusive offers.
      - generic [ref=f5e180]:
        - textbox "Your email address" [ref=f5e181]
        - button "Subscribe" [ref=f5e182] [cursor=pointer]
  - link "To top" [ref=f5e184]:
    - /url: "#collections"
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
> 24 |   await expect(firstCollectionLink, 'expected at least one collection link on /collections').toBeVisible();
     |                                                                                              ^ Error: expected at least one collection link on /collections
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