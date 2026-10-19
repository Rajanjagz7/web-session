import { request } from '@playwright/test';
const o='https://sunrise-family-medical.dev.clinic1.ai';
const ctx = await request.newContext({ storageState:'playwright/.auth/tz-user.json', baseURL:o });
const cid='6a32753a139744ccb3181d73';
const J=async u=>{const r=await ctx.get(u);return r.ok()?(await r.json()).response:{__err:r.status()}};
const locs=(await J(`/api/v1/clinic/location?clinicId=${cid}&page=1&limit=50`)).clinicLocations;
const hrs=d=>d?.days?.filter(x=>x.isActive).map(x=>x.day.slice(0,3)+' '+x.slots.map(s=>s.startTime+'-'+s.endTime).join('+')).join('; ');
for(const l of locs){
  console.log(`\n### ${l.name} tz=${l.timezone} scheduleTimezone=${l.scheduleTimezone}`);
  console.log(' clinic hours:',hrs(l.scheduleDetails));
  const pr=(await J(`/api/v1/practitioner/web?clinicId=${cid}&locationId=${l._id}&page=1&limit=20`)).practitioners||[];
  for(const p of pr.slice(0,3)){
    const id=p.userId||p._id||p.id;
    const out=[];
    for(const [s,e] of [['2026-09-28','2026-09-30'],['2026-10-05','2026-10-07']]){
      const r=await J(`/api/v1/schedule-override/calendar?clinicId=${cid}&locationId=${l._id}&practitionerId=${id}&startDate=${s}&endDate=${e}`);
      out.push(Array.isArray(r)?hrs(r[0]?.schedule):JSON.stringify(r).slice(0,80));
    }
    console.log(`  ${p.firstName||''} ${p.lastName||''}:\n    Sep: ${out[0]}\n    Oct: ${out[1]}\n    ${out[0]===out[1]?'SAME':'*** DIFFERENT ***'}`);
  }
}
