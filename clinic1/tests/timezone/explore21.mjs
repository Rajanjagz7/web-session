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
await p.waitForTimeout(2000);
if (!(await p.locator('text=Petra Hughes').count())) {
  await p.getByRole('combobox').nth(1).click();
  await p.getByRole('option', { name: /Petra/i }).click({ timeout: 10000 });
}
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
await dlg.getByRole('button', { name: /Update this date only/i }).click();
await p.waitForTimeout(1500);
const d2 = p.locator('[role=dialog]').first();
console.log('EDIT STEP1:', flat(await d2.innerText()).slice(0, 400));
console.log('INPUT VALUES BEFORE:', await d2.locator('input').evaluateAll(l => l.map(i => i.name + '=' + i.value)));
async function pick(idx, hh, mm, ap) {
  await d2.locator('input').nth(idx).click({ force: true });
  await p.waitForTimeout(600);
  const pop = p.locator('.MuiPickersPopper-root, .MuiPopper-root').last();
  await pop.getByText(hh, { exact: true }).first().click();
  await pop.getByText(mm, { exact: true }).first().click();
  await pop.getByText(ap, { exact: true }).first().click();
  await pop.getByRole('button', { name: 'OK' }).click();
  await p.waitForTimeout(500);
}
await pick(0, '09', '00', 'AM');
await pick(1, '12', '00', 'PM');
await p.screenshot({ path: 'test-results/walk/override-edit2.png' });
console.log('BUTTONS:', await d2.getByRole('button').allInnerTexts());
for (let i = 0; i < 3; i++) {
  const save = d2.getByRole('button', { name: /Save|Update/i }).first();
  if (await save.count()) { await save.click(); break; }
  await d2.getByRole('button', { name: /Next/i }).click();
  await p.waitForTimeout(1200);
}
await p.waitForTimeout(5000);
const m2 = flat(await p.locator('body').innerText());
console.log('AFTER:', m2.slice(m2.indexOf('| 17 |'), m2.indexOf('| 17 |') + 60));
await b.close();
