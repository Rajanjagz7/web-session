// E2E smoke: opens every bottom-nav view against a local server (uvicorn server:app --port 8765), prints JS page errors and 5xx API calls.
// Usage: node qa/e2e_smoke.js   (5xx on Upstox-backed routes are expected when the machine cannot reach Upstox)
const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const pg=await b.newPage({viewport:{width:420,height:900}});const pe=[],bad=[];
pg.on('pageerror',e=>pe.push(e.message.slice(0,150)));pg.on('response',r=>{if(r.url().includes('/api/')&&r.status()>=500)bad.push(r.status()+' '+r.url().split('8765')[1].slice(0,80))});
await pg.goto('http://localhost:8765/');await pg.waitForTimeout(3500);
const views=await pg.evaluate(()=>[...new Set([...document.querySelectorAll('[data-view]')].map(e=>e.dataset.view))]);
for(const v of views){await pg.evaluate(v=>{const e=document.querySelector(`[data-view="${v}"]`);e&&e.click()},v);await pg.waitForTimeout(1500)}
console.log('views:',views.join(','));console.log('page errors:',pe);console.log('5xx:',[...new Set(bad)]);await b.close()})()
