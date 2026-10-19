import { chromium } from '@playwright/test';
const b = await chromium.launch({ headless: false });
const c = await b.newContext({ viewport: { width: 1440, height: 1000 }, storageState: 'playwright/.auth/tz-user.json' });
const p = await c.newPage();
p.on('request', r => {
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(r.method()) && /\/api\/v1\//.test(r.url()))
    console.log('MUT', r.method(), r.url().replace(/https:\/\/[^/]+/, ''), (r.postData() || '').slice(0, 500));
});
const flat = t => t.split('\n').filter(Boolean).join(' | ');
const o = 'https://sunrise-family-medical.dev.clinic1.ai';
await p.goto(o + '/schedule/settings');
await p.waitForTimeout(5000);
const combos = p.getByRole('combobox');
console.log('combos', await combos.count());
await combos.first().click();
await p.waitForTimeout(1200);
console.log('listbox:', await p.getByRole('option').allInnerTexts());
await p.getByRole('option', { name: /BRISBANE/i }).click();
await p.waitForTimeout(4000);
console.log(flat(await p.locator('body').innerText()).slice(150, 700));
await p.getByRole('button', { name: /Add Override/i }).click();
await p.waitForTimeout(2500);
await p.screenshot({ path: 'test-results/walk/override-dialog.png' });
console.log('DIALOG:', flat(await p.locator('[role=dialog]').innerText().catch(() => 'no dialog')).slice(0, 900));
await b.close();
