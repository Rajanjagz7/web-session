"""Every NSE-listed stock (not just F&O): search, index constituents and a multibagger screen.

Source of truth is Upstox's public instrument master (all NSE_EQ symbols) and the official NSE index
constituent files. Everything is cached in memory for a few hours.
"""
import csv
import gzip
import io
import json
import re
import threading
import time
from typing import Dict, List

import requests
from fastapi import APIRouter, HTTPException, Query

try:  # package import (rajantrading/api) or flat import (rajanstocks)
    from .upstox_service import upstox_service
except Exception:  # pragma: no cover
    from upstox_service import upstox_service

router = APIRouter(prefix="/api/m")

NSE_URL = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz"
IDX_URL = "https://nsearchives.nseindia.com/content/indices/ind_%slist.csv"
UA = {"User-Agent": "Mozilla/5.0 (compatible; AlgoTrades/1.0)"}
TTL = 6 * 3600

# key -> (label, group, csv file stem)
INDEX_FILES = [
    ("nifty50", "Nifty 50", "Broad", "nifty50"),
    ("sensex", "BSE Sensex", "Broad", None),   # BSE publishes no open file; read from the maintained public list
    ("niftynext50", "Nifty Next 50", "Broad", "niftynext50"),
    ("nifty100", "Nifty 100", "Broad", "nifty100"),
    ("nifty200", "Nifty 200", "Broad", "nifty200"),
    ("nifty500", "Nifty 500", "Broad", "nifty500"),
    ("midcap50", "Nifty Midcap 50", "Midcap", "niftymidcap50"),
    ("midcap100", "Nifty Midcap 100", "Midcap", "niftymidcap100"),
    ("midcap150", "Nifty Midcap 150", "Midcap", "niftymidcap150"),
    ("smallcap50", "Nifty Smallcap 50", "Smallcap", "niftysmallcap50"),
    ("smallcap100", "Nifty Smallcap 100", "Smallcap", "niftysmallcap100"),
    ("smallcap250", "Nifty Smallcap 250", "Smallcap", "niftysmallcap250"),
    ("midsmall400", "Nifty MidSmallcap 400", "Smallcap", "niftymidsmallcap400"),
    ("microcap250", "Nifty Microcap 250", "Smallcap", "niftymicrocap250_"),
    ("infra", "Nifty Infrastructure", "Sector", "niftyinfra"),
    ("bank", "Nifty Bank", "Sector", "niftybank"),
    ("it", "Nifty IT", "Sector", "niftyit"),
    ("pharma", "Nifty Pharma", "Sector", "niftypharma"),
    ("healthcare", "Nifty Healthcare", "Sector", "niftyhealthcare"),
    ("auto", "Nifty Auto", "Sector", "niftyauto"),
    ("fmcg", "Nifty FMCG", "Sector", "niftyfmcg"),
    ("metal", "Nifty Metal", "Sector", "niftymetal"),
    ("energy", "Nifty Energy", "Sector", "niftyenergy"),
    ("oilgas", "Nifty Oil & Gas", "Sector", "niftyoilgas"),
    ("realty", "Nifty Realty", "Sector", "niftyrealty"),
    ("psubank", "Nifty PSU Bank", "Sector", "niftypsubank"),
    ("finance", "Nifty Financial Services", "Sector", "niftyfinance"),
    ("media", "Nifty Media", "Sector", "niftymedia"),
    ("consumption", "Nifty Consumption", "Thematic", "niftyconsumption"),
    ("commodities", "Nifty Commodities", "Thematic", "niftycommodities"),
    ("mnc", "Nifty MNC", "Thematic", "niftymnc"),
    ("pse", "Nifty PSE", "Thematic", "niftypse"),
    ("cpse", "Nifty CPSE", "Thematic", "niftycpse"),
]
INDEX_BY_KEY = {k: (label, group, stem) for k, label, group, stem in INDEX_FILES}

_lock = threading.Lock()
_eq = {"t": 0.0, "rows": [], "by_sym": {}}
_idx = {}      # key -> (t, [ {s,n,industry} ])
_multi = {"t": 0.0, "rows": []}


def _equities():
    with _lock:
        if _eq["rows"] and time.time() - _eq["t"] < TTL:
            return _eq
        try:
            r = requests.get(NSE_URL, timeout=25, headers=UA)
            r.raise_for_status()
            data = json.loads(gzip.decompress(r.content))
        except Exception as e:
            if _eq["rows"]:
                return _eq
            raise HTTPException(502, f"Could not load the NSE instrument list: {e}")
        rows, by = [], {}
        for x in data:
            if x.get("segment") != "NSE_EQ" or x.get("instrument_type") != "EQ":
                continue
            sym = (x.get("trading_symbol") or "").upper()
            if not sym or sym in by:
                continue
            row = {"s": sym, "n": (x.get("name") or sym).title().replace(" Ltd", " Ltd").strip(), "k": x.get("instrument_key"), "i": x.get("isin")}
            rows.append(row)
            by[sym] = row
        rows.sort(key=lambda r: r["s"])
        _eq.update(t=time.time(), rows=rows, by_sym=by)
        return _eq


@router.get("/stocks/all")
def stocks_all():
    """Compact list of every NSE equity: [[symbol, name], ...]."""
    eq = _equities()
    return {"count": len(eq["rows"]), "stocks": [[r["s"], r["n"]] for r in eq["rows"]], "asOf": int(eq["t"])}


@router.get("/stocks/search")
def stocks_search(q: str = "", limit: int = 30):
    q = q.strip().upper()
    if len(q) < 1:
        return {"results": []}
    eq = _equities()
    limit = max(1, min(limit, 100))
    starts, contains = [], []
    for r in eq["rows"]:
        if r["s"].startswith(q):
            starts.append(r)
        elif q in r["s"] or q in r["n"].upper():
            contains.append(r)
    out = (starts + contains)[:limit]
    return {"results": [{"s": r["s"], "n": r["n"]} for r in out], "total": len(starts) + len(contains)}


@router.get("/index-stocks/list")
def index_list():
    return {"indices": [{"key": k, "label": l, "group": g} for k, l, g, _ in INDEX_FILES]}


# BSE Sensex (30) — used if the live list cannot be read. Checked against the NSE equity list.
SENSEX_FALLBACK = [
    ("ADANIPORTS", "Adani Ports & SEZ", "Ports"), ("ASIANPAINT", "Asian Paints", "Consumer Durables"), ("AXISBANK", "Axis Bank", "Banks"),
    ("BAJFINANCE", "Bajaj Finance", "Finance"), ("BAJAJFINSV", "Bajaj Finserv", "Finance"), ("BEL", "Bharat Electronics", "Defence"),
    ("BHARTIARTL", "Bharti Airtel", "Telecom"), ("ETERNAL", "Eternal", "Internet"), ("HCLTECH", "HCLTech", "IT"),
    ("HDFCBANK", "HDFC Bank", "Banks"), ("HINDUNILVR", "Hindustan Unilever", "FMCG"), ("ICICIBANK", "ICICI Bank", "Banks"),
    ("INDIGO", "IndiGo", "Aviation"), ("INFY", "Infosys", "IT"), ("ITC", "ITC", "FMCG"), ("KOTAKBANK", "Kotak Mahindra Bank", "Banks"),
    ("LT", "Larsen & Toubro", "Capital Goods"), ("M&M", "Mahindra & Mahindra", "Auto"), ("MARUTI", "Maruti Suzuki", "Auto"),
    ("NTPC", "NTPC", "Power"), ("POWERGRID", "Power Grid", "Power"), ("RELIANCE", "Reliance Industries", "Energy"),
    ("SBIN", "State Bank of India", "Banks"), ("SUNPHARMA", "Sun Pharma", "Pharma"), ("TCS", "Tata Consultancy Services", "IT"),
    ("TATASTEEL", "Tata Steel", "Metals"), ("TECHM", "Tech Mahindra", "IT"), ("TITAN", "Titan Company", "Consumer"),
    ("TRENT", "Trent", "Consumer"), ("ULTRACEMCO", "UltraTech Cement", "Cement"),
]


def _sensex_live():
    """Current BSE Sensex members from the public 'List of BSE SENSEX companies' table (BSE's own API blocks servers)."""
    r = requests.get("https://en.wikipedia.org/w/api.php", timeout=15,
                     params={"action": "parse", "page": "List_of_BSE_SENSEX_companies", "prop": "wikitext", "format": "json"},
                     headers={"User-Agent": "AlgoTrades/1.0 (paper-trading app; index constituents)"})
    r.raise_for_status()
    w = r.json()["parse"]["wikitext"]["*"]
    cur = w[w.index("==Current=="):]
    end = cur.find("\n==", 10)
    cur = cur[:end] if end > 0 else cur
    out = []
    for block in re.split(r"\n\|-\n", cur):
        m = re.search(r"\n\|([A-Z0-9&\-]+)\.BO", block)
        if not m:
            continue
        n = re.search(r"!\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", block)
        out.append({"s": m.group(1), "n": ((n.group(2) or n.group(1)) if n else m.group(1)).strip(), "industry": ""})
    known = _equities()["by_sym"]
    out = [x for x in out if x["s"] in known]
    if not 25 <= len(out) <= 35:
        raise ValueError(f"unexpected Sensex list size {len(out)}")
    return out


def _constituents(key):
    meta = INDEX_BY_KEY.get(key)
    if not meta:
        raise HTTPException(404, "Unknown index")
    hit = _idx.get(key)
    if hit and time.time() - hit[0] < TTL:
        return hit[1]
    if key == "sensex":
        try:
            rows = _sensex_live()
        except Exception:
            rows = [{"s": s, "n": n, "industry": i} for s, n, i in SENSEX_FALLBACK]
        _idx[key] = (time.time(), rows)
        return rows
    try:
        r = requests.get(IDX_URL % meta[2], timeout=20, headers=UA)
        r.raise_for_status()
        rows = []
        for row in csv.DictReader(io.StringIO(r.content.decode("utf-8-sig"))):
            sym = (row.get("Symbol") or "").strip().upper()
            if sym:
                rows.append({"s": sym, "n": (row.get("Company Name") or sym).strip(), "industry": (row.get("Industry") or "").strip()})
    except Exception as e:
        if hit:
            return hit[1]
        raise HTTPException(502, f"Could not load {meta[0]}: {e}")
    _idx[key] = (time.time(), rows)
    return rows


@router.get("/index-stocks")
def index_stocks(index: str = "nifty50"):
    rows = _constituents(index)
    return {"index": index, "label": INDEX_BY_KEY[index][0], "count": len(rows), "stocks": rows}


def _quote_rows(symbols: List[str]) -> Dict[str, dict]:
    eq = _equities()
    keymap = {}
    for s in symbols:
        r = eq["by_sym"].get(s)
        if r and r.get("k"):
            keymap[r["k"]] = s
    out = {}
    if not keymap:
        return out
    raw = upstox_service._full_quotes(list(keymap.keys()))
    for k, q in raw.items():
        s = keymap.get(k)
        if not s:
            continue
        o = q.get("ohlc") or {}
        last = float(q.get("last_price") or 0)
        prev = float(q.get("prev_close_price") or 0) or (last - float(q.get("net_change") or 0))
        out[s] = {"s": s, "last": last, "prev": prev, "open": float(o.get("open") or 0), "high": float(o.get("high") or 0),
                  "low": float(o.get("low") or 0), "vol": float(q.get("volume") or 0),
                  "yh": float(q.get("year_high") or 0), "yl": float(q.get("year_low") or 0)}
    return out


@router.get("/stocks/quotes")
def stocks_quotes(symbols: str = Query("")):
    syms = [x.strip().upper() for x in symbols.split(",") if x.strip()][:200]
    try:
        q = _quote_rows(syms)
    except Exception as e:      # rate limit / outage: let the page keep its last prices
        return {"quotes": [], "stale": True, "reason": str(e)[:160]}
    return {"quotes": list(q.values())}


@router.get("/multibaggers")
def multibaggers(min_x: float = 2.0, limit: int = 120):
    """Stocks trading at >= min_x times their 52-week low across the Midcap 150, Smallcap 250 and Microcap 250 lists."""
    min_x = max(1.2, min(min_x, 20.0))
    if _multi["rows"] and time.time() - _multi["t"] < 300 and _multi.get("x") == min_x:
        return {"stocks": _multi["rows"][:limit], "cached": True}
    names = {}
    for key in ("midcap150", "smallcap250", "microcap250"):
        try:
            for r in _constituents(key):
                names.setdefault(r["s"], r)
        except HTTPException:
            continue
    if not names:
        raise HTTPException(502, "Index lists are unavailable right now")
    try:
        quotes = _quote_rows(list(names.keys()))
    except Exception as e:
        if _multi["rows"]:
            return {"stocks": _multi["rows"][:limit], "cached": True, "stale": True}
        raise HTTPException(503, f"Live prices are temporarily unavailable: {str(e)[:120]}")
    rows = []
    for s, q in quotes.items():
        if q["last"] > 0 and q["yl"] > 0 and q["last"] / q["yl"] >= min_x:
            rows.append({"s": s, "n": names[s]["n"], "industry": names[s]["industry"], "last": q["last"], "prev": q["prev"],
                         "yl": q["yl"], "yh": q["yh"], "x": round(q["last"] / q["yl"], 2),
                         "chg": round((q["last"] / q["prev"] - 1) * 100, 2) if q["prev"] else 0})
    rows.sort(key=lambda r: -r["x"])
    _multi.update(t=time.time(), rows=rows, x=min_x)
    return {"stocks": rows[:limit], "count": len(rows), "scanned": len(quotes)}
