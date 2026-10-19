const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  
  const text = await page.evaluate(async () => {
    const res = await fetch('/assets/index-BTGuwZAU.js');
    return await res.text();
  });

  // Find occurrences of SiteAssessorDeclaration and EnergySaverNomination
  const idxSite = text.indexOf('SiteAssessorDeclaration');
  if (idxSite !== -1) {
    console.log('SiteAssessorDeclaration context:');
    console.log(text.substring(Math.max(0, idxSite - 300), Math.min(text.length, idxSite + 300)));
  }

  const idxNom = text.indexOf('EnergySaverNomination');
  if (idxNom !== -1) {
    console.log('EnergySaverNomination context:');
    console.log(text.substring(Math.max(0, idxNom - 300), Math.min(text.length, idxNom + 300)));
  }

  await browser.close();
})();
