const { chromium } = require('playwright');

const BASE_URL = 'https://1er.softwareco.com';
const EMAIL = 'johns@softwareco.com';
const PASSWORD = 'admin@123';

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto(`${BASE_URL}/log-in`, { waitUntil: 'domcontentloaded' });
  await page.getByPlaceholder('Email ID').fill(EMAIL);
  await page.getByPlaceholder('Password').fill(PASSWORD);
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL(`${BASE_URL}/jobs`);
  console.log('Logged in successfully.');

  // Let's check Projects menu / URL
  console.log('--- Checking Projects ---');
  const projectsLink = page.getByRole('link', { name: /projects/i }).or(page.locator('text=Projects'));
  if (await projectsLink.count() > 0) {
    await projectsLink.first().click();
    await page.waitForTimeout(2000);
    console.log('Projects URL:', page.url());
    console.log('Projects content:', (await page.locator('body').innerText()).substring(0, 1000));
  }

  // Let's check Add Job button
  console.log('--- Checking Add Job ---');
  await page.goto(`${BASE_URL}/jobs`);
  await page.waitForTimeout(2000);
  const addJobBtn = page.getByRole('button', { name: /add job/i });
  if (await addJobBtn.isVisible()) {
    console.log('Clicking Add Job...');
    await addJobBtn.click();
    await page.waitForTimeout(2000);
    console.log('Add Job URL / Modal:');
    const modal = page.locator('div[role="dialog"], .modal-content, .drawer, form').first();
    console.log(await modal.innerText().catch(() => 'No modal found'));
  }

  await browser.close();
}

main().catch(console.error);
