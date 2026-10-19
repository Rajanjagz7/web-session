const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  const indexText = await page.evaluate(async () => {
    const res = await fetch('/assets/index-BTGuwZAU.js');
    return await res.text();
  });

  const chunks = indexText.match(/assets\/[a-zA-Z0-9_\-]+\.js/g) || [];
  const uniqueChunks = [...new Set(chunks)];
  console.log(`Total unique chunks: ${uniqueChunks.length}`);
  console.log('Chunks:', uniqueChunks);

  await browser.close();
})();
