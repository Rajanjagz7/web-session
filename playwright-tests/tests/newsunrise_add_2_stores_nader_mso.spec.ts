import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('New Sunrise - Add stores under Nader (MSO)', () => {
  test.setTimeout(180_000); // 3 minutes overall timeout

  test('Login and complete all available sites for existing MSO owner Nader, set Active', async ({ page }) => {
    page.on('response', async (response) => {
      if (response.url().includes('/api/store/add-store')) {
        const status = response.status();
        try {
          const body = await response.text();
          console.log(`[API add-store] Status: ${status} | Body: ${body}`);
        } catch (e) {
          console.log(`[API add-store] Status: ${status}`);
        }
      }
    });

    // ==========================================
    // 1. Login with OTP Bypass
    // ==========================================
    console.log('Navigating to sign-in page...');
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
      await otpInput.fill('149526');
      const verifyBtn = page.getByRole('button').filter({ hasText: /verify|submit|confirm|continue/i });
      if (await verifyBtn.isVisible()) {
        await verifyBtn.click();
      }
    }

    await page.waitForTimeout(4000);
    expect(page.url()).not.toContain('sign-in');
    console.log('Successfully logged in to New Sunrise MSO Dashboard.');

    const fixtureImagePath = path.join(__dirname, 'fixtures', 'sample_store.png');
    const MSO_OWNER_NAME = 'Nader';

    // Nader has exactly 2 unused sites available: "NSRwoods" (SH7778) and "Nader stores" (SH7777).
    // Each site can only be completed into a store once, so we loop until no sites remain (max 2).
    const cityOptions = ['Chatswood NSW, Australia', 'Chatswood NSW, Australia'];
    const fuelBrands = ['BP', 'Shell'];
    const posProviders = ['Beacon', 'Edge'];
    const pumpsOptions = ['6', '8'];

    let storeNum = 0;
    const MAX_STORES = 2;

    while (storeNum < MAX_STORES) {
      // Navigate to Add Store page fresh each time
      await page.goto('https://newsunrisedev.softwareco.com/store/add');
      await page.waitForTimeout(2500);

      // A. Upload Images
      const fileInputs = page.locator('input[type="file"]');
      const fileCount = await fileInputs.count();
      for (let f = 0; f < fileCount; f++) {
        await fileInputs.nth(f).setInputFiles(fixtureImagePath);
      }
      await page.waitForTimeout(1000);

      // B. Select Owner Type = MSO
      const ownerTypeSelect = page.locator('#storeOwnerType-select').locator('..').locator('.MuiSelect-select');
      await ownerTypeSelect.click();
      await page.waitForTimeout(400);
      await page.locator('li[role="option"]').filter({ hasText: /^MSO$/i }).click();
      await page.waitForTimeout(800);

      // C. Select existing MSO owner "Nader" via Group Name autocomplete
      const groupNameInput = page.locator('#rhf-autocomplete-storeOwnerId');
      await groupNameInput.click();
      await groupNameInput.fill(MSO_OWNER_NAME);
      await page.waitForTimeout(1200);
      await page.locator('li[role="option"], .MuiAutocomplete-option').filter({ hasText: MSO_OWNER_NAME }).first().click();
      await page.waitForTimeout(800);

      // D. Select the next available Site (consumes one of Nader's remaining sites)
      const selectSiteInput = page.locator('#rhf-autocomplete-ownerIdentifierStoreRelationId');
      await selectSiteInput.click();
      await page.waitForTimeout(1200);
      const siteOptions = await page.locator('li[role="option"], .MuiAutocomplete-option').allTextContents();
      console.log(`Remaining sites for ${MSO_OWNER_NAME}: ${JSON.stringify(siteOptions)}`);
      if (siteOptions.length === 0) {
        console.log('No more sites available for Nader - stopping.');
        break;
      }
      const chosenSiteName = siteOptions[0];
      await page.locator('li[role="option"], .MuiAutocomplete-option').first().click();
      await page.waitForTimeout(500);

      const storeName = await page.locator('input[name="storeName"]').inputValue();
      const siteId = await page.locator('input[name="siteId"]').inputValue();
      console.log(`\n========================================`);
      console.log(`Completing store ${storeNum + 1}: "${storeName}" (Site ID: ${siteId}) under MSO owner ${MSO_OWNER_NAME}`);
      console.log(`========================================`);

      // E. Toggle Active ON at creation time
      const activeSwitch = page.locator('#isActive-switch');
      if (!(await activeSwitch.isChecked())) {
        await activeSwitch.click();
      }
      await page.waitForTimeout(300);
      expect(await activeSwitch.isChecked()).toBeTruthy();

      // F. Contact Details
      const randSuffix = Math.floor(100 + Math.random() * 900);
      await page.locator('input[name="contactEmail"]').fill(`contact.nader${randSuffix}@yopmail.com`);
      await page.locator('input[name="contactNumber"]').fill(`0498${Math.floor(100000 + Math.random() * 900000)}`);
      await page.locator('input[name="contactName"]').fill(MSO_OWNER_NAME);

      // G. Address with Autocomplete
      const city = cityOptions[storeNum] || 'Sydney NSW, Australia';
      const addrInput = page.locator('input[placeholder*="Start typing address"]');
      await addrInput.click();
      await addrInput.fill(city);
      await page.waitForTimeout(1500);
      const optionLocator = page.locator('.MuiAutocomplete-option, [role="option"]').first();
      await optionLocator.waitFor({ state: 'visible', timeout: 6000 });
      await optionLocator.click();
      await page.waitForTimeout(1000);

      // H. Generate API Key
      const genBtn = page.getByRole('button', { name: 'Generate' });
      await genBtn.click();
      await page.waitForTimeout(500);

      // I. Fuel & Pumps
      await page.locator('input[name="pumps"]').fill(pumpsOptions[storeNum] || '6');
      await page.locator('input[name="fuelBrand"]').fill(fuelBrands[storeNum] || 'BP');

      // J. POS Provider
      const posProvider = posProviders[storeNum] || 'Beacon';
      const posSelect = page.locator('#posProvider-select').locator('..').locator('.MuiSelect-select');
      await posSelect.click();
      await page.waitForTimeout(400);
      await page.locator('li[role="option"]').filter({ hasText: posProvider }).first().click();
      await page.waitForTimeout(500);

      // K. Submit Form & Wait for success
      await page.getByRole('button', { name: 'Add Store' }).click();
      await page.waitForURL(url => url.pathname === '/store' || url.pathname.endsWith('/store'), { timeout: 20_000 });
      console.log(`Store "${chosenSiteName}" successfully completed and set Active!`);
      await page.waitForTimeout(2000);

      storeNum++;
    }

    console.log(`\n======================================================`);
    console.log(`Completed ${storeNum} store(s) under MSO owner ${MSO_OWNER_NAME}, all set Active.`);
    console.log(`======================================================`);
  });
});
