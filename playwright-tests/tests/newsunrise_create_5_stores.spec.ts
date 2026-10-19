import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('New Sunrise - Create 5 Stores in MSO', () => {
  test.setTimeout(300_000); // 5 minutes overall timeout

  test('Login and create 5 stores with authentic Australian names', async ({ page }) => {
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
    console.log(' Successfully logged in to New Sunrise MSO Dashboard.');

    const fixtureImagePath = path.join(__dirname, 'fixtures', 'sample_store.png');

    // Proper Australian Stores & People Dataset
    const storeProfiles = [
      {
        storeBaseName: 'Sunrise Express Melbourne Central',
        ownerFirstName: 'Liam',
        ownerLastName: 'O\'Connor',
        contactName: 'Jack Thompson',
        city: 'Melbourne VIC, Australia',
        fuelBrand: 'BP',
        posProvider: 'Beacon',
        pumps: '6'
      },
      {
        storeBaseName: 'Sunrise Fuel Bondi Junction',
        ownerFirstName: 'Oliver',
        ownerLastName: 'Smith',
        contactName: 'Charlotte Taylor',
        city: 'Sydney NSW, Australia',
        fuelBrand: 'Shell',
        posProvider: 'Edge',
        pumps: '8'
      },
      {
        storeBaseName: 'Sunrise QuickStop Brisbane North',
        ownerFirstName: 'Noah',
        ownerLastName: 'Wilson',
        contactName: 'Matilda Kelly',
        city: 'Brisbane QLD, Australia',
        fuelBrand: 'Ampol',
        posProvider: 'Gap Solutions',
        pumps: '4'
      },
      {
        storeBaseName: 'Sunrise Petroleum Adelaide Hills',
        ownerFirstName: 'Lucas',
        ownerLastName: 'Davies',
        contactName: 'Cooper Martin',
        city: 'Adelaide SA, Australia',
        fuelBrand: 'Mobil',
        posProvider: 'Ideal',
        pumps: '6'
      },
      {
        storeBaseName: 'Sunrise Roadhouse Perth Metro',
        ownerFirstName: 'Harrison',
        ownerLastName: 'Brown',
        contactName: 'Ruby Clarke',
        city: 'Perth WA, Australia',
        fuelBrand: 'Caltex',
        posProvider: 'QuickFuel',
        pumps: '10'
      }
    ];

    // ==========================================
    // 2. Loop to Create 5 Stores
    // ==========================================
    for (let i = 0; i < storeProfiles.length; i++) {
      const storeNum = i + 1;
      const profile = storeProfiles[i];
      const randNum = Math.floor(100000 + Math.random() * 900000);
      const storeName = `${profile.storeBaseName} ${randNum.toString().slice(-3)}`;
      const siteId = `AU-${randNum.toString().slice(-4)}`;
      const cleanOwnerLast = profile.ownerLastName.replace(/[^a-zA-Z]/g, '');

      console.log(`\n========================================`);
      console.log(` Creating Store ${storeNum} of 5: ${storeName}`);
      console.log(` Owner: ${profile.ownerFirstName} ${profile.ownerLastName} | Contact: ${profile.contactName}`);
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

      // B. Select Owner Type = SSO
      console.log(`[Store ${storeNum}] Selecting Owner Type (SSO)...`);
      const ownerTypeSelect = page.locator('#storeOwnerType-select').locator('..').locator('.MuiSelect-select');
      await ownerTypeSelect.click();
      await page.waitForTimeout(400);
      await page.locator('li[role="option"]').filter({ hasText: /^SSO$/i }).click();
      await page.waitForTimeout(400);

      // C. Fill Store Info
      console.log(`[Store ${storeNum}] Setting Store Name: "${storeName}" & Site ID: "${siteId}"...`);
      await page.locator('input[name="storeName"]').fill(storeName);
      await page.locator('input[name="siteId"]').fill(siteId);

      // D. Fill Australian Owner Details
      console.log(`[Store ${storeNum}] Setting Owner: ${profile.ownerFirstName} ${profile.ownerLastName}...`);
      await page.locator('input[name="storeOwnerFirstName"]').fill(profile.ownerFirstName);
      await page.locator('input[name="storeOwnerLastName"]').fill(profile.ownerLastName);
      await page.locator('input[name="storeOwnerEmail"]').fill(`${profile.ownerFirstName.toLowerCase()}.${cleanOwnerLast.toLowerCase()}${randNum.toString().slice(-3)}@yopmail.com`);

      // Select Gender (Male)
      const genderSelect = page.locator('#storeOwnerGender-select').locator('..').locator('.MuiSelect-select');
      if (await genderSelect.isVisible()) {
        await genderSelect.click();
        await page.waitForTimeout(400);
        await page.locator('li[role="option"]').first().click();
        await page.waitForTimeout(400);
      }

      await page.locator('input[name="storeOwnerPassword"]').fill('Pass@123456');
      await page.locator('input[name="storeOwnerPhoneNumber"]').fill(`0412${Math.floor(100000 + Math.random() * 900000)}`);

      // E. Australian Contact Details
      console.log(`[Store ${storeNum}] Setting Contact: ${profile.contactName}...`);
      await page.locator('input[name="contactEmail"]').fill(`contact.${cleanOwnerLast.toLowerCase()}${randNum.toString().slice(-3)}@yopmail.com`);
      await page.locator('input[name="contactNumber"]').fill(`0498${Math.floor(100000 + Math.random() * 900000)}`);
      await page.locator('input[name="contactName"]').fill(profile.contactName);

      // F. Address with Autocomplete
      console.log(`[Store ${storeNum}] Selecting Address: ${profile.city}...`);
      const addrInput = page.locator('input[placeholder*="Start typing address"]');
      await addrInput.click();
      await addrInput.fill(profile.city);
      await page.waitForTimeout(1500);

      const optionLocator = page.locator('.MuiAutocomplete-option, [role="option"]').first();
      await optionLocator.waitFor({ state: 'visible', timeout: 6000 });
      await optionLocator.click();
      await page.waitForTimeout(1000);

      // G. Generate API Key
      console.log(`[Store ${storeNum}] Generating API Key...`);
      const genBtn = page.getByRole('button', { name: 'Generate' });
      await genBtn.click();
      await page.waitForTimeout(500);

      // H. Fuel & Pumps
      await page.locator('input[name="pumps"]').fill(profile.pumps);
      await page.locator('input[name="fuelBrand"]').fill(profile.fuelBrand);

      // I. POS Provider
      console.log(`[Store ${storeNum}] Selecting POS Provider (${profile.posProvider})...`);
      const posSelect = page.locator('#posProvider-select').locator('..').locator('.MuiSelect-select');
      await posSelect.click();
      await page.waitForTimeout(400);
      await page.locator('li[role="option"]').filter({ hasText: profile.posProvider }).first().click();
      await page.waitForTimeout(500);

      // J. Submit Form & Wait for success
      console.log(`[Store ${storeNum}] Submitting Add Store form...`);
      await page.getByRole('button', { name: 'Add Store' }).click();

      // Wait up to 20s for navigation to /store
      await page.waitForURL(url => url.pathname === '/store' || url.pathname.endsWith('/store'), { timeout: 20_000 });
      console.log(` [Store ${storeNum}] Successfully created! Redirected to /store`);
      await page.waitForTimeout(2000);
    }

    console.log('\n======================================================');
    console.log(' All 5 Australian Stores Created Successfully in MSO!');
    console.log('======================================================');
  });
});
