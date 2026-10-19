const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  
  const text = await page.evaluate(async () => {
    const res = await fetch('/assets/index-BTGuwZAU.js');
    return await res.text();
  });

  // Search for path: ... SiteAssessorDeclaration
  const matches = [];
  let pos = 0;
  while ((pos = text.indexOf('SiteAssessorDeclaration-CTV5Es8w', pos)) !== -1) {
    matches.push(text.substring(Math.max(0, pos - 250), Math.min(text.length, pos + 150)));
    pos += 30;
  }
  console.log('SiteAssessorDeclaration route matches:', matches);

  const nomMatches = [];
  let posN = 0;
  while ((posN = text.indexOf('EnergySaverNomination-CHcLMJ35', posN)) !== -1) {
    nomMatches.push(text.substring(Math.max(0, posN - 250), Math.min(text.length, posN + 150)));
    posN += 30;
  }
  console.log('EnergySaverNomination route matches:', nomMatches);

  await browser.close();
})();
