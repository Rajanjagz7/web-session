const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();

  const assessorToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqb2JJZCI6IjZhYjI0MzhjN2MyOWI1YmY3Mzc5ZTM5MCIsInB1cnBvc2UiOiJzaXRlLWFzc2Vzc29yIiwiaWF0IjoxNzkwMDc2MDg4LCJleHAiOjE3OTI2NjgwODgsImF1ZCI6InJlYmF0ZW04IiwiaXNzIjoicmViYXRlbTgtbnN3In0.mD1U4JZGA9wrmNDGwLeAAVb0DAo4VGw7JMGLfzCBva4';
  const nominationToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqb2JJZCI6IjZhYjI0MzhjN2MyOWI1YmY3Mzc5ZTM5MCIsInB1cnBvc2UiOiJub21pbmF0aW9uIiwiaWF0IjoxNzkwMDc2MDkyLCJleHAiOjE3OTI2NjgwOTIsImF1ZCI6InJlYmF0ZW04IiwiaXNzIjoicmViYXRlbTgtbnN3In0.9KxJ6nMAU7T9lqHejiJY-9WjjDwGd19p_Z-Q4rIeKwU';

  console.log('=== STEP 1: Site Assessor Declaration Signing ===');
  await page.goto(`https://nswdev.rebatem8.com.au/site-assessor/sign?token=${assessorToken}`);
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000);

  await page.screenshot({ path: 'step1-assessor-loaded.png', fullPage: true });

  // Draw signature on canvas
  const assessorCanvas = page.locator('canvas').first();
  await assessorCanvas.scrollIntoViewIfNeeded();
  const box1 = await assessorCanvas.boundingBox();
  if (box1) {
    await page.mouse.move(box1.x + 30, box1.y + 30);
    await page.mouse.down();
    await page.mouse.move(box1.x + 80, box1.y + 60);
    await page.mouse.move(box1.x + 130, box1.y + 30);
    await page.mouse.move(box1.x + 180, box1.y + 50);
    await page.mouse.up();
    console.log('Signature drawn on assessor canvas');
  } else {
    console.error('Assessor canvas not found!');
  }

  await page.waitForTimeout(1000);

  // Check the confirmation checkbox
  const agreeAssessor = page.locator('label').filter({ hasText: /I confirm the details above are correct/i });
  await agreeAssessor.scrollIntoViewIfNeeded();
  await agreeAssessor.click();
  console.log('Clicked assessor agree checkbox');

  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'step1-assessor-filled.png', fullPage: true });

  // Click Sign declaration
  const signDeclBtn = page.getByRole('button', { name: /Sign declaration/i });
  await signDeclBtn.click();
  console.log('Clicked "Sign declaration" button');

  await page.waitForTimeout(5000);
  await page.screenshot({ path: 'step1-assessor-signed.png', fullPage: true });

  // Check Job Status via API
  const adminPage = await context.newPage();
  await adminPage.goto('https://nswdev.rebatem8.com.au/log-in');
  await adminPage.locator('input[name="email"]').fill('admin@rebatem8nsw.com.au');
  await adminPage.locator('input[name="password"]').fill('admin@123');
  await adminPage.getByRole('button', { name: 'Log In' }).click();
  await adminPage.waitForURL('**/jobs');

  let statusCheck = await adminPage.evaluate(async () => {
    const r = await fetch('/api/v1/jobs/6ab2438c7c29b5bf7379e390');
    const j = await r.json();
    return {
      status: j.data.job.status,
      siteAssessorDeclaration: j.data.job.siteAssessorDeclaration?.status,
      nomination: j.data.job.nomination?.status
    };
  });
  console.log('Status after assessor declaration:', statusCheck);

  console.log('=== STEP 2: Customer Nomination Signing ===');
  await page.goto(`https://nswdev.rebatem8.com.au/nomination/sign?token=${nominationToken}`);
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000);

  await page.screenshot({ path: 'step2-nomination-loaded.png', fullPage: true });

  // Draw signature on canvas
  const nomCanvas = page.locator('canvas').first();
  await nomCanvas.scrollIntoViewIfNeeded();
  const box2 = await nomCanvas.boundingBox();
  if (box2) {
    await page.mouse.move(box2.x + 30, box2.y + 30);
    await page.mouse.down();
    await page.mouse.move(box2.x + 80, box2.y + 60);
    await page.mouse.move(box2.x + 130, box2.y + 30);
    await page.mouse.move(box2.x + 180, box2.y + 50);
    await page.mouse.up();
    console.log('Signature drawn on nomination canvas');
  } else {
    console.error('Nomination canvas not found!');
  }

  await page.waitForTimeout(1000);

  // Check the confirmation checkbox
  const agreeNom = page.locator('label').filter({ hasText: /I confirm that the details above are correct/i });
  await agreeNom.scrollIntoViewIfNeeded();
  await agreeNom.click();
  console.log('Clicked nomination agree checkbox');

  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'step2-nomination-filled.png', fullPage: true });

  // Click Sign nomination form
  const signNomBtn = page.getByRole('button', { name: /Sign nomination form/i });
  await signNomBtn.click();
  console.log('Clicked "Sign nomination form" button');

  await page.waitForTimeout(5000);
  await page.screenshot({ path: 'step2-nomination-signed.png', fullPage: true });

  // Check Job Status via API again
  statusCheck = await adminPage.evaluate(async () => {
    const r = await fetch('/api/v1/jobs/6ab2438c7c29b5bf7379e390');
    const j = await r.json();
    return {
      status: j.data.job.status,
      siteAssessorDeclaration: j.data.job.siteAssessorDeclaration?.status,
      nomination: j.data.job.nomination?.status
    };
  });
  console.log('Status after customer nomination:', statusCheck);

  await browser.close();
})();
