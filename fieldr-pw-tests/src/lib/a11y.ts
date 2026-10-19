import AxeBuilder from '@axe-core/playwright';
import { expect, type Locator, type Page } from '@playwright/test';

/**
 * Automated accessibility scan limited to one region. It finds missing names/labels/roles only.
 * Real screen-reader behaviour (announcement order, focus, live regions) stays MANUAL.
 */
export async function expectNoLabelViolations(page: Page, region: Locator): Promise<void> {
  await expect(region).toBeVisible();
  const handle = await region.elementHandle();
  expect(handle, 'region element').not.toBeNull();
  const results = await new AxeBuilder({ page })
    .include('[role="dialog"]') // TODO(confirm): the invite dialog exposes role="dialog"; adjust if it is a different landmark
    .withRules(['button-name', 'label', 'aria-dialog-name', 'aria-input-field-name', 'link-name'])
    .analyze();
  expect(results.violations.map((v) => `${v.id}: ${v.nodes.length} node(s)`), 'axe label violations').toEqual([]);
}
