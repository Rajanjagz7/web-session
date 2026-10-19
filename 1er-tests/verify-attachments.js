const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  const jobs = ['M8N000380', 'M8N000378', 'M8N000379', 'M8N000377'];
  for (const j of jobs) {
    const searchInput = page.getByPlaceholder('Search Jobs...');
    await searchInput.fill(j);
    await page.waitForTimeout(1000);

    const row = page.locator('tr').filter({ hasText: j }).first();
    const eyeIcon = row.locator('.cursor-pointer').first();
    await eyeIcon.click();
    await page.waitForTimeout(2000);

    const drawer = page.locator('.drawer-content, [role="dialog"]').first();
    const text = await drawer.innerText();
    const hasAttached = text.includes('Attached') || text.includes('attached');
    const billName = text.match(/[a-zA-Z0-9_\-]+\.(?:png|jpg|pdf)/gi);
    console.log(`Job ${j}: hasAttached=${hasAttached}, files=${billName ? billName.join(', ') : 'none'}`);

    await page.keyboard.press('Escape');
    await page.waitForTimeout(1000);
  }

  await browser.close();
})();
