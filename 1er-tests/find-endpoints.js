const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  // Search in loaded scripts
  const endpoints = await page.evaluate(async () => {
    const scripts = Array.from(document.querySelectorAll('script[src]')).map(s => s.src);
    const matches = [];
    for (const src of scripts) {
      try {
        const text = await (await fetch(src)).text();
        const urls = text.match(/\/api\/v1\/jobs[a-zA-Z0-9_\-\/\:]*/g) || [];
        matches.push(...urls);
      } catch (e) {}
    }
    return [...new Set(matches)];
  });

  console.log('Discovered Job API Endpoints:', endpoints);
  await browser.close();
})();
