const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  const loadedScripts = [];
  page.on('response', resp => {
    const url = resp.url();
    if (url.includes('.js')) {
      loadedScripts.push(url);
    }
  });

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');
  await page.waitForTimeout(3000);

  // Open job drawer or job view
  const searchInput = page.getByPlaceholder('Search Jobs...');
  await searchInput.fill('M8N000380');
  await page.waitForTimeout(1500);

  const row = page.locator('tr').filter({ hasText: 'M8N000380' }).first();
  const eyeIcon = row.locator('.cursor-pointer').first();
  await eyeIcon.click();
  await page.waitForTimeout(3000);

  console.log('Loaded scripts:', loadedScripts);

  // Check each loaded script for nomination_signed
  for (const scriptUrl of loadedScripts) {
    const text = await page.evaluate(async (u) => {
      try {
        const r = await fetch(u);
        return await r.text();
      } catch (e) {
        return '';
      }
    }, scriptUrl);

    if (text.includes('nomination_signed')) {
      console.log(`FOUND nomination_signed in ${scriptUrl}!`);
      let idx = text.indexOf('nomination_signed');
      console.log(text.substring(Math.max(0, idx - 150), Math.min(text.length, idx + 400)));
    }
    if (text.includes('photos_started') || text.includes('photos-started')) {
      console.log(`FOUND photos_started in ${scriptUrl}!`);
      let idx = text.indexOf('photos_started') !== -1 ? text.indexOf('photos_started') : text.indexOf('photos-started');
      console.log(text.substring(Math.max(0, idx - 150), Math.min(text.length, idx + 400)));
    }
  }

  await browser.close();
})();
