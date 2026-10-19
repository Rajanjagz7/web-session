import { request } from '@playwright/test';
const CID = '6a32753a139744ccb3181d73', LOC = '6ab118ed88d0bf82a08492fd', PR = '6ab119b788d0bf82a0849810', CODE = 'sCYjCtj7';
const Q = `practitionerId=${PR}&clinicId=${CID}&locationId=${LOC}&slotDuration=30&appointmentTypeId=6ab1208888d0bf82a084adb2&consultationTypeId=6ab1208888d0bf82a084adb1&practitionerServiceId=6ab1208888d0bf82a084adc2`;
async function slots(tz, date) {
  const c = await request.newContext({ baseURL: 'https://dev.clinic1.ai', extraHTTPHeaders: { timezone: tz } });
  const j = await (await c.get(`/api/v1/public/${CODE}/availability/optimized?${Q}&date=${date}`)).json();
  await c.dispose();
  const all = Object.values(j.response?.[0]?.availabilityDay?.slots || {}).flat();
  return all.map(s => s.startTime + (s.booked ? '*' : '')).join(' ') || '(none)';
}
for (const tz of ['Australia/Sydney', 'Australia/Brisbane', 'Asia/Calcutta', 'Pacific/Auckland', 'America/New_York'])
  console.log(tz.padEnd(20), '2026-10-17:', await slots(tz, '2026-10-17'), ' | 2026-10-16:', (await slots(tz, '2026-10-16')).slice(0, 40));
const staff = await request.newContext({ baseURL: 'https://sunrise-family-medical.dev.clinic1.ai', storageState: 'playwright/.auth/tz-user.json', extraHTTPHeaders: { timezone: 'Australia/Sydney' } });
const j = await (await staff.get(`/api/v1/schedule-override/calendar?clinicId=${CID}&locationId=${LOC}&practitionerId=${PR}&startDate=2026-10-01&endDate=2026-10-31`)).json();
for (const o of j.response?.[0]?.overrides || []) console.log('OVERRIDE', JSON.stringify(o).slice(0, 500));
