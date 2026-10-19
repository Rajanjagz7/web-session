import { chromium } from '@playwright/test';
const b = await chromium.launch({ headless: false });
const c = await b.newContext({ viewport: { width: 1440, height: 1100 }, storageState: 'playwright/.auth/tz-user.json' });
const p = await c.newPage();
p.on('response', async r => {
  const u = r.url();
  if (/csv-mapper|platform|import/i.test(u) && /\/api\/v1\//.test(u) && r.request().method() !== 'OPTIONS')
    console.log('  api', r.status(), r.request().method(), u.replace(/https:\/\/[^/]+/, '').slice(0, 160), (await r.text().catch(() => '')).slice(0, 700));
});
const flat = t => t.split('\n').filter(Boolean).join(' | ');
await p.goto('https://sunrise-family-medical.dev.clinic1.ai/csv-mapper');
await p.waitForTimeout(5000);
await p.waitForTimeout(2000);
const combos = p.getByRole('combobox');
console.log('combos', await combos.count());
await p.keyboard.press('Escape'); await combos.nth(1).click();
await p.waitForTimeout(800);
console.log('MODULES:', await p.getByRole('option').allInnerTexts());
await p.getByRole('option').filter({ hasText: /practitioner/i }).first().click();
await p.waitForTimeout(2500);
console.log('AFTER MODULE:', flat(await p.locator('body').innerText()).slice(100, 1100));
await p.screenshot({ path: 'test-results/walk/data-import-dialog.png' });
console.log('combos now', await combos.count());
if (await combos.count() > 1) { await combos.nth(1).click(); await p.waitForTimeout(800); console.log('PLATFORMS:', await p.getByRole('option').allInnerTexts()); }
await b.close();
