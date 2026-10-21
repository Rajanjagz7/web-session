# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: collection.spec.ts >> Collection page — subcategories (CL-01..CL-04) >> CL-01/CL-02 subcategory section renders without a broken grid
- Location: tests\collection.spec.ts:5:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.goto: Test timeout of 30000ms exceeded.
Call log:
  - navigating to "https://bcppqf-4m.myshopify.com/collections", waiting until "load"

```

# Page snapshot

```yaml
- generic [active] [ref=f4e1]:
  - banner [ref=f4e5]:
    - generic [ref=f4e8]:
      - group [ref=f4e10]:
        - button "Menu" [ref=f4e11] [cursor=pointer]
      - heading [level=1] [ref=f4e14]:
        - link [ref=f4e15] [cursor=pointer]:
          - /url: /
          - img "ZeroGap Supply Co" [ref=f4e16]
      - generic [ref=f4e17]:
        - generic [ref=f4e18] [cursor=pointer]
        - link [ref=f4e22] [cursor=pointer]:
          - /url: /pages/wishlist
        - button [ref=f4e25] [cursor=pointer]
        - link [ref=f4e32] [cursor=pointer]:
          - /url: /account
  - main [ref=f4e36]:
    - heading [level=1] [ref=f4e37]
    - generic [ref=f4e43]:
      - generic [ref=f4e44]: SHOP BY CATEGORY
      - heading "FIND YOUR CATEGORY" [level=2] [ref=f4e45]
      - paragraph [ref=f4e47]: From strong-hold pomades to post-shave care — browse the full ZeroGap range by category and find exactly what your routine needs.
      - generic [ref=f4e48]:
        - generic [ref=f4e49]:
          - generic [ref=f4e50]: "13"
          - generic [ref=f4e51]: CATEGORIES
        - generic [ref=f4e52]:
          - generic [ref=f4e53]: "38"
          - generic [ref=f4e54]: PRODUCTS
        - generic [ref=f4e55]:
          - generic [ref=f4e56]: 100%
          - generic [ref=f4e57]: BARBER-GRADE
    - generic [ref=f4e60]:
      - list [ref=f4e61]:
        - listitem [ref=f4e62]:
          - generic [ref=f4e64]:
            - link [ref=f4e68]:
              - /url: /collections/barber-essentials
              - img "Barber Essentials" [ref=f4e69]
            - generic [ref=f4e71]:
              - heading [level=3] [ref=f4e72]:
                - link "Barber Essentials" [ref=f4e73]:
                  - /url: /collections/barber-essentials
              - paragraph [ref=f4e74]: 11 Items
        - listitem [ref=f4e75]:
          - generic [ref=f4e77]:
            - link [ref=f4e81]:
              - /url: /collections/barbercon
              - img "BarberCon" [ref=f4e82]
            - generic [ref=f4e84]:
              - heading [level=3] [ref=f4e85]:
                - link "BarberCon" [ref=f4e86]:
                  - /url: /collections/barbercon
              - paragraph [ref=f4e87]: 1 Item
              - paragraph [ref=f4e88]: BarberCON produces a core range of essential salon accessories, sanitation equipment, and...
        - listitem [ref=f4e89]:
          - generic [ref=f4e93]:
            - heading [level=3] [ref=f4e94]:
              - link "Bundles" [ref=f4e95]:
                - /url: /collections/bundles
            - paragraph [ref=f4e96]: 0 Items
        - listitem [ref=f4e97]:
          - generic [ref=f4e101]:
            - heading [level=3] [ref=f4e102]:
              - link "Bundles & Kits" [ref=f4e103]:
                - /url: /collections/bundles-kits
            - paragraph [ref=f4e104]: 0 Items
        - listitem [ref=f4e105]:
          - generic [ref=f4e109]:
            - heading [level=3] [ref=f4e110]:
              - link "Clippers, Trimmers & Shavers" [ref=f4e111]:
                - /url: /collections/clippers-trimmers-shavers
            - paragraph [ref=f4e112]: 0 Items
        - listitem [ref=f4e113]:
          - generic [ref=f4e115]:
            - link [ref=f4e119]:
              - /url: /collections/hair-2-beauty-imports
              - img "Hair 2 Beauty Imports" [ref=f4e120]
            - generic [ref=f4e122]:
              - heading [level=3] [ref=f4e123]:
                - link "Hair 2 Beauty Imports" [ref=f4e124]:
                  - /url: /collections/hair-2-beauty-imports
              - paragraph [ref=f4e125]: 0 Items
              - paragraph [ref=f4e126]: Hair 2 Beauty Imports serves as a trusted wholesale distributor for beauty...
        - listitem [ref=f4e127]:
          - generic [ref=f4e131]:
            - heading [level=3] [ref=f4e132]:
              - link "Hair Products" [ref=f4e133]:
                - /url: /collections/hair-products
            - paragraph [ref=f4e134]: 0 Items
        - listitem [ref=f4e135]:
          - generic [ref=f4e137]:
            - link [ref=f4e141]:
              - /url: /collections/frontpage
              - img "Home page" [ref=f4e142]
            - generic [ref=f4e144]:
              - heading [level=3] [ref=f4e145]:
                - link "Home page" [ref=f4e146]:
                  - /url: /collections/frontpage
              - paragraph [ref=f4e147]: 1 Item
      - link "Loading More" [ref=f4e150] [cursor=pointer]:
        - /url: /collections?page=2
    - generic [ref=f4e158]:
      - heading "BUNDLE" [level=6] [ref=f4e159]
      - heading "CAN'T DECIDE? BUILD YOUR KIT" [level=2] [ref=f4e160]
      - generic [ref=f4e161]: Tell us your routine and save up to 15% when you bundle pomade, beard and shave essentials together.
      - generic [ref=f4e162]:
        - link "Shop Now" [disabled] [ref=f4e163] [cursor=pointer]
        - link "View Bundles" [disabled] [ref=f4e165] [cursor=pointer]
    - generic [ref=f4e171]:
      - paragraph [ref=f4e173]: NEWSLETTER
      - heading "JOIN THE ZEROGAP LIST" [level=2] [ref=f4e174]
      - paragraph [ref=f4e176]: Get grooming tips, product drops, and exclusive offers.
      - generic [ref=f4e180]:
        - textbox "Your email address" [ref=f4e181]
        - button "Subscribe" [ref=f4e182] [cursor=pointer]
  - link "To top" [ref=f4e184]:
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
> 22 |   await page.goto('/collections');
     |              ^ Error: page.goto: Test timeout of 30000ms exceeded.
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