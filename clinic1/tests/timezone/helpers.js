// Reference model of the spec's fix: stored time-of-day is read/written with the zone's STANDARD offset.
const fmtCache = new Map();
function offsetMinutes(zone, utcMs) {
  let f = fmtCache.get(zone);
  if (!f) {
    f = new Intl.DateTimeFormat('en-US', { timeZone: zone, hourCycle: 'h23', year: 'numeric', month: 'numeric', day: 'numeric', hour: 'numeric', minute: 'numeric', second: 'numeric' });
    fmtCache.set(zone, f);
  }
  const p = Object.fromEntries(f.formatToParts(new Date(utcMs)).map(x => [x.type, +x.value]));
  const asUtc = Date.UTC(p.year, p.month - 1, p.day, p.hour, p.minute, p.second);
  return Math.round((asUtc - Math.floor(utcMs / 1000) * 1000) / 60000);
}
// "the offset the zone spends most of its time in" over a year, sampled daily (spec section 1)
function standardOffset(zone, year = 2026) {
  const counts = new Map();
  for (let d = 0; d < 365; d++) {
    const o = offsetMinutes(zone, Date.UTC(year, 0, 1 + d, 12));
    counts.set(o, (counts.get(o) || 0) + 1);
  }
  return [...counts.entries()].sort((a, b) => b[1] - a[1])[0][0];
}
// TRUE standard (non-DST) offset = the smallest offset the zone uses in the year (what the spec's Sydney example needs)
function trueStandardOffset(zone, year = 2026) {
  let min = Infinity;
  for (let d = 0; d < 365; d += 3) min = Math.min(min, offsetMinutes(zone, Date.UTC(year, 0, 1 + d, 12)));
  return min;
}
const toMin = hhmm => { const [h, m] = hhmm.split(':').map(Number); return h * 60 + m; };
const fmt = m => { m = ((m % 1440) + 1440) % 1440; return String(Math.floor(m / 60)).padStart(2, '0') + ':' + String(m % 60).padStart(2, '0'); };
// local wall time -> stored UTC string, and back, both with the standard offset
const encode = (zone, local, year) => fmt(toMin(local) - trueStandardOffset(zone, year));
const decode = (zone, stored, year) => fmt(toMin(stored) + trueStandardOffset(zone, year));
// the OLD buggy behaviour: offset in force on the viewing date
const decodeOld = (zone, stored, utcMs) => fmt(toMin(stored) + offsetMinutes(zone, utcMs));
const allZones = () => Intl.supportedValuesOf('timeZone');
module.exports = { offsetMinutes, standardOffset, trueStandardOffset, encode, decode, decodeOld, allZones, toMin, fmt };
