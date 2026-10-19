import { test, expect } from './fixtures';

const emailInput = (page: import('@playwright/test').Page) =>
  page.locator('input[type="email"]').first();

test.describe('Home page — newsletter signup (NL-01..NL-07)', () => {
  test('NL-01 empty submit is blocked by validation, no reload', async ({ unlockedPage: page }) => {
    const input = emailInput(page);
    await input.fill('');
    const urlBefore = page.url();
    await input.press('Enter');
    await page.waitForTimeout(500);
    expect(page.url()).toBe(urlBefore);
  });

  test('NL-02 malformed email is rejected by HTML5 validation', async ({ unlockedPage: page }) => {
    const input = emailInput(page);
    for (const bad of ['test', 'test@', 'test@.com', '@test.com']) {
      await input.fill(bad);
      const isValid = await input.evaluate((el: HTMLInputElement) => el.checkValidity());
      expect(isValid, `expected "${bad}" to be invalid`).toBeFalsy();
    }
  });

  test('NL-03 plus-alias email is accepted by client-side validation', async ({ unlockedPage: page }) => {
    const input = emailInput(page);
    await input.fill('user+test@mail.example.com');
    const isValid = await input.evaluate((el: HTMLInputElement) => el.checkValidity());
    expect(isValid).toBeTruthy();
  });

  test('NL-06 leading/trailing spaces do not break validity', async ({ unlockedPage: page }) => {
    const input = emailInput(page);
    await input.fill('  user@example.com  ');
    const isValid = await input.evaluate((el: HTMLInputElement) => el.checkValidity());
    // Browsers trim automatically for type=email; if this fails, the theme
    // needs its own trim-before-submit handling.
    expect(isValid).toBeTruthy();
  });

  test('NL-07 script payload in email field is never executed', async ({ unlockedPage: page }) => {
    let dialogFired = false;
    page.on('dialog', async (d) => {
      dialogFired = true;
      await d.dismiss();
    });
    const input = emailInput(page);
    await input.fill('<script>alert(1)</script>');
    await input.press('Enter');
    await page.waitForTimeout(500);
    expect(dialogFired).toBeFalsy();
  });
});
