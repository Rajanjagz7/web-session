import fs from 'fs';
import { api, IDS, apptBody, invoiceBody, paymentBody, post, sleep } from './seed-lib.mjs';
const c = await api();
const tpl = JSON.parse(fs.readFileSync('test-results/invoice-post.json','utf8'));
const log = JSON.parse(fs.readFileSync('test-results/seed-log.json','utf8'));
const used = new Set(log.map(x=>x.start));
const pad = n=>String(n).padStart(2,'0');
const first=['Ethan','Grace','Lucas','Mia','Noah','Chloe','Jack','Ruby','Henry','Zoe','Oscar','Ella','Leo','Amelia','Max','Harper','Finn','Layla','Archer','Nina','Jasper'];
const last=['Cavanagh','Doyle','Eastwood','Fitzgerald','Gallagher','Harrington','Ingram','Jessop','Kavanagh','Lockhart','Mcallister','Norris','Okafor','Pemberton','Quinlan','Redmond','Sutherland','Thornbury','Underwood','Vasquez','Whitlock'];
const plan = { 7:5, 8:5, 9:8, 10:3 };
const times=[]; for (let h=8;h<=17;h++) for (const m of [0,30]) times.push(`${pad(h)}:${pad(m)}`);
const end = s=>{const [d,t]=s.split('T');let [h,m]=t.split(':').map(Number);m+=30;if(m>=60){h++;m-=60;}return `${d}T${pad(h)}:${pad(m)}`;};
const days = (m,max)=>{const o=[];const d=new Date(Date.UTC(2026,m-1,1));while(d.getUTCMonth()===m-1&&d.getUTCDate()<=max){if(d.getUTCDay()%6)o.push(d.toISOString().slice(0,10));d.setUTCDate(d.getUTCDate()+1);}return o;};
let n=0, made=[];
for (const [ms,cnt] of Object.entries(plan)) { const m=+ms; const ds=days(m, m===10?7:31);
  for (let k=0;k<cnt;k++,n++) {
    const name=`${first[n]} ${last[n]}`;
    const rp = await post(c,'/api/v1/patient/add',{ name, phone:`4125551${pad(n)}`, email:`${first[n]}${last[n]}@yopmail.com`.toLowerCase(), clinicId:IDS.clinicId, role:'Patient', timezone:'Australia/Sydney', countryCode:'+61', countryFlag:'AU' });
    if (rp.s!==200) { console.log('patient fail',name,rp.s,rp.t.slice(0,100)); continue; }
    const pid = JSON.parse(rp.t).response.patient._id;
    for (let t=0;t<300;t++) {
      const s=`${ds[(n*3+t)%ds.length]}T${times[(n*7+t*5)%times.length]}`; if (used.has(s)) continue; used.add(s);
      const ra = await post(c,'/api/v1/appointment', apptBody(pid,s,end(s),true));
      if (ra.s===409) continue; if (ra.s!==200) { console.log('appt fail',ra.s,ra.t.slice(0,100)); break; }
      const id=JSON.parse(ra.t).response.appointmentIds[0]; log.push({month:m,patient:name,patientId:pid,start:s,id}); made.push(name);
      const iso=new Date(s+':00+11:00').toISOString();
      const ri=await post(c,'/api/v1/invoice',invoiceBody(tpl,pid,id,iso));
      if (ri.s===201) await post(c,'/api/v1/payment',paymentBody(JSON.parse(ri.t).response.invoice._id,pid,new Date(new Date(iso).getTime()+45*60000).toISOString()));
      break; }
    fs.writeFileSync('test-results/seed-log.json',JSON.stringify(log,null,1)); await sleep(200);
  } console.log('month',m,'done'); }
console.log('new patients seeded:', made.length);
