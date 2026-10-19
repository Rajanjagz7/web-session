import { chromium } from '@playwright/test';
const b = await chromium.launch({ headless: false });
const c = await b.newContext({ viewport: { width: 1440, height: 1100 }, storageState: 'playwright/.auth/tz-user.json' });
const p = await c.newPage();
p.on('request', r => {
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(r.method()) && /\/api\/v1\//.test(r.url()))
    console.log('MUT', r.method(), r.url().replace(/https:\/\/[^/]+/, ''), 'tz=' + r.headers().timezone, (r.postData() || '').slice(0, 900));
});
const flat = t => t.split('\n').filter(Boolean).join(' | ');
const o = 'https://sunrise-family-medical.dev.clinic1.ai';
await p.goto(o + '/schedule/settings');
await p.waitForTimeout(5000);
await p.getByRole('combobox').first().click();
await p.getByRole('option', { name: /BRISBANE/i }).click();
await p.waitForTimeout(4000);
await p.getByRole('combobox').nth(1).click();
await p.waitForTimeout(800);
console.log('practitioners:', await p.getByRole('option').allInnerTexts());
await p.getByRole('option', { name: /Petra/i }).click();
await p.waitForTimeout(4000);
await p.screenshot({ path: 'test-results/walk/petra-month.png' });
console.log(flat(await p.locator('body').innerText()).slice(180, 900));
// hover Sat 17 cell and show its controls
const cell = p.locator('div').filter({ hasText: /^17/ }).filter({ has: p.locator('button') }).last();
console.log('cell count', await cell.count());
await cell.hover().catch(() => {});
await p.waitForTimeout(800);
console.log('cell buttons', await cell.locator('button').count());
await cell.locator('button').first().click().catch(e => console.log('click fail', e.message.slice(0, 100)));
await p.waitForTimeout(2000);
await p.screenshot({ path: 'test-results/walk/petra-dayplus.png' });
console.log('DIALOG:', flat(await p.locator('[role=dialog]').first().innerText().catch(() => 'none')).slice(0, 900));
await b.close();
