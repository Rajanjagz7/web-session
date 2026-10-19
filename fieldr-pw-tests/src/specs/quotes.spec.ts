/**
 * Release notes: New Features > Quotes.
 * IDs in this file: QUO-01, QUO-02, QUO-03, QUO-04
 * Traceability: docs/traceability-matrix.md. Every title starts with its ID and carries area + persona tags.
 */
import { expect, test } from '../fixtures/data.fixture';
import { env, fill, personaApi } from '../lib/env';
import { QuotesPage } from '../pages/QuotesPage';
import { downloadPdf, expectMustNotContain } from '../lib/pdf';

test.describe('@quotes Quotes', () => {
  test('[QUO-01] @quotes @cost-viewer a formula column can use Cost Price, Margin % and Markup %', async ({ page, data, uniq }) => {
    const customer = await data.seedCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
    const title = uniq('rn-quote');
    await data.seedQuote(customer.id, title, [{ name: 'Line A', quantity: 1, sellPrice: 100, costPrice: 60 }]);
    const quotes = new QuotesPage(page);
    await quotes.openList();
    await quotes.openQuote(title);
    const column = uniq('rn-col');
    await quotes.addFormulaColumn(column, ['Cost Price', 'Margin %', 'Markup %']);
    await expect(quotes.columnHeader(column)).toBeVisible();
    // TODO: assert the computed cell values once the margin and markup definitions are confirmed
    // (margin on sell price vs on cost). Seeded line: sell 100, cost 60.
  });

  test('[QUO-02] @quotes @no-cost-viewer cost/margin/markup columns are hidden and absent from the customer PDF', async ({ page, data, request, uniq }) => {
    const customer = await data.seedCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
    const title = uniq('rn-quote');
    const quoteId = await data.seedQuote(customer.id, title, [{ name: 'Line A', quantity: 1, sellPrice: 100, costPrice: 60 }]);
    const quotes = new QuotesPage(page);
    await quotes.openList();
    await quotes.openQuote(title);
    for (const name of ['Cost Price', 'Margin %', 'Markup %']) {
      await expect(quotes.columnHeader(name)).toHaveCount(0);
    }
    const pdf = await downloadPdf(request, personaApi(fill(env.api.quotePdf, quoteId)));
    expectMustNotContain(pdf);
  });

  test('[QUO-02] @quotes @cost-viewer "Show to Customer" is locked off for columns that use cost/margin/markup',     async ({ page, data, request, uniq }) => {
      const customer = await data.seedCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
      const title = uniq('rn-quote');
      const quoteId = await data.seedQuote(customer.id, title, [{ name: 'Line A', quantity: 1, sellPrice: 100, costPrice: 60 }]);
      const quotes = new QuotesPage(page);
      await quotes.openList();
      await quotes.openQuote(title);
      const column = uniq('rn-col');
      await quotes.addFormulaColumn(column, ['Margin %']);
      const toggle = quotes.showToCustomerToggle(column);
      await expect(toggle).toBeDisabled();
      await expect(toggle).not.toBeChecked();
      expectMustNotContain(await downloadPdf(request, personaApi(fill(env.api.quotePdf, quoteId))));
  });

  test('[QUO-03] @quotes @cost-viewer a line with no cost price shows a dash, not 0', async ({ page, data, uniq }) => {
    const customer = await data.seedCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
    const title = uniq('rn-quote');
    await data.seedQuote(customer.id, title, [{ name: 'No cost line', quantity: 1, sellPrice: 100 }]);
    const quotes = new QuotesPage(page);
    await quotes.openList();
    await quotes.openQuote(title);
    const column = uniq('rn-col');
    await quotes.addFormulaColumn(column, ['Cost Price', 'Margin %', 'Markup %']);
    const cell = quotes.cell(column, 'No cost line');
    await expect(cell).toHaveText(/^\s*[-–—]\s*$/); // any dash glyph
    await expect(cell).not.toHaveText(/^\s*0(\.0+)?%?\s*$/);
  });

  test('[QUO-04] @quotes @super-admin the quote list has a Created By column', async ({ page }) => {
    const quotes = new QuotesPage(page);
    await quotes.openList();
    await expect(quotes.createdByHeader).toBeVisible();
    // TODO: assert the seeded quote's creator name in that column once a stable cell locator (test-id) exists.
  });
});
