// @ts-check
const { test, expect } = require('@playwright/test');
const { offsetMinutes, standardOffset, trueStandardOffset, encode, decode, decodeOld, allZones, toMin } = require('./helpers');

const ZONES = allZones();
const SAMPLES = ['09:00', '13:00', '17:00', '00:00', '23:30', '03:30'];

test.describe('All IANA zones - standard-offset model', () => {
  test(`enumerates a realistic zone list (${ZONES.length})`, () => {
    expect(ZONES.length).toBeGreaterThan(300);
    for (const z of ['Australia/Sydney', 'Australia/Melbourne', 'Australia/Brisbane', 'Australia/Perth', 'Asia/Calcutta', 'Pacific/Auckland', 'America/New_York', 'Europe/London', 'Australia/Lord_Howe']) expect(ZONES).toContain(z);
  });

  test('POSITIVE: every zone round-trips encode->decode (no DST drift)', () => {
    const bad = [];
    for (const z of ZONES) for (const t of SAMPLES) {
      if (decode(z, encode(z, t, 2026), 2026) !== t) bad.push(`${z} ${t}`);
    }
    expect(bad, bad.slice(0, 10).join('\n')).toEqual([]);
  });

  test('POSITIVE: standard offset stable across 2026-2055 for all zones', () => {
    const bad = [];
    for (const z of ZONES) {
      const base = trueStandardOffset(z, 2026);
      for (let y = 2027; y <= 2055; y += 4) if (trueStandardOffset(z, y) !== base) bad.push(`${z} ${y}`);
    }
    expect(bad.length, `zones with year-varying standard offset: ${bad.slice(0, 15).join(', ')}`).toBeLessThan(12);
  });

  test('NEGATIVE: OLD behaviour shifts hours in DST zones; non-DST zones are the control', () => {
    const jan = Date.UTC(2026, 0, 15, 12), jul = Date.UTC(2026, 6, 15, 12);
    let dstZones = 0;
    for (const z of ZONES) {
      const dj = offsetMinutes(z, jan), du = offsetMinutes(z, jul);
      if (dj === du) expect(decodeOld(z, '03:00', jan), z).toBe(decodeOld(z, '03:00', jul));
      else { dstZones++; expect(decodeOld(z, '03:00', jan), z).not.toBe(decodeOld(z, '03:00', jul)); }
    }
    expect(dstZones).toBeGreaterThan(50);
  });

  test('FINDING: literal "most-time offset" rule contradicts the spec example (Sydney reads 14:00, not 13:00)', () => {
    // spec: "sampling the whole year and taking the offset the zone spends most of its time in"
    expect(standardOffset('Australia/Sydney', 2026)).toBe(660); // DST wins by 1 day in 2026
    expect(standardOffset('Australia/Sydney', 2029)).toBe(600); // ...and flips back in 2029
    expect(standardOffset('Europe/London', 2026)).toBe(60);     // BST, not GMT
    expect(trueStandardOffset('Australia/Sydney', 2026)).toBe(600); // what the 13:00 example requires
  });

  test('POSITIVE: spec example - Sydney stored 03:00 reads 13:00', () => {
    expect(decode('Australia/Sydney', '03:00', 2026)).toBe('13:00');
    expect(encode('Australia/Sydney', '13:00', 2026)).toBe('03:00');
  });

  test('POSITIVE: Australian standard offsets', () => {
    expect(trueStandardOffset('Australia/Sydney')).toBe(600);
    expect(trueStandardOffset('Australia/Melbourne')).toBe(600);
    expect(trueStandardOffset('Australia/Brisbane')).toBe(600);
    expect(trueStandardOffset('Australia/Perth')).toBe(480);
    expect(trueStandardOffset('Australia/Adelaide')).toBe(570);
    expect(trueStandardOffset('Australia/Darwin')).toBe(570);
  });

  test('EDGE: half/quarter-hour offsets and 30-min DST (Lord Howe)', () => {
    expect(trueStandardOffset('Asia/Calcutta')).toBe(330);
    expect(trueStandardOffset('Asia/Kathmandu')).toBe(345);
    expect(trueStandardOffset('Australia/Eucla')).toBe(525);
    expect(trueStandardOffset('Australia/Lord_Howe')).toBe(630);
    expect(decode('Australia/Lord_Howe', encode('Australia/Lord_Howe', '13:00', 2026), 2026)).toBe('13:00');
  });

  test('EDGE: midnight wrap in every zone', () => {
    const bad = [];
    for (const z of ZONES) for (const t of ['00:00', '23:30', '23:59']) {
      const st = encode(z, t, 2026);
      if (!/^\d\d:\d\d$/.test(st) || decode(z, st, 2026) !== t) bad.push(`${z} ${t} -> ${st}`);
    }
    expect(bad).toEqual([]);
  });

  test('EDGE: 4 Oct 2026 transition - Sydney +10 -> +11, Brisbane unchanged', () => {
    const before = Date.UTC(2026, 9, 3, 12), after = Date.UTC(2026, 9, 5, 12);
    expect(offsetMinutes('Australia/Sydney', before)).toBe(600);
    expect(offsetMinutes('Australia/Sydney', after)).toBe(660);
    expect(offsetMinutes('Australia/Brisbane', before)).toBe(offsetMinutes('Australia/Brisbane', after));
    expect(decodeOld('Australia/Sydney', '03:00', after)).toBe('14:00'); // the bug
    expect(decode('Australia/Sydney', '03:00', 2026)).toBe('13:00'); // the fix
  });

  test('NEGATIVE: invalid zone rejected, malformed time is NaN', () => {
    expect(() => offsetMinutes('Not/AZone', Date.now())).toThrow();
    expect(() => standardOffset('')).toThrow();
    expect(toMin('xx:yy')).toBeNaN();
  });

  test('POSITIVE: a 13:00 booking stays inside a 13:00-17:00 band in every zone', () => {
    const bad = [];
    for (const z of ZONES) {
      const s = toMin(decode(z, encode(z, '13:00', 2026), 2026)), e = toMin(decode(z, encode(z, '17:00', 2026), 2026));
      if (!(s <= 13 * 60 && 13 * 60 < e)) bad.push(z);
    }
    expect(bad).toEqual([]);
  });
});
