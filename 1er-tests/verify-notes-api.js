const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  await page.goto('https://nswdev.rebatem8.com.au/log-in');
  await page.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await page.locator('input[name="password"]').fill('admin@123');
  await page.getByRole('button', { name: 'Log In' }).click();
  await page.waitForURL('**/jobs');

  const jobs = [
    { num: 'M8N000380', id: '6ab2438c7c29b5bf7379e390' },
    { num: 'M8N000379', id: '6ab2430e7c29b5bf7379e2f3' },
    { num: 'M8N000378', id: '6ab2424b7c29b5bf7379e1e9' },
    { num: 'M8N000377', id: '6ab241457c29b5bf7379e077' }
  ];

  for (const j of jobs) {
    const notesData = await page.evaluate(async (jobId) => {
      const res = await fetch(`/api/v1/notes?jobId=${jobId}`);
      return await res.json();
    }, j.id);

    console.log(`\n=== Notes for ${j.num} ===`);
    console.log('Total notes:', notesData.data?.total || notesData.data?.notes?.length);
    const notes = notesData.data?.notes || [];
    for (const n of notes) {
      console.log(' - Note:', n.note || n.text || n.content);
      console.log('   Attachments:', n.attachments || n.files || n.media);
    }
  }

  // Also take a nice screenshot of M8N000380 scrolled to the note cards
  await page.goto(`https://nswdev.rebatem8.com.au/jobs/6ab2438c7c29b5bf7379e390`);
  await page.waitForTimeout(3000);
  await page.getByRole('button', { name: 'Notes' }).click();
  await page.waitForTimeout(2000);

  await page.evaluate(() => window.scrollTo(0, 300));
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'm8n000380-notes-display.png' });
  console.log('Saved m8n000380-notes-display.png');

  await browser.close();
})();
