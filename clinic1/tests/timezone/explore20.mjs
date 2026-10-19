import { chromium } from '@playwright/test';
const TZ = 'Australia/Sydney';
const b = await chromium.launch({ headless: false });
const c = await b.newContext({ viewport: { width: 1440, height: 1100 }, storageState: 'playwright/.auth/tz-user.json', timezoneId: TZ });
const p = await c.newPage();
p.on('request', r => {
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(r.method()) && /\/api\/v1\//.test(r.url()))
    console.log('MUT', r.method(), r.url().replace(/https:\/\/[^/]+/, ''), 'tz=' + r.headers().timezone, (r.postData() || '').slice(0, 900));
});
p.on('response', async r => {
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(r.request().method()) && /\/api\/v1\//.test(r.url()))
    console.log('  ->', r.status(), (await r.text().catch(() => '')).slice(0, 300));
});
const flat = t => t.split('\n').filter(Boolean).join(' | ');
const o = 'https://sunrise-family-medical.dev.clinic1.ai';
await p.goto(o + '/schedule/settings');
await p.waitForTimeout(5000);
await p.getByRole('combobox').first().click();
await p.getByRole('option', { name: /BRISBANE/i }).click();
await p.waitForTimeout(4000);
await p.getByRole('combobox').nth(1).click();
await p.getByRole('option', { name: /Petra/i }).click();
await p.waitForTimeout(4000);
const cell = p.locator('div').filter({ hasText: /^17/ }).filter({ has: p.locator('button') }).last();
await cell.hover();
await p.waitForTimeout(500);
console.log('cell buttons:', await cell.locator('button').count());
await cell.locator('button').first().click();
await p.waitForTimeout(2000);
await p.screenshot({ path: 'test-results/walk/override-edit.png' });
const dlg = p.locator('[role=dialog]').first();
console.log('DIALOG:', flat(await dlg.innerText().catch(() => 'none')).slice(0, 700));
console.log('BUTTONS:', await dlg.getByRole('button').allInnerTexts());
await b.close();
