import { request } from '@playwright/test';
const O='https://sunrise-family-medical.dev.clinic1.ai', CID='6a32753a139744ccb3181d73', LOC='6ab118ed88d0bf82a08492fd', PR='6ab119b788d0bf82a0849810';
const mk=tz=>request.newContext({ baseURL:O, storageState:'playwright/.auth/tz-user.json', extraHTTPHeaders: tz?{timezone:tz}:{} });
const tue=d=>d?.days?.find(x=>x.day==='Tuesday')?.slots.map(s=>s.startTime+'-'+s.endTime).join('+');
console.log('Staff schedule template, Tuesday (clinic Sydney 13:00-17:00 local), by viewer tz and week:');
for (const tz of ['Australia/Sydney','Australia/Brisbane','Australia/Perth','Asia/Calcutta','Pacific/Auckland','America/New_York','Europe/London']) {
  const c=await mk(tz); const o=[];
  for (const [s,e] of [['2026-09-28','2026-10-04'],['2026-10-05','2026-10-11']]) {
    const r=await (await c.get(`/api/v1/schedule-override/calendar?clinicId=${CID}&locationId=${LOC}&practitionerId=${PR}&startDate=${s}&endDate=${e}`)).json();
    o.push(tue(r.response?.[0]?.schedule));
  }
  console.log(' ',tz.padEnd(20),'Sep28wk:',o[0],'  Oct5wk:',o[1]);
}
