const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const artifactDir = 'C:\\Users\\Baps\\.gemini\\antigravity-ide\\brain\\47c56265-f783-4594-9904-b20c400f716a\\screenshots';
if (!fs.existsSync(artifactDir)) {
  fs.mkdirSync(artifactDir, { recursive: true });
}

const jobs = [
  { num: 'M8N000380', id: '6ab2438c7c29b5bf7379e390', title: 'Commercial Hot Water Heat Pump' },
  { num: 'M8N000379', id: '6ab2430e7c29b5bf7379e2f3', title: 'Residential Hot Water Heat Pump' },
  { num: 'M8N000378', id: '6ab2424b7c29b5bf7379e1e9', title: 'Commercial Heating & Cooling' },
  { num: 'M8N000377', id: '6ab241457c29b5bf7379e077', title: 'Residential Heating & Cooling' }
];

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  for (const j of jobs) {
    console.log(`Capturing evidence for ${j.num}...`);
    await page.goto(`https://nswdev.rebatem8.com.au/jobs/${j.id}`);
    await page.waitForTimeout(3000);

    // Click Notes tab
    await page.getByRole('button', { name: 'Notes' }).click();
    await page.waitForTimeout(2000);

    await page.evaluate(() => window.scrollTo(0, 250));
    await page.waitForTimeout(1000);

    const destPath = path.join(artifactDir, `job-${j.num}-image-evidence.png`);
    await page.screenshot({ path: destPath });
    console.log(`Saved screenshot to ${destPath}`);
  }

  // Also take energy bill screenshot for M8N000380 and M8N000378
  await page.goto('https://nswdev.rebatem8.com.au/jobs');
  await page.waitForTimeout(1500);
  const searchInput = page.getByPlaceholder('Search Jobs...');
  await searchInput.fill('M8N000380');
  await page.waitForTimeout(1500);
  const row = page.locator('tr').filter({ hasText: 'M8N000380' }).first();
  await row.locator('.cursor-pointer').first().click();
  await page.waitForTimeout(2500);

  const billDest = path.join(artifactDir, `job-M8N000380-energy-bill-evidence.png`);
  await page.screenshot({ path: billDest });
  console.log(`Saved energy bill screenshot to ${billDest}`);

  await browser.close();
})();
