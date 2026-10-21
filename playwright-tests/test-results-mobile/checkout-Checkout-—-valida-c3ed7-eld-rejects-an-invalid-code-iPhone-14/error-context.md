# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: checkout.spec.ts >> Checkout — validation (CV-01..CV-03) >> CV-03 discount code field rejects an invalid code
- Location: tests\checkout.spec.ts:76:7

# Error details

```
Test timeout of 120000ms exceeded.
```

```
Error: locator.click: Test timeout of 120000ms exceeded.
Call log:
  - waiting for getByRole('button', { name: /add discount/i })
    - locator resolved to <button type="button" aria-expanded="false" class="_1m2hr9gj _1m2hr9gi _1fragem12w _1fragemws _1fragemyd _1fragem126 _1fragem12n _1fragem12p _1fragem12e _1fragemyk _1m2hr9g1d _1m2hr9g18 _1fragem12d _1m2hr9g1v _1m2hr9g1u _1m2hr9g15 _1m2hr9gm _1m2hr9gk _1fragem5u _1m2hr9g1r _16s97g78w _1m2hr9g1i">…</button>
  - attempting click action
    - scrolling into view if needed
    - done scrolling

```

# Page snapshot

```yaml
- generic [ref=f14e2]:
  - generic [ref=f14e4]:
    - status [ref=f14e5]
    - generic [ref=f14e6]:
      - generic [ref=f14e7]:
        - link "Skip to content" [ref=f14e8]:
          - /url: "#checkout-main"
        - generic [ref=f14e9]:
          - banner [ref=f14e10]:
            - generic [ref=f14e15]:
              - link "ZeroGap Supply Co Navigate to Online Store" [ref=f14e18]:
                - /url: https://bcppqf-4m.myshopify.com
                - img "ZeroGap Supply Co"
                - generic [ref=f14e19]: Navigate to Online Store
              - link "Cart" [ref=f14e21]:
                - /url: https://bcppqf-4m.myshopify.com/cart
          - complementary [ref=f14e25]:
            - button "Order summary Total price $9.96" [ref=f14e28] [cursor=pointer]:
              - generic [ref=f14e29]:
                - generic [ref=f14e30]: Order summary
                - generic [ref=f14e34]:
                  - generic [ref=f14e35]: Total price
                  - paragraph [ref=f14e37]:
                    - strong [ref=f14e38]: $9.96
          - generic [ref=f14e41]:
            - main [ref=f14e42]:
              - heading "ZeroGap Supply Co Checkout" [level=1] [ref=f14e43]
              - generic [ref=f14e45]:
                - status [ref=f14e46]: Loading…
                - generic [ref=f14e47]:
                  - generic [ref=f14e48]:
                    - region "Contact" [ref=f14e49]:
                      - generic [ref=f14e53]:
                        - generic [ref=f14e54]:
                          - heading "Contact" [level=2] [ref=f14e55]
                          - link "Sign in" [ref=f14e56]:
                            - /url: https://bcppqf-4m.myshopify.com/customer_authentication/login?locale=en-AU&region_country=AU&return_to=%2Fcheckouts%2Fcn%2FhWNIDv20OjBfqIe5cteF8YbM%2Fen-au%3F_r%3DAQABWacor0Zff1IAtATWqeDZfx1kqFBugKjZbvj5iagZSV8biiIU%26company_location_id%26locale%3Den-AU
                        - generic [ref=f14e58]:
                          - generic [ref=f14e63]:
                            - generic: Email
                            - textbox "Email" [ref=f14e64]
                            - generic [ref=f14e66]:
                              - img "More information about how your contact info is used" [ref=f14e68]
                              - tooltip [ref=f14e71]: Used for your order confirmation and cart reminders
                          - generic [ref=f14e74]:
                            - checkbox "Email me with news and offers" [ref=f14e76] [cursor=pointer]
                            - generic [ref=f14e77] [cursor=pointer]: Email me with news and offers
                    - group [ref=f14e81]:
                      - generic [ref=f14e82]:
                        - heading "Delivery" [level=2] [ref=f14e84]
                        - generic [ref=f14e89]:
                          - generic [ref=f14e93]:
                            - generic [ref=f14e94]:
                              - generic [ref=f14e98]:
                                - generic: Country/Region
                                - combobox "Country/Region" [ref=f14e99]:
                                  - option "Australia" [selected]
                              - generic [ref=f14e100]:
                                - generic [ref=f14e102]:
                                  - generic: First name
                                  - textbox "First name" [ref=f14e103]
                                - generic [ref=f14e105]:
                                  - generic: Last name
                                  - textbox "Last name" [ref=f14e106]
                              - generic [ref=f14e111]:
                                - generic: Address
                                - textbox "Address" [ref=f14e112]
                              - generic [ref=f14e119]:
                                - generic: Apartment, suite, etc. (optional)
                                - textbox "Apartment, suite, etc. (optional)" [ref=f14e120]
                              - generic [ref=f14e121]:
                                - generic [ref=f14e123]:
                                  - generic: Suburb
                                  - textbox "Suburb" [ref=f14e124]
                                - generic [ref=f14e127]:
                                  - generic: State/territory
                                  - combobox "State/territory" [ref=f14e128]:
                                    - option "Australian Capital Territory"
                                    - option "New South Wales"
                                    - option "Northern Territory"
                                    - option "Queensland"
                                    - option "South Australia"
                                    - option "Tasmania"
                                    - option "Victoria"
                                    - option "Western Australia"
                                - generic [ref=f14e131]:
                                  - generic: Postcode
                                  - textbox "Postcode" [ref=f14e132]
                              - generic [ref=f14e135]:
                                - generic: Phone (optional)
                                - textbox "Phone (optional)" [ref=f14e136]
                                - generic [ref=f14e138]:
                                  - img "More information about Phone" [ref=f14e139]
                                  - tooltip [ref=f14e142]: In case we need to contact you about your order
                              - generic [ref=f14e144]:
                                - checkbox "Save this information for next time" [ref=f14e146] [cursor=pointer]
                                - generic [ref=f14e147] [cursor=pointer]: Save this information for next time
                            - generic [ref=f14e148]:
                              - textbox [ref=f14e149]
                              - textbox [ref=f14e150]
                              - textbox [ref=f14e151]
                              - textbox [ref=f14e152]
                              - textbox [ref=f14e153]: AU
                              - textbox [ref=f14e154]
                              - textbox [ref=f14e155]
                              - textbox [ref=f14e156]
                              - textbox [ref=f14e157]
                              - textbox [ref=f14e158]
                          - generic [ref=f14e159]:
                            - heading "Shipping method" [level=2] [ref=f14e160]
                            - paragraph [ref=f14e165]: Enter your shipping address to view available shipping methods.
                    - generic [ref=f14e167]:
                      - region "Payment" [ref=f14e170]:
                        - group [ref=f14e171]:
                          - generic [ref=f14e172]:
                            - heading "Payment" [level=2] [ref=f14e175]
                            - paragraph [ref=f14e177]: All transactions are secure and encrypted.
                          - generic [ref=f14e180]:
                            - group [ref=f14e186]:
                              - generic [ref=f14e187]:
                                - generic [ref=f14e188]:
                                  - generic [ref=f14e189] [cursor=pointer]:
                                    - generic [ref=f14e190]:
                                      - radio "Credit card, UnionPay and JCB" [checked] [ref=f14e192]
                                      - strong [ref=f14e194]: Credit card
                                    - generic [ref=f14e197]:
                                      - status [ref=f14e198]
                                      - generic [ref=f14e200]:
                                        - img "VISA" [ref=f14e202]
                                        - img "MASTERCARD" [ref=f14e204]
                                        - img "AMEX" [ref=f14e206]
                                        - generic [ref=f14e207]: "+2"
                                        - tooltip [ref=f14e211]
                                  - generic [ref=f14e221]:
                                    - generic [ref=f14e224]:
                                      - generic [ref=f14e225]: Card number
                                      - generic [ref=f14e236]:
                                        - generic [ref=f14e237]: Expiration date (MM / YY)
                                        - generic [ref=f14e246]:
                                          - generic: Security code
                                          - img "More information about Security code" [ref=f14e250]
                                      - generic [ref=f14e255]: Name on card
                                    - generic [ref=f14e264]:
                                      - checkbox "Use shipping address as billing address" [checked] [ref=f14e266] [cursor=pointer]
                                      - generic [ref=f14e267] [cursor=pointer]: Use shipping address as billing address
                                - radio [ref=f14e271] [cursor=pointer]
                                - generic [ref=f14e273] [cursor=pointer]:
                                  - radio "Cash on Delivery (COD)" [ref=f14e275]
                                  - strong [ref=f14e278]: Cash on Delivery (COD)
                            - textbox [ref=f14e280]
                      - generic [ref=f14e285]:
                        - region [ref=f14e286]:
                          - heading "Order summary" [level=2] [ref=f14e287]
                          - button "Add discount" [ref=f14e288] [cursor=pointer]
                          - button "Order summary Total 1 item AUD $9.96" [ref=f14e293] [cursor=pointer]:
                            - generic [ref=f14e295]:
                              - generic [ref=f14e296]: Order summary
                              - generic [ref=f14e301]:
                                - strong [ref=f14e303]: Total
                                - generic [ref=f14e304]: 1 item
                              - generic [ref=f14e308]:
                                - generic [ref=f14e309]: AUD
                                - strong [ref=f14e312]:
                                  - generic "$9.96" [ref=f14e314]
                        - generic [ref=f14e321]:
                          - heading "Finalize order" [level=2] [ref=f14e322]
                          - button "Pay now $9.96" [ref=f14e329] [cursor=pointer]:
                            - generic:
                              - generic:
                                - generic: Pay now
                                - generic:
                                  - generic:
                                    - generic:
                                      - generic:
                                        - generic "$9.96"
                  - button [disabled] [ref=f14e331] [cursor=pointer]: Submit
            - contentinfo [ref=f14e332]:
              - list [ref=f14e336]:
                - listitem [ref=f14e337]:
                  - button "Terms and policies" [ref=f14e338] [cursor=pointer]
      - generic:
        - progressbar
  - generic [ref=f14e339]: Opens external website in a new window.
  - generic [ref=f14e340]: Opens in a new window.
  - generic [ref=f14e341]: Opens external website.
  - status [ref=f14e342]
  - alert [ref=f14e343]
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
  22  |     await expect(checkoutBtn, 'expected a checkout button on /cart').toBeVisible({ timeout: 20_000 });
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
> 81  |       await page.getByRole('button', { name: /add discount/i }).click({ force: true });
      |                                                                 ^ Error: locator.click: Test timeout of 120000ms exceeded.
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