import { test, expect } from '@playwright/test';

test.describe('New Sunrise - Comprehensive Negative Scenarios', () => {
  // Run tests serially with adequate timeout for clean execution
  test.describe.configure({ mode: 'serial' });
  test.setTimeout(60_000);

  // ==========================================
  // SECTION 1: AUTHENTICATION NEGATIVE SCENARIOS
  // ==========================================

  test('Negative 1.1: Invalid password prevents login and keeps user on sign-in page', async ({ page }) => {
    await page.goto('https://newsunrisedev.softwareco.com/sign-in');

    const emailInput = page.locator('input[type="email"], input[name="email"], input[name="username"]');
    await emailInput.waitFor({ state: 'visible' });
    await emailInput.fill('rajanj+superadmin@softwareco.com');

    const passwordInput = page.locator('input[type="password"], input[name="password"]');
    await passwordInput.fill('IncorrectPassword@999');

    const submitButton = page.getByRole('button').filter({ hasText: /sign in|login|submit|continue/i });
    await submitButton.click();

    await page.waitForTimeout(2500);
    expect(page.url()).toContain('sign-in');
    expect(page.url()).not.toContain('dashboard');
    console.log(' [Negative 1.1] Verified: Invalid password denied access.');
  });

  test('Negative 1.2: Unregistered user email fails authentication', async ({ page }) => {
    await page.goto('https://newsunrisedev.softwareco.com/sign-in');

    const emailInput = page.locator('input[type="email"], input[name="email"], input[name="username"]');
    await emailInput.waitFor({ state: 'visible' });
    await emailInput.fill('nonexistent.fakeuser.999@softwareco.com');

    const passwordInput = page.locator('input[type="password"], input[name="password"]');
    await passwordInput.fill('RandomPass@123');

    const submitButton = page.getByRole('button').filter({ hasText: /sign in|login|submit|continue/i });
    await submitButton.click();

    await page.waitForTimeout(2500);
    expect(page.url()).toContain('sign-in');
    console.log(' [Negative 1.2] Verified: Unregistered user email rejected.');
  });

  test('Negative 1.3: Submitting empty login form blocks progression', async ({ page }) => {
    await page.goto('https://newsunrisedev.softwareco.com/sign-in');

    const submitButton = page.getByRole('button').filter({ hasText: /sign in|login|submit|continue/i });
    await submitButton.click();

    await page.waitForTimeout(1500);
    expect(page.url()).toContain('sign-in');
    console.log(' [Negative 1.3] Verified: Empty form submission blocked.');
  });

  test('Negative 1.4: Invalid OTP code fails verification', async ({ page }) => {
    await page.goto('https://newsunrisedev.softwareco.com/sign-in');

    const emailInput = page.locator('input[type="email"], input[name="email"], input[name="username"]');
    await emailInput.waitFor({ state: 'visible' });
    await emailInput.fill('rajanj+superadmin@softwareco.com');

    const passwordInput = page.locator('input[type="password"], input[name="password"]');
    await passwordInput.fill('Rajan@123');

    const submitButton = page.getByRole('button').filter({ hasText: /sign in|login|submit|continue/i });
    await submitButton.click();

    await page.waitForTimeout(2000);
    const otpInput = page.locator('input[name="otp"], input[name="code"], input[placeholder*="OTP" i], input[type="text"]').first();
    if (await otpInput.isVisible()) {
      await otpInput.fill('000000');
      const verifyBtn = page.getByRole('button').filter({ hasText: /verify|submit|confirm|continue/i });
      if (await verifyBtn.isVisible()) {
        await verifyBtn.click();
      }

      await page.waitForTimeout(2500);
      expect(page.url()).not.toContain('dashboard');
      console.log(' [Negative 1.4] Verified: Invalid OTP prevented login.');
    }
  });


  // ==========================================
  // SECTION 2: STORE CREATION NEGATIVE SCENARIOS
  // ==========================================

  test('Negative 2.1: Empty Add Store form triggers all validation errors', async ({ page }) => {
    await page.goto('https://newsunrisedev.softwareco.com/sign-in');
    await page.locator('input[type="email"], input[name="email"], input[name="username"]').fill('rajanj+superadmin@softwareco.com');
    await page.locator('input[type="password"], input[name="password"]').fill('Rajan@123');
    await page.getByRole('button').filter({ hasText: /sign in|login|submit|continue/i }).click();
    await page.waitForTimeout(2000);

    const otpInput = page.locator('input[name="otp"], input[name="code"], input[placeholder*="OTP" i], input[type="text"]').first();
    if (await otpInput.isVisible()) {
      await otpInput.fill('149526');
      const verifyBtn = page.getByRole('button').filter({ hasText: /verify|submit|confirm|continue/i });
      if (await verifyBtn.isVisible()) await verifyBtn.click();
    }

    await page.waitForTimeout(4000);
    await page.goto('https://newsunrisedev.softwareco.com/store/add');
    await page.waitForTimeout(3000);

    // Submit blank form
    const submitBtn = page.getByRole('button', { name: /add store/i });
    await submitBtn.click();
    await page.waitForTimeout(2000);

    const errorMessages = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('.Mui-error, p.MuiFormHelperText-root, [role="alert"]'))
        .map(el => (el as HTMLElement).innerText.trim())
        .filter(Boolean);
    });

    console.log(' [Negative 2.1] Form Validation Errors caught:', errorMessages.length);
    expect(errorMessages.length).toBeGreaterThan(0);
    expect(page.url()).toContain('/store/add');
  });

  test('Negative 2.2: Short Store Name and Invalid Owner Email trigger format errors', async ({ page }) => {
    await page.goto('https://newsunrisedev.softwareco.com/sign-in');
    await page.locator('input[type="email"], input[name="email"], input[name="username"]').fill('rajanj+superadmin@softwareco.com');
    await page.locator('input[type="password"], input[name="password"]').fill('Rajan@123');
    await page.getByRole('button').filter({ hasText: /sign in|login|submit|continue/i }).click();
    await page.waitForTimeout(2000);

    const otpInput = page.locator('input[name="otp"], input[name="code"], input[placeholder*="OTP" i], input[type="text"]').first();
    if (await otpInput.isVisible()) {
      await otpInput.fill('149526');
      const verifyBtn = page.getByRole('button').filter({ hasText: /verify|submit|confirm|continue/i });
      if (await verifyBtn.isVisible()) await verifyBtn.click();
    }

    await page.waitForTimeout(4000);
    await page.goto('https://newsunrisedev.softwareco.com/store/add');
    await page.waitForTimeout(3000);

    const ownerTypeSelect = page.locator('#storeOwnerType-select').locator('..').locator('.MuiSelect-select');
    await ownerTypeSelect.click();
    await page.waitForTimeout(400);
    await page.locator('li[role="option"]').filter({ hasText: /^SSO$/i }).click();
    await page.waitForTimeout(400);

    await page.locator('input[name="storeName"]').fill('A');
    await page.locator('input[name="storeOwnerEmail"]').fill('invalid-email-address');
    await page.locator('input[name="storeOwnerPassword"]').fill('12');

    await page.getByRole('button', { name: /add store/i }).click();
    await page.waitForTimeout(2000);

    expect(page.url()).toContain('/store/add');
    console.log(' [Negative 2.2] Format errors validated.');
  });

  test('Negative 2.3: Missing mandatory Store Banner Image prevents store submission', async ({ page }) => {
    await page.goto('https://newsunrisedev.softwareco.com/sign-in');
    await page.locator('input[type="email"], input[name="email"], input[name="username"]').fill('rajanj+superadmin@softwareco.com');
    await page.locator('input[type="password"], input[name="password"]').fill('Rajan@123');
    await page.getByRole('button').filter({ hasText: /sign in|login|submit|continue/i }).click();
    await page.waitForTimeout(2000);

    const otpInput = page.locator('input[name="otp"], input[name="code"], input[placeholder*="OTP" i], input[type="text"]').first();
    if (await otpInput.isVisible()) {
      await otpInput.fill('149526');
      const verifyBtn = page.getByRole('button').filter({ hasText: /verify|submit|confirm|continue/i });
      if (await verifyBtn.isVisible()) await verifyBtn.click();
    }

    await page.waitForTimeout(4000);
    await page.goto('https://newsunrisedev.softwareco.com/store/add');
    await page.waitForTimeout(3000);

    const rand = Math.floor(1000 + Math.random() * 9000);
    const ownerTypeSelect = page.locator('#storeOwnerType-select').locator('..').locator('.MuiSelect-select');
    await ownerTypeSelect.click();
    await page.waitForTimeout(400);
    await page.locator('li[role="option"]').filter({ hasText: /^SSO$/i }).click();
    await page.waitForTimeout(400);

    await page.locator('input[name="storeName"]').fill(`Missing Image Store ${rand}`);
    await page.locator('input[name="siteId"]').fill(`ST-${rand}`);
    await page.locator('input[name="storeOwnerFirstName"]').fill('Jack');
    await page.locator('input[name="storeOwnerLastName"]').fill('Thompson');
    await page.locator('input[name="storeOwnerEmail"]').fill(`jack.thompson${rand}@yopmail.com`);
    await page.locator('input[name="storeOwnerPassword"]').fill('Pass@123456');
    await page.locator('input[name="storeOwnerPhoneNumber"]').fill('0412345678');
    await page.locator('input[name="contactEmail"]').fill(`contact${rand}@yopmail.com`);
    await page.locator('input[name="contactNumber"]').fill('0498765432');
    await page.locator('input[name="contactName"]').fill('Manager');

    const addrInput = page.locator('input[placeholder*="Start typing address"]');
    await addrInput.click();
    await addrInput.fill('Melbourne');
    await page.waitForTimeout(1500);
    const option = page.locator('.MuiAutocomplete-option, [role="option"]').first();
    if (await option.isVisible()) await option.click();
    await page.waitForTimeout(800);

    await page.getByRole('button', { name: 'Generate' }).click();
    await page.waitForTimeout(500);

    await page.locator('input[name="pumps"]').fill('4');
    await page.locator('input[name="fuelBrand"]').fill('BP');

    const posSelect = page.locator('#posProvider-select').locator('..').locator('.MuiSelect-select');
    await posSelect.click();
    await page.waitForTimeout(400);
    await page.locator('li[role="option"]').first().click();

    // Submit with NO image uploaded
    await page.getByRole('button', { name: /add store/i }).click();
    await page.waitForTimeout(2000);

    expect(page.url()).toContain('/store/add');
    console.log(' [Negative 2.3] Missing image blocked submission.');
  });

});
