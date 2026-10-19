import { chromium } from '@playwright/test';
const b = await chromium.launch({ headless: false });
for (const code of ['xnM3xngd','NawSQ8P2','sCYjCtj7']) {
  const p = await (await b.newContext({ viewport:{width:1280,height:900} })).newPage();
  const errs=[], reqs=[];
  p.on('console',m=>{if(m.type()==='error')errs.push(m.text().slice(0,200))});
  p.on('pageerror',e=>errs.push('PAGEERR '+e.message.slice(0,200)));
  p.on('requestfailed',r=>errs.push('REQFAIL '+r.url().slice(0,120)+' '+(r.failure()?.errorText||'')));
  p.on('response',r=>{const u=r.url(); if(!/\.(js|css|png|svg|woff2?)(\?|$)/.test(u)) reqs.push(r.status()+' '+r.request().method()+' '+u.slice(0,140));});
  await p.goto('https://booking.dev.clinic1.ai/online-booking/'+code); await p.waitForTimeout(12000);
  console.log('\n=====',code,'\nERRORS:',errs.slice(0,8),'\nREQS:',reqs.slice(0,15));
  console.log((await p.locator('body').innerText()).replace(/\n+/g,' | ').slice(0,500));
  await p.screenshot({path:`test-results/walk/portal-${code}.png`});
}
await b.close();
