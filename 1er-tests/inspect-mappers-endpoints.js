const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  
  const text = await page.evaluate(async () => {
    const res = await fetch('/assets/publicDetailMappers-BfE9p5i8.js');
    return await res.text();
  });

  // Extract urls and function names
  const urls = text.match(/\/api\/v1\/[a-zA-Z0-9_\-\/]+/g) || [];
  console.log('URLs in publicDetailMappers:', [...new Set(urls)]);

  const exports = text.match(/export\s*\{[^}]+\}/g) || [];
  console.log('Exports:', exports);

  // Print text in slices of 1000 chars
  for (let i = 0; i < text.length; i += 1000) {
    console.log(`--- Part ${i / 1000} ---`);
    console.log(text.substring(i, i + 1000));
  }

  await browser.close();
})();
