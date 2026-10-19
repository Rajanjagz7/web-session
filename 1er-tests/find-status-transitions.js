const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('https://nswdev.rebatem8.com.au/log-in');

  // Let's get the list of all script tags or assets loaded
  const scripts = await page.evaluate(async () => {
    // Check index.html for all script tags or fetch manifest
    const res = await fetch('/index.html');
    const html = await res.text();
    const matches = html.match(/\/assets\/[a-zA-Z0-9_\-\.]+\.js/g) || [];
    return matches;
  });
  console.log('Scripts in index.html:', scripts);

  // Let's also check JobDetail or jobs components
  // Let's see all assets in the vite manifest or common components
  const commonAssets = [
    '/assets/index-BTGuwZAU.js',
    '/assets/Jobs-C2tH_z7K.js',
    '/assets/JobDetail-D3rM-qZk.js',
    '/assets/JobModal-DK-5wF9L.js',
    '/assets/JobDrawer-C3s6h0zJ.js'
  ];

  // Let's search inside the app's route definitions for "photos" or status update
  const mainText = await page.evaluate(async () => {
    const res = await fetch('/assets/index-BTGuwZAU.js');
    return await res.text();
  });

  // Find occurrences of "status" update API calls like /api/v1/jobs/
  const apiMatches = mainText.match(/\/jobs\/[a-zA-Z0-9_\-\/]+/g) || [];
  console.log('Job API routes:', [...new Set(apiMatches)]);

  // Let's check status transitions or constants
  const statusMatches = mainText.match(/status[:\s=]+["'][a-zA-Z0-9_\s]+["']/g) || [];
  console.log('Status references:', [...new Set(statusMatches)].slice(0, 30));

  await browser.close();
})();
