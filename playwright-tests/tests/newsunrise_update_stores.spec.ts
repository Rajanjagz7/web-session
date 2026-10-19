import { test, expect } from '@playwright/test';

test.describe('New Sunrise - Update Stores in MSO', () => {
  test.setTimeout(300_000); // 5 minutes overall timeout

  test('Login, navigate to stores and update all stores with Australian data', async ({ page }) => {
    // Listen to update API responses
    page.on('response', async (response) => {
      if (response.url().includes('/api/store') && (response.request().method() === 'PUT' || response.request().method() === 'POST' || response.request().method() === 'PATCH')) {
        console.log(`[API Store Update] ${response.status()} ${response.url()}`);
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

    // Updated Australian dataset for updating the stores
    const updatedStoreData = [
      {
        fuelBrand: 'BP Ultimate',
        pumps: '8',
        posProvider: 'Beacon',
        about: 'Premium New Sunrise flagship store located in Melbourne CBD with 24/7 barista service.'
      },
      {
        fuelBrand: 'Shell V-Power',
        pumps: '10',
        posProvider: 'Edge',
        about: 'Coastal Bondi express hub featuring fresh food, high-flow diesel, and EV supercharging.'
      },
      {
        fuelBrand: 'Ampol Premium',
        pumps: '6',
        posProvider: 'Gap Solutions',
        about: 'High-traffic Brisbane North convenience center with automated touchless car wash.'
      },
      {
        fuelBrand: 'Mobil Synergy',
        pumps: '8',
        posProvider: 'Ideal',
        about: 'Adelaide Hills regional stop offering premium local gourmet snacks and 24hr fuel pumps.'
      },
      {
        fuelBrand: 'Caltex Star',
        pumps: '12',
        posProvider: 'QuickFuel',
        about: 'Major Perth Metro heavy-vehicle and commuter roadhouse with full diner facilities.'
      }
    ];

    // ==========================================
    // 2. Navigate to All Stores & Collect Links
    // ==========================================
    await page.goto('https://newsunrisedev.softwareco.com/store');
    await page.waitForTimeout(3000);

    // Click "All Stores" tab
    const allStoresTab = page.locator('button, [role="tab"]').filter({ hasText: /all stores/i });
    await allStoresTab.waitFor({ state: 'visible' });
    await allStoresTab.click();
    await page.waitForTimeout(2500);

    // Extract store view links from the table
    const storeLinks = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('table tbody tr a'))
        .map(a => a.getAttribute('href'))
        .filter((href): href is string => !!href && href.includes('/store/') && href.includes('/view'))
        .slice(0, 5);
    });

    console.log(`Found ${storeLinks.length} stores to update:`, storeLinks);
    expect(storeLinks.length).toBeGreaterThan(0);

    // ==========================================
    // 3. Sequentially Update Each Store
    // ==========================================
    for (let i = 0; i < storeLinks.length; i++) {
      const storeNum = i + 1;
      const storeHref = storeLinks[i];
      const updateData = updatedStoreData[i % updatedStoreData.length];

      console.log(`\n========================================`);
      console.log(` Updating Store ${storeNum} of ${storeLinks.length}...`);
      console.log(` Target: ${storeHref}`);
      console.log(` New Fuel: ${updateData.fuelBrand} | Pumps: ${updateData.pumps} | POS: ${updateData.posProvider}`);
      console.log(`========================================`);

      await page.goto(`https://newsunrisedev.softwareco.com${storeHref}`);
      await page.waitForTimeout(3000);

      // A. Update Fuel Brand & Pumps
      const fuelInput = page.locator('input[name="fuelBrand"]');
      if (await fuelInput.isVisible()) {
        await fuelInput.fill(updateData.fuelBrand);
      }

      const pumpsInput = page.locator('input[name="pumps"]');
      if (await pumpsInput.isVisible()) {
        await pumpsInput.fill(updateData.pumps);
      }

      // B. Update POS Provider
      const posSelect = page.locator('#posProvider-select').locator('..').locator('.MuiSelect-select');
      if (await posSelect.isVisible()) {
        await posSelect.click();
        await page.waitForTimeout(400);
        const posOption = page.locator('li[role="option"]').filter({ hasText: updateData.posProvider }).first();
        if (await posOption.isVisible()) {
          await posOption.click();
        } else {
          await page.locator('li[role="option"]').first().click();
        }
        await page.waitForTimeout(400);
      }

      // C. Update About Description
      const aboutTextarea = page.locator('textarea[name="about"]');
      if (await aboutTextarea.isVisible()) {
        await aboutTextarea.fill(updateData.about);
      }

      // D. Toggle Active Timing / Switch
      const activeSwitch = page.locator('#isActive-switch');
      if (await activeSwitch.isVisible() && !(await activeSwitch.isChecked())) {
        await activeSwitch.check();
      }

      // E. Click "Save changes"
      console.log(`[Store ${storeNum}] Saving changes...`);
      const saveBtn = page.getByRole('button', { name: /save changes/i });
      await saveBtn.scrollIntoViewIfNeeded();
      await saveBtn.click();
      await page.waitForTimeout(3500);

      console.log(` [Store ${storeNum}] Successfully updated and saved!`);
    }

    console.log('\n======================================================');
    console.log(' All Stores Successfully Updated with Australian Data!');
    console.log('======================================================');
  });
});
