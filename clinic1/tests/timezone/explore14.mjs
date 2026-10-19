import { chromium } from '@playwright/test';
const b = await chromium.launch({ headless: false });
const c = await b.newContext({ viewport: { width: 1440, height: 1000 }, storageState: 'playwright/.auth/tz-user.json' });
const p = await c.newPage();
p.on('request', r => {
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(r.method()) && /\/api\/v1\//.test(r.url()))
    console.log('MUT', r.method(), r.url().replace(/https:\/\/[^/]+/, ''), JSON.stringify(r.headers().timezone), (r.postData() || '').slice(0, 900));
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
await p.getByRole('button', { name: /Add Override/i }).click();
await p.waitForTimeout(2000);
const dlg = p.locator('[role=dialog]');
async function setTime(label, text) {
  const f = dlg.getByRole('textbox', { name: label }).first();
  await f.click();
  await p.keyboard.type(text, { delay: 60 });
}
await setTime('Start Time', '0900AM');
await setTime('Finish Time', '1200PM');
await p.screenshot({ path: 'test-results/walk/wizard-1.png' });
await dlg.getByRole('button', { name: /Next/i }).click();
await p.waitForTimeout(1500);
console.log('STEP2:', flat(await dlg.innerText()).slice(0, 500));
await p.screenshot({ path: 'test-results/walk/wizard-2.png' });
await dlg.getByRole('button', { name: /Next/i }).click();
await p.waitForTimeout(1500);
console.log('STEP3:', flat(await dlg.innerText()).slice(0, 500));
await p.screenshot({ path: 'test-results/walk/wizard-3.png' });
console.log('BUTTONS:', await dlg.getByRole('button').allInnerTexts());
await b.close();
