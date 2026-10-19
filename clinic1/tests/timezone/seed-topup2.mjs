import fs from 'fs';
import { api, apptBody, invoiceBody, paymentBody, post, sleep } from './seed-lib.mjs';
const c = await api();
const tpl = JSON.parse(fs.readFileSync('test-results/invoice-post.json','utf8'));
const log = JSON.parse(fs.readFileSync('test-results/seed-log.json','utf8'));
const used = new Set(log.map(x=>x.start));
const pad = n => String(n).padStart(2,'0');
const slotTimes=[]; for (let h=8;h<=17;h++) for (const m of [0,30]) slotTimes.push(`${pad(h)}:${pad(m)}`);
const weekdays = (m,maxDay) => { const o=[]; const d=new Date(Date.UTC(2026,m-1,1)); while(d.getUTCMonth()===m-1 && d.getUTCDate()<=maxDay){const w=d.getUTCDay(); if(w>=1&&w<=5)o.push(d.toISOString().slice(0,10)); d.setUTCDate(d.getUTCDate()+1);} return o; };
const end = s=>{const [d,t]=s.split('T');let [h,m]=t.split(':').map(Number);m+=30;if(m>=60){h++;m-=60;}return `${d}T${pad(h)}:${pad(m)}`;};
const people = [...new Map(log.filter(x=>x.month<=6).map(x=>[x.patientId,{id:x.patientId,name:x.patient}])).values()];
const plan = { 7:36, 8:14, 9:38, 10:9 };
const maxDay = { 7:31, 8:31, 9:30, 10:7 };
let booked=0, paidN=0, i=0;
for (const [ms,count] of Object.entries(plan)) {
  const m=+ms, days=weekdays(m,maxDay[m]);
  for (let k=0;k<count;k++) {
    const p = people[(i*5+k)%people.length]; i++;
    let start=null;
    for (let t=0;t<400;t++) { const s=`${days[(i*3+t)%days.length]}T${slotTimes[(i*7+t*5)%slotTimes.length]}`; if(!used.has(s)){start=s;used.add(s);break;} }
    if (!start) continue;
    let r = await post(c,'/api/v1/appointment', apptBody(p.id,start,end(start),true));
    if (r.s===409) { used.add(start); k--; continue; } // slot clash, try another
    if (r.s!==200) { console.log('fail',m,start,r.s,r.t.slice(0,100)); continue; }
    const id = JSON.parse(r.t).response.appointmentIds[0]; booked++;
    log.push({month:m,patient:p.name,patientId:p.id,start,id}); fs.writeFileSync('test-results/seed-log.json',JSON.stringify(log,null,1));
    if (i % 10 <= 6) { // ~70% paid
      const iso = new Date(start+':00+11:00').toISOString();
      const ri = await post(c,'/api/v1/invoice', invoiceBody(tpl,p.id,id,iso));
      if (ri.s===201) { const inv=JSON.parse(ri.t).response.invoice._id; const rp=await post(c,'/api/v1/payment', paymentBody(inv,p.id,new Date(new Date(iso).getTime()+45*60000).toISOString())); if(rp.s===201) paidN++; else console.log('pay fail',rp.s,rp.t.slice(0,100)); }
      else console.log('inv fail',ri.s,ri.t.slice(0,100));
    }
    await sleep(200);
  }
  console.log('month',m,'done');
}
console.log({booked,paidN});
