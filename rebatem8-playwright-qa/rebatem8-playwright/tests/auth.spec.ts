import {test, expect, LoginPage, LOGIN_API, credentials} from './helpers';

test('AUTH-001 | Positive | Login page renders over HTTPS', async ({page}) => {
  const login = new LoginPage(page); await login.open();
  expect(new URL(page.url()).protocol).toBe('https:');
  await expect(page).toHaveTitle('RebateM8 NSW');
  await expect(page.getByRole('heading', {name: 'Welcome Back!'})).toBeVisible();
  await expect(login.password).toHaveAttribute('type', 'password');
  await expect(login.submit).toBeEnabled();
});

const invalid = [
  {id:'002', title:'Both fields empty', email:'', password:'', error:'Please Enter Your Email ID'},
  {id:'003', title:'Email empty', email:'', password:'Synthetic-Only-123!', error:'Please Enter Your Email ID'},
  {id:'004', title:'Password empty', email:'qa@example.com', password:'', error:'Please Enter Your Password'},
  {id:'005', title:'Email whitespace only', email:'   ', password:'Synthetic-Only-123!'},
  {id:'006', title:'Email missing at sign', email:'invalid.example.com', password:'Synthetic-Only-123!'},
  {id:'007', title:'Email missing local part', email:'@example.com', password:'Synthetic-Only-123!'},
  {id:'008', title:'Email missing domain', email:'user@', password:'Synthetic-Only-123!'},
  {id:'009', title:'Email multiple at signs', email:'user@@example.com', password:'Synthetic-Only-123!'},
  {id:'010', title:'Email embedded space', email:'first last@example.com', password:'Synthetic-Only-123!'},
  {id:'011', title:'Email consecutive dots', email:'first..last@example.com', password:'Synthetic-Only-123!'},
  {id:'012', title:'Email leading dot', email:'.first@example.com', password:'Synthetic-Only-123!'},
  {id:'013', title:'Email trailing local dot', email:'first.@example.com', password:'Synthetic-Only-123!'},
  {id:'014', title:'Markup entered as email', email:'<svg onload=alert(1)>', password:'Synthetic-Only-123!'},
];
for (const c of invalid) test(`AUTH-${c.id} | Negative | ${c.title}`, async ({page}) => {
  // All submissions are intercepted: validation probes cannot lock out a real account.
  let calls = 0, dialogOpened = false;
  page.on('dialog', async d => {dialogOpened = true; await d.dismiss();});
  await page.route(LOGIN_API, async r => {calls++; await r.fulfill({status:401,json:{message:'Invalid credentials'}});});
  const login = new LoginPage(page); await login.open(); await login.fill(c.email,c.password); await login.submit.click();
  await expect.soft(page.locator('.form-explain').first()).toBeVisible();
  if(c.error) await expect(page.getByText(c.error,{exact:true})).toBeVisible();
  if(c.id === '002') await expect(page.getByText('Please Enter Your Password',{exact:true})).toBeVisible();
  expect(calls, 'Invalid form must not submit a login request').toBe(0);
  expect(dialogOpened).toBe(false); await expect(page).toHaveURL(/\/log-in$/);
});

test('AUTH-015 | Positive | Valid credentials reach Jobs using Enter', async ({page}) => {
  const c=credentials(), login=new LoginPage(page); await login.open(); await login.fill(c.email,c.password);
  await login.password.press('Enter'); await expect(page).toHaveURL(/\/jobs$/);
  await expect(page.getByRole('heading',{name:'All Jobs',exact:true})).toBeVisible();
  expect(new URL(page.url()).search).toBe('');
});

test('AUTH-016 | Negative LIVE | Incorrect password is rejected', async ({page}) => {
  const c=credentials(), login=new LoginPage(page); await login.open();
  await login.fill(c.email, 'Definitely-Wrong-Password-QA-2026!');
  const response=page.waitForResponse(r=>r.url().includes('/api/v1/auth/admin/login')&&r.request().method()==='POST');
  await login.submit.click(); expect([400,401,403]).toContain((await response).status());
  await expect(page).toHaveURL(/\/log-in$/); await expect(login.submit).toBeEnabled();
  await expect(page.locator('.notification-description').filter({hasText:/invalid|incorrect|credentials|not found|wrong/i}).first()).toBeVisible();
});

test('AUTH-017 | Negative LIVE | Nonexistent account is rejected', async ({page}) => {
  const login=new LoginPage(page); await login.open();
  await login.fill(`qa-nonexistent-${Date.now()}@example.com`, 'Synthetic-Only-123!');
  const response=page.waitForResponse(r=>r.url().includes('/api/v1/auth/admin/login')&&r.request().method()==='POST');
  await login.submit.click(); expect([400,401,403]).toContain((await response).status());
  await expect(page).toHaveURL(/\/log-in$/); await expect(login.submit).toBeEnabled();
  await expect(page.locator('.notification-description').filter({hasText:/invalid|incorrect|credentials|not found|wrong/i}).first()).toBeVisible();
});

test('AUTH-018 | Edge | Password reveal toggle preserves input and remasks', async ({page}) => {
  const login=new LoginPage(page); await login.open(); await login.password.fill('Synthetic-Only-123!');
  const toggle=page.locator('.input-suffix-end .cursor-pointer');
  await toggle.click(); await expect(login.password).toHaveAttribute('type','text');
  await expect(login.password).toHaveValue('Synthetic-Only-123!');
  await toggle.click(); await expect(login.password).toHaveAttribute('type','password');
});

test('AUTH-019 | Positive | Validation clears when inputs are corrected', async ({page}) => {
  const login=new LoginPage(page); await login.open(); await login.submit.click();
  await expect(page.getByText('Please Enter Your Email ID',{exact:true})).toBeVisible();
  await login.fill('qa@example.com','Synthetic-Only-123!'); await login.password.press('Tab');
  await expect(page.getByText('Please Enter Your Email ID',{exact:true})).toBeHidden();
  await expect(page.getByText('Please Enter Your Password',{exact:true})).toBeHidden();
});

for(const [i,email] of ['qa+tag@example.com','first.last@example.co.uk','QA@EXAMPLE.COM'].entries())
 test(`AUTH-${20+i} | Edge MOCK | Syntactically valid email ${i+1} reaches authentication`, async ({page})=>{
  let sent=''; await page.route(LOGIN_API,async r=>{sent=r.request().postDataJSON().email;await r.fulfill({status:401,json:{message:'Invalid credentials'}});});
  const login=new LoginPage(page);await login.open();await login.fill(email,'Synthetic-Only-123!');await login.submit.click();
  await expect.poll(()=>sent.toLowerCase()).toBe(email.toLowerCase()); await expect(page).toHaveURL(/\/log-in$/);
 });

test('AUTH-023 | Edge MOCK | Long and Unicode passwords are not silently truncated', async ({page})=>{
  const password='Aß🔒'.repeat(256);let sent='';
  await page.route(LOGIN_API,async r=>{sent=r.request().postDataJSON().password;await r.fulfill({status:401,json:{message:'Invalid credentials'}});});
  const login=new LoginPage(page);await login.open();await login.fill('qa@example.com',password);await login.submit.click();
  await expect.poll(()=>sent.length).toBe(password.length);expect(sent===password).toBe(true);
});

test('AUTH-024 | Edge MOCK | Password leading/trailing spaces are preserved', async ({page})=>{
  const password='  Synthetic-Only-123!  ';let preserved=false;
  await page.route(LOGIN_API,async r=>{preserved=r.request().postDataJSON().password===password;await r.fulfill({status:401,json:{message:'Invalid credentials'}});});
  const login=new LoginPage(page);await login.open();await login.fill('qa@example.com',password);await login.submit.click();
  await expect.poll(()=>preserved).toBe(true);
});
