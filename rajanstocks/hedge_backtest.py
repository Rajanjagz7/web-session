"""Hedged option selling (credit spreads / iron condor) - backtest on real expired option prices (GitHub Actions).

Setup tested (index weekly options; BANKNIFTY monthly):
  * Entry at 09:30 on the session before expiry (T-1) or on expiry day (T-0).
  * Expected move EM = spot x VIX/100 x sqrt(sessions left / 252)   (spot = that day's open, VIX = previous close).
  * SELL the CE whose strike is >= spot + k x EM and BUY the CE `w` strikes further out (bear call spread);
    SELL the PE whose strike is <= spot - k x EM and BUY the PE `w` strikes further out (bull put spread).
  * Sides: "condor" = both spreads; "trend" = only the spread on the side away from the trend
    (previous close above its 20-day EMA -> put spread only, below -> call spread only).
  * Exit: on expiry day at 15:20, or earlier when the spread's value reaches `stop` x the credit received.
  * P&L per lot after ~Rs 100 charges per spread (4 orders + taxes). A trade is a win when its net P&L > 0.
Prices are the real 5-minute candles of the expired contracts (Upstox, through the site's read-only research proxy).
"""
import concurrent.futures as cf
import json
import math
import os
import statistics
import sys
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import premium_backtest as PB  # noqa: E402  (get(), cache helpers, Yahoo via CI)
import run_backtest_ci as CI  # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))
UND = {"NIFTY": {"step": 50, "since": "2024-10-01"}, "SENSEX": {"step": 100, "since": "2024-10-01"},
       "BANKNIFTY": {"step": 100, "since": "2024-12-01"}}
KS = (1.0, 1.25, 1.5, 2.0)
WS = (2, 4)
STOPS = (None, 2.0, 3.0)
ENTRY_MIN, EXIT_MIN = 9 * 60 + 30, 15 * 60 + 20
CHARGES = 100.0


def ema(vals, n):
    k, e, out = 2 / (n + 1), None, []
    for v in vals:
        e = v if e is None else v * k + e * (1 - k)
        out.append(e)
    return out


def fetch(j):
    p = PB._cpath("h5" + j["key"] + j["frm"] + j["to"])
    if os.path.exists(p):
        with open(p) as f:
            return j, {k: [tuple(b) for b in v] for k, v in json.load(f).items()}
    d = PB.get("/api/research/expired/candles", {"key": j["key"], "interval": "5minute", "frm": j["frm"], "to": j["to"]})
    out = PB.by_day(((d or {}).get("data") or {}).get("candles") or [])
    if d is not None:
        with open(p, "w") as f:
            json.dump(out, f)
    return j, out


def plan(sym):
    """Every (expiry, entry day) with the strikes each variant needs."""
    step = UND[sym]["step"]
    ex = [e for e in ((PB.get("/api/research/expired/expiries", {"symbol": sym}) or {}).get("data") or []) if e >= UND[sym]["since"]]
    daily = CI._yahoo(sym)
    vix = {b["date"]: b["close"] for b in CI._yahoo("INDIAVIX")}
    days = [b["date"] for b in daily]
    bar = {b["date"]: b for b in daily}
    e20 = dict(zip(days, ema([b["close"] for b in daily], 20)))
    out = []
    for e in ex:
        if e not in bar:
            continue
        i = days.index(e)
        for lag in (1, 0):
            if i - lag - 1 < 0:
                continue
            d, prev = days[i - lag], days[i - lag - 1]
            v = vix.get(prev) or vix.get(d)
            if not v:
                continue
            spot = bar[d]["open"]
            em = spot * v / 100 * math.sqrt((lag + 1) / 252)
            trend = 1 if bar[prev]["close"] > e20[prev] else -1
            legs = {}
            for k in KS:
                ce = math.ceil((spot + k * em) / step) * step
                pe = math.floor((spot - k * em) / step) * step
                for w in WS:
                    legs[(k, w)] = {"CE": (ce, ce + w * step), "PE": (pe, pe - w * step)}
            out.append({"sym": sym, "expiry": e, "day": d, "lag": lag, "spot": spot, "vix": v, "em": round(em, 1), "trend": trend, "legs": legs})
    return out


def leg_px(bars, minute, upto=15):
    """Price at `minute`: the first print in [minute, minute + upto]; otherwise the last close before it (thin far strikes)."""
    before = None
    for b in bars:
        if b[0] < minute:
            before = b[4]
        elif b[0] <= minute + upto:
            return b[1]
        else:
            break
    return before


def run_trade(t, k, w, side, stop, data):
    short_k, long_k = t["legs"][(k, w)][side]
    S = data.get((t["expiry"], side, short_k)) or {}
    L = data.get((t["expiry"], side, long_k)) or {}
    if t["day"] not in S or t["day"] not in L or t["expiry"] not in S or t["expiry"] not in L:
        return None
    s0, l0 = leg_px(S[t["day"]], ENTRY_MIN), leg_px(L[t["day"]], ENTRY_MIN)
    if s0 is None or l0 is None:
        return None
    credit = s0 - l0
    if credit <= 0.5:
        return None                                   # nothing worth selling at this distance
    lot = data["lot"].get((t["expiry"], side, short_k)) or 1
    exit_val, why = None, "EXPIRY"
    ls, ll = s0, l0                                  # carry the last print forward (far strikes trade thinly)
    for d in dict.fromkeys((t["day"], t["expiry"])):
        sm, lm = {b[0]: b[4] for b in S.get(d, [])}, {b[0]: b[4] for b in L.get(d, [])}
        for m in sorted(set(sm) | set(lm)):
            if d == t["day"] and m <= ENTRY_MIN:
                continue
            if m > EXIT_MIN:
                break
            ls, ll = sm.get(m, ls), lm.get(m, ll)
            val = ls - ll
            if stop and val >= stop * credit:
                exit_val, why = val, "STOP"
                break
            if d == t["expiry"]:
                exit_val = val
        if why == "STOP":
            break
    if exit_val is None:
        return None
    net = (credit - exit_val) * lot - CHARGES
    width = (w * UND[t["sym"]]["step"])
    return {"sym": t["sym"], "expiry": t["expiry"], "day": t["day"], "side": side, "short": short_k, "long": long_k,
            "credit": round(credit, 2), "exit": round(exit_val, 2), "lot": lot, "net": round(net, 0), "why": why,
            "maxLoss": round((width - credit) * lot + CHARGES, 0)}


def stats(trades):
    if not trades:
        return None
    nets = [x["net"] for x in trades]
    wins = [n for n in nets if n > 0]
    losses = [n for n in nets if n <= 0]
    gp, gl = sum(wins), -sum(losses)
    return {"n": len(nets), "winRate": round(len(wins) / len(nets) * 100, 1), "total": round(sum(nets)),
            "avgWin": round(statistics.mean(wins)) if wins else 0, "avgLoss": round(statistics.mean(losses)) if losses else 0,
            "worst": round(min(nets)), "pf": round(gp / gl, 2) if gl > 0 else None,
            "perTrade": round(sum(nets) / len(nets)), "stops": sum(1 for x in trades if x["why"] == "STOP")}


def main():
    plans = []
    for sym in UND:
        p = plan(sym)
        print(f"{sym}: {len(p)} entry days", flush=True)
        plans += p
    jobs, seen = [], set()
    for sym in UND:
        cons = {}
        for t in [x for x in plans if x["sym"] == sym]:
            if t["expiry"] not in cons:
                cons[t["expiry"]] = (PB.get("/api/research/expired/contracts", {"symbol": sym, "expiry": t["expiry"]}) or {}).get("data") or []
            by = {(c.get("instrument_type"), float(c.get("strike_price") or 0)): c for c in cons[t["expiry"]]}
            for lg in t["legs"].values():
                for side, ks in lg.items():
                    for kk in ks:
                        c = by.get((side, float(kk)))
                        key = (t["expiry"], side, kk)
                        if c and key not in seen:
                            seen.add(key)
                            frm = (date.fromisoformat(t["expiry"]) - timedelta(days=6)).isoformat()
                            jobs.append({"k": key, "key": c["instrument_key"], "lot": int(c.get("lot_size") or 1), "frm": frm, "to": t["expiry"]})
    print(f"{len(jobs)} contracts to fetch", flush=True)
    data = {"lot": {}}
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        for n, (j, days) in enumerate(ex.map(fetch, jobs), 1):
            data[j["k"]] = days
            data["lot"][j["k"]] = j["lot"]
            if n % 200 == 0:
                print(f"  {n}/{len(jobs)}", flush=True)
    variants = []
    for lag in (1, 0):
        for k in KS:
            for w in WS:
                for stop in STOPS:
                    for mode in ("condor", "trend"):
                        tr = []
                        for t in plans:
                            if t["lag"] != lag:
                                continue
                            sides = ("CE", "PE") if mode == "condor" else (("PE",) if t["trend"] > 0 else ("CE",))
                            for sd in sides:
                                r = run_trade(t, k, w, sd, stop, data)
                                if r:
                                    tr.append(r)
                        st = stats(tr)
                        if st:
                            by_sym = {s: stats([x for x in tr if x["sym"] == s]) for s in UND}
                            variants.append({"entry": "T-1 09:30" if lag else "expiry day 09:30", "k": k, "w": w,
                                             "stop": f"{stop:g}x credit" if stop else "none", "mode": mode, **st, "bySym": by_sym,
                                             "recent": tr[-8:]})
    variants.sort(key=lambda v: (-(v["pf"] or 0) if v["n"] >= 40 else 0, -v["winRate"]))
    good = [v for v in variants if v["n"] >= 40 and (v["pf"] or 0) > 1.0 and v["total"] > 0]
    best = max(good, key=lambda v: (v["winRate"], v["pf"] or 0)) if good else None
    res = {"generated": datetime.now(IST).isoformat(timespec="seconds"), "method": __doc__.strip(), "best": best,
           "top": sorted(good, key=lambda v: (-v["winRate"], -(v["pf"] or 0)))[:15], "variants": len(variants),
           "all": [{k2: v[k2] for k2 in ("entry", "k", "w", "stop", "mode", "n", "winRate", "pf", "total", "perTrade", "worst")} for v in variants]}
    out = os.path.join(HERE, "static", "hedge_backtest.json")
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps({k2: res[k2] for k2 in ("best",)}, indent=1)[:3000])


if __name__ == "__main__":
    main()
