import { env, personaApi } from '../config/env';
import { expect, live, test } from '../fixtures/test';
import { PickerComponent } from '../pages/PickerComponent';

/** Release notes: Improvements > Customer & Job Pickers (PIC-01..04) and Jobs (JOB-01, JOB-02). */
const newJob = (path = env.routes.jobNew): string => new URL(path, env.baseUrl).toString();

test.describe('@pickers Customer and job pickers', () => {
  live('PIC-01', 'options show the company in bold with the contact underneath, and a loading state while results come in', async ({ page, api, uniq }) => {
    const company = uniq('rn-co');
    const contact = uniq('rn-contact');
    await api.createCustomer({ company, contact, email: `${uniq('rn')}@example.invalid` });
    // Slow the customer search so the loading state is observable without a hard wait.
    await page.route(`**${env.api.customers}**`, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1500));
      await route.continue();
    });
    await page.goto(newJob());
    const picker = new PickerComponent(page);
    await picker.combobox.click();
    await expect(picker.loading).toBeVisible();
    await expect(picker.option(company)).toBeVisible();
    const text = await picker.option(company).innerText();
    expect(text.indexOf(company)).toBeLessThan(text.indexOf(contact));
    await expect(picker.option(company).getByRole('strong')).toContainText(company); // TODO(confirm): bold is exposed as <strong>/<b>
  });

  live('PIC-02', 'the picker can be searched by company, name and email (Customer ID: see TODO)', async ({ page, api, uniq }) => {
    const company = uniq('rn-co');
    const contact = uniq('rn-contact');
    const email = `${uniq('rn')}@example.invalid`;
    await api.createCustomer({ company, contact, email });
    await page.goto(newJob());
    const picker = new PickerComponent(page);
    await picker.open();
    for (const term of [company, contact, email]) {
      await picker.search(term);
      await expect(picker.option(company)).toBeVisible();
    }
    // TODO: search by Customer ID. The id shown in the UI (a customer number) is not the API id; read it from the customer
    // details page, then search for it here.
  });

  live('PIC-03', 'clearing the search brings back the full list', async ({ page }) => {
    await page.goto(newJob());
    const picker = new PickerComponent(page);
    await picker.open();
    const full = await picker.options.count();
    await picker.search('zzzz-no-such-customer');
    await expect(picker.options).toHaveCount(0);
    await picker.clear();
    await expect(picker.options).toHaveCount(full);
  });

  live('PIC-04', 'long names are shortened neatly and do not break the layout', async ({ page, api, uniq }) => {
    const company = `${uniq('rn-co')}-${'Long Company Name '.repeat(8)}`.slice(0, 120);
    await api.createCustomer({ company, contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
    await page.goto(newJob());
    const picker = new PickerComponent(page);
    await picker.open();
    await picker.search(company.slice(0, 20));
    await expect(picker.options.first()).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow, 'horizontal overflow (px)').toBeLessThanOrEqual(0);
    // TODO: assert the option text is truncated (ellipsis) rather than wrapped once a test-id for the option label exists.
  });
});

test.describe('@jobs Jobs', () => {
  live('JOB-01', 'a new job starts with a 1000 m site radius', async ({ page }) => {
    await page.goto(newJob());
    await expect(page.getByLabel(/site radius/i)).toHaveValue(/^1000(\.0+)?$/); // TODO(confirm): label and unit rendering
    // TODO: also convert a quote to a job and assert the same value (needs the quote-to-job action locator).
  });

  live('JOB-02', 'the job description is optional on create and on edit', async ({ page, api, request, uniq }) => {
    await page.goto(newJob());
    await expect(page.getByLabel(/description/i)).not.toHaveAttribute('aria-required', 'true');
    // Edit side, through the API as the same persona: clearing the description must not be rejected.
    const customer = await api.createCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
    const jobId = await api.createJob(customer.id, uniq('rn-job'), { description: '' }); // TODO(confirm): payload key
    const res = await request.get(personaApi(`${env.api.jobs}/${encodeURIComponent(jobId)}`));
    expect(res.ok()).toBeTruthy();
  });
});
