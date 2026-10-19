const { offsetMinutes, standardOffset, allZones } = require('./helpers');
// For every zone/year: does "most-time offset" equal the true standard (minimum / non-DST) offset?
const rows = [];
for (const z of allZones()) {
  const offs = new Set();
  for (let d = 0; d < 365; d += 7) offs.add(offsetMinutes(z, Date.UTC(2026, 0, 1 + d, 12)));
  if (offs.size < 2) continue; // no DST in 2026
  const trueStd = Math.min(...offs);
  const perYear = {};
  let wrong = 0, years = 0;
  for (let y = 2026; y <= 2055; y++) {
    const m = standardOffset(z, y);
    years++;
    if (m !== trueStd) { wrong++; (perYear[m] ||= []).push(y); }
  }
  if (wrong) rows.push({ zone: z, trueStd, wrongYears: wrong + '/' + years, modeSeenInWrongYears: Object.keys(perYear).join(',') });
}
console.table(rows);
console.log('zones affected:', rows.length);
const syd = [];
for (let y = 2026; y <= 2035; y++) syd.push(y + ':' + standardOffset('Australia/Sydney', y));
console.log('Sydney mode by year ->', syd.join('  '));
const mel = [];
for (let y = 2026; y <= 2035; y++) mel.push(y + ':' + standardOffset('Australia/Melbourne', y));
console.log('Melbourne mode by year ->', mel.join('  '));
