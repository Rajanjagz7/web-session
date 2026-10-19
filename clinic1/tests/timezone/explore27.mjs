import { request } from '@playwright/test';
const CID = '6a32753a139744ccb3181d73', LOC = '6ab118ed88d0bf82a08492fd', PR = '6ab119b788d0bf82a0849810';
const staff = await request.newContext({ baseURL: 'https://sunrise-family-medical.dev.clinic1.ai', storageState: 'playwright/.auth/tz-user.json', extraHTTPHeaders: { timezone: 'Australia/Sydney' } });
for (const [s, e] of [['2020-01-01', '2020-01-31'], ['2026-09-01', '2026-09-30'], ['2026-10-01', '2026-10-31'], ['2026-11-01', '2026-11-30']]) {
  const j = await (await staff.get(`/api/v1/schedule-override/calendar?clinicId=${CID}&locationId=${LOC}&practitionerId=${PR}&startDate=${s}&endDate=${e}`)).json();
  const ov = j.response?.[0]?.overrides || [];
  console.log(s, '->', ov.length, 'overrides', ov.map(o => `${o._id} ${o.startDate.slice(0, 10)} ${o.slots.map(x => x.startTime + '-' + x.endTime).join('+')}`));
}
