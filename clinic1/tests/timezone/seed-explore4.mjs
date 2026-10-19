import { chromium } from '@playwright/test';
const b = await chromium.launch({ headless: false });
const c = await b.newContext({ viewport:{width:1440,height:1300}, storageState:'playwright/.auth/tz-user.json', timezoneId:'Australia/Sydney' });
const p = await c.newPage();
const flat = t => t.split('\n').filter(Boolean).join(' | ');
p.on('request', r => { if (['POST','PUT','PATCH'].includes(r.method()) && /\/api\/v1\//.test(r.url())) console.log('MUT', r.method(), r.url().replace(/https:\/\/[^/]+/,''), (r.postData()||'').slice(0,1200)); });
p.on('response', async r => { if (['POST','PUT','PATCH'].includes(r.request().method()) && /\/api\/v1\//.test(r.url())) console.log('  ->', r.status(), (await r.text().catch(()=>'')).slice(0,300)); });
await p.goto('https://sunrise-family-medical.dev.clinic1.ai/schedule'); await p.waitForTimeout(5000);
await p.getByRole('combobox').first().click(); await p.getByRole('option',{name:/BRISBANE/i}).click(); await p.waitForTimeout(4000);
await p.getByRole('button',{name:'Add Appointment',exact:true}).click(); await p.waitForTimeout(2500);
const d = p.locator('[role=dialog]').first();
const pickNth = async (idx, re) => {
  await d.getByRole('combobox').nth(idx).click(); await p.waitForTimeout(900);
  const opts = await p.getByRole('option').allInnerTexts(); console.log(`combo ${idx}:`, opts.slice(0,8).map(x=>x.split('\n')[0]));
  await (re ? p.getByRole('option',{name:re}).first() : p.getByRole('option').first()).click(); await p.waitForTimeout(1200);
};
await pickNth(0, /^Appointment$/);
await pickNth(1);  // location
await pickNth(2);  // profession
await pickNth(3);  // practitioner
console.log('NOW:', flat(await d.innerText()).slice(0,700));
await pickNth(4);  // patient
await pickNth(5);  // appointment type
console.log('NOW2:', flat(await d.innerText()).slice(0,900));
console.log('INPUTS:', await d.locator('input').evaluateAll(l=>l.map(i=>[i.name,i.placeholder,i.value].join('|'))));
await p.screenshot({path:'test-results/walk/add-appt3.png'});
await b.close();
