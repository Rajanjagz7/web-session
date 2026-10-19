const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  page.on('response', res => {
    if (res.url().includes('api') || res.url().includes('s3') || res.url().includes('storage')) {
      if (res.request().method() !== 'GET') {
        console.log(`[NOTE NET] ${res.status()} ${res.request().method()} ${res.url()}`);
      }
    }
  });

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  const jobId = '6ab2438c7c29b5bf7379e390';
  await page.goto(`https://nswdev.rebatem8.com.au/jobs/${jobId}`);
  await page.waitForTimeout(3000);

  // Click Notes tab
  await page.getByRole('button', { name: 'Notes' }).click();
  await page.waitForTimeout(2000);

  // Click Add Note button
  const addNoteBtn = page.getByRole('button', { name: 'Add Note' }).or(page.locator('button:has-text("Add Note")'));
  await addNoteBtn.first().click();
  await page.waitForTimeout(1000);

  // Type note in contenteditable or textarea
  const editor = page.locator('[contenteditable="true"], textarea').first();
  await editor.click();
  await editor.fill('Pre-installation site photos and equipment verification images uploaded.');
  await page.waitForTimeout(1000);

  // Attach image
  const fileInput = page.locator('input[type="file"].upload-input');
  const imgPath = path.resolve(__dirname, 'test-images/pre-installation-water-heater.jpg');
  console.log('Attaching image file:', imgPath);
  await fileInput.setInputFiles(imgPath);
  await page.waitForTimeout(5000);

  await page.screenshot({ path: 'note-with-attached-image.png' });
  console.log('Saved note-with-attached-image.png');

  // Click Add Note submit button
  const submitNote = page.getByRole('button', { name: 'Add Note' }).last();
  console.log('Submitting note...');
  await submitNote.click();
  await page.waitForTimeout(4000);

  await page.screenshot({ path: 'after-note-added.png' });
  console.log('Saved after-note-added.png');

  await browser.close();
})();
