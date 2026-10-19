import { test, expect } from '@playwright/test';
import { login, openJobDetail, openJobDetailTab, controlForLabel, fieldExists } from './helpers';

// A signed, "Site Assessment Complete" job with at least one product -
// reused across this file's tests since they're read/no-persist-expected
// checks, not destructive edits (the whole point is that Save doesn't
// persist, so re-running these repeatedly is safe).
const SIGNED_JOB = 'M8N000114';

test.describe('KNOWN BUGS (BUG-02): "Save" fires zero network requests on signed-job edit tabs', () => {
  /**
   * All three of these currently assert the ACTUAL (buggy) behaviour - zero
   * requests fired - so the suite catches a regression either way: if this
   * starts failing because a request DOES fire, that's BUG-02 being fixed
   * and these assertions should be flipped to check the request succeeds
   * and the edited value persists after reload.
   */
  async function countRequestsOnSave(page: import('@playwright/test').Page, saveAction: () => Promise<void>) {
    const fired: string[] = [];
    const handler = (req: import('@playwright/test').Request) => {
      if (['POST', 'PATCH', 'PUT'].includes(req.method())) fired.push(`${req.method()} ${req.url()}`);
    };
    page.on('request', handler);
    await saveAction();
    await page.waitForTimeout(2500);
    page.off('request', handler);
    return fired;
  }

  test('Job Information tab: editing Own Reference and clicking Save fires no request', async ({ page }) => {
    await login(page);
    await openJobDetail(page, SIGNED_JOB);

    const refField = page.locator('input[name="ownReference"]').first();
    await refField.fill('REGRESSION-CHECK-' + Date.now());

    const fired = await countRequestsOnSave(page, async () => {
      await page.getByRole('button', { name: /^save$/i }).first().click();
    });
    expect(fired).toEqual([]);
  });

  test('Post Install Details tab: editing CES Number and clicking Save fires no request', async ({ page }) => {
    await login(page);
    await openJobDetail(page, SIGNED_JOB);
    await openJobDetailTab(page, 'Post Install Details');

    await page.getByPlaceholder('Enter Certificate of Electrical Safety Number').fill('REGRESSION-CES-' + Date.now());

    const fired = await countRequestsOnSave(page, async () => {
      await page.getByRole('button', { name: /^save$/i }).first().click();
    });
    expect(fired).toEqual([]);
  });

  test('Products tab: editing an existing product via its pencil icon and clicking Save fires no request', async ({ page }) => {
    await login(page);
    await openJobDetail(page, SIGNED_JOB);
    await openJobDetailTab(page, 'Products');

    const editIcon = page.getByText('Product 1', { exact: true }).first().locator('xpath=following-sibling::*[1]');
    await editIcon.click();
    await page.waitForTimeout(800);

    const brandControl = page.locator('.select__control').nth(0);
    await brandControl.click();
    await page.waitForTimeout(400);
    const options = await page.getByRole('option').allTextContents();
    await page.getByRole('option', { name: options[0], exact: true }).click();

    const fired = await countRequestsOnSave(page, async () => {
      await page.getByRole('button', { name: /^save$/i }).first().click({ force: true });
    });
    expect(fired).toEqual([]);
  });
});

test.describe('KNOWN BUG (BUG-07): no duplicate-serial-number detection', () => {
  test('two products on the same job can share an identical serial number', async ({ page }) => {
    await login(page);
    await openJobDetail(page, SIGNED_JOB);
    await openJobDetailTab(page, 'Products');

    const sharedSerial = 'SN-DUP-REGRESSION-' + Date.now();

    async function addProduct(index: number) {
      await page.getByRole('button', { name: /add another product/i }).click({ force: true });
      await page.waitForTimeout(700);
      const panel = page.getByText(/Add Product \d+/, { exact: false }).last()
        .locator('xpath=ancestor::*[.//button[normalize-space(text())="Add"]][1]');

      const eq = await controlForLabel(panel, 'Original Equipment');
      await eq.click({ force: true });
      await page.waitForTimeout(350);
      await page.getByRole('option', { name: 'No existing system (new installation)', exact: true }).click();
      await page.waitForTimeout(400);

      const install = await controlForLabel(panel, 'Replacement or new installation');
      await install.click({ force: true });
      await page.waitForTimeout(350);
      const installOpts = await page.getByRole('option').allTextContents();
      await page.getByRole('option', { name: installOpts[0], exact: true }).click();
      await page.waitForTimeout(400);

      const brand = await controlForLabel(panel, 'New Unit - Brand');
      await brand.click({ force: true });
      await page.waitForTimeout(350);
      await page.getByRole('option', { name: 'ACTRON AIR', exact: true }).click();
      await page.waitForTimeout(400);

      const model = await controlForLabel(panel, 'New Unit - Model Number');
      await model.click({ force: true });
      await page.waitForTimeout(350);
      const modelOpts = await page.getByRole('option').allTextContents();
      await page.getByRole('option', { name: modelOpts[0], exact: true }).click();
      await page.waitForTimeout(400);

      await page.getByPlaceholder(/serial/i).last().fill(sharedSerial);
      await page.getByRole('button', { name: /^add$/i }).last().click({ force: true });
      await page.waitForTimeout(1500);
    }

    await addProduct(1);
    await addProduct(2);

    // Both products should now display the identical serial with no warning.
    await openJobDetail(page, SIGNED_JOB);
    await openJobDetailTab(page, 'Products');
    const serialFields = page.locator(`input[value="${sharedSerial}"]`);
    await expect(serialFields).toHaveCount(2);
  });
});
