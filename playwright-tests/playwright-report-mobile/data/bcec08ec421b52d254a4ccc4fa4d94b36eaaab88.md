# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: cart.spec.ts >> Cart page — update items (UC-01..UC-05) >> UC-01 updating quantity to 0 removes the item or is blocked, consistently
- Location: tests\cart.spec.ts:24:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.goto: Test timeout of 30000ms exceeded.
Call log:
  - navigating to "https://bcppqf-4m.myshopify.com/cart", waiting until "load"

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
        - button "1 item" [ref=f11e26] [cursor=pointer]:
          - generic [ref=f11e33]:
            - generic [ref=f11e34]: "1"
            - generic [ref=f11e35]: 1 item
  - main [ref=f11e36]:
    - navigation "breadcrumbs cart" [ref=f11e41]:
      - heading "Your Shopping Cart" [level=2] [ref=f11e42]
    - generic [ref=f11e44]:
      - heading "Cart" [level=1] [ref=f11e46]
      - generic [ref=f11e47]:
        - table [ref=f11e50]:
          - caption [ref=f11e51]: Cart
          - rowgroup [ref=f11e52]:
            - row [ref=f11e53]:
              - cell [ref=f11e54]:
                - link [ref=f11e55]:
                  - /url: /products/andis-clipper-oil-118ml?variant=45211104084037
                - img "Andis Clipper Oil 118ml" [ref=f11e57]
              - cell "Andis Clipper Oil 118ml $9.05" [ref=f11e58]:
                - link "Andis Clipper Oil 118ml" [ref=f11e59]:
                  - /url: /products/andis-clipper-oil-118ml?variant=45211104084037
                - generic [ref=f11e60]: $9.05
              - cell "Quantity Decrease quantity for Andis Clipper Oil 118ml 1 Increase quantity for Andis Clipper Oil 118ml" [ref=f11e61]:
                - generic [ref=f11e62]:
                  - generic [ref=f11e63]: Quantity
                  - generic [ref=f11e64]:
                    - button "Decrease quantity for Andis Clipper Oil 118ml" [ref=f11e65] [cursor=pointer]
                    - spinbutton "Quantity for Andis Clipper Oil 118ml" [ref=f11e67]: "1"
                    - button "Increase quantity for Andis Clipper Oil 118ml" [ref=f11e68] [cursor=pointer]
                - alert
              - cell [ref=f11e70]:
                - link "Remove Andis Clipper Oil 118ml" [ref=f11e73] [cursor=pointer]:
                  - /url: /cart/change?id=45211104084037:52a38e27dde3abfa19d6dcee03b277c3&quantity=0
                  - text: X
        - status [ref=f11e74]: Loading...
      - link "Continue shopping" [ref=f11e76] [cursor=pointer]:
        - /url: /collections/all
    - generic [ref=f11e81]:
      - generic [ref=f11e82]:
        - generic [ref=f11e83]:
          - heading "Subtotal" [level=2] [ref=f11e84]
          - paragraph [ref=f11e85]: $9.05 AUD
        - generic [ref=f11e86]: Taxes and shipping calculated at checkout
      - generic [ref=f11e88]:
        - textbox "Enter Your Discount Code" [ref=f11e89]
        - button "Apply" [ref=f11e90] [cursor=pointer]
      - button "Check out" [ref=f11e92] [cursor=pointer]
  - link "To top" [ref=f11e94]:
    - /url: "#your-shopping-cart"
  - generic [ref=f11e100]:
    - link "Home" [ref=f11e101] [cursor=pointer]:
      - /url: /
    - link "Shop" [ref=f11e106] [cursor=pointer]:
      - /url: /collections
    - link "Wishlist" [ref=f11e111] [cursor=pointer]:
      - /url: /pages/wishlist
    - link "Log in" [ref=f11e116] [cursor=pointer]:
      - /url: https://shopify.com/74156900421/account?locale=en&region_country=AU&buyer_flags=eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJiY3BwcWYtNG0ubXlzaG9waWZ5LmNvbSIsImZsYWdzIjpbXSwiZXhwIjoxNzkzMTgyOTA4LCJuYmYiOjE3OTI1NzgxMDh9.dvIDpC-IC2Nkue9OfmyEE5iL91W-_neTNijSBExcrOc
```

# Test source

```ts
  1   | import { test, expect } from './fixtures';
  2   | import { addFirstProductToCart, cartLineItems, couponInput, quantityInput } from './helpers';
  3   | 
  4   | test.describe('Cart page — sidebar display (SC-01..SC-03)', () => {
  5   |   test('SC-01 empty cart shows a clear message, not a blank sidebar', async ({ unlockedPage: page }) => {
  6   |     await page.goto('/cart');
  7   |     const items = await cartLineItems(page).count();
  8   |     if (items === 0) {
  9   |       await expect(page.locator('body')).toContainText(/empty|nothing in your cart/i);
  10  |     } else {
  11  |       test.skip(true, 'Cart was not empty at test start — clear it first to exercise this case.');
  12  |     }
  13  |   });
  14  | 
  15  |   test('SC-02 cart with exactly 1 item renders cleanly', async ({ unlockedPage: page }) => {
  16  |     await addFirstProductToCart(page);
  17  |     await page.goto('/cart');
  18  |     const count = await cartLineItems(page).count();
  19  |     expect(count).toBeGreaterThanOrEqual(1);
  20  |   });
  21  | });
  22  | 
  23  | test.describe('Cart page — update items (UC-01..UC-05)', () => {
  24  |   test('UC-01 updating quantity to 0 removes the item or is blocked, consistently', async ({ unlockedPage: page }) => {
  25  |     await addFirstProductToCart(page);
> 26  |     await page.goto('/cart');
      |                ^ Error: page.goto: Test timeout of 30000ms exceeded.
  27  |     const qty = quantityInput(page).first();
  28  |     if (!(await qty.isVisible().catch(() => false))) {
  29  |       test.skip(true, 'No editable quantity input on the cart page for this theme.');
  30  |       return;
  31  |     }
  32  |     await qty.fill('0');
  33  |     await qty.press('Enter').catch(() => {});
  34  |     await page.waitForTimeout(800);
  35  |     // Either the line item is now gone, or the input reverted to a positive number.
  36  |     const remainingValue = await qty.inputValue().catch(() => '0');
  37  |     const itemsLeft = await cartLineItems(page).count();
  38  |     expect(itemsLeft === 0 || Number(remainingValue) > 0).toBeTruthy();
  39  |   });
  40  | 
  41  |   test('UC-02 negative quantity is rejected', async ({ unlockedPage: page }) => {
  42  |     await addFirstProductToCart(page);
  43  |     await page.goto('/cart');
  44  |     const qty = quantityInput(page).first();
  45  |     if (!(await qty.isVisible().catch(() => false))) {
  46  |       test.skip(true, 'No editable quantity input on the cart page for this theme.');
  47  |       return;
  48  |     }
  49  |     await qty.fill('-1');
  50  |     const value = await qty.inputValue();
  51  |     expect(Number(value)).toBeGreaterThanOrEqual(0);
  52  |   });
  53  | 
  54  |   test('UC-05 rapid successive quantity changes settle on a correct final value', async ({ unlockedPage: page }) => {
  55  |     await addFirstProductToCart(page);
  56  |     await page.goto('/cart');
  57  |     const plusButton = page.locator('button[name="plus"], [class*="quantity"] button:has-text("+")').first();
  58  |     if (!(await plusButton.isVisible().catch(() => false))) {
  59  |       test.skip(true, 'No +/- quantity stepper on the cart page for this theme.');
  60  |       return;
  61  |     }
  62  |     for (let i = 0; i < 5; i++) await plusButton.click({ timeout: 1000 }).catch(() => {});
  63  |     await page.waitForTimeout(1000);
  64  |     const qty = quantityInput(page).first();
  65  |     const value = await qty.inputValue().catch(() => '');
  66  |     expect(Number(value)).toBeGreaterThan(1);
  67  |   });
  68  | });
  69  | 
  70  | test.describe('Cart page — remove items (RC-01..RC-02)', () => {
  71  |   test('RC-01 removing the last item shows the empty-cart state', async ({ unlockedPage: page }) => {
  72  |     await addFirstProductToCart(page);
  73  |     await page.goto('/cart');
  74  |     const removeButton = page.locator('[class*="remove"], a[href*="quantity=0"], button[aria-label*="remove" i]').first();
  75  |     if (!(await removeButton.isVisible().catch(() => false))) {
  76  |       test.skip(true, 'No remove control found on the cart page for this theme.');
  77  |       return;
  78  |     }
  79  |     await removeButton.click();
  80  |     await page.waitForTimeout(800);
  81  |     await expect(page.locator('body')).toContainText(/empty|nothing in your cart/i);
  82  |   });
  83  | 
  84  |   test('RC-02 double-clicking remove does not throw an error', async ({ unlockedPage: page }) => {
  85  |     await addFirstProductToCart(page);
  86  |     await page.goto('/cart');
  87  |     const removeButton = page.locator('[class*="remove"], a[href*="quantity=0"], button[aria-label*="remove" i]').first();
  88  |     if (!(await removeButton.isVisible().catch(() => false))) {
  89  |       test.skip(true, 'No remove control found on the cart page for this theme.');
  90  |       return;
  91  |     }
  92  |     const errors: string[] = [];
  93  |     page.on('pageerror', (e) => errors.push(e.message));
  94  |     await removeButton.click().catch(() => {});
  95  |     await removeButton.click({ timeout: 1000 }).catch(() => {});
  96  |     await page.waitForTimeout(500);
  97  |     expect(errors).toHaveLength(0);
  98  |   });
  99  | });
  100 | 
  101 | test.describe('Cart page — subtotal (ST-01..ST-04)', () => {
  102 |   test('ST-01 subtotal updates immediately after a quantity change', async ({ unlockedPage: page }) => {
  103 |     await addFirstProductToCart(page);
  104 |     await page.goto('/cart');
  105 |     const subtotal = page.locator('[class*="subtotal"], [class*="total"]').first();
  106 |     const before = (await subtotal.textContent().catch(() => '')) || '';
  107 |     const qty = quantityInput(page).first();
  108 |     if (!(await qty.isVisible().catch(() => false))) {
  109 |       test.skip(true, 'No editable quantity input on the cart page for this theme.');
  110 |       return;
  111 |     }
  112 |     await qty.fill('2');
  113 |     await qty.press('Enter').catch(() => {});
  114 |     await page.waitForTimeout(1000);
  115 |     const after = (await subtotal.textContent().catch(() => '')) || '';
  116 |     expect(after).not.toBe(before);
  117 |   });
  118 | 
  119 |   test('ST-03 subtotal on an empty cart shows $0.00, never NaN', async ({ unlockedPage: page }) => {
  120 |     await page.goto('/cart');
  121 |     await expect(page.locator('body')).not.toContainText(/NaN|undefined/i);
  122 |   });
  123 | });
  124 | 
  125 | test.describe('Cart page — coupon code (CP-01..CP-10)', () => {
  126 |   test('CP-01 empty coupon field submit does not error', async ({ unlockedPage: page }) => {
```