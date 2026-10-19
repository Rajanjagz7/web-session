import { test, expect } from '@playwright/test';
import { countPipelines, deletePipelinesByPrefix, openNewPipelineDialog, pipelinesUrl } from './helpers';

const PREFIX = 'UIQA ';
test.afterAll(async ({ request }) => deletePipelinesByPrefix(request, PREFIX));

test.describe('New pipeline dialog', () => {
  test('[negative] blank and whitespace-only name keep Create disabled', async ({ page }) => {
    const dialog = await openNewPipelineDialog(page);
    const create = dialog.getByRole('button', { name: 'Create pipeline' });
    await dialog.getByRole('textbox', { name: 'Stage 1' }).fill('Lead');
    await expect(create).toBeDisabled();
    await dialog.locator('#pipeline-name').fill('   ');
    await expect(create).toBeDisabled();
  });

  test('[negative] duplicate stage names are flagged case-insensitively', async ({ page }) => {
    const dialog = await openNewPipelineDialog(page);
    await dialog.locator('#pipeline-name').fill(`${PREFIX}dup stages`);
    await dialog.getByRole('textbox', { name: 'Stage 1' }).fill('Lead');
    await dialog.getByRole('button', { name: 'Add stage' }).click();
    await dialog.getByRole('textbox', { name: 'Stage 2' }).fill('lead');
    await expect(dialog.getByText('Another stage already has this name.').first()).toBeVisible();
    await expect(dialog.getByRole('button', { name: 'Create pipeline' })).toBeDisabled();
  });

  test('[positive] create with keyboard only (type, Tab, Enter)', async ({ page, request }) => {
    const name = `${PREFIX}keyboard ${Date.now()}`;
    const dialog = await openNewPipelineDialog(page);
    await dialog.locator('#pipeline-name').fill(name);
    await page.keyboard.press('Tab');
    await page.keyboard.type('First');
    await page.keyboard.press('Enter');
    await expect(dialog).toBeHidden();
    await expect(page.getByRole('region', { name: `Stages of ${name}` })).toBeVisible();
    expect(await countPipelines(request, name)).toBe(1);
  });

  test('[security] markup in a name is rendered as text, never executed', async ({ page }) => {
    let alerted = false;
    page.on('dialog', async (d) => { alerted = true; await d.dismiss(); });
    const name = `${PREFIX}<img src=x onerror=alert(1)> "q" & 'a'`;
    const dialog = await openNewPipelineDialog(page);
    await dialog.locator('#pipeline-name').fill(name);
    await dialog.getByRole('textbox', { name: 'Stage 1' }).fill('A');
    await dialog.getByRole('button', { name: 'Create pipeline' }).click();
    await expect(page.getByRole('region', { name: `Stages of ${name}` })).toBeVisible();
    await page.waitForTimeout(500);
    expect(alerted).toBe(false);
    expect(await page.locator('img[src="x"]').count()).toBe(0);
  });

  test('[edge] double-click on Create makes exactly one pipeline', async ({ page, request }) => {
    const name = `${PREFIX}dblclick ${Date.now()}`;
    const dialog = await openNewPipelineDialog(page);
    await dialog.locator('#pipeline-name').fill(name);
    await dialog.getByRole('textbox', { name: 'Stage 1' }).fill('S1');
    await dialog.getByRole('button', { name: 'Create pipeline' }).dblclick();
    await expect(dialog).toBeHidden();
    await page.waitForTimeout(800);
    expect(await countPipelines(request, name)).toBe(1);
  });

  test('[a11y] dialog is modal, labelled, and Escape returns focus to the trigger', async ({ page, browserName }) => {
    const dialog = await openNewPipelineDialog(page);
    await expect(dialog).toHaveAttribute('aria-modal', 'true');
    await page.keyboard.press('Escape');
    await expect(dialog).toBeHidden();
    if (browserName === 'webkit') {
      // Safari does not focus a button when it is clicked, so there is nothing to restore focus to.
      // Assert only that focus is not left inside the removed dialog.
      expect(await page.evaluate(() => !document.querySelector('[role=dialog]')?.contains(document.activeElement))).toBe(true);
    } else {
      await expect(page.getByRole('button', { name: 'New pipeline' }).first()).toBeFocused();
    }
  });

  test('[boundary] name input enforces the 120 character limit', async ({ page }) => {
    const dialog = await openNewPipelineDialog(page);
    await expect(dialog.locator('#pipeline-name')).toHaveAttribute('maxlength', '120');
  });
});

test.describe('resilience', () => {
  test('[edge] offline submit keeps the draft and shows a clear message; retry makes exactly one pipeline', async ({ page, context, request }) => {
    const name = `${PREFIX}offline ${Date.now()}`;
    const dialog = await openNewPipelineDialog(page);
    await dialog.locator('#pipeline-name').fill(name);
    await dialog.getByRole('textbox', { name: 'Stage 1' }).fill('S1');
    await context.setOffline(true);
    await dialog.getByRole('button', { name: 'Create pipeline' }).click();
    await expect(dialog.getByText('Could not reach the Platform')).toBeVisible();
    await expect(dialog.locator('#pipeline-name')).toHaveValue(name);
    await context.setOffline(false);
    await dialog.getByRole('button', { name: 'Create pipeline' }).click();
    await expect(dialog).toBeHidden();
    expect(await countPipelines(request, name)).toBe(1);
  });

  test('[edge] acting on a pipeline deleted elsewhere shows an error and the page stays usable', async ({ page, request }) => {
    const name = `${PREFIX}stale ${Date.now()}`;
    const dialog = await openNewPipelineDialog(page);
    await dialog.locator('#pipeline-name').fill(name);
    await dialog.getByRole('textbox', { name: 'Stage 1' }).fill('A');
    await dialog.getByRole('button', { name: 'Create pipeline' }).click();
    await expect(page.getByRole('region', { name: `Stages of ${name}` })).toBeVisible();
    await deletePipelinesByPrefix(request, name); // "another tab" deletes it
    await page.getByRole('textbox', { name: /new stage/i }).first().fill('Ghost');
    await page.getByRole('button', { name: 'Add stage' }).first().click();
    await expect(page.getByText('Pipeline not found').first()).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Pipelines' })).toBeVisible();
  });

  test('[security] login ?next= never redirects off-site', async ({ browser }) => {
    for (const next of ['//evil.example/x', 'https://evil.example/x', '/\\evil.example', 'javascript:alert(1)']) {
      const ctx = await browser.newContext({ storageState: undefined });
      const p = await ctx.newPage();
      await p.goto(`/login?next=${encodeURIComponent(next)}`);
      await p.getByRole('textbox', { name: 'Email' }).fill(process.env.CRM_EMAIL!);
      await p.getByRole('textbox', { name: 'Password' }).fill(process.env.CRM_PASSWORD!);
      await p.getByRole('button', { name: 'Sign in' }).click();
      await p.waitForURL((u) => !u.pathname.startsWith('/login'));
      expect(new URL(p.url()).origin).toBe(new URL(process.env.CRM_BASE_URL ?? 'https://crm.staging.notbhavik.dev').origin);
      await ctx.close();
    }
  });
});

test.describe('known UI bugs (expected to fail until fixed)', () => {
  test('[known_bug] expired session on submit should send the user to sign in, not show a raw API error', async ({ page, context }) => {
    test.fail(true, 'BUG: dialog shows "A secret API key or Dashboard session is required" and stays open');
    const dialog = await openNewPipelineDialog(page);
    await dialog.locator('#pipeline-name').fill(`${PREFIX}expired`);
    await dialog.getByRole('textbox', { name: 'Stage 1' }).fill('S1');
    await context.clearCookies();
    await dialog.getByRole('button', { name: 'Create pipeline' }).click();
    await expect(page).toHaveURL(/\/login/, { timeout: 8000 });
  });

  test('[known_bug] every page should have a distinct <title>', async ({ page }) => {
    test.fail(true, 'BUG: all pages are titled "CRM Dashboard"');
    const titles = new Set<string>();
    for (const p of [pipelinesUrl, pipelinesUrl.replace('/pipelines', '/contacts'), pipelinesUrl.replace('/pipelines', '/deals')]) {
      await page.goto(p);
      await expect(page.locator('h1').first()).toBeVisible();
      titles.add(await page.title());
    }
    expect(titles.size).toBe(3);
  });
});
