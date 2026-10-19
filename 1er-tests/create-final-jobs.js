const { chromium } = require('playwright');

const JOBS = [
  {
    tag: 'Job 2',
    activityType: 'Hot Water Heat Pump',
    leadGen: 'Online advertisement',
    buildingType: 'Residential Building',
    isBusiness: false,
    customerName: 'Jack Wilson',
    phone: '+61423456789',
    email: 'rajan.nsw.job2@yopmail.com',
    address: '88 George St, The Rocks NSW',
    postcode: '2000',
    newSystem: 'Heat pump'
  },
  {
    tag: 'Job 4',
    activityType: 'Hot Water Heat Pump',
    leadGen: 'Email campaign',
    buildingType: 'Small Business Site (273 kWh/day or more)',
    isBusiness: true,
    businessName: 'Coastal Enterprises NSW Pty Ltd',
    authFirstName: 'Noah',
    authLastName: 'Collins',
    authPosition: 'General Manager',
    phone: '+61458901234',
    email: 'rajan.nsw.job4@yopmail.com',
    abn: '33102417032',
    address: '15 Crown St, Wollongong NSW',
    postcode: '2500',
    newSystem: 'Heat pump'
  }
];

async function createJob(page, job) {
  console.log(`\n========================================`);
  console.log(`Creating ${job.tag}: ${job.isBusiness ? job.businessName : job.customerName}`);
  console.log(`Type: ${job.activityType} | ${job.buildingType}`);
  console.log(`========================================`);

  await page.goto('https://nswdev.rebatem8.com.au/jobs', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000);

  await page.getByRole('button', { name: 'Add Job' }).click();
  await page.waitForTimeout(1500);

  async function selectByLabel(labelText, optionText, searchText = '') {
    const item = page.locator('.form-item').filter({ hasText: labelText }).first();
    await item.locator('.select__control').click();
    await page.waitForTimeout(300);
    if (searchText) {
      const inp = item.locator('input.select__input');
      await inp.fill(searchText);
      await page.waitForTimeout(400);
    }
    const opt = page.locator('[class*="-option"]').filter({ hasText: optionText }).first();
    await opt.waitFor({ state: 'visible', timeout: 8000 });
    await opt.click();
    await page.waitForTimeout(400);
    console.log(`Selected "${optionText}" for [${labelText}]`);
  }

  // Reference
  await page.locator('input[name="ownReference"]').fill(`RJN-${Date.now().toString().slice(-6)}`);

  // Activity Type
  await selectByLabel('Activity Type', job.activityType);

  // Lead Gen
  await selectByLabel('Method of Lead Generation', job.leadGen);

  // Building Type
  await selectByLabel('Building Type', job.buildingType.substring(0, 15));

  // Installer Company
  await selectByLabel('Installer', 'Rajan Testing Company', 'Rajan');

  // Installer Person
  await selectByLabel('Attended', 'Rajan Jagwani');

  // Customer or Business
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

  // Address
  await page.locator('.switcher-toggle').click();
  await page.waitForTimeout(300);
  await page.locator('input[name="customerAddress"]').fill(job.address);
  await page.locator('input[name="postcode"]').fill(job.postcode);

  // New System (for Hot Water Heat Pump)
  if (job.newSystem) {
    await selectByLabel('New System', job.newSystem);
  }

  // Original Equipment
  await selectByLabel('Original Equipment', 'Electric Hot Water Unit');

  // Brand
  await selectByLabel('Brand', 'AGM Energy');

  // Model
  await selectByLabel('Model', 'AGMHP270W');

  // Submit
  console.log(`Submitting ${job.tag}...`);
  await page.locator('#submitButton').click();
  await page.waitForTimeout(5000);

  const shotPath = `screenshots/${job.tag.replace(/\s+/g, '_').toLowerCase()}.png`;
  await page.screenshot({ path: shotPath });
  console.log(`Saved screenshot: ${shotPath}`);
}

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  page.on('response', res => {
    if (res.url().includes('/api/v1/jobs') && res.request().method() === 'POST') {
      console.log(`[API RESPONSE SUCCESS] ${res.status()} ${res.url()}`);
    }
  });

  await page.goto('https://nswdev.rebatem8.com.au/log-in', { waitUntil: 'domcontentloaded' });
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');
  console.log('Logged in successfully!');

  for (const j of JOBS) {
    try {
      await createJob(page, j);
    } catch (e) {
      console.error(`Failed ${j.tag}:`, e.message);
    }
  }

  // Fetch updated jobs list
  console.log('\n--- Final Updated Jobs Table ---');
  await page.goto('https://nswdev.rebatem8.com.au/jobs', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);
  const rows = await page.locator('table tbody tr').all();
  for (let i = 0; i < Math.min(rows.length, 6); i++) {
    const text = (await rows[i].innerText()).replace(/\n+/g, ' | ');
    console.log(`Row ${i + 1}: ${text}`);
  }

  await browser.close();
}

main().catch(console.error);
