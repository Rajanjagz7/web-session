import { env, fill, personaApi } from '../config/env';
import { expect, live, test } from '../fixtures/test';
import { QuotesPage } from '../pages/QuotesPage';
import { downloadPdf, expectMustNotContain } from '../utils/pdf';

/** Release notes: New Features > Quotes (QUO-01..04) and Bug Fixes > Quotes (BUG-02). */
test.describe('@quotes Quotes', () => {
  live('QUO-01', 'a formula column can use Cost Price, Margin % and Markup %', async ({ page, api, uniq }) => {
    const customer = await api.createCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
    const title = uniq('rn-quote');
    await api.createQuote(customer.id, title, [{ name: 'Line A', quantity: 1, sellPrice: 100, costPrice: 60 }]);
    const quotes = new QuotesPage(page);
    await quotes.openList();
    await quotes.openQuote(title);
    const column = uniq('rn-col');
    await quotes.addFormulaColumn(column, ['Cost Price', 'Margin %', 'Markup %']);
    await expect(quotes.columnHeader(column)).toBeVisible();
    // TODO: assert the computed cell values once the margin and markup definitions are confirmed
    // (margin on sell price vs on cost). Seeded line: sell 100, cost 60.
  });

  // Negative: a person who may NOT see cost prices sees none of the internal columns, in the UI or in a customer artefact.
  live('QUO-02', 'cost/margin/markup columns are hidden and absent from the customer PDF', async ({ page, api, request, uniq }) => {
    const customer = await api.createCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
    const title = uniq('rn-quote');
    const quoteId = await api.createQuote(customer.id, title, [{ name: 'Line A', quantity: 1, sellPrice: 100, costPrice: 60 }]);
    const quotes = new QuotesPage(page);
    await quotes.openList();
    await quotes.openQuote(title);
    for (const name of ['Cost Price', 'Margin %', 'Markup %']) {
      await expect(quotes.columnHeader(name)).toHaveCount(0);
    }
    const pdf = await downloadPdf(request, personaApi(fill(env.api.quotePdf, quoteId)));
    expectMustNotContain(pdf);
  });

  // Positive side of the same rule: a cost viewer can use the columns but "Show to Customer" is locked off.
  live(
    'QUO-02',
    '"Show to Customer" is locked off for columns that use cost/margin/markup',
    async ({ page, api, request, uniq }) => {
      const customer = await api.createCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
      const title = uniq('rn-quote');
      const quoteId = await api.createQuote(customer.id, title, [{ name: 'Line A', quantity: 1, sellPrice: 100, costPrice: 60 }]);
      const quotes = new QuotesPage(page);
      await quotes.openList();
      await quotes.openQuote(title);
      const column = uniq('rn-col');
      await quotes.addFormulaColumn(column, ['Margin %']);
      const toggle = quotes.showToCustomerToggle(column);
      await expect(toggle).toBeDisabled();
      await expect(toggle).not.toBeChecked();
      expectMustNotContain(await downloadPdf(request, personaApi(fill(env.api.quotePdf, quoteId))));
    },
    'cost-viewer',
  );

  live('QUO-03', 'a line with no cost price shows a dash, not 0', async ({ page, api, uniq }) => {
    const customer = await api.createCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
    const title = uniq('rn-quote');
    await api.createQuote(customer.id, title, [{ name: 'No cost line', quantity: 1, sellPrice: 100 }]);
    const quotes = new QuotesPage(page);
    await quotes.openList();
    await quotes.openQuote(title);
    const column = uniq('rn-col');
    await quotes.addFormulaColumn(column, ['Cost Price', 'Margin %', 'Markup %']);
    const cell = quotes.cell(column, 'No cost line');
    await expect(cell).toHaveText(/^\s*[-–—]\s*$/); // any dash glyph
    await expect(cell).not.toHaveText(/^\s*0(\.0+)?%?\s*$/);
  });

  live('QUO-04', 'the quote list has a Created By column', async ({ page }) => {
    const quotes = new QuotesPage(page);
    await quotes.openList();
    await expect(quotes.createdByHeader).toBeVisible();
    // TODO: assert the seeded quote's creator name in that column once a stable cell locator (test-id) exists.
  });

  live('BUG-02', 'a new quote does not keep the section name and rows from the previous new quote', async ({ page }) => {
    const quotes = new QuotesPage(page);
    await quotes.openList();
    await quotes.newQuoteButton.click();
    await quotes.sectionNameInputs.first().fill('rn-previous-section'); // TODO(confirm): sections step locator
    await page.goBack(); // leave without saving
    await quotes.newQuoteButton.click();
    await expect(quotes.sectionNameInputs.first()).toHaveValue('');
    await expect(quotes.lineRows).toHaveCount(0);
  });
});
