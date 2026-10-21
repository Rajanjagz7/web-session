"""Day Power - a Vedic + Gann bias for each coming NSE session (Nifty), with every ingredient shown.

Vedic (Moon-based, Lahiri sidereal, Mumbai)
  1 Lunar phase      Shukla paksha (waxing) +1, Krishna (waning) -1; Purnima / Amavasya 0 and flagged volatile
  2 Day lord         Thursday Jupiter +1, Friday Venus +1, Monday Moon +0.5, Wednesday Mercury +0.5, Tuesday Mars -1
  3 Nakshatra lord   Moon's nakshatra ruled by Jupiter / Venus / Moon / Mercury +1, by Saturn / Mars / Rahu / Ketu / Sun -1
  4 Moon aspects     Moon within 8 deg of Jupiter or Venus +1 each; of Saturn, Rahu or Ketu -1 each; opposite Saturn -1
  5 Session timing   hora + choghadiya + Rahu Kaal score of every 5 minutes 09:15-15:30 (vedic_timing):
                     average > +0.5 -> +1, < -0.5 -> -1; first half vs second half decides a "mix" day
Gann (Nifty daily candles up to the day before - no look-ahead)
  6 Time cycle       calendar days from the last 90-day swing high and swing low hitting 30/45/60/90/120/144/180/270/360
                     (+/-1 day) = a turn date: against the last 5 sessions' direction, +/-1
  7 Seasonal         the Sun's tropical longitude within 1 deg of a 45-degree point (Gann's seasonal dates): same
Total S -> STRONG BULLISH (S >= 3), BULLISH (1.5 to 2.5), MILD BULLISH (1), MIX (-0.5..0.5, or the two halves disagree
with |S| <= 1), MILD BEARISH (-1), BEARISH (-1.5 to -2.5), STRONG BEARISH (<= -3). Dots = strength out of 5.

Traditional market astrology and Gann time work - not a validated forecast (see day_power_backtest.json for how it
scored on past Nifty sessions). Act only on price confirmation.
"""
from datetime import date, datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
LORD_PTS = {0: ("Moon", 0.5), 1: ("Mars", -1), 2: ("Mercury", 0.5), 3: ("Jupiter", 1), 4: ("Venus", 1)}
NAK_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
BENEFIC = {"Jupiter", "Venus", "Moon", "Mercury"}
GANN_DAYS = (30, 45, 60, 90, 120, 144, 180, 270, 360)


def _sg(v):
    """+0.4 / -0.6 / 0.0 (never "-0.0")."""
    v = 0.0 if abs(v) < 0.05 else v
    return f"{v:+.1f}" if v else "0.0"


def _sep(a, b):
    d = abs((a - b) % 360)
    return min(d, 360 - d)


def _trading_days(start, n, holidays):
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5 and d.isoformat() not in holidays:
            out.append(d)
        d += timedelta(days=1)
    return out


def score_day(d, holidays, bars=None):
    import vedic_panchang
    import vedic_timing
    t_open = datetime(d.year, d.month, d.day, 9, 15, tzinfo=IST).astimezone(timezone.utc)
    p = vedic_panchang.compute_panchang(t_open)
    pl = p["planets_sidereal_deg"]
    moon = float(p["moon_sidereal_lon"])
    parts = []

    def add(group, name, pts, why):
        parts.append({"group": group, "name": name, "pts": pts, "why": why})

    # 1 lunar phase
    tn = p["tithi_number"]
    if tn in (15, 30):
        add("Vedic", "Lunar phase", 0, f"{'Purnima' if tn == 15 else 'Amavasya'} - turning point, volatile")
    else:
        add("Vedic", "Lunar phase", 1 if p["paksha"] == "Shukla" else -1, f"{p['paksha']} paksha, {p['tithi_name']} tithi")
    # 2 day lord
    lord, pts = LORD_PTS.get(d.weekday(), ("-", 0))
    add("Vedic", "Day lord", pts, f"{p['weekday_sanskrit']} - ruled by {lord}")
    # 3 nakshatra lord
    nidx = int(moon / (360 / 27)) % 27
    nl = NAK_LORDS[nidx % 9]
    add("Vedic", "Nakshatra lord", 1 if nl in BENEFIC else -1, f"Moon in {p['nakshatra']} (lord {nl})")
    # 4 Moon aspects
    asp, notes = 0, []
    for name, key, val in (("Jupiter", "Jupiter", 1), ("Venus", "Venus", 1), ("Saturn", "Saturn", -1),
                           ("Rahu", "Rahu (true node)", -1), ("Ketu", "Ketu (true node)", -1)):
        lon = pl.get(key)
        if lon is None:
            continue
        if _sep(moon, float(lon)) <= 8:
            asp += val
            notes.append(f"Moon with {name}")
        elif name == "Saturn" and _sep(moon, float(lon)) >= 172:
            asp -= 1
            notes.append("Moon opposite Saturn")
    add("Vedic", "Moon aspects", max(-2, min(2, asp)), ", ".join(notes) or "no close Moon aspect")
    # 5 session timing (hora + choghadiya + kaal)
    first = second = None
    try:
        st = vedic_timing.build(d, p, holidays)
        sl = st["slots"]
        mid = len(sl) // 2
        avg = sum(s["score"] for s in sl) / len(sl)
        first = sum(s["score"] for s in sl[:mid]) / max(1, mid)
        second = sum(s["score"] for s in sl[mid:]) / max(1, len(sl) - mid)
        add("Vedic", "Session timing", 1 if avg > 0.5 else -1 if avg < -0.5 else 0,
            f"hora/choghadiya average {_sg(avg)} (first half {_sg(first)}, second half {_sg(second)})")
    except Exception as e:
        add("Vedic", "Session timing", 0, f"unavailable ({str(e)[:40]})")
    # 6 Gann time cycle + 7 seasonal (direction = against the last 5 sessions)
    trend = 0
    past = [b for b in (bars or []) if b["date"] < d.isoformat()]
    if len(past) >= 6:
        trend = 1 if past[-1]["close"] > past[-6]["close"] else -1
    turn_against = -trend if trend else 0
    if len(past) >= 90:
        win = past[-90:]
        hi = max(win, key=lambda b: b["high"])
        lo = min(win, key=lambda b: b["low"])
        hits = []
        for tag, b in (("high", hi), ("low", lo)):
            n = (d - date.fromisoformat(b["date"])).days
            for g in GANN_DAYS:
                if abs(n - g) <= 1:
                    hits.append(f"{n} days from the {b['date']} swing {tag} ({g}-day cycle)")
        add("Gann", "Time cycle", turn_against if hits else 0,
            ("Turn date: " + "; ".join(hits) + (f" - reversal of the {'rise' if trend > 0 else 'fall'} favoured" if trend else "")) if hits else "no Gann cycle date")
    else:
        add("Gann", "Time cycle", 0, "not enough price history")
    sun_trop = (float(p["sun_sidereal_lon"]) + float(p["ayanamsa_lahiri_deg"])) % 360
    off = min(sun_trop % 45, 45 - sun_trop % 45)
    add("Gann", "Seasonal", turn_against if off <= 1 else 0,
        f"Sun at {sun_trop:.1f} deg - a Gann seasonal point (45 deg)" if off <= 1 else f"Sun at {sun_trop:.1f} deg, {off:.1f} deg from a seasonal point")

    s = sum(x["pts"] for x in parts)
    halves_disagree = first is not None and second is not None and ((first > 0.3 and second < -0.3) or (first < -0.3 and second > 0.3))
    if abs(s) <= 0.5 or (halves_disagree and abs(s) <= 1):
        label, side = "BULLISH / BEARISH MIX", "mix"
        if halves_disagree:
            note = ("First half favours buyers, second half sellers - book profits into the afternoon." if first > second
                    else "First half favours sellers, second half buyers - look for the turn after midday.")
        else:
            note = "Both sides likely. If the first half is bullish the second tends to be bearish, and vice versa."
    elif s >= 3:
        label, side, note = "STRONG BULLISH", "bull", "Strong buying support expected - buy dips while price holds VWAP."
    elif s >= 1.5:
        label, side, note = "BULLISH", "bull", "Upside tilt - prefer longs on confirmation."
    elif s > 0.5:
        label, side, note = "MILD BULLISH", "bull", "Slight upside tilt - trade only with price confirmation."
    elif s <= -3:
        label, side, note = "STRONG BEARISH", "bear", "Heavy selling pressure expected - reduce exposure, sell rises."
    elif s <= -1.5:
        label, side, note = "BEARISH", "bear", "Profit booking expected - reduce exposure."
    else:
        label, side, note = "MILD BEARISH", "bear", "Slight downside tilt - be careful with fresh longs."
    dots = {"STRONG": 5, "MILD": 3}.get(label.split()[0], 3 if side == "mix" else 4)
    return {"date": d.isoformat(), "weekday": d.strftime("%A"), "score": round(s, 1), "label": label, "side": side, "dots": dots,
            "note": note, "parts": parts,
            "halves": {"first": round(first, 2) if first is not None else None, "second": round(second, 2) if second is not None else None}}


def build(holidays, bars=None, n=3, start=None):
    now = datetime.now(IST)
    first = start or (now.date() if (now.hour, now.minute) < (15, 30) else now.date() + timedelta(days=1))
    days = _trading_days(first, n, holidays)
    return {"available": True, "days": [score_day(d, holidays, bars) for d in days],
            "method": __doc__.split("Traditional")[0].strip(),
            "caveat": "Traditional market astrology and Gann time work - not a validated forecast. Backtest on 494 Nifty sessions "
                      "(Oct 2024-Oct 2026): the bullish/bearish calls matched Nifty's direction 49.8% of the time - no better than a coin "
                      "flip. Use it as a mood guide only and act on price confirmation."}
