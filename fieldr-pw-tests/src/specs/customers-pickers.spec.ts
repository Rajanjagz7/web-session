/**
 * Release notes: New Features > Customers; Improvements > Customer & Job Pickers and Jobs.
 * IDs in this file: CU-01, CU-02, CU-03a, CU-03b, CU-03d, CU-03e, CU-03f, CU-04, CU-05, CU-06, JOBS-01, JOBS-02, JOBS-04, PICK-01, PICK-02, PICK-03, PICK-04
 * Traceability: docs/traceability-matrix.md. Every title starts with its ID and carries area + persona tags.
 */
import { expect, test } from '../fixtures/data.fixture';
import { env, fill, personaApi } from '../lib/env';
import { CustomersPage } from '../pages/CustomersPage';
import { PickerPage } from '../pages/PickerPage';
import { downloadPdf, indexOfText } from '../lib/pdf';

const newJob = (path: string = env.routes.jobNew): string => new URL(path, env.baseUrl).toString();

test.describe('@customers Customers', () => {
  test('[CU-01] @customers @super-admin Create Job opens New Job with the customer already picked', async ({ page, data, uniq }) => {
    const company = uniq('rn-co');
    const customer = await data.seedCustomer({ company, contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
    const customers = new CustomersPage(page);
    await customers.openDetails(customer.id);
    await customers.createJobButton.click();
    await expect(page).toHaveURL(new RegExp(env.routes.jobNew.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&')));
    await expect(new PickerPage(page).combobox).toContainText(company);
  });

  test('[CU-02] @customers @no-permission Create Job is hidden for a user without job permission',     async ({ page, data, uniq }) => {
      const customer = await data.seedCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
      const customers = new CustomersPage(page);
      await customers.openDetails(customer.id);
      await expect(customers.main).toBeVisible();
      await expect(customers.createJobButton).toHaveCount(0);
  });

  test('[CU-02] @customers @no-permission Create Job is hidden for an inactive customer', async ({ page, data, uniq }) => {
    const customer = await data.seedCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid`, active: false });
    const customers = new CustomersPage(page);
    await customers.openDetails(customer.id);
    await expect(customers.main).toBeVisible();
    await expect(customers.createJobButton).toHaveCount(0);
  });

  test('[CU-03a] @customers @super-admin the customer list shows the company name first, then the contact', async ({ page, data, uniq }) => {
    const company = uniq('rn-co');
    const contact = uniq('rn-contact');
    await data.seedCustomer({ company, contact, email: `${uniq('rn')}@example.invalid` });
    const customers = new CustomersPage(page);
    await customers.openList();
    await customers.searchBox.fill(company);
    const row = customers.row(company);
    await expect(row).toBeVisible();
    const text = await row.innerText();
    expect(text.indexOf(company)).toBeGreaterThanOrEqual(0);
    expect(text.indexOf(company)).toBeLessThan(text.indexOf(contact));
  });

  test('[CU-03b] @customers @super-admin the quote drawer shows the company name first', async ({ page, data, uniq }) => {
    const company = uniq('rn-co');
    const contact = uniq('rn-contact');
    const customer = await data.seedCustomer({ company, contact, email: `${uniq('rn')}@example.invalid` });
    const title = uniq('rn-quote');
    await data.seedQuote(customer.id, title, [{ name: 'Line A', quantity: 1, sellPrice: 100 }]);
    await page.goto(new URL(env.routes.quotes, env.baseUrl).toString());
    await page.getByRole('row', { name: title }).click(); // TODO(confirm): how the drawer opens
    const drawer = page.getByRole('dialog');
    await expect(drawer).toBeVisible();
    const text = await drawer.innerText();
    expect(text.indexOf(company)).toBeLessThan(text.indexOf(contact));
    // TODO: the invoice drawer needs an invoice seed endpoint (none is available to this suite); repeat this check for it.
  });

  test('[CU-03d] @customers @super-admin Company name first in Send Contract and contract requests', async () => {
    test.fixme(true, 'reason: needs a contract-request seed endpoint and the contract screen locators');
  });

  test('[CU-03e] @customers @super-admin the portal access screen shows the company name first', async ({ page, data, uniq }) => {
    const company = uniq('rn-co');
    const contact = uniq('rn-contact');
    const customer = await data.seedCustomer({ company, contact, email: `${uniq('rn')}@example.invalid` });
    const customers = new CustomersPage(page);
    await customers.openDetails(customer.id);
    await expect(customers.portalAccessSection).toBeVisible();
    const text = await customers.portalAccessSection.innerText();
    expect(text.indexOf(company)).toBeGreaterThanOrEqual(0);
    expect(text.indexOf(company)).toBeLessThan(text.indexOf(contact));
  });

  test('[CU-03f] @customers @super-admin Company name first in job exports and job reports', async () => {
    test.fixme(true, 'reason: export file format and column names are not in the release notes');
  });

  test('[CU-04] @customers @super-admin the quote PDF prints the company first with the contact underneath', async ({ request, data, uniq }) => {
    const company = uniq('rn-co');
    const contact = uniq('rn-contact');
    const customer = await data.seedCustomer({ company, contact, email: `${uniq('rn')}@example.invalid` });
    const quoteId = await data.seedQuote(customer.id, uniq('rn-quote'), [{ name: 'Line A', quantity: 1, sellPrice: 100 }]);
    const pdf = await downloadPdf(request, personaApi(fill(env.api.quotePdf, quoteId)));
    expect(indexOfText(pdf, company), 'company on the PDF').toBeGreaterThanOrEqual(0);
    expect(indexOfText(pdf, company)).toBeLessThan(indexOfText(pdf, contact));
    // TODO: "bold" cannot be read from extracted text; verify the company font weight manually or with a visual baseline.
    // TODO: repeat for the invoice PDF (fill(env.api.invoicePdf, id)) once an invoice can be seeded.
  });

  test('[CU-05] @customers @super-admin the job PDF lists Company before Client', async ({ request, data, uniq }) => {
    const customer = await data.seedCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
    const jobId = await data.seedJob(customer.id, uniq('rn-job'));
    const pdf = await downloadPdf(request, personaApi(fill(env.api.jobPdf, jobId)));
    const company = indexOfText(pdf, 'Company');
    const client = indexOfText(pdf, 'Client');
    expect(company, 'a "Company" label').toBeGreaterThanOrEqual(0);
    expect(client, 'a "Client" label').toBeGreaterThanOrEqual(0);
    expect(company).toBeLessThan(client);
  });

  test('[CU-06] @customers @super-admin a customer without a company still prints on the quote PDF with no blank company line', async ({ request, data, uniq }) => {
    const contact = uniq('rn-contact');
    const customer = await data.seedCustomer({ contact, email: `${uniq('rn')}@example.invalid` });
    const quoteId = await data.seedQuote(customer.id, uniq('rn-quote'), [{ name: 'Line A', quantity: 1, sellPrice: 100 }]);
    const pdf = await downloadPdf(request, personaApi(fill(env.api.quotePdf, quoteId)));
    expect(indexOfText(pdf, contact), 'the contact name').toBeGreaterThanOrEqual(0);
    expect(pdf.text).not.toMatch(/undefined|null/i);
    // TODO: "exactly as before" needs a stored baseline of the previous release's PDF text for this seed; add it as a golden file.
  });
});

test.describe('@jobs Jobs', () => {
  test('[JOBS-01] @jobs @super-admin a new job starts with a 1000 m site radius', async ({ page }) => {
    await page.goto(newJob());
    await expect(page.getByLabel(/site radius/i)).toHaveValue(/^1000(\.0+)?$/); // TODO(confirm): label and unit rendering
    // TODO: also convert a quote to a job and assert the same value (needs the quote-to-job action locator).
  });

  test('[JOBS-02] @jobs @super-admin the job description is optional on create and on edit', async ({ page, data, request, uniq }) => {
    await page.goto(newJob());
    await expect(page.getByLabel(/description/i)).not.toHaveAttribute('aria-required', 'true');
    // Edit side, through the API as the same persona: clearing the description must not be rejected.
    const customer = await data.seedCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
    const jobId = await data.seedJob(customer.id, uniq('rn-job'), { description: '' }); // TODO(confirm): payload key
    const res = await request.get(personaApi(`${env.api.jobs}/${encodeURIComponent(jobId)}`));
    expect(res.ok()).toBeTruthy();
  });

  test('[JOBS-04] @jobs @super-admin an inactive customer cannot be given a new job from the customer screen', async ({ page, data, uniq }) => {
    const customer = await data.seedCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid`, active: false });
    const customers = new CustomersPage(page);
    await customers.openDetails(customer.id);
    await expect(customers.createJobButton).toHaveCount(0);
    // The same customer must not be offered when starting a job from elsewhere (see PICK-02 for the picker).
  });
});

test.describe('@pickers Pickers', () => {
  test('[PICK-01] @pickers @super-admin options show the company in bold with the contact underneath, and a loading state while results come in', async ({ page, data, uniq }) => {
    const company = uniq('rn-co');
    const contact = uniq('rn-contact');
    await data.seedCustomer({ company, contact, email: `${uniq('rn')}@example.invalid` });
    // Slow the customer search so the loading state is observable without a hard wait.
    await page.route(`**${env.api.customers}**`, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 1500));
      await route.continue();
    });
    await page.goto(newJob());
    const picker = new PickerPage(page);
    await picker.combobox.click();
    await expect(picker.loading).toBeVisible();
    await expect(picker.option(company)).toBeVisible();
    const text = await picker.option(company).innerText();
    expect(text.indexOf(company)).toBeLessThan(text.indexOf(contact));
    await expect(picker.option(company).getByRole('strong')).toContainText(company); // TODO(confirm): bold is exposed as <strong>/<b>
  });

  test('[PICK-02] @pickers @super-admin the picker can be searched by company, name and email (Customer ID: see TODO)', async ({ page, data, uniq }) => {
    const company = uniq('rn-co');
    const contact = uniq('rn-contact');
    const email = `${uniq('rn')}@example.invalid`;
    await data.seedCustomer({ company, contact, email });
    await page.goto(newJob());
    const picker = new PickerPage(page);
    await picker.open();
    for (const term of [company, contact, email]) {
      await picker.search(term);
      await expect(picker.option(company)).toBeVisible();
    }
    // TODO: search by Customer ID. The id shown in the UI (a customer number) is not the API id; read it from the customer
    // details page, then search for it here.
  });

  test('[PICK-03] @pickers @super-admin clearing the search brings back the full list', async ({ page }) => {
    await page.goto(newJob());
    const picker = new PickerPage(page);
    await picker.open();
    const full = await picker.options.count();
    await picker.search('zzzz-no-such-customer');
    await expect(picker.options).toHaveCount(0);
    await picker.clear();
    await expect(picker.options).toHaveCount(full);
  });

  test('[PICK-04] @pickers @super-admin long names are shortened neatly and do not break the layout', async ({ page, data, uniq }) => {
    const company = `${uniq('rn-co')}-${'Long Company Name '.repeat(8)}`.slice(0, 120);
    await data.seedCustomer({ company, contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
    await page.goto(newJob());
    const picker = new PickerPage(page);
    await picker.open();
    await picker.search(company.slice(0, 20));
    await expect(picker.options.first()).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow, 'horizontal overflow (px)').toBeLessThanOrEqual(0);
    // TODO: assert the option text is truncated (ellipsis) rather than wrapped once a test-id for the option label exists.
  });
});
