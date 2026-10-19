const { chromium } = require('playwright');

const JOBS_TO_CREATE = [
  {
    tag: 'Job 2',
    activityType: 'Hot Water Heat Pump',
    newSystem: 'Heat pump',
    leadGen: 'Online advertisement',
    buildingType: 'Residential Building',
    isBusiness: false,
    company: 'Rajan Testing Company',
    customerName: 'Jack Wilson',
    phone: '+61423456789',
    email: 'rajan.nsw.job2@yopmail.com',
    address: '88 George St, The Rocks NSW',
    postcode: '2000'
  },
  {
    tag: 'Job 3',
    activityType: 'Heating & Cooling',
    leadGen: 'Social media',
    buildingType: 'Small Business Site (less than 273 kWh/day)',
    isBusiness: true,
    businessName: 'Sydney Tech Solutions Pty Ltd',
    authFirstName: 'Aria',
    authLastName: 'Patel',
    authPosition: 'Managing Director',
    company: 'Rajan Testing Company',
    phone: '+61434567890',
    email: 'rajan.nsw.job3@yopmail.com',
    abn: '33102417032',
    address: '45 Hunter St, Newcastle NSW',
    postcode: '2300'
  },
  {
    tag: 'Job 4',
    activityType: 'Hot Water Heat Pump',
    newSystem: 'Heat pump',
    leadGen: 'Email campaign',
    buildingType: 'Small Business Site (273 kWh/day or more)',
    isBusiness: true,
    businessName: 'Coastal Enterprises NSW Pty Ltd',
    authFirstName: 'Noah',
    authLastName: 'Collins',
    authPosition: 'General Manager',
    company: 'Rajan Testing Company',
    phone: '+61458901234',
    email: 'rajan.nsw.job4@yopmail.com',
    abn: '33102417032',
    address: '15 Crown St, Wollongong NSW',
    postcode: '2500'
  }
];

async function createSingleJob(page, job) {
  console.log(`\n========================================`);
  console.log(`Starting ${job.tag}: ${job.isBusiness ? job.businessName : job.customerName}`);
  console.log(`Activity: ${job.activityType} | Building: ${job.buildingType}`);
  console.log(`========================================`);

  await page.goto('https://nswdev.rebatem8.com.au/jobs', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000);

  await page.getByRole('button', { name: 'Add Job' }).click();
  await page.waitForTimeout(1500);

  // 1. Reference
  const ref = `RJN-${Date.now().toString().slice(-6)}`;
  await page.locator('input[name="ownReference"]').fill(ref);

  // 2. Activity Type
  const actSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Activity Type' }).first();
  await actSelect.click();
  await page.locator('[class*="-option"]').filter({ hasText: job.activityType }).first().click();
  await page.waitForTimeout(400);

  // 3. Lead Gen
  const leadSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Method of Lead Generation' }).first();
  await leadSelect.click();
  await page.locator('[class*="-option"]').filter({ hasText: job.leadGen }).first().click();
  await page.waitForTimeout(400);

  // 4. Building Type
  const bldgSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Building Type' }).first();
  await bldgSelect.click();
  await page.locator('[class*="-option"]').filter({ hasText: job.buildingType.substring(0, 20) }).first().click();
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

  // 7. Customer / Business Fields
  if (job.isBusiness) {
    await page.locator('input[name="businessName"]').fill(job.businessName);
    await page.locator('input[name="authFirstName"]').fill(job.authFirstName);
    await page.locator('input[name="authLastName"]').fill(job.authLastName);
    await page.locator('input[name="authSignPosition"]').fill(job.authPosition);
    await page.locator('input[name="authPhoneNumber"]').fill(job.phone);
    await page.locator('input[name="authEmail"]').fill(job.email);
    await page.locator('input[name="abnAcn"]').fill(job.abn);
  } else {
    await page.locator('input[name="customerName"]').fill(job.customerName);
    await page.locator('input[name="phone"]').fill(job.phone);
    await page.locator('input[name="email"]').fill(job.email);
  }

  // 8. Address Switcher
  await page.locator('.switcher-toggle').click();
  await page.waitForTimeout(300);
  await page.locator('input[name="customerAddress"]').fill(job.address);
  await page.locator('input[name="postcode"]').fill(job.postcode);

  // 9. Hot Water Heat Pump - Select New System if present
  if (job.newSystem) {
    const newSysSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select New System' }).first();
    if (await newSysSelect.isVisible()) {
      await newSysSelect.click();
      await page.waitForTimeout(400);
      await page.locator('[class*="-option"]').filter({ hasText: job.newSystem }).first().click();
      await page.waitForTimeout(400);
    }
  }

  // 10. Original Equipment
  const eqSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Original Equipment' }).first();
  if (await eqSelect.isVisible()) {
    await eqSelect.click();
    await page.waitForTimeout(400);
    await page.locator('[class*="-option"]').first().click();
    await page.waitForTimeout(400);
  }

  // 11. Brand
  const brandSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Brand' }).first();
  if (await brandSelect.isVisible()) {
    await brandSelect.click();
    await page.waitForTimeout(400);
    await page.locator('[class*="-option"]').first().click();
    await page.waitForTimeout(400);
  }

  // 12. Model
  const modelSelect = page.locator('.select, [class*="-control"]').filter({ hasText: 'Select Model' }).first();
  if (await modelSelect.isVisible()) {
    await modelSelect.click();
    await page.waitForTimeout(400);
    await page.locator('[class*="-option"]').first().click();
    await page.waitForTimeout(400);
  }

  // 13. Submit
  console.log(`Submitting ${job.tag}...`);
  await page.locator('#submitButton').click();
  await page.waitForTimeout(5000);

  const screenshotPath = `screenshots/${job.tag.replace(/\s+/g, '_').toLowerCase()}.png`;
  await page.screenshot({ path: screenshotPath });
  console.log(`Saved screenshot: ${screenshotPath}`);
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
  console.log('Logged in successfully!');

  for (const job of JOBS_TO_CREATE) {
    try {
      await createSingleJob(page, job);
    } catch (e) {
      console.error(`Error in ${job.tag}:`, e.message);
    }
  }

  // Verification: Read top rows of jobs list
  console.log('\n--- Fetching Updated Jobs List ---');
  await page.goto('https://nswdev.rebatem8.com.au/jobs', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);

  const rows = await page.locator('table tbody tr').all();
  console.log(`Total rows in table: ${rows.length}`);
  for (let i = 0; i < Math.min(rows.length, 8); i++) {
    const text = (await rows[i].innerText()).replace(/\n+/g, ' | ');
    console.log(`Row ${i + 1}: ${text}`);
  }

  await browser.close();
}

main().catch(console.error);
