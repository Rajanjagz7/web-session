const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  
  const text = await page.evaluate(async () => {
    const res = await fetch('/assets/SiteAssessorDeclaration-CTV5Es8w.js');
    return await res.text();
  });

  console.log('SiteAssessorDeclaration code:');
  console.log(text);

  await browser.close();
})();
