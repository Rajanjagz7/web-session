const { chromium } = require('playwright');
const path = require('path');

const JOBS = [
  {
    jobNumber: 'M8N000380',
    id: '6ab2438c7c29b5bf7379e390',
    customer: 'Coastal Enterprises NSW Pty Ltd',
    energyBillImg: 'energy-bill-coastal-enterprises.png',
    sitePhotoImg: 'pre-installation-water-heater.jpg',
    noteText: 'Pre-installation site inspection and energy bill verified for Commercial Hot Water Heat Pump system.'
  },
  {
    jobNumber: 'M8N000379',
    id: '6ab2430e7c29b5bf7379e2f3',
    customer: 'Jack Wilson',
    energyBillImg: null, // Residential
    sitePhotoImg: 'heat-pump-nameplate.jpg',
    noteText: 'Site inspection completed. Existing water heater nameplate and installation location images attached.'
  },
  {
    jobNumber: 'M8N000378',
    id: '6ab2424b7c29b5bf7379e1e9',
    customer: 'Sydney Tech Solutions Pty Ltd',
    energyBillImg: 'energy-bill-sydney-tech.png',
    sitePhotoImg: 'air-conditioner-outdoor-unit.jpg',
    noteText: 'Commercial energy bill and proposed air conditioner outdoor unit location photos attached.'
  },
  {
    jobNumber: 'M8N000377',
    id: '6ab241457c29b5bf7379e077',
    customer: 'Olivia Nguyen',
    energyBillImg: null, // Residential
    sitePhotoImg: 'air-conditioner-outdoor-unit.jpg',
    noteText: 'Residential site survey completed. Pre-installation heating and cooling photos attached.'
  }
];

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  page.on('response', res => {
    if (res.url().includes('api/v1/storage') || res.url().includes('api/v1/notes')) {
      if (res.request().method() !== 'GET') {
        console.log(`[NET] ${res.status()} ${res.request().method()} ${res.url().split('?')[0]}`);
      }
    }
  });

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');
  console.log('Logged in successfully');

  for (const job of JOBS) {
    console.log(`\n========================================`);
    console.log(`Processing Job ${job.jobNumber} (${job.customer})...`);
    console.log(`========================================`);

    // 1. If energy bill image is applicable, upload via drawer if not yet attached
    if (job.energyBillImg) {
      console.log(`Checking energy bill for ${job.jobNumber}...`);
      await page.goto('https://nswdev.rebatem8.com.au/jobs');
      await page.waitForTimeout(1000);
      const searchInput = page.getByPlaceholder('Search Jobs...');
      await searchInput.fill(job.jobNumber);
      await page.waitForTimeout(1500);

      const row = page.locator('tr').filter({ hasText: job.jobNumber }).first();
      const eyeIcon = row.locator('.cursor-pointer').first();
      await eyeIcon.click();
      await page.waitForTimeout(2000);

      const drawer = page.locator('.drawer-content, [role="dialog"]').first();
      const drawerText = await drawer.innerText();

      if (!drawerText.includes('Attached') && !drawerText.includes('attached')) {
        const fileInput = page.locator('input[type="file"].upload-input');
        if (await fileInput.count() > 0) {
          const billPath = path.resolve(__dirname, 'test-images', job.energyBillImg);
          console.log(`Uploading energy bill: ${billPath}`);
          await fileInput.setInputFiles(billPath);
          await page.waitForTimeout(4000);
        }
      } else {
        console.log(`Energy bill already attached for ${job.jobNumber}`);
      }

      await page.screenshot({ path: `evidence-${job.jobNumber}-energy-bill.png` });
      await page.keyboard.press('Escape');
      await page.waitForTimeout(1000);
    }

    // 2. Upload site photo image attachment via Notes on job direct page
    console.log(`Navigating to direct job page for ${job.jobNumber} (/jobs/${job.id})...`);
    await page.goto(`https://nswdev.rebatem8.com.au/jobs/${job.id}`);
    await page.waitForTimeout(2500);

    // Click Notes tab
    await page.getByRole('button', { name: 'Notes' }).click();
    await page.waitForTimeout(2000);

    // Check if a note with attachment already exists or add new note
    const existingNotes = await page.locator('.note-card, [class*="note"], div.shadow-custom, div.border-gray-200').allInnerTexts();
    const alreadyHasPhoto = existingNotes.some(t => t.includes('.jpg') || t.includes('.png') || t.includes('photos'));
    console.log(`Job ${job.jobNumber} already has note photo?:`, alreadyHasPhoto);

    if (!alreadyHasPhoto) {
      console.log(`Adding image note to ${job.jobNumber}...`);
      const addNoteBtn = page.getByRole('button', { name: 'Add Note' }).or(page.locator('button:has-text("Add Note")'));
      await addNoteBtn.first().click();
      await page.waitForTimeout(1000);

      const editor = page.locator('[contenteditable="true"], textarea').first();
      await editor.click();
      await editor.fill(job.noteText);
      await page.waitForTimeout(1000);

      const photoPath = path.resolve(__dirname, 'test-images', job.sitePhotoImg);
      console.log(`Attaching site photo image: ${photoPath}`);
      const fileInput = page.locator('input[type="file"].upload-input');
      await fileInput.setInputFiles(photoPath);
      await page.waitForTimeout(5000);

      const submitBtn = page.getByRole('button', { name: 'Add Note' }).last();
      await submitBtn.click();
      await page.waitForTimeout(4000);
    }

    // Capture screenshot of Notes tab with image attached
    await page.screenshot({ path: `evidence-${job.jobNumber}-notes.png` });
    console.log(`Saved evidence-${job.jobNumber}-notes.png`);
  }

  console.log('\nAll 4 jobs processed with images successfully!');
  await browser.close();
})();
