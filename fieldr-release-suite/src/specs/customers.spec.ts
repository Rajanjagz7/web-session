import { env, fill, personaApi } from '../config/env';
import { expect, fixme, live, test } from '../fixtures/test';
import { CustomersPage } from '../pages/CustomersPage';
import { PickerComponent } from '../pages/PickerComponent';
import { downloadPdf, indexOfText } from '../utils/pdf';

/** Release notes: New Features > Customers (CUS-01..06), Improvements > Jobs (JOB-04). */
test.describe('@customers Customers', () => {
  live('CUS-01', 'Create Job opens New Job with the customer already picked', async ({ page, api, uniq }) => {
    const company = uniq('rn-co');
    const customer = await api.createCustomer({ company, contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
    const customers = new CustomersPage(page);
    await customers.openDetails(customer.id);
    await customers.createJobButton.click();
    await expect(page).toHaveURL(new RegExp(env.routes.jobNew.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&')));
    await expect(new PickerComponent(page).combobox).toContainText(company);
  });

  // Negative 1: no job permission.
  live(
    'CUS-02',
    'Create Job is hidden for a user without job permission',
    async ({ page, api, uniq }) => {
      const customer = await api.createCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
      const customers = new CustomersPage(page);
      await customers.openDetails(customer.id);
      await expect(customers.main).toBeVisible();
      await expect(customers.createJobButton).toHaveCount(0);
    },
    'no-permission',
  );

  // Negative 2: inactive customer, even for a user who has job permission.
  live('CUS-02', 'Create Job is hidden for an inactive customer', async ({ page, api, uniq }) => {
    const customer = await api.createCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid`, active: false });
    const customers = new CustomersPage(page);
    await customers.openDetails(customer.id);
    await expect(customers.main).toBeVisible();
    await expect(customers.createJobButton).toHaveCount(0);
  });

  live('CUS-03a', 'the customer list shows the company name first, then the contact', async ({ page, api, uniq }) => {
    const company = uniq('rn-co');
    const contact = uniq('rn-contact');
    await api.createCustomer({ company, contact, email: `${uniq('rn')}@example.invalid` });
    const customers = new CustomersPage(page);
    await customers.openList();
    await customers.searchBox.fill(company);
    const row = customers.row(company);
    await expect(row).toBeVisible();
    const text = await row.innerText();
    expect(text.indexOf(company)).toBeGreaterThanOrEqual(0);
    expect(text.indexOf(company)).toBeLessThan(text.indexOf(contact));
  });

  live('CUS-03b', 'the quote drawer shows the company name first', async ({ page, api, uniq }) => {
    const company = uniq('rn-co');
    const contact = uniq('rn-contact');
    const customer = await api.createCustomer({ company, contact, email: `${uniq('rn')}@example.invalid` });
    const title = uniq('rn-quote');
    await api.createQuote(customer.id, title, [{ name: 'Line A', quantity: 1, sellPrice: 100 }]);
    await page.goto(new URL(env.routes.quotes, env.baseUrl).toString());
    await page.getByRole('row', { name: title }).click(); // TODO(confirm): how the drawer opens
    const drawer = page.getByRole('dialog');
    await expect(drawer).toBeVisible();
    const text = await drawer.innerText();
    expect(text.indexOf(company)).toBeLessThan(text.indexOf(contact));
    // TODO: the invoice drawer needs an invoice seed endpoint (none is available to this suite); repeat this check for it.
  });

  fixme('CUS-03d');

  live('CUS-03e', 'the portal access screen shows the company name first', async ({ page, api, uniq }) => {
    const company = uniq('rn-co');
    const contact = uniq('rn-contact');
    const customer = await api.createCustomer({ company, contact, email: `${uniq('rn')}@example.invalid` });
    const customers = new CustomersPage(page);
    await customers.openDetails(customer.id);
    await expect(customers.portalAccessSection).toBeVisible();
    const text = await customers.portalAccessSection.innerText();
    expect(text.indexOf(company)).toBeGreaterThanOrEqual(0);
    expect(text.indexOf(company)).toBeLessThan(text.indexOf(contact));
  });

  fixme('CUS-03f');

  live('CUS-04', 'the quote PDF prints the company first with the contact underneath', async ({ request, api, uniq }) => {
    const company = uniq('rn-co');
    const contact = uniq('rn-contact');
    const customer = await api.createCustomer({ company, contact, email: `${uniq('rn')}@example.invalid` });
    const quoteId = await api.createQuote(customer.id, uniq('rn-quote'), [{ name: 'Line A', quantity: 1, sellPrice: 100 }]);
    const pdf = await downloadPdf(request, personaApi(fill(env.api.quotePdf, quoteId)));
    expect(indexOfText(pdf, company), 'company on the PDF').toBeGreaterThanOrEqual(0);
    expect(indexOfText(pdf, company)).toBeLessThan(indexOfText(pdf, contact));
    // TODO: "bold" cannot be read from extracted text; verify the company font weight manually or with a visual baseline.
    // TODO: repeat for the invoice PDF (fill(env.api.invoicePdf, id)) once an invoice can be seeded.
  });

  live('CUS-05', 'the job PDF lists Company before Client', async ({ request, api, uniq }) => {
    const customer = await api.createCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
    const jobId = await api.createJob(customer.id, uniq('rn-job'));
    const pdf = await downloadPdf(request, personaApi(fill(env.api.jobPdf, jobId)));
    const company = indexOfText(pdf, 'Company');
    const client = indexOfText(pdf, 'Client');
    expect(company, 'a "Company" label').toBeGreaterThanOrEqual(0);
    expect(client, 'a "Client" label').toBeGreaterThanOrEqual(0);
    expect(company).toBeLessThan(client);
  });

  live('CUS-06', 'a customer without a company still prints on the quote PDF with no blank company line', async ({ request, api, uniq }) => {
    const contact = uniq('rn-contact');
    const customer = await api.createCustomer({ contact, email: `${uniq('rn')}@example.invalid` });
    const quoteId = await api.createQuote(customer.id, uniq('rn-quote'), [{ name: 'Line A', quantity: 1, sellPrice: 100 }]);
    const pdf = await downloadPdf(request, personaApi(fill(env.api.quotePdf, quoteId)));
    expect(indexOfText(pdf, contact), 'the contact name').toBeGreaterThanOrEqual(0);
    expect(pdf.text).not.toMatch(/undefined|null/i);
    // TODO: "exactly as before" needs a stored baseline of the previous release's PDF text for this seed; add it as a golden file.
  });

  live('JOB-04', 'an inactive customer cannot be given a new job from the customer screen', async ({ page, api, uniq }) => {
    const customer = await api.createCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid`, active: false });
    const customers = new CustomersPage(page);
    await customers.openDetails(customer.id);
    await expect(customers.createJobButton).toHaveCount(0);
    // The same customer must not be offered when starting a job from elsewhere (see PIC-02 for the picker).
  });
});
