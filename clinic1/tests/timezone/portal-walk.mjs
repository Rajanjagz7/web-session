import { chromium } from '@playwright/test';
import fs from 'fs';
const b = await chromium.launch({ headless: false });
const p = await (await b.newContext({ viewport:{width:1280,height:1000} })).newPage();
let n=0;
p.on('response', async r=>{const u=r.url(); if(/dev\.clinic1\.ai\/api\//.test(u)&&r.request().method()!=='OPTIONS'){let t='';try{t=await r.text()}catch{}; console.log('  api',r.status(),r.request().method(),u.replace(/https:\/\/[^/]+/,'').slice(0,170)); if(/slot|availab|practitioner|schedule|calendar/i.test(u)) fs.writeFileSync(`test-results/walk/portal-api-${n++}.json`,JSON.stringify({url:u,body:t}));}});
const show=async(l)=>{await p.waitForTimeout(3500);console.log('\n== '+l);console.log((await p.locator('body').innerText()).replace(/\n+/g,' | ').slice(200,900));await p.screenshot({path:`test-results/walk/portal-s-${l}.png`});};
await p.goto('https://booking.dev.clinic1.ai/online-booking/xnM3xngd'); await show('1-profession');
// pick first profession card
const prof = p.getByText('Massage Therapy').first();
if (await prof.count()) await prof.click(); else await p.locator('[role=option], li, [class*=card]').first().click();
await p.getByRole('button',{name:/continue/i}).click(); await show('2-practitioner');
const names = await p.locator('body').innerText();
await p.locator('[role=radio], [class*=card], li').filter({hasText:/./}).nth(0).click({timeout:5000}).catch(()=>{});
await p.getByRole('button',{name:/continue/i}).click().catch(()=>{}); await show('3-setup');
await b.close();
