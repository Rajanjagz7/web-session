# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: checkout.spec.ts >> Checkout — validation (CV-01..CV-03) >> CV-02 submitting with required fields empty shows errors and does not advance
- Location: tests\checkout.spec.ts:65:7

# Error details

```
Test timeout of 120000ms exceeded.
```

```
TimeoutError: page.waitForURL: Timeout 30000ms exceeded.
=========================== logs ===========================
  "domcontentloaded" event fired
  "networkidle" event fired
============================================================
```

# Page snapshot

```yaml
- generic [ref=f12e2]:
  - generic [ref=f12e4]:
    - status [ref=f12e5]
    - generic [ref=f12e6]:
      - generic [ref=f12e7]:
        - link "Skip to content" [ref=f12e8]:
          - /url: "#checkout-main"
        - generic [ref=f12e9]:
          - banner [ref=f12e10]:
            - generic [ref=f12e15]:
              - link "ZeroGap Supply Co Navigate to Online Store" [ref=f12e18]:
                - /url: https://bcppqf-4m.myshopify.com
                - img "ZeroGap Supply Co"
                - generic [ref=f12e19]: Navigate to Online Store
              - link "Cart" [ref=f12e21]:
                - /url: https://bcppqf-4m.myshopify.com/cart
          - complementary [ref=f12e25]:
            - button "Order summary Total price $9.96" [ref=f12e28] [cursor=pointer]:
              - generic [ref=f12e29]:
                - generic [ref=f12e30]: Order summary
                - generic [ref=f12e34]:
                  - generic [ref=f12e35]: Total price
                  - paragraph [ref=f12e37]:
                    - strong [ref=f12e38]: $9.96
          - generic [ref=f12e41]:
            - main [ref=f12e42]:
              - heading "ZeroGap Supply Co Checkout" [level=1] [ref=f12e43]
              - generic [ref=f12e45]:
                - status [ref=f12e46]
                - generic [ref=f12e47]:
                  - generic [ref=f12e48]:
                    - region "Contact" [ref=f12e49]:
                      - generic [ref=f12e53]:
                        - generic [ref=f12e54]:
                          - heading "Contact" [level=2] [ref=f12e55]
                          - link "Sign in" [ref=f12e56]:
                            - /url: https://bcppqf-4m.myshopify.com/customer_authentication/login?locale=en-AU&region_country=AU&return_to=%2Fcheckouts%2Fcn%2FhWNIDwIkYUXu20HamrdUTenk%2Fen-au%3F_r%3DAQABOG_ENJAIMQYN_CXbLrhzy2NP3dUCx0UCwk6wGo-2-jYZnWXK%26company_location_id%26locale%3Den-AU
                        - generic [ref=f12e58]:
                          - generic [ref=f12e63]:
                            - generic: Email
                            - textbox "Email" [ref=f12e64]
                            - generic [ref=f12e66]:
                              - img "More information about how your contact info is used" [ref=f12e68]
                              - tooltip [ref=f12e71]: Used for your order confirmation and cart reminders
                          - generic [ref=f12e74]:
                            - checkbox "Email me with news and offers" [ref=f12e76] [cursor=pointer]
                            - generic [ref=f12e77] [cursor=pointer]: Email me with news and offers
                    - group [ref=f12e81]:
                      - generic [ref=f12e82]:
                        - heading "Delivery" [level=2] [ref=f12e84]
                        - generic [ref=f12e89]:
                          - generic [ref=f12e93]:
                            - generic [ref=f12e94]:
                              - generic [ref=f12e98]:
                                - generic: Country/Region
                                - combobox "Country/Region" [ref=f12e99]:
                                  - option "Australia" [selected]
                              - generic [ref=f12e100]:
                                - generic [ref=f12e102]:
                                  - generic: First name
                                  - textbox "First name" [ref=f12e103]
                                - generic [ref=f12e105]:
                                  - generic: Last name
                                  - textbox "Last name" [ref=f12e106]
                              - generic [ref=f12e112]:
                                - generic: Address
                                - combobox "Address" [ref=f12e113]
                              - generic [ref=f12e120]:
                                - generic: Apartment, suite, etc. (optional)
                                - textbox "Apartment, suite, etc. (optional)" [ref=f12e121]
                              - generic [ref=f12e122]:
                                - generic [ref=f12e124]:
                                  - generic: Suburb
                                  - textbox "Suburb" [ref=f12e125]
                                - generic [ref=f12e128]:
                                  - generic: State/territory
                                  - combobox "State/territory" [ref=f12e129]:
                                    - option "Australian Capital Territory"
                                    - option "New South Wales"
                                    - option "Northern Territory"
                                    - option "Queensland"
                                    - option "South Australia"
                                    - option "Tasmania"
                                    - option "Victoria"
                                    - option "Western Australia"
                                - generic [ref=f12e132]:
                                  - generic: Postcode
                                  - textbox "Postcode" [ref=f12e133]
                              - generic [ref=f12e136]:
                                - generic: Phone (optional)
                                - textbox "Phone (optional)" [ref=f12e137]
                                - generic [ref=f12e139]:
                                  - img "More information about Phone" [ref=f12e140]
                                  - tooltip [ref=f12e143]: In case we need to contact you about your order
                              - generic [ref=f12e145]:
                                - checkbox "Save this information for next time" [ref=f12e147] [cursor=pointer]
                                - generic [ref=f12e148] [cursor=pointer]: Save this information for next time
                            - generic [ref=f12e149]:
                              - textbox [ref=f12e150]
                              - textbox [ref=f12e151]
                              - textbox [ref=f12e152]
                              - textbox [ref=f12e153]
                              - textbox [ref=f12e154]: AU
                              - textbox [ref=f12e155]
                              - textbox [ref=f12e156]
                              - textbox [ref=f12e157]
                              - textbox [ref=f12e158]
                              - textbox [ref=f12e159]
                          - generic [ref=f12e160]:
                            - heading "Shipping method" [level=2] [ref=f12e161]
                            - paragraph [ref=f12e166]: Enter your shipping address to view available shipping methods.
                    - generic [ref=f12e168]:
                      - region "Payment" [ref=f12e171]:
                        - group [ref=f12e172]:
                          - generic [ref=f12e173]:
                            - heading "Payment" [level=2] [ref=f12e176]
                            - paragraph [ref=f12e178]: All transactions are secure and encrypted.
                          - generic [ref=f12e181]:
                            - group [ref=f12e187]:
                              - generic [ref=f12e188]:
                                - generic [ref=f12e189]:
                                  - generic [ref=f12e190] [cursor=pointer]:
                                    - generic [ref=f12e191]:
                                      - radio "Credit card, UnionPay and JCB" [checked] [ref=f12e193]
                                      - strong [ref=f12e195]: Credit card
                                    - generic [ref=f12e198]:
                                      - status [ref=f12e199]
                                      - generic [ref=f12e201]:
                                        - img "VISA" [ref=f12e203]
                                        - img "MASTERCARD" [ref=f12e205]
                                        - img "AMEX" [ref=f12e207]
                                        - generic [ref=f12e208]: "+2"
                                        - tooltip [ref=f12e212]
                                  - generic [ref=f12e222]:
                                    - generic [ref=f12e225]:
                                      - generic [ref=f12e228]:
                                        - generic: Card number
                                        - iframe [ref=f12e231]:
                                          - generic [ref=f16e2]:
                                            - generic [ref=f16e3]:
                                              - generic [ref=f16e4]: Card number
                                              - textbox "Card number" [ref=f16e5]
                                            - generic [ref=f16e8]: Name on card
                                            - textbox [ref=f16e9]
                                            - generic [ref=f16e10]: Expiry month
                                            - textbox [ref=f16e11]
                                            - generic [ref=f16e12]: Expiry year
                                            - textbox [ref=f16e13]
                                            - generic [ref=f16e14]: Expiry date (MM / YY)
                                            - textbox [ref=f16e15]
                                            - generic [ref=f16e16]: Security code
                                            - textbox [ref=f16e17]
                                            - generic [ref=f16e18]: Issue date (MM / YY)
                                            - textbox [ref=f16e19]
                                            - generic [ref=f16e20]: Issue number
                                            - textbox [ref=f16e21]
                                            - button [ref=f16e22]
                                      - generic [ref=f12e236]:
                                        - generic [ref=f12e239]:
                                          - generic: Expiration date (MM / YY)
                                          - iframe [ref=f12e242]:
                                            - generic [ref=f17e2]:
                                              - generic [ref=f17e3]: Credit Card Number
                                              - textbox [ref=f17e4]
                                              - generic [ref=f17e5]: Name on card
                                              - textbox [ref=f17e6]
                                              - generic [ref=f17e7]: Expiry month
                                              - textbox [ref=f17e8]
                                              - generic [ref=f17e9]: Expiry year
                                              - textbox [ref=f17e10]
                                              - generic [ref=f17e11]:
                                                - generic [ref=f17e12]: Expiration date (MM / YY)
                                                - textbox "Expiration date (MM / YY)" [ref=f17e13]
                                              - generic [ref=f17e16]: Security code
                                              - textbox [ref=f17e17]
                                              - generic [ref=f17e18]: Issue date (MM / YY)
                                              - textbox [ref=f17e19]
                                              - generic [ref=f17e20]: Issue number
                                              - textbox [ref=f17e21]
                                              - button [ref=f17e22]
                                        - generic [ref=f12e245]:
                                          - generic: Security code
                                          - generic [ref=f12e246]:
                                            - iframe [ref=f12e248]:
                                              - generic [ref=f18e2]:
                                                - generic [ref=f18e3]: Credit Card Number
                                                - textbox [ref=f18e4]
                                                - generic [ref=f18e5]: Name on card
                                                - textbox [ref=f18e6]
                                                - generic [ref=f18e7]: Expiry month
                                                - textbox [ref=f18e8]
                                                - generic [ref=f18e9]: Expiry year
                                                - textbox [ref=f18e10]
                                                - generic [ref=f18e11]: Expiry date (MM / YY)
                                                - textbox [ref=f18e12]
                                                - generic [ref=f18e13]:
                                                  - generic [ref=f18e14]: Security code
                                                  - textbox "Security code" [ref=f18e15]
                                                - generic [ref=f18e18]: Issue date (MM / YY)
                                                - textbox [ref=f18e19]
                                                - generic [ref=f18e20]: Issue number
                                                - textbox [ref=f18e21]
                                                - button [ref=f18e22]
                                            - generic [ref=f12e249]:
                                              - img "More information about Security code" [ref=f12e250]
                                              - tooltip [ref=f12e253]: 3-digit security code usually found on the back of your card. American Express cards have a 4-digit code located on the front.
                                      - generic [ref=f12e256]:
                                        - generic: Name on card
                                        - iframe [ref=f12e259]:
                                          - generic [ref=f21e2]:
                                            - generic [ref=f21e3]: Credit Card Number
                                            - textbox [ref=f21e4]
                                            - generic [ref=f21e5]:
                                              - generic [ref=f21e6]: Name on card
                                              - textbox "Name on card" [ref=f21e7]
                                            - generic [ref=f21e10]: Expiry month
                                            - textbox [ref=f21e11]
                                            - generic [ref=f21e12]: Expiry year
                                            - textbox [ref=f21e13]
                                            - generic [ref=f21e14]: Expiry date (MM / YY)
                                            - textbox [ref=f21e15]
                                            - generic [ref=f21e16]: Security code
                                            - textbox [ref=f21e17]
                                            - generic [ref=f21e18]: Issue date (MM / YY)
                                            - textbox [ref=f21e19]
                                            - generic [ref=f21e20]: Issue number
                                            - textbox [ref=f21e21]
                                            - button [ref=f21e22]
                                    - generic [ref=f12e262]:
                                      - checkbox "Use shipping address as billing address" [checked] [ref=f12e264] [cursor=pointer]
                                      - generic [ref=f12e265] [cursor=pointer]: Use shipping address as billing address
                                - generic [ref=f12e267] [cursor=pointer]:
                                  - generic [ref=f12e268]:
                                    - radio "PayPal" [ref=f12e270]
                                    - strong [ref=f12e272]: PayPal
                                  - img "PayPal" [ref=f12e274]
                                - generic [ref=f12e276] [cursor=pointer]:
                                  - radio "Cash on Delivery (COD)" [ref=f12e278]
                                  - strong [ref=f12e281]: Cash on Delivery (COD)
                            - textbox [ref=f12e283]
                      - generic [ref=f12e288]:
                        - region [ref=f12e289]:
                          - heading "Order summary" [level=2] [ref=f12e290]
                          - button "Add discount" [ref=f12e291] [cursor=pointer]
                          - button "Order summary Total 1 item AUD $9.96" [ref=f12e296] [cursor=pointer]:
                            - generic [ref=f12e298]:
                              - generic [ref=f12e299]: Order summary
                              - generic [ref=f12e304]:
                                - strong [ref=f12e306]: Total
                                - generic [ref=f12e307]: 1 item
                              - generic [ref=f12e311]:
                                - generic [ref=f12e312]: AUD
                                - strong [ref=f12e315]:
                                  - generic "$9.96" [ref=f12e317]
                        - generic [ref=f12e324]:
                          - heading "Finalize order" [level=2] [ref=f12e325]
                          - button "Pay now $9.96" [ref=f12e332] [cursor=pointer]:
                            - generic:
                              - generic:
                                - generic: Pay now
                                - generic:
                                  - generic:
                                    - generic:
                                      - generic:
                                        - generic "$9.96"
                  - button [ref=f12e334] [cursor=pointer]: Submit
            - contentinfo [ref=f12e335]:
              - list [ref=f12e339]:
                - listitem [ref=f12e340]:
                  - button "Terms and policies" [ref=f12e341] [cursor=pointer]
      - generic:
        - progressbar
  - generic [ref=f12e342]: Opens external website in a new window.
  - generic [ref=f12e343]: Opens in a new window.
  - generic [ref=f12e344]: Opens external website.
  - status [ref=f12e345]
  - alert [ref=f12e346]
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
> 25  |   await page.waitForURL(/\/checkouts\//, { timeout: 30_000 });
      |              ^ TimeoutError: page.waitForURL: Timeout 30000ms exceeded.
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