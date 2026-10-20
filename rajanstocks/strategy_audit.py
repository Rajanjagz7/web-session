"""Deep audit of every strategy on the site (visible and hidden) - run on GitHub Actions with Yahoo data.

For each DAILY indicator, over ~4 years of daily candles for 5 indices + 20 liquid F&O stocks:
  1. Repaint / delay check - for a sample of signals the indicator is re-run "as of" the signal day and the next
     few days. A signal that only appears on a past candle later (pivots, divergences) gets its real confirmation
     delay; entries in every test below use that delay, so hindsight signals are not rewarded.
  2. Edge - direction-adjusted move after the signal (1, 3, 5, 10 sessions, in ATR units) minus the symbol's normal
     drift over the same horizon, with a t-statistic.
  3. Lag - how far price had already moved in the signal's direction over the 3 sessions before it (in ATR).
  4. Futures / stock test - indicator stop (or signal-candle stop, 0.5-1 ATR), 2R target, 10 sessions, 0.05% cost.
  5. Option-buyer test - backtest.simulate (30%-of-premium stop, daily theta to the real expiry, out before expiry).
  Every test is split in time: first 70% of signals in-sample, last 30% out-of-sample.
For INTRADAY indicators (ORB, VWAP+RSI, 3-min HA channels) the last ~25 sessions of 1-minute candles are replayed
day by day; edge = direction-adjusted move 30 minutes later and at 15:25.
Duplicates: share of signals two indicators give on the same symbol, same side, within one session.

Verdict
  KEEP   - out-of-sample futures PF >= 1.10 with in-sample PF >= 1.0 and >= 30 OOS trades, OR a 3/5-session edge with
           t >= 2 in BOTH halves.
  WATCH  - one half clearly positive and the other not negative (PF >= 1.0 / edge >= 0), or too few trades to judge.
  REMOVE - no edge in either half, or the signal mostly exists only in hindsight (repaints).
  INFO   - not a buy/sell signal (range / volume / compression tools): judged on what they claim instead.
"""
import json
import math
import os
import random
import statistics
import sys
import time
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import run_backtest_ci as CI  # noqa: E402  (patches bar_source to Yahoo daily candles)
import bar_source  # noqa: E402
import backtest  # noqa: E402
import requests  # noqa: E402
import strategies_api as SA  # noqa: E402
import ut_bot  # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))
SYMS = backtest.INDEX_SYMS + backtest.STOCK_SYMS
INTRADAY = ["orb-15m", "vwap-rsi", "heikin-ashi-channel", "ha-dancing-trend"]
INFO = {"vix-range": "range", "volume-buzzer-15m": "volume", "volume-buzzer-daily": "volume", "volume-spurt": "volume",
        "tight-range": "compression"}
OFFSETS = list(range(0, 1500, 75))           # as-of replays every 75 calendar days -> ~4 years, no gaps
HORIZONS = (1, 3, 5, 10)
random.seed(7)
TODAY = datetime.now(IST).date()

FULL = {}
for s in SYMS + ["INDIAVIX"]:
    FULL[s] = CI._yahoo(s)
SYMS = [s for s in SYMS if len(FULL.get(s) or []) > 400]
ATR = {s: backtest._atr(FULL[s]) for s in SYMS}
IDX = {s: {b["date"]: i for i, b in enumerate(FULL[s])} for s in SYMS}
_asof = {"d": None}


def _daily(symbol, lookback_days=180):
    bars = FULL.get(symbol.upper()) or CI._yahoo(symbol)
    cut = (_asof["d"] or TODAY).isoformat()
    lo = ((_asof["d"] or TODAY) - timedelta(days=int(lookback_days))).isoformat()
    return [b for b in bars if lo <= b["date"] <= cut]


bar_source.daily_bars = _daily
ut_bot.fetch_index_history = lambda symbol, lookback_days=60, max_workers=20: _daily(symbol, lookback_days)
try:
    import quantum_matrix
    quantum_matrix.fetch_index_history = ut_bot.fetch_index_history
except Exception:
    pass
for mod in ("rajan_pavan_indicators", "rajan_new_indicators", "rajan_extra_indicators"):
    try:
        m = __import__(mod)
        if hasattr(m, "fetch_index_history"):
            m.fetch_index_history = ut_bot.fetch_index_history
    except Exception:
        pass


def norm(v):
    s = str(v or "").upper()
    if s in ("BUZZ", "SPURT", "COMPRESSING"):
        return "INFO"
    return backtest.norm_signal(v)


def run_key(key, sym):
    if key == "quantum-matrix":           # its trade signal is UT Bot (key 1.0, ATR 10) on daily candles
        bars = _daily(sym, 400)
        stops, pos, sig = ut_bot.compute_signals(bars, key_value=1.0, atr_period=10)
        return [{"date": b["date"], "signal": sig[i] if i < len(sig) else None} for i, b in enumerate(bars)]
    r = SA._run_raw(key, sym)
    return r.get("bars") or r.get("rows") or []


def rows_signals(rows):
    """{date: (side, stop)} - first bar of every run of the same signal."""
    out, prev = {}, None
    for r in rows:
        d = r.get("date")
        sg = norm(r.get("signal"))
        if d and sg and sg != prev:
            stop = r.get("stop") or r.get("stopLoss") or (r.get("bullSL") if sg == "BUY" else r.get("bearSL") if sg == "SELL" else None)
            out.setdefault(str(d)[:10], (sg, stop))
        prev = sg
    return out


def collect(key, sym):
    sig = {}
    for off in OFFSETS:
        _asof["d"] = TODAY - timedelta(days=off)
        try:
            rows = run_key(key, sym)
        except Exception:
            continue
        for d, v in rows_signals(rows).items():
            sig.setdefault(d, v)
    _asof["d"] = None
    return sig


def confirm_delay(key, sym, d, side):
    """Trading sessions after d at which the indicator first SHOWS this signal on bar d (None = never in 8)."""
    i0 = IDX[sym].get(d)
    if i0 is None:
        return None
    for k in (0, 1, 2, 3, 5, 8):
        j = i0 + k
        if j >= len(FULL[sym]):
            return None
        _asof["d"] = date.fromisoformat(FULL[sym][j]["date"])
        try:
            got = rows_signals(run_key(key, sym))
        except Exception:
            got = {}
        _asof["d"] = None
        if got.get(d, (None,))[0] == side:
            if k == 0:
                return 0
            for kk in range(max(0, k - 2), k + 1):        # refine between the probed points
                jj = i0 + kk
                _asof["d"] = date.fromisoformat(FULL[sym][jj]["date"])
                try:
                    g2 = rows_signals(run_key(key, sym))
                except Exception:
                    g2 = {}
                _asof["d"] = None
                if g2.get(d, (None,))[0] == side:
                    return kk
            return k
    return None


def tstat(xs):
    if len(xs) < 3:
        return 0.0
    sd = statistics.pstdev(xs)
    return statistics.mean(xs) / (sd / math.sqrt(len(xs))) if sd > 0 else 0.0


def drift(sym, h):
    bars, atr = FULL[sym], ATR[sym]
    xs = [(bars[t + h - 1]["close"] - bars[t]["open"]) / atr[t - 1] for t in range(20, len(bars) - h) if atr[t - 1]]
    return statistics.mean(xs) if xs else 0.0


DRIFT = {(s, h): drift(s, h) for s in SYMS for h in HORIZONS}


def fut_sim(bars, atr, i, side, ind_stop):
    """Futures/stock trade: entry next open, indicator or signal-candle stop (no premium cap), 2R, 10 sessions."""
    if i + 1 >= len(bars) or not atr[i]:
        return None
    d = 1 if side == "BUY" else -1
    entry = bars[i + 1]["open"]
    risk = backtest.plan_risk(bars, atr[i], i, side, entry, 1e12, ind_stop=ind_stop)
    if risk <= 0:
        return None
    stop, tgt = entry - d * risk, entry + d * 2 * risk
    cost = 0.0005 * entry / risk
    for j in range(i + 1, min(len(bars), i + 11)):
        b = bars[j]
        if j > i + 1 and (b["open"] - stop) * d <= 0:
            return d * (b["open"] - entry) / risk - cost
        if (b["low"] - stop if d > 0 else stop - b["high"]) <= 0:
            return -1 - cost
        if (b["high"] - tgt if d > 0 else tgt - b["low"]) >= 0:
            return 2 - cost
    j = min(len(bars) - 1, i + 10)
    if j < i + 10:
        return None
    return d * (bars[j]["close"] - entry) / risk - cost


def stats_r(rs):
    if not rs:
        return {"n": 0, "avgR": 0, "pf": 0, "win": 0}
    w = sum(r for r in rs if r > 0)
    l = -sum(r for r in rs if r < 0)
    return {"n": len(rs), "avgR": round(statistics.mean(rs), 3), "pf": round(w / l, 2) if l > 0 else (99.0 if w > 0 else 0),
            "win": round(sum(1 for r in rs if r > 0) / len(rs), 3)}


def audit_daily(keys):
    allsig = {}
    for key in keys:
        t0 = time.time()
        allsig[key] = {s: collect(key, s) for s in SYMS}
        print(f"  {key}: {sum(len(v) for v in allsig[key].values())} signals in {time.time() - t0:.0f}s", flush=True)
    dates = sorted(d for k in allsig for s in allsig[k] for d in allsig[k][s])
    split = dates[int(len(dates) * 0.7)] if dates else TODAY.isoformat()
    res = {}
    for key in keys:
        sig = allsig[key]
        n_all = sum(len(v) for v in sig.values())
        directional = [(s, d, v) for s in sig for d, v in sig[s].items() if v[0] in ("BUY", "SELL")]
        info = [(s, d, v) for s in sig for d, v in sig[s].items() if v[0] == "INFO"]
        r = {"key": key, "name": SA.META.get(key, {}).get("name", key), "hidden": key in SA.HIDDEN, "signals": n_all}
        if not directional:
            # an alert tool claims "a big move is coming": next 5 sessions' range vs the symbol's normal 5-session range
            ratios = {"is": [], "oos": []}
            for s, d, v in info:
                i = IDX[s].get(d)
                if i is None or i + 6 >= len(FULL[s]) or i < 30:
                    continue
                bars = FULL[s]
                rng = (max(b["high"] for b in bars[i + 1:i + 6]) - min(b["low"] for b in bars[i + 1:i + 6]))
                base = statistics.mean(max(b["high"] for b in bars[t:t + 5]) - min(b["low"] for b in bars[t:t + 5]) for t in range(i - 25, i - 5))
                if base > 0:
                    ratios["is" if d < split else "oos"].append(rng / base)
            r.update(kind="info", infoSignals=len(info),
                     nextRange={h: {"ratio": round(statistics.mean(v), 2) if v else None, "n": len(v)} for h, v in ratios.items()})
            res[key] = r
            continue
        # 1. repaint / delay
        sample = random.sample(directional, min(len(directional), 60))
        ks = [confirm_delay(key, s, d, v[0]) for s, d, v in sample]
        found = [k for k in ks if k is not None]
        delay = int(math.ceil(statistics.median(found))) if found else 0
        r["repaint"] = {"checked": len(ks), "liveOnTheDay": sum(1 for k in ks if k == 0), "late": sum(1 for k in ks if k and k > 0),
                        "neverLive": sum(1 for k in ks if k is None), "delayUsed": delay}
        # 2-5 per signal
        edge = {h: {"is": [], "oos": []} for h in HORIZONS}
        lag, fut, opt = [], {"is": [], "oos": []}, {"is": [], "oos": []}
        years = max(1.0, (date.fromisoformat(max(dates)) - date.fromisoformat(min(dates))).days / 365) if dates else 1
        for s, d, (side, stop) in directional:
            i0 = IDX[s].get(d)
            if i0 is None:
                continue
            i = i0 + delay
            bars, atr = FULL[s], ATR[s]
            if i + 11 >= len(bars) or i < 25 or not atr[i]:
                continue
            sgn = 1 if side == "BUY" else -1
            half = "is" if d < split else "oos"
            for h in HORIZONS:
                if i + h < len(bars):
                    mv = sgn * (bars[i + h]["close"] - bars[i + 1]["open"]) / atr[i] - sgn * DRIFT[(s, h)]
                    edge[h][half].append(mv)
            lag.append(sgn * (bars[i]["close"] - bars[i - 3]["close"]) / atr[i])
            f = fut_sim(bars, atr, i, side, stop if delay == 0 else None)
            if f is not None:
                fut[half].append(f)
            try:
                o = backtest.simulate(bars, atr, i, side, "fixed", None, "index" if s in backtest.INDEX_SYMS else "stock",
                                      stop if delay == 0 else None)
                if o:
                    opt[half].append(o[0])
            except Exception:
                pass
        r.update(kind="directional", perSymbolYear=round(len(directional) / len(SYMS) / years, 1),
                 edge={str(h): {"is": round(statistics.mean(edge[h]["is"]), 3) if edge[h]["is"] else None,
                                "isT": round(tstat(edge[h]["is"]), 2),
                                "oos": round(statistics.mean(edge[h]["oos"]), 3) if edge[h]["oos"] else None,
                                "oosT": round(tstat(edge[h]["oos"]), 2)} for h in HORIZONS},
                 lagATR=round(statistics.mean(lag), 2) if lag else None,
                 futures={"is": stats_r(fut["is"]), "oos": stats_r(fut["oos"])},
                 options={"is": stats_r(opt["is"]), "oos": stats_r(opt["oos"])})
        res[key] = r
    # duplicates
    def keyset(k):
        return {(s, d, v[0]) for s in allsig[k] for d, v in allsig[k][s].items() if v[0] in ("BUY", "SELL")}
    sets = {k: keyset(k) for k in keys}
    near = {}
    for k in keys:
        st = set()
        for s, d, side in sets[k]:
            i = IDX[s].get(d)
            if i is None:
                continue
            for j in (i - 1, i, i + 1):
                if 0 <= j < len(FULL[s]):
                    st.add((s, FULL[s][j]["date"], side))
        near[k] = st
    dups = []
    for a in keys:
        for b in keys:
            if a < b and sets[a] and sets[b]:
                ov_a = len(sets[a] & near[b]) / len(sets[a])
                ov_b = len(sets[b] & near[a]) / len(sets[b])
                if max(ov_a, ov_b) >= 0.35:
                    dups.append({"a": a, "b": b, "aInB": round(ov_a, 2), "bInA": round(ov_b, 2)})
    return res, dups, split


# ───────────────────────── intraday ─────────────────────────
def yahoo_1m(sym):
    t = CI.YH.get(sym, sym + ".NS")
    out = {}
    end = int(time.time())
    for k in range(4):
        p2, p1 = end - k * 7 * 86400, end - (k + 1) * 7 * 86400
        try:
            r = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{requests.utils.quote(t)}",
                             params={"period1": p1, "period2": p2, "interval": "1m"}, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            res = r.json()["chart"]["result"][0]
            q = res["indicators"]["quote"][0]
            for i, ts in enumerate(res.get("timestamp") or []):
                o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
                if None in (o, h, l, c):
                    continue
                dt = datetime.fromtimestamp(ts, IST)
                out[dt] = {"dt": dt, "open": o, "high": h, "low": l, "close": c, "volume": q["volume"][i] or 0}
        except Exception as e:
            print(f"  1m {sym}: {e}")
        time.sleep(0.5)
    return [out[k] for k in sorted(out)]


def parse_events(key, ev, day):
    out = []
    for e in ev or []:
        side, ts = None, None
        if key in ("heikin-ashi-channel", "ha-dancing-trend"):
            if e.get("event") != "ENTRY":
                continue
            side = "BUY" if e.get("type") == "BUY" else "SELL"
            try:
                ts = datetime.strptime(e["time"], "%Y-%m-%d %H:%M").replace(tzinfo=IST)
            except Exception:
                continue
        else:
            txt = str(e.get("text", "")).upper()
            side = "BUY" if "BUY" in txt else "SELL" if "SELL" in txt else None
            try:
                ts = datetime.strptime(f"{e['date']} {day.year}", "%d %b %H:%M %Y").replace(tzinfo=IST)
            except Exception:
                continue
        if side and ts.date() == day:
            out.append((ts, side))
    return out


def audit_intraday():
    M1 = {s: yahoo_1m(s) for s in SYMS}
    days = sorted({b["dt"].date() for s in M1 for b in M1[s]})
    res = {}
    for key in INTRADAY:
        moves30, moves_eod, n = {"is": [], "oos": []}, {"is": [], "oos": []}, 0
        cut = days[int(len(days) * 0.6)] if days else TODAY
        for s in SYMS:
            bars = M1[s]
            if len(bars) < 2000:
                continue
            by_dt = {b["dt"]: i for i, b in enumerate(bars)}
            for day in days[5:]:
                end = datetime(day.year, day.month, day.day, 15, 30, tzinfo=IST)
                start = end - timedelta(days=9)
                bar_source.bars_1m = lambda symbol, days=5, _s=s, _e=end, _st=start: [b for b in M1[_s] if _st <= b["dt"] <= _e]
                _asof["d"] = day - timedelta(days=1)
                try:
                    r = SA._run_raw(key, s)
                except Exception:
                    continue
                finally:
                    _asof["d"] = None
                seen = set()
                for ts, side in parse_events(key, r.get("events"), day):
                    if (side in seen) or ts.hour * 60 + ts.minute > 14 * 60 + 45:
                        continue
                    seen.add(side)
                    i = by_dt.get(ts)
                    if i is None:
                        continue
                    sg = 1 if side == "BUY" else -1
                    px = bars[i]["close"]
                    j30 = min(i + 30, len(bars) - 1)
                    eod = max(k for k in range(i, min(i + 400, len(bars))) if bars[k]["dt"].date() == day)
                    half = "is" if day < cut else "oos"
                    moves30[half].append(sg * (bars[j30]["close"] / px - 1) * 1e4)
                    moves_eod[half].append(sg * (bars[eod]["close"] / px - 1) * 1e4)
                    n += 1
        res[key] = {"key": key, "name": SA.META.get(key, {}).get("name", key), "hidden": key in SA.HIDDEN, "kind": "intraday",
                    "sessions": len(days), "signals": n,
                    "bp30": {h: {"mean": round(statistics.mean(v), 1) if v else None, "t": round(tstat(v), 2), "n": len(v),
                                 "hit": round(sum(1 for x in v if x > 0) / len(v), 3) if v else None} for h, v in moves30.items()},
                    "bpClose": {h: {"mean": round(statistics.mean(v), 1) if v else None, "t": round(tstat(v), 2), "n": len(v),
                                    "hit": round(sum(1 for x in v if x > 0) / len(v), 3) if v else None} for h, v in moves_eod.items()}}
        print(f"  {key}: {n} intraday signals", flush=True)
    return res


def info_checks():
    out = {}
    # VIX range: share of next-day high/low staying inside the predicted range (a 1-sigma band should hold ~68%)
    try:
        _asof["d"] = None
        rows = SA._run_raw("vix-range", "NIFTY").get("bars") or []
        nb = {b["date"]: b for b in FULL["NIFTY"]}
        days = sorted(nb)
        inside = tot = 0
        for r in rows:
            d = r.get("date")
            if d in nb and r.get("upperRange") and r.get("lowerRange"):
                k = days.index(d)
                if k + 1 < len(days):
                    b = nb[days[k + 1]]
                    tot += 1
                    inside += int(b["high"] <= r["upperRange"] and b["low"] >= r["lowerRange"])
        out["vix-range"] = {"checked": tot, "nextDayInsideRange": round(inside / tot, 3) if tot else None, "expected": 0.68}
    except Exception as e:
        out["vix-range"] = {"error": str(e)[:120]}
    return out


INFO_RES = {}


def verdict(r):
    if r.get("key") == "vix-range":
        v = (INFO_RES or {}).get("vix-range") or {}
        c = v.get("nextDayInsideRange")
        if c is None:
            return "WATCH", "Range tool - could not be checked"
        return ("KEEP" if 0.55 <= c <= 0.85 else "REMOVE"), f"Range tool: next day stayed inside the range {c * 100:.0f}% of the time ({v.get('checked')} days)"
    if r.get("signals", 1) == 0 and r.get("kind") != "intraday":
        return "REMOVE", "Never gave a signal in ~4 years on 23 symbols"
    if r.get("kind") == "info":
        nr = r.get("nextRange") or {}
        a, b = (nr.get("is") or {}), (nr.get("oos") or {})
        if r["key"] == "vix-range":
            v = (INFO_RES or {}).get("vix-range") or {}
            c = v.get("nextDayInsideRange")
            if c is None:
                return "WATCH", "Range tool - could not be checked"
            return ("KEEP" if 0.55 <= c <= 0.85 else "REMOVE"), f"Range tool: next day stayed inside the range {c * 100:.0f}% of the time ({v.get('checked')} days)"
        if (a.get("n") or 0) + (b.get("n") or 0) < 30:
            return "WATCH", "Alert tool: too few alerts to judge"
        if (a.get("ratio") or 0) >= 1.15 and (b.get("ratio") or 0) >= 1.15:
            return "KEEP", f"Alert tool: the next 5 sessions move {b['ratio']}x the normal range"
        return "REMOVE", f"Alert tool: moves after the alert are normal size ({a.get('ratio')}x / {b.get('ratio')}x)"
    if r.get("kind") == "intraday":
        a, b = r["bp30"]["is"], r["bp30"]["oos"]
        c, d = r["bpClose"]["is"], r["bpClose"]["oos"]
        if (a["n"] + b["n"]) < 30:
            return "WATCH", "Too few intraday signals in ~25 sessions to judge"
        good = lambda x: x["mean"] is not None and x["mean"] > 0 and x["t"] >= 1.5
        if (good(a) and (b["mean"] or 0) > 0) or (good(c) and (d["mean"] or 0) > 0) or (good(b) and (a["mean"] or 0) > 0):
            return "KEEP", "Moves the right way after the signal in both halves"
        if max((a["mean"] or -1), (b["mean"] or -1), (c["mean"] or -1), (d["mean"] or -1)) > 0:
            return "WATCH", "Mixed: positive in one window only"
        return "REMOVE", "Price moved against the signal on average"
    rp = r["repaint"]
    if rp["checked"] >= 10 and rp["neverLive"] / rp["checked"] > 0.5:
        return "REMOVE", "Most signals only appear in hindsight (repaints)"
    fi, fo = r["futures"]["is"], r["futures"]["oos"]
    e3, e5 = r["edge"]["3"], r["edge"]["5"]
    edge_both = any(e["isT"] >= 2 and e["oosT"] >= 2 for e in (e3, e5))
    if (fo["n"] >= 30 and fo["pf"] >= 1.10 and fi["pf"] >= 1.0) or edge_both:
        return "KEEP", "Real edge out-of-sample" + (" (also in-sample)" if fi["pf"] >= 1.1 or edge_both else "")
    if fo["n"] < 30 and fi["n"] < 60:
        return "WATCH", "Too few trades to judge"
    pos = lambda e: (e["is"] or 0) > 0 and (e["oos"] or 0) > 0
    if (fo["pf"] >= 1.0 and fi["pf"] >= 0.95) or pos(e3) or pos(e5):
        return "WATCH", "Small positive edge, not significant"
    return "REMOVE", "No edge: loses in futures test and the signal does not beat normal drift"


if __name__ == "__main__":
    t0 = time.time()
    daily_keys = [k for k in SA.META if k not in INTRADAY]
    print(f"daily audit: {len(daily_keys)} indicators x {len(SYMS)} symbols", flush=True)
    res, dups, split = audit_daily(daily_keys)
    print("intraday audit", flush=True)
    try:
        res.update(audit_intraday())
    except Exception as e:
        print("intraday failed:", e)
    info = info_checks()
    INFO_RES = info
    for k, r in res.items():
        r["verdict"], r["why"] = verdict(r)
    out = {"generatedAt": datetime.now(IST).isoformat(), "symbols": SYMS, "split": split, "results": res,
           "duplicates": sorted(dups, key=lambda x: -max(x["aInB"], x["bInA"])), "info": info,
           "method": __doc__, "runtimeSec": round(time.time() - t0)}
    with open(os.path.join(HERE, "static", "strategy_audit.json"), "w") as f:
        json.dump(out, f)
    for k, r in sorted(res.items(), key=lambda x: x[1]["verdict"]):
        print(f"{r['verdict']:7} {k:22} {r['why']}")
    print(f"done in {time.time() - t0:.0f}s")
