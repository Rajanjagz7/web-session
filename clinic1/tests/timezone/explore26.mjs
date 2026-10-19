import { request } from '@playwright/test';
const CID = '6a32753a139744ccb3181d73';
const staff = await request.newContext({ baseURL: 'https://sunrise-family-medical.dev.clinic1.ai', storageState: 'playwright/.auth/tz-user.json' });
for (const body of [{ clinicId: CID }, { clinicId: CID, integrations: ['halaxy', 'splose', 'xero'] }]) {
  const r = await staff.post('/api/v1/clinic/integration-status', { data: body });
  console.log('integration-status', JSON.stringify(body), '->', r.status(), (await r.text()).slice(0, 700));
}
for (const u of ['/api/v1/halaxy/status', '/api/v1/splose/status', '/api/v1/integration', '/api/v1/halaxy', '/api/v1/splose', '/api/v1/csv-mapper/platforms']) {
  const r = await staff.get(u + `?clinicId=${CID}`);
  console.log(u, '->', r.status(), (await r.text()).slice(0, 200));
}
