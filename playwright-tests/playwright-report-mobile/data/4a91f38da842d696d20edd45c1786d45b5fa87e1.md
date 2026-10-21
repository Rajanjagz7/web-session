# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: checkout.spec.ts >> Checkout — page load (CO-01..CO-03) >> CO-01 checkout URL loads on the store domain with /checkouts/ path
- Location: tests\checkout.spec.ts:35:7

# Error details

```
Error: expected a checkout button on /cart

expect(locator).toBeVisible() failed

Locator: locator('button[name="checkout"], input[name="checkout"], a[href*="/checkout"]').or(getByRole('button', { name: /check\s?out/i })).filter({ visible: true }).first()
Expected: visible
Timeout: 20000ms
Error: element(s) not found

Call log:
  - expected a checkout button on /cart with timeout 20000ms
  - waiting for locator('button[name="checkout"], input[name="checkout"], a[href*="/checkout"]').or(getByRole('button', { name: /check\s?out/i })).filter({ visible: true }).first()

```

```yaml
- banner:
  - group:
    - button "Menu"
  - heading "ZeroGap Supply Co" [level=1]:
    - link "ZeroGap Supply Co":
      - /url: /
      - img "ZeroGap Supply Co"
  - img
  - link:
    - /url: /pages/wishlist
    - img
  - button:
    - img
- main:
  - img "Cart"
  - heading "Your cart is empty" [level=3]
  - paragraph: Browse our range and add your first product to get started.
  - link "Continue shopping":
    - /url: /collections/all
- contentinfo:
  - link:
    - /url: /
  - paragraph: Professional-grade grooming and barbering tools, built for sharp cuts and clean fades. Australia-wide shipping.
  - textbox "Your email address"
  - button "Subscribe"
  - heading "Useful links" [level=2]
  - img
  - heading "Help & Support" [level=2]
  - img
  - heading "Resources" [level=2]
  - img
  - list:
    - listitem:
      - link "TW":
        - /url: "#"
        - img
        - text: TW
    - listitem:
      - link "FB":
        - /url: "#"
        - img
        - text: FB
    - listitem:
      - link "IN":
        - /url: "#"
    - listitem:
      - link "Snapchat":
        - /url: "#"
    - listitem:
      - link "Vimeo":
        - /url: "#"
  - text: Payment methods
  - list:
    - listitem:
      - img "American Express"
    - listitem:
      - img "Apple Pay"
    - listitem:
      - img "Google Pay"
    - listitem:
      - img "Mastercard"
    - listitem:
      - img "PayPal"
    - listitem:
      - img "Union Pay"
    - listitem:
      - img "Visa"
  - paragraph: © 2026 ZeroGap Supply Co.
- link "To top":
  - /url: "#your-shopping-cart"
  - img
  - text: To top
- link "Home":
  - /url: /
  - img
  - text: Home
- link "Shop":
  - /url: /collections
  - img
  - text: Shop
- link "Wishlist":
  - /url: /pages/wishlist
  - img
  - text: Wishlist
- link "Log in":
  - /url: https://shopify.com/74156900421/account?locale=en&region_country=AU&buyer_flags=eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJiY3BwcWYtNG0ubXlzaG9waWZ5LmNvbSIsImZsYWdzIjpbXSwiZXhwIjoxNzkzMTgyMDkwLCJuYmYiOjE3OTI1NzcyOTB9.Akt2Gy3SyD7g4NgsYiTdFsgmBVEuLd2asoR9WzWoOus
  - img
  - text: Log in
```

# Test source

```ts
  1   | import { test, expect } from './fixtures';
  2   | import { addFirstProductToCart } from './helpers';
  3   | import { Page } from '@playwright/test';
  4   | 
  5   | /**
  6   |  * Reaches a live Shopify checkout by adding a product and using the cart's
  7   |  * checkout button. The /checkouts/cn/<token> URL is single-session, so it
  8   |  * can't be hard-coded; set CHECKOUT_URL to test one specific session instead.
  9   |  * Tests stop before payment — no real orders are placed.
  10  |  */
  11  | async function goToCheckout(page: Page) {
  12  |   if (process.env.CHECKOUT_URL) {
  13  |     await page.goto(process.env.CHECKOUT_URL);
  14  |   } else {
  15  |     await addFirstProductToCart(page);
  16  |     await page.goto('/cart');
  17  |     const checkoutBtn = page
  18  |       .locator('button[name="checkout"], input[name="checkout"], a[href*="/checkout"]')
  19  |       .or(page.getByRole('button', { name: /check\s?out/i }))
  20  |       .locator('visible=true')
  21  |       .first();
> 22  |     await expect(checkoutBtn, 'expected a checkout button on /cart').toBeVisible({ timeout: 20_000 });
      |                                                                      ^ Error: expected a checkout button on /cart
  23  |     await checkoutBtn.click();
  24  |   }
  25  |   await page.waitForURL(/\/checkouts\//, { timeout: 30_000 });
  26  |   await page.waitForLoadState('domcontentloaded');
  27  | }
  28  | 
  29  | test.describe.configure({ timeout: 120_000 });
  30  | 
  31  | const emailInput = (page: Page) =>
  32  |   page.locator('input[name="email"], input[autocomplete="email"], input[type="email"]').first();
  33  | 
  34  | test.describe('Checkout — page load (CO-01..CO-03)', () => {
  35  |   test('CO-01 checkout URL loads on the store domain with /checkouts/ path', async ({ unlockedPage: page }) => {
  36  |     await goToCheckout(page);
  37  |     expect(page.url()).toMatch(/\/checkouts\//);
  38  |     await expect(page.locator('body')).not.toContainText(/404|page not found/i);
  39  |   });
  40  | 
  41  |   test('CO-02 contact email field is present', async ({ unlockedPage: page }) => {
  42  |     await goToCheckout(page);
  43  |     await expect(emailInput(page)).toBeVisible({ timeout: 20_000 });
  44  |   });
  45  | 
  46  |   test('CO-03 order summary shows the product and a total', async ({ unlockedPage: page }) => {
  47  |     await goToCheckout(page);
  48  |     const summary = page.getByRole('complementary');
  49  |     await expect(summary.getByRole('heading', { name: /order summary/i })).toBeVisible({ timeout: 20_000 });
  50  |     await expect(summary.getByRole('row').filter({ hasText: /^Total/ })).toContainText(/AUD\s*\$\d/);
  51  |     await expect(summary.getByRole('row').filter({ hasText: /^Subtotal/ })).toContainText(/\$\d/);
  52  |   });
  53  | });
  54  | 
  55  | test.describe('Checkout — validation (CV-01..CV-03)', () => {
  56  |   test('CV-01 invalid email format is rejected', async ({ unlockedPage: page }) => {
  57  |     await goToCheckout(page);
  58  |     const email = emailInput(page);
  59  |     await expect(email).toBeVisible({ timeout: 20_000 });
  60  |     await email.fill('not-an-email');
  61  |     await email.blur();
  62  |     await expect(page.getByText(/enter a valid email|invalid email|valid email/i).first()).toBeVisible();
  63  |   });
  64  | 
  65  |   test('CV-02 submitting with required fields empty shows errors and does not advance', async ({ unlockedPage: page }) => {
  66  |     await goToCheckout(page);
  67  |     const submit = page
  68  |       .getByRole('button', { name: /pay now|continue to shipping/i })
  69  |       .first();
  70  |     await expect(submit).toBeVisible({ timeout: 20_000 });
  71  |     await submit.click();
  72  |     await expect(page.getByText(/enter an? |required|can't be blank|select a/i).first()).toBeVisible();
  73  |     expect(page.url()).toMatch(/\/checkouts\//);
  74  |   });
  75  | 
  76  |   test('CV-03 discount code field rejects an invalid code', async ({ unlockedPage: page }) => {
  77  |     await goToCheckout(page);
  78  |     const code = page.getByRole('textbox', { name: /discount code/i }).first();
  79  |     // On narrow viewports the field is collapsed behind an "Add discount" toggle.
  80  |     if (!(await code.isVisible({ timeout: 5_000 }).catch(() => false))) {
  81  |       await page.getByRole('button', { name: /add discount/i }).click({ force: true });
  82  |     }
  83  |     if (!(await code.isVisible({ timeout: 10_000 }).catch(() => false))) {
  84  |       test.skip(true, 'No discount field visible on this checkout.');
  85  |       return;
  86  |     }
  87  |     await code.fill('INVALID-CODE-123');
  88  |     await page.getByRole('button', { name: /apply discount code/i }).click();
  89  |     await expect(page.getByText(/enter a valid discount code|unable to apply|couldn't be applied/i).first()).toBeVisible({
  90  |       timeout: 15_000,
  91  |     });
  92  |   });
  93  | });
  94  | 
  95  | test.describe('Checkout — region (CR-01)', () => {
  96  |   test('CR-01 en-au checkout shows Australia as the default country', async ({ unlockedPage: page }) => {
  97  |     await goToCheckout(page);
  98  |     const country = page.getByRole('combobox', { name: /country\/region/i });
  99  |     await expect(country).toBeVisible({ timeout: 20_000 });
  100 |     await expect(country.locator('option:checked')).toHaveText('Australia');
  101 |   });
  102 | });
  103 | 
```