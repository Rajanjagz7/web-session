import { env, fill, personaApi } from '../config/env';
import { KEY } from '../config/payloads';
import { expect, live, needs, test, type Fx, type Uniq } from '../fixtures/test';
import { JobBudgetPage } from '../pages/JobBudgetPage';

/** Release notes: Job Budget (BUD-01..04), Jobs > budget tile (JOB-03), Bug Fixes > budget prices (BUG-05a). */
async function seedJobWithBudgetLine(api: Fx['api'], uniq: Uniq): Promise<{ jobId: string; quoteId: string }> {
  const customer = await api.createCustomer({ company: uniq('rn-co'), contact: uniq('rn-contact'), email: `${uniq('rn')}@example.invalid` });
  const quoteId = await api.createQuote(customer.id, uniq('rn-quote'), [{ name: 'Line A', quantity: 2, sellPrice: 100, costPrice: 60 }]);
  const jobId = await api.createJob(customer.id, uniq('rn-job'), { [KEY.job.quoteId]: quoteId });
  return { jobId, quoteId };
}

test.describe('@budget Job budget', () => {
  live('BUD-01', 'picking a catalogue item fills sell price and cost price', async ({ page, api, uniq }) => {
    needs(env.fixtures.catalogueConfigured, 'FIXTURE_CATALOGUE_ITEM_EXISTS');
    const { jobId } = await api.seedBudgetJob(uniq);
    const budget = new JobBudgetPage(page);
    await budget.openJob(jobId);
    await budget.openBudgetTab();
    await budget.catalogueItemPicker.click();
    await page.getByRole('option').first().click();
    const row = page.getByRole('row').last(); // TODO: fragile; the new line should be addressable by a test-id
    await expect(row.getByRole('spinbutton', { name: /sell price/i })).not.toHaveValue('');
    await expect(row.getByRole('spinbutton', { name: /cost price/i })).not.toHaveValue('');
  });

  live('BUD-02', 'line total = quantity x sell price and both budget totals are shown', async ({ page, api, uniq }) => {
    const { jobId } = await api.seedBudgetJob(uniq);
    const budget = new JobBudgetPage(page);
    await budget.openJob(jobId);
    await budget.openBudgetTab();
    await budget.quantity('Line A').fill('3');
    await budget.sellPrice('Line A').fill('25');
    await expect(budget.lineTotal('Line A')).toContainText('75'); // 3 x 25
    await expect(budget.jobBudgetTotal).toBeVisible();
    await expect(budget.costBudgetTotal).toBeVisible();
  });

  // Negative: without the cost-price permission neither the UI nor the API exposes prices.
  live('BUD-03', 'prices are hidden in the UI and absent from the API for a user without cost-price permission', async ({ page, request, api, uniq }) => {
    const { jobId } = await api.seedBudgetJob(uniq);
    const budget = new JobBudgetPage(page);
    await budget.openJob(jobId);
    await budget.openBudgetTab();
    await expect(page.getByRole('spinbutton', { name: /cost price/i })).toHaveCount(0);
    await expect(page.getByRole('spinbutton', { name: /sell price/i })).toHaveCount(0);
    const res = await request.get(personaApi(fill(env.api.jobBudget, jobId)));
    if (res.status() !== 403) {
      expect(res.ok()).toBeTruthy();
      expect(await res.text(), 'price fields must not be in the response body').not.toContain(KEY.quote.lineCost); // TODO(confirm): real field names
    }
  });

  live('BUD-04', 'the Job Budget tile shows what is left after costs (or how far over)', async ({ page, api, uniq }) => {
    const { jobId } = await api.seedBudgetJob(uniq);
    const budget = new JobBudgetPage(page);
    await budget.openJob(jobId);
    await expect(budget.remainingBudgetTile).toBeVisible();
    // TODO: assert the exact remaining amount. Seeded budget: 2 x 100 = 200 sell, cost 2 x 60 = 120; the notes do not say
    // whether the tile shows budget minus cost-so-far or minus total cost, so the expected number is left to fill in.
  });

  live('JOB-03', 'the tile is "Lines Over Planned Qty", shows a count like "2 of 5" and has a caption', async ({ page, api, uniq }) => {
    const { jobId } = await api.seedBudgetJob(uniq);
    const budget = new JobBudgetPage(page);
    await budget.openJob(jobId);
    await expect(budget.linesOverPlannedQtyTile).toBeVisible();
    await expect(budget.linesOverPlannedQtyTile).toContainText(/\d+ of \d+/);
    // TODO: assert the caption text once it is confirmed (the notes say a caption exists but not its wording).
    await expect(page.getByText('Budget quantity')).toHaveCount(0); // the old tile name is gone
  });

  live('BUG-05a', 'editing the job budget no longer wipes the prices copied from the quote', async ({ page, api, uniq }) => {
    const { jobId } = await api.seedBudgetJob(uniq);
    const budget = new JobBudgetPage(page);
    await budget.openJob(jobId);
    await budget.openBudgetTab();
    await expect(budget.sellPrice('Line A')).toHaveValue('100');
    await expect(budget.costPrice('Line A')).toHaveValue('60');
    await budget.quantity('Line A').fill('5');
    await budget.saveButton.click();
    await page.reload();
    await budget.openBudgetTab();
    await expect(budget.sellPrice('Line A')).toHaveValue('100');
    await expect(budget.costPrice('Line A')).toHaveValue('60');
  });
});
