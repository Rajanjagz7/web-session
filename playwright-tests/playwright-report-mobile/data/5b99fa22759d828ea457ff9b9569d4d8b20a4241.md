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
TimeoutError: page.waitForURL: Timeout 30000ms exceeded.
=========================== logs ===========================
  "networkidle" event fired
============================================================
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
                - status [ref=f14e46]
                - generic [ref=f14e47]:
                  - generic [ref=f14e48]:
                    - region "Contact" [ref=f14e49]:
                      - generic [ref=f14e53]:
                        - generic [ref=f14e54]:
                          - heading "Contact" [level=2] [ref=f14e55]
                          - link "Sign in" [ref=f14e56]:
                            - /url: https://bcppqf-4m.myshopify.com/customer_authentication/login?locale=en-AU&region_country=AU&return_to=%2Fcheckouts%2Fcn%2FhWNIDwJWbmnvl3JYBPodjRfY%2Fen-au%3F_r%3DAQABg4U1PGJAtXcOei7yaL2w1esSHCjFZZxC8jbToKUOaz0AvwpP%26company_location_id%26locale%3Den-AU
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
                              - generic [ref=f14e112]:
                                - generic: Address
                                - combobox "Address" [ref=f14e113]
                              - generic [ref=f14e120]:
                                - generic: Apartment, suite, etc. (optional)
                                - textbox "Apartment, suite, etc. (optional)" [ref=f14e121]
                              - generic [ref=f14e122]:
                                - generic [ref=f14e124]:
                                  - generic: Suburb
                                  - textbox "Suburb" [ref=f14e125]
                                - generic [ref=f14e128]:
                                  - generic: State/territory
                                  - combobox "State/territory" [ref=f14e129]:
                                    - option "Australian Capital Territory"
                                    - option "New South Wales"
                                    - option "Northern Territory"
                                    - option "Queensland"
                                    - option "South Australia"
                                    - option "Tasmania"
                                    - option "Victoria"
                                    - option "Western Australia"
                                - generic [ref=f14e132]:
                                  - generic: Postcode
                                  - textbox "Postcode" [ref=f14e133]
                              - generic [ref=f14e136]:
                                - generic: Phone (optional)
                                - textbox "Phone (optional)" [ref=f14e137]
                                - generic [ref=f14e139]:
                                  - img "More information about Phone" [ref=f14e140]
                                  - tooltip [ref=f14e143]: In case we need to contact you about your order
                              - generic [ref=f14e145]:
                                - checkbox "Save this information for next time" [ref=f14e147] [cursor=pointer]
                                - generic [ref=f14e148] [cursor=pointer]: Save this information for next time
                            - generic [ref=f14e149]:
                              - textbox [ref=f14e150]
                              - textbox [ref=f14e151]
                              - textbox [ref=f14e152]
                              - textbox [ref=f14e153]
                              - textbox [ref=f14e154]: AU
                              - textbox [ref=f14e155]
                              - textbox [ref=f14e156]
                              - textbox [ref=f14e157]
                              - textbox [ref=f14e158]
                              - textbox [ref=f14e159]
                          - generic [ref=f14e160]:
                            - heading "Shipping method" [level=2] [ref=f14e161]
                            - paragraph [ref=f14e166]: Enter your shipping address to view available shipping methods.
                    - generic [ref=f14e168]:
                      - region "Payment" [ref=f14e171]:
                        - group [ref=f14e172]:
                          - generic [ref=f14e173]:
                            - heading "Payment" [level=2] [ref=f14e176]
                            - paragraph [ref=f14e178]: All transactions are secure and encrypted.
                          - generic [ref=f14e181]:
                            - group [ref=f14e187]:
                              - generic [ref=f14e188]:
                                - generic [ref=f14e189]:
                                  - generic [ref=f14e190] [cursor=pointer]:
                                    - generic [ref=f14e191]:
                                      - radio "Credit card, UnionPay and JCB" [checked] [ref=f14e193]
                                      - strong [ref=f14e195]: Credit card
                                    - generic [ref=f14e198]:
                                      - status [ref=f14e199]
                                      - generic [ref=f14e201]:
                                        - img "VISA" [ref=f14e203]
                                        - img "MASTERCARD" [ref=f14e205]
                                        - img "AMEX" [ref=f14e207]
                                        - generic [ref=f14e208]: "+2"
                                        - tooltip [ref=f14e212]
                                  - generic [ref=f14e222]:
                                    - generic [ref=f14e225]:
                                      - generic [ref=f14e228]:
                                        - generic: Card number
                                        - iframe [ref=f14e231]
                                      - generic [ref=f14e238]:
                                        - generic [ref=f14e241]:
                                          - generic: Expiration date (MM / YY)
                                          - iframe [ref=f14e244]
                                        - generic [ref=f14e249]:
                                          - generic: Security code
                                          - generic [ref=f14e250]:
                                            - iframe [ref=f14e252]
                                            - generic [ref=f14e253]:
                                              - img "More information about Security code" [ref=f14e254]
                                              - tooltip [ref=f14e257]: 3-digit security code usually found on the back of your card. American Express cards have a 4-digit code located on the front.
                                      - generic [ref=f14e262]:
                                        - generic: Name on card
                                        - iframe [ref=f14e265]
                                    - generic [ref=f14e270]:
                                      - checkbox "Use shipping address as billing address" [checked] [ref=f14e272] [cursor=pointer]
                                      - generic [ref=f14e273] [cursor=pointer]: Use shipping address as billing address
                                - radio [ref=f14e277] [cursor=pointer]
                                - generic [ref=f14e279] [cursor=pointer]:
                                  - radio "Cash on Delivery (COD)" [ref=f14e281]
                                  - strong [ref=f14e284]: Cash on Delivery (COD)
                            - textbox [ref=f14e286]
                      - generic [ref=f14e291]:
                        - region [ref=f14e292]:
                          - heading "Order summary" [level=2] [ref=f14e293]
                          - button "Add discount" [ref=f14e294] [cursor=pointer]
                          - button "Order summary Total 1 item AUD $9.96" [ref=f14e299] [cursor=pointer]:
                            - generic [ref=f14e301]:
                              - generic [ref=f14e302]: Order summary
                              - generic [ref=f14e307]:
                                - strong [ref=f14e309]: Total
                                - generic [ref=f14e310]: 1 item
                              - generic [ref=f14e314]:
                                - generic [ref=f14e315]: AUD
                                - strong [ref=f14e318]:
                                  - generic "$9.96" [ref=f14e320]
                        - generic [ref=f14e327]:
                          - heading "Finalize order" [level=2] [ref=f14e328]
                          - generic [ref=f14e334]:
                            - button "Pay now $9.96" [disabled]:
                              - generic:
                                - generic:
                                  - generic: Pay now
                                  - generic:
                                    - generic:
                                      - generic:
                                        - generic:
                                          - generic "$9.96"
                  - button [ref=f14e336] [cursor=pointer]: Submit
            - contentinfo [ref=f14e337]:
              - list [ref=f14e341]:
                - listitem [ref=f14e342]:
                  - button "Terms and policies" [ref=f14e343] [cursor=pointer]
      - generic:
        - progressbar
  - generic [ref=f14e344]: Opens external website in a new window.
  - generic [ref=f14e345]: Opens in a new window.
  - generic [ref=f14e346]: Opens external website.
  - status [ref=f14e347]
  - alert [ref=f14e348]
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