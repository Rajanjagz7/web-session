"""Backtest of the three premium indicators on real 1-minute prices (run on GitHub Actions).

Data (through the site's read-only research proxy, which holds the broker token):
  * NIFTY weekly + BANKNIFTY monthly EXPIRED option contracts, 1-minute candles, the last 5 sessions of every expiry,
    strikes ATM +/- 8 steps (CE and PE), ~Oct 2024 onwards.
  * 20 liquid F&O stocks, 1-minute candles, last 12 months.

Indicators (as specified by the user)
  A  Expiry Divisor   - expiry day only. Premium Open = High (never traded above open + 0.5). Buy levels Open/4, /6.5,
                        /8, /10 (limit at the level when price falls to it). SL 5 or 10 points.
  B  Daily Divisor    - other days. Base = High when High = Open or High = Previous close (not exceeded). Buy levels
                        base/2 and base/4. SL 5 or 10 points.
     B-OL Clean buy   - Open = Low (low never under open - 0.5) at 09:20 and price above open -> buy at 09:20.
  C  OH / OL (10 pt)  - at 09:20 (and 09:30): Open = Low within 10 points (low >= open - 10) and price >= open -> BUY;
                        stocks also Open = High within 10 (high <= open + 10) and price <= open -> SELL. SL 3 points.
Exits tested for every entry: target 1:2, target 1:3, next divisor level up (A/B), premium 1.5x / 2x / 5x / 10x
(user targets, options only), or hold to 15:25. A candle that
touches both stop and target counts as a stop. No entries after 15:00.
"""
import concurrent.futures as cf
import json
import os
import statistics
import sys
import time
from datetime import date, datetime, timedelta, timezone

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_backtest_ci as CI  # noqa: E402  (Yahoo daily candles for strike selection)

BASE = os.environ.get("RESEARCH_BASE", "https://rajanstocks.vercel.app")
IST = timezone(timedelta(hours=5, minutes=30))
S = requests.Session()
S.headers["User-Agent"] = "rajan-backtest"
INDEX = {"NIFTY": {"step": 50, "yh": "NIFTY"}, "BANKNIFTY": {"step": 100, "yh": "BANKNIFTY"}, "SENSEX": {"step": 100, "yh": "SENSEX"}}
ZONES = {   # user zone indicators (20 Oct 2026) - same numbers as strategies_api.ZONES
    "sensex-310": {"ref": "prev", "ref_lo": 310, "ref_hi": 340, "lo": 52, "hi": 58, "t": (88, 92, 105), "sl": (48,), "only": "SENSEX"},     # SL 10 points under the 58 entry
    "prem-38-42": {"ref": "open", "ref_lo": 38, "ref_hi": 42, "lo": 7.80, "hi": 8.45, "t": (12, 16, 22, 32, 42), "sl": (5.80,), "only": None},
}
STOCKS = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK", "LT",
          "AXISBANK", "BAJFINANCE", "MARUTI", "SUNPHARMA", "TITAN", "HCLTECH", "TATASTEEL", "M&M", "ADANIENT", "ONGC"]
TOL = 0.5
LAST_ENTRY = 15 * 60
EOD = 15 * 60 + 25


def get(path, params, tries=4):
    for k in range(tries):
        try:
            r = S.get(BASE + path, params=params, timeout=60)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (400, 404):
                return None
        except Exception:
            pass
        time.sleep(1.5 * (k + 1))
    return None


def mins(ts):
    d = datetime.fromisoformat(ts)
    return d.hour * 60 + d.minute


def by_day(candles):
    """[[ts,o,h,l,c,v,...]] -> {date: [(minute,o,h,l,c)]} sorted."""
    out = {}
    for c in candles:
        ts = c[0]
        out.setdefault(ts[:10], []).append((mins(ts), float(c[1]), float(c[2]), float(c[3]), float(c[4])))
    for d in out:
        out[d].sort()
    return out


# ───────────────────────── trade management ─────────────────────────
def manage(bars, i, entry, side, sl_pts, targets, at_close=False):
    """Run one trade from bar i (entry inside bar i, or at its close when at_close). -> {target_name: points}."""
    d = 1 if side == "BUY" else -1
    stop = max(0.05, entry - sl_pts) if d > 0 else entry + sl_pts
    res = {}
    for name, tgt in targets.items():
        out = None
        for j in range(i, len(bars)):
            m, o, h, l, c = bars[j]
            if m > EOD:
                break
            hit_sl = (l <= stop) if d > 0 else (h >= stop)
            hit_t = tgt is not None and ((h >= tgt) if d > 0 else (l <= tgt))
            if j == i:                               # entry bar: only a stop beyond the entry can be resolved
                if at_close:
                    continue
                if (d > 0 and l <= stop and stop < entry) or (d < 0 and h >= stop):
                    out = (stop - entry) * d
                    break
                continue
            if hit_sl:
                out = (stop - entry) * d
                break
            if hit_t:
                out = (tgt - entry) * d
                break
        if out is None:
            eod = [b for b in bars[i:] if b[0] <= EOD]
            out = ((eod[-1][4] if eod else entry) - entry) * d
        res[name] = round(out, 2)
    return res


def level_trades(bars, base_fn, valid_fn, levels, sl_list):
    """Limit buys at base/k when price falls to them while the condition still holds. One trade per level per day."""
    trades = []
    done = set()
    hi = -1e9
    lo = 1e9
    for i, (m, o, h, l, c) in enumerate(bars):
        if m > LAST_ENTRY:
            break
        hi, lo = max(hi, h), min(lo, l)
        if not valid_fn(hi, i):
            break                                   # condition broken: the setup is over for the day
        base = base_fn(hi, i)
        if not base:
            continue
        ks = sorted(levels, key=lambda k: base / k, reverse=True)
        for idx, k in enumerate(ks):
            lv = round(base / k, 2)
            if k in done or lv < 1.0:
                continue
            if l <= lv and (i > 0 and bars[i - 1][4] > lv):   # touched from above
                nxt = round(base / ks[idx - 1], 2) if idx > 0 else round(base / 2, 2)
                for sl in sl_list:
                    t = {"1:2": lv + 2 * sl, "1:3": lv + 3 * sl, "next level": nxt, "hold to 15:25": None, **mult_targets(lv)}
                    trades.append({"level": f"/{k:g}", "sl": sl, "entryMin": m, "entry": lv, "res": manage(bars, i, lv, "BUY", sl, t)})
                done.add(k)
    return trades


def ind_A(bars):
    o = bars[0][1]
    if o < 20:
        return []
    return level_trades(bars, lambda hi, i: o, lambda hi, i: hi <= o + TOL, (4, 6.5, 8, 10), (5, 10))


def ind_B(bars, pc):
    o = bars[0][1]
    if o < 20:
        return []
    def valid(hi, i):                       # High = Open so far, or price has not gone above the previous close
        return hi <= o + TOL or bool(pc and hi <= pc + TOL)
    def base(hi, i):
        if hi <= o + TOL:
            return max(o, hi)
        if pc and abs(hi - pc) <= TOL:
            return pc
        return None
    return level_trades(bars, base, valid, (2, 4), (5, 10))


def ind_open_low(bars, check_min, tol, sl_list, tgts_fn, allow_sell):
    o = bars[0][1]
    lo = min(b[3] for b in bars if b[0] <= check_min) if bars else None
    hi = max(b[2] for b in bars if b[0] <= check_min) if bars else None
    idx = max((k for k, b in enumerate(bars) if b[0] <= check_min), default=None)
    if idx is None or idx + 1 >= len(bars):
        return []
    px = bars[idx][4]
    out = []
    if lo >= o - tol and px >= o:
        for sl in sl_list:
            out.append({"side": "BUY", "sl": sl, "entry": px, "res": manage(bars, idx, px, "BUY", sl, tgts_fn(px, sl, 1), at_close=True)})
    if allow_sell and hi <= o + tol and px <= o:
        for sl in sl_list:
            out.append({"side": "SELL", "sl": sl, "entry": px, "res": manage(bars, idx, px, "SELL", sl, tgts_fn(px, sl, -1), at_close=True)})
    return out


def ind_zone(z, bars, pc):
    """Buy at the top of the zone when the premium first falls into it (touch from above); one trade a day."""
    ref = pc if z["ref"] == "prev" else bars[0][1]
    if not ref or not (z["ref_lo"] <= ref <= z["ref_hi"]):
        return []
    for i, (m, o, h, l, c) in enumerate(bars):
        if m > LAST_ENTRY:
            return []
        prev_c = bars[i - 1][4] if i else o
        if l <= z["hi"] and prev_c > z["hi"]:
            out = []
            for sl in z["sl"]:
                t = {f"T {v:g}": v for v in z["t"]}
                t["hold to 15:25"] = None
                out.append({"sl": sl, "entry": z["hi"], "res": manage(bars, i, z["hi"], "BUY", z["hi"] - sl, t)})
            return out
    return []


def rr_targets(px, sl, d):
    return {"1:2": px + d * 2 * sl, "1:3": px + d * 3 * sl, "hold to 15:25": None}


def mult_targets(px):
    """User targets for premiums (20 Oct 2026): 1.5x, 2x, 5x, 10x the entry premium, within the day."""
    return {f"{m:g}x": round(px * m, 2) for m in (1.5, 2, 5, 10)}


def opt_targets(px, sl, d):
    return {**rr_targets(px, sl, d), **mult_targets(px)}


# ───────────────────────── data ─────────────────────────
def option_weeks(sym):
    ex = (get("/api/research/expired/expiries", {"symbol": sym}) or {}).get("data") or []
    ex = [e for e in ex if e >= "2024-10-01"]
    if sym == "BANKNIFTY":
        ex = [e for e in ex if e >= "2024-12-01"]          # monthly only from Dec 2024
    daily = {b["date"]: b for b in CI._yahoo(INDEX[sym]["yh"])}
    days = sorted(daily)
    jobs = []
    for e in ex:
        start = (date.fromisoformat(e) - timedelta(days=7)).isoformat()
        ref = [d for d in days if d <= start]
        if not ref:
            continue
        spot = daily[ref[-1]]["close"]
        con = (get("/api/research/expired/contracts", {"symbol": sym, "expiry": e}) or {}).get("data") or []
        step = INDEX[sym]["step"]
        atm = round(spot / step) * step
        for c in con:
            k = float(c.get("strike_price") or 0)
            if abs(k - atm) <= 8 * step and c.get("instrument_type") in ("CE", "PE"):
                jobs.append({"sym": sym, "expiry": e, "strike": k, "type": c["instrument_type"], "key": c["instrument_key"],
                             "lot": int(c.get("lot_size") or 1), "frm": start, "to": e})
    return jobs


CACHE_DIR = os.path.join(HERE, ".pcache")
os.makedirs(CACHE_DIR, exist_ok=True)


def _cpath(key):
    import hashlib
    return os.path.join(CACHE_DIR, hashlib.md5(key.encode()).hexdigest() + ".json")


def fetch_contract(j):
    p = _cpath(j["key"] + j["frm"] + j["to"])
    if os.path.exists(p):
        with open(p) as f:
            return j, {k: [tuple(b) for b in v] for k, v in json.load(f).items()}
    d = get("/api/research/expired/candles", {"key": j["key"], "interval": "1minute", "frm": j["frm"], "to": j["to"]})
    cs = ((d or {}).get("data") or {}).get("candles") or []
    out = by_day(cs)
    if d is not None and j["to"] < datetime.now(IST).date().isoformat():
        with open(p, "w") as f:
            json.dump(out, f)
    return j, out


def run_options():
    jobs = []
    for sym in INDEX:
        w = option_weeks(sym)
        print(f"{sym}: {len(w)} contracts to fetch", flush=True)
        jobs += w
    A, B, BOL, C = [], [], [], []
    Z = {k: [] for k in ZONES}
    done = 0
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        for j, days in ex.map(fetch_contract, jobs):
            done += 1
            if done % 250 == 0:
                print(f"  {done}/{len(jobs)} contracts", flush=True)
            prev_close = None
            for d in sorted(days):
                bars = days[d]
                if len(bars) < 60 or bars[0][0] > 9 * 60 + 20:
                    prev_close = bars[-1][4] if bars else prev_close
                    continue
                tag = {"sym": j["sym"], "date": d, "expiry": j["expiry"], "strike": j["strike"], "type": j["type"], "lot": j["lot"]}
                for zk, z in ZONES.items():
                    if z["only"] in (None, j["sym"]):
                        for t in ind_zone(z, bars, prev_close):
                            Z[zk].append({**tag, **t})
                if d == j["expiry"]:
                    for t in ind_A(bars):
                        A.append({**tag, **t})
                else:
                    for t in ind_B(bars, prev_close):
                        B.append({**tag, **t})
                    for t in ind_open_low(bars, 9 * 60 + 20, TOL, (5, 10), opt_targets, False):
                        BOL.append({**tag, **t})
                for cm in (9 * 60 + 20, 9 * 60 + 30):
                    for t in ind_open_low(bars, cm, 10.0, (3,), opt_targets, False):
                        C.append({**tag, **t, "check": f"{cm // 60:02d}:{cm % 60:02d}", "market": "option"})
                prev_close = bars[-1][4]
    return A, B, BOL, C, Z


def run_stocks():
    C = []
    today = datetime.now(IST).date()
    for s in STOCKS:
        for k in range(12):
            to = today - timedelta(days=30 * k)
            frm = to - timedelta(days=29)
            p = _cpath(f"stk{s}{frm}{to}")
            if os.path.exists(p) and k > 0:
                with open(p) as f:
                    days = {kk: [tuple(b) for b in v] for kk, v in json.load(f).items()}
            else:
                d = get("/api/research/candles", {"symbol": s, "frm": frm.isoformat(), "to": to.isoformat(), "interval": "1"})
                days = by_day((d or {}).get("candles") or [])
                if d is not None and k > 0:
                    with open(p, "w") as f:
                        json.dump(days, f)
            for day, bars in days.items():
                if len(bars) < 300 or bars[0][0] > 9 * 60 + 16:
                    continue
                for cm in (9 * 60 + 20, 9 * 60 + 30):
                    for t in ind_open_low(bars, cm, 10.0, (3,), rr_targets, True):
                        C.append({"sym": s, "date": day, "lot": 1, **t, "check": f"{cm // 60:02d}:{cm % 60:02d}", "market": "stock"})
        print(f"  {s}: {sum(1 for t in C if t['sym'] == s)} OH/OL signals", flush=True)
    return C


# ───────────────────────── summary ─────────────────────────
def summarize(trades, group_keys):
    out = []
    if not trades:
        return out
    split = sorted(t["date"] for t in trades)[int(len(trades) * 0.7)]
    groups = {}
    for t in trades:
        for tname, pts in t["res"].items():
            g = tuple(t.get(k) for k in group_keys) + (tname,)
            groups.setdefault(g, []).append((t["date"], pts, pts * t.get("lot", 1)))
    for g, rows in sorted(groups.items(), key=lambda x: [str(v) for v in x[0]]):
        def st(rs):
            if not rs:
                return {"n": 0}
            pts = [r[1] for r in rs]
            w, l = sum(p for p in pts if p > 0), -sum(p for p in pts if p < 0)
            return {"n": len(pts), "win": round(sum(1 for p in pts if p > 0) / len(pts), 3), "avgPts": round(statistics.mean(pts), 2),
                    "totalPts": round(sum(pts), 1), "pf": round(w / l, 2) if l else (99.0 if w else 0),
                    "avgRsLot": round(statistics.mean(r[2] for r in rs), 0)}
        out.append({**{k: v for k, v in zip(group_keys + ["exit"], g)}, "all": st(rows),
                    "is": st([r for r in rows if r[0] < split]), "oos": st([r for r in rows if r[0] >= split])})
    return out


if __name__ == "__main__":
    t0 = time.time()
    A, B, BOL, Copt, Z = run_options()
    Cst = run_stocks()
    res = {
        "generatedAt": datetime.now(IST).isoformat(), "method": __doc__,
        "A_expiry_divisor": summarize(A, ["level", "sl"]),
        "B_daily_divisor": summarize(B, ["level", "sl"]),
        "B_open_low_clean_buy": summarize(BOL, ["sl"]),
        "C_ohol_options": summarize(Copt, ["check", "side"]),
        "C_ohol_stocks": summarize(Cst, ["check", "side"]),
        "D_sensex_310": summarize(Z["sensex-310"], ["sl"]),
        "E_prem_38_42": summarize(Z["prem-38-42"], ["sym", "sl"]),
        "counts": {"D": len(Z["sensex-310"]), "E": len(Z["prem-38-42"]), "A": len(A), "B": len(B), "BOL": len(BOL), "Copt": len(Copt), "Cst": len(Cst),
                   "expiryDays": len({(t["sym"], t["date"]) for t in A}), "optionDays": len({(t["sym"], t["date"]) for t in B + BOL})},
        "runtimeSec": round(time.time() - t0),
    }
    with open(os.path.join(HERE, "static", "premium_backtest.json"), "w") as f:
        json.dump(res, f)
    for name in ("A_expiry_divisor", "B_daily_divisor", "B_open_low_clean_buy", "C_ohol_options", "C_ohol_stocks", "D_sensex_310", "E_prem_38_42"):
        print("==", name)
        for r in res[name]:
            print({k: v for k, v in r.items() if k not in ("is", "oos")}, "| OOS", r["oos"])
    print(res["counts"], f"{time.time() - t0:.0f}s")
