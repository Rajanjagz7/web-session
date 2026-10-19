import { env } from '../config/env';
import { expect, fixme, live, test } from '../fixtures/test';
import { JobOrderPage } from '../pages/JobOrderPage';
import { UserFormPage } from '../pages/UserFormPage';

/** Release notes: Improvements > Job Orders (ORD-01..03) and Phone Numbers (PHN-01). */
test.describe('@joborders Job orders', () => {
  live('ORD-01', '"Phone" is now "Mobile Number" and "Site Contact" is now "Site Contact Name"', async ({ page }) => {
    const order = new JobOrderPage(page);
    await order.openNewOrder();
    await expect(order.mobileNumber).toBeVisible();
    await expect(order.siteContactName).toBeVisible();
    await expect(order.oldPhoneLabel).toHaveCount(0);
    await expect(order.oldSiteContactLabel).toHaveCount(0);
  });

  fixme('ORD-02');

  live('ORD-03', 'Add Line adds a line and scrolls the page to it', async ({ page }) => {
    const order = new JobOrderPage(page);
    await order.openNewOrder();
    const before = await order.lineRows.count();
    await order.addLine.click();
    await expect(order.lineRows).toHaveCount(before + 1);
    await expect(order.lineRows.last()).toBeInViewport();
  });
});

test.describe('@phone Phone numbers', () => {
  live('PHN-01', 'a phone number is formatted identically across forms', async ({ page }) => {
    const raw = '0412345678';
    const shown: string[] = [];
    // Form 1: job order
    const order = new JobOrderPage(page);
    await order.openNewOrder();
    await order.mobileNumber.fill(raw);
    await order.mobileNumber.blur();
    shown.push(await order.mobileNumber.inputValue());
    // Form 2: My Profile
    const profile = new UserFormPage(page);
    await profile.openProfile();
    await profile.mobile.fill(raw);
    await profile.mobile.blur();
    shown.push(await profile.mobile.inputValue());
    // Form 3: customer form. TODO: sign-up and customer-contract forms need their own page objects and routes.
    await page.goto(new URL(env.routes.customers, env.baseUrl).toString());
    await page.getByRole('button', { name: /new customer|add customer/i }).click(); // TODO(confirm)
    const customerMobile = page.getByLabel(/mobile|phone/i);
    await customerMobile.fill(raw);
    await customerMobile.blur();
    shown.push(await customerMobile.inputValue());
    expect(new Set(shown).size, `values shown: ${JSON.stringify(shown)}`).toBe(1);
    if (env.expected.phoneDisplayFormat !== '') expect(shown[0]).toBe(env.expected.phoneDisplayFormat); // TODO: fill EXPECTED_PHONE_DISPLAY_FORMAT
  });
});
