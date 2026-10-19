import {authTest as test,expect} from './helpers';
import modules from './data/modules.json';

for(const [index,module] of modules.entries()) {
  if(module.denied) continue;
  test(`MOD-${String(index+1).padStart(3,'0')} | Positive LIVE | ${module.name} loads with healthy data requests`,async({page},testInfo)=>{
    const failures:{path:string,status:number}[]=[],crashes:string[]=[];let requests=0;
    page.on('pageerror',e=>crashes.push(e.message));
    page.on('response',r=>{const url=new URL(r.url());if(url.pathname.startsWith('/api/')){requests++;if(r.status()>=400)failures.push({path:url.pathname,status:r.status()});}});
    await page.goto(module.path);await expect(page).toHaveURL(new RegExp(module.path.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+'$'));
    await expect(page.locator('main')).toBeVisible();
    if(module.heading) await expect(page.getByRole('heading',{name:module.heading,exact:true}).first()).toBeVisible();
    else await expect(page.getByRole('columnheader',{name:module.tableHeader!,exact:true}).first()).toBeVisible();
    await page.waitForLoadState('networkidle');
    await testInfo.attach('network-health.json',{body:JSON.stringify({path:module.path,failures,requests,crashes},null,2),contentType:'application/json'});
    expect(requests,'An authenticated page must verify its session/data').toBeGreaterThan(0);
    expect.soft(failures,'No failed API requests while loading this module').toEqual([]);
    expect(crashes,'No uncaught JavaScript errors').toEqual([]);
  });
}

test('MOD-LOGS | Characterization LIVE | Exception Logs currently redirects this account to access-denied',async({page})=>{
  // This records observed role behavior, not approval of the underlying permission policy.
  await page.goto('/logs');await expect(page).toHaveURL(/\/access-denied$/);
  await expect(page.getByRole('heading',{name:'Access Denied!'})).toBeVisible();
});

for(const [index,module] of modules.filter(m=>m.search&&m.searchHealthy).entries())
 test(`SEARCH-${String(index+1).padStart(3,'0')} | Edge LIVE | ${module.name} no-match search and clear`,async({page})=>{
  await page.goto(module.path);await page.waitForLoadState('networkidle');
  const search=page.getByPlaceholder(module.search!,{exact:true});await expect(search).toBeVisible();
  const marker='qa_no_match_7d9f2c_20260914';
  const response=page.waitForResponse(r=>r.request().method()==='GET'&&new URL(r.url()).pathname===module.searchEndpoint&&decodeURIComponent(r.url()).includes(marker));
  await search.fill(marker);const r=await response;expect(r.status(),'Search HTTP status must be 200').toBe(200);
  await expect(page.getByRole('heading',{name:/no data found|no .*found/i}).first()).toBeVisible();
  const reset=page.waitForResponse(r=>r.request().method()==='GET'&&new URL(r.url()).pathname===module.searchEndpoint&&!decodeURIComponent(r.url()).includes(marker));
  await search.clear();expect((await reset).ok()).toBe(true);await expect(search).toHaveValue('');
 });
