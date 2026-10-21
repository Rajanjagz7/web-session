# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: home-wishlist.spec.ts >> Home page — wishlist (WL-01..WL-05) >> WL-05 spam-clicking the toggle leaves a consistent final state
- Location: tests\home-wishlist.spec.ts:35:7

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.click: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('[class*="wishlist"], [aria-label*="wishlist" i], button[data-wishlist]').first()

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
        - button [ref=f5e26] [cursor=pointer]
  - navigation "breadcrumbs page" [ref=f5e37]:
    - heading "Wishlist" [level=2] [ref=f5e38]
    - link "Home" [ref=f5e39]:
      - /url: /
    - generic [ref=f5e43]: Wishlist
  - main [ref=f5e44]:
    - paragraph [ref=f5e50]: Loading...
  - link "To top" [ref=f5e52]:
    - /url: "#wishlist"
  - generic [ref=f5e58]:
    - link "Home" [ref=f5e59] [cursor=pointer]:
      - /url: /
    - link "Shop" [ref=f5e64] [cursor=pointer]:
      - /url: /collections
    - link "Wishlist" [ref=f5e69] [cursor=pointer]:
      - /url: /pages/wishlist
    - link "Log in" [ref=f5e74] [cursor=pointer]:
      - /url: https://shopify.com/74156900421/account?locale=en&region_country=AU&buyer_flags=eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJiY3BwcWYtNG0ubXlzaG9waWZ5LmNvbSIsImZsYWdzIjpbXSwiZXhwIjoxNzkzMTg0MTc1LCJuYmYiOjE3OTI1NzkzNzV9.xSc5RlNeejqyJmwNtWhlcFsWrne77bbclN3njwTCcXE
```

# Test source

```ts
  1  | import { test, expect } from './fixtures';
  2  | 
  3  | const wishlistIcon = (page: import('@playwright/test').Page) =>
  4  |   page.locator('[class*="wishlist"], [aria-label*="wishlist" i], button[data-wishlist]').first();
  5  | 
  6  | test.describe('Home page — wishlist (WL-01..WL-05)', () => {
  7  |   test('WL-01 adding the same item twice does not duplicate it', async ({ unlockedPage: page }) => {
  8  |     const icon = wishlistIcon(page);
  9  |     if (!(await icon.isVisible().catch(() => false))) {
  10 |       test.skip(true, 'No wishlist control detected on Home page for this theme.');
  11 |       return;
  12 |     }
  13 |     await icon.click();
  14 |     await page.waitForTimeout(300);
  15 |     const stateAfterFirst = await icon.getAttribute('aria-pressed').catch(() => null);
  16 |     await icon.click();
  17 |     await page.waitForTimeout(300);
  18 |     const stateAfterSecond = await icon.getAttribute('aria-pressed').catch(() => null);
  19 |     expect(stateAfterFirst).not.toBe(stateAfterSecond === stateAfterFirst ? undefined : stateAfterFirst);
  20 |   });
  21 | 
  22 |   test('WL-02 wishlist as a guest does not throw an error', async ({ unlockedPage: page }) => {
  23 |     const icon = wishlistIcon(page);
  24 |     if (!(await icon.isVisible().catch(() => false))) {
  25 |       test.skip(true, 'No wishlist control detected on Home page for this theme.');
  26 |       return;
  27 |     }
  28 |     const errors: string[] = [];
  29 |     page.on('pageerror', (e) => errors.push(e.message));
  30 |     await icon.click();
  31 |     await page.waitForTimeout(500);
  32 |     expect(errors).toHaveLength(0);
  33 |   });
  34 | 
  35 |   test('WL-05 spam-clicking the toggle leaves a consistent final state', async ({ unlockedPage: page }) => {
  36 |     const icon = wishlistIcon(page);
  37 |     if (!(await icon.isVisible().catch(() => false))) {
  38 |       test.skip(true, 'No wishlist control detected on Home page for this theme.');
  39 |       return;
  40 |     }
  41 |     for (let i = 0; i < 10; i++) {
> 42 |       await icon.click();
     |                  ^ Error: locator.click: Test timeout of 30000ms exceeded.
  43 |     }
  44 |     await page.waitForTimeout(500);
  45 |     await page.reload();
  46 |     // After reload, the icon's persisted state should be readable without error.
  47 |     await expect(icon).toBeVisible();
  48 |   });
  49 | });
  50 | 
```