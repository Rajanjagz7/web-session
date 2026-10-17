"""Strategy backtester + 2-month earnings estimate (paper trading only).

What it does
  1. Replays every daily-bar strategy "as of" several past dates (so ~3 years of signals, not just the last 1.5),
     for 5 indices and the most liquid F&O stocks.
  2. Simulates each fresh signal on daily candles with one fixed rule set:
        entry next session's open, stop 1.5 x ATR(14), target 2R, max hold 10 sessions, round-trip cost 0.05%.
     A candle that touches both stop and target is treated as a stop (conservative).
  3. Splits the history: the first 70% of trades is IN-SAMPLE (used to decide which strategies "work"),
     the last 30% is OUT-OF-SAMPLE (used only to judge them).
  4. Replays the daily executor (max 5 entries a day: 3 index + 2 stock, best proven strategy first) over the
     out-of-sample period and reports rolling 2-month results at the BRD risk budget (0.5% of Rs 10,00,000 = Rs 5,000/trade).

Honest limits (also returned to the UI): it is run on the UNDERLYING's daily candles, not on option premiums
(historical option candles for expired contracts are not available), options add theta/gamma/spread effects,
and past results do not guarantee future results.
"""
import json
import os
import statistics
import threading
import time
from datetime import date, datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
HERE = os.path.dirname(__file__)
OUT_FILE = os.path.join(HERE, "static", "backtest_result.json")   # bundled with the deploy, so the live site can read it

INDEX_SYMS = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"]
STOCK_SYMS = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK", "LT",
              "AXISBANK", "BAJFINANCE", "MARUTI", "SUNPHARMA", "TITAN", "HCLTECH", "TATASTEEL", "M&M", "ADANIENT", "ONGC"]
ASOF_OFFSETS = [0, 380, 760, 1140]          # calendar days back; each replay yields ~1.5y of signals
RISK_RS = 5000.0                            # BRD default: 0.5% of Rs 10,00,000
ATR_N, STOP_ATR, TARGET_R, MAX_HOLD, COST = 14, 1.5, 2.0, 10, 0.0005
SKIP_KEYS = {"vix-range", "volume-buzzer-15m", "volume-buzzer-daily", "potential-breakout"}   # not directional entries

_tl = threading.local()          # the as-of replay must only affect the backtest thread
_state = {"running": False, "progress": "", "result": None, "started": 0.0, "error": None}
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


def _runners():
    import donchian
    import rajan_pavan_indicators as rp
    import trade_predictor
    import ut_bot
    import strategies_api

    out = {}
    for k, fn in rp.RAJAN_PAVAN_KEYS.items():
        if k not in SKIP_KEYS:
            out[k] = (lambda sym, lb, fn=fn: fn(sym, lookback_days=lb))
    out["ut-bot"] = lambda sym, lb: ut_bot.ut_bot_scan(sym, lookback_days=lb)
    out["trade-predictor"] = lambda sym, lb: trade_predictor.trade_predictor_scan(sym, lookback_days=lb)
    out["donchian"] = lambda sym, lb: donchian.donchian_scan(sym, lookback_days=lb)
    out["supertrend-mtf"] = lambda sym, lb: strategies_api._raw_supertrend_mtf(sym)
    return out


def _atr(bars, n=ATR_N):
    from ut_bot import _rma, _true_range
    return _rma(_true_range(bars), n)


VARIANTS = ("fixed", "trail", "reverse")      # exit styles tried for every strategy
FILTERS = ("none", "trend200")                 # optional: only trade with the 200-day EMA trend
TRAIL_ATR, TRAIL_HOLD = 2.0, 40


def simulate(bars, atr, i, side, variant="fixed", opp_i=None):
    """Signal on bar i's close -> enter bar i+1 open. Returns (R, exit_index, reason) or None while still open.
    fixed   : stop 1.5 ATR, target 2R, max 10 sessions
    trail   : stop 2 ATR trailing the best price since entry, no target, max 40 sessions
    reverse : stop 2 ATR, exit at the open after the strategy's opposite signal, max 40 sessions"""
    if i + 1 >= len(bars) or atr[i] is None or atr[i] <= 0:
        return None
    d = 1 if side == "BUY" else -1
    entry = bars[i + 1]["open"]
    if not entry or entry <= 0:
        return None
    if variant == "fixed":
        risk = STOP_ATR * atr[i]
        stop, target, hold = entry - d * risk, entry + d * TARGET_R * risk, MAX_HOLD
    else:
        risk = TRAIL_ATR * atr[i]
        stop, target, hold = entry - d * risk, None, TRAIL_HOLD
    last = min(len(bars) - 1, i + hold)
    best = entry
    cost_r = COST * entry / risk
    for j in range(i + 1, last + 1):
        b = bars[j]
        if j > i + 1:
            if (d > 0 and b["open"] <= stop) or (d < 0 and b["open"] >= stop):
                return (d * (b["open"] - entry) / risk - cost_r, j, "SL")
            if variant == "reverse" and opp_i is not None and j == opp_i + 1:
                return (d * (b["open"] - entry) / risk - cost_r, j, "REV")
        hit_stop = b["low"] <= stop if d > 0 else b["high"] >= stop
        if hit_stop:
            return (d * (stop - entry) / risk - cost_r, j, "SL")
        if target is not None and (b["high"] >= target if d > 0 else b["low"] <= target):
            return (TARGET_R - cost_r, j, "T")
        if variant == "trail":
            best = max(best, b["high"]) if d > 0 else min(best, b["low"])
            stop = max(stop, best - risk) if d > 0 else min(stop, best + risk)
    if last == len(bars) - 1 and last < i + hold:
        return None
    return (d * (bars[last]["close"] - entry) / risk - cost_r, last, "TIME")


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


def run_backtest(progress=None):
    import bar_source
    import market_api
    market_api.ensure_universe()
    runners = _runners()
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
    total = len(runners) * len(syms) * len(ASOF_OFFSETS)
    done = 0
    bar_source.daily_bars = replay
    try:
        for off in ASOF_OFFSETS:
            cur["asof"] = date.today() - timedelta(days=off)
            for key, fn in runners.items():
                for s in syms:
                    done += 1
                    if progress and done % 25 == 0:
                        progress(f"replaying strategies {done}/{total}")
                    try:
                        r = fn(s, 400)
                        rows = r.get("bars") or []
                    except Exception:
                        continue
                    prev = None
                    m = signals.setdefault((key, s), {})
                    for row in rows:
                        sg = norm_signal(row.get("signal"))
                        d = row.get("date")
                        if sg and d and sg != prev:     # only the first bar of a run is a new entry
                            m.setdefault(d, sg)
                        prev = sg
    finally:
        _tl.on = False
        bar_source.daily_bars = orig_daily

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
                    res = simulate(bars, atr[s_], i, side, variant, opp_i)
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
            slots = {"index": 3, "stock": 2}
            for t in sorted(by_day[d], key=lambda x: -score.get(x["key"], 0)):
                if slots[t["kind"]] <= 0 or t["sym"] in taken or len(open_pos) >= 5:
                    continue
                slots[t["kind"]] -= 1
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
                      "fixed": f"stop {STOP_ATR} x ATR({ATR_N}), target {TARGET_R}R, max {MAX_HOLD} sessions",
                      "trail": f"stop {TRAIL_ATR} x ATR trailing the best price, max {TRAIL_HOLD} sessions",
                      "reverse": f"stop {TRAIL_ATR} x ATR, exit on the opposite signal, max {TRAIL_HOLD} sessions"},
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
    }


def _worker():
    try:
        r = run_backtest(progress=lambda m: _state.__setitem__("progress", m))
        with _lock:
            _state["result"], _state["error"] = r, None
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


def start(force=False):
    with _lock:
        if _state["running"]:
            return False
        if not force and _state["result"] is not None:
            return False
        _state.update(running=True, started=time.time(), error=None, progress="starting")
    threading.Thread(target=_worker, daemon=True, name="backtest").start()
    return True


def get():
    if _state["result"] is None:
        try:
            with open(OUT_FILE, encoding="utf-8") as f:
                _state["result"] = json.load(f)
        except Exception:
            pass
    return {"running": _state["running"], "progress": _state["progress"], "error": _state["error"],
            "elapsed": round(time.time() - _state["started"], 0) if _state["running"] else 0,
            "result": _state["result"]}


def proven_scores():
    """{strategy key: in-sample avg R} for strategies that passed - used by the executor."""
    r = get()["result"]
    if not r:
        return {}
    return {x["key"]: x["inSample"]["avgR"] for x in r["ranking"] if x["proven"]}


# ───────────────────────── API ─────────────────────────
from fastapi import APIRouter  # noqa: E402

router = APIRouter(prefix="/api/backtest")


@router.get("")
def api_get():
    return get()


@router.post("/run")
def api_run(force: bool = True):
    return {"started": start(force=force), **{k: v for k, v in get().items() if k != "result"}}
