"""Backtest of the morning shortlist (morning_picks.py): strength >= 75 first, Open = Low (BUY) / Open = High (SELL) second, 10-15 trades.

    python morning_backtest.py [N_STOCKS=100] [MONTHS=13]     # writes docs/MORNING_PICKS_ACCURACY.md and public/static/morning_backtest.json

Two replays, both free of look-ahead (each pick only uses data that existed at its decision time):
  MORNING  (the live behaviour)  5-minute candles. At 09:30 each stock is scored by the Picks engine on what the screen would show at
           that minute (today's open / range / volume so far + the completed daily history), then morning_picks.select() takes the
           shortlist and every trade is entered at the 09:35 candle's open.
  OVERNIGHT (long sample, ~4 years)  daily candles. The evening list (strength + risk/reward, no Open = Low/High - that needs intraday data)
           is entered at the next session's open.
Exits (underlying price, 0.1% round-trip cost, a candle touching both stop and target counts as the stop, gaps through the stop fill at the open):
  SWING     the pick's own stop (1.5-3 ATR), half at 1.5R then stop to entry, rest at 2.5R, max 10 sessions
  INTRADAY  stop just beyond today's extreme (0.3-0.6 ATR), all at 1R / 2R, squared off at 15:15
"""
import json
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone

import backtest as bt
import morning_picks as mp

IST = timezone(timedelta(hours=5, minutes=30))
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, ".cache", "m5")
COST = 0.001
HOLD = 10
DECIDE_MIN = 9 * 60 + 30            # the screen is read at 09:30
SQUARE_OFF = 15 * 60 + 15


# ───────────────────────── data ─────────────────────────
def load_5m(sym, months, log=None):
    """{date: [{m, o, h, l, c, v}]} for the last `months` months, 28-day windows, cached on disk."""
    import bar_source
    from upstox_service import background
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"{sym}.json")
    have = {}
    if os.path.exists(path):
        try:
            have = json.load(open(path))
        except Exception:
            have = {}
    end = date.today()
    start = end - timedelta(days=int(months * 30.5))
    need_from = have.get("_from")
    if need_from and need_from <= start.isoformat() and have.get("_to", "") >= (end - timedelta(days=3)).isoformat():
        return {k: v for k, v in have.items() if not k.startswith("_")}
    up = bar_source._up()
    key, _ = up._resolve_underlying(sym)
    days = {}
    a = start
    with background():
        while a < end:
            b = min(end, a + timedelta(days=28))
            for attempt in range(4):
                try:
                    rows = up.fetch_historical_candles(key, "minutes", "5", b.isoformat(), a.isoformat())
                    break
                except Exception as e:
                    rows = None
                    time.sleep(2 + 3 * attempt)
            if rows is None:
                raise RuntimeError(f"{sym} {a}..{b}: 5-minute history unavailable")
            for c in rows:
                dt = datetime.fromisoformat(c["time"]).astimezone(IST)
                days.setdefault(dt.date().isoformat(), []).append(
                    {"m": dt.hour * 60 + dt.minute, "o": c["open"], "h": c["high"], "l": c["low"], "c": c["close"], "v": c["volume"]})
            a = b + timedelta(days=1)
    for d in days:
        days[d].sort(key=lambda x: x["m"])
        seen = set()
        days[d] = [x for x in days[d] if not (x["m"] in seen or seen.add(x["m"]))]
    json.dump({**days, "_from": start.isoformat(), "_to": end.isoformat()}, open(path, "w"), separators=(",", ":"))
    return days


# ───────────────────────── trade walker ─────────────────────────
def walk(candles, side, entry, stop, targets, mode, cost=COST):
    """candles: [{o,h,l,c}] after the entry. mode 'split' (half at targets[0], stop to entry, rest at targets[1]) or 'all' (everything at targets[0]).
    Returns (R, why, n_candles_used) with the last candle's close as the time exit."""
    d = 1 if side == "BUY" else -1
    risk = d * (entry - stop)
    if risk <= 0 or entry <= 0 or not candles:
        return None
    cost_r = cost * entry / risk
    half, locked, cur = False, 0.0, stop
    for n, b in enumerate(candles, 1):
        if (d > 0 and b["l"] <= cur) or (d < 0 and b["h"] >= cur):
            gap = (d > 0 and b["o"] <= cur) or (d < 0 and b["o"] >= cur)
            px = b["o"] if gap else cur
            r = d * (px - entry) / risk
            return (locked + (0.5 * r if half else r) - cost_r, "SL" if (not half or r < 0) else "T", n)
        if mode == "all":
            if (d > 0 and b["h"] >= targets[0]) or (d < 0 and b["l"] <= targets[0]):
                return (d * (targets[0] - entry) / risk - cost_r, "T", n)
        else:
            if not half and ((d > 0 and b["h"] >= targets[0]) or (d < 0 and b["l"] <= targets[0])):
                half, locked, cur = True, 0.5 * d * (targets[0] - entry) / risk, entry
            if half and ((d > 0 and b["h"] >= targets[1]) or (d < 0 and b["l"] <= targets[1])):
                return (locked + 0.5 * d * (targets[1] - entry) / risk - cost_r, "T", n)
    r = d * (candles[-1]["c"] - entry) / risk
    return (locked + (0.5 * r if half else r) - cost_r, "TIME", len(candles))


def stats(Rs, whys=None):
    n = len(Rs)
    if not n:
        return {"n": 0, "winRate": 0.0, "avgR": 0.0, "pf": 0.0, "sumR": 0.0, "maxDD_R": 0.0, "targetHit": 0.0, "stopped": 0.0}
    w = [r for r in Rs if r > 0]
    gl = -sum(r for r in Rs if r < 0)
    cum = pk = dd = 0.0
    for r in Rs:
        cum += r
        pk = max(pk, cum)
        dd = max(dd, pk - cum)
    out = {"n": n, "winRate": round(len(w) / n, 3), "avgR": round(sum(Rs) / n, 3), "pf": round(sum(w) / gl, 2) if gl > 0 else (99.0 if w else 0.0),
           "sumR": round(sum(Rs), 1), "maxDD_R": round(dd, 1)}
    if whys is not None:
        out["targetHit"] = round(sum(1 for x in whys if x == "T") / n, 3)
        out["stopped"] = round(sum(1 for x in whys if x == "SL") / n, 3)
    return out


def wilson(w, n, z=1.96):
    import math
    if not n:
        return [0, 0]
    p = w / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(max(0, c - h), 3), round(min(1, c + h), 3)]


# ───────────────────────── building the picks as the screen would show them ─────────────────────────
def _rows_before(bars, i, extra=None):
    """Daily rows for _pick: the last ~90 calendar days up to bars[i-1] (+ today's partial bar)."""
    d0 = (date.fromisoformat(bars[i]["date"]) - timedelta(days=90)).isoformat()
    j = i
    while j > 0 and bars[j - 1]["date"] >= d0:
        j -= 1
    rows = bars[j:i]
    return rows + [extra] if extra else rows


def build_morning(sym, bars, idx, m5, sector):
    """Yield (date, pick, ctx) for every session with 5-minute data: the pick the screen would show at 09:30."""
    import market_api
    for d, cs in m5.items():
        i = idx.get(d)
        if i is None or i < 60 or i + 1 >= len(bars):
            continue
        early = [c for c in cs if c["m"] < DECIDE_MIN]
        rest = [c for c in cs if DECIDE_MIN <= c["m"] <= SQUARE_OFF + 4]
        if len(early) < max(1, (DECIDE_MIN - (9 * 60 + 15)) // 5) or not rest or early[0]["m"] != 9 * 60 + 15:
            continue
        op, hi, lo, ltp = early[0]["o"], max(c["h"] for c in early), min(c["l"] for c in early), early[-1]["c"]
        vol = sum(c["v"] for c in early)
        part = {"date": d, "open": op, "high": hi, "low": lo, "close": ltp, "volume": vol}
        q = {"last_price": ltp, "ohlc": {"open": op, "high": hi, "low": lo}, "prev_close_price": bars[i - 1]["close"], "volume": vol}
        try:
            p = market_api._pick(sym, q, _rows_before(bars, i, part))
        except Exception:
            continue
        if not p:
            continue
        p["kind"], p["sec"] = "stock", sector
        yield d, p, {"rest": rest, "i": i}


def build_overnight(sym, bars, sector):
    """Yield (date, pick, ctx) for every session: the pick the Picks screen shows at that day's close."""
    import market_api
    for i in range(60, len(bars) - HOLD - 2):
        b = bars[i]
        q = {"last_price": b["close"], "ohlc": {"open": b["open"], "high": b["high"], "low": b["low"]}, "prev_close_price": bars[i - 1]["close"], "volume": b.get("volume") or 0}
        try:
            p = market_api._pick(sym, q, _rows_before(bars, i + 1))      # the 90 calendar days up to and including bar i
        except Exception:
            continue
        if not p:
            continue
        p["open"] = 0.0               # Open = Low / High is a live, intraday read: not used in the overnight list
        p["kind"], p["sec"] = "stock", sector
        yield b["date"], p, {"i": i}


# ───────────────────────── trades ─────────────────────────
def trade_morning(p, ctx, bars, side, entry_px):
    """(swing R, why, intraday R, why) for a morning entry at the 09:35 open."""
    rest, i = ctx["rest"], ctx["i"]
    after = [c for c in rest if c["m"] >= DECIDE_MIN + 5]
    if not after:
        return None
    entry = after[0]["o"]
    out = {}
    # swing: today's 5-minute candles from the entry, then the next sessions' daily candles (max HOLD sessions in all)
    risk = mp.swing_risk(p, side)
    d = 1 if side == "BUY" else -1
    stop, t1, t2 = entry - d * risk, entry + d * 1.5 * risk, entry + d * 2.5 * risk
    day = [{"o": c["o"], "h": c["h"], "l": c["l"], "c": c["c"]} for c in after]
    nxt = [{"o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"]} for b in bars[i + 1:i + HOLD]]
    if len(nxt) < HOLD - 1:
        return None
    out["swing"] = walk(day + nxt, side, entry, stop, [t1, t2], "split")
    # intraday: stop beyond today's extreme, 1R / 2R, flat at 15:15
    ri = mp.intraday_risk(p, side)
    stop, t1, t2 = entry - d * ri, entry + d * ri, entry + d * 2 * ri
    intra = [{"o": c["o"], "h": c["h"], "l": c["l"], "c": c["c"]} for c in after if c["m"] < SQUARE_OFF]
    out["intraday"] = walk(intra, side, entry, stop, [t2], "all") if intra else None
    out["intraday1"] = walk(intra, side, entry, stop, [t1], "all") if intra else None
    return out


def trade_overnight(p, ctx, bars, side):
    i = ctx["i"]
    entry = bars[i + 1]["open"]
    if entry <= 0:
        return None
    risk = mp.swing_risk(p, side)
    d = 1 if side == "BUY" else -1
    stop, t1, t2 = entry - d * risk, entry + d * 1.5 * risk, entry + d * 2.5 * risk
    seq = [{"o": b["open"], "h": b["high"], "l": b["low"], "c": b["close"]} for b in bars[i + 1:i + 1 + HOLD]]
    if len(seq) < HOLD:
        return None
    return {"swing": walk(seq, side, entry, stop, [t1, t2], "split")}


# ───────────────────────── portfolio ─────────────────────────
def day_lists(day_picks):
    """{date: {'all': [...], 'short': [...]}}: every Picks BUY/SELL idea vs the shortlist."""
    out = {}
    for d, plist in day_picks.items():
        base = [p for p in plist if p.get("signal") in ("BUY", "SELL") and (p.get("strength") or 0) >= mp.FILL_STRENGTH_MIN]
        out[d] = {"all": base, "short": mp.select(plist)}
    return out


def block(trades, key):
    """stats of the R list for a trade-record list, for exit `key`."""
    T = [t[key] for t in trades if t.get(key)]
    return stats([r for r, _w, _n in T], [w for _r, w, _n in T])


def report(label, trades, split, per_day):
    """trades: [{date, side, tier, both, group('all'|'short'), swing, intraday...}]."""
    res = {"label": label, "days": len(per_day), "avgTradesPerDay": 0, "groups": {}}
    sel = [t for t in trades if t["group"] == "short"]
    res["avgTradesPerDay"] = round(len(sel) / max(1, len(per_day)), 1)
    keys = [k for k in ("swing", "intraday", "intraday1") if any(t.get(k) for t in trades)]
    cuts = {"all picks (no priority, strength >= 50)": lambda t: t["group"] == "all",
            "SHORTLIST (10-15)": lambda t: t["group"] == "short",
            "  tier 1: strength >= 75 + good R:R": lambda t: t["group"] == "short" and t["tier"] == 1,
            "  tier 1 + Open=Low/High agrees": lambda t: t["group"] == "short" and t["tier"] == 1 and t["both"],
            "  tier 2: Open=Low BUY / Open=High SELL": lambda t: t["group"] == "short" and t["tier"] == 2,
            "  tier 3: fill-up": lambda t: t["group"] == "short" and t["tier"] == 3,
            "  shortlist BUY": lambda t: t["group"] == "short" and t["side"] == "BUY",
            "  shortlist SELL": lambda t: t["group"] == "short" and t["side"] == "SELL"}
    for name, f in cuts.items():
        sub = [t for t in trades if f(t)]
        g = {}
        for k in keys:
            g[k] = {"all": block(sub, k), "inSample": block([t for t in sub if t["date"] <= split], k), "outOfSample": block([t for t in sub if t["date"] > split], k)}
            n_all = g[k]["all"]["n"]
            g[k]["all"]["ci95"] = wilson(round(g[k]["all"]["winRate"] * n_all), n_all)
        res["groups"][name] = g
    return res


def run(n_stocks=100, months=13, progress=print):
    import bar_source
    import market_api
    from upstox_service import background
    t0 = time.time()
    market_api.ensure_universe()
    universe = [s for s, _n, _sec in market_api.STOCKS]
    sector = {s: sec for s, _n, sec in market_api.STOCKS}
    daily = {}
    with background():
        for s in universe:
            try:
                b = bar_source.daily_bars(s, 1700)
                if len(b) > 300:
                    daily[s] = b
            except Exception:
                pass
    progress(f"daily history: {len(daily)} F&O stocks")
    # the N most liquid by recent traded value
    liq = sorted(daily, key=lambda s: -sum(b["close"] * (b.get("volume") or 0) for b in daily[s][-60:]))
    live = liq[:n_stocks]

    # ---- OVERNIGHT: every F&O stock, whole history
    over = {}
    for n, s in enumerate(daily):
        idx_ = {b["date"]: i for i, b in enumerate(daily[s])}
        for d, p, ctx in build_overnight(s, daily[s], sector.get(s, "")):
            over.setdefault(d, []).append((s, p, ctx))
        if n % 40 == 0:
            progress(f"overnight picks {n}/{len(daily)}")
    over_trades, per_day_o = [], {}
    for d in sorted(over):
        plist = [dict(p, s=s) for s, p, _c in over[d]]
        ctx_of = {s: c for s, _p, c in over[d]}
        lists = day_lists({d: plist})[d]
        per_day_o[d] = len(lists["short"])
        for grp in ("all", "short"):
            for p in lists[grp]:
                side = p["side"] if grp == "short" else p["signal"]
                tr = trade_overnight(p, ctx_of[p["s"]], daily[p["s"]], side)
                if not tr or not tr.get("swing"):
                    continue
                over_trades.append({"date": d, "sym": p["s"], "side": side, "group": grp, "tier": p.get("tier", 0), "both": p.get("both", False), **tr})
    dates_o = sorted({t["date"] for t in over_trades})
    split_o = dates_o[int(len(dates_o) * 0.7)]
    progress(f"overnight: {len(over_trades)} trades, {len(dates_o)} days, split {split_o}")

    # ---- MORNING: liquid stocks, last `months` months of 5-minute candles
    morn = {}
    skipped = 0
    for n, s in enumerate(live):
        try:
            m5 = load_5m(s, months)
        except Exception as e:
            skipped += 1
            progress(f"  {s}: {str(e)[:80]}")
            continue
        idx_ = {b["date"]: i for i, b in enumerate(daily[s])}
        for d, p, ctx in build_morning(s, daily[s], idx_, m5, sector.get(s, "")):
            morn.setdefault(d, []).append((s, p, ctx))
        if n % 10 == 0:
            progress(f"morning picks {n}/{len(live)} ({time.time() - t0:.0f}s)")
    morn_trades, per_day_m = [], {}
    for d in sorted(morn):
        plist = [dict(p, s=s) for s, p, _c in morn[d]]
        ctx_of = {s: c for s, _p, c in morn[d]}
        lists = day_lists({d: plist})[d]
        per_day_m[d] = len(lists["short"])
        for grp in ("all", "short"):
            for p in lists[grp]:
                side = p["side"] if grp == "short" else p["signal"]
                tr = trade_morning(p, ctx_of[p["s"]], daily[p["s"]], side, None)
                if not tr or not tr.get("swing"):
                    continue
                morn_trades.append({"date": d, "sym": p["s"], "side": side, "group": grp, "tier": p.get("tier", 0), "both": p.get("both", False), **tr})
    dates_m = sorted({t["date"] for t in morn_trades})
    split_m = dates_m[int(len(dates_m) * 0.7)] if dates_m else ""
    progress(f"morning: {len(morn_trades)} trades, {len(dates_m)} days, split {split_m}, skipped {skipped}")
    return {"generatedAt": datetime.now(IST).isoformat(), "stocksMorning": len(live), "stocksOvernight": len(daily),
            "overnight": {**report("overnight", over_trades, split_o, per_day_o), "from": dates_o[0], "to": dates_o[-1], "split": split_o},
            "morning": {**report("morning", morn_trades, split_m, per_day_m), "from": dates_m[0] if dates_m else "", "to": dates_m[-1] if dates_m else "", "split": split_m},
            "perDayShortlist": {"overnight": round(sum(per_day_o.values()) / max(1, len(per_day_o)), 1), "morning": round(sum(per_day_m.values()) / max(1, len(per_day_m)), 1)},
            "tookSeconds": round(time.time() - t0, 1)}


def _pct(x):
    return f"{x * 100:.0f}%"


def to_markdown(r):
    L = ["# Morning shortlist - backtest (strength >= 75 first, Open = Low / High second, 10-15 trades)",
         f"_Generated {r['generatedAt'][:16].replace('T', ' ')} IST. Paper research, not advice. Underlying price with a stop-loss and targets on every trade, 0.1% round-trip cost; "
         "a candle touching both stop and target counts as the stop. Out-of-sample = the last 30% of the days, which no rule was tuned on._", "",
         f"Shortlist rule (morning_picks.py): tier 1 = strength >= 75 and good risk/reward (stop <= {mp.MAX_RISK_PCT:g}% of price and >= {mp.MIN_ROOM_R:g}R of room to the last 20 sessions' high/low), "
         "tier 1 that is also Open = Low (BUY) / Open = High (SELL) first; tier 2 = Open = Low BUY / Open = High SELL with good risk/reward; tier 3 = fill-up (strength >= 50) only to reach 10; at most 15, at most 4 per sector.", ""]
    for key, title, exits in (("morning", "A. MORNING replay (what the live screen shows at 09:30, entry 09:35) - 5-minute candles", (("swing", "SWING: pick's own stop, half at 1.5R, rest at 2.5R, up to 10 sessions"), ("intraday", "INTRADAY: stop beyond today's extreme, 2R target, flat 15:15"), ("intraday1", "INTRADAY: same stop, 1R target"))),
                              ("overnight", "B. OVERNIGHT replay (evening list, entered next open) - daily candles, long history", (("swing", "SWING: pick's own stop, half at 1.5R, rest at 2.5R, up to 10 sessions"),))):
        s = r[key]
        L += [f"## {title}", f"_{s['from']} → {s['to']} · {s['days']} sessions · shortlist averaged {s['avgTradesPerDay']} trades a day · out-of-sample from {s['split']}_", ""]
        for ek, en in exits:
            L += [f"### {en}", "", "| Group | Trades | Win rate (95% range) | Target hit | Stopped | Avg R | PF | Out-of-sample: trades · win · avg R · PF |", "|---|---:|---|---:|---:|---:|---:|---|"]
            for name, g in s["groups"].items():
                x = g.get(ek)
                if not x or not x["all"]["n"]:
                    continue
                a, o = x["all"], x["outOfSample"]
                L.append(f"| {name} | {a['n']} | {_pct(a['winRate'])} ({_pct(a['ci95'][0])}-{_pct(a['ci95'][1])}) | {_pct(a['targetHit'])} | {_pct(a['stopped'])} | {a['avgR']:+.2f} | {a['pf']} | {o['n']} · {_pct(o['winRate'])} · {o['avgR']:+.2f} · {o['pf']} |")
            L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    m = int(sys.argv[2]) if len(sys.argv) > 2 else 13
    rep = run(n, m, progress=lambda x: print(x, flush=True))
    os.makedirs(os.path.join(HERE, "docs"), exist_ok=True)
    out_json = os.path.join(HERE, ".cache", "morning_backtest.json")
    json.dump(rep, open(out_json, "w"), separators=(",", ":"))
    open(os.path.join(HERE, "docs", "MORNING_PICKS_ACCURACY.md"), "w", encoding="utf-8").write(to_markdown(rep))
    print("done", rep["tookSeconds"], "s")
