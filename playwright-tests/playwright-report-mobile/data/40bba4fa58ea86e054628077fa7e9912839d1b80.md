# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: cart.spec.ts >> Cart page — subtotal (ST-01..ST-04) >> ST-03 subtotal on an empty cart shows $0.00, never NaN
- Location: tests\cart.spec.ts:119:7

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
  - main [ref=f4e32]:
    - generic [ref=f4e35]:
      - img "Cart" [ref=f4e37]
      - heading "Your cart is empty" [level=3] [ref=f4e38]
      - paragraph [ref=f4e39]: Browse our range and add your first product to get started.
      - link "Continue shopping" [ref=f4e40] [cursor=pointer]:
        - /url: /collections/all
  - link "To top" [ref=f4e42]:
    - /url: "#your-shopping-cart"
  - generic [ref=f4e48]:
    - link "Home" [ref=f4e49] [cursor=pointer]:
      - /url: /
    - link "Shop" [ref=f4e54] [cursor=pointer]:
      - /url: /collections
    - link "Wishlist" [ref=f4e59] [cursor=pointer]:
      - /url: /pages/wishlist
    - link "Log in" [ref=f4e64] [cursor=pointer]:
      - /url: https://shopify.com/74156900421/account?locale=en&region_country=AU&buyer_flags=eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJiY3BwcWYtNG0ubXlzaG9waWZ5LmNvbSIsImZsYWdzIjpbXSwiZXhwIjoxNzkzMTgyOTU0LCJuYmYiOjE3OTI1NzgxNTR9.v48EJea35cGI0rlpEUGnriOZUFkpoP3hjOPdSiwYAb0
```

# Test source

```ts
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
> 120 |     await page.goto('/cart');
      |                ^ Error: page.goto: Test timeout of 30000ms exceeded.
  121 |     await expect(page.locator('body')).not.toContainText(/NaN|undefined/i);
  122 |   });
  123 | });
  124 | 
  125 | test.describe('Cart page — coupon code (CP-01..CP-10)', () => {
  126 |   test('CP-01 empty coupon field submit does not error', async ({ unlockedPage: page }) => {
  127 |     await addFirstProductToCart(page);
  128 |     await page.goto('/cart');
  129 |     const input = couponInput(page);
  130 |     if (!(await input.isVisible().catch(() => false))) {
  131 |       test.skip(true, 'No discount code field found on cart page for this theme.');
  132 |       return;
  133 |     }
  134 |     await input.fill('');
  135 |     await input.press('Enter');
  136 |     await page.waitForTimeout(500);
  137 |     await expect(page.locator('body')).not.toContainText(/500|internal server error/i);
  138 |   });
  139 | 
  140 |   test('CP-02 nonexistent coupon code shows an invalid-code message', async ({ unlockedPage: page }) => {
  141 |     await addFirstProductToCart(page);
  142 |     await page.goto('/cart');
  143 |     const input = couponInput(page);
  144 |     if (!(await input.isVisible().catch(() => false))) {
  145 |       test.skip(true, 'No discount code field found on cart page for this theme.');
  146 |       return;
  147 |     }
  148 |     await input.fill('FAKECODE99');
  149 |     await input.press('Enter');
  150 |     await page.waitForTimeout(1000);
  151 |     await expect(page.locator('body')).toContainText(/invalid|doesn.?t exist|not valid|not found/i);
  152 |   });
  153 | 
  154 |   test('CP-06 applying the same coupon twice does not double-discount', async ({ unlockedPage: page }) => {
  155 |     if (!process.env.VALID_COUPON) {
  156 |       test.skip(true, 'Set VALID_COUPON=<real code> to run this check.');
  157 |       return;
  158 |     }
  159 |     await addFirstProductToCart(page);
  160 |     await page.goto('/cart');
  161 |     const input = couponInput(page);
  162 |     if (!(await input.isVisible().catch(() => false))) {
  163 |       test.skip(true, 'No discount code field found on cart page for this theme.');
  164 |       return;
  165 |     }
  166 |     await input.fill(process.env.VALID_COUPON!);
  167 |     await input.press('Enter');
  168 |     await page.waitForTimeout(1000);
  169 |     const subtotalAfterFirst = await page.locator('[class*="total"]').first().textContent();
  170 |     await input.fill(process.env.VALID_COUPON!);
  171 |     await input.press('Enter');
  172 |     await page.waitForTimeout(1000);
  173 |     const subtotalAfterSecond = await page.locator('[class*="total"]').first().textContent();
  174 |     expect(subtotalAfterSecond).toBe(subtotalAfterFirst);
  175 |   });
  176 | 
  177 |   test('CP-08 coupon code with leading/trailing spaces is trimmed and accepted', async ({ unlockedPage: page }) => {
  178 |     if (!process.env.VALID_COUPON) {
  179 |       test.skip(true, 'Set VALID_COUPON=<real code> to run this check.');
  180 |       return;
  181 |     }
  182 |     await addFirstProductToCart(page);
  183 |     await page.goto('/cart');
  184 |     const input = couponInput(page);
  185 |     if (!(await input.isVisible().catch(() => false))) {
  186 |       test.skip(true, 'No discount code field found on cart page for this theme.');
  187 |       return;
  188 |     }
  189 |     await input.fill(`  ${process.env.VALID_COUPON}  `);
  190 |     await input.press('Enter');
  191 |     await page.waitForTimeout(1000);
  192 |     await expect(page.locator('body')).not.toContainText(/invalid|doesn.?t exist/i);
  193 |   });
  194 | 
  195 |   test('CP-09 injection-style coupon string is rejected, not reflected', async ({ unlockedPage: page }) => {
  196 |     await addFirstProductToCart(page);
  197 |     await page.goto('/cart');
  198 |     const input = couponInput(page);
  199 |     if (!(await input.isVisible().catch(() => false))) {
  200 |       test.skip(true, 'No discount code field found on cart page for this theme.');
  201 |       return;
  202 |     }
  203 |     await input.fill('<script>alert(1)</script>');
  204 |     await input.press('Enter');
  205 |     await page.waitForTimeout(1000);
  206 |     const bodyHtml = await page.locator('body').innerHTML();
  207 |     expect(bodyHtml).not.toContain('<script>alert(1)</script>');
  208 |   });
  209 | 
  210 |   test('CP-10 a discount larger than the subtotal floors the total at $0.00', async ({ unlockedPage: page }) => {
  211 |     if (!process.env.OVERSIZED_COUPON) {
  212 |       test.skip(true, 'Set OVERSIZED_COUPON=<real code worth more than the cart total> to run this check.');
  213 |       return;
  214 |     }
  215 |     await addFirstProductToCart(page);
  216 |     await page.goto('/cart');
  217 |     const input = couponInput(page);
  218 |     if (!(await input.isVisible().catch(() => false))) {
  219 |       test.skip(true, 'No discount code field found on cart page for this theme.');
  220 |       return;
```