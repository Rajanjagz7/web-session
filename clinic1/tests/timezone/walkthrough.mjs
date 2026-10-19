import { chromium } from '@playwright/test';
import fs from 'fs';
const b = await chromium.launch({ headless: false });
const c = await b.newContext({ viewport:{width:1440,height:900}, storageState:'playwright/.auth/tz-user.json' });
const p = await c.newPage();
const o='https://sunrise-family-medical.dev.clinic1.ai';
let cur=''; const report={};
p.on('response', async r => { const u=r.url(); if(!/\/api\/v1\//.test(u)) return; if(r.request().method()==='OPTIONS') return;
  let t=''; try{t=await r.text();}catch{}
  const timeKeys=[...new Set((t.match(/"(startTime|endTime|timezone|startDateTime|endDateTime|appointmentTime|utcOffset|start|end|date|time)"/gi)||[]).map(s=>s.replace(/"/g,'')))];
  (report[cur] ||= []).push({m:r.request().method(), s:r.status(), url:u.replace(/https:\/\/[^/]+/,'').slice(0,200), timeKeys});});
const pages=['/dashboard','/schedule','/schedule/calendar','/schedule/settings','/appointments','/classes','/room-booking','/patients','/case','/invoices','/payments','/reports','/activity-log','/settings','/settings/locations','/cms','/data-import','/support-requests'];
for (const path of pages){
  cur=path; await p.goto(o+path).catch(()=>{}); await p.waitForTimeout(6000);
  const txt=(await p.locator('body').innerText().catch(()=>'')).replace(/\n+/g,' | ');
  report[path+'__meta']={finalUrl:p.url(), text:txt.slice(600,1400)};
  await p.screenshot({path:`test-results/walk/${path.replace(/\//g,'_')||'root'}.png`});
  console.log(path,'->',p.url().replace(o,''));
}
fs.writeFileSync('test-results/walk/report.json',JSON.stringify(report,null,1));
await b.close();
