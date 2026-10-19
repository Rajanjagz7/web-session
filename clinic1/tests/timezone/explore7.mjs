import { chromium } from '@playwright/test';
const b = await chromium.launch({ headless: false });
const c = await b.newContext({ viewport:{width:1440,height:900}, storageState:'playwright/.auth/tz-user.json' });
const p = await c.newPage();
const o='https://sunrise-family-medical.dev.clinic1.ai';
const seen=new Set();
p.on('response', r=>{const u=r.url(); if(/\/api\/v1\//.test(u)&&r.request().method()!=='OPTIONS'){const k=u.split('?')[0]; if(!seen.has(k)&&!/socket|notif|sticky|ai-pref|scribe|tenant|checkSession|overdue|clinic\/location|dashboard/.test(u)){seen.add(k);console.log('  api',r.status(),r.request().method(),u.replace(/https:\/\/[^/]+/,'').slice(0,140));}}});
await p.goto(o+'/settings'); await p.waitForTimeout(5000);
const links = await p.locator('a,button,[role=tab],[role=button]').evaluateAll(l=>[...new Set(l.map(a=>(a.innerText||'').trim().split('\n')[0]).filter(t=>t&&t.length<40))]);
console.log('SETTINGS controls:', links.join(' | '));
for (const t of ['Integrations','Booking','Online booking','Booking page','Halaxy','Splose']) {
  const el = p.getByText(t,{exact:false}).first();
  if (await el.count()) console.log('has text:',t);
}
await p.screenshot({path:'test-results/walk/settings-full.png', fullPage:true});
for (const path of ['/settings/integrations','/integrations','/settings/online-booking','/booking','/settings/booking']) {
  await p.goto(o+path); await p.waitForTimeout(3500); console.log(path,'->',p.url().replace(o,''));
}
await b.close();
