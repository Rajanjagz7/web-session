const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  page.on('console', msg => console.log(`[PAGE LOG] ${msg.type()}: ${msg.text()}`));
  page.on('response', async res => {
    if (res.url().includes('api')) {
      const status = res.status();
      const method = res.request().method();
      let bodyText = '';
      if (method !== 'GET') {
        bodyText = await res.text().catch(() => '');
      }
      console.log(`[NET RES] ${status} ${method} ${res.url()} ${bodyText.substring(0, 120)}`);
    }
  });

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  const searchInput = page.getByPlaceholder('Search Jobs...');
  await searchInput.fill('M8N000380');
  await page.waitForTimeout(1500);

  const row = page.locator('tr').filter({ hasText: 'M8N000380' }).first();
  const eyeIcon = row.locator('.cursor-pointer').first();
  await eyeIcon.click();
  await page.waitForTimeout(2000);

  // Check if energy bill is already attached or upload if not
  const fileInput = page.locator('input[type="file"].upload-input');
  if (await fileInput.count() > 0) {
    const testImagePath = path.resolve(__dirname, 'test-images/energy-bill-coastal-enterprises.png');
    console.log('Attaching energy bill image...');
    await fileInput.setInputFiles(testImagePath);
    await page.waitForTimeout(4000);
  } else {
    console.log('Energy bill already attached!');
  }

  // Check Plumber
  const drawer = page.locator('.drawer-content, [role="dialog"]').first();
  const plumberSelected = await drawer.locator('div:has-text("Dhruti Patel")').count() > 0;
  console.log('Plumber selected already?:', plumberSelected);
  if (!plumberSelected) {
    console.log('Selecting Plumber...');
    const plumberPlaceholder = drawer.locator('div').filter({ hasText: /^Select Plumber$/ }).last();
    if (await plumberPlaceholder.isVisible()) {
      await plumberPlaceholder.click();
    } else {
      await drawer.locator('.select__control').first().click();
    }
    await page.waitForTimeout(1000);
    await page.locator('[class*="-option"]').filter({ hasText: 'Dhruti Patel' }).first().click();
    await page.waitForTimeout(1000);
  }

  // Click "No" for electrical wiring work
  console.log('Clicking No button...');
  const noBtn = drawer.getByRole('button', { name: 'No' });
  await noBtn.click();
  await page.waitForTimeout(1000);

  await page.screenshot({ path: 'm8n000380-pre-send.png' });

  // Click Send
  console.log('Clicking Send button...');
  const sendBtn = drawer.getByRole('button', { name: 'Send' });
  await sendBtn.click();
  await page.waitForTimeout(5000);

  await page.screenshot({ path: 'm8n000380-post-send.png' });
  console.log('Saved m8n000380-post-send.png. URL:', page.url());

  // Check job in jobs table
  await page.waitForTimeout(2000);
  const updatedStatus = await page.locator('tr').filter({ hasText: 'M8N000380' }).innerText();
  console.log('Updated row text:', updatedStatus);

  await browser.close();
})();
