"""Astro intraday time slices for one NSE session (09:15-15:30 IST), Mumbai.

A new slice starts whenever one of these changes:
  - Hora lord (planetary hour, 12 per day from sunrise)                  Jupiter/Venus +2, Moon/Mercury +1, Sun 0, Mars/Saturn -2
  - Choghadiya (8 equal parts of the day)                                Amrit/Shubh +2, Labh +1, Chal 0, Udveg -1, Rog/Kaal -2
  - Rahu Kaal / Yamaganda / Gulika (start and end)                       -2 / -1 / -1
  - Lagna star lord: the nakshatra lord of the rising sign (sidereal ascendant at Mumbai, Lahiri), about every 40-70 min
                                                                         Jupiter/Venus +1, Moon/Mercury +0.5, Sun 0, Mars/Saturn/Rahu/Ketu -1
Each slice is labelled from the total and from how much the parts disagree:
  strong agreement up = Positive, mild = Sideways to Positive, mirror for Negative,
  big plus AND big minus together = Volatile Positive / Volatile Negative / Sideways-Volatile.
The first minute (09:15-09:16) is always "Volatile" (opening auction spill-over).

Traditional market astrology - a timing guide, not a validated forecast. The backtest (astro_slices_backtest.py)
measures how often each label matched Nifty's move in that slice.
"""
import math
from datetime import date, datetime, timedelta, timezone

import vedic_timing as VT

IST = timezone(timedelta(hours=5, minutes=30))
MUMBAI_LAT, MUMBAI_LON = 18.96, 72.82
OPEN, CLOSE = VT.OPEN, VT.CLOSE

VIM = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]   # nakshatra lords in order
LAGNA_PTS = {"Jupiter": 1, "Venus": 1, "Moon": 0.5, "Mercury": 0.5, "Sun": 0, "Mars": -1, "Saturn": -1, "Rahu": -1, "Ketu": -1}
NAKS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
        "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula",
        "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]


def _julian_year(dt_utc):
    return 2000.0 + (dt_utc - datetime(2000, 1, 1, 12, tzinfo=timezone.utc)).total_seconds() / (365.25 * 86400)


def _gmst_deg(dt_utc):
    """Greenwich mean sidereal time (IAU 1982), degrees - plenty for a rising-sign boundary to the minute."""
    jd = 2440587.5 + dt_utc.timestamp() / 86400
    T = (jd - 2451545.0) / 36525
    g = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * T * T - T ** 3 / 38710000
    return g % 360


def ascendant_sidereal(dt_utc, lat=MUMBAI_LAT, lon=MUMBAI_LON):
    """Sidereal (Lahiri) ascendant longitude in degrees."""
    ramc = math.radians((_gmst_deg(dt_utc) + lon) % 360)
    jy = _julian_year(dt_utc)
    eps = math.radians(23.4392911 - 0.0130042 * (jy - 2000) / 100)
    phi = math.radians(lat)
    asc = math.degrees(math.atan2(math.cos(ramc), -(math.sin(ramc) * math.cos(eps) + math.tan(phi) * math.sin(eps)))) % 360
    ayan = 23.85 + (jy - 2000.0) * 50.2388 / 3600.0
    return (asc - ayan) % 360


def lagna_at(dt_utc):
    lon = ascendant_sidereal(dt_utc)
    i = int(lon // (360 / 27))
    return {"lon": lon, "nak": NAKS[i], "lord": VIM[i % 9]}


def _label(score, pos, neg):
    if pos >= 2 and neg <= -2:
        return "Volatile Positive" if score >= 1 else "Volatile Negative" if score <= -1 else "Sideways/Volatile"
    if score >= 3:
        return "Positive"
    if score >= 1:
        return "Sideways to Positive"
    if score <= -3:
        return "Negative"
    if score <= -1:
        return "Sideways to Negative"
    return "Sideways/Volatile"


TONE = {"Positive": "up", "Sideways to Positive": "up", "Volatile Positive": "up",
        "Negative": "down", "Sideways to Negative": "down", "Volatile Negative": "down",
        "Sideways/Volatile": "flat", "Volatile": "flat"}


def build(session_date, panchang):
    """panchang = vedic_panchang.compute_panchang() for 09:15 IST of session_date (sunrise/sunset come from it)."""
    sr = datetime.fromisoformat(panchang["sunrise_utc"].replace("Z", "+00:00"))
    ss = datetime.fromisoformat(panchang["sunset_utc"].replace("Z", "+00:00"))
    sr_m, ss_m = VT._mins(sr), VT._mins(ss)
    eighth, hora_len = (ss_m - sr_m) / 8, (ss_m - sr_m) / 12
    wd = session_date.weekday()
    h0 = VT.CHALDEAN.index(VT.LORD[wd])
    c0 = VT.CHOG_CYCLE.index(VT.CHOG_START[wd])
    kaals = [("Rahu Kaal", VT.RAHU[wd], -2), ("Yamaganda", VT.YAMA[wd], -1), ("Gulika", VT.GULIKA[wd], -1)]
    base = datetime(session_date.year, session_date.month, session_date.day, tzinfo=IST)

    def parts(m):
        """Score parts at minute-of-day m (IST)."""
        hora = VT.CHALDEAN[(h0 + int((m - sr_m) // hora_len)) % 7]
        chog = VT.CHOG_CYCLE[(c0 + int((m - sr_m) // eighth)) % 7]
        lg = lagna_at((base + timedelta(minutes=m)).astimezone(timezone.utc))
        out = [(f"{hora} hora", VT.HORA_PTS[hora]), (f"{chog} choghadiya", VT.CHOG_PTS[chog]),
               (f"Lagna in {lg['nak']} ({lg['lord']})", LAGNA_PTS[lg["lord"]])]
        for name, seg, p in kaals:
            a = sr_m + eighth * (seg - 1)
            if a <= m < a + eighth:
                out.append((name, p))
        return out, (hora, chog, lg["lord"], tuple(n for n, _ in out[3:]))

    slices, cur = [], None
    for m in range(OPEN, CLOSE):                       # minute resolution: a new slice whenever any input changes
        ps, key = parts(m + 0.5)
        if m == OPEN:
            key = ("open",)
        if cur is None or key != cur["key"]:
            if cur:
                slices.append(cur)
            cur = {"a": m, "b": m + 1, "key": key, "parts": ps}
        else:
            cur["b"] = m + 1
    slices.append(cur)

    out = []
    for s in slices:
        if s["key"] == ("open",):
            lab, score, why = "Volatile", 0, ["Opening minute"]
        else:
            vals = [p for _, p in s["parts"]]
            score = sum(vals)
            lab = _label(score, sum(v for v in vals if v > 0), sum(v for v in vals if v < 0))
            why = [f"{n} {'+' if p > 0 else ''}{p:g}" for n, p in s["parts"]]
        out.append({"from": VT._hm(s["a"]), "to": VT._hm(s["b"]), "a": s["a"], "b": s["b"], "projection": lab,
                    "tone": TONE[lab], "score": score, "why": why})
    # merge neighbours that ended up with the same projection (fewer, cleaner rows; the reasons are kept from the first)
    merged = []
    for s in out:
        if merged and merged[-1]["projection"] == s["projection"] and s["projection"] != "Volatile":
            merged[-1]["to"], merged[-1]["b"] = s["to"], s["b"]
        else:
            merged.append(dict(s))
    return {"available": True, "date": session_date.isoformat(), "slices": merged, "count": len(merged),
            "method": "Hora + choghadiya + Rahu/Yamaganda/Gulika + Lagna (ascendant) nakshatra lord at Mumbai; a new slice at every change.",
            "note": "Astro timing guide, not a forecast. Act only when price and volume confirm."}


METHOD2_ANCHOR_DATE = date(2026, 10, 26)
METHOD2_BASE_SLICES = [
    {"from": "09:15", "to": "09:22", "a": 9 * 60 + 15, "b": 9 * 60 + 22, "projection": "Sideways/Volatile", "tone": "flat", "why": "KP Sub-Lord: Rahu in Anuradha · early session sideways transition"},
    {"from": "09:22", "to": "09:51", "a": 9 * 60 + 22, "b": 9 * 60 + 51, "projection": "Volatile Negative", "tone": "down", "why": "KP Sub-Lord: Jupiter in Anuradha · opening pressure & sharp moves"},
    {"from": "09:51", "to": "10:00", "a": 9 * 60 + 51, "b": 10 * 60 + 0, "projection": "Volatile Positive", "tone": "up", "why": "KP Sub-Lord: Mercury in Jyeshtha · sub-transition 1 (positive bias)"},
    {"from": "10:00", "to": "10:15", "a": 10 * 60 + 0, "b": 10 * 60 + 15, "projection": "Volatile Positive", "tone": "up", "why": "KP Sub-Lord: Ketu in Jyeshtha · sub-transition 2 (continuation)"},
    {"from": "10:15", "to": "10:25", "a": 10 * 60 + 15, "b": 10 * 60 + 25, "projection": "Volatile Positive", "tone": "up", "why": "KP Sub-Lord: Venus in Jyeshtha · sub-transition 3 (morning crest)"},
    {"from": "10:25", "to": "10:52", "a": 10 * 60 + 25, "b": 10 * 60 + 52, "projection": "Sideways/Volatile", "tone": "flat", "why": "KP Sub-Lord: Sun/Moon in Jyeshtha · consolidation before mid-morning"},
    {"from": "10:52", "to": "11:26", "a": 10 * 60 + 52, "b": 11 * 60 + 26, "projection": "Volatile", "tone": "flat", "why": "KP Sub-Lord: Mars/Rahu in Mula · expansion & wide-range oscillation"},
    {"from": "11:26", "to": "11:55", "a": 11 * 60 + 26, "b": 11 * 60 + 55, "projection": "Volatile", "tone": "flat", "why": "KP Sub-Lord: Jupiter/Saturn in Mula · heavy institutional churn"},
    {"from": "11:55", "to": "12:08", "a": 11 * 60 + 55, "b": 12 * 60 + 8, "projection": "Sideways to Negative", "tone": "down", "why": "KP Sub-Lord: Mercury/Venus in Purva Ashadha · softening midday drift"},
    {"from": "12:08", "to": "12:43", "a": 12 * 60 + 8, "b": 12 * 60 + 43, "projection": "Volatile", "tone": "flat", "why": "KP Sub-Lord: Sun/Moon in Purva Ashadha · European market open cross-waves"},
    {"from": "12:43", "to": "12:53", "a": 12 * 60 + 43, "b": 12 * 60 + 53, "projection": "Negative", "tone": "down", "why": "KP Sub-Lord: Mars in Uttara Ashadha · afternoon distribution wave 1"},
    {"from": "12:53", "to": "13:11", "a": 12 * 60 + 53, "b": 13 * 60 + 11, "projection": "Negative", "tone": "down", "why": "KP Sub-Lord: Rahu in Uttara Ashadha · afternoon distribution wave 2"},
    {"from": "13:11", "to": "13:23", "a": 13 * 60 + 11, "b": 13 * 60 + 23, "projection": "Negative", "tone": "down", "why": "KP Sub-Lord: Jupiter in Uttara Ashadha · afternoon distribution wave 3"},
    {"from": "13:23", "to": "13:55", "a": 13 * 60 + 23, "b": 13 * 60 + 55, "projection": "Volatile", "tone": "flat", "why": "KP Sub-Lord: Saturn in Shravana · base building & two-way swings"},
    {"from": "13:55", "to": "14:23", "a": 13 * 60 + 55, "b": 14 * 60 + 23, "projection": "Sideways to Negative", "tone": "down", "why": "KP Sub-Lord: Mercury/Ketu in Shravana · late shakeout before power hour"},
    {"from": "14:23", "to": "14:50", "a": 14 * 60 + 23, "b": 14 * 60 + 50, "projection": "Volatile Positive", "tone": "up", "why": "KP Sub-Lord: Venus in Dhanishta · initial closing rally push"},
    {"from": "14:50", "to": "15:01", "a": 14 * 60 + 50, "b": 15 * 60 + 1, "projection": "Sideways/Volatile", "tone": "flat", "why": "KP Sub-Lord: Sun in Dhanishta · square-off equilibrium"},
    {"from": "15:01", "to": "15:30", "a": 15 * 60 + 1, "b": 15 * 60 + 30, "projection": "Volatile Positive", "tone": "up", "why": "KP Sub-Lord: Moon in Dhanishta · final market on close (MOC) strength"}
]

def build_method2(session_date):
    diff_days = (session_date - METHOD2_ANCHOR_DATE).days
    if diff_days == 0:
        slices = list(METHOD2_BASE_SLICES)
    else:
        shift_mins = round(diff_days * 3.9333333)
        slices = []
        for s in METHOD2_BASE_SLICES:
            raw_a = s["a"] - shift_mins
            raw_b = s["b"] - shift_mins
            start_m = max(OPEN, min(CLOSE, raw_a))
            end_m = max(OPEN, min(CLOSE, raw_b))
            if start_m < end_m:
                slices.append({
                    "from": VT._hm(start_m),
                    "to": VT._hm(end_m),
                    "a": start_m,
                    "b": end_m,
                    "projection": s["projection"],
                    "tone": s["tone"],
                    "why": s["why"] + (f" (adjusted by {abs(shift_mins)}m sidereal shift)" if shift_mins else "")
                })
    return {
        "available": True,
        "date": session_date.isoformat(),
        "slices": slices,
        "count": len(slices),
        "method": "Method 2: KP Lagna Sub-Lord transits over Mumbai (18.975° N, 72.825° E) — 18 unmerged time slices.",
        "note": "KP Ascendant Sub-Lord timing guide. Keeps every Sub-Lord transition as its own row (unmerged)."
    }

if __name__ == "__main__":
    import sys, vedic_panchang
    d = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    p = vedic_panchang.compute_panchang(datetime(d.year, d.month, d.day, 9, 15, tzinfo=IST).astimezone(timezone.utc))
    r = build(d, p)
    for s in r["slices"]:
        print(s["from"], s["to"], f"{s['projection']:22}", s["score"], "|", ", ".join(s["why"]))
    print(r["count"], "slices")
