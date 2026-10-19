import { request } from '@playwright/test';
const O='https://sunrise-family-medical.dev.clinic1.ai', CID='6a32753a139744ccb3181d73';
const mk=tz=>request.newContext({ baseURL:O, storageState:'playwright/.auth/tz-user.json', extraHTTPHeaders: tz?{timezone:tz}:{} });
const hrs=d=>(d?.days||[]).filter(x=>x.isActive).map(x=>x.day.slice(0,3)+' '+x.slots.map(s=>s.startTime+'-'+s.endTime).join('+')).join('; ');
const base=await mk(null);
const locs=(await (await base.get(`/api/v1/clinic/location?clinicId=${CID}&page=1&limit=50`)).json()).response.clinicLocations;
for (const l of locs) {
  const pr=(await (await base.get(`/api/v1/practitioner/web?clinicId=${CID}&locationId=${l._id}&page=1&limit=20`)).json()).response.practitioners||[];
  console.log(`\n### ${l.name} (${l.timezone})`);
  for (const tz of [null, l.timezone, 'Australia/Sydney', 'Asia/Calcutta', 'America/New_York']) {
    const c=await mk(tz);
    const loc=(await (await c.get(`/api/v1/clinic/location?clinicId=${CID}&page=1&limit=50`)).json()).response.clinicLocations.find(x=>x._id===l._id);
    let line=`  hdr=${tz||'(none)'}: clinic ${hrs(loc.scheduleDetails).split(';')[1]?.trim()}`;
    if(pr[0]){ const r=await (await c.get(`/api/v1/schedule-override/calendar?clinicId=${CID}&locationId=${l._id}&practitionerId=${pr[0].userId||pr[0]._id}&startDate=2026-10-05&endDate=2026-10-11`)).json();
      line+=` | prac0 ${hrs(r.response?.[0]?.schedule).split(';')[1]?.trim()}`; }
    console.log(line);
  }
}
