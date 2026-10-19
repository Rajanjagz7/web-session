const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  // Let's inspect all script tags and assets
  const scriptUrls = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('script[src]')).map(s => s.src);
  });
  console.log('Script URLs:', scriptUrls);

  // Let's fetch index or bundle script and find chunk names
  for (const s of scriptUrls) {
    const text = await page.evaluate(async (url) => {
      const res = await fetch(url);
      return await res.text();
    }, s);
    console.log(`Script ${s.split('/').pop()} length: ${text.length}`);

    // Search for photo or evidence or upload in text
    const photoMatches = text.match(/[a-zA-Z0-9_\-\/]*photo[a-zA-Z0-9_\-\/]*/gi) || [];
    console.log('Photo keywords in bundle:', [...new Set(photoMatches)].slice(0, 15));

    const chunkMatches = text.match(/"assets\/[a-zA-Z0-9_\-]+\.js"/g) || [];
    console.log('Referenced chunks count:', chunkMatches.length);
    if (chunkMatches.length > 0) {
      console.log('Sample chunks:', chunkMatches.slice(0, 10));
    }
  }

  await browser.close();
})();
