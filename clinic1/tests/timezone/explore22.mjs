import { request } from '@playwright/test';
const CID = '6a32753a139744ccb3181d73', LOC = '6ab118ed88d0bf82a08492fd', PR = '6ab119b788d0bf82a0849810', CODE = 'sCYjCtj7';
const OVR = '6abedb356d7152112df0d7cb';
const Q = `practitionerId=${PR}&clinicId=${CID}&locationId=${LOC}&slotDuration=30&appointmentTypeId=6ab1208888d0bf82a084adb2&consultationTypeId=6ab1208888d0bf82a084adb1&practitionerServiceId=6ab1208888d0bf82a084adc2`;
async function slots(tz, date) {
  const c = await request.newContext({ baseURL: 'https://dev.clinic1.ai', extraHTTPHeaders: { timezone: tz } });
  const j = await (await c.get(`/api/v1/public/${CODE}/availability/optimized?${Q}&date=${date}`)).json();
  await c.dispose();
  const all = Object.values(j.response?.[0]?.availabilityDay?.slots || {}).flat();
  return all.length ? `${all[0].startTime}..${all.at(-1).startTime} (${all.length})` : '(none)';
}
console.log('AFTER EDIT  Sydney 10-17:', await slots('Australia/Sydney', '2026-10-17'), '| Calcutta:', await slots('Asia/Calcutta', '2026-10-17'));
const staff = await request.newContext({ baseURL: 'https://sunrise-family-medical.dev.clinic1.ai', storageState: 'playwright/.auth/tz-user.json', extraHTTPHeaders: { timezone: 'Australia/Sydney' } });
const del = await staff.delete(`/api/v1/schedule-override/${OVR}`);
console.log('DELETE override ->', del.status(), (await del.text()).slice(0, 300));
console.log('AFTER DELETE Sydney 10-17:', await slots('Australia/Sydney', '2026-10-17'));
