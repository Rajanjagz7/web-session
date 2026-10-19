import { chromium } from '@playwright/test';
const b = await chromium.launch({ headless: false });
const c = await b.newContext({ viewport: { width: 1440, height: 1000 }, storageState: 'playwright/.auth/tz-user.json' });
const p = await c.newPage();
p.on('request', r => {
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(r.method()) && /\/api\/v1\//.test(r.url()))
    console.log('MUT', r.method(), r.url().replace(/https:\/\/[^/]+/, ''), 'tzHeader=' + r.headers().timezone, (r.postData() || '').slice(0, 1200));
});
p.on('response', async r => {
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(r.request().method()) && /\/api\/v1\//.test(r.url()))
    console.log('  ->', r.status(), (await r.text().catch(() => '')).slice(0, 400));
});
const flat = t => t.split('\n').filter(Boolean).join(' | ');
const o = 'https://sunrise-family-medical.dev.clinic1.ai';
await p.goto(o + '/schedule/settings');
await p.waitForTimeout(5000);
await p.getByRole('combobox').first().click();
await p.getByRole('option', { name: /BRISBANE/i }).click();
await p.waitForTimeout(4000);
await p.getByRole('button', { name: /Add Override/i }).click();
await p.waitForTimeout(2000);
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
await pick(0, '09', '00', 'AM');
await pick(1, '12', '00', 'PM');
console.log('INPUTS:', await dlg.locator('input').evaluateAll(l => l.map(i => i.value)));
await dlg.getByRole('button', { name: /Next/i }).click();
await p.waitForTimeout(1500);
console.log('STEP2:', flat(await dlg.innerText()).slice(0, 600));
await p.screenshot({ path: 'test-results/walk/wizard-2.png' });
await dlg.getByRole('button', { name: /Next/i }).click();
await p.waitForTimeout(1500);
console.log('STEP3:', flat(await dlg.innerText()).slice(0, 600));
await p.screenshot({ path: 'test-results/walk/wizard-3.png' });
await dlg.getByRole('button', { name: /Save/i }).click();
await p.waitForTimeout(5000);
console.log('AFTER SAVE:', flat(await p.locator('body').innerText()).slice(150, 700));
await p.screenshot({ path: 'test-results/walk/wizard-saved.png' });
await b.close();
