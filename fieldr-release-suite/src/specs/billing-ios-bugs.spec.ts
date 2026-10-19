import { env } from '../config/env';
import { expect, fixme, live, manual, test } from '../fixtures/test';
import { DefectsPage } from '../pages/DefectsPage';
import { LoginPage } from '../pages/LoginPage';

/**
 * Subscription & Billing (SUB-01..03, SBS-01, PUR-01..03): every item needs a billing sandbox with specific subscription
 * states, so they are fixme with the prerequisite named in src/notes.ts. iPhone App (IOS-01..03) and the other bug fixes follow.
 */
test.describe('@subscription Subscription and purchase history', () => {
  fixme('SUB-01');
  fixme('SUB-02');
  fixme('SUB-03');
  fixme('SBS-01');
  fixme('PUR-01');
  fixme('PUR-02');
  fixme('PUR-03');
});

test.describe('@ios iPhone app', () => {
  manual('IOS-01');
  manual('IOS-02');
  manual('IOS-03');
});

test.describe('@bugfix Bug fixes', () => {
  fixme('BUG-01');

  live('BUG-03', 'defect title and description changes are saved when the menu is closed', async ({ page, api, uniq }) => {
    const customer = await api.createCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
    const jobId = await api.createJob(customer.id, uniq('rn-job'));
    const defects = new DefectsPage(page);
    await defects.openJobDefects(jobId);
    await defects.addDefect.click();
    const title = uniq('rn-defect');
    await defects.title.fill(title);
    await defects.description.fill('rn-description-after-edit');
    await defects.close.click(); // closing the menu is what used to lose the edit
    await page.reload();
    await expect(defects.defectRow(title)).toBeVisible();
    await defects.defectRow(title).click();
    await expect(defects.description).toHaveValue('rn-description-after-edit');
  });

  fixme('BUG-04');
  fixme('BUG-05b');
  fixme('BUG-06');
  fixme('BUG-08');

  live('BUG-16', 'the login logo is not squashed against the top of the screen', async ({ browser }) => {
    const context = await browser.newContext(); // signed out
    const page = await context.newPage();
    const login = new LoginPage(page);
    await login.openLogin(env.baseUrl);
    await expect(login.logo).toBeVisible();
    const box = await login.logo.boundingBox();
    expect(box, 'logo has a box').not.toBeNull();
    expect(box?.y ?? 0, 'space above the logo (px)').toBeGreaterThanOrEqual(8); // TODO(confirm): the design spacing; 8 px is a minimum, not the spec
    expect(box?.height ?? 0, 'logo height (px)').toBeGreaterThan(16);
    // TODO: add a visual baseline (toHaveScreenshot) once the approved design is available.
    await context.close();
  });
});
