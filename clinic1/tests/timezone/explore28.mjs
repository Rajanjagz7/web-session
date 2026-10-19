import { chromium } from '@playwright/test';
const flat = t => t.split('\n').filter(Boolean).join(' | ');
const o = 'https://sunrise-family-medical.dev.clinic1.ai';
const b = await chromium.launch({ headless: false });
// 1) Diary grid (Schedule > Calendar) per location, viewed as a clinic-local user
for (const [tz, loc] of [['Australia/Sydney', /BRISBANE/i], ['Australia/Sydney', /Australian Clinic/i], ['Asia/Calcutta', /Melbourne Primary/i]]) {
  const c = await b.newContext({ viewport: { width: 1440, height: 1200 }, storageState: 'playwright/.auth/tz-user.json', timezoneId: tz });
  const p = await c.newPage();
  await p.goto(o + '/schedule');
  await p.waitForTimeout(5000);
  await p.getByRole('combobox').first().click();
  await p.getByRole('option', { name: loc }).click();
  await p.waitForTimeout(6000);
  const t = flat(await p.locator('body').innerText());
  const hours = [...t.matchAll(/\b(1[0-2]|[1-9])(:\d\d)? ?(AM|PM)\b/g)].map(m => m[0]);
  console.log(`\n[${tz}] ${loc}: time labels seen ->`, [...new Set(hours)].slice(0, 30).join(', '));
  await p.screenshot({ path: `test-results/walk/grid-${String(loc).replace(/\W/g, '')}.png` });
  await c.close();
}
// 2) any Halaxy / Splose connection UI?
const c2 = await b.newContext({ viewport: { width: 1440, height: 1200 }, storageState: 'playwright/.auth/tz-user.json' });
const p2 = await c2.newPage();
for (const path of ['/settings', '/csv-mapper', '/invoices', '/dashboard']) {
  await p2.goto(o + path);
  await p2.waitForTimeout(4500);
  const t = flat(await p2.locator('body').innerText());
  console.log(path, 'halaxy:', /halaxy/i.test(t), 'splose:', /splose/i.test(t), 'integration:', /integration/i.test(t));
}
await b.close();
