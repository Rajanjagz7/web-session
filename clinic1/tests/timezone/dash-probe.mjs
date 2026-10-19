import { request } from '@playwright/test';
const O='https://sunrise-family-medical.dev.clinic1.ai', CID='6a32753a139744ccb3181d73';
const c = await request.newContext({ baseURL:O, storageState:'playwright/.auth/tz-user.json' });
for (const period of ['weekly','monthly','yearly']) {
  const r = await c.get(`/api/v1/clinic/dashboard?clinicId=${CID}&period=${period}`);
  console.log('\n##',period,r.status(), (await r.text()).slice(0,1800));
}
