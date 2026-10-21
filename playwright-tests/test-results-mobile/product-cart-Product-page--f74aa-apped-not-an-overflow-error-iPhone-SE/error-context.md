# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: product-cart.spec.ts >> Product page — add to cart (PA-01..PA-08) >> PA-06 very large quantity is capped, not an overflow error
- Location: tests\product-cart.spec.ts:53:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.fill: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('input[type="number"][name="quantity"], input[name="quantity"]').first()
    - locator resolved to <input max="" min="1" value="1" data-max="" data-min="1" type="number" name="quantity" class="quantity__input" id="Quantity-template--21254024659013__main" form="product-form-template--21254024659013__main"/>

```

# Page snapshot

```yaml
- generic [active] [ref=f5e1]:
  - banner [ref=f5e5]:
    - generic [ref=f5e8]:
      - group [ref=f5e10]:
        - generic "Menu" [ref=f5e11] [cursor=pointer]
      - heading [level=1] [ref=f5e14]:
        - link [ref=f5e15] [cursor=pointer]:
          - /url: /
          - img "ZeroGap Supply Co" [ref=f5e16]
      - generic [ref=f5e17]:
        - generic [ref=f5e18] [cursor=pointer]
        - link [ref=f5e22] [cursor=pointer]:
          - /url: /pages/wishlist
        - link [ref=f5e26] [cursor=pointer]:
          - /url: /cart
  - main [ref=f5e33]:
    - navigation "breadcrumbs product" [ref=f5e38]:
      - link "All" [ref=f5e39]:
        - /url: /collections/all
      - generic [ref=f5e43]: Andis Clipper Oil 118ml
    - generic [ref=f5e47]:
      - generic [ref=f5e49]:
        - region "Gallery Viewer" [ref=f5e51]:
          - list [ref=f5e53]:
            - listitem [ref=f5e54]:
              - link [ref=f5e56]:
                - /url: //bcppqf-4m.myshopify.com/cdn/shop/files/12108-andis-4oz-oil-bottle-straight-1-web.webp?v=1782345444&width=2489
                - img "Andis Clipper Oil 118ml" [ref=f5e57]
        - generic [ref=f5e59]:
          - heading "Andis Clipper Oil 118ml" [level=1] [ref=f5e61]
          - status [ref=f5e62]:
            - generic [ref=f5e65]:
              - generic [ref=f5e66]: Regular price
              - text: $9.05 AUD
          - generic [ref=f5e67]: Blade lubricant for regular clipper and trimmer maintenance.
          - status [ref=f5e68]:
            - paragraph [ref=f5e69]:
              - generic [ref=f5e72]: Hurry! Only 12 left in stock
          - generic [ref=f5e73]:
            - generic [ref=f5e74]:
              - group [ref=f5e76]:
                - generic "Share" [ref=f5e77] [cursor=pointer]
              - generic [ref=f5e86]:
                - generic [ref=f5e88]:
                  - button "Decrease quantity for Andis Clipper Oil 118ml" [ref=f5e89] [cursor=pointer]
                  - spinbutton "Quantity" [ref=f5e91]: "1"
                  - button "Increase quantity for Andis Clipper Oil 118ml" [ref=f5e92] [cursor=pointer]
                - button "Add To Cart" [ref=f5e94] [cursor=pointer]
                - generic "Add to wishlist" [ref=f5e99] [cursor=pointer]
            - generic [ref=f5e101]:
              - generic [ref=f5e102]:
                - paragraph [ref=f5e103]: Express checkout with Shop Pay · Apple Pay · Google Pay
                - paragraph [ref=f5e104]: Ships from Australia in 1–2 business days
              - generic [ref=f5e110]:
                - generic [ref=f5e111]: 12 MONTH WARRANTY
                - generic [ref=f5e112]: Every Andis product is crafted to a premium standard.
      - generic [ref=f5e113]:
        - heading "WHY YOU'LL LIKE IT" [level=6] [ref=f5e114]
        - group [ref=f5e115]:
          - heading "Description" [level=3] [ref=f5e118] [cursor=pointer]
      - generic [ref=f5e121]:
        - heading "GOOD TO KNOW" [level=6] [ref=f5e122]
        - group [ref=f5e123]:
          - heading "SHIPPING & RETURNS" [level=3] [ref=f5e126] [cursor=pointer]
```

# Test source

```ts
  1  | import { test, expect } from './fixtures';
  2  | import { openFirstProduct, quantityInput } from './helpers';
  3  | 
  4  | const addToCartButton = (page: import('@playwright/test').Page) =>
  5  |   page.getByRole('button', { name: /add to cart/i });
  6  | 
  7  | test.describe('Product page — add to cart (PA-01..PA-08)', () => {
  8  |   test('PA-01 quantity zero blocks add to cart', async ({ unlockedPage: page }) => {
  9  |     await openFirstProduct(page);
  10 |     const qty = quantityInput(page);
  11 |     if (!(await qty.isVisible().catch(() => false))) {
  12 |       test.skip(true, 'No visible quantity input on this theme — check variant/quantity selector manually.');
  13 |       return;
  14 |     }
  15 |     await qty.fill('0');
  16 |     const button = addToCartButton(page);
  17 |     const isDisabled = await button.isDisabled().catch(() => false);
  18 |     if (!isDisabled) {
  19 |       await button.click();
  20 |       await expect(page.locator('body')).not.toContainText(/added to your cart/i);
  21 |     } else {
  22 |       expect(isDisabled).toBeTruthy();
  23 |     }
  24 |   });
  25 | 
  26 |   test('PA-02 negative quantity is rejected', async ({ unlockedPage: page }) => {
  27 |     await openFirstProduct(page);
  28 |     const qty = quantityInput(page);
  29 |     if (!(await qty.isVisible().catch(() => false))) {
  30 |       test.skip(true, 'No visible quantity input on this theme.');
  31 |       return;
  32 |     }
  33 |     await qty.fill('-1');
  34 |     const value = await qty.inputValue();
  35 |     expect(Number(value)).toBeGreaterThanOrEqual(0);
  36 |   });
  37 | 
  38 |   test('PA-03 decimal quantity is rejected or rounded, never silently accepted as-is', async ({ unlockedPage: page }) => {
  39 |     await openFirstProduct(page);
  40 |     const qty = quantityInput(page);
  41 |     if (!(await qty.isVisible().catch(() => false))) {
  42 |       test.skip(true, 'No visible quantity input on this theme.');
  43 |       return;
  44 |     }
  45 |     const step = await qty.getAttribute('step');
  46 |     await qty.fill('2.5');
  47 |     const value = await qty.inputValue();
  48 |     if (step === '1' || step === null) {
  49 |       expect(Number.isInteger(Number(value)), 'expected decimal input to be rounded to a whole number').toBeTruthy();
  50 |     }
  51 |   });
  52 | 
  53 |   test('PA-06 very large quantity is capped, not an overflow error', async ({ unlockedPage: page }) => {
  54 |     await openFirstProduct(page);
  55 |     const qty = quantityInput(page);
  56 |     if (!(await qty.isVisible().catch(() => false))) {
  57 |       test.skip(true, 'No visible quantity input on this theme.');
  58 |       return;
  59 |     }
> 60 |     await qty.fill('99999');
     |               ^ Error: locator.fill: Test timeout of 30000ms exceeded.
  61 |     const button = addToCartButton(page);
  62 |     await button.click();
  63 |     await page.waitForTimeout(1000);
  64 |     await expect(page.locator('body')).not.toContainText(/500|internal server error|overflow/i);
  65 |   });
  66 | 
  67 |   test('PA-07 add without selecting a required variant is blocked with a prompt', async ({ unlockedPage: page }) => {
  68 |     await openFirstProduct(page);
  69 |     const variantSelect = page.locator('select[name*="option" i]').first();
  70 |     if (!(await variantSelect.isVisible().catch(() => false))) {
  71 |       test.skip(true, 'No variant selector on this product — nothing to leave unselected.');
  72 |       return;
  73 |     }
  74 |     // Only meaningful if the theme ships with a blank/placeholder first option.
  75 |     const firstOptionValue = await variantSelect.locator('option').first().getAttribute('value');
  76 |     if (firstOptionValue) {
  77 |       test.skip(true, 'Variant selector has no blank placeholder option on this theme.');
  78 |       return;
  79 |     }
  80 |     const button = addToCartButton(page);
  81 |     const isDisabled = await button.isDisabled().catch(() => false);
  82 |     expect(isDisabled).toBeTruthy();
  83 |   });
  84 | 
  85 |   test('PA-08 rapid double-click does not duplicate the line item', async ({ unlockedPage: page }) => {
  86 |     await openFirstProduct(page);
  87 |     const button = addToCartButton(page);
  88 |     await expect(button).toBeVisible();
  89 |     await Promise.all([button.click(), button.click()]);
  90 |     await page.waitForTimeout(1000);
  91 |     await page.goto('/cart');
  92 |     const lineItems = page.locator('[class*="cart-item"], [class*="line-item"], tr[class*="cart"]');
  93 |     const count = await lineItems.count();
  94 |     expect(count, 'expected exactly one line item, not a duplicate').toBeLessThanOrEqual(1);
  95 |   });
  96 | });
  97 | 
```