const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  
  const text = await page.evaluate(async () => {
    const res = await fetch('/assets/ManageInstallerTeam-qmiPu2LM.js');
    return await res.text();
  });

  const apiEndpoints = text.match(/\/api\/v1\/[a-zA-Z0-9_\-\/]+/g) || [];
  console.log('Endpoints in ManageInstallerTeam:', [...new Set(apiEndpoints)]);

  const textListing = await page.evaluate(async () => {
    const res = await fetch('/assets/installerListing-3bsxp3mP.js');
    return await res.text();
  });
  const apiListing = textListing.match(/\/api\/v1\/[a-zA-Z0-9_\-\/]+/g) || [];
  console.log('Endpoints in installerListing:', [...new Set(apiListing)]);

  await browser.close();
})();
