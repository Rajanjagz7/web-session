// Logs into 1er.softwareco.com and searches for a job by ID.
// Usage: node find-job.js <jobId>
const { chromium } = require('playwright');

const BASE_URL = 'https://1er.softwareco.com';
const EMAIL = 'johns@softwareco.com';
const PASSWORD = 'admin@123';

async function main() {
  const jobId = process.argv[2];
  if (!jobId) {
    console.error('Usage: node find-job.js <jobId>');
    process.exit(1);
  }

  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();

  await page.goto(`${BASE_URL}/log-in`);
  await page.getByPlaceholder('Email ID').fill(EMAIL);
  await page.getByPlaceholder('Password').fill(PASSWORD);
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL(`${BASE_URL}/jobs`);

  const searchBox = page.getByPlaceholder('Search Jobs...');
  await searchBox.fill(jobId);
  await searchBox.press('Enter');

  await page.waitForTimeout(1500);

  const noData = await page.getByText('No Data Found').isVisible().catch(() => false);
  if (noData) {
    console.log(`No job found matching "${jobId}".`);
  } else {
    const row = page.locator('a', { hasText: jobId }).first();
    const href = await row.getAttribute('href').catch(() => null);
    console.log(`Found job "${jobId}". Link: ${href}`);
  }

  await browser.close();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
