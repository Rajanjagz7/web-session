"""Run the strategy backtest outside Vercel (GitHub Actions) and write static/backtest_result.json.

Vercel's 30-second limit cannot fit a full replay, and Upstox needs a login token, so this runner feeds the same
backtest with daily candles from Yahoo Finance instead. Usage:  python run_backtest_ci.py
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bar_source  # noqa: E402
import market_api  # noqa: E402
import backtest  # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))
YH = {"NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK", "SENSEX": "^BSESN", "FINNIFTY": "NIFTY_FIN_SERVICE.NS",
      "MIDCPNIFTY": "NIFTY_MID_SELECT.NS", "INDIAVIX": "^INDIAVIX"}
_cache = {}


def _yahoo(sym):
    s = sym.upper()
    if s in _cache:
        return _cache[s]
    t = YH.get(s, s + ".NS")
    for attempt in range(3):
        try:
            r = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{requests.utils.quote(t)}",
                             params={"range": "10y", "interval": "1d"}, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            res = r.json()["chart"]["result"][0]
            q = res["indicators"]["quote"][0]
            out = []
            for k, ts in enumerate(res["timestamp"]):
                o, h, l, c = q["open"][k], q["high"][k], q["low"][k], q["close"][k]
                if None in (o, h, l, c) or c <= 0:
                    continue
                d = datetime.fromtimestamp(ts, IST).date().isoformat()
                if out and out[-1]["date"] == d:
                    continue
                out.append({"date": d, "open": o, "high": h, "low": l, "close": c, "volume": q["volume"][k] or 0})
            _cache[s] = out
            return out
        except Exception as e:
            print(f"  {s}: retry {attempt + 1} ({e})")
            time.sleep(2)
    _cache[s] = []
    return []


def daily(sym, lookback_days=180):
    bars = _yahoo(sym)
    cut = (datetime.now(IST).date() - timedelta(days=int(lookback_days))).isoformat()
    return [b for b in bars if b["date"] >= cut]


bar_source.daily_bars = daily
bar_source.supports = lambda s: True
bar_source.completed_only = lambda on=True: None
market_api.ensure_universe = lambda: None

if __name__ == "__main__":
    t0 = time.time()
    r = backtest.run_backtest(progress=lambda m: print(m, flush=True))
    r["dataSource"] = "Yahoo Finance daily candles (GitHub Actions run)"
    with open(backtest.OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(r, f)
    print(f"done in {time.time() - t0:.0f}s: {r['tradesSimulated']} trades, proven {r['provenKeys']}, research {r['researchKeys']}")
