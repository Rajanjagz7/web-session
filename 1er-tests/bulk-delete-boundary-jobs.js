const { chromium } = require('playwright');

const JOB_NUMBERS = [
  'M8N000190', 'M8N000191', 'M8N000192', 'M8N000193', 'M8N000194', 'M8N000195',
  'M8N000196', 'M8N000197', 'M8N000198', 'M8N000199', 'M8N000200', 'M8N000201',
];

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 250 });
  const context = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
  const page = await context.newPage();

  console.log('=== STEP 1: Log in ===');
  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.getByPlaceholder(/email/i).fill('admin@rebatem8nsw.com.au');
  await page.getByPlaceholder(/password/i).fill('admin@123');
  await page.getByRole('button', { name: /log ?in|sign ?in/i }).click();
  await page.waitForTimeout(2000);

  console.log('=== STEP 2: Search "REF-BND-" to isolate the 12 throwaway boundary-test jobs ===');
  await page.goto('https://nswdev.rebatem8.com.au/jobs');
  await page.getByPlaceholder('Search Jobs...').fill('REF-BND-69247897');
  await page.waitForTimeout(2000);

  const rowCount = await page.locator('table tbody tr').count();
  console.log(`Rows matched: ${rowCount}`);

  console.log('=== STEP 3: Select all matched rows via checkbox ===');
  const selectAllCheckbox = page.locator('table thead input[type="checkbox"]').first();
  if (await selectAllCheckbox.count()) {
    await selectAllCheckbox.check();
  } else {
    for (let i = 0; i < rowCount; i++) {
      await page.locator('table tbody tr').nth(i).locator('input[type="checkbox"]').check();
    }
  }
  await page.waitForTimeout(800);

  console.log('=== STEP 4: Click Delete and confirm ===');
  const deleteBtn = page.getByRole('button', { name: /delete/i }).first();
  await deleteBtn.click();
  await page.waitForTimeout(1000);
  const confirmBtn = page.getByRole('button', { name: /confirm|yes|delete/i }).last();
  if (await confirmBtn.isVisible().catch(() => false)) {
    await confirmBtn.click();
  }
  await page.waitForTimeout(2500);
  console.log('Deleted via the real bulk-delete UI action.');

  console.log('=== STEP 5: Confirm they are gone from the default list ===');
  await page.goto('https://nswdev.rebatem8.com.au/jobs');
  await page.getByPlaceholder('Search Jobs...').fill('REF-BND-69247897');
  await page.waitForTimeout(2000);
  const bodyAfter = await page.evaluate(() => document.body.innerText);
  console.log('Result:', bodyAfter.includes('No Data Found') ? 'No Data Found - all 12 correctly excluded' : 'Some rows still showing (check manually)');

  console.log('=== STEP 6: Cross-check via API - confirm all 12 are isDeleted:true in the trash view ===');
  const trashCheck = await page.evaluate(async (jobNumbers) => {
    const res = await fetch('/api/v1/jobs?deleted=true&search=REF-BND-69247897&limit=20', { credentials: 'include' });
    const body = await res.json();
    return body.data.jobs.map(j => ({ jobNumber: j.jobNumber, isDeleted: j.isDeleted, deletedAt: j.deletedAt }));
  }, JOB_NUMBERS);
  console.log('Trash entries found:', trashCheck.length, 'of', JOB_NUMBERS.length, 'expected');
  console.log(JSON.stringify(trashCheck, null, 2));

  console.log('\nLeaving browser open 15s to inspect.');
  await page.waitForTimeout(15000);
  await browser.close();
})();
