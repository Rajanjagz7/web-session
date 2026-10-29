"""Strategy backtester + 2-month earnings estimate (paper trading only).

What it does
  1. Replays every daily-bar strategy "as of" several past dates (so ~3 years of signals, not just the last 1.5),
     for 5 indices and the most liquid F&O stocks.
  2. Simulates each fresh signal on daily candles with one fixed rule set:
        entry next session's open, signal-candle stop capped at 12.5% of the option premium, target 2R,
        max hold 10 sessions, estimated option time decay per session, round-trip cost 0.05%.
     A candle that touches both stop and target is treated as a stop (conservative).
  3. Splits the history: the first 70% of trades is IN-SAMPLE (used to decide which strategies "work"),
     the last 30% is OUT-OF-SAMPLE (used only to judge them).
  4. Replays the daily executor (no daily limit: every qualifying signal, best proven strategy first, one position per symbol) over the
     out-of-sample period and reports rolling 2-month results at the BRD risk budget (0.5% of Rs 10,00,000 = Rs 5,000/trade).

Honest limits (also returned to the UI): it is run on the UNDERLYING's daily candles, not on option premiums
(historical option candles for expired contracts are not available), options add theta/gamma/spread effects,
and past results do not guarantee future results.
"""
import json
import os
import threading
import time
from datetime import date, datetime, timedelta, timezone

import shared_cache

IST = timezone(timedelta(hours=5, minutes=30))
HERE = os.path.dirname(__file__)
STATIC_DIR = os.path.join(HERE, "public", "static") if os.path.exists(os.path.join(HERE, "public", "static")) else os.path.join(HERE, "static")
OUT_FILE = os.path.join(STATIC_DIR, "backtest_result.json")   # local-dev fallback only - read-only on Vercel
CACHE_KEY = "backtest_result_v2"          # v2: option-premium stop (30% cap), theta, kept indicators only
CACHE_TTL = 48 * 3600   # Vercel runs several instances with their own /tmp and a read-only static/ -
                        # shared_cache (Upstash) is what actually makes a fresh run visible to every instance

INDEX_SYMS = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"]
STOCK_SYMS = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK", "LT",
              "AXISBANK", "BAJFINANCE", "MARUTI", "SUNPHARMA", "TITAN", "HCLTECH", "TATASTEEL", "M&M", "ADANIENT", "ONGC"]
ASOF_OFFSETS = [0, 380, 760, 1140]          # calendar days back; each replay yields ~1.5y of signals
RISK_RS = 5000.0                            # BRD default: 0.5% of Rs 10,00,000
ATR_N, TARGET_R, MAX_HOLD, COST = 14, 2.0, 10, 0.0005
# Option-buyer stop (same rule in auto_trader.py). The stop is the indicator's signal candle: just beyond the low (BUY) or
# high (SELL) of the signal bar and the bar before it, kept between 0.5 and 1.0 ATR - but never more than PREM_SL of the
# option premium (at delta 0.5). Without that cap a 1.5 ATR stop let one ATM option lose ~90% of its premium.
# PREM_SL is 12.5% = auto_trader.PREM_SL_PCT, the cap the live trader uses since 28 Oct (it was 30% here, so the backtest tested wider
# stops than the ones actually traded). test_backtest_matches_live.py fails if the two ever differ again.
PREM_SL, DELTA, SWING_BUF, MIN_ATR, MAX_ATR = 0.125, 0.5, 0.1, 0.5, 1.0
DTE_EST = {"index": 5, "stock": 15}        # fallback only - theta now follows the real expiry calendar (expiry_for)
MIN_DTE = 3                                 # the live trader buys the nearest expiry at least 3 days away
SKIP_KEYS = {"vix-range", "volume-buzzer-15m", "volume-buzzer-daily", "potential-breakout"}   # not directional entries

_tl = threading.local()          # the as-of replay must only affect the backtest thread
_state = {"running": False, "progress": "", "result": None, "started": 0.0, "error": None, "cleared": False}
_lock = threading.Lock()


def norm_signal(v):
    s = str(v or "").upper()
    if not s or s in ("NONE", "NR7", "COMPRESSING", "BREAKOUT", "RANGE", "FLAT", "NEUTRAL", "WAIT", "NO SIGNAL"):
        return None
    if "ABOVE" in s or s.startswith(("BUY", "LONG", "BULL")) or s in ("BOTTOM", "MOMENTUM", "CANDIDATE", "UPTREND"):
        return "BUY"
    if "BELOW" in s or s.startswith(("SELL", "SHORT", "BEAR")) or s == "DOWNTREND":
        return "SELL"
    return None


def _runners(include_hidden=False):
    import donchian
    import rajan_pavan_indicators as rp
    import trade_predictor
    import ut_bot
    import strategies_api

    out = {}
    for k, fn in rp.RAJAN_PAVAN_KEYS.items():
        if k not in SKIP_KEYS and (include_hidden or k not in strategies_api.HIDDEN):
            out[k] = (lambda sym, lb, fn=fn: fn(sym, lookback_days=lb))
    out["ut-bot"] = lambda sym, lb: ut_bot.ut_bot_scan(sym, lookback_days=lb)
    out["trade-predictor"] = lambda sym, lb: trade_predictor.trade_predictor_scan(sym, lookback_days=lb)
    out["donchian"] = lambda sym, lb: donchian.donchian_scan(sym, lookback_days=lb)
    out["supertrend-mtf"] = lambda sym, lb: strategies_api._raw_supertrend_mtf(sym)
    import rajan_new_indicators as newind
    for k, fn in newind.NEW_KEYS.items():                # daily-bar Rajan strategies (they give their own stop)
        out[k] = (lambda sym, lb, fn=fn: fn(sym, lookback_days=max(lb, 250)))
    import rzt as rzt_mod
    out["rzt"] = lambda sym, lb: rzt_mod.rzt_scan(sym, lookback_days=lb)   # Rajan Zone Trend (Z Trend): flip + line stop
    # quantum-matrix, ha-dancing-trend, volume-spurt, orb-15m and vwap-rsi run on 1-minute bars: years of
    # 1-minute history are not available, so they cannot be replayed here.
    return {k: v for k, v in out.items() if include_hidden or k not in strategies_api.HIDDEN}      # default: only the indicators kept on the site


def _atr(bars, n=ATR_N):
    from ut_bot import _rma, _true_range
    return _rma(_true_range(bars), n)


def est_premium(atr_v, kind, days=None):
    """ATM option premium estimate: 0.4 x sigma x S x sqrt(trading days left), daily sigma x S ~= 0.8 x ATR.
    days = CALENDAR days to expiry (converted at 5 trading days per 7); None -> typical DTE for the kind."""
    td = DTE_EST.get(kind, 5) if days is None else max(0.0, days) * 5 / 7
    return 0.32 * atr_v * (td ** 0.5)


def expiry_for(day_iso, kind):
    """The contract the live trader would buy on this day: nearest expiry at least MIN_DTE days away.
    Index options: weekly (Thursday until Aug 2025, Tuesday from Sep 2025). Stock options: monthly, last such weekday.
    Exchange holidays that move an expiry by a day are ignored (an approximation)."""
    d0 = date.fromisoformat(day_iso)
    wd = 3 if d0 < date(2025, 9, 1) else 1
    if kind == "index":
        e = d0 + timedelta(days=(wd - d0.weekday()) % 7)
        while (e - d0).days < MIN_DTE:
            e += timedelta(days=7)
        return e
    y, m = d0.year, d0.month
    while True:
        nxt = date(y + (m == 12), m % 12 + 1, 1)
        wdm = 3 if nxt - timedelta(days=1) < date(2025, 9, 1) else 1
        e = nxt - timedelta(days=1)
        while e.weekday() != wdm:
            e -= timedelta(days=1)
        if (e - d0).days >= MIN_DTE:
            return e
        y, m = nxt.year, nxt.month


def plan_risk(bars, atr_v, i, side, entry, premium, delta=DELTA, ind_stop=None):
    """Underlying stop distance for a signal on bar i. The indicator's own stop when it gives one (Rajan Trend Rider,
    HA Momentum, Breakout Trap, OH/OL, Gann Sq9), otherwise the signal candle; either way never more than PREM_SL of
    the option premium (see PREM_SL above)."""
    d = 1 if side == "BUY" else -1
    own = d * (entry - ind_stop) if ind_stop else None
    if own is not None and own > 0.2 * atr_v:
        risk = own
    else:
        lo = min(b["low"] for b in bars[max(0, i - 1):i + 1])
        hi = max(b["high"] for b in bars[max(0, i - 1):i + 1])
        swing = d * (entry - (lo if d > 0 else hi)) + SWING_BUF * atr_v
        risk = min(max(swing, MIN_ATR * atr_v), MAX_ATR * atr_v)
    return min(risk, PREM_SL * premium / max(delta, 0.05))


def theta_r(atr_v, kind, risk, d_from, d_to):
    """Time decay in R between two moments, from the real days-to-expiry on each date: premium(days) falls with
    sqrt(days), so the daily loss is small a week out and steep in the last sessions."""
    return (est_premium(atr_v, kind, d_from) - est_premium(atr_v, kind, d_to)) / DELTA / risk


VARIANTS = ("fixed", "trail", "reverse")      # exit styles tried for every strategy
FILTERS = ("none", "trend200")                 # optional: only trade with the 200-day EMA trend
TRAIL_HOLD = 10      # options cannot be held for 40 sessions


def simulate(bars, atr, i, side, variant="fixed", opp_i=None, kind="index", ind_stop=None, target_r=None):
    """Signal on bar i's close -> enter bar i+1 open. Returns (R, exit_index, reason) or None while still open.
    Stop for every variant: plan_risk() (signal-candle stop, capped at PREM_SL of the option premium).
    fixed   : target 2R (or target_r), max 10 sessions
    trail   : the stop trails the best price by the same distance, no target, max 10 sessions
    reverse : exit at the open after the strategy's opposite signal, max 10 sessions
    Every session held costs the option's estimated time decay (theta_r)."""
    if i + 1 >= len(bars) or atr[i] is None or atr[i] <= 0:
        return None
    tr_ = target_r or TARGET_R
    d = 1 if side == "BUY" else -1
    entry = bars[i + 1]["open"]
    if not entry or entry <= 0:
        return None
    exp = expiry_for(bars[i + 1]["date"], kind)
    dte = lambda j, frac: (exp - date.fromisoformat(bars[j]["date"])).days + frac   # frac: part of that day still to run
    d_entry = dte(i + 1, 0.26)                                                       # entry at 09:15, expiry at 15:30
    risk = plan_risk(bars, atr[i], i, side, entry, est_premium(atr[i], kind, d_entry), ind_stop=ind_stop)
    if risk <= 0:
        return None
    if variant == "fixed":
        stop, target, hold = entry - d * risk, entry + d * tr_ * risk, MAX_HOLD
    else:
        stop, target, hold = entry - d * risk, None, TRAIL_HOLD
    last = min(len(bars) - 1, i + hold)
    best = entry
    cost_r = COST * entry / risk

    def out(r, j, why, when="mid"):
        frac = {"open": 0.26, "mid": 0.13, "close": 0.0}[when]                       # intraday exits: ~3 h before close
        th = theta_r(atr[i], kind, risk, d_entry, dte(j, frac))
        return (r - cost_r - th, j, why)     # gaps through the stop are kept (they happen to options too)
    for j in range(i + 1, last + 1):
        b = bars[j]
        if j > i + 1:
            if (d > 0 and b["open"] <= stop) or (d < 0 and b["open"] >= stop):
                return out(d * (b["open"] - entry) / risk, j, "SL", "open")
            if variant == "reverse" and opp_i is not None and j == opp_i + 1:
                return out(d * (b["open"] - entry) / risk, j, "REV", "open")
        hit_stop = b["low"] <= stop if d > 0 else b["high"] >= stop
        if hit_stop:
            return out(d * (stop - entry) / risk, j, "SL")
        if target is not None and (b["high"] >= target if d > 0 else b["low"] <= target):
            return out(tr_, j, "T")
        if dte(j, 0.0) <= 1:                                                         # live rule: out one day before expiry
            return out(d * (b["close"] - entry) / risk, j, "EXP", "close")
        if variant == "trail":
            best = max(best, b["high"]) if d > 0 else min(best, b["low"])
            stop = max(stop, best - risk) if d > 0 else min(stop, best + risk)
    if last == len(bars) - 1 and last < i + hold:
        return None
    return out(d * (bars[last]["close"] - entry) / risk, last, "TIME", "close")


def _hold_days(T):
    """Calendar days from entry to exit, from the backtest's own simulated trades - not a guess."""
    ds = sorted(d for d in ((date.fromisoformat(t["exit"]) - date.fromisoformat(t["entry"])).days for t in T) if d >= 0)
    if not ds:
        return {"avg": 0, "median": 0, "n": 0}
    return {"avg": round(sum(ds) / len(ds), 1), "median": ds[len(ds) // 2], "n": len(ds)}


def _stats(Rs):
    n = len(Rs)
    if not n:
        return {"n": 0, "winRate": 0, "avgR": 0, "pf": 0, "maxDD_R": 0, "sumR": 0}
    w = [r for r in Rs if r > 0]
    l = [-r for r in Rs if r < 0]
    cum = pk = dd = 0.0
    for r in Rs:
        cum += r
        pk = max(pk, cum)
        dd = max(dd, pk - cum)
    gl = sum(l)
    return {"n": n, "winRate": round(len(w) / n, 3), "avgR": round(sum(Rs) / n, 3),
            "pf": round(sum(w) / gl, 2) if gl > 0 else (99.0 if w else 0), "maxDD_R": round(dd, 2), "sumR": round(sum(Rs), 2)}


def collect_signals(runners, syms, full, progress=None, orig_daily=None):
    """Replay every runner "as of" several past dates and return ({(key, sym): {date: BUY/SELL}}, {(key, sym): {date: own stop}})."""
    import bar_source
    orig_daily = orig_daily or bar_source.daily_bars
    cur = {"asof": None}

    _tl.on = True

    def replay(symbol, lookback_days=180):
        bars = full.get(symbol.upper())
        if bars is None or not getattr(_tl, "on", False):
            return orig_daily(symbol, lookback_days)
        cut = cur["asof"].isoformat()
        lo = (cur["asof"] - timedelta(days=int(lookback_days))).isoformat()
        return [b for b in bars if lo <= b["date"] <= cut]

    signals = {}        # (key, sym) -> {date: BUY/SELL}
    istops = {}         # (key, sym) -> {date: the indicator's own stop, when it gives one}
    total = len(runners) * len(syms) * len(ASOF_OFFSETS)
    done = 0
    t_start = time.time()
    bar_source.daily_bars = replay
    try:
        for off in ASOF_OFFSETS:
            cur["asof"] = date.today() - timedelta(days=off)
            for key, fn in runners.items():
                for s in syms:
                    done += 1
                    if progress and (done % 10 == 0 or done == total):
                        pct = int((done / total) * 100)
                        el = max(0.1, time.time() - t_start)
                        rate = done / el
                        rem_s = max(0, int((total - done) / rate)) if rate > 0 else 0
                        progress({
                            "pct": pct,
                            "done": done,
                            "total": total,
                            "elapsed": int(el),
                            "eta": rem_s,
                            "msg": f"{pct}% ({done}/{total} combinations) · ~{rem_s}s remaining"
                        })
                    try:
                        r = fn(s, 400)
                        rows = r.get("bars") or []
                    except Exception:
                        continue
                    prev = None
                    m = signals.setdefault((key, s), {})
                    ms = istops.setdefault((key, s), {})
                    for row in rows:
                        sg = norm_signal(row.get("signal"))
                        d = row.get("date")
                        if sg and d and sg != prev:     # only the first bar of a run is a new entry
                            m.setdefault(d, sg)
                            if row.get("stop"):
                                ms.setdefault(d, row["stop"])
                        prev = sg
    finally:
        _tl.on = False
        bar_source.daily_bars = orig_daily
    return signals, istops


def run_backtest(progress=None, only=None):
    import bar_source
    import market_api
    market_api.ensure_universe()
    runners = _runners()
    if only:
        keep = {k for k in only if k in runners}
        if not keep:
            raise ValueError("no matching strategy in the filter")
        runners = {k: v for k, v in runners.items() if k in keep}
    syms = INDEX_SYMS + [s for s in STOCK_SYMS if bar_source.supports(s)]
    t0 = time.time()
    orig_daily = bar_source.daily_bars
    full = {}
    for s in syms:
        try:
            b = orig_daily(s, 1700)
            if len(b) > 260:
                full[s] = b
        except Exception:
            pass
    syms = [s for s in syms if s in full]
    atr = {s: _atr(full[s]) for s in syms}
    idx_of = {s: {b["date"]: i for i, b in enumerate(full[s])} for s in syms}

    signals, istops = collect_signals(runners, syms, full, progress, orig_daily)

    # ---- simulate every signal under every exit style / trend filter ----
    ema200 = {}
    for sym in syms:
        c = [bb["close"] for bb in full[sym]]
        k, e, out = 2 / 201, None, []
        for v in c:
            e = v if e is None else v * k + e * (1 - k)
            out.append(e)
        ema200[sym] = out
    trades = []
    for (key, s_), m in signals.items():
        bars, ix = full[s_], idx_of[s_]
        order = sorted(m)
        for variant in VARIANTS:
            for flt in FILTERS:
                busy_until = -1
                for n_, d in enumerate(order):
                    i = ix.get(d)
                    if i is None or i <= busy_until:
                        continue
                    side = m[d]
                    if flt == "trend200":
                        if i < 200 or (side == "BUY") != (bars[i]["close"] > ema200[s_][i]):
                            continue
                    opp_i = None
                    if variant == "reverse":
                        for d2 in order[n_ + 1:]:
                            if m[d2] != side:
                                opp_i = ix.get(d2)
                                break
                    res = simulate(bars, atr[s_], i, side, variant, opp_i, "index" if s_ in INDEX_SYMS else "stock",
                                   istops.get((key, s_), {}).get(d))
                    if not res:
                        continue
                    R, j, why = res
                    busy_until = j
                    trades.append({"key": key, "sym": s_, "kind": "index" if s_ in INDEX_SYMS else "stock", "side": side,
                                   "variant": variant, "filter": flt, "entry": bars[i + 1]["date"], "exit": bars[j]["date"],
                                   "R": round(R, 3), "why": why})
    if not trades:
        raise RuntimeError("No simulated trades — historical data is unavailable right now.")
    base = [t for t in trades if t["variant"] == "fixed" and t["filter"] == "none"]
    dates = sorted(t["entry"] for t in base)
    split = dates[int(len(dates) * 0.7)]
    months = max(1.0, (date.fromisoformat(dates[-1]) - date.fromisoformat(dates[0])).days / 30.4)
    MIN_IS, IS_R, IS_PF, MIN_OOS, OOS_R, OOS_PF = 40, 0.12, 1.25, 20, 0.08, 1.15

    ranking = []
    for key in sorted({t["key"] for t in trades}):
        cfgs = []
        for variant in VARIANTS:
            for flt in FILTERS:
                T = [t for t in trades if t["key"] == key and t["variant"] == variant and t["filter"] == flt]
                is_ = [t["R"] for t in T if t["entry"] <= split]
                oos = [t["R"] for t in T if t["entry"] > split]
                cfgs.append({"variant": variant, "filter": flt, "all": _stats([t["R"] for t in T]),
                             "inSample": _stats(is_), "outOfSample": _stats(oos)})
        elig = [c for c in cfgs if c["inSample"]["n"] >= MIN_IS]
        chosen = max(elig, key=lambda c: c["inSample"]["avgR"]) if elig else max(cfgs, key=lambda c: c["inSample"]["n"])
        i_, o, a_ = chosen["inSample"], chosen["outOfSample"], chosen["all"]
        proven = (i_["n"] >= MIN_IS and o["n"] >= MIN_OOS and i_["avgR"] >= IS_R and i_["pf"] >= IS_PF
                  and o["avgR"] >= OOS_R and o["pf"] >= OOS_PF)
        why = "" if proven else ("too few trades" if i_["n"] < MIN_IS or o["n"] < MIN_OOS else
                                 "no profitable setup in-sample" if i_["avgR"] < IS_R or i_["pf"] < IS_PF else
                                 "did not hold up out-of-sample")
        T0 = [t for t in trades if t["key"] == key and t["variant"] == chosen["variant"] and t["filter"] == chosen["filter"]]
        ranking.append({"key": key, "variant": chosen["variant"], "filter": chosen["filter"], "all": a_, "inSample": i_,
                        "outOfSample": o, "tradesPerMonth": round(a_["n"] / months, 1), "proven": proven, "reason": why,
                        "holdDays": _hold_days(T0),
                        "index": _stats([t["R"] for t in T0 if t["kind"] == "index"]),
                        "stock": _stats([t["R"] for t in T0 if t["kind"] == "stock"]), "configs": cfgs,
                        "perSymbol": {sy: {"all": _stats([t["R"] for t in T0 if t["sym"] == sy]),
                                           "oos": _stats([t["R"] for t in T0 if t["sym"] == sy and t["entry"] > split])}
                                      for sy in syms}})
    ranking.sort(key=lambda r: (not r["proven"], -r["inSample"]["avgR"]))
    proven_keys = [r["key"] for r in ranking if r["proven"]]
    chosen_cfg = {r["key"]: (r["variant"], r["filter"]) for r in ranking}
    score = {r["key"]: r["inSample"]["avgR"] for r in ranking}      # ranked on in-sample only: no peeking
    research_keys = [r["key"] for r in sorted(ranking, key=lambda r: -r["inSample"]["avgR"]) if r["inSample"]["n"] >= MIN_IS][:3]

    def replay(keys):
        by_day = {}
        for t in trades:
            if t["key"] in keys and (t["variant"], t["filter"]) == chosen_cfg[t["key"]] and t["entry"] > split:
                by_day.setdefault(t["entry"], []).append(t)
        picked, open_pos = [], []
        for d in sorted(by_day):
            open_pos = [p for p in open_pos if p["exit"] >= d]
            taken = {p["sym"] for p in open_pos}
            for t in sorted(by_day[d], key=lambda x: -score.get(x["key"], 0)):
                if t["sym"] in taken:                            # no daily limit any more: one position per symbol is the only rule
                    continue
                taken.add(t["sym"])
                open_pos.append(t)
                picked.append(t)
        daily_pnl = {}
        for t in picked:
            daily_pnl[t["exit"]] = daily_pnl.get(t["exit"], 0.0) + t["R"] * RISK_RS
        equity, cum, peak, dd = [], 0.0, 0.0, 0.0
        for d in sorted(daily_pnl):
            cum += daily_pnl[d]
            peak = max(peak, cum)
            dd = max(dd, peak - cum)
            equity.append({"date": d, "cum": round(cum, 0)})
        cal = sorted({b["date"] for b in full[INDEX_SYMS[0]] if b["date"] > split})
        windows = []
        for k in range(0, max(0, len(cal) - 42) + 1, 5):
            lo, hi = cal[k], cal[min(k + 41, len(cal) - 1)]
            windows.append(sum(v for d, v in daily_pnl.items() if lo <= d <= hi))
        wins = sorted(windows)
        q = lambda p: wins[min(len(wins) - 1, int(p * (len(wins) - 1)))] if wins else 0
        return {
            "strategies": keys, "from": split, "to": dates[-1], "entries": len(picked),
            "stats": _stats([t["R"] for t in picked]), "netPnL": round(sum(t["R"] for t in picked) * RISK_RS, 0),
            "maxDrawdown": round(dd, 0),
            "twoMonth": {"windows": len(windows), "median": round(q(0.5), 0), "p10": round(q(0.1), 0), "p90": round(q(0.9), 0),
                         "worst": round(min(windows), 0) if windows else 0, "best": round(max(windows), 0) if windows else 0,
                         "profitableShare": round(sum(1 for w in windows if w > 0) / len(windows), 2) if windows else 0},
            "equity": equity[-250:],
        }

    ex_proven = replay(proven_keys) if proven_keys else None
    ex_research = replay(research_keys) if research_keys else None
    return {
        "generatedAt": datetime.now(IST).isoformat(), "symbols": syms, "strategiesTested": len(ranking),
        "tradesSimulated": len(trades), "historyFrom": dates[0], "historyTo": dates[-1], "splitDate": split,
        "rules": {"entry": "next session open", "exitStyles": {
                      "fixed": f"signal-candle stop ({MIN_ATR}-{MAX_ATR} ATR, max {PREM_SL * 100:g}% of premium), target {TARGET_R}R, max {MAX_HOLD} sessions, theta from the real days to expiry, out 1 day before expiry",
                      "trail": f"same stop trailing the best price, max {TRAIL_HOLD} sessions, daily theta, out 1 day before expiry",
                      "reverse": f"same stop, exit on the opposite signal, max {TRAIL_HOLD} sessions, daily theta, out 1 day before expiry"},
                  "filters": {"none": "no filter", "trend200": "only with the 200-day EMA trend"},
                  "roundTripCost": f"{COST * 100:.2f}%", "riskPerTrade": RISK_RS, "tieBreak": "stop wins a same-candle tie",
                  "provenIf": f"in-sample n>={MIN_IS}, avgR>={IS_R}, PF>={IS_PF}; out-of-sample n>={MIN_OOS}, avgR>={OOS_R}, PF>={OOS_PF}"},
        "ranking": ranking, "provenKeys": proven_keys, "researchKeys": research_keys, "chosen": chosen_cfg,
        "executor": ex_proven, "executorResearch": ex_research,
        "caveats": [
            "Run on the underlying's daily candles - not on option premiums (expired option candles are unavailable).",
            "Options add theta, gamma, wider spreads and slippage; real option results can differ materially.",
            "Each strategy's exit style / trend filter was picked on the first 70% of trades and judged on the last 30%.",
            "Testing 6 configurations per strategy raises the chance of a lucky pass; treat a 'proven' tag as weak evidence.",
            "Past performance does not guarantee future results. Paper trading only.",
        ],
        "tookSeconds": round(time.time() - t0, 1),
        "filteredKeys": sorted(only) if only else [],
    }


def _worker():
    try:
        r = run_backtest(progress=lambda m: _state.__setitem__("progress", m))
        with _lock:
            _state["result"], _state["error"] = r, None
        try:
            shared_cache.set(CACHE_KEY, r, CACHE_TTL)
        except Exception:
            pass
        try:
            with open(OUT_FILE, "w", encoding="utf-8") as f:
                json.dump(r, f)
        except Exception:
            pass
    except Exception as e:
        _state["error"] = str(e)[:300]
    finally:
        _state["running"] = False
        _state["progress"] = ""


# filtered runs ("only these strategies") live in their own state + store so a custom run can
# never replace the FULL result that drives the auto trader's proven / research selection
CACHE_KEY_CUSTOM = "backtest_result_custom_v1"
OUT_FILE_CUSTOM = os.path.join(STATIC_DIR, "backtest_custom.json")
_custom = {"running": False, "progress": "", "result": None, "error": None, "started": 0.0, "cleared": False}


def _worker_custom(only):
    try:
        r = run_backtest(progress=lambda m: _custom.__setitem__("progress", m), only=only)
        r["filteredKeys"] = sorted(only)
        _custom["result"], _custom["error"] = r, None
        try:
            shared_cache.set(CACHE_KEY_CUSTOM, r, CACHE_TTL)
        except Exception:
            pass
        try:
            with open(OUT_FILE_CUSTOM, "w", encoding="utf-8") as f:
                json.dump(r, f)
        except Exception:
            pass
    except Exception as e:
        _custom["error"] = str(e)[:300]
    finally:
        _custom["running"] = False
        _custom["progress"] = ""


def start_custom(only):
    with _lock:
        if _custom["running"]:
            return False
        _custom.update(running=True, started=time.time(), error=None, progress="starting", result=None, cleared=False)
    threading.Thread(target=_worker_custom, args=(sorted(set(only)),), daemon=True, name="backtest-custom").start()
    return True


def custom_get():
    if _custom.get("cleared"):
        return {"running": False, "progress": "", "pct": 0, "eta": 0, "error": None, "elapsed": 0, "result": None, "cleared": True}
    if _custom["result"] is None:
        try:
            _custom["result"] = shared_cache.get(CACHE_KEY_CUSTOM)
        except Exception:
            pass
    if _custom["result"] is None:
        try:
            with open(OUT_FILE_CUSTOM, encoding="utf-8") as f:
                _custom["result"] = json.load(f)
        except Exception:
            pass
    prog = _custom["progress"]
    prog_str = prog if isinstance(prog, str) else (prog.get("msg") if isinstance(prog, dict) else "")
    prog_pct = prog.get("pct", 0) if isinstance(prog, dict) else (100 if _custom["result"] else 0)
    eta = prog.get("eta", 0) if isinstance(prog, dict) else 0
    return {"running": _custom["running"], "progress": prog_str, "pct": prog_pct, "eta": eta, "error": _custom["error"],
            "elapsed": round(time.time() - _custom["started"], 0) if _custom["running"] else 0,
            "result": _custom["result"], "cleared": False}


def start(force=False):
    with _lock:
        if _state["running"]:
            return False
        if not force and _state["result"] is not None and not _state.get("cleared"):
            return False
        _state.update(running=True, started=time.time(), error=None, progress="starting", cleared=False)
        try:
            shared_cache.set("bt:cleared", None, 1)
        except Exception:
            pass
    threading.Thread(target=_worker, daemon=True, name="backtest").start()
    return True


def get():
    if _state.get("cleared") or shared_cache.get("bt:cleared"):
        return {"running": False, "progress": "", "pct": 0, "eta": 0, "error": None, "elapsed": 0, "result": None, "cleared": True}
    if _state["result"] is None:
        try:
            _state["result"] = shared_cache.get(CACHE_KEY)
        except Exception:
            pass
    if _state["result"] is None:
        try:
            with open(OUT_FILE, encoding="utf-8") as f:
                _state["result"] = json.load(f)
        except Exception:
            pass
    prog = _state["progress"]
    prog_str = prog if isinstance(prog, str) else (prog.get("msg") if isinstance(prog, dict) else "")
    prog_pct = prog.get("pct", 0) if isinstance(prog, dict) else (100 if _state["result"] else 0)
    eta = prog.get("eta", 0) if isinstance(prog, dict) else 0
    return {"running": _state["running"], "progress": prog_str, "pct": prog_pct, "eta": eta, "error": _state["error"],
            "elapsed": round(time.time() - _state["started"], 0) if _state["running"] else 0,
            "result": _state["result"], "cleared": False}


def proven_scores():
    """{strategy key: in-sample avg R} for strategies that passed - used by the executor."""
    r = get()["result"]
    if not r:
        return {}
    return {x["key"]: x["inSample"]["avgR"] for x in r["ranking"] if x["proven"]}


# ───────────────────────── API ─────────────────────────
from fastapi import APIRouter, HTTPException  # noqa: E402

router = APIRouter(prefix="/api/backtest")


@router.get("")
def api_get():
    return get()


@router.post("/run")
def api_run(force: bool = True, only: str = ""):
    keys = [k.strip() for k in only.split(",") if k.strip()] if only else None
    if keys:
        return {"started": start_custom(keys), **{k: v for k, v in custom_get().items() if k != "result"}}
    return {"started": start(force=force), **{k: v for k, v in get().items() if k != "result"}}


@router.post("/reset")
def api_reset():
    """Journal 'Reset': drop the stored full result (shared store + local file) so nothing is shown until a fresh run."""
    with _lock:
        _state["result"] = None
        _state["cleared"] = True
        _state["running"] = False
        _state["progress"] = ""
        _custom["result"] = None
        _custom["cleared"] = True
        _custom["running"] = False
        _custom["progress"] = ""
    try:
        shared_cache.set(CACHE_KEY, None, 1)
        shared_cache.set(CACHE_KEY_CUSTOM, None, 1)
        shared_cache.set("bt:cleared", True, 86400)
    except Exception:
        pass
    try:
        if os.path.exists(OUT_FILE):
            os.remove(OUT_FILE)
    except Exception:
        pass
    try:
        if os.path.exists(OUT_FILE_CUSTOM):
            os.remove(OUT_FILE_CUSTOM)
    except Exception:
        pass
    return {"ok": True, "reset": True}


@router.get("/custom")
def api_custom():
    return custom_get()

@router.get("/accuracy")
def api_accuracy(full: bool = False):
    """Accuracy of every indicator and of the Picks screen with stop-loss and target (see accuracy_report.py).
    Default: a compact summary; ?full=true adds every exit rule, long/short, index/stock and per-year split."""
    path = os.path.join(STATIC_DIR, "accuracy_report.json")
    try:
        with open(path, encoding="utf-8") as f:
            rep = json.load(f)
    except Exception:
        raise HTTPException(404, "No accuracy report yet - run: python accuracy_report.py")
    if full:
        return rep
    out = {k: rep[k] for k in ("generatedAt", "history", "splitDate", "notReplayable", "caveats") if k in rep}
    out["symbols"] = len(rep.get("symbols") or [])
    out["indicators"] = [{"key": e["key"], "name": e["name"], "group": e["group"], "visible": e["visible"], "signals": e["signals"],
                          "directional": e["directional"],
                          "models": {m: {k: v[k] for k in ("best", "verdict", "bestAll", "bestOOS")} for m, v in e["models"].items()}}
                         for e in rep.get("indicators", [])]
    p_ = rep.get("picks")
    if p_:
        out["picks"] = {k: p_[k] for k in ("symbols", "from", "to", "splitDate", "trades", "rules")}
        out["picks"]["variants"] = [{k: v[k] for k in ("entryAt", "exit", "all", "outOfSample", "buy", "sell")} for v in p_["variants"]]
    return out
