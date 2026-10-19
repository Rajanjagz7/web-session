import { chromium } from '@playwright/test';
const b = await chromium.launch({ headless: false });
const c = await b.newContext({ viewport:{width:1440,height:1100}, storageState:'playwright/.auth/tz-user.json', timezoneId:'Australia/Sydney' });
const p = await c.newPage();
const flat = t => t.split('\n').filter(Boolean).join(' | ');
await p.goto('https://sunrise-family-medical.dev.clinic1.ai/schedule'); await p.waitForTimeout(5000);
await p.getByRole('combobox').first().click(); await p.getByRole('option',{name:/BRISBANE/i}).click(); await p.waitForTimeout(4000);
console.log('BUTTONS:', await p.getByRole('button').allInnerTexts().then(a=>a.filter(Boolean)));
// click an empty slot on the grid (1 PM row, practitioner column)
await p.mouse.click(800, 740); await p.waitForTimeout(2500);
const d = p.locator('[role=dialog]').first();
console.log('AFTER GRID CLICK:', flat(await d.innerText().catch(()=>'no dialog')).slice(0,1200));
await p.screenshot({path:'test-results/walk/grid-click.png'});
await b.close();
