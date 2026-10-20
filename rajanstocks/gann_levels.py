"""Gann tools for the Vedic Astro + Gann daily page.

Everything here is arithmetic on real inputs (NIFTY prices from the app's live
services and daily history, planet longitudes from vedic_panchang). Gann
techniques are traditional/heuristic, not scientifically validated - the page
presents them as levels and dates to watch, never as signals by themselves.
"""
import math
from datetime import date, timedelta

ANGLES = [(-4, "180°"), (-3, "135°"), (-2, "90°"), (-1, "45°"), (0, "0°"), (1, "45°"), (2, "90°"), (3, "135°"), (4, "180°")]
CYCLE_DAYS = [30, 45, 60, 90, 120, 144, 180, 240, 270, 360]
# Gann's seasonal (solar) dates: equinoxes, solstices and the cross-quarter points between them.
SEASONAL = [(2, 4), (3, 21), (5, 5), (6, 21), (8, 8), (9, 23), (11, 8), (12, 21)]
PLANET_SHORT = {"Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me", "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa",
                "Rahu (true node)": "Ra", "Ketu (true node)": "Ke"}


def sq9_level(base, n, step=0.25):
    """(sqrt(base) + n*step)^2 - 0.25 on the root is 45 degrees on the Square of 9 (360 deg = +2)."""
    r = math.sqrt(base) + n * step
    return r * r if r > 0 else None


def sq9_levels(base, step=0.25):
    out = []
    for n, ang in ANGLES:
        lv = sq9_level(base, n, step)
        if lv:
            out.append({"n": n, "angle": ang, "level": round(lv, 2), "side": "resistance" if n > 0 else "support" if n < 0 else "base"})
    return out


def plan_around(grid, spot):
    """Long above the first level over the price, short below the first level under it; targets are the next two levels."""
    up = [x["level"] for x in grid if x["level"] > spot]
    dn = [x["level"] for x in grid if x["level"] < spot][::-1]
    if len(up) < 3 or len(dn) < 3:
        return {"buy_above": None, "buy_targets": [None, None], "buy_stop": None, "sell_below": None, "sell_targets": [None, None], "sell_stop": None}
    return {"buy_above": up[0], "buy_targets": [up[1], up[2]], "buy_stop": dn[0],
            "sell_below": dn[0], "sell_targets": [dn[1], dn[2]], "sell_stop": up[0]}


def price_angle(price):
    """Where a price sits on the Square of 9 wheel, in degrees (Gann's standard (sqrt(P) * 180 - 225) mod 360)."""
    return (math.sqrt(price) * 180.0 - 225.0) % 360.0


def planet_lines(planets_deg, spot, harmonic=360.0):
    """Gann planetary price lines: a planet at L degrees maps to prices L + k*360. Nearest line below and above spot."""
    rows = []
    for name, deg in planets_deg.items():
        d = float(deg)
        k = math.floor((spot - d) / harmonic)
        below, above = d + k * harmonic, d + (k + 1) * harmonic
        near = below if spot - below <= above - spot else above
        rows.append({"planet": name, "short": PLANET_SHORT.get(name, name[:2]), "deg": round(d, 2),
                     "below": round(below, 2), "above": round(above, 2),
                     "nearest": round(near, 2), "dist_pct": round((near - spot) / spot * 100, 2)})
    rows.sort(key=lambda r: abs(r["dist_pct"]))
    return rows


def gann_hilo(bars, length=3):
    """Gann HiLo activator on daily bars: close above the prior SMA(high) = up, below the prior SMA(low) = down."""
    if len(bars) < length + 2:
        return None
    trend = 0
    for i in range(length, len(bars)):
        hi = sum(b["high"] for b in bars[i - length:i]) / length
        lo = sum(b["low"] for b in bars[i - length:i]) / length
        c = bars[i]["close"]
        trend = 1 if c > hi else -1 if c < lo else trend
    return trend


def time_cycles(bars, today, lookahead=14):
    """Gann time cycles counted in calendar days from the 1-year swing high and low."""
    year = [b for b in bars if b["date"] >= (today - timedelta(days=365)).isoformat()]
    if len(year) < 30:
        return None
    hi = max(year, key=lambda b: b["high"])
    lo = min(year, key=lambda b: b["low"])
    pivots = []
    upcoming = []
    for kind, b, px in (("52W high", hi, hi["high"]), ("52W low", lo, lo["low"])):
        d0 = date.fromisoformat(b["date"])
        elapsed = (today - d0).days
        pivots.append({"kind": kind, "date": b["date"], "price": round(px, 2), "days_since": elapsed})
        for n in CYCLE_DAYS:
            for mult in (1, 2):
                due = d0 + timedelta(days=n * mult)
                gap = (due - today).days
                if -1 <= gap <= lookahead:
                    upcoming.append({"date": due.isoformat(), "in_days": gap, "cycle": f"{n * mult} days from {kind}",
                                     "pivot": kind, "strength": "major" if n in (90, 180, 360) else "minor"})
    upcoming.sort(key=lambda u: u["date"])
    return {"pivots": pivots, "upcoming": upcoming[:8]}


def seasonal_dates(today, count=2):
    out = []
    for y in (today.year, today.year + 1):
        for m, d in SEASONAL:
            dt = date(y, m, d)
            if dt >= today:
                out.append({"date": dt.isoformat(), "in_days": (dt - today).days})
    return out[:count]


def build(spot, prev_close, today_open, planets_sidereal, ayanamsa, bars, today, base_kind=None):
    """Everything the Gann tab and the combined plan need. Any missing input degrades that part only."""
    out = {"available": spot is not None and spot > 0}
    if not out["available"]:
        out["reason"] = "No NIFTY price available to anchor Gann levels"
        return out
    base = prev_close or spot
    out["base"] = {"price": round(base, 2), "kind": base_kind or ("previous close" if prev_close else "last price")}
    out["levels"] = sq9_levels(base)
    # wide grid (+-24 x 45 deg) so the page can always show levels above AND below a live price that has moved far from the base
    out["grid"] = [{"n": n, "level": round(lv, 2)} for n in range(-24, 25) if (lv := sq9_level(base, n))]
    if today_open:
        out["open_levels"] = sq9_levels(today_open)
    up = [l for l in out["levels"] if l["level"] > spot]
    dn = [l for l in out["levels"] if l["level"] < spot]
    out["nearest"] = {"resistance": dict(up[0], side="resistance") if up else None, "support": dict(dn[-1], side="support") if dn else None}
    out["spot"] = round(float(spot), 2)
    out["plan"] = plan_around(out["grid"], spot)
    out["planet_lines"] = planet_lines(planets_sidereal, spot)
    sun_trop = (float(planets_sidereal.get("Sun", 0)) + float(ayanamsa)) % 360
    pa = price_angle(spot)
    diff = (pa - sun_trop + 180) % 360 - 180
    out["price_vs_sun"] = {"price_angle": round(float(pa), 1), "sun_tropical": round(float(sun_trop), 1), "diff": round(float(diff), 1),
                           "balanced": bool(abs(diff) <= 10 or abs(abs(diff) - 180) <= 10)}
    if bars:
        t = gann_hilo(bars)
        out["hilo_trend"] = {1: "up", -1: "down", 0: "neutral"}.get(t, None) if t is not None else None
        out["cycles"] = time_cycles(bars, today)
    else:
        out["hilo_trend"] = None
        out["cycles"] = None
    out["seasonal"] = seasonal_dates(today)
    return out
