const { chromium } = require('playwright');

const JOBS_DATA = [
  {
    ref: `TEST-RJN-HWHP-RES-${Date.now()}`,
    activityType: 'Hot Water Heat Pump',
    leadGen: 'Online advertisement',
    buildingType: 'Residential Building',
    company: 'Rajan Testing Company',
    customerName: 'Jack Wilson',
    phone: '+61423456789',
    email: 'rajan.nsw.job2@yopmail.com',
    address: '88 George St, The Rocks NSW',
    postcode: '2000'
  },
  {
    ref: `TEST-RJN-HC-SMB1-${Date.now() + 1}`,
    activityType: 'Heating & Cooling',
    leadGen: 'Social media',
    buildingType: 'Small Business Site (less than 273 kWh/day)',
    company: 'Rajan Testing Company',
    customerName: 'Aria Patel',
    phone: '+61434567890',
    email: 'rajan.nsw.job3@yopmail.com',
    address: '45 Hunter St, Newcastle NSW',
    postcode: '2300'
  },
  {
    ref: `TEST-RJN-HWHP-SMB2-${Date.now() + 2}`,
    activityType: 'Hot Water Heat Pump',
    leadGen: 'Email campaign',
    buildingType: 'Small Business Site (273 kWh/day or more)',
    company: 'Rajan Testing Company',
    customerName: 'Noah Collins',
    phone: '+61458901234',
    email: 'rajan.nsw.job4@yopmail.com',
    address: '15 Crown St, Wollongong NSW',
    postcode: '2500'
  }
];

async function createJob(page, data, index) {
  console.log(`\n=== Creating Job ${index + 2}: ${data.customerName} (${data.activityType} - ${data.buildingType}) ===`);
  
  await page.goto('https://nswdev.rebatem8.com.au/jobs', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000);

  await page.getByRole('button', { name: 'Add Job' }).click();
  await page.waitForTimeout(1500);

  // 1. Own Reference
  await page.locator('input[name="ownReference"]').fill(data.ref);

  // 2. Activity Type
  const actSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Activity Type' }).first();
  await actSelect.click();
  await page.locator('[class*="-option"]').filter({ hasText: data.activityType }).first().click();
  await page.waitForTimeout(400);

  // 3. Lead Gen
  const leadSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Method of Lead Generation' }).first();
  await leadSelect.click();
  await page.locator('[class*="-option"]').filter({ hasText: data.leadGen }).first().click();
  await page.waitForTimeout(400);

  // 4. Building Type
  const bldgSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Building Type' }).first();
  await bldgSelect.click();
  await page.locator('[class*="-option"]').filter({ hasText: data.buildingType }).first().click();
  await page.waitForTimeout(400);

  // 5. Installer Company
  const compSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Installer (Company)' }).first();
  await compSelect.click();
  const compInput = page.locator('#react-select-8-input');
  await compInput.fill('Rajan');
  await page.waitForTimeout(400);
  await page.locator('[class*="-option"]').filter({ hasText: 'Rajan Testing Company' }).first().click();
  await page.waitForTimeout(500);

  // 6. Installer Person
  const personSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Installer Name' }).first();
  if (await personSelect.isVisible()) {
    await personSelect.click();
    await page.waitForTimeout(400);
    await page.locator('[class*="-option"]').first().click();
    await page.waitForTimeout(400);
  }

  // 7. Customer Name
  await page.locator('input[name="customerName"]').fill(data.customerName);

  // 8. Customer Phone
  const phoneInput = page.locator('input[name="phone"]');
  await phoneInput.fill(data.phone);

  // 9. Customer Email
  await page.locator('input[name="email"]').fill(data.email);

  // 10. Address Switcher
  await page.locator('.switcher-toggle').click();
  await page.waitForTimeout(300);
  await page.locator('input[name="customerAddress"]').fill(data.address);
  await page.locator('input[name="postcode"]').fill(data.postcode);

  // 11. Equipment
  const eqSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Original Equipment' }).first();
  if (await eqSelect.isVisible()) {
    await eqSelect.click();
    await page.waitForTimeout(400);
    await page.locator('[class*="-option"]').first().click();
    await page.waitForTimeout(400);
  }

  // 12. Brand
  const brandSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Brand' }).first();
  if (await brandSelect.isVisible()) {
    await brandSelect.click();
    await page.waitForTimeout(400);
    await page.locator('[class*="-option"]').first().click();
    await page.waitForTimeout(400);
  }

  // 13. Model
  const modelSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Model' }).first();
  if (await modelSelect.isVisible()) {
    await modelSelect.click();
    await page.waitForTimeout(400);
    await page.locator('[class*="-option"]').first().click();
    await page.waitForTimeout(400);
  }

  // 14. Submit
  console.log(`Submitting Job ${index + 2}...`);
  await page.locator('#submitButton').click();
  await page.waitForTimeout(4000);

  console.log(`Job ${index + 2} submitted successfully!`);
  await page.screenshot({ path: `job-${index + 2}-created.png` });
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  page.on('response', res => {
    if (res.url().includes('/api/v1/jobs') && res.request().method() === 'POST') {
      console.log(`[API RESPONSE] ${res.status()} ${res.url()}`);
    }
  });

  await page.goto('https://nswdev.rebatem8.com.au/log-in', { waitUntil: 'domcontentloaded' });
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');
  console.log('Logged in to RebateM8 NSW.');

  for (let i = 0; i < JOBS_DATA.length; i++) {
    await createJob(page, JOBS_DATA[i], i);
  }

  // Verify all in table
  await page.goto('https://nswdev.rebatem8.com.au/jobs', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);
  const rows = await page.locator('table tbody tr').all();
  console.log(`\n=== Current Jobs Table (Top ${rows.length}) ===`);
  for (let i = 0; i < Math.min(rows.length, 6); i++) {
    const text = (await rows[i].innerText()).replace(/\n+/g, ' | ');
    console.log(`Row ${i + 1}: ${text}`);
  }

  await browser.close();
}

main().catch(console.error);
