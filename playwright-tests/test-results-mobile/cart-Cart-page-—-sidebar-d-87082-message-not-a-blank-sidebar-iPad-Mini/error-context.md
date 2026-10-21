# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: cart.spec.ts >> Cart page — sidebar display (SC-01..SC-03) >> SC-01 empty cart shows a clear message, not a blank sidebar
- Location: tests\cart.spec.ts:5:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: expect(locator).toContainText(expected) failed

Locator: locator('body')
Expected pattern: /empty|nothing in your cart/i
Received string:  ""

Call log:
  - Expect "toContainText" with timeout 5000ms
  - waiting for locator('body')
  - 

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
    - generic [ref=f4e39]:
      - img "Cart" [ref=f4e41]
      - heading "Your cart is empty" [level=3] [ref=f4e42]
      - paragraph [ref=f4e43]: Browse our range and add your first product to get started.
      - link "Continue shopping" [ref=f4e44] [cursor=pointer]:
        - /url: /collections/all
  - contentinfo [ref=f4e46]:
    - generic [ref=f4e49]:
      - paragraph [ref=f4e53]: Professional-grade grooming and barbering tools, built for sharp cuts and clean fades. Australia-wide shipping.
      - generic [ref=f4e59]:
        - heading "Useful links" [level=2] [ref=f4e60]
        - list [ref=f4e61]:
          - listitem [ref=f4e62]
          - listitem [ref=f4e63]
          - listitem [ref=f4e64]
          - listitem [ref=f4e65]
          - listitem [ref=f4e66]
      - generic [ref=f4e67]:
        - heading "Help & Support" [level=2] [ref=f4e68]
        - list [ref=f4e69]:
          - listitem [ref=f4e70]
          - listitem [ref=f4e71]
          - listitem [ref=f4e72]
          - listitem [ref=f4e73]
      - generic [ref=f4e74]:
        - heading "Resources" [level=2] [ref=f4e75]
        - list [ref=f4e76]:
          - listitem [ref=f4e77]
          - listitem [ref=f4e78]
          - listitem [ref=f4e79]
          - listitem [ref=f4e80]
      - list [ref=f4e83]:
        - listitem [ref=f4e84]
        - listitem [ref=f4e85]
        - listitem [ref=f4e86]
        - listitem [ref=f4e87]
        - listitem [ref=f4e88]
    - generic [ref=f4e92]:
      - generic [ref=f4e93]:
        - generic [ref=f4e94]: Payment methods
        - list [ref=f4e95]:
          - listitem [ref=f4e96]:
            - img "American Express" [ref=f4e97]
          - listitem [ref=f4e102]:
            - img "Apple Pay" [ref=f4e103]
          - listitem [ref=f4e114]:
            - img "Google Pay" [ref=f4e115]
          - listitem [ref=f4e123]:
            - img "Mastercard" [ref=f4e124]
          - listitem [ref=f4e131]:
            - img "PayPal" [ref=f4e132]
          - listitem [ref=f4e138]:
            - img "Union Pay" [ref=f4e139]
          - listitem [ref=f4e145]:
            - img "Visa" [ref=f4e146]
      - paragraph [ref=f4e153]: © 2026 ZeroGap Supply Co.
  - link "To top" [ref=f4e154]:
    - /url: "#your-shopping-cart"
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
> 9   |       await expect(page.locator('body')).toContainText(/empty|nothing in your cart/i);
      |                                          ^ Error: expect(locator).toContainText(expected) failed
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
  26  |     await page.goto('/cart');
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
```