"""Special timing for the NSE session - "Sellers" and "Buyers" windows from Vedic time divisions and Gann time.

Every 5-minute slot between 09:15 and 15:30 IST gets a score:

  Hora (planetary hour, 12 per day from sunrise, first = weekday lord, Chaldean order)
      Jupiter, Venus +2 · Moon, Mercury +1 · Sun 0 · Mars, Saturn -2
  Choghadiya (8 equal parts of the day, weekday-specific sequence)
      Amrit, Shubh +2 · Labh +1 · Chal 0 · Udveg -1 · Rog, Kaal -2
  Kaal periods (8 equal parts of the day)
      Rahu Kaal -2 · Yamaganda -1 · Gulika -1

Runs of slots at <= -2 become "Sellers" windows, >= +2 "Buyers" windows (20-60 min, strongest two of
each, never inside the 09:15-09:30 opening range). Gann time turns are the 45-minute steps from the
09:15 open; a turn inside or at the edge of a window is noted. A Moon nakshatra or tithi change during
the session is flagged as a likely shift in tone.

This is traditional market astrology and Gann time work, not a validated forecast: a window only matters
if price action and volume confirm it.
"""
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
OPEN, CLOSE = 9 * 60 + 15, 15 * 60 + 30

LORD = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]          # Python weekday 0=Mon
CHALDEAN = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]
HORA_PTS = {"Jupiter": 2, "Venus": 2, "Moon": 1, "Mercury": 1, "Sun": 0, "Mars": -2, "Saturn": -2}

CHOG_CYCLE = ["Udveg", "Chal", "Labh", "Amrit", "Kaal", "Shubh", "Rog"]
CHOG_START = {6: "Udveg", 0: "Amrit", 1: "Rog", 2: "Labh", 3: "Shubh", 4: "Chal", 5: "Kaal"}   # Sun..Sat
CHOG_PTS = {"Amrit": 2, "Shubh": 2, "Labh": 1, "Chal": 0, "Udveg": -1, "Rog": -2, "Kaal": -2}

# which eighth of the day (1..8) each kaal occupies, by Python weekday
RAHU = {0: 2, 1: 7, 2: 5, 3: 6, 4: 4, 5: 3, 6: 8}
YAMA = {0: 4, 1: 3, 2: 2, 3: 1, 4: 7, 5: 6, 6: 5}
GULIKA = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 7}

MOON_DEG_PER_DAY = 13.18
ELONGATION_DEG_PER_DAY = 12.19


def _hm(m):
    return f"{int(m) // 60:02d}:{int(m) % 60:02d}"


def _mins(dt):
    d = dt.astimezone(IST)
    return d.hour * 60 + d.minute + d.second / 60


def next_session(now_ist, holidays):
    """The session the timing is for: today until 15:30 on a trading day, else the next trading day."""
    d = now_ist.date()
    if not (d.weekday() < 5 and d.isoformat() not in holidays and (now_ist.hour, now_ist.minute) < (15, 30)):
        d = d + timedelta(days=1)
    while d.weekday() >= 5 or d.isoformat() in holidays:
        d = d + timedelta(days=1)
    return d


def nifty_expiry(d, holidays):
    """NIFTY weekly options expire on Tuesday; a Tuesday holiday moves expiry to the previous trading day."""
    tue = d + timedelta(days=(1 - d.weekday()) % 7)
    exp = tue
    while exp.weekday() >= 5 or exp.isoformat() in holidays:
        exp = exp - timedelta(days=1)
    return exp


def build(session_date, panchang, holidays=None):
    """panchang: vedic_panchang.compute_panchang() for 09:15 IST on session_date."""
    holidays = holidays or {}
    sr = datetime.fromisoformat(panchang["sunrise_utc"].replace("Z", "+00:00"))
    ss = datetime.fromisoformat(panchang["sunset_utc"].replace("Z", "+00:00"))
    sr_m, ss_m = _mins(sr), _mins(ss)
    day_len = ss_m - sr_m
    wd = session_date.weekday()

    hora_len, eighth = day_len / 12, day_len / 8
    first = LORD[wd]
    start_i = CHALDEAN.index(first)

    def hora_at(m):
        k = int((m - sr_m) // hora_len)
        return CHALDEAN[(start_i + k) % 7], k

    chog_start = CHOG_START[wd]
    c0 = CHOG_CYCLE.index(chog_start)

    def chog_at(m):
        k = int((m - sr_m) // eighth)
        return CHOG_CYCLE[(c0 + k) % 7]

    def kaal(seg):
        a = sr_m + eighth * (seg - 1)
        return a, a + eighth

    kaals = {"Rahu Kaal": (kaal(RAHU[wd]), -2), "Yamaganda": (kaal(YAMA[wd]), -1), "Gulika": (kaal(GULIKA[wd]), -1)}

    slots = []
    for m in range(OPEN, CLOSE, 5):
        mid = m + 2.5
        h, _ = hora_at(mid)
        c = chog_at(mid)
        pts = HORA_PTS[h] + CHOG_PTS[c]
        why = [f"{h} hora", f"{c} choghadiya"]
        for name, ((a, b), p) in kaals.items():
            if a <= mid < b:
                pts += p
                why.append(name)
        slots.append({"m": m, "score": pts, "hora": h, "chog": c, "why": why})

    def runs(pred):
        out, cur = [], None
        for s in slots:
            if s["m"] < OPEN + 15 or not pred(s["score"]):
                if cur:
                    out.append(cur)
                cur = None
                continue
            if cur is None:
                cur = {"a": s["m"], "b": s["m"] + 5, "sum": 0, "n": 0, "why": {}}
            cur["b"] = s["m"] + 5
            cur["sum"] += s["score"]
            cur["n"] += 1
            for w in s["why"]:
                cur["why"][w] = cur["why"].get(w, 0) + 1
        if cur:
            out.append(cur)
        res = []
        for r in out:
            if r["b"] - r["a"] < 20:
                continue
            if r["b"] - r["a"] > 60:   # keep the strongest 60-minute stretch inside a long run
                best, bi = None, r["a"]
                for a in range(r["a"], r["b"] - 55, 5):
                    sc = sum(s["score"] for s in slots if a <= s["m"] < a + 60)
                    if best is None or abs(sc) > abs(best):
                        best, bi = sc, a
                r = dict(r, a=bi, b=bi + 60, sum=best, n=12)
            res.append(r)
        return res

    gann = [OPEN + 45 * k for k in range(1, 9) if OPEN + 45 * k < CLOSE]

    def window(r, side):
        avg = r["sum"] / max(1, r["n"])
        top = sorted(r["why"].items(), key=lambda x: -x[1])
        def pts(w):
            if w.endswith(" hora"):
                return HORA_PTS[w[:-5]]
            if w.endswith(" choghadiya"):
                return CHOG_PTS[w[:-11]]
            return -1   # Rahu Kaal / Yamaganda / Gulika
        want = (lambda v: v < 0) if side == "Sellers" else (lambda v: v > 0)
        reasons = [w for w, n in top if n >= max(1, r["n"] // 3) and want(pts(w))][:4]
        turns = [t for t in gann if r["a"] - 10 <= t <= r["b"] + 10]
        return {"side": side, "start": _hm(r["a"]), "end": _hm(r["b"]), "start_min": r["a"], "end_min": r["b"],
                "strength": "strong" if abs(avg) >= 3 else "moderate", "score": round(avg, 1),
                "reasons": reasons, "gann_turns": [_hm(t) for t in turns]}

    sellers = sorted(runs(lambda x: x <= -2), key=lambda r: r["sum"])[:2]
    buyers = sorted(runs(lambda x: x >= 2), key=lambda r: -r["sum"])[:2]
    wins = sorted([window(r, "Sellers") for r in sellers] + [window(r, "Buyers") for r in buyers], key=lambda w: w["start_min"])

    # Moon events inside the session (computed from the 09:15 snapshot and mean motion)
    events = []
    nak_left = panchang["nakshatra_ends_fraction_remaining"] * (360 / 27)
    t_nak = OPEN + nak_left / MOON_DEG_PER_DAY * 1440
    if OPEN < t_nak < CLOSE:
        events.append({"time": _hm(t_nak), "min": round(t_nak), "what": f"Moon leaves {panchang['nakshatra']} nakshatra", "note": "Mood often shifts around a nakshatra change - re-check the trend after it"})
    tithi_left = panchang["tithi_ends_fraction_of_day_remaining"] * 12
    t_tithi = OPEN + tithi_left / ELONGATION_DEG_PER_DAY * 1440
    if OPEN < t_tithi < CLOSE:
        events.append({"time": _hm(t_tithi), "min": round(t_tithi), "what": f"{panchang['paksha']} {panchang['tithi_name']} tithi ends", "note": "Tithi change - watch for a reversal or a fresh move"})

    exp = nifty_expiry(session_date, holidays)
    is_exp = exp == session_date
    return {
        "available": True,
        "session_date": session_date.isoformat(),
        "is_expiry": is_exp,
        "next_expiry": exp.isoformat(),
        "title": ("Nifty Expiry Special Timing" if is_exp else "Nifty Special Timing"),
        "windows": wins,
        "gann_turns": [_hm(t) for t in gann],
        "moon_events": events,
        "slots": [{"m": s["m"], "score": s["score"], "hora": s["hora"], "chog": s["chog"]} for s in slots],
        "hora_sequence": [{"start": _hm(max(OPEN, sr_m + hora_len * k)), "end": _hm(min(CLOSE, sr_m + hora_len * (k + 1))),
                           "lord": CHALDEAN[(start_i + k) % 7]} for k in range(12)
                          if sr_m + hora_len * (k + 1) > OPEN and sr_m + hora_len * k < CLOSE],
        "kaals": [{"name": n, "start": _hm(a), "end": _hm(b), "in_session": b > OPEN and a < CLOSE} for n, ((a, b), _) in kaals.items()],
        "sunrise_ist": _hm(sr_m), "sunset_ist": _hm(ss_m),
        "confirm_note": "Act only if price action confirms. Watch volume with price action in the given period.",
        "method": "Hora + choghadiya + Rahu/Yamaganda/Gulika per 5-minute slot; Gann turns every 45 minutes from 09:15; Moon nakshatra/tithi changes.",
    }
