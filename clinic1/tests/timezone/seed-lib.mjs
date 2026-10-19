import { request } from '@playwright/test';
export const IDS = { clinicId:'6a32753a139744ccb3181d73', locationId:'6ab118ed88d0bf82a08492fd', practitionerId:'6ab119b788d0bf82a0849810',
  practitionerServiceId:'6ab1208888d0bf82a084adc2', specializationId:'6a4359c047cfffb959b262a3', appointmentTypeId:'6ab1208888d0bf82a084adb2',
  consultationTypeId:'6ab1208888d0bf82a084adb1', appointmentSetterId:'6a32753a139744ccb3181d71' };
export const api = () => request.newContext({ baseURL:'https://sunrise-family-medical.dev.clinic1.ai', storageState:'playwright/.auth/tz-user.json', extraHTTPHeaders:{ timezone:'Australia/Sydney' } });
export const apptBody = (patientId, start, end, custom=false) => ({ ...IDS, patientId, bookingFor:'Patient', problemDescription:'', customTimeSlot:custom, isRecurring:false,
  startDateTime:start, endDateTime:end, slots:[{ customTimeSlot:custom, startDateTime:start, endDateTime:end, discount:{type:'percentage',value:0,amount:0}, surcharge:{name:'No Surcharge',type:'amount',value:0,_id:'66520a4c3f4ef5b73439e9a1',amount:0} }] });

export const CARD = '6ab4deafc5943a3e002d72b4';
export function invoiceBody(tpl, patientId, apptId, dateIso, rate=100) {
  const b = JSON.parse(JSON.stringify(tpl));
  delete b._id; delete b.invoiceNumber;
  b.patient = patientId; b.date = dateIso; b.createdAt = dateIso; b.updatedAt = dateIso;
  b.amount = rate; b.total = rate; b.unpaidAmount = rate;
  const ap = JSON.parse(JSON.stringify(b.appointments[0].appointmentPayment)); ap.paymentAmount = rate; ap.rate = rate;
  b.appointmentPayment = ap; b.appointments = [{ practitioner: b.issuedBy, appointment: apptId, appointmentPayment: ap }]; b.appointmentsPayment = { [apptId]: ap };
  return b;
}
export const paymentBody = (invoiceId, patientId, paidAtIso, amount=100) => ({ invoice: invoiceId, patient: patientId, paymentMethodsRootError:'', paymentMethods:[{ paymentMethod: CARD, amount }], paidAt: paidAtIso, paymentType:'appointment', location: IDS.locationId, clinic: IDS.clinicId, status:'Paid' });

export const sleep = ms => new Promise(r => setTimeout(r, ms));
export async function post(c, url, data, tries = 6) {
  let last;
  for (let i = 0; i < tries; i++) {
    const r = await c.post(url, { data }); const t = await r.text(); last = { s: r.status(), t };
    if (r.status() !== 502 && r.status() !== 503 && r.status() !== 504) return last;
    await sleep(3000 * (i + 1));
  }
  return last;
}
