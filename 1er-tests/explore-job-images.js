const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  page.on('console', msg => console.log(`[PAGE LOG] ${msg.type()}: ${msg.text()}`));
  page.on('response', res => {
    if (res.url().includes('api') && res.request().method() !== 'GET') {
      console.log(`[NET RES] ${res.status()} ${res.url()}`);
    }
  });

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  console.log('Logged in. Current URL:', page.url());

  // Search for M8N000380
  const searchInput = page.getByPlaceholder('Search Jobs...');
  await searchInput.fill('M8N000380');
  await page.waitForTimeout(1500);

  // Take screenshot of search result
  await page.screenshot({ path: 'job-search-result.png' });
  console.log('Saved job-search-result.png');

  // Check action icons/buttons on the row
  const row = page.locator('tr').filter({ hasText: 'M8N000380' }).first();
  const actionElements = await row.locator('button, a, svg, [role="button"]').all();
  console.log(`Found ${actionElements.length} interactive elements in row`);
  for (let i = 0; i < actionElements.length; i++) {
    const el = actionElements[i];
    const tag = await el.evaluate(e => e.tagName);
    const title = await el.getAttribute('title').catch(() => null);
    const ariaLabel = await el.getAttribute('aria-label').catch(() => null);
    const href = await el.getAttribute('href').catch(() => null);
    const text = (await el.innerText().catch(() => '')).trim();
    console.log(`Action ${i}: <${tag}> text="${text}" title="${title}" aria-label="${ariaLabel}" href="${href}"`);
  }

  // Click on the eye icon or row or job id link to see where it leads
  const jobLink = row.locator('text=M8N000380');
  if (await jobLink.isVisible()) {
    console.log('Clicking job link/text...');
    await jobLink.click();
    await page.waitForTimeout(3000);
    console.log('URL after clicking job link:', page.url());
  }

  // If not navigated, try clicking the first icon in the action cell
  if (page.url().endsWith('/jobs')) {
    const actionCell = row.locator('td').nth(1);
    const firstIcon = actionCell.locator('svg, [role="button"], button').first();
    console.log('Clicking first action icon in action cell...');
    await firstIcon.click();
    await page.waitForTimeout(3000);
    console.log('URL after clicking action icon:', page.url());
  }

  await page.screenshot({ path: 'job-detail-page.png' });
  console.log('Saved job-detail-page.png');

  // Let's see what tabs or buttons exist on this page
  const buttons = await page.locator('button, [role="tab"], nav a').all();
  console.log(`Found ${buttons.length} buttons/tabs:`);
  for (const b of buttons.slice(0, 30)) {
    const txt = (await b.innerText().catch(() => '')).trim();
    if (txt) console.log(` - "${txt}"`);
  }

  await browser.close();
})();
