import fs from 'fs';
import { api, invoiceBody, paymentBody, post, sleep } from './seed-lib.mjs';
const c = await api();
const tpl = JSON.parse(fs.readFileSync('test-results/invoice-post.json','utf8'));
const log = JSON.parse(fs.readFileSync('test-results/seed-log.json','utf8'));
const PLOG = 'test-results/seed-pay-log.json';
const paid = fs.existsSync(PLOG) ? JSON.parse(fs.readFileSync(PLOG,'utf8')) : [{ id:'6ac7278b878e2487273d0c22' }];
const done = new Set(paid.map(x=>x.id));
let n=0, bad=0;
for (const a of log) {
  if (a.month > 8 || done.has(a.id)) continue;
  n++; if (n % 10 > 6 && n % 10 !== 0) continue; // ~70% of appointments get paid
  const iso = new Date(a.start+':00+11:00').toISOString();
  const ri = await post(c,'/api/v1/invoice', invoiceBody(tpl,a.patientId,a.id,iso));
  if (ri.s!==201) { bad++; console.log('inv fail',a.month,a.patient,ri.s,ri.t.slice(0,120)); continue; }
  const invId = JSON.parse(ri.t).response.invoice._id;
  const paidAt = new Date(new Date(iso).getTime()+45*60000).toISOString();
  const rp = await post(c,'/api/v1/payment', paymentBody(invId,a.patientId,paidAt));
  if (rp.s!==201) { bad++; console.log('pay fail',a.month,a.patient,rp.s,rp.t.slice(0,120)); continue; }
  paid.push({ id:a.id, month:a.month, invoice:invId }); fs.writeFileSync(PLOG, JSON.stringify(paid,null,1));
  await sleep(200);
}
console.log('paid total', paid.length, 'failures', bad);
