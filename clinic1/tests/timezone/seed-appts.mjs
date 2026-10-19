// Seeds backdated/future appointments for BRISBANE HEALTH CLINIC / Petra Hughes so the yearly dashboard is filled Jan-Dec.
// Usage: node seed-appts.mjs [--dry]   Log of created ids -> test-results/seed-log.json
import fs from 'fs';
import { api, apptBody } from './seed-lib.mjs';
const DRY = process.argv.includes('--dry');
const c = await api();
const all = JSON.parse(fs.readFileSync('test-results/patients.json','utf8'));
const clean = all.filter(p => !p.n && /^[A-Z][a-z]+ [A-Z][a-z]+$/.test(p.name) && !/Probe|Wilson|Andrade|Ursula|Yolanda/.test(p.name));
console.log('clean zero-appointment patients:', clean.length);
// new patients per month (first appointment month): Jan..Jun, Nov, Dec
const newPerMonth = { 1:3, 2:4, 3:5, 4:5, 5:5, 6:2, 11:5, 12:4 };
const apptsPerMonth = { 1:12, 2:18, 3:24, 4:30, 5:36, 6:34, 8:26, 11:34, 12:30 };
const log = fs.existsSync('test-results/seed-log.json') ? JSON.parse(fs.readFileSync('test-results/seed-log.json','utf8')) : [];
const used = new Set(log.map(x => x.start));
const established = []; // patients whose first appointment is already in an earlier month
let pool = [...clean];
const pad = n => String(n).padStart(2,'0');
const slotTimes = []; for (let h=8; h<=17; h++) for (const m of [0,30]) slotTimes.push(`${pad(h)}:${pad(m)}`);
function weekdays(y, m) { const out=[]; const d=new Date(Date.UTC(y,m-1,1)); while (d.getUTCMonth()===m-1) { const w=d.getUTCDay(); if (w>=1 && w<=5) out.push(d.toISOString().slice(0,10)); d.setUTCDate(d.getUTCDate()+1); } return out; }
const nextSlot = (days, i) => { for (let k=0;k<400;k++) { const day = days[(i*3+k)%days.length], t = slotTimes[((i*7)+k*5)%slotTimes.length]; const key=`${day}T${t}`; if (!used.has(key)) { used.add(key); return key; } } return null; };
const end = s => { const [d,t]=s.split('T'); let [h,m]=t.split(':').map(Number); m+=30; if (m>=60){h++;m-=60;} return `${d}T${pad(h)}:${pad(m)}`; };
const today = '2026-10-08';
let created = 0, failed = 0;
for (const m of [1,2,3,4,5,6,8,11,12]) {
  const days = weekdays(2026, m).filter(d => m>=11 || d < today);
  const fresh = pool.splice(0, newPerMonth[m] || 0);
  established.push(...fresh);
  const people = m >= 11 ? [...established, ...all.filter(p=>p.n).slice(0,25)] : established.length ? established : [];
  const firstVisit = new Set();
  for (let i=0; i<apptsPerMonth[m]; i++) {
    // first the new patients' first visits (earliest days), then returning visits from established patients
    let patient;
    if (i < fresh.length) patient = fresh[i]; else patient = people[(i*5) % people.length];
    const start = nextSlot(days, i + m*50);
    if (!start) { console.log('no free slot', m, i); continue; }
    const body = apptBody(patient.id, start, end(start), true);
    if (DRY) { console.log(m, patient.name, start); continue; }
    const r = await c.post('/api/v1/appointment', { data: body });
    const t = await r.text();
    if (r.status()===200) { created++; log.push({ month:m, patient:patient.name, patientId:patient.id, start, id: JSON.parse(t).response?.appointmentIds?.[0] }); }
    else { failed++; used.delete(start); console.log('FAIL', m, patient.name, start, r.status(), t.slice(0,140)); }
    fs.writeFileSync('test-results/seed-log.json', JSON.stringify(log,null,1));
  }
  console.log(`month ${m}: done (new patients: ${fresh.map(f=>f.name).join(', ')})`);
}
console.log({ created, failed });
