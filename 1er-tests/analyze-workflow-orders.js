const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('https://nswdev.rebatem8.com.au/log-in');

  const text = await page.evaluate(async () => {
    const r = await fetch('/assets/useOriginalEquipment-DbROuEqr.js');
    return await r.text();
  });
  fs.writeFileSync('useOriginalEquipment.js', text);
  console.log('Saved useOriginalEquipment.js, length:', text.length);

  // Print all functions and exports
  const fnMatches = text.match(/function\s+([a-zA-Z0-9_]+)\s*\([^)]*\)\s*\{[^}]+\}/g) || [];
  console.log('Functions found:');
  for (const fn of fnMatches) {
    if (fn.includes('order') || fn.includes('status') || fn.includes('photo')) {
      console.log(fn);
    }
  }

  // Print exports
  const exportMatch = text.match(/export\s*\{[^}]+\}/);
  if (exportMatch) {
    console.log('Exports:', exportMatch[0]);
  }

  await browser.close();
})();
