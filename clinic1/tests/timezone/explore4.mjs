import { chromium } from '@playwright/test';
const b = await chromium.launch({ headless: false });
const c = await b.newContext({ viewport:{width:1440,height:900}, storageState:'playwright/.auth/tz-user.json' });
const p = await c.newPage();
const seen=new Set();
p.on('response', async r => { const u=r.url(); const k=r.request().method()+u.split('?')[0]; if(/\/api\//.test(u) && !seen.has(k)){seen.add(k); console.log(r.status(), r.request().method(), u.slice(0,170));} });
const o='https://sunrise-family-medical.dev.clinic1.ai';
await p.goto(o+'/dashboard'); await p.waitForTimeout(6000);
console.log(await p.locator('body').innerText().then(t=>t.slice(0,800)));
for (const path of ['/calendar','/schedule','/diary','/appointments']) {
  await p.goto(o+path); await p.waitForTimeout(5000);
  console.log('==',path,p.url(), (await p.locator('body').innerText()).slice(0,200).replace(/\n/g,' | '));
}
await p.screenshot({ path:'test-results/tz-cal.png' });
await b.close();
