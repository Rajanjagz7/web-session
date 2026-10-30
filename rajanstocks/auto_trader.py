"""Automated PAPER executor: no daily entry limit (it used to stop at 5: 3 index + 2 stock options) - every qualifying signal is taken,
one position per symbol at a time, each sized at the same fixed risk.

No broker is involved and no real order is ever sent. Trades are simulated at live option prices.

Rules (identical to the backtest in backtest.py, so results are comparable):
  * Only strategies that PASSED the out-of-sample backtest are used, ranked by in-sample average R.
  * Signal = the fresh BUY/SELL on the last COMPLETED daily bar, acted on from 09:16 (the first full minute after the open).
  * BUY -> ATM call, SELL -> ATM put, nearest expiry that is at least 3 days away.
  * Risk per trade = 1.0% of its sleeve's equity (0.5% until 28 Oct 11:16); lots = floor(budget / (lot x 0.5 delta x stop distance)), minimum 1.
  * Stop = the indicator's signal candle (beyond its low/high, 0.5-1.0 ATR) but never more than 12.5% of the option
    premium (backtest.plan_risk). Exit when the underlying hits that stop OR the option bid falls 12.5% below entry,
    target ladder 1.5R 2R 3R 4R 5R 6R 10R (stop trails one target behind; 10R closes), 10 sessions, or one day before expiry. There is no intraday square-off: option trades are held across sessions (the "squareOff" config value is not used).
  * Stock picks are chosen automatically: proven-strategy signal agreeing with the stock's screen score.
"""
import json
import math
import os
import threading
import time
from datetime import date, datetime, timedelta, timezone

import requests
import shared_cache
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

IST = timezone(timedelta(hours=5, minutes=30))
router = APIRouter(prefix="/api/auto")
_lock = threading.Lock()

KEY = "rajanone:auto:v1"
FILE = os.path.join(os.environ.get("BHAV_CACHE_WRITE_DIR") or os.path.dirname(__file__), "auto_state.json")
NO_LIMIT = 10 ** 6                      # "maxPerDay", "indexSlots", "stockSlots": 0 (or empty) means no limit


def _cap(cfg, key):
    v = cfg.get(key)
    return NO_LIMIT if not v else int(v)


PLAN_V = 202610282     # one-time switch (28 Oct 2026): Rs 10 L option buying (stock options + index, calls and puts) in three sleeves, the Rs 5 L share trader on
IDX_V = 20261028       # one-time: index options are bought too (not only stock options) - stockOnly stays a setting that can be turned back on
SLEEVES = {"picks": 400000.0, "eagle": 200000.0, "signals": 400000.0, "old": 500000.0}      # Rs 10 L of option buying for the NEW IND sources + Rs 5 L for the OLD FILT filter (30 Oct); the cash share trader has its own Rs 5 L
SLEEVE_NAMES = {"picks": "Today's Picks", "eagle": "Eagle Trades", "signals": "Indicator signals", "old": "OLD FILT"}
STOP_GAP_TOL = 0.02                      # a premium stop fills AT the stop unless the price seen is more than this far beyond it (a gap / fast move between two cycles): then it fills at that price
MAX_SPREAD_OF_STOP = 0.8                 # an option is only bought when its bid/ask spread is at most this share of the premium stop (12.5% stop -> 10% spread, same limit as _contract; 0.4 blocked every opening-minute entry)
SCAN_RETRIES = 3                         # a symbol whose indicator run failed is retried this many times (cycles) before it is closed for the day
PREM_SL_PCT = 0.125                      # option premium stop: at most this share of the premium (30% until 28 Oct, 20% for a few hours, then 12.5%)
MAX_OUTLAY = {"BANKNIFTY": 15000.0}     # most one trade may spend on premium, per symbol (user, 28 Oct: Bank Nifty options 10-15k max) - a dearer ATM strike moves to the nearest OTM one that fits
TARGET_LADDER = (1.5, 2, 3, 4, 5, 6, 10)    # targets in R (user, 28 Oct): the stop trails one target behind, the last one closes the trade
SL_V = 1                                 # one-time: premium stop 12.5% + risk per trade 1.0% (bigger trades) from 28 Oct 11:16
DEFAULT_CFG = {"enabled": True, "capital": 1000000.0, "buyOnly": True, "stockOnly": False, "idxV": IDX_V, "stockTrader": True, "sleeves": dict(SLEEVES), "planV": PLAN_V, "riskPct": 1.0, "maxOutlay": dict(MAX_OUTLAY), "premSlPct": PREM_SL_PCT, "slV": SL_V, "maxPerDay": 0, "indexSlots": 0, "stockSlots": 0, "limitRemoved": True,
               "windowStart": "09:16", "lastEntry": "14:30", "squareOff": "15:15", "minDaysToExpiry": 3,
               "maxHoldSessions": 10, "openBurstCap": 12, "costPct": 0.1, "researchMode": True, "dayPnlLimit": 45000.0, "zTrendHedge": False, "pairSell": False,
               "lockMode": "old", "eagleOn": True, "eagleV": 1, "classicOnly": True, "classicV": 1}
MIN_AGREE_STOCK = 2                      # user 29 Oct: a STOCK option trade needs at least 2 indicators pointing the same way ...
INDEX_MIN_AGREE = 2                      # 30 Oct (user): an index option trade needs 2+ indicators pointing the same way (the call/put screen + its backing points + other strategies on that index)
INDEX_MAX_PER_DAY = 3                    # 30 Oct (user): at most 3 trades a day in any one index OR stock option (was 5) - the best ranked (risk/reward + indicators) go first, so wins and losses come from 2-3 trades, not a stream of them
SOLO_STRENGTH = 75.0                     # ... unless a single signal comes with Picks strength >= 75 (100 ranks first). Index trades are not affected.
SELL_FROM = 9 * 60 + 20                  # option SELL legs (the paired shorts) only from 09:20 - buys start at windowStart (09:16)
# Vercel kills a function at 30 s and the state is only saved at the end of a cycle: at the open (30+ entries, each with its own option
# quotes) a cycle ran out of time and NOTHING was kept. A cycle now opens trades for at most this long, saves, and the next cycle
# (1-2 minutes later) takes the rest - best-ranked first.
CYCLE_BUDGET = 18.0 if os.environ.get("VERCEL") else 10 ** 9
PERSIST_KEYS = ("shadow", "skipUntil", "dayGuardMode", "idxWhy", "carry", "cleared")      # book keys beyond trades / log / cfg that must survive from one cycle to the next
CARRY_FOR = 540          # screen candidates not tried in their own cycle are offered again for 9 minutes (3 screens)
FILL_EVERY = 180          # index / stock screens are re-read every 3 minutes (10 missed short-lived signals)
MIN_INDEX_RR = 1.5        # index call / put screen: reward to target 1 must be >= 1.5x the stop distance
SOFT_ZONE = 0.75                         # past 75% of the day P&L limit only high-conviction entries are taken
INDEX_SYMS = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX"]


# ───────────────────────── state ─────────────────────────
def _remote():
    import shared_cache                                   # one place decides the URL+token pair (never mixed)
    return shared_cache._creds()


_RC = {}
_ver_of = shared_cache.ver_of
_strip_ver = shared_cache.strip_ver


def _read_ver():
    return shared_cache.read_ver(KEY)


def _load(cached=False, verify=False):
    st = {"cfg": dict(DEFAULT_CFG), "trades": [], "log": []}
    try:
        r = _remote()
        if r:
            raw = shared_cache.cached_raw(KEY, _RC, 60.0, verify) if cached else None     # a short local copy saves store requests; verify=True checks the stored version first
            if raw is None:
                j = shared_cache.kv([["GET", KEY]], 8.0)[0]                # primary, or the backup database
                if j.get("error"):                                  # store refused (e.g. request limit): never treat as "empty"
                    raise RuntimeError(f"state store error: {j['error']}")
                raw = j.get("result")
                _RC.update(t=time.time(), raw=raw)
            d = json.loads(raw) if raw else {}
            st["_ver0"] = _ver_of(raw)                              # the version this copy was read at (checked again when it is saved)
        else:
            with open(FILE, encoding="utf-8") as f:
                d = json.load(f)
        saved = d.get("cfg") or {}
        st["cfg"].update(saved)
        if saved.get("pairV") != 1:                            # one-time: paired option SELL leg off (buy-only); the settings API can turn it back on
            st["cfg"].update(pairSell=False, pairV=1)
            st["_dirty"] = True
        if saved and saved.get("planV") != PLAN_V:              # one-time: Rs 10 L option buying in three sleeves + the Rs 5 L share trader on
            st["cfg"].update(capital=1000000.0, buyOnly=True, stockTrader=True, sleeves=dict(SLEEVES), pairSell=False, zTrendHedge=False, planV=PLAN_V)
            st["_dirty"] = True
        if saved.get("idxV") != IDX_V:                          # one-time: index options are bought as well as stock options
            st["cfg"].update(stockOnly=False, idxV=IDX_V)
            st["_dirty"] = True
        if saved and saved.get("slV") != SL_V:                  # one-time (user, 28 Oct): 10-15% option stop and bigger trades; the settings API can change both later
            st["cfg"].update(premSlPct=PREM_SL_PCT, riskPct=1.0, slV=SL_V)
            st["_dirty"] = True
        if saved and saved.get("eagleV") != 1:                  # one-time (user, 28 Oct): Eagle Trades back ON - buy-only like everything else (call for Open = Low, put for Open = High); the Algo button / settings API can switch it off again
            st["cfg"].update(eagleOn=True, eagleV=1)
            st["_dirty"] = True
        if saved and saved.get("classicV") != 1:                # one-time (user, 28 Oct): auto trade ONLY the four classic entry types (1 / 2 indicators agree, stock screen, index call/put); Picks, Eagle, Gann angle, time cycle and Z Trend run as paper-only "shadow" signals for a week of testing
            st["cfg"].update(classicOnly=True, classicV=1)
            st["_dirty"] = True
        if saved and saved.get("splitV") != 1:                  # one-time (user, 30 Oct): OLD FILT trades in their own Rs 5 L sleeve, and every NEW IND source trades live (classic mode off) so the two filters can be compared
            st["cfg"].update(classicOnly=False, splitV=1, sleeves={**(saved.get("sleeves") or dict(SLEEVES)), "old": SLEEVES["old"]})
            st["_dirty"] = True
        if saved.get("dayLimitV") != 45000:                    # one-time: the day P&L break is Rs 45,000 (later changes through the settings API stay)
            st["cfg"].update(dayPnlLimit=45000.0, dayLimitV=45000)
            st["_dirty"] = True
        if saved and not saved.get("limitRemoved"):          # settings saved in the 5-a-day days: lift the cap once
            st["cfg"].update(maxPerDay=0, indexSlots=0, stockSlots=0, limitRemoved=True)
        st["trades"], st["log"] = d.get("trades") or [], d.get("log") or []
        from common import before_fresh_start, fresh_start_active
        old = [t for t in st["trades"] if before_fresh_start(t)] if fresh_start_active(_now()) else []
        if old:                                           # "remove all old entries, start from 0"
            _remember_cleared(st, old)                    # what was traded today is not bought straight back
            st["trades"] = [t for t in st["trades"] if not before_fresh_start(t)]
            st["cand"] = {}
            st["log"] = [{"at": _now().isoformat(), "msg": f"Fresh start: {len(old)} older paper trade(s) cleared - the book starts at zero"}]
            st["resetAt"] = _now().isoformat()
            st["_dirty"] = True
        import nse_calendar                               # trades "opened" on an exchange holiday used stale prices: void them
        bad = [t for t in st["trades"] if nse_calendar.holiday(t.get("date"))]
        if bad:
            st["trades"] = [t for t in st["trades"] if not nse_calendar.holiday(t.get("date"))]
            st["log"].append({"at": _now().isoformat(), "msg": f"Voided {len(bad)} paper trade(s) opened on an NSE holiday ({nse_calendar.holiday(bad[0]['date'])}) - prices were stale"})
            st["_dirty"] = True
        # Explicitly remove trade IDs 27, 1004, 1009 (dated: later trades reusing those numbers are kept)
        from common import is_removed_trade
        pre_cnt = len(st["trades"])
        st["trades"] = [t for t in st["trades"] if not is_removed_trade(t)]
        if len(st["trades"]) != pre_cnt:
            st["_dirty"] = True
        st["fillNext"], st["fillBackoff"] = d.get("fillNext") or 0, d.get("fillBackoff") or 0
        if d.get("resetAt"):
            st["resetAt"] = d["resetAt"]
        if d.get("cand"):
            st["cand"] = d["cand"]
        for k_ in PERSIST_KEYS:                                       # _save writes these but _load used to drop them: the skip cooldown, the paper-only signal log,
            if d.get(k_) is not None:                                  # the day-guard state and the carried screen candidates all restarted from empty every cycle
                st[k_] = d[k_]
        if st["cfg"].get("windowStart") in ("09:15", "09:20"):   # entries (buying) start at 09:16 - the first full minute after the open
            st["cfg"]["windowStart"] = "09:16"
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"[auto] state load failed: {e}")
        st["_readonly"] = True                                      # never save an empty state over the real trades
    return st


def _save(st):
    """True = saved (or nothing to save); "conflict" = somebody else saved the book after this copy was read, nothing was written
    (the caller reloads and redoes its change); False = the store refused the write."""
    if st.get("_readonly"):
        print("[auto] state was not read - not saving")
        return True
    st.pop("_dirty", None)
    st["log"] = st["log"][-120:]
    try:
        r = _remote()
        if r:
            rest = {k: v for k, v in st.items() if k not in ("ver", "_ver0")}
            res, info = shared_cache.versioned_set(KEY, rest, _RC, st.get("_ver0"))
            if res == "conflict":
                print("[auto] book changed since it was read - save skipped (conflict)")
                return "conflict"
            if res == "error":
                print(f"[auto] state save refused: {info}")
                return False
            if res == "ok":
                st["_ver0"] = info
            return True
        rest = {k: v for k, v in st.items() if k != "_ver0"}
        tmp = FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(rest, f)
        os.replace(tmp, FILE)
        return True
    except Exception as e:
        print(f"[auto] state save failed: {e}")
        return False


def _mutate(apply, tries=3):
    """Read-modify-write of the book for the user's own actions (exit, stop, TSL, settings, reset). Each action waits briefly for a running
    cycle, works on a fresh copy and, if another instance saved in between, is redone on the newest copy - so neither a manual action nor a
    cycle's trade can overwrite the other. apply(st) changes the book and returns the response."""
    for _ in range(8):
        if shared_cache.lock("auto-cycle", 2):
            break
        time.sleep(0.5)
    for attempt in range(tries):
        with _lock:
            st = _load()
            if st.get("_readonly"):
                raise HTTPException(503, "The book could not be read right now - try again in a moment")
            out = apply(st)
            res = _save(st)
        if res is True:
            return out
        if res is False:
            raise HTTPException(503, "The book could not be saved right now (the state store refused the write) - try again in a moment")
        time.sleep(0.25 * (attempt + 1))
    raise HTTPException(409, "The book changed while you were saving - nothing was lost, please try again")


def _now():
    return datetime.now(IST)


def _hm(s):
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def _mins(now):
    return now.hour * 60 + now.minute


def _equity(st):
    return st["cfg"]["capital"] + sum(t.get("net", 0.0) for t in st["trades"] if t["status"] == "CLOSED")


def _sleeve_of(c):
    """The sleeve an entry is sized and capped in. Every OLD FILT entry (the 22 Oct filter) has its own Rs 5 L; the NEW IND sources split into
    Picks / Eagle / Indicator signals. Takes the candidate (or just its key: a bare key is never OLD FILT)."""
    key = c.get("key") if isinstance(c, dict) else c
    if isinstance(c, dict) and filter_set(c) == "OLD FILT":
        return "old"
    return "picks" if key == "morning-pick" else "eagle" if key == "Eagle Trades" else "signals"


def _sleeve_equity(st, name):
    """The sleeve's start + what that sleeve has closed so far; None when sleeves are off (the old single-pool sizing then applies)."""
    base = (st["cfg"].get("sleeves") or {}).get(name)
    if not base:
        return None
    return float(base) + sum(t.get("net", 0.0) for t in st["trades"] if t["status"] == "CLOSED" and t.get("sleeve") == name)


def _sleeve_deployed(st, name):
    return sum(t["entry"] * t["lots"] * t["lot"] for t in st["trades"] if t["status"] == "OPEN" and t.get("sleeve") == name and t.get("pos") != "short")


def sleeve_report(st):
    out = []
    for name, label in SLEEVE_NAMES.items():
        eq = _sleeve_equity(st, name)
        if eq is None:
            continue
        mine = [t for t in st["trades"] if t.get("sleeve") == name]
        closed = [t for t in mine if t["status"] == "CLOSED"]
        opens = [t for t in mine if t["status"] == "OPEN"]
        wins = [t for t in closed if t.get("net", 0) > 0]
        out.append({"key": name, "name": label, "capital": float(st["cfg"]["sleeves"][name]), "equity": round(eq, 0),
                    "deployed": round(_sleeve_deployed(st, name), 0), "open": len(opens), "closed": len(closed),
                    "net": round(sum(t.get("net", 0.0) for t in closed), 0),
                    "openPnL": round(sum((_mk(t) - t["entry"]) * t["lots"] * t["lot"] for t in opens if t.get("pos") != "short"), 0),
                    "winRate": round(len(wins) / len(closed), 2) if closed else 0})
    return out


def _open_pnl(t):
    sgn = -1 if t.get("pos") == "short" else 1
    return (_mk(t) - t["entry"]) * t["lots"] * t["lot"] * sgn


def _day_base(t, today):
    """First look at a position on a trading day: remember its price then. Today's P&L is the move SINCE that price - the entry for a trade
    opened today, the previous mark for a carried one - not everything since the entry."""
    if t.get("baseDate") != today:
        t["baseDate"] = today
        t["basePx"] = round(float(t["entry"] if t.get("date") == today else (_mk(t) or t["entry"])), 2)


def _base_px(t, today):
    if t.get("baseDate") == today and t.get("basePx") is not None:
        return float(t["basePx"])
    if t.get("date") == today:
        return float(t["entry"])
    return _mk(t) if t["status"] == "OPEN" else None


def _day_part(t, today):
    """What one trade added to TODAY's P&L: closed today (by its EXIT day, not its entry day) or still open."""
    sgn = -1 if t.get("pos") == "short" else 1
    qty = (t.get("lots") or 0) * (t.get("lot") or 0)
    if t["status"] == "CLOSED":
        if str(t.get("closedAt") or t.get("date") or "")[:10] != today:
            return 0.0
        if t.get("date") == today:                           # opened today: its whole result belongs to today
            return float(t.get("net", 0.0))
        base = _base_px(t, today)
        if base is None:                                     # carried, and never marked today: its whole result is the best guess
            return float(t.get("net", 0.0))
        return (float(t.get("exit") or base) - base) * qty * sgn - float(t.get("cost", 0.0))
    return (_mk(t) - _base_px(t, today)) * qty * sgn


def _day_pnl(st, today):
    """Today's realised (trades closed today) + unrealised (open positions: the move since their price at the start of today)."""
    return sum(_day_part(t, today) for t in st["trades"])


def _day_guard(st, today):
    """The ±dayPnlLimit guard: past the limit no new trades at all (profit locks and trailing keep running);
    inside the 75% soft zone only high-conviction entries (3+ indicators agreeing, or a Z Trend flip) are taken.
    Returns (mode, note): mode is 'off' | 'soft' | 'blocked'."""
    limit = float(st["cfg"].get("dayPnlLimit") or 0)
    if limit <= 0:
        return "off", None
    day = _day_pnl(st, today)
    if day >= limit or day <= -limit:
        return "blocked", (f"Day P&L {'+' if day >= 0 else '−'}₹{abs(day):,.0f} crossed the ±₹{limit:,.0f} guard - "
                           f"no new trades today, existing positions keep their profit lock and trailing stop")
    if day >= limit * SOFT_ZONE or day <= -limit * SOFT_ZONE:
        return "soft", (f"Day P&L {'+' if day >= 0 else '−'}₹{abs(day):,.0f} is inside the soft zone "
                        f"(±₹{limit:,.0f} limit) - only 3-indicator confluence and Z Trend entries are taken")
    return "off", None


# ───────────────────────── market helpers ─────────────────────────
def _quotes(keys):
    from nse_service import nse_service
    return nse_service.upstox._full_quotes(list(keys))


def _last(q):
    return float((q or {}).get("last_price") or 0)


def _sessions_between(a, b):
    n, d = 0, date.fromisoformat(a)
    end = date.fromisoformat(b)
    while d < end:
        d += timedelta(days=1)
        if __import__("nse_calendar").is_trading_day(d):
            n += 1
    return n


# ───────────────────────── signal selection ─────────────────────────
FORWARD_TEST_EXTRA = ("rajan-rsi2-pullback",)   # unproven, added by hand (RSI(2) Pullback): runs once the backtest result contains it


def active_set(cfg):
    """({key: score}, {key: (variant, filter)}, label). Proven strategies first; if none passed the out-of-sample
    test and research mode is on, the top 3 in-sample configs are forward-tested and clearly labelled UNPROVEN."""
    import backtest
    r = backtest.get()["result"]
    if not r:
        return {}, {}, "waiting for the backtest"
    sc = {x["key"]: x["inSample"]["avgR"] for x in r["ranking"]}
    chosen = {k: tuple(v) for k, v in r["chosen"].items()}
    if r["provenKeys"]:
        return {k: sc[k] for k in r["provenKeys"]}, chosen, "proven"
    if cfg.get("researchMode") and r.get("researchKeys"):
        keys = list(r["researchKeys"]) + [k for k in FORWARD_TEST_EXTRA if k in sc and k not in r["researchKeys"]]   # hand-picked strategies forward-tested beside the top 3
        return {k: sc[k] for k in keys}, chosen, "unproven (forward test)"
    return {}, chosen, "no strategy passed the backtest and research mode is off"


def _trend_ok(sym, side, today):
    import bar_source
    bars = [b for b in bar_source.daily_bars(sym, 420) if b["date"] < today]
    if len(bars) < 200:
        return False
    k, e = 2 / 201, None
    for b in bars:
        e = b["close"] if e is None else b["close"] * k + e * (1 - k)
    return (side == "BUY") == (bars[-1]["close"] > e)


def candidates(today):
    """Fresh signals on the last completed daily bar from the active strategies (same logic the backtest used)."""
    import backtest
    import bar_source
    st0 = _load()
    scores, chosen, label = active_set(st0["cfg"])
    if not scores:
        return [], label
    runners = backtest._runners()
    syms = INDEX_SYMS + [s for s in backtest.STOCK_SYMS if bar_source.supports(s)]
    out, deadline = [], time.time() + (9 if os.environ.get("VERCEL") else 150)

    import concurrent.futures as cf

    def one(job):
        key, sym = job
        if time.time() > deadline:
            return None
        try:
            rows = runners[key](sym, 400).get("bars") or []
        except Exception:
            return None
        rows = [r for r in rows if r.get("date") and r["date"] < today]      # completed sessions only
        if len(rows) < 2:
            return None
        sg = backtest.norm_signal(rows[-1].get("signal"))
        prev = backtest.norm_signal(rows[-2].get("signal"))
        if not sg or sg == prev:
            return None
        variant, flt = chosen.get(key, ("fixed", "none"))
        if flt == "trend200" and not _trend_ok(sym, sg, today):
            return None
        return {"key": key, "sym": sym, "side": sg, "asOf": rows[-1]["date"], "score": scores[key], "indStop": rows[-1].get("stop"),
                "variant": variant, "filter": flt, "label": label, "kind": "index" if sym in INDEX_SYMS else "stock"}

    jobs = [(k, s) for s in syms for k in scores if k in runners]
    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        for r in ex.map(one, jobs):
            if r:
                out.append(r)
    return out, label



def _picks():
    """market_api.picks() with a shared 3-minute cool-down after a rate-limited failure: the Eagle scan and the screens asked
    for picks every cycle, and while Upstox was refusing (HTTP 429) each ask started a full ~200-quote rebuild - which kept
    the limit tripped for everyone (Trade screen quotes included)."""
    import market_api
    if shared_cache.get("auto:picks-backoff"):
        raise RuntimeError("picks paused for 3 min after an Upstox rate limit")
    try:
        return market_api.picks()
    except Exception as e:
        m = str(e).lower()
        if "429" in m or "rate" in m or "too many" in m:
            shared_cache.set("auto:picks-backoff", 1, 180)
        raise

INDEX_MEMBERS = {"NIFTY": "nifty50", "BANKNIFTY": "bank", "FINNIFTY": "finance", "SENSEX": "sensex", "MIDCPNIFTY": "midcap50"}


def _index_backing(c, side):
    """Index call/put confirmation (user, 29 Oct): (points 0-3, text). One point each for: the index's own strength >= 75%, the index option flow
    (the calls / puts share of volume near ATM) >= 75% on the trade's side, and at least 3 of the index's own stocks with a strength >= 75% signal
    the same way on the Picks list. Used to rank index entries - the more of them, the earlier the entry."""
    pts, bits = 0, []
    if (c.get("strength") or 0) >= 75:
        pts += 1
        bits.append(f"index strength {c['strength']:.0f}%")
    pct = c.get("callPct") if side == "BUY" else c.get("putPct")
    if (pct or 0) >= 75:
        pts += 1
        bits.append(f"option flow {pct:.0f}%")
    try:
        import stocks_api
        key = INDEX_MEMBERS.get(c.get("instrument"))
        if key:
            mem = {r["s"] for r in stocks_api._constituents(key)}
            n = sum(1 for p in _picks().get("picks", []) if p.get("s") in mem and p.get("signal") == side and (p.get("strength") or 0) >= 75)
            if n >= 3:
                pts += 1
                bits.append(f"{n} index stocks >= 75%")
    except Exception:
        pass
    return pts, bits


REENTRY_GAP_MIN = 0       # minutes after a trade closes before the same symbol can be entered again (user, 29 Oct: no restriction - a fresh signal re-enters at once)
INDEX_ONE_OPEN_PER_SIDE = True   # an index takes any number of trades a day, but not a second one in the same direction (CE / PE) while one is still open
BLOCK_SAME_CONTRACT = True    # an option contract (same strike / expiry / side) already traded today or still open is refused; any other strike of the same index or stock may be entered (user, 30 Oct)


def _remember_cleared(st, trades):
    """Symbols that were traded today before the user cleared the book. They are not entered again until tomorrow: an empty book forgot
    them and the next cycle (a minute later) bought the very same trades back."""
    today = _now().date().isoformat()
    cl = st.get("cleared") if isinstance(st.get("cleared"), dict) and st["cleared"].get("date") == today else {"date": today, "syms": []}
    syms = set(cl.get("syms") or [])
    for t in trades:
        if t.get("date") == today or t.get("status") == "OPEN" or str(t.get("closedAt") or "")[:10] == today:
            syms.add(t["sym"])
    st["cleared"] = {"date": today, "syms": sorted(syms)}


def _taken_syms(st, today, now=None):
    """Symbols that cannot get a new entry right now: one with an open trade (one position per symbol at a time), and - only if REENTRY_GAP_MIN
    is set - one whose trade (opened today) closed less than that many minutes ago. By default a closed symbol can be entered again at once
    on a fresh signal, in any option. A trade carried from an earlier day that closes today never blocks its symbol."""
    now = now or _now()
    out = set()
    cl = st.get("cleared")
    if isinstance(cl, dict) and cl.get("date") == today:
        out.update(x for x in (cl.get("syms") or []) if x not in INDEX_SYMS)   # traded today, then cleared by the user: no second entry today
    for t in st["trades"]:
        if t["status"] == "OPEN":
            continue                                     # 30 Oct (user): an index or stock may hold and re-enter any number of trades a day; only the identical option contract is refused (open_trade)
        if REENTRY_GAP_MIN > 0 and t.get("date") == today and t.get("closedAt"):
            try:
                if (now - datetime.fromisoformat(t["closedAt"])).total_seconds() < REENTRY_GAP_MIN * 60:
                    out.add(t["sym"])
            except Exception:
                out.add(t["sym"])
    return out


IDX_NOTE_EVERY = 900      # the "why no trade in this index" line is repeated at most every 15 minutes while the reason stays the same


def _idx_note(st, sym, text):
    """One Algo-log line per index saying WHY the call/put screen did not trade it (no signal, flow not confirming, R:R, already holding...). The
    screen used to drop those silently, so a quiet index looked like a broken one."""
    seen = st.setdefault("idxWhy", {})
    prev = seen.get(sym) or {}
    now_t = time.time()
    if prev.get("text") == text and now_t - prev.get("t", 0) < IDX_NOTE_EVERY:
        return
    seen[sym] = {"text": text, "t": now_t, "at": _now().isoformat()}
    st["log"].append({"at": _now().isoformat(), "msg": f"index {sym}: {text}"})


def fill_slots(st, today, already):
    """Entries beyond the strategy signals come from the app's own screens:
       index slots  <- index CALL / PUT where the daily chart and the live option flow agree
       stock slots  <- strongest BUY / SELL stock screens among 20 liquid F&O stocks (chosen automatically)
    Every trade is tagged with its source so strategy trades and screen trades can be judged separately."""
    import backtest
    import market_api
    cfg = st["cfg"]
    todays = [t for t in st["trades"] if t["date"] == today]
    # same guard as choose(): a symbol stopped out today (even from a swing opened earlier) must not re-enter
    used = _taken_syms(st, today) | {c["sym"] for c in already}
    have = {"index": 0, "stock": 0}
    for k in [t["kind"] for t in todays] + [c["kind"] for c in already]:
        have[k] += 1
    need = {"index": max(0, _cap(cfg, "indexSlots") - have["index"]), "stock": max(0, _cap(cfg, "stockSlots") - have["stock"])}
    room = _cap(cfg, "maxPerDay") - len(todays) - len(already)
    vercel = bool(os.environ.get("VERCEL"))
    out = []
    if room <= 0:
        return out
    if need["index"] > 0 and not cfg.get("stockOnly"):
        try:
            calls = market_api.quick_index_calls(6 if vercel else 15)
            ranked = []
            for c in calls:
                # an index is blocked while a trade in it is open, or once one was OPENED today (no re-entry after a stop - the 30-minute
                # re-entry rule bought the same index again after a loss). A carried trade that merely exited today (opened on an earlier
                # day, e.g. out at 09:07) does not count, so it never blocks the index all day.
                busy_idx = {x["sym"] for x in already} | {x["sym"] for x in out}
                if c["instrument"] in busy_idx:
                    _idx_note(st, c["instrument"], "not looked at - a trade in it is still open")
                    continue
                e_, s_, t1_ = (c.get(k) for k in ("entry", "stopLoss", "target1"))
                if e_ and s_ and t1_ and e_ > s_ and (t1_ - e_) / (e_ - s_) < MIN_INDEX_RR:
                    _idx_note(st, c["instrument"], f"{c.get('signal')} skipped - reward to target 1 is under {MIN_INDEX_RR}x the stop")
                    continue                                                   # weak risk/reward on the screen's own levels
                if c.get("signal") not in ("BUY CALL", "BUY PUT"):
                    _idx_note(st, c["instrument"], f"no entry - {c.get('signal') or 'NO SIGNAL'}: {c.get('reason') or 'chart and option flow do not agree yet'}")
                if c.get("signal") in ("BUY CALL", "BUY PUT"):
                    tier = 0 if c.get("confidence") == "high" else 1               # tier 0: chart + flow agree; tier 1: flow-led
                    sd = "BUY" if c["signal"] == "BUY CALL" else "SELL"
                    pts, bits = _index_backing(c, sd)
                    ranked.append((tier, -(c.get("strength") or 0), c, sd,
                                   f"index call/put ({c.get('basis', 'chart + option flow agree')})" + (f" · backed by {', '.join(bits)}" if bits else ""), pts))
            ranked.sort(key=lambda r: (r[0], -r[5], r[1]))                  # chart + flow agree first, then the most backing, then strength
            for tier, neg, c, side, why, pts in ranked:
                if need["index"] <= 0:
                    break
                score = (-neg) / 100 if tier == 0 else (-neg) / 200
                out.append({"_fill": True, "key": "index-call-put", "sym": c["instrument"], "side": side, "kind": "index", "variant": "fixed",
                            "filter": "none", "score": score, "rank": (1.0 if tier == 0 else 0.5) + score + 0.3 * pts, "agree": 1 + pts,
                            "source": why, "label": "index call/put screen"})
                used.add(c["instrument"])
                need["index"] -= 1
        except Exception as e:
            st["log"].append({"at": _now().isoformat(), "msg": f"index screen failed: {str(e)[:80]}"})
    if need["stock"] > 0:
        try:
            # the morning shortlist (morning_picks.py, same ranking as the Picks screen's `top`): strength >= 75 with good risk/reward first
            # (+ Open = Low / High agreeing), then Open = Low BUY / Open = High SELL, then fill-up - 10 to 15 stock trades a day in all
            import morning_picks
            classic = bool(cfg.get("classicOnly", True))
            n_before, screen_rows = len(out), []
            short_syms = set() if classic else {x["s"] for x in morning_picks.select([q for q in _picks().get("picks", []) if q.get("s") not in INDEX_SYMS and q.get("universe") != "cash"], max_n=NO_LIMIT, per_sector=NO_LIMIT)}
            if True:                                                           # 30 Oct (user): the stock screen runs in every mode, besides Today's Picks / Eagle, with no daily cap. The classic "stock screen (trend + volume + RSI)": the Picks engine's BUY / SELL stock signals with good risk/reward
                took = sum(1 for t in todays if t["kind"] == "stock" and t.get("strategy") == "stock-screen") + sum(1 for c in already if c.get("key") == "stock-screen")
                rows = []
                for p in _picks().get("picks", []):
                    if p.get("s") in INDEX_SYMS or p.get("universe") == "cash" or p.get("s") in used or p.get("signal") not in ("BUY", "SELL"):
                        continue
                    if not classic and p.get("s") in short_syms:
                        continue                                              # the shortlist takes its own names first
                    if (p.get("strength") or 0) >= morning_picks.FILL_STRENGTH_MIN and morning_picks.good_rr(p, p["signal"]):
                        rows.append(p)
                rows.sort(key=lambda p: -_quality(p))                    # strength >= 75% first, then strength and volume
                for p in rows[:max(0, need["stock"])]:
                    d = 1 if p["signal"] == "BUY" else -1
                    out.append({"_fill": True, "key": "stock-screen", "sym": p["s"], "side": p["signal"], "kind": "stock", "variant": "fixed", "filter": "none",
                                "indStop": round(p["ltp"] - d * morning_picks.swing_risk(p, p["signal"]), 2), "score": (p.get("strength") or 0) / 100,
                                "rank": (1.0 if classic else 0.01) + _quality(p) * (1 if classic else 0.01), "agree": 1, "source": "stock screen (trend + volume + RSI)", "label": "stock screen"})
                    used.add(p["s"]); need["stock"] -= 1
                if classic:
                    return out[:room]
                screen_rows, out = out[n_before:], out[:n_before]          # not classic: the shortlist keeps priority, the screen's picks follow it
            took = sum(1 for t in todays if t["kind"] == "stock" and t.get("strategy") == "morning-pick") + sum(1 for c in already if c.get("key") == "morning-pick")
            left = NO_LIMIT                                    # 30 Oct (user): the 15-a-day number belongs to the Fresh picks list on screen, not to the trades - every qualifying pick is taken
            picks = [p for p in _picks().get("picks", []) if p.get("s") not in INDEX_SYMS and p.get("universe") != "cash"]
            # tier 1 (strength >= 75 + good risk/reward on the daily chart) is valid from 09:16; tier 2 rests on Open = Low / High,
            # which nearly every stock shows in the first minutes - it waits for 09:20 (same as Eagle Trades)
            early = _mins(_now()) < EAGLE_FROM
            for p in [x for x in morning_picks.select(picks, max_n=NO_LIMIT, per_sector=NO_LIMIT) if x["s"] not in used and not (early and x["tier"] == 2)][:max(0, min(need["stock"], left))]:
                out.append({"_fill": True, "key": "morning-pick", "sym": p["s"], "side": p["side"], "kind": "stock", "variant": "fixed", "filter": "none",
                            "indStop": p["stop"],          # the shortlist's own stop for that side - the trade's risk is the one the list was ranked on
                            "score": (p.get("strength") or 0) / 100, "rank": p["rank"], "agree": 1, "tier": p["tier"],
                            "source": f"Today's Picks · tier {p['tier']} · {p['why']}", "label": "Today's Picks shortlist"})
            out.extend(screen_rows)
        except Exception as e:
            st["log"].append({"at": _now().isoformat(), "msg": f"stock screen failed: {str(e)[:80]}"})
    return out[:room]


EAGLE = "Eagle Trades"                    # the strategy name shown in the Journal (its "By strategy / setup" table groups on it)
EAGLE_STOP_PTS = 5.0       # Eagle (Open = Low -> call, Open = High -> put) premium rules (user, 30 Oct): stop 5 points from the entry, targets 1.5x / 2x / 3x ... of that risk,
EAGLE_OPEN_TOL = 0.03      # profit lock from Rs 1,500 / 2,000; bought only when the premium is at its day-open price (+3%) or down to 10 points below it
EAGLE_DIP_PTS = 10.0
EAGLE_FROM, EAGLE_TO = 9 * 60 + 20, 10 * 60 + 30     # the screen is read in the opening hour (backtested at 09:20-10:15)


def eagle_cands(st, today, taken=()):
    """Eagle Trades: strength >= 75, good risk/reward, and Open = Low (BUY) / Open = High (SELL) - every F&O stock that qualifies, no daily cap.
    Scanned on every cycle (not on the 10-minute screen timer) because Open = Low / High only holds until price breaks the open."""
    import market_api
    import morning_picks
    now_m = _mins(_now())
    if not (EAGLE_FROM <= now_m <= EAGLE_TO):
        return []
    used = _taken_syms(st, today) | set(taken)
    out = []
    for p in _picks().get("picks", []):
        if p.get("kind") == "index" or p.get("universe") == "cash" or p.get("s") in used:
            continue
        c = morning_picks.eagle(p)
        if not c:
            continue
        out.append({"key": EAGLE, "sym": p["s"], "side": c["side"], "kind": "stock", "variant": "fixed", "filter": "none",
                    "score": (p.get("strength") or 0) / 100, "rank": 20 + (p.get("strength") or 0) / 100, "agree": 1,
                    "indStop": round(p["ltp"] - (1 if c["side"] == "BUY" else -1) * morning_picks.swing_risk(p, c["side"]), 2),   # the pick's own stop, as in the backtest (the live stop is then capped at premSlPct of the premium, see open_trade)
                    "source": EAGLE, "why": c["why"], "label": EAGLE})
    return sorted(out, key=lambda c: -c["rank"])


def x_stop(rows):
    return rows[-1].get("stop") if rows else None


def _scan_settle(cache, sym, found, errs):
    """True when this symbol's scan is final for the day. Out of time -> not final. Some indicator runs FAILED -> not final: the symbol is
    retried in the next cycles (up to SCAN_RETRIES), instead of being closed for the whole day with whatever the surviving runs found."""
    if found is None:
        return False
    if errs:
        tries = cache.setdefault("tries", {})
        tries[sym] = tries.get(sym, 0) + 1
        return tries[sym] >= SCAN_RETRIES
    return True


def scan_all(st, today):
    """Fresh BUY/SELL events from EVERY indicator on the last completed daily bar, for 5 indices + every F&O stock
    with listed options (~218, not just the curated 20 - a stock is only skipped when it has no daily history).
    Completed bars only change once a day, so this is scanned ONCE per day, symbol by symbol (it resumes in the next
    cycle if it runs out of time) instead of being recomputed every 5 minutes - that was a big part of the Upstox load."""
    import backtest
    import bar_source
    import market_api
    cache = st.setdefault("cand", {})
    if cache.get("date") != today:
        cache.clear()
        cache.update(date=today, done=[], items=[], tries={})
    r = backtest.get()["result"]
    score = {x["key"]: x["inSample"]["avgR"] for x in (r["ranking"] if r else [])}
    chosen = {k: tuple(v) for k, v in ((r["chosen"] if r else {}) or {}).items()}
    runners = backtest._runners()
    try:
        uni = [s for s, _n, _sec in market_api.STOCKS] or backtest.STOCK_SYMS
        ensure = getattr(market_api, "ensure_universe", None)
        if ensure and len(uni) <= len(backtest.STOCK_SYMS):
            ensure()
            uni = [s for s, _n, _sec in market_api.STOCKS] or uni
    except Exception:
        uni = backtest.STOCK_SYMS
    syms = INDEX_SYMS + [x for x in uni if x not in INDEX_SYMS and bar_source.supports(x)]
    todo = [x for x in syms if x not in cache["done"]]
    deadline = time.time() + (8 if os.environ.get("VERCEL") else 120)

    import concurrent.futures as cf

    def one_symbol(sym):
        bar_source.completed_only(True)               # long-cached completed bars, no intraday request
        found, errs = [], 0
        for key, fn in runners.items():
            if time.time() > deadline:
                return sym, None, 0                    # not finished: stays on the to-do list
            try:
                rows = fn(sym, 400).get("bars") or []
            except Exception:
                errs += 1                              # a failed run (rate limit, timeout) is NOT "no signal"
                continue
            rows = [x for x in rows if x.get("date") and x["date"] < today]
            if len(rows) < 2:
                continue
            sg, prev = backtest.norm_signal(rows[-1].get("signal")), backtest.norm_signal(rows[-2].get("signal"))
            if not sg or sg == prev:
                continue
            variant, flt = chosen.get(key, ("fixed", "none"))
            if flt == "trend200" and not _trend_ok(sym, sg, today):
                continue
            found.append({"key": key, "sym": sym, "side": sg, "asOf": rows[-1]["date"], "score": score.get(key, 0.0), "indStop": x_stop(rows),
                          "variant": variant, "filter": flt, "kind": "index" if sym in INDEX_SYMS else "stock"})
        return sym, found, errs

    with cf.ThreadPoolExecutor(max_workers=4) as ex:
        for sym, found, errs in ex.map(one_symbol, todo):
            if _scan_settle(cache, sym, found, errs):
                cache["done"].append(sym)
                cache["items"].extend(found)
    done = len(cache["done"])
    note = f"all indicators scanned: {done}/{len(syms)} symbols, {len(cache['items'])} fresh signals"
    for c in cache["items"]:
        c["label"] = "all indicators"
    return list(cache["items"]), note


def _screen_score():
    """Stock screen score and direction from the Picks engine (used only to choose among stock signals)."""
    try:
        import market_api
        return {p["s"]: p for p in _picks().get("picks", [])}
    except Exception:
        return {}


TC_TRIGGER_TOL = 0.0015          # price within 0.15% of the zone at the cycle time
TC_MIN_RR = 1.2                  # only take a cycle trigger when the zone-to-zone reward is worth the risk


GANN_STOCKS = 30                 # stocks scanned per 15-minute bar: the strongest F&O names on the Picks screen (each costs one candle request)


def _gann_one(sym, now):
    import gann_angle
    import market_api
    try:
        bars = market_api.candles(symbol=sym, tf="15m", recent=10)["bars"]
    except Exception:
        return None
    ms = now.timestamp() * 1000
    bars = [b for b in bars if b["t"] + 15 * 60 * 1000 <= ms]                                  # closed bars only
    if not bars or ms - (bars[-1]["t"] + 15 * 60 * 1000) > 20 * 60 * 1000:
        return None                                                                           # the signal bar must be the one that just closed
    return gann_angle.bounce(bars)


def _gann_cands(now, used=()):
    """Gann time-price angle bounce (see gann_angle.py) on every index and the strongest F&O stocks, 15-minute bars: the latest CLOSED bar
    dipped to the slanted 1x1 line and closed back off it. Buy-only - a call for a support bounce, a put for a resistance rejection.
    Indices are looked at every cycle (candles are cached for seconds); the stock list once per 15-minute bar."""
    import concurrent.futures
    now_m = _mins(now)
    if not (9 * 60 + 45 <= now_m <= 15 * 60):
        return []
    syms = [(s, "index") for s in INDEX_SYMS if s not in used]
    slot = int(now.timestamp() // 900)
    if not shared_cache.get(f"auto:gann-stocks:{slot}"):
        shared_cache.set(f"auto:gann-stocks:{slot}", 1, 900)
        try:
            ps = [p for p in _picks().get("picks", []) if p.get("kind") != "index" and p.get("universe") != "cash" and p.get("s") not in INDEX_SYMS and p.get("s") not in used]
            ps.sort(key=lambda p: -(p.get("strength") or 0))
            syms += [(p["s"], "stock") for p in ps[:GANN_STOCKS]]
        except Exception:
            pass
    out = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        for (sym, kind), g in zip(syms, pool.map(lambda x: _gann_one(x[0], now), syms)):
            if g:
                out.append({"key": "gann-angle", "sym": sym, "side": g["side"], "asOf": now.date().isoformat(), "score": 0.6, "rank": 6 + g["rr"] / 10, "indStop": g["stop"],
                            "variant": "fixed", "filter": "none", "kind": kind, "source": g["why"], "label": "Gann angle"})
    return sorted(out, key=lambda c: -c["rank"])[:3]


ZTC_WINDOW_MIN = 5            # a strong / medium cycle time is honoured +-5 minutes (the plain time-cycle trigger uses +-3)
ZTC_ZONE_TOL = 0.0025         # price within 0.25% of the zone (plain trigger: 0.15%) - the Z Trend agreement is the extra filter


def _ztc_cands(now):
    """Z Trend + Gann time cycle confluence (user, 29 Oct): the cycle TIME and the ZONE must line up (as in the plain time-cycle trigger) AND the
    Z Trend direction on the 5-minute chart must agree - its latest flip today: BUY at the vibration support with the last flip BUY, SELL at the
    resistance with the last flip SELL. Two independent readings (time/price and trend) have to point the same way, which is what should cut
    the false cycle triggers. Stop = a whisker beyond the zone, target = the next zone, R:R >= TC_MIN_RR. Tagged "z-timecycle" so the journal's
    By-strategy table measures it on its own (forward test: no historical cycle backtest exists for it)."""
    try:
        import vedic_api
        import rzt as rzt_mod
    except Exception:
        return []
    now_m, out = _mins(now), []
    for sym in ("NIFTY", "BANKNIFTY"):
        try:
            d = vedic_api.timecycle(symbol=sym, mode="underlying", strike=0)
            cyc = next((c for c in d.get("cycles") or [] if abs(c.get("m", 10 ** 6) - now_m) <= ZTC_WINDOW_MIN and c.get("strength") in ("strong", "medium")), None)
            last = float(d.get("last") or 0)
            vib, res = (d.get("vibration") or {}).get("level"), (d.get("nextResistance") or {}).get("level")
            if not (cyc and last > 0 and vib and res):
                continue
            flips = [c for c in rzt_mod.intraday_cands([sym], fresh_min=10 ** 4) if c.get("sym") == sym]   # every flip today (cached ~4 min)
            if not flips:
                continue
            trend = flips[-1]["side"]                                                   # the latest flip is the trend now
            tol = last * ZTC_ZONE_TOL
            if abs(last - vib) <= tol and trend == "BUY":
                stop = round(vib - last * 0.001, 2)
                risk, reward, side, at = last - stop, res - last, "BUY", f"vibration zone {vib:,.2f} · target {res:,.2f}"
            elif abs(last - res) <= tol and trend == "SELL":
                stop = round(res + last * 0.001, 2)
                risk, reward, side, at = stop - last, last - vib, "SELL", f"resistance {res:,.2f} · target {vib:,.2f}"
            else:
                continue
            if risk > 0 and reward / risk >= TC_MIN_RR:
                out.append({"key": "z-timecycle", "sym": sym, "side": side, "asOf": now.date().isoformat(), "score": 0.7, "indStop": stop,
                            "variant": "fixed", "filter": "none", "kind": "index", "label": "Z Trend + time cycle",
                            "source": f"Z Trend {side} + Gann cycle {cyc['time']} ({cyc['strength']}) · price at {at} · R:R 1:{reward / risk:.1f}"})
        except Exception:
            continue
    return out[:1]


def _timecycle_cands(now):
    """Gann time cycle trigger (indices only): at a strong / medium cycle time, price sitting at the
    vibration zone (support) or the next resistance is the traditional 'price confirms time' entry.
    Stop = a whisker beyond the zone, target = the next zone; skipped unless reward/risk >= TC_MIN_RR."""
    try:
        import vedic_api
    except Exception:
        return []
    now_m = _mins(now)
    out = []
    for s in ("NIFTY", "BANKNIFTY"):
        try:
            d = vedic_api.timecycle(symbol=s, mode="underlying", strike=0)
        except Exception:
            continue
        cyc = next((c for c in d.get("cycles") or [] if abs(c.get("m", 10 ** 6) - now_m) <= 3 and c.get("strength") in ("strong", "medium")), None)
        if not cyc:
            continue
        last = float(d.get("last") or 0)
        vib = (d.get("vibration") or {}).get("level")
        res = (d.get("nextResistance") or {}).get("level")
        if not (last > 0 and vib and res):
            continue
        tol = last * TC_TRIGGER_TOL
        if abs(last - vib) <= tol:
            stop = round(vib - last * 0.001, 2)
            risk, reward = last - stop, res - last
            if risk > 0 and reward / risk >= TC_MIN_RR:
                out.append({"key": "timecycle", "sym": s, "side": "BUY", "asOf": now.date().isoformat(), "score": 0.6,
                            "indStop": stop, "variant": "fixed", "filter": "none", "kind": "index",
                            "source": f"Gann cycle {cyc['time']} ({cyc['strength']}) · price at vibration zone {vib:,.2f} · target {res:,.2f} · R:R 1:{reward / risk:.1f}",
                            "label": "time cycle"})
        elif abs(last - res) <= tol:
            stop = round(res + last * 0.001, 2)
            risk, reward = stop - last, last - vib
            if risk > 0 and reward / risk >= TC_MIN_RR:
                out.append({"key": "timecycle", "sym": s, "side": "SELL", "asOf": now.date().isoformat(), "score": 0.6,
                            "indStop": stop, "variant": "fixed", "filter": "none", "kind": "index",
                            "source": f"Gann cycle {cyc['time']} ({cyc['strength']}) · price at resistance {res:,.2f} · target {vib:,.2f} · R:R 1:{reward / risk:.1f}",
                            "label": "time cycle"})
    return out[:1]                   # at most one cycle trade per cycle - it is a timing cherry-pick, not a machine gun


SHADOW_KEYS = {"morning-pick", EAGLE, "gann-angle", "timecycle"}          # tested on paper only while classicOnly is on
SHADOW_MAX = 800


def shadow_record(st, cands, now):
    """Paper-only log of the signals classic mode does not trade (Picks shortlist, Eagle, Gann angle, time cycle, Z Trend): entry = the
    underlying's live price, stop = the signal's own stop, target = 1.5R. Resolved by shadow_resolve(); summary in status()['shadow']."""
    sh = st.setdefault("shadow", [])
    today = now.date().isoformat()
    have = {(x["date"], x["sym"], x["key"]) for x in sh}
    for c in cands:
        k = "rzt" if str(c.get("key", "")).startswith("rzt") else c.get("key")
        if (today, c["sym"], k) in have or not c.get("indStop"):
            continue
        try:
            px = _live_spot(c["sym"])
        except Exception:
            px = 0
        d = 1 if c["side"] == "BUY" else -1
        risk = (px - c["indStop"]) * d
        if px <= 0 or risk <= 0 or risk > px * 0.08:
            continue
        sh.append({"id": f"{today}-{c['sym']}-{k}", "date": today, "at": now.isoformat(), "key": k, "sym": c["sym"], "side": c["side"], "entry": round(px, 2),
                   "stop": round(c["indStop"], 2), "target": round(px + d * 1.5 * risk, 2), "status": "OPEN"})
        st["_dirty"] = True
    del sh[:-SHADOW_MAX]


def shadow_record_premium(st, signals, now):
    """Paper-only log of Premium Rider signals (premium_rider.py): the entry / stop / target are PREMIUM prices of the contract itself."""
    sh = st.setdefault("shadow", [])
    today = now.date().isoformat()
    have = {x["id"] for x in sh}
    for g in signals:
        sid = f"{today}-{g['contract']}-{g['pattern']}"
        if sid in have or not g.get("key") or not (g["entry"] > g["stop"] > 0):
            continue
        sh.append({"id": sid, "date": today, "at": now.isoformat(), "key": "premium-rider", "sym": g["contract"], "ikey": g["key"], "side": "BUY", "entry": g["entry"],
                   "stop": g["stop"], "target": g["target"], "pattern": g["pattern"], "status": "OPEN"})
        st["_dirty"] = True
    del sh[:-SHADOW_MAX]


def shadow_resolve(st, now):
    """Close shadow signals on their stop / 1.5R target (live underlying price); anything still open is closed at the 15:25 mark at that day's last price."""
    opens = [x for x in st.get("shadow", []) if x["status"] == "OPEN"]
    if not opens:
        return
    import market_api
    keys = {x["id"]: (x.get("ikey") or market_api._key(x["sym"])) for x in opens}
    try:
        q = _quotes(set(keys.values()))
    except Exception:
        return
    for x in opens:
        px = _last(q.get(keys[x["id"]]))
        if px <= 0:
            continue
        d = 1 if x["side"] == "BUY" else -1
        risk = abs(x["entry"] - x["stop"]) or 1
        r_now = (px - x["entry"]) * d / risk
        if r_now > x.get("peakR", 0):
            x["peakR"] = round(r_now, 2)                                  # best the trade reached before it ended (how far a target ladder could have run)
            st["_dirty"] = True
        end = x["date"] < now.date().isoformat() or _mins(now) >= 15 * 60 + 25
        why = "stop" if r_now <= -1 else "close" if end else None
        if why:
            x.update(status="CLOSED", exit=round(px, 2), why=why, R=round(r_now, 2), closedAt=now.isoformat())
            st["_dirty"] = True


def shadow_summary(st):
    """Per strategy: signals, win %, average R if held to the stop / 15:25, how often it reached 1.5R / 2R / 3R first (peak R before the stop),
    the planned risk:reward to the 1.5R first target, the profit factor of the 1.5R-or-stop outcome - the numbers to tune the stops and targets on."""
    out = {}
    for x in st.get("shadow", []):
        o = out.setdefault(x["key"], {"key": x["key"], "n": 0, "open": 0, "wins": 0, "sumR": 0.0, "h15": 0, "h2": 0, "h3": 0, "gain": 0.0, "loss": 0.0, "stopPct": 0.0})
        o["n"] += 1
        if x["status"] == "OPEN":
            o["open"] += 1
            continue
        r = x.get("R") or 0
        pk = x.get("peakR") or 0
        o["sumR"] += r
        o["wins"] += 1 if r > 0 else 0
        o["h15"] += 1 if pk >= 1.5 else 0
        o["h2"] += 1 if pk >= 2 else 0
        o["h3"] += 1 if pk >= 3 else 0
        r15 = 1.5 if pk >= 1.5 else r                      # take-profit at 1.5R, otherwise whatever the day gave
        o["gain" if r15 > 0 else "loss"] += abs(r15)
        o["stopPct"] += abs(x["entry"] - x["stop"]) / x["entry"] * 100
    for o in out.values():
        c = o["n"] - o["open"]
        pct = lambda v: round(v / c, 2) if c else 0
        o.update(winRate=pct(o["wins"]), avgR=round(o["sumR"] / c, 2) if c else 0, hit15=pct(o.pop("h15")), hit2=pct(o.pop("h2")), hit3=pct(o.pop("h3")),
                 pf=round(o["gain"] / o["loss"], 2) if o["loss"] else (None if not o["gain"] else 99), avgStopPct=round(o.pop("stopPct") / c, 2) if c else 0, plannedRR="1 : 1.5")
        o["sumR"] = round(o["sumR"], 2)
        o.pop("gain"); o.pop("loss")
    return sorted(out.values(), key=lambda o: -o["n"])


def classic_filter(entries, extras_agree=False):
    """Classic mode: (traded, paper-only). Picks / Eagle / Gann angle / time cycle / Z Trend trade only when a classic entry on the same symbol
    and side agrees (the extra is taken instead of the classic one, tagged 'agrees with ...'); unconfirmed extras stay paper-only."""
    is_extra = lambda c: c.get("key") in SHADOW_KEYS or str(c.get("key", "")).startswith("rzt")
    classic = {(c["sym"], c["side"]): c for c in entries if not is_extra(c)}
    agreed = {(c["sym"], c["side"]) for c in entries if extras_agree and is_extra(c) and (c["sym"], c["side"]) in classic}
    kept, paper = [], []
    for c in entries:
        k = (c["sym"], c["side"])
        if not is_extra(c):
            if k not in agreed:
                kept.append(c)
        elif extras_agree and k in classic:
            base = classic[k]
            kept.append(dict(c, source=f"{c.get('source') or c.get('label') or c['key']} · agrees with {base.get('label') or base.get('key')}", agree=max(c.get("agree", 1), 2)))
        else:
            paper.append(c)
    return kept, paper


STRENGTH_BANDS = (99.5, 95.0, 85.0, 75.0)       # then index options, then 65+, 50+, the rest


def entry_priority(c, pmap):
    """Order in which entries are taken (user, 30 Oct): by Picks strength, highest first - 100, then 95+, 85+, 75+, 65+, 50+ and the rest last; index options sit in the same bands by their own
    Picks strength (30 Oct, user), and inside a band the one with more agreeing indicators goes first. Inside one band an Eagle trade (Open = High -> put, Open = Low -> call) goes before the others; equal entries keep their existing order."""
    stren = float((pmap.get(c.get("sym")) or {}).get("strength") or 0)
    if c.get("kind") == "index" and stren <= 0:               # 30 Oct (user): an index is ranked like a stock - its own Picks strength; without a Picks row, by how many fresh indicators agree
        stren = 85.0 if int(c.get("agree") or 1) >= 3 else 75.0 if int(c.get("agree") or 1) >= 2 else 0.0
    band = next((i for i, lvl in enumerate(STRENGTH_BANDS) if stren >= lvl), None)
    if band is None:
        band = len(STRENGTH_BANDS) + 1 + (0 if stren >= 65 else 1 if stren >= 50 else 2)
    return (band, 0 if c.get("key") == EAGLE else 1, -int(c.get("agree") or 1))     # then the entry with more agreeing (fresh) indicators first


def _quality(p):
    """How good a stock's Picks row looks for the entry ranking (user, 29 Oct): strength >= 75% first, then more strength, then more volume
    (volume vs its own average, capped at 3x). Added to a candidate's rank so strong, busy stocks are bought before weak, quiet ones."""
    if not p:
        return 0.0
    st_ = float(p.get("strength") or 0)
    vx = float(p.get("volx") or 0)
    top = 1.0 if st_ >= 99.5 else 0.0                       # user, 29 Oct: strength-100 stocks first; among them (and everywhere below) the higher volume goes first - no volume threshold
    return top + (0.5 if st_ >= 75 else 0.0) + min(st_, 100) / 400 + min(vx, 3.0) / 6


def choose(cands, st, today):
    cfg = st["cfg"]
    taken_today = [t for t in st["trades"] if t["date"] == today]
    have_idx = sum(1 for t in taken_today if t["kind"] == "index")
    have_stk = sum(1 for t in taken_today if t["kind"] == "stock")
    # one entry per symbol a day - a swing trade that hit its stop TODAY counts too (it closed today, opened earlier),
    # which is exactly the re-entry-after-stop bug this set exists to prevent
    open_syms = _taken_syms(st, today)
    by_sym = {}
    for c in cands:
        by_sym.setdefault(c["sym"], []).append(c)
    clean = []
    for sym, lst in by_sym.items():
        if sym in open_syms:
            continue                                         # already holding it
        buys, sells = [c for c in lst if c["side"] == "BUY"], [c for c in lst if c["side"] == "SELL"]
        if len(buys) == len(sells):
            continue                                         # indicators cancel out: no view
        side_list = buys if len(buys) > len(sells) else sells
        best = max(side_list, key=lambda c: c["score"])
        best["agree"] = len(side_list)                       # how many indicators point the same way
        best["against"] = len(lst) - len(side_list)
        best["strategies"] = [c["key"] for c in side_list]
        clean.append(best)
    screen = _screen_score() if any(c["kind"] == "stock" for c in clean) else {}
    for c in clean:
        p = screen.get(c["sym"])
        c["screenAgrees"] = bool(p and ((c["side"] == "BUY" and p["signal"] == "BUY") or (c["side"] == "SELL" and p["signal"] == "SELL")))
        c["rank"] = c["score"] + 0.5 * (c["agree"] - c.get("against", 0) - 1) + (0.3 if c["screenAgrees"] else 0) + (_quality(p) if c["kind"] == "stock" else 0)
    idx = sorted([c for c in clean if c["kind"] == "index"], key=lambda c: -c["rank"])[:max(0, _cap(cfg, "indexSlots") - have_idx)]
    stk = sorted([c for c in clean if c["kind"] == "stock" and c["screenAgrees"]], key=lambda c: -c["rank"])
    if len(stk) < max(0, _cap(cfg, "stockSlots") - have_stk):              # fall back to any proven stock signal
        stk += sorted([c for c in clean if c["kind"] == "stock" and not c["screenAgrees"]], key=lambda c: -c["rank"])
    stk = stk[:max(0, _cap(cfg, "stockSlots") - have_stk)]
    room = max(0, _cap(cfg, "maxPerDay") - len(taken_today))
    return (idx + stk)[:room]


# ───────────────────────── entries / exits ─────────────────────────
def _live_spot(sym, fallback=0.0):
    """Live price of the underlying (index or stock); the option chain's own spot is only the fallback."""
    try:
        import market_api
        k = market_api._key(sym)
        v = _last(_quotes({k}).get(k))
        if v > 0:
            return v
    except Exception:
        pass
    return float(fallback or 0)


def _contract(sym, side, today, min_days, max_outlay=None):
    import market_api
    ch = market_api.chain(sym, "")
    exps = [e for e in (ch.get("expiries") or [ch.get("expiry")]) if e]
    pick = next((e for e in sorted(exps) if (date.fromisoformat(e) - date.fromisoformat(today)).days >= min_days), None)
    if pick and pick != ch.get("expiry"):
        ch = market_api.chain(sym, pick)
    rows = ch.get("rows") or []
    chain_spot = float(ch.get("spot") or 0)
    # The strike is chosen from the LIVE price of the underlying, not the chain's own spot field: that field can lag at the open, and a
    # stale spot after a gap bought a call far in the money (28 Oct, Bank Nifty). Rule: at-the-money only (nearest strike to the live
    # price); a trade is never opened in the money.
    spot = _live_spot(sym, chain_spot)
    if not rows or spot <= 0:
        raise RuntimeError("no chain")
    row = min(rows, key=lambda r: abs(r["strike"] - spot))
    strikes = sorted({r["strike"] for r in rows})
    step = min((b - a for a, b in zip(strikes, strikes[1:]) if b > a), default=0) or max(1.0, spot * 0.005)
    if abs(row["strike"] - spot) > step:
        raise RuntimeError(f"skipped: no strike near the price ({row['strike']:.0f} vs {spot:.0f})")
    # second check from the option prices themselves (put-call parity: call - put at a strike = forward - strike): a call that is clearly
    # in the money (or a put that is) is refused even if both price feeds agree on a wrong spot
    ce_, pe_ = (row.get("ce") or {}).get("ltp") or 0, (row.get("pe") or {}).get("ltp") or 0
    if ce_ > 0 and pe_ > 0:
        days = max(0, (date.fromisoformat(ch["expiry"]) - date.fromisoformat(today)).days) if ch.get("expiry") else 30
        itm = (ce_ - pe_ if side == "BUY" else pe_ - ce_) - 0.08 * spot * days / 365     # allow for carry / dividends
        if itm > 1.5 * step:
            raise RuntimeError(f"skipped: {row['strike']:.0f} {'CE' if side == 'BUY' else 'PE'} looks in the money (~{itm:.0f} pts) - ATM / OTM only")
    lot_ = int(ch.get("lot") or 1)
    if max_outlay:                                       # premium budget per trade: walk OTM (calls up, puts down) from the ATM strike until one lot fits
        side_k = "ce" if side == "BUY" else "pe"
        order = sorted(rows, key=lambda r: r["strike"]) if side == "BUY" else sorted(rows, key=lambda r: -r["strike"])
        start = next((i for i, r in enumerate(order) if r["strike"] == row["strike"]), 0)
        fit = next((r for r in order[start:] if (lambda lg: (lg.get("key") and (float(lg.get("ask") or 0) or float(lg.get("ltp") or 0)) > 0
                                                          and (float(lg.get("ask") or 0) or float(lg.get("ltp") or 0)) * lot_ <= max_outlay))(r.get(side_k) or {})), None)
        if not fit:
            raise RuntimeError(f"skipped: no strike fits the Rs {max_outlay:,.0f} premium budget")
        row = fit
    leg = row.get("ce" if side == "BUY" else "pe") or {}
    ask, bid, ltp = float(leg.get("ask") or 0), float(leg.get("bid") or 0), float(leg.get("ltp") or 0)
    px = ask or ltp
    if not leg.get("key") or px <= 0:
        raise RuntimeError("no price")
    # liquidity guard: a stale or one-sided quote is not a price you can trade at (it turned a flat MIDCPNIFTY entry into a fake -48%)
    if ask > 0 and bid > 0 and (ask - bid) / ask > 0.10:
        raise RuntimeError(f"skipped: bid/ask spread {(ask - bid) / ask * 100:.0f}% is too wide")
    if ask > 0 and ltp > 0 and abs(ask - ltp) / ltp > 0.25:
        raise RuntimeError(f"skipped: ask {ask} is far from the last traded price {ltp} (illiquid)")
    if ask > 0 and bid <= 0:
        raise RuntimeError("skipped: no bid in the market")
    return {"expiry": ch["expiry"], "strike": row["strike"], "key": leg["key"], "premium": px, "lot": int(ch.get("lot") or 1),
            "spot": spot, "bid": bid, "ask": ask, "ltp": ltp,
            "pOpen": float(leg.get("open") or 0), "pHigh": float(leg.get("high") or 0), "pLow": float(leg.get("low") or 0)}


OEL_TOL, OEL_WIDE = 0.5, 10.0


def premium_oel(ct):
    """User rule (29 Oct, same as the Trade screen's premium indicator): the option we would BUY opened at its day low.
       'clean'  = Open = Low (low >= open - 0.5) and the price is above the open -> stop 10 pts (capped at 35% of the premium)
       'wide'   = Open = Low within 10 pts (low >= open - 10) and the price is at / above the open -> stop 3 pts
       None otherwise. Returns (kind, stop_pts) - the stop is only ever used when it is TIGHTER than the normal premium stop."""
    o, h, l, p = float(ct.get("pOpen") or 0), float(ct.get("pHigh") or 0), float(ct.get("pLow") or 0), float(ct.get("ltp") or ct.get("premium") or 0)
    if o < 5 or not (h > l > 0) or p <= 0:
        return None
    # the setup is only live while the price is still near the low it bounced from: stop = low - 10 pts, targets 1.5x / 2x / 3x the entry. Once
    # price has run past the buy zone or already touched the first target the signal is over (it used to keep saying BUY at 141 after a low of 86)
    if p < l - OEL_WIDE or p > max(l + max(3.0, 0.1 * l), o * 1.05) or h >= 1.5 * l:
        return None
    stop = round(max(0.5, p - (l - 10.0)), 2)
    if abs(l - o) <= OEL_TOL and p > o:
        return "clean", stop
    if l >= o - OEL_WIDE and p >= o:
        return "wide", stop
    return None


def _oel_stop(entry, pts):
    return round(max(0.05, entry - min(pts, max(0.5, entry * 0.35))), 2)       # same cap as the Trade screen: never more than 35% of a small premium


_OEL_CACHE = {}


def oel_tag(c, today, cfg):
    """Premium Open = Low tag of a candidate's ATM contract (cached 60 s: the chain is already cached, this only reads it)."""
    k = (c["sym"], c["side"], today)
    hit = _OEL_CACHE.get(k)
    if hit and time.time() - hit[0] < 60:
        return hit[1]
    tag = None
    try:
        cap = float((cfg.get("maxOutlay") or MAX_OUTLAY).get(c["sym"]) or 0) or None
        tag = premium_oel(_contract(c["sym"], c["side"], today, cfg["minDaysToExpiry"], cap))
    except Exception:
        tag = None
    _OEL_CACHE[k] = (time.time(), tag)
    return tag


CONTRACT_CONFIRM = True      # 29 Oct (user): a bought option is only entered when the contract's OWN 5m indicators are not clearly against it


def _ema(vals, n):
    k, e, out = 2.0 / (n + 1), None, []
    for v in vals:
        e = v if e is None else v * k + e * (1 - k)
        out.append(e)
    return out


def contract_votes(bars):
    """Bull / bear votes from the option's own 5m candles - the same five readings the Trade screen shows
    (RSI 14, MACD 12/26/9, VWAP, EMA 21, SMA 20). Returns (bull, bear) or None when there are too few candles to judge."""
    cl = [float(b["close"]) for b in bars if float(b.get("close") or 0) > 0]
    if len(cl) < 22:
        return None
    px, bull, bear = cl[-1], 0, 0
    g = [max(cl[i] - cl[i - 1], 0) for i in range(1, len(cl))]
    l = [max(cl[i - 1] - cl[i], 0) for i in range(1, len(cl))]
    ag, al = sum(g[:14]) / 14, sum(l[:14]) / 14
    for i in range(14, len(g)):
        ag, al = (ag * 13 + g[i]) / 14, (al * 13 + l[i]) / 14
    rsi = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    if rsi > 55:
        bull += 1
    elif rsi < 45:
        bear += 1
    if len(cl) >= 35:
        m = [a_ - b_ for a_, b_ in zip(_ema(cl, 12), _ema(cl, 26))]
        sg = _ema(m, 9)
        if m[-1] > sg[-1]:
            bull += 1
        else:
            bear += 1
    day = str(bars[-1].get("time") or "")[:10]
    sess = [b for b in bars if str(b.get("time") or "")[:10] == day] or bars
    pv = sum(((float(b["high"]) + float(b["low"]) + float(b["close"])) / 3) * float(b.get("volume") or 0) for b in sess)
    vv = sum(float(b.get("volume") or 0) for b in sess)
    if vv > 0:
        if px > pv / vv:
            bull += 1
        else:
            bear += 1
    for ref in (_ema(cl, 21)[-1], sum(cl[-20:]) / 20):
        if px > ref:
            bull += 1
        else:
            bear += 1
    return bull, bear


def stock_open_backs(sym, side):
    """The stock's own Open = Low (BUY) / Open = High (SELL) from the Picks row - the user's open rule, for any stock or index entry."""
    try:
        import morning_picks
        for p in _picks().get("picks", []):
            if p.get("s") == sym:
                ol, oh = morning_picks.open_flags(p)
                return bool(ol if side == "BUY" else oh)
    except Exception:
        pass
    return False


def contract_blocked(ct, cfg=None):
    """A bought option is skipped when most of its own indicators point down (a premium that is falling is not a long to buy,
    even when the stock's strategies lean the right way). Unknown / too little data never blocks."""
    if not CONTRACT_CONFIRM or (cfg is not None and cfg.get("contractConfirm") is False):
        return None
    try:
        from nse_service import nse_service
        bars = nse_service.upstox.get_candles(ct["key"], "5minute")
        v = contract_votes(bars or [])
    except Exception as e:
        print(f"[auto] contract check unavailable: {e}")
        return None
    if v and v[1] >= 4 and v[0] <= 1:                       # loosened (user 29 Oct): only when 4 of the 5 readings are down and at most 1 is up
        return f"skipped: this option's own 5m indicators are bearish ({v[0]} up / {v[1]} down) - waiting for the contract itself to turn up"
    return None


def _atr_for(sym):
    import bar_source
    from ut_bot import _rma, _true_range
    bars = bar_source.daily_bars(sym, 120)
    bars = [b for b in bars if b["date"] < _now().date().isoformat()]
    a = _rma(_true_range(bars), 14)
    return a[-1], bars[-1]["close"], bars


def _premium_plan(entry, risk_u, delta=0.5):
    """Option stop and targets in premium terms: 1R = delta x underlying stop distance."""
    rp = round(delta * risk_u, 2)
    return {"premRisk": rp, "premSL": round(max(0.05, entry - rp), 2),
            "premT": [round(entry + k * rp, 2) for k in TARGET_LADDER]}


def _replan(t):
    """Trades opened under the old 1.5-2 ATR rule risked up to 90% of the premium; cap them at 30% (tighten only)."""
    if t.get("plan") == "v2" or t["status"] != "OPEN" or t.get("pos") == "short":
        return
    import backtest
    d = 1 if t["side"] == "BUY" else -1
    cap = backtest.PREM_SL * t["entry"] / backtest.DELTA
    if t["riskU"] > cap:
        t["riskU"] = round(cap, 2)
        ns = t["entryU"] - d * cap
        t["stopU"] = round(max(t["stopU"], ns) if d > 0 else min(t["stopU"], ns), 2)
        if t.get("targetU") is not None:
            t["targetU"] = round(t["entryU"] + d * backtest.TARGET_R * cap, 2)
        qty = t["lots"] * t["lot"]
        t["initialRisk"] = round(min(qty * backtest.DELTA * cap, qty * t["entry"]), 0)
    t.update(_premium_plan(t["entry"], t["riskU"]), plan="v2")


def open_trade(st, c, today):
    cfg = st["cfg"]
    import backtest
    atr, last_close, bars = _atr_for(c["sym"])
    cap = float((cfg.get("maxOutlay") or MAX_OUTLAY).get(c["sym"]) or 0) or None
    ct = _contract(c["sym"], c["side"], today, cfg["minDaysToExpiry"], cap)
    if INDEX_ONE_OPEN_PER_SIDE and c["sym"] in INDEX_SYMS:        # 30 Oct (user): the ATM strike rolls up with the price, so a standing signal bought a "new" contract every 2-minute cycle
        want = "CE" if c["side"] == "BUY" else "PE"
        if any(t.get("status") == "OPEN" and t.get("sym") == c["sym"] and t.get("opt") == want and not t.get("pairOf") and t.get("pos") != "short" for t in st["trades"]):
            raise RuntimeError(f"skipped: a {c['sym']} {want} trade is still open - the next one comes after it exits or on the opposite side")
    if BLOCK_SAME_CONTRACT and any(t.get("key") == ct["key"] and (t.get("status") == "OPEN" or t.get("date") == today or (t.get("closedAt") or "") >= today) for t in st["trades"]):
        raise RuntimeError("skipped: this option contract was already traded today (a new entry has to be in another option)")
    ask_, bid_ = float(ct.get("ask") or 0), float(ct.get("bid") or 0)
    if ask_ > 0 and bid_ > 0:                           # the stop is judged on the bid but the entry is paid at the ask: the spread must leave room for the stop
        sp_, lim_ = (ask_ - bid_) / ask_, MAX_SPREAD_OF_STOP * float(cfg.get("premSlPct", PREM_SL_PCT))
        if sp_ > lim_:
            raise RuntimeError(f"skipped: bid/ask spread {sp_ * 100:.1f}% is too wide for the {float(cfg.get('premSlPct', PREM_SL_PCT)) * 100:.1f}% stop (max {lim_ * 100:.1f}%)")
    # the bearish-contract veto does not apply when the open itself backs the trade: the option opened at its day low (premium Open = Low, stop low - 10),
    # or it is an Eagle trade (stock Open = Low for a BUY / Open = High for a SELL). Those are the user's own entry rules (29 Oct).
    open_backed = filter_set(c) == "OLD FILT" or bool(premium_oel(ct)) or c.get("key") == EAGLE or stock_open_backs(c["sym"], c["side"])
    if c.get("pos") != "short" and c.get("key") != "rzt-hedge" and not str(c.get("id", "")).endswith("-W") and not open_backed:
        why_ = contract_blocked(ct, cfg)
        if why_:
            raise RuntimeError(why_)
    d = 1 if c["side"] == "BUY" else -1
    entry_u = ct["spot"] or last_close
    variant = c.get("variant", "fixed")
    # signal-candle stop from the backtest's plan_risk() (capped at backtest.PREM_SL of the premium); the live cap below (premSlPct, same 12.5% by default) is applied on top
    risk_u = backtest.plan_risk(bars, atr, len(bars) - 1, c["side"], entry_u, ct["premium"], ind_stop=c.get("indStop"))
    if risk_u <= 0:
        raise RuntimeError("no valid stop")
    # 28 Oct (user: the stops were too big - up to 30% of the premium): the option stop is capped at premSlPct (default 12.5%) of the premium.
    # The target keeps its 2R distance, so the reward shrinks with the risk; position size is set from the risk budget, so a tighter stop
    # means more lots for the same money at risk.
    # 30 Oct (user): the OLD FILT set trades by its 21 Oct rules so its accuracy can be compared with the new indicators: the stop is the signal-candle stop
    # capped at 30% of the premium (backtest.plan_risk - no 12.5% cap), ONE target at 2R (no 1.5R-10R ladder), no premium Open = Low stop, no contract veto.
    old_rules = filter_set(c) == "OLD FILT"
    if not old_rules:
        risk_u = min(risk_u, float(cfg.get("premSlPct", PREM_SL_PCT)) * ct["premium"] / 0.5)
    if c.get("key") == EAGLE:                           # Eagle: a fixed 5-point premium stop; 1R = 5 premium points = 10 underlying points at delta 0.5, so the whole ladder follows
        p0, o0 = float(ct["premium"]), float(ct.get("pOpen") or 0)
        if o0 >= 5 and (p0 > o0 * (1 + EAGLE_OPEN_TOL) or p0 < o0 - EAGLE_DIP_PTS):
            raise RuntimeError(f"skipped: Eagle buys at the option's open price or up to {EAGLE_DIP_PTS:.0f} points below it (open {o0:.2f}, now {p0:.2f})")
        if EAGLE_STOP_PTS <= 0.35 * p0:                  # on a very cheap option 5 points is more than 35% of the premium: it keeps the percentage stop
            risk_u = min(risk_u, EAGLE_STOP_PTS / 0.5)
    stop_u = entry_u - d * risk_u
    tgts = [round(entry_u + d * r * risk_u, 2) for r in TARGET_LADDER] if (variant == "fixed" and not old_rules) else None     # T1..T7 on the underlying
    target_u = tgts[-1] if tgts else (entry_u + d * backtest.TARGET_R * risk_u if (old_rules and variant == "fixed") else None)   # the last one (10R) ends the trade; old rules: one 2R target
    sl_name = _sleeve_of(c)
    sl_eq = _sleeve_equity(st, sl_name)
    base_eq = sl_eq if sl_eq else _equity(st)                # a sleeve sizes its own trades (risk % and the 20% position cap)
    budget = base_eq * cfg["riskPct"] / 100
    pair = cfg.get("pairSell", WRITE_PAIR)
    if pair:
        budget /= 2                                          # the paired sell takes the other half of the risk budget
    per_lot = ct["lot"] * 0.5 * risk_u
    lots = max(1, int(budget // per_lot)) if per_lot > 0 else 1
    lots = 1                                                 # 30 Oct (user): every auto entry (OLD FILT and NEW IND) takes exactly 1 lot - the risk-budget sizing above is bypassed
    max_out = base_eq * 0.2
    while lots > 1 and lots * ct["lot"] * ct["premium"] > max_out:
        lots -= 1
    while cap and lots > 1 and lots * ct["lot"] * ct["premium"] > cap:       # per-symbol premium budget (Bank Nifty 15k)
        lots -= 1
    if sl_eq:                                                # never spend more premium than the sleeve has free
        free = sl_eq - _sleeve_deployed(st, sl_name)
        while lots > 1 and lots * ct["lot"] * ct["premium"] > free:
            lots -= 1
        if lots * ct["lot"] * ct["premium"] > free:
            raise RuntimeError(f"skipped: {SLEEVE_NAMES[sl_name]} sleeve is full (Rs {max(0, free):,.0f} free of Rs {sl_eq:,.0f})")
    t = {
        "id": f"A-{today.replace('-', '')}-{len([x for x in st['trades'] if x['date'] == today]) + 1}",
        "date": today, "openedAt": _now().isoformat(), "sym": c["sym"], "kind": c["kind"], "side": c["side"],
        "opt": "CE" if c["side"] == "BUY" else "PE", "strike": ct["strike"], "expiry": ct["expiry"], "key": ct["key"],
        "lot": ct["lot"], "lots": lots, "entry": round(ct["premium"], 2), "entryU": round(entry_u, 2),
        "stopU": round(stop_u, 2), "targetU": round(target_u, 2) if target_u is not None else None, "riskU": round(risk_u, 2),
        **({"tgts": tgts, "tHit": 0} if tgts else {}),
        "variant": variant, "filter": c.get("filter", "none"), "bestU": round(entry_u, 2), "mode": c.get("label", ""),
        "initialRisk": round(min(lots * per_lot, lots * ct["lot"] * ct["premium"]), 0), "riskBudget": round(budget, 0),
        "strategy": c["key"], "sleeve": sl_name, "agree": c.get("agree", 1), **({"why": c["why"]} if c.get("why") else {}),
        "screenAgrees": c.get("screenAgrees"), "indicators": c.get("strategies") or [c["key"]],
        "source": c.get("source", f"{c.get('agree', 1)} indicator(s) agree" if c.get("strategies") else "strategy signal"), "status": "OPEN", "last": round(ct["premium"], 2),
        "plan": "v2", **_premium_plan(round(ct["premium"], 2), risk_u),
        "fset": filter_set(c),
    }
    oel = None if old_rules else premium_oel(ct)
    if oel:                                                  # the bought option opened at its day low: its own point stop, when that is tighter than the normal one
        t["premSig"] = "Open = Low" if oel[0] == "clean" else "Open = Low (within 10 pts)"
        sl_ = _oel_stop(t["entry"], oel[1])
        if sl_ > float(t.get("premSL") or 0):
            t["premSL"] = sl_
    st["trades"].append(t)
    st["log"].append({"at": _now().isoformat(), "msg": f"ENTER {t['sym']} {t['strike']:.0f}{t['opt']} x{lots} @ {t['entry']} [{c['key']} · {variant}]{' · premium ' + t['premSig'] if t.get('premSig') else ''}"})
    if pair:
        if _mins(_now()) < SELL_FROM:
            t["writePending"] = True          # option SELL legs wait until 09:20 (user rule); buys go at 09:16
            st["log"].append({"at": _now().isoformat(), "msg": f"paired sell for {t['id']} deferred - option selling starts at 09:20"})
        else:
            try:
                _open_short(st, c, today, t)
            except Exception as e:
                st["log"].append({"at": _now().isoformat(), "msg": f"no paired sell for {c['sym']}: {str(e)[:80]}"})
    return t


WRITE_PAIR = True        # user: every entry also SELLS the opposite option (bullish: buy CE + sell PE, bearish: buy PE + sell CE)
WRITE_SL_CAP = 0.35      # small premium stop on the sold option: at most +35% of the premium received
WRITE_MARGIN_PCT = 0.12  # paper margin per unit sold: max(12% of spot, premium)

# Z Trend taken as a HEDGED credit spread (so its accuracy can be judged separately from the naked premium buys):
# sell the OTM strike ~1.5 expected moves away on the trend's side, buy the hedge 2 strikes further out.
HEDGE_K, HEDGE_W, HEDGE_MIN_RATIO = 1.5, 2, 0.25
SPREAD_STOP_X, SPREAD_T1_KEEP = 2.0, 0.5     # exit when the spread is worth 2x the credit, or at 50% of the credit banked


def _expected_move(sym, sessions, spot):
    """Daily expected move from India VIX (same math as the Hedged Seller card)."""
    try:
        import market_api
        k = market_api._key("INDIAVIX")
        vix = _last(_quotes({k}).get(k)) or 15.0
    except Exception:
        vix = 15.0
    return spot * (vix / 100) * (max(1, sessions) / 252) ** 0.5


def _open_rzt_hedge(st, c, today):
    """A Z Trend flip opened as a credit spread: two linked paper trades (short leg + hedge leg) that
    are managed as ONE position - the spread's value decides the exit, not each leg on its own."""
    import market_api
    if _mins(_now()) < SELL_FROM:                        # selling is a 09:20+ activity, same rule as the paired shorts
        raise RuntimeError("option selling starts at 09:20")
    ch = market_api.chain(c["sym"], "")
    if ch.get("expiry") and (date.fromisoformat(ch["expiry"]) - date.fromisoformat(today)).days <= 1:
        # expiry day / the day before: the spread would be closed as SPREAD-EXPIRY by the next cycle - use the next expiry
        nxt = next((e for e in ch.get("expiries") or [] if (date.fromisoformat(e) - date.fromisoformat(today)).days >= 2), None)
        if not nxt:
            raise RuntimeError("only an expiring contract - no spread")
        ch = market_api.chain(c["sym"], nxt)
    rows = [r for r in ch.get("rows") or [] if (r.get("ce") or {}).get("key") and (r.get("pe") or {}).get("key")]
    spot = float(ch.get("spot") or 0)
    if len(rows) < 4 or spot <= 0:
        raise RuntimeError("no chain")
    exp_days = max(1, (date.fromisoformat(ch["expiry"]) - date.fromisoformat(today)).days)
    em = _expected_move(c["sym"], exp_days, spot) * HEDGE_K
    side = c["side"]                                     # SELL trend -> bear call spread; BUY trend -> bull put spread
    opt = "CE" if side == "SELL" else "PE"
    strikes = [r["strike"] for r in rows]
    step = min((b - a for a, b in zip(strikes, strikes[1:]) if b > a), default=50.0)
    if side == "SELL":
        pool = sorted([r for r in rows if r["strike"] >= spot], key=lambda r: r["strike"])
    else:
        pool = sorted([r for r in rows if r["strike"] <= spot], key=lambda r: -r["strike"])
    short_r = next((r for r in pool if 0.35 * em <= abs(r["strike"] - spot) <= em), None)
    if short_r is None:
        raise RuntimeError("no strike near the expected move")
    si = strikes.index(short_r["strike"])
    hi = min(si + HEDGE_W, len(rows) - 1)
    if hi - si < 1:
        raise RuntimeError("no room for the hedge")
    hedge_r = rows[hi]
    sl_, hl_ = short_r.get("ce" if side == "SELL" else "pe") or {}, hedge_r.get("ce" if side == "SELL" else "pe") or {}
    sell_px = float(sl_.get("bid") or 0) or float(sl_.get("ltp") or 0)
    buy_px = float(hl_.get("ask") or 0) or float(hl_.get("ltp") or 0)
    width = (hedge_r["strike"] - short_r["strike"]) if side == "SELL" else (short_r["strike"] - hedge_r["strike"])
    credit = round(sell_px - buy_px, 2)
    if credit <= 0 or width <= 0:
        raise RuntimeError(f"no credit (sell {sell_px:.2f} / hedge {buy_px:.2f})")
    if sell_px < HEDGE_MIN_RATIO * width:
        raise RuntimeError(f"strike pays {sell_px:.1f} of the {width:.0f} width (< {int(HEDGE_MIN_RATIO * 100)}%) - skip")
    max_loss_u = round(width - credit, 2)
    budget = _equity(st) * st["cfg"]["riskPct"] / 100
    lot = int(ch.get("lot") or 1)
    lots = max(1, int(budget // max(1.0, lot * max_loss_u))) if max_loss_u > 0 else 1
    while lots > 1 and lots * lot * (sell_px + buy_px) > _equity(st) * 0.2:
        lots -= 1
    qty = lots * lot
    now = _now().isoformat()
    n_today = len([x for x in st["trades"] if x["date"] == today])
    base = {"date": today, "sym": c["sym"], "kind": "index", "side": side, "opt": opt, "lot": lot, "lots": lots,
            "expiry": ch["expiry"], "variant": "spread", "plan": "v2", "filter": "none", "strategy": "rzt-hedge",
            "indicators": ["Z Trend", "Hedged Seller"], "status": "OPEN", "mode": "Z Trend hedge",
            "source": c.get("source") or "Z Trend hedged credit spread"}
    t1 = dict(base, id=f"A-{today.replace('-', '')}-{n_today + 1}-H", pos="short", strike=short_r["strike"], key=sl_.get("key"),
              entry=round(sell_px, 2), last=round(sell_px, 2), creditU=credit,
              spreadStop=round(SPREAD_STOP_X * credit, 2), spreadT1=round(SPREAD_T1_KEEP * credit, 2),
              spreadW=round(width, 2), maxLossU=max_loss_u, openedAt=now,
              initialRisk=round(qty * max_loss_u / 2, 0), riskBudget=round(budget, 0))
    t2 = dict(base, id=t1["id"] + "-X", pos="long", pairOf=t1["id"], strike=hedge_r["strike"], key=hl_.get("key"),
              entry=round(buy_px, 2), last=round(buy_px, 2), openedAt=now, initialRisk=round(qty * max_loss_u / 2, 0))
    t1["hedgeId"] = t2["id"]
    st["trades"].append(t1)
    st["trades"].append(t2)
    st["log"].append({"at": now, "msg": f"SELL SPREAD {c['sym']} {t1['strike']:.0f}{opt} / +{t2['strike']:.0f}{opt} x{lots} · "
                                        f"credit {credit:.2f} · max loss {max_loss_u:.2f}/unit [Z Trend {side} → hedge]"})
    _push(f"auto|{t1['id']}", f"PAPER SELL SPREAD · {c['sym']} {t1['strike']:.0f}/{t2['strike']:.0f} {opt}",
          f"Z Trend {side} → hedged credit spread · {lots} lot(s) · credit ₹{credit:.2f} · max loss ₹{max_loss_u:.2f}/unit · "
          f"exit at {SPREAD_STOP_X:.0f}x credit or banking {int(SPREAD_T1_KEEP * 100)}% of it")
    return t1


def _open_short(st, c, today, main):
    """Paired option SELL in the same direction as the signal, held to the same underlying stop / target."""
    if _mins(_now()) < SELL_FROM:
        raise RuntimeError("option selling starts at 09:20")
    cfg = st["cfg"]
    opp = "SELL" if c["side"] == "BUY" else "BUY"               # the leg on the other side of the chain
    ct = _contract(c["sym"], opp, today, cfg["minDaysToExpiry"])
    px = ct["bid"] if ct.get("bid", 0) > 0 else (ct.get("ltp") or ct["premium"])   # we sell at the bid
    if px <= 0:
        raise RuntimeError("no bid")
    rp = round(min(0.5 * main["riskU"], WRITE_SL_CAP * px), 2)  # premium risk per unit (small SL)
    if rp <= 0:
        raise RuntimeError("no valid stop")
    spot = ct["spot"] or main["entryU"]
    margin_u = max(WRITE_MARGIN_PCT * spot, px)
    lots = main["lots"]
    while lots > 1 and lots * ct["lot"] * margin_u > _equity(st) * 0.2:
        lots -= 1
    half = _equity(st) * cfg["riskPct"] / 100 / 2              # this leg's half of the per-trade risk budget
    while lots > 1 and lots * ct["lot"] * rp > half:
        lots -= 1
    if lots * ct["lot"] * rp > half:                            # even 1 lot risks more: tighten the premium stop to fit
        rp = round(max(0.05, half / (lots * ct["lot"])), 2)
    qty = lots * ct["lot"]
    t = dict(main)
    t.update({"id": main["id"] + "-W", "pos": "short", "pairOf": main["id"], "opt": "PE" if c["side"] == "BUY" else "CE",
              "strike": ct["strike"], "expiry": ct["expiry"], "key": ct["key"], "lot": ct["lot"], "lots": lots,
              "entry": round(px, 2), "last": round(px, 2), "premRisk": rp, "premSL": round(px + rp, 2),
              "premT": [round(max(0.05, px - k * rp), 2) for k in (1, 2, 3)], "initialRisk": round(qty * rp, 0),
              "margin": round(qty * margin_u, 0), "openedAt": _now().isoformat(), "status": "OPEN"})
    for k in ("lock", "bestPnl", "stopMoved", "tsl", "baseDate", "basePx"):
        t.pop(k, None)
    st["trades"].append(t)
    st["log"].append({"at": _now().isoformat(), "msg": f"SELL {t['sym']} {t['strike']:.0f}{t['opt']} x{lots} @ {t['entry']} (paired with {main['id']}, SL {t['premSL']})"})
    return t


def _close(st, t, px, why):
    qty = t["lots"] * t["lot"]
    if not (px and px > 0):                  # a missing price must never book as 0: a sold option "bought back" at 0 showed its whole premium as profit
        px = float(t.get("last") or 0) or float(t["entry"])
    gross = (px - t["entry"]) * qty * (-1 if t.get("pos") == "short" else 1)      # a sold option gains when the premium falls
    cost = t.get("costPct", st["cfg"]["costPct"]) / 100 * (t["entry"] + px) * qty
    t.update(status="CLOSED", exit=round(px, 2), exitReason=why, closedAt=_now().isoformat(), gross=round(gross, 2),
             cost=round(cost, 2), net=round(gross - cost, 2),
             R=round((gross - cost) / t["initialRisk"], 2) if t.get("initialRisk") else None, last=round(px, 2))
    st["log"].append({"at": _now().isoformat(), "msg": f"EXIT {t['sym']} {t['strike']:.0f}{t['opt']} @ {px:.2f} ({why}) net {t['net']:+.0f}"})
    kind = None                                      # exits are not pushed (user: only 5 trade pushes a day) - they stay in the journal
    if kind:                                         # phone pushes: only take profit / stop loss (entries, locks, time exits stay in the journal)
        _push(f"auto-exit|{t['id']}", f"{kind} · {t['sym']} {t['strike']:.0f} {t['opt']}",
              f"Exit @ ₹{px:.2f} (entry ₹{t['entry']}) · net {'+' if t['net'] >= 0 else '−'}₹{abs(t['net']):,.0f}")


def _push(idem, title, body, kind="trade"):
    try:
        import push_signals
        push_signals.notify_all(idem, title, body, url="/#journal", kind=kind)
    except Exception as e:
        print(f"[auto] notify failed: {e}")


def manage(st, now, t_end=None):
    import market_api
    opens = [t for t in st["trades"] if t["status"] == "OPEN"]
    if not opens:
        return
    # paired option SELL legs that were deferred before 09:20 go on now (user rule: selling starts at 09:20)
    if _mins(now) >= SELL_FROM and st["cfg"].get("pairSell", WRITE_PAIR):
        for t in [x for x in opens if x.get("writePending") and not x.get("pairOf")]:
            if t_end and time.time() > t_end:
                break                                         # out of time this cycle - the rest go on in the next one
            try:
                _open_short(st, {"sym": t["sym"], "side": t["side"]}, now.date().isoformat(), t)
                t.pop("writePending", None)
            except Exception as e:
                if "09:20" in str(e):
                    break                                     # not yet 09:20 by the exchange clock - keep waiting
                st["log"].append({"at": now.isoformat(), "msg": f"no paired sell for {t['sym']}: {str(e)[:80]}"})
                t.pop("writePending", None)                   # one honest try per cycle - do not retry forever
    keys = {t["key"] for t in opens} | {market_api._key(t["sym"]) for t in opens}
    try:
        q = _quotes(keys)
    except Exception as e:
        print(f"[auto] quote failure: {e}")
        return
    today = now.date().isoformat()
    for t in opens:
        _replan(t)
        _day_base(t, today)
    for t in opens:
        if t.get("expiry") and t["expiry"] < today:          # contract already expired (missed while the store was down): no quote any more
            _close(st, t, float(t.get("last") or t["entry"]), "EXPIRY (late)")
            continue
        opt_q, und_q = q.get(t["key"]), q.get(market_api._key(t["sym"]))
        opt_px, und_px = _last(opt_q), _last(und_q)
        if opt_px > 0:
            t["last"] = round(opt_px, 2)
            t["lastAt"] = _now().isoformat()          # when this price was seen: the Journal never swaps a newer price for an older one
        bid =float((((opt_q or {}).get("depth") or {}).get("buy") or [{}])[0].get("price") or 0)
        ask = float((((opt_q or {}).get("depth") or {}).get("sell") or [{}])[0].get("price") or 0)
        short = t.get("pos") == "short"
        exit_px = (ask if ask > 0 else opt_px) if short else (bid if bid > 0 else opt_px)   # a short is bought back at the ask
        if bid > 0 and ask > 0 and (ask - bid) / ask > 0.10 and opt_px > 0:
            exit_px = opt_px                       # a gaping book (opening minutes, one-sided quote) is not a price anyone could trade at: judge the stop on the last traded price
        if exit_px > 0:
            t["mark"] = round(exit_px, 2)          # the same price drives the stop AND the running P&L the Journal shows (they used to disagree)
        if exit_px <= 0 or und_px <= 0:
            continue
        d = 1 if t["side"] == "BUY" else -1
        why = None
        variant = t.get("variant", "fixed")
        if variant == "spread":
            continue                             # a hedged credit spread is ONE position - the pair is managed below on the spread's value
        if variant == "trail":                       # the stop trails the best underlying price since entry by the same distance
            t["bestU"] = max(t.get("bestU", t["entryU"]), und_px) if d > 0 else min(t.get("bestU", t["entryU"]), und_px)
            t["stopU"] = round(max(t["stopU"], t["bestU"] - t["riskU"]) if d > 0 else min(t["stopU"], t["bestU"] + t["riskU"]), 2)
        tsl = t.get("tsl")
        if tsl and tsl.get("mode") in ("trail", "breakeven", "step"):
            best = t.get("bestU", t["entryU"])
            best = max(best, und_px) if d > 0 else min(best, und_px)
            t["bestU"] = round(best, 2)
            fav = d * (best - t["entryU"])
            ns = None
            if tsl["mode"] == "trail" and tsl.get("trail"):
                ns = best - d * float(tsl["trail"])
            elif tsl["mode"] == "breakeven":
                if fav >= float(tsl.get("trigger") or 1.0) * t["riskU"]:
                    ns = t["entryU"]
            elif tsl["mode"] == "step" and tsl.get("step"):
                k = math.floor(fav / float(tsl["step"]))
                if k >= 1:
                    ns = t["entryU"] + d * (k - 1) * float(tsl["step"])        # one full step of cushion is kept
            if ns is not None:
                new = max(t["stopU"], ns) if d > 0 else min(t["stopU"], ns)    # never loosen
                if new != t["stopU"]:
                    t["stopU"] = round(new, 2)
                    t["stopMoved"] = _now().isoformat()
        tg = t.get("tgts")
        if tg and variant == "fixed" and not short:        # target ladder: each target reached moves the stop up (T1 -> breakeven, then one target behind)
            n0 = n = int(t.get("tHit") or 0)
            while n < len(tg) and d * (und_px - tg[n]) >= 0:
                n += 1
            if n > n0:
                t["tHit"] = n
                ns = t["entryU"] if n == 1 else tg[n - 2]
                new = max(t["stopU"], ns) if d > 0 else min(t["stopU"], ns)
                if new != t["stopU"]:
                    t["stopU"] = round(new, 2)
                    t["stopMoved"] = _now().isoformat()
                st["log"].append({"at": _now().isoformat(), "msg": f"T{n} reached on {t['sym']} {t['strike']:.0f}{t['opt']} ({TARGET_LADDER[n - 1]}R) - stop moved to {t['stopU']}"})
        if not tg or t.get("strategy") == EAGLE:            # Eagle also gets the premium lock (breakeven at Rs 1,500, trailing from Rs 2,000); other ladder trades trail on the underlying; the old rupee profit lock is for trades opened before it
            _profit_lock(t, opt_px if opt_px > 0 else exit_px, st["cfg"].get("lockMode", "old"))
        hold = st["cfg"]["maxHoldSessions"] if variant == "fixed" else 40
        if t.get("premSL") and (exit_px >= t["premSL"] if short else exit_px <= t["premSL"]):
            why = "TSL" if t.get("lock") else "STOP"   # option premium stop (30% cap) - catches time decay too
            sl_ = float(t["premSL"])                   # a stop order fills AT the stop when the market only just crossed it ...
            beyond = exit_px > sl_ * (1 + STOP_GAP_TOL) if short else exit_px < sl_ * (1 - STOP_GAP_TOL)
            exit_px = exit_px if beyond else sl_       # ... but at the price actually seen when it is well past it (a gap): never a better fill than the market gave
        elif d * (und_px - t["stopU"]) <= 0:
            why = "TSL" if ((tsl and tsl.get("mode") in ("trail", "breakeven", "step") and t.get("stopMoved")) or t.get("tHit")) else "STOP"
        elif t.get("targetU") is not None and d * (und_px - t["targetU"]) >= 0:
            why = "TARGET"
        elif (date.fromisoformat(t["expiry"]) - date.fromisoformat(today)).days <= 1:
            why = "EXPIRY"
        elif _sessions_between(t["date"], today) >= hold:
            why = "TIME"
        elif variant == "reverse" and t["date"] < today and _reversed(t, today):
            why = "REVERSE"
        if why:
            _close(st, t, exit_px, why)
    # hedged credit spreads (variant "spread"): the PAIR is the position - exit when the spread's value
    # hits its stop (2x credit), banks the target share of the credit, or the expiry is a day away.
    for main in [t for t in st["trades"] if t["status"] == "OPEN" and t.get("variant") == "spread" and not t.get("pairOf")]:
        hedge = next((x for x in st["trades"] if x["id"] == main.get("hedgeId") and x["status"] == "OPEN"), None)
        if not hedge:
            continue
        s1, s2 = float(main.get("last") or 0), float(hedge.get("last") or 0)
        credit = float(main.get("creditU") or 0)
        if s1 <= 0 or s2 <= 0 or credit <= 0:
            continue
        spread = s1 - s2
        if (date.fromisoformat(main["expiry"]) - date.fromisoformat(today)).days <= 1:
            _close(st, main, s1, "SPREAD-EXPIRY"); _close(st, hedge, s2, "SPREAD-EXPIRY")
        elif spread >= float(main.get("spreadStop") or 10 ** 9):
            _close(st, main, s1, "SPREAD-STOP"); _close(st, hedge, s2, "SPREAD-STOP")
        elif spread <= float(main.get("spreadT1") or -1):
            _close(st, main, s1, "SPREAD-T1"); _close(st, hedge, s2, "SPREAD-T1")


LOCK_BE, LOCK_TRAIL, LOCK_KEEP = 2500.0, 3500.0, 0.4          # "new" lock (from 26 Oct)
# "old" lock (21-25 Oct, the one with the better R:R): breakeven at Rs 1,500 profit, trail from Rs 2,000 keeping 50% (60% from 4k, 70% from 6k)
LOCKS = {"old": (1500.0, 2000.0, 0.5, ((6000.0, 0.7), (4000.0, 0.6))),
         "new": (LOCK_BE, LOCK_TRAIL, LOCK_KEEP, ((10000.0, 0.65), (6000.0, 0.5)))}


def _profit_lock(t, px, mode="old"):
    """Auto profit lock on the option premium: at Rs 2,500 open profit the premium stop moves to entry + charges
    (breakeven); from Rs 3,500 it trails, keeping 40% of the best profit seen (50% from Rs 6,000, 65% from Rs 10,000).
    Only ever tightens."""
    qty = (t.get("lots") or 0) * (t.get("lot") or 0)
    if not (px and px > 0 and qty > 0):
        return
    sgn = -1 if t.get("pos") == "short" else 1
    pnl = sgn * (px - t["entry"]) * qty
    best = max(float(t.get("bestPnl") or 0.0), pnl)
    t["bestPnl"] = round(best, 2)
    be, trail, base, steps = LOCKS.get(mode) or LOCKS["old"]
    if best < be:
        return
    fee_u = 80.0 / qty                                  # ~ two option legs of brokerage + taxes per lot set
    frac = next((f for lvl, f in steps if best >= lvl), base)
    keep = frac * best if best >= trail else 0.0
    stop = round(t["entry"] + sgn * (fee_u + keep / qty), 2)
    cur = float(t.get("premSL") or 0)
    if (stop > cur) if sgn > 0 else (cur <= 0 or stop < cur):     # only ever tightens (down for a sold option)
        first = not t.get("lock") or (keep and t["lock"].get("mode") != "trail")
        t["premSL"] = stop
        t["lock"] = {"mode": "trail" if keep else "breakeven", "keep": round(keep), "best": round(best), "at": _now().isoformat()}
        t["stopMoved"] = _now().isoformat()
        if first and PUSH_LOCKS:
            _push(f"auto-lock|{t.get('id')}|{t['lock']['mode']}", f"PROFIT LOCKED · {t.get('sym')} {t.get('strike', 0):.0f} {t.get('opt', '')}",
                  f"Profit ₹{best:,.0f} - stop moved to ₹{stop:.2f} ({'keeps ₹' + format(round(keep), ',') if keep else 'breakeven'})", kind="lock")


def _reversed(t, today):
    """True when the strategy's last completed signal is now the opposite of this trade's side."""
    try:
        import backtest
        rows = backtest._runners()[t["strategy"]](t["sym"], 400).get("bars") or []
        rows = [r for r in rows if r.get("date") and t["date"] < r["date"] < today]
        for r in reversed(rows):
            sg = backtest.norm_signal(r.get("signal"))
            if sg:
                return sg != t["side"]
    except Exception:
        pass
    return False


def _prewarm_scan(now):
    """08:30-09:15 on a trading day: run the once-a-day indicator scan (completed daily bars only - nothing intraday, no trade) so that it is
    finished when the session opens. On Vercel one call may only spend ~8 s on it and it used to start at 09:15, so the first cycles of the day saw
    only 65 of ~220 stocks and the rest trickled in over later cycles - signals on the other stocks were taken late or missed."""
    if not shared_cache.lock("auto-prewarm", 20):
        return {"ran": False, "reason": "market closed (pre-open scan already running)"}
    try:
        with _lock:
            st = _load()
            if not st["cfg"].get("enabled", True):
                return {"ran": False, "reason": "auto trader is switched off"}
            _, note = scan_all(st, now.date().isoformat())
            _save(st)
        return {"ran": False, "reason": "market closed", "preOpenScan": note}
    except Exception as e:
        return {"ran": False, "reason": "market closed", "preOpenScan": f"failed: {str(e)[:80]}"}
    finally:
        shared_cache.unlock("auto-prewarm")


def run_cycle(force=False, dry=False):
    run_cycle._last_ran = time.time()
    now = _now()
    if not force and not dry:                       # closed market: no lock, no state read - zero Upstash commands
        import nse_calendar
        if not nse_calendar.session_open(now):
            if nse_calendar.is_trading_day(now.date()) and 8 * 60 + 30 <= _mins(now) < 9 * 60 + 15:
                return _prewarm_scan(now)               # before the open: read the indicators of every stock now, so 09:15 starts with all of them
            return {"ran": False, "reason": "market closed"}
    if not dry and not shared_cache.lock("auto-cycle", 30):
        return {"ran": False, "reason": "another cycle is already running"}
    try:
        return _run_cycle(now, force, dry)
    finally:
        if not dry:
            shared_cache.unlock("auto-cycle")
            try:                                   # the stock paper trader rides on the same schedule (if this call still has time)
                import stock_trader
                if time.time() - run_cycle._last_ran < CYCLE_BUDGET:
                    stock_trader.run_cycle()
            except Exception as e:
                print(f"[stockbot] cycle failed: {e}")


_MARK_AT = 0.0


def mark_open_positions(min_gap=120):
    """Mark the open positions to market and run their exit checks (stop, target, trailing stop, expiry, time).
    Server-side scheduling is not available on Vercel (the 5-minute cycle only runs while a browser tab with notifications on is
    open), so positions used to keep their entry price - P&L frozen at 0, stops never checked - until that happened. The status
    read now does this itself, at most once per `min_gap` seconds across all instances, only in market hours, and never while a
    full cycle is running (they share a lock). Returns True when it ran."""
    global _MARK_AT
    if time.time() - _MARK_AT < min_gap:
        return False
    import nse_calendar
    now = _now()
    if not nse_calendar.session_open(now):
        return False
    if not shared_cache.lock("auto-cycle", 20):
        return False
    try:
        with _lock:
            st = _load()
            if not any(t["status"] == "OPEN" for t in st["trades"]):
                return False
            _MARK_AT = time.time()
            manage(st, now)
            return _save(st) is True
    finally:
        shared_cache.unlock("auto-cycle")


def _run_cycle(now, force, dry):
    t0 = time.time()
    with _lock:
        st = _load()
        cfg = st["cfg"]
        rep = {"ran": True, "dry": dry, "entered": [], "closed": [], "note": None}
        if not cfg["enabled"] and not dry:
            return {"ran": False, "reason": "auto trader is switched off"}
        import nse_calendar
        is_open = nse_calendar.session_open(now)
        if not is_open and (not force or not nse_calendar.is_trading_day(now.date())):
            return {"ran": False, "reason": "market closed" + (f" ({nse_calendar.holiday(now.date())})" if nse_calendar.holiday(now.date()) else "")}
        before = {t["id"] for t in st["trades"] if t["status"] == "CLOSED"}
        if not dry:
            manage(st, now, t0 + CYCLE_BUDGET * 0.5)
        rep["closed"] = [t["id"] for t in st["trades"] if t["status"] == "CLOSED" and t["id"] not in before]
        if not dry:
            try:
                shadow_resolve(st, now)
            except Exception as e:
                st["log"].append({"at": now.isoformat(), "msg": f"shadow check failed: {str(e)[:80]}"})
        today = now.date().isoformat()
        in_window = _hm(cfg["windowStart"]) <= _mins(now) <= _hm(cfg["lastEntry"])
        todays = [t for t in st["trades"] if t["date"] == today]
        guard, note = _day_guard(st, today)
        if note:
            rep["dayGuard"] = note
        if note and st.get("dayGuardMode") != guard:
            st["log"].append({"at": now.isoformat(), "msg": note})
        st["dayGuardMode"] = guard
        entries, tried = [], set()
        pend_notify = []                      # entry pushes wait until the book is saved: a rejected save used to leave a push for a trade that did not exist
        if (in_window or force) and guard != "blocked" and len(todays) < _cap(cfg, "maxPerDay"):
            cands, why = scan_all(st, today)
            rep["note"] = why
            chosen = choose(cands, st, today)
            if guard == "soft":                       # fewer, better trades near the day P&L limit
                strong = [c for c in chosen if c.get("agree", 1) >= 3]
                if strong:
                    chosen = strong
                    rep["note"] = (rep["note"] + " · " if rep["note"] else "") + f"soft zone: {len(strong)} high-conviction signal(s) only"
                else:
                    chosen = []
            try:                                      # Z Trend (intraday) flips join the daily-bar signals
                import rzt as rzt_mod
                seen = {c["sym"] for c in chosen} | _taken_syms(st, today)
                room = max(0, _cap(cfg, "maxPerDay") - len(todays) - len(chosen))
                extra = [c for c in rzt_mod.intraday_cands() if c["sym"] not in seen]
                if guard == "soft":
                    extra = extra[:1]
                if cfg.get("zTrendHedge", True):
                    extra = [dict(c, key="rzt-hedge", source=(c.get("source") or "") + " · hedged credit spread") for c in extra]
                chosen = chosen + extra[:room]
                if extra:
                    rep["note"] = (rep["note"] + " · " if rep["note"] else "") + f"{len(extra)} Z Trend intraday flip(s)"
            except Exception as e:
                st["log"].append({"at": now.isoformat(), "msg": f"rzt intraday failed: {str(e)[:80]}"})
            try:                                      # Gann time cycle: price AT a zone AT a cycle time, with the zone as stop
                tc_extra = _ztc_cands(now) + _timecycle_cands(now)
                _seen_tc = set()
                tc_extra = [c for c in tc_extra if not (c["sym"] in _seen_tc or _seen_tc.add(c["sym"]))]        # one trigger per symbol (the confluence one wins)
                # not just this cycle's picks: a symbol already traded / open today must not be bought again on every cycle
                # while its time-cycle trigger stays active (BANKNIFTY went in 3 times in 3 minutes)
                tseen = {c["sym"] for c in chosen} | _taken_syms(st, today)
                troom = max(0, _cap(cfg, "maxPerDay") - len(todays) - len(chosen))
                chosen = chosen + [c for c in tc_extra if c["sym"] not in tseen][:troom]
                if tc_extra:
                    rep["note"] = (rep["note"] + " · " if rep["note"] else "") + f"{len(tc_extra)} time-cycle trigger(s)"
            except Exception as e:
                st["log"].append({"at": now.isoformat(), "msg": f"timecycle trigger failed: {str(e)[:80]}"})
            try:                                      # Gann time-price angle bounce (chart indicator "Gann", user 28 Oct)
                if cfg.get("gannOn", True):
                    gseen = {c["sym"] for c in chosen} | _taken_syms(st, today)
                    g_extra = _gann_cands(now, gseen)
                    groom = max(0, _cap(cfg, "maxPerDay") - len(todays) - len(chosen))
                    chosen = chosen + [c for c in g_extra if c["sym"] not in gseen][:groom]
                    if g_extra:
                        rep["note"] = (rep["note"] + " · " if rep["note"] else "") + f"{len(g_extra)} Gann-angle trigger(s)"
            except Exception as e:
                st["log"].append({"at": now.isoformat(), "msg": f"gann angle failed: {str(e)[:80]}"})
            try:                                      # Premium Rider (option premium support bounce / heavy selling + volume surge): paper-tracked for the testing week
                import premium_rider
                pr = premium_rider.scan()
                if pr.get("signals"):
                    shadow_record_premium(st, pr["signals"], now)
                    rep["note"] = (rep["note"] + " · " if rep["note"] else "") + f"{len(pr['signals'])} premium-rider signal(s) (paper)"
            except Exception as e:
                st["log"].append({"at": now.isoformat(), "msg": f"premium rider failed: {str(e)[:80]}"})
            filled = []
            if cfg.get("fillSlots", True) and time.time() >= max(st.get("fillBackoff", 0), st.get("fillNext", 0)):
                st["fillNext"] = time.time() + FILL_EVERY          # live screens every 3 minutes (each costs ~40 Upstox calls)
                filled = fill_slots(st, today, chosen)
                if any("rate-limiting" in (l.get("msg") or "") or "budget" in (l.get("msg") or "") for l in st["log"][-2:]):
                    st["fillBackoff"] = time.time() + 600        # Upstox pushed back: leave it alone for 10 minutes
            # No limit on the day - only the opening burst is capped: in the first minute of the entry window (09:16) at most
            # `openBurstCap` (12) entries are taken (paired hedge legs -W belong to their entry and do not count). Best-ranked
            # first; the rest are picked up by the following cycles as normal.
            # Screen candidates (index call/put, stock screen) exist only in the cycle that ran the 3-minute screen. When that cycle ran out of
            # time (or the opening cap) the rest were simply lost until the next screen - and index ones rank below the stock entries, so they
            # were the ones lost. Whatever was not tried is kept for CARRY_FOR seconds and offered again in the next cycles.
            try:
                busy_ = _taken_syms(st, today)
                have_ = {(c["sym"], c["side"]) for c in chosen + filled}
                back = [c for c in (st.get("carry") or []) if c.get("_exp", 0) > time.time() and c["sym"] not in busy_ and (c["sym"], c["side"]) not in have_]
                if back:
                    filled = filled + back
                    rep["note"] = (rep["note"] + " · " if rep["note"] else "") + f"{len(back)} screen candidate(s) carried over from the last cycle"
                st["carry"] = []
            except Exception:
                st["carry"] = []
            try:
                eagles = eagle_cands(st, today, {c["sym"] for c in chosen + filled if c.get("key") == EAGLE}) if cfg.get("eagleOn", False) else []   # Eagle is on by default since 28 Oct (setting "eagleOn"); buy-only like the rest
            except Exception as e:
                eagles = []
                st["log"].append({"at": now.isoformat(), "msg": f"eagle scan failed: {str(e)[:80]}"})
            if eagles:
                have = {c["sym"] for c in eagles}
                chosen, filled = [c for c in chosen if c["sym"] not in have], [c for c in filled if c["sym"] not in have]
                rep["note"] = (rep["note"] + " · " if rep["note"] else "") + f"{len(eagles)} Eagle trade(s)"
            entries = sorted(eagles + chosen + filled, key=lambda c: (c.get("kind") != "index", -(c.get("rank", c.get("score")) or 0)))   # indices first (there are at most five; they ranked below every stock entry and were never reached)
            try:                                                              # premium Open = Low / High (user 29 Oct): trades whose option opened at its day low go first
                from concurrent.futures import ThreadPoolExecutor
                scan = [c for c in entries[:16] if c.get("key") != "rzt-hedge" and c.get("pos") != "short"]
                with ThreadPoolExecutor(max_workers=6) as ex:
                    for c, tag in zip(scan, ex.map(lambda c: oel_tag(c, today, cfg), scan, timeout=8)):
                        c["oel"] = tag[0] if tag else None
                if any(c.get("oel") for c in entries):
                    entries = sorted(entries, key=lambda c: (c.get("kind") != "index", {"clean": 0, "wide": 1}.get(c.get("oel"), 2), -(c.get("rank", c.get("score")) or 0)))
                    rep["note"] = (rep["note"] + " · " if rep["note"] else "") + f"{sum(1 for c in entries if c.get('oel'))} with premium Open = Low first"
            except Exception as e:
                st["log"].append({"at": now.isoformat(), "msg": f"premium open=low scan failed: {str(e)[:80]}"})
            if cfg.get("classicOnly", True):                                  # classic mode (user, 28 Oct): the four classic entry types trade; Picks / Eagle / Gann angle / time cycle / Z Trend trade ONLY
                kept, paper = classic_filter(entries, bool(cfg.get("extrasAgree", False)))
                shadow_record(st, paper, now)
                n0 = len(entries)
                entries = kept
                if paper:
                    rep["note"] = (rep["note"] + " · " if rep["note"] else "") + f"{len(paper)} extra-strategy signal(s) logged as paper only"
            # only good risk/reward (user rule): every STOCK entry - strategy signal, Eagle, screen - must pass the same check as
            # Today's Picks (risk <= 5% of the price, >= 1R of room to the 20-session high / low); a stock without a Picks row passes
            try:
                import morning_picks
                pmap = _screen_score()
                weak = [c for c in entries if c.get("kind") == "stock" and pmap.get(c["sym"]) and not morning_picks.good_rr(pmap[c["sym"]], c["side"])]
                if weak:
                    wk = {id(c) for c in weak}
                    entries = [c for c in entries if id(c) not in wk]
                    rep["note"] = (rep["note"] + " · " if rep["note"] else "") + f"{len(weak)} skipped for weak risk/reward"
            except Exception as e:
                st["log"].append({"at": now.isoformat(), "msg": f"risk/reward check failed: {str(e)[:80]}"})
            try:                                                  # agreement rule (user 29 Oct): stock options need 2+ indicators, or one indicator with strength >= 75
                need, solo = int(cfg.get("minAgreeStock", MIN_AGREE_STOCK)), float(cfg.get("soloStrength", SOLO_STRENGTH))
                pm_ = _screen_score()

                def _agree_ok(c):
                    if c.get("kind") != "stock" or need <= 1:
                        return True
                    if int(c.get("agree") or len(c.get("strategies") or []) or 1) >= need:
                        return True
                    return float((pm_.get(c["sym"]) or {}).get("strength") or 0) >= solo
                few = [c for c in entries if not _agree_ok(c)]
                if few:
                    fk = {id(c) for c in few}
                    entries = [c for c in entries if id(c) not in fk]
                    rep["note"] = (rep["note"] + " · " if rep["note"] else "") + f"{len(few)} skipped (stock option needs {need}+ indicators or strength {solo:.0f}+)"
            except Exception as e:
                st["log"].append({"at": now.isoformat(), "msg": f"agreement check failed: {str(e)[:80]}"})
            try:                                                  # index rule (user 30 Oct): 3+ indicators agree, at most 5 trades a day per index
                need_i, max_i = int(cfg.get("indexMinAgree", INDEX_MIN_AGREE)), int(cfg.get("indexMaxPerDay", INDEX_MAX_PER_DAY))
                same = {}
                for c in entries:
                    same.setdefault((c["sym"], c["side"]), set()).add(c.get("key"))
                done_idx = {}
                for t in st["trades"]:
                    if t.get("date") == today and not t.get("pairOf") and t.get("pos") != "short":
                        done_idx[t["sym"]] = done_idx.get(t["sym"], 0) + 1
                dead = {(t["sym"], t.get("opt")) for t in st["trades"]       # user 30 Oct: once an entry in a name + side hit its stop (or the signal reversed), no more entries on that side today
                        if t.get("date") == today and t.get("status") == "CLOSED" and t.get("exitReason") in ("STOP", "REVERSE") and not t.get("pairOf") and t.get("pos") != "short"}
                keep_i, few_i, cap_i = [], 0, 0
                for c in entries:
                    if c.get("key") == "rzt-hedge" or c.get("pos") == "short":
                        keep_i.append(c)
                        continue
                    if (c["sym"], "CE" if c["side"] == "BUY" else "PE") in dead:
                        cap_i += 1
                        if c.get("kind") == "index":
                            _idx_note(st, c["sym"], "no entry - the earlier trade on this side hit its stop (or reversed) today")
                        continue
                    if c.get("kind") != "index":                  # stock options: the same daily limit per stock, no indicator minimum here (the stock rule above has its own)
                        if max_i > 0 and done_idx.get(c["sym"], 0) >= max_i:
                            cap_i += 1
                            continue
                        done_idx[c["sym"]] = done_idx.get(c["sym"], 0) + 1
                        keep_i.append(c)
                        continue
                    n_ind = int(c.get("agree") or 1) + len(same.get((c["sym"], c["side"]), set()) - {c.get("key")})
                    if need_i > 1 and n_ind < need_i:
                        few_i += 1
                        _idx_note(st, c["sym"], f"no entry - only {n_ind} indicator(s) agree, {need_i} needed")
                        continue
                    if max_i > 0 and done_idx.get(c["sym"], 0) >= max_i:
                        cap_i += 1
                        _idx_note(st, c["sym"], f"no entry - {max_i} trades already taken today")
                        continue
                    done_idx[c["sym"]] = done_idx.get(c["sym"], 0) + 1
                    c["agree"] = n_ind
                    keep_i.append(c)
                if few_i or cap_i:
                    entries = keep_i
                    rep["note"] = (rep["note"] + " · " if rep["note"] else "") + f"{few_i} index skipped (under {need_i} indicators), {cap_i} skipped (max {max_i} trades a day in one name)"
                else:
                    entries = keep_i
            except Exception as e:
                st["log"].append({"at": now.isoformat(), "msg": f"index agreement check failed: {str(e)[:80]}"})
            if cfg.get("stockOnly") or cfg.get("buyOnly"):        # from 28 Oct: options are only BOUGHT (call for a bullish signal, put for a bearish one) - nothing is written / sold (stock options only too when stockOnly is switched on)
                n0 = len(entries)
                entries = [c for c in entries if not (cfg.get("stockOnly") and c.get("kind") != "stock")
                           and not (cfg.get("buyOnly") and (c.get("key") == "rzt-hedge" or c.get("pos") == "short"))]
                if n0 != len(entries):
                    rep["note"] = (rep["note"] + " · " if rep["note"] else "") + f"{n0 - len(entries)} skipped (buy-only / stock-options-only)"
            try:
                _pm = _screen_score()
                entries = sorted(entries, key=lambda c: entry_priority(c, _pm))          # stable: strength 100 first, then Eagle, strength 75+, index, the rest
            except Exception as e:
                st["log"].append({"at": now.isoformat(), "msg": f"entry priority failed: {str(e)[:80]}"})
            slots = len(entries)
            if not force and _mins(now) <= _hm(cfg["windowStart"]):
                burst = int(cfg.get("openBurstCap") or 12)
                slots = max(0, burst - sum(1 for t in todays if not str(t.get("id", "")).endswith("-W")))
                if len(entries) > slots:
                    rep["note"] = (rep["note"] + " · " if rep["note"] else "") + f"opening-minute cap {burst}: {len(entries) - slots} candidate(s) wait for the next cycle"
            taken = 0
            for i, c in enumerate(entries):
                if taken >= slots:
                    break
                over = time.time() - t0              # at least one entry per cycle (a slow scan must not starve them), hard stop at budget + 6 s
                if not dry and (over > CYCLE_BUDGET + 6 or (taken and over > CYCLE_BUDGET)):
                    rep["note"] = (rep["note"] + " · " if rep["note"] else "") + f"time budget: {len(entries) - i} entr(ies) wait for the next cycle"
                    break
                tried.add(id(c))
                if dry:
                    rep["entered"].append({"sym": c["sym"], "side": c["side"], "strategy": c["key"], "kind": c["kind"],
                                           "rank": round(c.get("rank", c.get("score") or 0), 2), "source": c.get("source") or c.get("label") or ""})   # Z Trend / time-cycle / filled candidates carry a score but no rank
                    taken += 1
                    continue
                # a candidate that just failed (no credit, thin strike, wide spread) is not retried every minute - each try costs
                # option-chain calls and kept Upstox rate-limited; it is tried again after 15 minutes
                cool = st.setdefault("skipUntil", {})
                ck = f"{c.get('key')}|{c['sym']}|{c.get('side')}"
                if cool.get(ck, 0) > time.time():
                    continue
                try:
                    # Timing rule: option BUYING (CE for a BUY signal, PE for a SELL signal - stocks and indices) from 09:16;
                    # option SELLING (credit spreads, written legs) from 09:20. Paired written legs (-W) are deferred inside open_trade.
                    is_sell = c.get("key") == "rzt-hedge" or c.get("pos") == "short"
                    if is_sell and _mins(now) < SELL_FROM and not force:
                        st["log"].append({"at": now.isoformat(), "msg": f"holding {c['sym']} SELL trade until 09:20"})
                        continue
                    if c.get("key") == "rzt-hedge":
                        try:
                            t = _open_rzt_hedge(st, c, today)  # Z Trend flip as a hedged credit spread (its own notify)
                        except RuntimeError as e:
                            if "no credit" not in str(e):
                                raise
                            # no credit for the spread (expiry day, steep skew): take the flip as a plain option BUY instead
                            # (CE for a BUY flip, PE for a SELL flip) so index flips are not lost
                            b = dict(c, key="rzt-intraday", source=(c.get("source") or "").replace(" · hedged credit spread", "") + " · option buy (no credit for a spread)")
                            t = open_trade(st, b, today)
                            pend_notify.append(t)
                    else:
                        t = open_trade(st, c, today)
                        pend_notify.append(t)
                    rep["entered"].append(t["id"])
                    taken += 1
                except Exception as e:
                    st["log"].append({"at": now.isoformat(), "msg": f"skip {c['sym']}: {str(e)[:80]}"})
                    if "09:20" not in str(e):
                        cool[ck] = time.time() + 900
                        for k_ in [k_ for k_, v_ in cool.items() if v_ < time.time()]:
                            cool.pop(k_, None)
        if not dry:
            try:                                                                                  # what this cycle did not get to is offered again next cycle
                exp = time.time() + CARRY_FOR
                st["carry"] = [dict(c, _exp=c.get("_exp") or exp) for c in entries if c.get("_fill") and id(c) not in tried][:20]
            except Exception:
                st["carry"] = []
        if not dry:
            _sv = _save(st)
            if _sv is True:
                for _t in pend_notify:
                    _notify(_t)
            if _sv is not True:
                rep["entered"] = []                # nothing was kept: do not report these as entered
                rep["saveConflict"] = True
                rep["note"] = (rep["note"] + " · " if rep["note"] else "") + "the book changed while this cycle ran - its changes were not saved, the next cycle redoes them"
                st["log"].append({"at": now.isoformat(), "msg": "cycle not saved: the book changed meanwhile (a manual action or another instance)"})
        else:
            try:                                   # a preview still persists the day's scan cache so the next
                real = _load()                     # preview (or live cycle) does not rescan every symbol from zero
                real["cand"] = st.get("cand") or real.get("cand")
                _save(real)
            except Exception:
                pass
        return rep


PUSH_ENTRIES = True       # user: push the auto trader's trades, max 5 a day (push_signals.MAX_TRADE_PER_DAY)
PUSH_LOCKS = True        # builds the "stop moved" alert; push_signals.MAX_LOCK_PER_DAY = 0 keeps it OFF on the phone (user 29 Oct) - it still shows in the app; hard total 5 pushes a day


def _notify(t):
    if not PUSH_ENTRIES:
        return
    try:
        import push_signals
        push_signals.notify_all(f"auto|{t['id']}|{str(t.get('openedAt') or '')[11:19]}", f"PAPER ENTRY · {t['sym']} {t['strike']:.0f} {t['opt']}",
                                f"{t['lots']} lot(s) @ ₹{t['entry']} · stop {t['stopU']} · target {t['targetU'] if t['targetU'] else 'trailing'} · "
                                f"{len(t.get('indicators') or [])} indicator(s): {', '.join((t.get('indicators') or [t['strategy']])[:3])}",
                                bucket="index" if t.get("kind") == "index" else "stock")
    except Exception as e:
        print(f"[auto] notify failed: {e}")


# ───────────────────────── API ─────────────────────────
class Cfg(BaseModel):
    enabled: bool | None = None
    researchMode: bool | None = None
    riskPct: float | None = None
    premSlPct: float | None = None
    maxPerDay: int | None = None
    dayPnlLimit: float | None = None
    zTrendHedge: bool | None = None
    pairSell: bool | None = None
    eagleOn: bool | None = None
    gannOn: bool | None = None
    classicOnly: bool | None = None
    extrasAgree: bool | None = None
    lockMode: str | None = None
    buyOnly: bool | None = None
    stockOnly: bool | None = None
    stockTrader: bool | None = None
    capital: float | None = None
    sleeves: dict | None = None


class TslBody(BaseModel):
    mode: str
    trail: float | None = None        # underlying points behind the best price
    trigger: float | None = None      # breakeven trigger, in R (multiples of the initial underlying risk)
    step: float | None = None         # underlying points per step


class StopBody(BaseModel):
    stopU: float


def filter_set(c):
    """Which filter set an entry belongs to, for the Journal's two accuracy panels: "OLD FILT" = the 22 Oct filter ("N indicator(s) agree",
    stock screen, index call/put); "NEW IND" = every other working indicator (Z Trend, time cycle, Today's Picks, Eagle, Gann ...)."""
    return "OLD FILT" if c.get("strategies") or c.get("key") in ("stock-screen", "index-call-put") else "NEW IND"


def _open_trade(st, tid):
    t = next((x for x in st["trades"] if x["id"] == tid), None)
    if not t:
        raise HTTPException(404, "Trade not found")
    if t["status"] != "OPEN":
        raise HTTPException(400, "This trade is already closed")
    return t


def _und_price(t):
    import market_api
    q = _quotes({market_api._key(t["sym"])})
    return _last(q.get(market_api._key(t["sym"])))


def _book(q):
    """(bid, ask) from a full quote's top-of-book depth; 0 when a side is empty."""
    d = (q or {}).get("depth") or {}
    bid = float(((d.get("buy") or [{}])[0] or {}).get("price") or 0)
    ask = float(((d.get("sell") or [{}])[0] or {}).get("price") or 0)
    return bid, ask


def _exit_px(t, q):
    """The price a manual exit books for this trade: a sold option is bought back at the ask, a bought one sold at the bid; the last
    traded price when that side of the book is empty. 0 when there is no price at all. ONE function, used by the exit endpoints and
    by the live preview the Journal shows, so the price on the exit screen is the price that gets booked."""
    bid, ask = _book(q)
    side_px = ask if t.get("pos") == "short" else bid
    return side_px if side_px > 0 else _last(q)


def _mark_px(t, q):
    """The price an open option is MARKED at for its running P&L and for its stop: what it could be closed at right now - the bid for a bought
    option, the ask for a sold one. The last traded price is used when that side of the book is empty or the book is gaping (spread over 10%,
    typical of the opening minutes and of thin stock options), because then the bid/ask is not a price anyone could trade at. The last traded
    price alone is stale or jumps on thin contracts and did not match what a stop or an exit books."""
    bid, ask = _book(q)
    ltp = _last(q)
    if bid > 0 and ask > 0 and (ask - bid) / ask > 0.10 and ltp > 0:
        return ltp
    px = ask if t.get("pos") == "short" else bid
    return px if px > 0 else ltp


def _mk(t):
    """The stored mark of an open trade (falls back to the last traded price for trades marked before marks existed)."""
    return float(t.get("mark") or t.get("last") or t["entry"] or 0)


MOVE_TOL = 0.03          # an exit is refused when the price moved more than this since the screen the user confirmed on


class ExitBody(BaseModel):
    seen: float | None = None        # the exit price on the confirm screen; the exit is refused (409) if it has moved by more than MOVE_TOL


_LIVE = {"at": 0.0, "keys": (), "q": {}}


def _live_quotes(keys, ttl=3.0):
    """Quotes for the open contracts, shared for `ttl` seconds across requests on this instance so ten open tabs polling every few
    seconds cost one broker call, not ten."""
    keys = tuple(sorted(set(keys)))
    if not keys:
        return {}
    if _LIVE["keys"] == keys and time.time() - _LIVE["at"] < ttl:
        return _LIVE["q"]
    q = _quotes(list(keys)) or {}
    _LIVE.update(at=time.time(), keys=keys, q=q)
    return q


@router.get("/live")
def live_prices():
    """Read-only live prices of every open option trade: last traded, bid, ask and the price an exit would book right now. The status
    read only marks to market every couple of minutes (and serves a cached copy), so the Journal polls this while it is on screen and
    on every exit confirm screen. Nothing is saved here."""
    st = _load(cached=True)
    opens = [t for t in st["trades"] if t["status"] == "OPEN" and t.get("key")]
    now = _now()
    out = {"at": now.isoformat(), "trades": [], "ok": True}
    if not opens:
        return out
    try:
        q = _live_quotes([t["key"] for t in opens])
    except Exception as e:
        out.update(ok=False, error=str(e)[:80])
        return out
    for t in opens:
        qq = q.get(t["key"]) or {}
        bid, ask = _book(qq)
        ltp = _last(qq)
        ex = _exit_px(t, qq)
        mk = _mark_px(t, qq)
        qty = (t.get("lots") or 0) * (t.get("lot") or 0)
        sgn = -1 if t.get("pos") == "short" else 1
        out["trades"].append({"id": t["id"], "ltp": round(ltp, 2), "bid": round(bid, 2), "ask": round(ask, 2), "exitPx": round(ex, 2), "mark": round(mk, 2),
                              "unrealised": round((mk - t["entry"]) * qty * sgn, 2) if mk > 0 else None,
                              "exitGross": round((ex - t["entry"]) * qty * sgn, 2) if ex > 0 else None, "at": now.isoformat()})
    return out


@router.post("/trade/{tid}/exit")
def manual_exit(tid: str, b: ExitBody | None = None):
    """Close an open automated paper trade right now at the live bid (ask for a sold option)."""
    seen = b.seen if b else None

    def apply(st):
        t = _open_trade(st, tid)
        try:
            q = _quotes([t["key"]]).get(t["key"]) or {}
        except Exception as e:
            raise HTTPException(503, f"Live price unavailable right now, try again in a moment ({str(e)[:80]})")
        px = _exit_px(t, q)
        if px <= 0:
            raise HTTPException(503, "No live price for this contract right now, try again in a moment")
        if seen and seen > 0 and abs(px - seen) / seen > MOVE_TOL:
            raise HTTPException(409, f"Price moved from {seen:.2f} to {px:.2f} while you were confirming. Check the new price and exit again.")
        _close(st, t, px, "MANUAL")
        return {"ok": True, "exit": t["exit"], "net": t["net"], "R": t["R"]}
    return _mutate(apply)


@router.post("/exit-all")
def exit_all():
    """Close EVERY open automated paper trade at the live bid / ask in ONE request (one state load, one quote call for all contracts,
    one save). The Journal used to call the single-trade exit 20+ times in a row: each call loaded and saved the whole book and waited for
    the cycle lock, so on Vercel the first one could hang and "Exit all" sat at 1/20 forever."""
    def apply(st):
        opens = [t for t in st["trades"] if t["status"] == "OPEN"]
        if not opens:
            return {"ok": True, "closed": 0, "net": 0, "failed": []}
        keys = sorted({t["key"] for t in opens if t.get("key")})
        try:
            q = _quotes(keys) if keys else {}
        except Exception as e:
            raise HTTPException(503, f"Live prices unavailable right now, try again in a moment ({str(e)[:80]})")
        n, net, failed = 0, 0.0, []
        for t in opens:
            px = _exit_px(t, q.get(t.get("key")) or {})
            if px <= 0:                                  # no live price for this contract: leave it open rather than book a guess
                failed.append(f"{t['id']}: no live price")
                continue
            _close(st, t, px, "MANUAL")
            n += 1
            net += t.get("net") or 0
        return {"ok": True, "closed": n, "net": round(net, 2), "failed": failed}
    return _mutate(apply)


@router.post("/trade/{tid}/tsl")
def set_tsl(tid: str, b: TslBody):
    """Attach (or remove) your own trailing stop. It only ever tightens the stop."""
    mode = (b.mode or "").lower()
    if mode not in ("off", "trail", "breakeven", "step"):
        raise HTTPException(400, "mode must be off, trail, breakeven or step")

    def apply(st):
        t = _open_trade(st, tid)
        if mode == "off":
            t["tsl"] = None
        elif mode == "trail":
            if not (b.trail and b.trail > 0):
                raise HTTPException(400, "Enter the trail distance (underlying points)")
            t["tsl"] = {"mode": "trail", "trail": b.trail}
        elif mode == "breakeven":
            t["tsl"] = {"mode": "breakeven", "trigger": b.trigger if (b.trigger and b.trigger > 0) else 1.0}
        else:
            if not (b.step and b.step > 0):
                raise HTTPException(400, "Enter the step size (underlying points)")
            t["tsl"] = {"mode": "step", "step": b.step}
        st["log"].append({"at": _now().isoformat(), "msg": f"TSL {mode} set on {t['sym']} {t['strike']:.0f}{t['opt']} by user"})
        return {"ok": True, "tsl": t["tsl"], "stopU": t["stopU"]}
    return _mutate(apply)


@router.post("/trade/{tid}/stop")
def tighten_stop(tid: str, b: StopBody):
    def apply(st):
        t = _open_trade(st, tid)
        d = 1 if t["side"] == "BUY" else -1
        try:
            und = _und_price(t)
        except Exception as e:
            raise HTTPException(503, f"Live price unavailable right now, try again in a moment ({str(e)[:80]})")
        if d * (b.stopU - t["stopU"]) <= 0:
            raise HTTPException(400, f"A stop can only be tightened: it is {t['stopU']} now")
        if und > 0 and d * (und - b.stopU) <= 0:
            raise HTTPException(400, f"That stop is already beyond the current price ({und}); use Exit now instead")
        t["stopU"] = round(b.stopU, 2)
        t["stopMoved"] = _now().isoformat()
        st["log"].append({"at": _now().isoformat(), "msg": f"Stop moved to {t['stopU']} on {t['sym']} {t['strike']:.0f}{t['opt']} by user"})
        return {"ok": True, "stopU": t["stopU"]}
    return _mutate(apply)


@router.get("/status")
def status():
    try:
        mark_open_positions()
    except Exception as e:                                 # a failed mark must never break the status screen
        print(f"[auto] mark-to-market failed: {e}")
    now = _now()
    try:
        import nse_calendar
        gap = 30 if 9 * 60 + 16 <= _mins(now) <= 9 * 60 + 19 else 180      # opening minutes: buying must start at 09:16, do not wait for a 3-minute gap
        if nse_calendar.session_open(now) and time.time() - getattr(run_cycle, "_last_ran", 0) >= gap:
            run_cycle._last_ran = time.time()
            run_cycle()
    except Exception as e:
        print(f"[auto] status cycle trigger failed: {e}")
    st = _load(cached=True, verify=True)                       # read-only screen: this instance's copy, but only if nobody saved since (else two refreshes could show two different books)
    if st.get("_dirty"):
        with _lock:
            _save(st)
    now = _now()
    today = now.date().isoformat()
    closed = [t for t in st["trades"] if t["status"] == "CLOSED"]
    wins = [t for t in closed if t["net"] > 0]
    opens = [t for t in st["trades"] if t["status"] == "OPEN"]
    for t in opens:
        _replan(t)
        t["unrealised"] = round((_mk(t) - t["entry"]) * t["lots"] * t["lot"] * (-1 if t.get("pos") == "short" else 1), 2)
        t["costPctEff"] = t.get("costPct", st["cfg"]["costPct"])      # the Journal shows open P&L after the estimated exit cost (same % as _close charges)
    import backtest
    bt = backtest.get()["result"]
    import backtest
    r0 = backtest.get()["result"]
    chosen = {k: tuple(v) for k, v in ((r0["chosen"] if r0 else {}) or {}).items()}
    keys = list(chosen) or []
    proven = bool(r0 and r0["provenKeys"])
    label = ("proven indicators" if proven else "all indicators, ranked by how many agree · unproven (forward test)")
    guard, guard_note = _day_guard(st, today)
    return {
        "activeStrategies": [{"key": k, "variant": chosen.get(k, ("fixed", "none"))[0], "filter": chosen.get(k, ("fixed", "none"))[1]} for k in keys],
        "mode": label,
        "shadow": {"summary": shadow_summary(st), "recent": st.get("shadow", [])[-60:][::-1]},
        "cfg": st["cfg"], "group": "all", "book": "main", "today": today, "marketOpen": __import__("nse_calendar").session_open(now),
        "dayPnl": {"value": round(_day_pnl(st, today), 0), "limit": st["cfg"].get("dayPnlLimit", 0), "mode": guard, "note": guard_note},
        "todayCount": len([t for t in st["trades"] if t["date"] == today]),
        "sleeves": sleeve_report(st),
        "open": opens, "closed": closed[-120:][::-1], "log": st["log"][-120:][::-1],
        "summary": {"trades": len(closed), "net": round(sum(t["net"] for t in closed), 0),
                    "winRate": round(len(wins) / len(closed), 2) if closed else 0,
                    "avgR": round(sum(t["R"] or 0 for t in closed) / len(closed), 2) if closed else 0,
                    "openPnL": round(sum(t.get("unrealised", 0) for t in opens), 0), "equity": round(_equity(st), 0)},
        "backtest": {"provenKeys": bt["provenKeys"] if bt else [], "twoMonth": (bt["executor"] or bt["executorResearch"] or {}).get("twoMonth") if bt else None,
                     "researchReplay": bt["executorResearch"] if bt else None,
                     "generatedAt": bt["generatedAt"] if bt else None},
    }


@router.post("/config")
def config(c: Cfg):
    def apply(st):
        if c.enabled is not None:
            st["cfg"]["enabled"] = c.enabled
        if c.researchMode is not None:
            st["cfg"]["researchMode"] = c.researchMode
        if c.eagleOn is not None:
            st["cfg"]["eagleOn"] = c.eagleOn
        if c.gannOn is not None:
            st["cfg"]["gannOn"] = c.gannOn
        if c.classicOnly is not None:
            st["cfg"]["classicOnly"] = c.classicOnly
        if c.extrasAgree is not None:
            st["cfg"]["extrasAgree"] = c.extrasAgree
        if c.lockMode is not None:
            if c.lockMode not in LOCKS:
                raise HTTPException(400, "lockMode must be 'old' or 'new'")
            st["cfg"]["lockMode"] = c.lockMode
        if c.premSlPct is not None:
            if not (0.05 <= c.premSlPct <= 0.5):
                raise HTTPException(400, "premSlPct must be between 0.05 and 0.5 (5% to 50% of the premium)")
            st["cfg"]["premSlPct"] = c.premSlPct
        if c.riskPct is not None:
            if not (0.05 <= c.riskPct <= 2):
                raise HTTPException(400, "riskPct must be between 0.05 and 2")
            st["cfg"]["riskPct"] = c.riskPct
        if c.maxPerDay is not None:                                     # 0 = no limit
            if c.maxPerDay < 0:
                raise HTTPException(400, "maxPerDay must be 0 (no limit) or a positive number")
            st["cfg"]["maxPerDay"] = c.maxPerDay
        if c.dayPnlLimit is not None:                                   # 0 = guard off; default ±45,000
            if c.dayPnlLimit < 0:
                raise HTTPException(400, "dayPnlLimit must be 0 (guard off) or a positive rupee amount")
            st["cfg"]["dayPnlLimit"] = float(c.dayPnlLimit)
        if c.buyOnly is not None:                                       # true: options are only bought (calls AND puts), no written / spread legs
            st["cfg"]["buyOnly"] = c.buyOnly
        if c.stockOnly is not None:                                     # true: stock options only, no index trades
            st["cfg"]["stockOnly"] = c.stockOnly
        if c.stockTrader is not None:                                   # false: the separate share paper trader opens nothing new (open trades are still managed)
            st["cfg"]["stockTrader"] = c.stockTrader
        if c.capital is not None:
            if c.capital < 100000:
                raise HTTPException(400, "capital must be at least 1,00,000")
            st["cfg"]["capital"] = float(c.capital)
        if c.sleeves is not None:                                       # {"picks": 500000, "eagle": 500000, "signals": 500000}; {} = one pool
            if any(k not in SLEEVE_NAMES or float(v) < 0 for k, v in c.sleeves.items()):
                raise HTTPException(400, "sleeves keys must be picks / eagle / signals with amounts >= 0")
            st["cfg"]["sleeves"] = {k: float(v) for k, v in c.sleeves.items()}
        if c.pairSell is not None:                                      # false: buy-only, no paired opposite-option sell leg
            st["cfg"]["pairSell"] = c.pairSell
        if c.zTrendHedge is not None:                                   # true: Z Trend flips open hedged credit spreads
            st["cfg"]["zTrendHedge"] = c.zTrendHedge
        st["cfg"]["cfgAt"] = time.time()                                # newest settings win if two databases are merged
        return st["cfg"]
    return _mutate(apply)


@router.post("/log/clear")
def clear_log():
    def apply(st):
        st["log"] = []
        return {"ok": True}
    return _mutate(apply)


@router.post("/reset")
def reset_portfolio():
    """Journal 'Reset portfolio': drop every paper trade (open and closed) so equity starts again from capital.
    Settings are kept. Today's entries count restarts too."""
    def apply(st):
        n = len(st["trades"])
        _remember_cleared(st, st["trades"])                      # 29 Oct (user): after "Reset", the same ideas were bought again at once ("old entries come back")
        st["trades"], st["cand"] = [], {}
        st["resetAt"] = _now().isoformat()                       # a later merge of two databases respects the reset
        st["log"] = [{"at": _now().isoformat(), "msg": f"Portfolio reset by the user ({n} paper trades cleared)"}]
        return {"ok": True, "cleared": n}
    return _mutate(apply)


@router.api_route("/run", methods=["GET", "POST"])
def run():
    return run_cycle()


@router.get("/preview")
def preview():
    return run_cycle(force=True, dry=True)


def start_watcher():
    if os.environ.get("VERCEL"):
        return

    def loop():
        time.sleep(45)
        import backtest
        while True:
            try:
                if backtest.get()["result"] is None and not backtest.get()["running"]:
                    backtest.start()
                r = run_cycle()
                if r.get("entered") or r.get("closed"):
                    print(f"[auto] {r}")
            except Exception as e:
                print(f"[auto] cycle failed: {e}")
            time.sleep(300)

    threading.Thread(target=loop, daemon=True, name="auto-trader").start()
