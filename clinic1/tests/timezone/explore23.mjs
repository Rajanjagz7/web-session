import { request } from '@playwright/test';
const CID = '6a32753a139744ccb3181d73', LOC = '6ab118ed88d0bf82a08492fd', PR = '6ab119b788d0bf82a0849810';
for (const tz of ['Australia/Sydney', 'Asia/Calcutta']) {
  const staff = await request.newContext({ baseURL: 'https://sunrise-family-medical.dev.clinic1.ai', storageState: 'playwright/.auth/tz-user.json', extraHTTPHeaders: { timezone: tz } });
  const r = await (await staff.get(`/api/v1/appointment/scheduler?page=1&limit=100&clinicId=${CID}&locationId=${LOC}&startDate=2026-10-05&endDate=2026-10-08`)).json();
  const g = r.response.groupedByPractitioner.find(x => x.practitioner._id === PR);
  console.log('\n== viewer', tz, '| keys:', Object.keys(g).join(','));
  const walk = (o, depth = 0) => Array.isArray(o) ? o.forEach(x => walk(x, depth + 1)) : null;
  for (const k of Object.keys(g)) if (Array.isArray(g[k])) console.log(' ', k, g[k].length, JSON.stringify(g[k][0]).slice(0, 700));
  for (const a of g.appointments || []) console.log('  APPT', a.startDateTime, a.endDateTime, a.status, a.date || '', a.startTime || '', a.timezone || '');
  if (g.availability) console.log('  AVAIL', JSON.stringify(g.availability).slice(0, 600));
}
