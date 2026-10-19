import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('New Sunrise - Add 10 Stores under Grace Robinson (MSO)', () => {
  test.setTimeout(600_000); // 10 minutes overall timeout

  test('Login and add 10 active stores under existing MSO owner Grace Robinson', async ({ page }) => {
    // Listen to network responses for store creation
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
    const MSO_OWNER_NAME = 'Grace Robinson';

    // Varied Australian store profiles - all placed under the same MSO owner (Grace Robinson)
    const storeProfiles = [
      { storeBaseName: 'Sunrise Fuel Parramatta', city: 'Parramatta NSW, Australia', fuelBrand: 'BP', posProvider: 'Beacon', pumps: '6' },
      { storeBaseName: 'Sunrise Express Geelong', city: 'Geelong VIC, Australia', fuelBrand: 'Shell', posProvider: 'Edge', pumps: '8' },
      { storeBaseName: 'Sunrise QuickStop Toowoomba', city: 'Toowoomba QLD, Australia', fuelBrand: 'Ampol', posProvider: 'Gap Solutions', pumps: '4' },
      { storeBaseName: 'Sunrise Petroleum Mount Gambier', city: 'Mount Gambier SA, Australia', fuelBrand: 'Mobil', posProvider: 'Ideal', pumps: '6' },
      { storeBaseName: 'Sunrise Roadhouse Mandurah', city: 'Mandurah WA, Australia', fuelBrand: 'Caltex', posProvider: 'QuickFuel', pumps: '10' },
      { storeBaseName: 'Sunrise Fuel Newcastle', city: 'Newcastle NSW, Australia', fuelBrand: 'BP', posProvider: 'Infinity', pumps: '5' },
      { storeBaseName: 'Sunrise Express Ballarat', city: 'Ballarat VIC, Australia', fuelBrand: 'Shell', posProvider: 'Independent Solutions', pumps: '7' },
      { storeBaseName: 'Sunrise QuickStop Cairns', city: 'Cairns QLD, Australia', fuelBrand: 'Ampol', posProvider: 'Beacon', pumps: '4' },
      { storeBaseName: 'Sunrise Petroleum Whyalla', city: 'Whyalla SA, Australia', fuelBrand: 'Mobil', posProvider: 'Edge', pumps: '6' },
      { storeBaseName: 'Sunrise Roadhouse Bunbury', city: 'Bunbury WA, Australia', fuelBrand: 'Caltex', posProvider: 'Gap Solutions', pumps: '9' },
    ];

    // ==========================================
    // 2. Loop to Create 10 Stores under Grace Robinson (MSO)
    // ==========================================
    for (let i = 0; i < storeProfiles.length; i++) {
      const storeNum = i + 1;
      const profile = storeProfiles[i];
      const randNum = Math.floor(100000 + Math.random() * 900000);
      const storeName = `${profile.storeBaseName} ${randNum.toString().slice(-3)}`;
      const siteId = `AU-${randNum.toString().slice(-4)}`;

      console.log(`\n========================================`);
      console.log(`Creating Store ${storeNum} of 10: ${storeName} (MSO owner: ${MSO_OWNER_NAME})`);
      console.log(`========================================`);

      // Navigate to Add Store page
      await page.goto('https://newsunrisedev.softwareco.com/store/add');
      await page.waitForTimeout(2500);

      // A. Upload Images
      console.log(`[Store ${storeNum}] Uploading store images...`);
      const fileInputs = page.locator('input[type="file"]');
      const fileCount = await fileInputs.count();
      for (let f = 0; f < fileCount; f++) {
        await fileInputs.nth(f).setInputFiles(fixtureImagePath);
      }
      await page.waitForTimeout(1500);

      // B. Select Owner Type = MSO
      console.log(`[Store ${storeNum}] Selecting Owner Type (MSO)...`);
      const ownerTypeSelect = page.locator('#storeOwnerType-select').locator('..').locator('.MuiSelect-select');
      await ownerTypeSelect.click();
      await page.waitForTimeout(400);
      await page.locator('li[role="option"]').filter({ hasText: /^MSO$/i }).click();
      await page.waitForTimeout(800);

      // C. Select existing MSO owner "Grace Robinson" via Group Name autocomplete
      console.log(`[Store ${storeNum}] Selecting Group Name (existing MSO owner): ${MSO_OWNER_NAME}...`);
      const groupNameInput = page.locator('#rhf-autocomplete-storeOwnerId');
      await groupNameInput.click();
      await groupNameInput.fill('Grace');
      await page.waitForTimeout(1200);
      await page.locator('li[role="option"], .MuiAutocomplete-option').filter({ hasText: MSO_OWNER_NAME }).first().click();
      await page.waitForTimeout(400);

      // D. Fill Store Info
      console.log(`[Store ${storeNum}] Setting Store Name: "${storeName}" & Site ID: "${siteId}"...`);
      await page.locator('input[name="storeName"]').fill(storeName);
      await page.locator('input[name="siteId"]').fill(siteId);

      // E. Toggle Active ON at creation time
      console.log(`[Store ${storeNum}] Setting store Active...`);
      const activeSwitch = page.locator('#isActive-switch');
      if (!(await activeSwitch.isChecked())) {
        await activeSwitch.click();
      }
      await page.waitForTimeout(300);
      expect(await activeSwitch.isChecked()).toBeTruthy();

      // F. Australian Contact Details
      const randSuffix = randNum.toString().slice(-3);
      console.log(`[Store ${storeNum}] Setting Contact details...`);
      await page.locator('input[name="contactEmail"]').fill(`contact.grace${randSuffix}@yopmail.com`);
      await page.locator('input[name="contactNumber"]').fill(`0498${Math.floor(100000 + Math.random() * 900000)}`);
      await page.locator('input[name="contactName"]').fill(MSO_OWNER_NAME);

      // G. Address with Autocomplete
      console.log(`[Store ${storeNum}] Selecting Address: ${profile.city}...`);
      const addrInput = page.locator('input[placeholder*="Start typing address"]');
      await addrInput.click();
      await addrInput.fill(profile.city);
      await page.waitForTimeout(1500);

      const optionLocator = page.locator('.MuiAutocomplete-option, [role="option"]').first();
      await optionLocator.waitFor({ state: 'visible', timeout: 6000 });
      await optionLocator.click();
      await page.waitForTimeout(1000);

      // H. Generate API Key
      console.log(`[Store ${storeNum}] Generating API Key...`);
      const genBtn = page.getByRole('button', { name: 'Generate' });
      await genBtn.click();
      await page.waitForTimeout(500);

      // I. Fuel & Pumps
      await page.locator('input[name="pumps"]').fill(profile.pumps);
      await page.locator('input[name="fuelBrand"]').fill(profile.fuelBrand);

      // J. POS Provider
      console.log(`[Store ${storeNum}] Selecting POS Provider (${profile.posProvider})...`);
      const posSelect = page.locator('#posProvider-select').locator('..').locator('.MuiSelect-select');
      await posSelect.click();
      await page.waitForTimeout(400);
      await page.locator('li[role="option"]').filter({ hasText: profile.posProvider }).first().click();
      await page.waitForTimeout(500);

      // K. Submit Form & Wait for success
      console.log(`[Store ${storeNum}] Submitting Add Store form...`);
      await page.getByRole('button', { name: 'Add Store' }).click();

      // Wait up to 20s for navigation to /store
      await page.waitForURL(url => url.pathname === '/store' || url.pathname.endsWith('/store'), { timeout: 20_000 });
      console.log(`[Store ${storeNum}] Successfully created and active! Redirected to /store`);
      await page.waitForTimeout(2000);
    }

    console.log('\n======================================================');
    console.log('All 10 stores created and set Active under MSO owner Grace Robinson!');
    console.log('======================================================');
  });
});
