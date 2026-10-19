/**
 * Release notes: New Features > Job Budget; Improvements > Jobs (budget tile).
 * IDs in this file: JB-01, JB-02, JB-03, JB-04, JOBS-03
 * Traceability: docs/traceability-matrix.md. Every title starts with its ID and carries area + persona tags.
 */
import { expect, needs, test } from '../fixtures/data.fixture';
import { env, fill, personaApi } from '../lib/env';
import { KEY } from '../lib/payloads';
import { JobBudgetPage } from '../pages/JobBudgetPage';

test.describe('@jobs Job Budget', () => {
  test('[JB-01] @jobs @cost-viewer picking a catalogue item fills sell price and cost price', async ({ page, data, uniq }) => {
    needs(env.fixtures.catalogueConfigured, 'FIXTURE_CATALOGUE_ITEM_EXISTS');
    const { jobId } = await data.seedBudgetJob(uniq);
    const budget = new JobBudgetPage(page);
    await budget.openJob(jobId);
    await budget.openBudgetTab();
    await budget.catalogueItemPicker.click();
    await page.getByRole('option').first().click();
    const row = page.getByRole('row').last(); // TODO: fragile; the new line should be addressable by a test-id
    await expect(row.getByRole('spinbutton', { name: /sell price/i })).not.toHaveValue('');
    await expect(row.getByRole('spinbutton', { name: /cost price/i })).not.toHaveValue('');
  });

  test('[JB-02] @jobs @cost-viewer line total = quantity x sell price and both budget totals are shown', async ({ page, data, uniq }) => {
    const { jobId } = await data.seedBudgetJob(uniq);
    const budget = new JobBudgetPage(page);
    await budget.openJob(jobId);
    await budget.openBudgetTab();
    await budget.quantity('Line A').fill('3');
    await budget.sellPrice('Line A').fill('25');
    await expect(budget.lineTotal('Line A')).toContainText('75'); // 3 x 25
    await expect(budget.jobBudgetTotal).toBeVisible();
    await expect(budget.costBudgetTotal).toBeVisible();
  });

  test('[JB-03] @jobs @no-cost-viewer prices are hidden in the UI and absent from the API for a user without cost-price permission', async ({ page, request, data, uniq }) => {
    const { jobId } = await data.seedBudgetJob(uniq);
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

  test('[JB-04] @jobs @cost-viewer the Job Budget tile shows what is left after costs (or how far over)', async ({ page, data, uniq }) => {
    const { jobId } = await data.seedBudgetJob(uniq);
    const budget = new JobBudgetPage(page);
    await budget.openJob(jobId);
    await expect(budget.remainingBudgetTile).toBeVisible();
    // TODO: assert the exact remaining amount. Seeded budget: 2 x 100 = 200 sell, cost 2 x 60 = 120; the notes do not say
    // whether the tile shows budget minus cost-so-far or minus total cost, so the expected number is left to fill in.
  });
});

test.describe('@jobs Jobs', () => {
  test('[JOBS-03] @jobs @cost-viewer the tile is "Lines Over Planned Qty", shows a count like "2 of 5" and has a caption', async ({ page, data, uniq }) => {
    const { jobId } = await data.seedBudgetJob(uniq);
    const budget = new JobBudgetPage(page);
    await budget.openJob(jobId);
    await expect(budget.linesOverPlannedQtyTile).toBeVisible();
    await expect(budget.linesOverPlannedQtyTile).toContainText(/\d+ of \d+/);
    // TODO: assert the caption text once it is confirmed (the notes say a caption exists but not its wording).
    await expect(page.getByRole('main')).not.toContainText('Budget quantity'); // the old tile name is gone
  });
});
