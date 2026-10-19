import { chromium } from '@playwright/test';
import fs from 'fs';
const b = await chromium.launch({ headless: false });
const c = await b.newContext({ viewport:{width:1440,height:900}, storageState:'playwright/.auth/tz-user.json' });
const p = await c.newPage();
const seen=new Set(); let n=0;
p.on('response', async r => { const u=r.url(); if(!/\/api\/v1\//.test(u)) return; const k=r.request().method()+u.split('?')[0]; if(seen.has(k)) return; seen.add(k);
  console.log(r.status(), r.request().method(), u.replace(/https:\/\/[^/]+/,'').slice(0,160));
  if(/schedul|availab|slot|calendar|override|opening/i.test(u)){ fs.writeFileSync(`test-results/tz-api-${n++}.json`, JSON.stringify({url:u,body:await r.text().catch(()=>'')})); } });
const o='https://sunrise-family-medical.dev.clinic1.ai';
for (const path of ['/schedule/calendar','/schedule/settings','/settings']) {
  console.log('=====',path);
  await p.goto(o+path); await p.waitForTimeout(7000);
  console.log(p.url(), (await p.locator('main, body').first().innerText()).slice(0,500).replace(/\n/g,' | '));
  await p.screenshot({ path:`test-results/tz${path.replace(/\//g,'_')}.png` });
}
await b.close();
