import { chromium } from '@playwright/test';
const TZ = process.argv[2] || 'Australia/Sydney';
const b = await chromium.launch({ headless: false });
const c = await b.newContext({ viewport: { width: 1440, height: 1100 }, storageState: 'playwright/.auth/tz-user.json', timezoneId: TZ });
const p = await c.newPage();
p.on('request', r => {
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(r.method()) && /\/api\/v1\//.test(r.url()))
    console.log('MUT', r.method(), r.url().replace(/https:\/\/[^/]+/, ''), 'tz=' + r.headers().timezone, (r.postData() || '').slice(0, 900));
});
p.on('response', async r => {
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(r.request().method()) && /\/api\/v1\//.test(r.url()))
    console.log('  ->', r.status(), (await r.text().catch(() => '')).slice(0, 500));
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
const month = flat(await p.locator('body').innerText());
console.log('VIEW as', TZ, '->', month.slice(month.indexOf('MON'), month.indexOf('MON') + 520));
const cell = p.locator('div').filter({ hasText: /^17/ }).filter({ has: p.locator('button') }).last();
await cell.hover();
await cell.locator('button').first().click();
await p.waitForTimeout(1500);
const dlg = p.locator('[role=dialog]').first();
async function pick(idx, hh, mm, ap) {
  await dlg.locator('input').nth(idx).click({ force: true });
  await p.waitForTimeout(600);
  const pop = p.locator('.MuiPickersPopper-root, .MuiPopper-root').last();
  await pop.getByText(hh, { exact: true }).first().click();
  await pop.getByText(mm, { exact: true }).first().click();
  await pop.getByText(ap, { exact: true }).first().click();
  await pop.getByRole('button', { name: 'OK' }).click();
  await p.waitForTimeout(500);
}
await pick(0, '11', '00', 'AM');
await pick(1, '11', '30', 'AM');
await dlg.getByRole('button', { name: /Next/i }).click();
await p.waitForTimeout(1500);
console.log('STEP2 inputs:', await dlg.locator('input').evaluateAll(l => l.map(i => i.name + '=' + i.value)));
await p.screenshot({ path: 'test-results/walk/override-step2.png' });
if (process.env.SAVE) {
  await dlg.getByRole('button', { name: /Next/i }).click();
  await p.waitForTimeout(1500);
  await dlg.getByRole('button', { name: /Save/i }).click();
  await p.waitForTimeout(5000);
  const m2 = flat(await p.locator('body').innerText());
  console.log('AFTER SAVE:', m2.slice(m2.indexOf('MON'), m2.indexOf('MON') + 900));
  await p.screenshot({ path: 'test-results/walk/override-saved.png' });
}
await b.close();
