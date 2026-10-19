const { chromium } = require('playwright');

async function controlForLabel(page, labelText) {
  const label = page.getByText(labelText, { exact: false }).first();
  const fieldWrapper = label.locator('xpath=ancestor::*[.//*[contains(@class,"select__control")]][1]');
  return fieldWrapper.locator('.select__control').first();
}
async function selectOption(page, labelText, optionName) {
  const control = await controlForLabel(page, labelText);
  await control.scrollIntoViewIfNeeded();
  await control.click();
  await page.getByRole('option', { name: optionName, exact: true }).click();
}

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 350 });
  const page = await browser.newPage({ viewport: null, args: ['--start-maximized'] });

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.getByPlaceholder(/email/i).fill('admin@rebatem8nsw.com.au');
  await page.getByPlaceholder(/password/i).fill('admin@123');
  await page.getByRole('button', { name: /log ?in|sign ?in/i }).click();
  await page.waitForTimeout(2000);

  const runId = Date.now().toString().slice(-8);
  const customerName = `Soft Delete Demo ${runId}`;
  const ownReference = `REF-DEMO-${runId}`;

  console.log(`\n=== STEP 1: Create a fresh job live via the UI (ref: ${ownReference}) ===`);
  await page.goto('https://nswdev.rebatem8.com.au/jobs');
  await page.getByRole('button', { name: /add job/i }).click();
  const dialog = page.getByRole('dialog');
  await dialog.getByPlaceholder('Enter customer name').waitFor({ state: 'visible' });

  await dialog.getByPlaceholder('Enter customer name').fill(customerName);
  await dialog.getByPlaceholder('customer@email.com').fill(`soft.delete.demo.${runId}@yopmail.com`);
  const phoneField = dialog.getByPlaceholder('412345678');
  await phoneField.click();
  await page.keyboard.type(`4${runId.slice(-8)}`);
  await dialog.getByPlaceholder('12345678901').fill(runId.padStart(11, '0').slice(-11));

  const addressControl = await controlForLabel(dialog, 'Site address');
  await addressControl.click();
  await page.keyboard.type('1 George Street Sydney');
  await page.waitForTimeout(1200);
  await page.getByRole('option').first().click();
  await dialog.getByPlaceholder('2000').fill('2000');

  await selectOption(page, 'Activity type', 'Heating & Cooling');
  await selectOption(page, 'Building type', 'Residential Building');
  await selectOption(page, 'Method of lead generation', 'Phone');
  await dialog.getByPlaceholder('REF-001').fill(ownReference);
  const dateField = dialog.getByPlaceholder('DD-MM-YYYY');
  await dateField.click();
  await page.keyboard.type('01-12-2026');
  await selectOption(page, 'Installer (company)', 'Rajan Testing Company');
  await page.waitForTimeout(600);
  await selectOption(page, 'Original equipment', 'No existing system (new installation)');
  await page.waitForTimeout(500);
  const brandControl = await controlForLabel(dialog, 'Brand');
  await brandControl.click();
  await page.getByRole('option').first().click();
  await page.waitForTimeout(500);
  const modelControl = await controlForLabel(dialog, 'Model');
  await modelControl.click();
  await page.getByRole('option').first().click();

  await dialog.getByRole('button', { name: /send engagement letter/i }).click();
  await dialog.getByPlaceholder('Enter customer name').waitFor({ state: 'hidden', timeout: 15000 });
  await page.waitForTimeout(1500);
  console.log('Job created.');

  const jobInfo = await page.evaluate(async (ref) => {
    const res = await fetch(`/api/v1/jobs?search=${encodeURIComponent(ref)}`, { credentials: 'include' });
    const body = await res.json();
    return body.data.jobs[0];
  }, ownReference);
  console.log(`Job number: ${jobInfo.jobNumber}, id: ${jobInfo.id}`);

  console.log('\n=== STEP 2: Confirm it in the Jobs list ===');
  await page.goto('https://nswdev.rebatem8.com.au/jobs');
  await page.getByPlaceholder('Search Jobs...').fill(ownReference);
  await page.waitForTimeout(2000);

  console.log('\n=== STEP 3: Delete it via the real UI (checkbox + Delete button) ===');
  const rowCheckbox = page.locator('table tbody tr').first().locator('input[type="checkbox"]');
  await rowCheckbox.waitFor({ state: 'visible', timeout: 15000 });
  await rowCheckbox.check();
  await page.waitForTimeout(1000);
  const deleteBtn = page.getByRole('button', { name: /delete/i }).first();
  await deleteBtn.click();
  await page.waitForTimeout(1000);
  const confirmBtn = page.getByRole('button', { name: /confirm|yes|delete/i }).last();
  if (await confirmBtn.isVisible().catch(() => false)) {
    await confirmBtn.click();
  }
  await page.waitForTimeout(2000);
  console.log('Deleted via the UI.');

  console.log('\n=== STEP 4: Confirm it is gone from the list ===');
  await page.goto('https://nswdev.rebatem8.com.au/jobs');
  await page.getByPlaceholder('Search Jobs...').fill(ownReference);
  await page.waitForTimeout(2000);
  const bodyAfterDelete = await page.evaluate(() => document.body.innerText);
  console.log('Result:', bodyAfterDelete.includes('No Data Found') ? 'No Data Found - correctly excluded' : 'Still showing (unexpected)');

  console.log('\n=== STEP 5: Direct URL access shows the error page ===');
  await page.goto(`https://nswdev.rebatem8.com.au/jobs/${jobInfo.id}`);
  await page.waitForTimeout(2500);
  const bodyDirectNav = await page.evaluate(() => document.body.innerText);
  console.log('Result:', bodyDirectNav.includes('Something went Wrong') ? 'Error page shown, as expected' : 'Unexpected: loaded normally');

  console.log('\n=== STEP 6: Prove it is sitting in the trash (no UI page for this - API call, BUG-13) ===');
  const trashCheck = await page.evaluate(async (ref) => {
    const res = await fetch(`/api/v1/jobs?deleted=true&search=${encodeURIComponent(ref)}`, { credentials: 'include' });
    return res.json();
  }, ownReference);
  console.log('Trash entry:', JSON.stringify(trashCheck.data.jobs.map(j => ({ jobNumber: j.jobNumber, isDeleted: j.isDeleted, deletedAt: j.deletedAt }))));

  console.log('\n=== STEP 7: Restore via API (no UI button exists for this) ===');
  const restoreResp = await page.evaluate(async (id) => {
    const res = await fetch('/api/v1/jobs/restore', {
      method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jobIds: [id] }),
    });
    return res.json();
  }, jobInfo.id);
  console.log('Restore response:', JSON.stringify(restoreResp.data));

  console.log('\n=== STEP 8: Confirm it is back in the UI ===');
  await page.goto('https://nswdev.rebatem8.com.au/jobs');
  await page.getByPlaceholder('Search Jobs...').fill(ownReference);
  await page.waitForTimeout(2500);
  const rowTextAfterRestore = await page.locator('table tbody tr').first().allTextContents();
  console.log('Job after restore:', JSON.stringify(rowTextAfterRestore));

  console.log('\nDone. Leaving the browser open for 25s to look at the final state.');
  await page.waitForTimeout(25000);
  await browser.close();
})();
