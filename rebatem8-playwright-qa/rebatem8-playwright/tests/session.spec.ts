import {test,authTest,expect,LoginPage,credentials} from './helpers';
import modules from './data/modules.json';
import type {Page} from '@playwright/test';
async function expectLoginBoundary(page: Page) {
  // Observed anonymous routes use the phone-based /sign-in; direct admin login is /log-in.
  // Accept either public login boundary, but never protected content.
  await expect(page).toHaveURL(/\/(?:log-in|sign-in)(?:\?.*)?$/);
  await expect(page.locator('input[name="email"], input[name="emailMobile"]')).toBeVisible();
  await expect(page.locator('main table')).toHaveCount(0);
}
for(const [index,module] of modules.entries())
 test(`GUARD-${String(index+1).padStart(3,'0')} | Negative LIVE | Anonymous access to ${module.name} is blocked`,async({page})=>{
  await page.goto(module.path);await expectLoginBoundary(page);
 });

authTest('SESSION-001 | Positive LIVE | Authenticated Jobs survives refresh',async({page})=>{
  await page.goto('/jobs');await expect(page.getByRole('heading',{name:'All Jobs',exact:true})).toBeVisible();
  await page.reload();await expect(page).toHaveURL(/\/jobs$/);await expect(page.getByPlaceholder('Search Jobs...')).toBeVisible();
});
authTest('SESSION-002 | Positive LIVE | Authenticated login URL redirects to Jobs',async({page})=>{
  await page.goto('/log-in');await expect(page).toHaveURL(/\/jobs$/);await expect(page.getByPlaceholder('Search Jobs...')).toBeVisible();
});
authTest('SESSION-003 | Negative MOCK | Server-rejected session redirects to login',async({page})=>{
  await page.route('**/api/v1/auth/me',r=>r.fulfill({status:401,json:{message:'Unauthorized'}}));
  await page.goto('/jobs');await expectLoginBoundary(page);
});
authTest('SESSION-004 | Positive LIVE | New tab in the same context retains authentication',async({context})=>{
  const page=await context.newPage();await page.goto('/jobs');await expect(page.getByPlaceholder('Search Jobs...')).toBeVisible();await page.close();
});

test('SESSION-005 | Negative LIVE | Sign out blocks deep links and browser Back',async({page})=>{
  // Separate login/session avoids invalidating shared read-only module session.
  const login=new LoginPage(page);await login.login();await page.locator('header .dropdown-toggle').click();
  await page.getByText('Sign Out',{exact:true}).click();await expectLoginBoundary(page);
  await page.goBack();await expectLoginBoundary(page);await expect(page.getByRole('heading',{name:'All Jobs',exact:true})).toBeHidden();
  await page.goto('/jobs');await expectLoginBoundary(page);
});
