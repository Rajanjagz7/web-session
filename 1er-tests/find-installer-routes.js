const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  
  const text = await page.evaluate(async () => {
    const res = await fetch('/assets/index-BTGuwZAU.js');
    return await res.text();
  });

  const matches = text.match(/\/installers\/[a-zA-Z0-9_\-\/]+/g) || [];
  console.log('Matches for /installers/:', [...new Set(matches)]);

  const userMatches = text.match(/\/users\/[a-zA-Z0-9_\-\/]+/g) || [];
  console.log('Matches for /users/:', [...new Set(userMatches)]);

  await browser.close();
})();
