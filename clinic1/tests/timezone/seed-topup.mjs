import fs from 'fs';
import { api, apptBody, IDS } from './seed-lib.mjs';
const c = await api();
const log = JSON.parse(fs.readFileSync('test-results/seed-log.json','utf8'));
const used = new Set(log.map(x=>x.start));
const sleep = ms => new Promise(r=>setTimeout(r,ms));
const pad = n => String(n).padStart(2,'0');
async function post(url, data, tries=5) { for (let i=0;i<tries;i++) { const r = await c.post(url,{data}); const t = await r.text(); if (r.status()!==502 && r.status()!==503) return {s:r.status(),t}; await sleep(2500*(i+1)); } return {s:502,t:'gave up'}; }
// 1) patients
const names = [['Marcus','Holloway','6ac729380e70d589fd1619cc'],['Priya','Nandakumar'],['Oliver','Brennan'],['Hannah','Whitfield'],['Declan','Murphy'],
              ['Sophie','Lancaster'],['Tariq','Rahman'],['Isabella','Moretti'],['Callum','Fraser']];
const pts = [];
for (const [f,l,id] of names) {
  if (id) { pts.push({id,name:`${f} ${l}`}); continue; }
  const r = await post('/api/v1/patient/add',{ name:`${f} ${l}`, phone:`4125550${pad(10+pts.length)}`, email:`${f}${l}@yopmail.com`.toLowerCase(), clinicId:IDS.clinicId, role:'Patient', timezone:'Australia/Sydney', countryCode:'+61', countryFlag:'AU' });
  if (r.s===200) pts.push({ id: JSON.parse(r.t).response.patient._id, name:`${f} ${l}` }); else console.log('patient fail', f, l, r.s, r.t.slice(0,120));
  await sleep(300);
}
console.log('patients ready:', pts.length);
fs.writeFileSync('test-results/new-patients.json', JSON.stringify(pts));
const slotTimes=[]; for (let h=8;h<=17;h++) for (const m of [0,30]) slotTimes.push(`${pad(h)}:${pad(m)}`);
function weekdays(m){const o=[];const d=new Date(Date.UTC(2026,m-1,1));while(d.getUTCMonth()===m-1){const w=d.getUTCDay();if(w>=1&&w<=5)o.push(d.toISOString().slice(0,10));d.setUTCDate(d.getUTCDate()+1);}return o;}
const end = s=>{const [d,t]=s.split('T');let [h,m]=t.split(':').map(Number);m+=30;if(m>=60){h++;m-=60;}return `${d}T${pad(h)}:${pad(m)}`;};
async function book(m, patient, i) {
  const days = weekdays(m).filter(d=>m>=11||d<'2026-10-08');
  for (let k=0;k<300;k++) {
    const start = `${days[(i*3+k)%days.length]}T${slotTimes[(i*7+k*5)%slotTimes.length]}`;
    if (used.has(start)) continue; used.add(start);
    const r = await post('/api/v1/appointment', apptBody(patient.id,start,end(start),true));
    if (r.s===200) { log.push({month:m,patient:patient.name,patientId:patient.id,start,id:JSON.parse(r.t).response?.appointmentIds?.[0]}); fs.writeFileSync('test-results/seed-log.json',JSON.stringify(log,null,1)); await sleep(250); return true; }
    used.delete(start); if (r.s!==409) { console.log('fail',m,patient.name,start,r.s,r.t.slice(0,100)); return false; }
  }
  return false;
}
let ok=0;
// Nov: 5 new patients first visits (+ 2 returns each); Dec: 4 new (+ others)
const novNew = pts.slice(0,5), decNew = pts.slice(5,9);
let i=1000;
for (const p of novNew) { if (await book(11,p,i++)) ok++; }
for (const p of decNew) { if (await book(12,p,i++)) ok++; }
// returns from the new patients for Dec to reach ~30, and August top-up from patients seen earlier in the year
const early = log.filter(x=>x.month<=6).map(x=>({id:x.patientId,name:x.patient}));
const uniq = [...new Map(early.map(p=>[p.id,p])).values()];
for (let k=0;k<9;k++) if (await book(12, decNew[k%4], i++)) ok++;
for (let k=0;k<16;k++) if (await book(8, uniq[k%uniq.length], i++)) ok++;
console.log('booked', ok);
