const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  
  const code = await page.evaluate(async () => {
    const res = await fetch('/assets/publicDetailMappers-BfE9p5i8.js');
    return await res.text();
  });
  fs.writeFileSync('publicDetailMappers.js', code);
  console.log('Saved publicDetailMappers.js length:', code.length);

  const declCode = await page.evaluate(async () => {
    const res = await fetch('/assets/SiteAssessorDeclaration-CTV5Es8w.js');
    return await res.text();
  });
  fs.writeFileSync('SiteAssessorDeclaration.js', declCode);
  console.log('Saved SiteAssessorDeclaration.js length:', declCode.length);

  const nomCode = await page.evaluate(async () => {
    const res = await fetch('/assets/EnergySaverNomination-CHcLMJ35.js');
    return await res.text();
  });
  fs.writeFileSync('EnergySaverNomination.js', nomCode);
  console.log('Saved EnergySaverNomination.js length:', nomCode.length);

  await browser.close();
})();
