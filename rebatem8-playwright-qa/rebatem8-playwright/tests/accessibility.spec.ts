import {test,expect,LoginPage} from './helpers';
for(const size of [{width:320,height:568},{width:375,height:812},{width:768,height:1024},{width:1440,height:900}])
 test(`UI-${size.width} | Edge | Login is usable at ${size.width}x${size.height}`,async({page})=>{
  await page.setViewportSize(size);const login=new LoginPage(page);await login.open();
  for(const control of [login.email,login.password,login.submit]){
    await expect(control).toBeVisible();await control.scrollIntoViewIfNeeded();const box=await control.boundingBox();
    expect(box).not.toBeNull();expect(box!.x).toBeGreaterThanOrEqual(0);expect(box!.x+box!.width).toBeLessThanOrEqual(size.width+1);
  }
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'No horizontal document overflow').toBe(true);
 });

test('A11Y-001 | Accessibility | Email has a programmatically associated label',async({page})=>{
  await new LoginPage(page).open();await expect(page.getByLabel('Email ID',{exact:true})).toBeVisible();
});
test('A11Y-002 | Accessibility | Password has a programmatically associated label',async({page})=>{
  await new LoginPage(page).open();await expect(page.getByLabel('Password',{exact:true})).toBeVisible();
});
test('A11Y-003 | Accessibility | Reveal password has a keyboard-accessible named button',async({page})=>{
  await new LoginPage(page).open();const toggle=page.getByRole('button',{name:/show password|reveal password|toggle password/i});
  await expect(toggle).toBeVisible();await toggle.focus();await expect(toggle).toBeFocused();
});
test('A11Y-004 | Accessibility | Validation errors identify invalid fields',async({page})=>{
  const login=new LoginPage(page);await login.open();await login.submit.click();
  await expect(login.email).toHaveAttribute('aria-invalid','true');
  await expect(login.password).toHaveAttribute('aria-invalid','true');
  const ids=await login.email.getAttribute('aria-describedby');expect(ids).toBeTruthy();
  for(const id of ids!.split(/\s+/)) await expect(page.locator(`[id="${id}"]`)).toBeVisible();
});
test('A11Y-005 | Positive | Keyboard tab order reaches email, password, submit',async({page})=>{
  const login=new LoginPage(page);await login.open();await login.email.focus();await page.keyboard.press('Tab');await expect(login.password).toBeFocused();
  // Reveal control may become accessible after a fix; allow one extra stop.
  await page.keyboard.press('Tab');if(!await login.submit.evaluate(e=>document.activeElement===e))await page.keyboard.press('Tab');
  await expect(login.submit).toBeFocused();
});
