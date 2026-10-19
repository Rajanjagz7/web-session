import { chromium } from '@playwright/test';
const b = await chromium.launch({ headless: false });
const c = await b.newContext({ viewport:{width:1440,height:1300}, storageState:'playwright/.auth/tz-user.json', timezoneId:'Australia/Sydney' });
const p = await c.newPage();
await p.goto('https://sunrise-family-medical.dev.clinic1.ai/appointments/booking-list'); await p.waitForTimeout(5000);
const n = await p.getByRole('combobox').count(); console.log('combos', n);
for (let i=0;i<n;i++){ await p.getByRole('combobox').nth(i).click({force:true}).catch(()=>{}); await p.waitForTimeout(700); console.log(i, (await p.getByRole('option').allInnerTexts()).map(x=>x.split('\n')[0]).slice(0,8)); await p.keyboard.press('Escape'); await p.waitForTimeout(300); }
await b.close();
