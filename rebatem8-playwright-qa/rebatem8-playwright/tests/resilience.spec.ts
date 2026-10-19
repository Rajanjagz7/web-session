import {test,expect,LoginPage,LOGIN_API} from './helpers';
for(const c of [
  {id:'001',status:401,message:'Invalid credentials'},
  {id:'002',status:429,message:'Too many attempts. Please try again later.'},
  {id:'003',status:500,message:'Service temporarily unavailable'},
  {id:'004',status:503,message:'Service temporarily unavailable'},
]) test(`RES-${c.id} | Negative MOCK | HTTP ${c.status} gives feedback and permits retry`,async({page})=>{
  await page.route(LOGIN_API,r=>r.fulfill({status:c.status,json:{message:c.message},headers:c.status===429?{'Retry-After':'60'}:{}}));
  const login=new LoginPage(page);await login.open();await login.fill('qa@example.com','Synthetic-Only-123!');await login.submit.click();
  await expect(page.getByText(c.message,{exact:true}).first()).toBeVisible();
  await expect(login.submit).toBeEnabled();await expect(page).toHaveURL(/\/log-in$/);
});

test('RES-005 | Edge MOCK | Double submit sends only one pending login request',async({page})=>{
  let calls=0;let release!:()=>void;const held=new Promise<void>(resolve=>release=resolve);
  await page.route(LOGIN_API,async r=>{calls++;await held;await r.fulfill({status:401,json:{message:'Invalid credentials'}});});
  const login=new LoginPage(page);await login.open();await login.fill('qa@example.com','Synthetic-Only-123!');
  try {
    await login.submit.click();await expect.poll(()=>calls).toBe(1);
    await login.password.press('Enter');await login.password.press('Enter');
    // Bounded observation window for extra submit events while the first response is held.
    await page.waitForTimeout(250);
    expect(calls, 'Only one login request may be in flight').toBe(1);
  } finally {release();}
  await expect(login.submit).toBeEnabled();
});

test('RES-006 | Negative MOCK | Network failure restores login and displays error',async({page})=>{
  await page.route(LOGIN_API,r=>r.abort('internetdisconnected'));
  const login=new LoginPage(page);await login.open();await login.fill('qa@example.com','Synthetic-Only-123!');await login.submit.click();
  await expect(page.locator('.notification-description').filter({hasText:/network|connection|failed|error|try again/i}).first()).toBeVisible();
  await expect(login.submit).toBeEnabled();await expect(page).toHaveURL(/\/log-in$/);
});

test('RES-007 | Edge MOCK | Non-JSON gateway error does not crash login',async({page})=>{
  const crashes:string[]=[];page.on('pageerror',e=>crashes.push(e.message));
  await page.route(LOGIN_API,r=>r.fulfill({status:502,contentType:'text/html',body:'<html><body>Bad Gateway</body></html>'}));
  const login=new LoginPage(page);await login.open();await login.fill('qa@example.com','Synthetic-Only-123!');await login.submit.click();
  await expect(login.submit).toBeEnabled();await expect(page.locator('.notification-description').filter({hasText:/error|failed|gateway|try again/i}).first()).toBeVisible();expect(crashes).toEqual([]);
});
