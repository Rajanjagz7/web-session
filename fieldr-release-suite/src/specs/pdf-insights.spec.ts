import { env, fill, personaApi } from '../config/env';
import { expect, fixme, live, needs, test } from '../fixtures/test';
import { InsightsPage } from '../pages/InsightsPage';
import { blankPages, downloadPdf } from '../utils/pdf';

/** Release notes: Improvements > PDFs (PDF-01..03) and Insights (INS-01, INS-02) plus Insights bug fixes (BUG-10..13, fixme). */
// Standard Australian ABN layout "XX XXX XXX XXX". TODO(confirm): the release notes say "properly formatted" without a pattern.
const ABN_SPACED = /\b\d{2} \d{3} \d{3} \d{3}\b/;
const ABN_UNSPACED = /\b\d{11}\b/;

test.describe('@pdf PDFs', () => {
  live('PDF-01', 'the order PDF shows the ABN formatted and has clearer labels', async ({ request }) => {
    needs(env.fixtures.orderId, 'FIXTURE_ORDER_ID');
    const pdf = await downloadPdf(request, personaApi(fill(env.api.orderPdf, env.fixtures.orderId)));
    expect(pdf.text, 'a formatted ABN').toMatch(ABN_SPACED);
    expect(pdf.text, 'no unformatted 11-digit ABN').not.toMatch(ABN_UNSPACED);
    if (env.expected.abnDisplayFormat !== '') expect(pdf.text).toContain(env.expected.abnDisplayFormat); // TODO: fill EXPECTED_ABN_DISPLAY_FORMAT
    // TODO: assert the new label wording once the notes say what "clearer labels" are (compare with Mobile Number / Site Contact Name in ORD-01).
  });

  live('PDF-02', 'the company ABN is formatted on reports too', async ({ request }) => {
    needs(env.fixtures.reportId, 'FIXTURE_REPORT_ID');
    const pdf = await downloadPdf(request, personaApi(fill(env.api.reportPdf, env.fixtures.reportId)));
    expect(pdf.text).toMatch(ABN_SPACED);
    expect(pdf.text).not.toMatch(ABN_UNSPACED);
  });

  live('PDF-03', 'timesheet PDFs have no blank pages', async ({ request }) => {
    const pdf = await downloadPdf(request, personaApi(env.api.timesheetPdf));
    expect(pdf.pages.length, 'at least one page').toBeGreaterThan(0);
    expect(blankPages(pdf), 'blank page numbers').toEqual([]);
    // TODO: seed a timesheet range that previously produced blank pages (the notes do not say which) for a sharper regression.
  });
});

test.describe('@insights Insights', () => {
  live('INS-01', 'reports show the status, customer and worker filters', async ({ page }) => {
    const insights = new InsightsPage(page);
    await insights.openInsights();
    await insights.reportLink(/./).first().click(); // TODO: iterate over each report; the report names are unconfirmed
    await expect(insights.statusFilter).toBeVisible();
    await expect(insights.customerFilter).toBeVisible();
    await expect(insights.workerFilter).toBeVisible();
  });

  live('INS-02', 'percentages on cards use the same rounding as the table', async ({ page }) => {
    const insights = new InsightsPage(page);
    await insights.openInsights();
    const decimals = (s: string): number[] => [...s.matchAll(/(\d+)(?:\.(\d+))?%/g)].map((m) => (m[2] ?? '').length);
    const cardPct = decimals(await insights.cards.allInnerTexts().then((t) => t.join(' ')));
    const tablePct = decimals(await insights.tableCells.allInnerTexts().then((t) => t.join(' ')));
    expect(cardPct.length + tablePct.length, 'percentages found').toBeGreaterThan(0);
    // Proxy check: cards and table use the same number of decimal places. TODO: replace with an exact per-metric comparison
    // (card figure === table figure for the same metric) once cards and rows share a test-id per metric.
    expect(new Set([...cardPct, ...tablePct]).size, 'one rounding style across cards and table').toBe(1);
  });

  fixme('BUG-10');
  fixme('BUG-11');
  fixme('BUG-12');
  fixme('BUG-13');
});
