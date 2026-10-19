const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  
  const tokenScript = await page.evaluate(async () => {
    const res = await fetch('/assets/usePublicLinkToken-CrYfxe6d.js');
    return await res.text();
  });
  console.log('usePublicLinkToken length:', tokenScript.length);
  console.log('usePublicLinkToken code:', tokenScript);

  const declScript = await page.evaluate(async () => {
    const res = await fetch('/assets/SiteAssessorDeclaration-CTV5Es8w.js');
    return await res.text();
  });
  console.log('SiteAssessorDeclaration length:', declScript.length);
  // Find URL path or api endpoints in declScript
  const apis = declScript.match(/\/api\/v1\/[a-zA-Z0-9_\-\/]+/g) || [];
  console.log('APIs in SiteAssessorDeclaration:', [...new Set(apis)]);

  const nomScript = await page.evaluate(async () => {
    const res = await fetch('/assets/EnergySaverNomination-CHcLMJ35.js');
    return await res.text();
  });
  console.log('EnergySaverNomination length:', nomScript.length);
  const nomApis = nomScript.match(/\/api\/v1\/[a-zA-Z0-9_\-\/]+/g) || [];
  console.log('APIs in EnergySaverNomination:', [...new Set(nomApis)]);

  await browser.close();
})();
