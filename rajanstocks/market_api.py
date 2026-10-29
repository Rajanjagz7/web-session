"""Market data + recommendations API for the Rajan Algo UI.

All numbers come from Upstox (quotes, candles). Nothing is simulated.
"""
import concurrent.futures
import hashlib
import json
import os
import math
import re
import threading
import time

import shared_cache
from datetime import date, datetime, timedelta, timezone

import hmac
from fastapi import APIRouter, Header, HTTPException, Query, Response

from nse_service import nse_service
from upstox_service import _BG, UpstoxRateLimited, background

upstox_service = nse_service.upstox

router = APIRouter(prefix="/api/m")
IST = timezone(timedelta(hours=5, minutes=30))
HERE = os.path.dirname(os.path.abspath(__file__))

def _static_path(filename: str):
    for c in [
        os.path.join(HERE, 'public', 'static', filename),
        os.path.join(HERE, 'static', filename),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public', 'static', filename),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', filename),
    ]:
        if os.path.exists(c):
            return c
    return os.path.join(HERE, 'public', 'static', filename)


# (symbol, name, sector) -- liquid NSE F&O stocks
STOCKS = [
    ("RELIANCE", "Reliance Industries", "Energy"), ("TCS", "Tata Consultancy Services", "IT"),
    ("HDFCBANK", "HDFC Bank", "Banks"), ("INFY", "Infosys", "IT"),
    ("ICICIBANK", "ICICI Bank", "Banks"), ("SBIN", "State Bank of India", "Banks"),
    ("BHARTIARTL", "Bharti Airtel", "Telecom"), ("ITC", "ITC", "FMCG"),
    ("KOTAKBANK", "Kotak Mahindra Bank", "Banks"), ("LT", "Larsen & Toubro", "Capital Goods"),
    ("AXISBANK", "Axis Bank", "Banks"), ("BAJFINANCE", "Bajaj Finance", "Finance"),
    ("MARUTI", "Maruti Suzuki", "Auto"), ("SUNPHARMA", "Sun Pharma", "Pharma"),
    ("TITAN", "Titan Company", "Consumer"), ("WIPRO", "Wipro", "IT"),
    ("HCLTECH", "HCL Technologies", "IT"), ("ASIANPAINT", "Asian Paints", "Consumer"),
    ("ADANIPORTS", "Adani Ports", "Infra"), ("POWERGRID", "Power Grid", "Power"),
    ("NTPC", "NTPC", "Power"), ("ONGC", "ONGC", "Energy"),
    ("TMPV", "Tata Motors Passenger Vehicles", "Auto"), ("BAJAJFINSV", "Bajaj Finserv", "Finance"),
    ("TECHM", "Tech Mahindra", "IT"), ("DIVISLAB", "Divi's Laboratories", "Pharma"),
    ("DRREDDY", "Dr. Reddy's", "Pharma"), ("GRASIM", "Grasim Industries", "Materials"),
    ("CIPLA", "Cipla", "Pharma"), ("EICHERMOT", "Eicher Motors", "Auto"),
    ("HEROMOTOCO", "Hero MotoCorp", "Auto"), ("HINDALCO", "Hindalco", "Metals"),
    ("INDUSINDBK", "IndusInd Bank", "Banks"), ("NESTLEIND", "Nestle India", "FMCG"),
    ("TRENT", "Trent", "Consumer"), ("BEL", "Bharat Electronics", "Defence"),
    ("APOLLOHOSP", "Apollo Hospitals", "Healthcare"), ("SHRIRAMFIN", "Shriram Finance", "Finance"),
    ("JSWSTEEL", "JSW Steel", "Metals"), ("TATASTEEL", "Tata Steel", "Metals"),
    ("COALINDIA", "Coal India", "Energy"), ("ULTRACEMCO", "UltraTech Cement", "Materials"),
    ("HINDUNILVR", "Hindustan Unilever", "FMCG"), ("M&M", "Mahindra & Mahindra", "Auto"),
    ("BAJAJ-AUTO", "Bajaj Auto", "Auto"), ("ADANIENT", "Adani Enterprises", "Infra"),
    ("HAL", "Hindustan Aeronautics", "Defence"), ("DLF", "DLF", "Realty"),
    ("PFC", "Power Finance Corp", "Finance"), ("IRCTC", "IRCTC", "Travel"),
    ("BANKBARODA", "Bank of Baroda", "Banks"), ("PNB", "Punjab National Bank", "Banks"),
    ("TATAPOWER", "Tata Power", "Power"), ("VEDL", "Vedanta", "Metals"),
    ("SIEMENS", "Siemens", "Capital Goods"), ("DMART", "Avenue Supermarts", "Consumer"),
    ("GAIL", "GAIL India", "Energy"), ("BRITANNIA", "Britannia", "FMCG"),
    ("ETERNAL", "Eternal (Zomato)", "Internet"), ("TVSMOTOR", "TVS Motor", "Auto"),
]
INDICES = [
    ("NIFTY", "Nifty 50"), ("BANKNIFTY", "Nifty Bank"), ("FINNIFTY", "Nifty Fin Service"),
    ("MIDCPNIFTY", "Nifty Midcap Select"), ("SENSEX", "BSE Sensex"), ("INDIAVIX", "India VIX"),
]
# (replaced below once the instrument master is loaded - see ensure_universe)
CORE = [s for s, _, _ in STOCKS]            # curated liquid set (sectors known) -> default for heavy scans
CORE_SECTOR = {s: sec for s, _, sec in STOCKS}
CORE_NAME = {s: n for s, n, _ in STOCKS}
INDICES[:] = [("NIFTY", "Nifty 50"), ("BANKNIFTY", "Nifty Bank"), ("FINNIFTY", "Nifty Fin Service"),
              ("MIDCPNIFTY", "Nifty Midcap Select"), ("NIFTYNXT50", "Nifty Next 50"), ("NIFTYFPI", "Nifty FPI 150"),
              ("SENSEX", "BSE Sensex"), ("BANKEX", "BSE Bankex"), ("SENSEX50", "BSE Sensex 50"), ("FOCIT", "BSE FOCIT"),
              ("INDIAVIX", "India VIX")]
NAME = {s: n for s, n, _ in STOCKS} | {s: n for s, n in INDICES}
SECTOR = {s: sec for s, _, sec in STOCKS}
INDEX_SET = {s for s, _ in INDICES}
_uni = {"t": 0.0}

# ---- every other NSE / BSE index that has a live feed: charts, quotes, indicators (no options) ----
_MORE = {
    "Broad market": [
        ("Nifty 100", "Nifty 100"), ("Nifty 200", "Nifty 200"), ("Nifty 500", "Nifty 500"), ("NIFTY TOTAL MKT", "Nifty Total Market"),
        ("NIFTY500 MULTICAP", "Nifty 500 Multicap"), ("Nifty500 Flexicap", "Nifty 500 Flexicap"), ("NIFTY LARGEMID250", "Nifty LargeMidcap 250"),
        ("NIFTY MIDSML 400", "Nifty MidSmallcap 400"),
    ],
    "Midcap": [
        ("Nifty Midcap 50", "Nifty Midcap 50"), ("NIFTY MIDCAP 100", "Nifty Midcap 100"), ("NIFTY MIDCAP 150", "Nifty Midcap 150"),
    ],
    "Smallcap and microcap": [
        ("NIFTY SMLCAP 50", "Nifty Smallcap 50"), ("NIFTY SMLCAP 100", "Nifty Smallcap 100"), ("NIFTY SMLCAP 250", "Nifty Smallcap 250"),
        ("Nifty Smallcap 500", "Nifty Smallcap 500"), ("NIFTY MICROCAP250", "Nifty Microcap 250"),
    ],
    "Sectoral": [
        ("Nifty Auto", "Nifty Auto"), ("Nifty IT", "Nifty IT"), ("Nifty Pharma", "Nifty Pharma"), ("Nifty FMCG", "Nifty FMCG"),
        ("Nifty Metal", "Nifty Metal"), ("Nifty Energy", "Nifty Energy"), ("Nifty Infra", "Nifty Infrastructure"), ("Nifty Realty", "Nifty Realty"),
        ("Nifty PSU Bank", "Nifty PSU Bank"), ("Nifty Pvt Bank", "Nifty Private Bank"), ("Nifty Media", "Nifty Media"),
        ("Nifty FinSerExBnk", "Nifty Fin Services Ex-Bank"), ("NIFTY OIL AND GAS", "Nifty Oil & Gas"), ("NIFTY HEALTHCARE", "Nifty Healthcare"),
        ("NIFTY CONSR DURBL", "Nifty Consumer Durables"), ("Nifty Chemicals", "Nifty Chemicals"), ("Nifty Cement", "Nifty Cement"),
        ("Nifty Capital Mkt", "Nifty Capital Markets"), ("Nifty Housing", "Nifty Housing"), ("Nifty Commodities", "Nifty Commodities"),
        ("Nifty Consumption", "Nifty Consumption"), ("Nifty Serv Sector", "Nifty Services Sector"), ("Nifty InfraLog", "Nifty Infra & Logistics"),
        ("Nifty Trans Logis", "Nifty Transport & Logistics"), ("Nifty RailwaysPSU", "Nifty Railways PSU"),
    ],
    "Thematic": [
        ("Nifty Ind Defence", "Nifty India Defence"), ("NIFTY IND DIGITAL", "Nifty India Digital"), ("NIFTY INDIA MFG", "Nifty India Manufacturing"),
        ("Nifty Mobility", "Nifty Mobility"), ("Nifty EV", "Nifty EV & New Age Auto"), ("Nifty Internet", "Nifty Internet"),
        ("Nifty Ind Tourism", "Nifty India Tourism"), ("Nifty CPSE", "Nifty CPSE"), ("Nifty PSE", "Nifty PSE"), ("Nifty MNC", "Nifty MNC"),
        ("Nifty Rural", "Nifty Rural"), ("Nifty New Consump", "Nifty New Age Consumption"), ("Nifty IPO", "Nifty IPO"),
    ],
    "Strategy": [
        ("Nifty HighBeta 50", "Nifty High Beta 50"), ("Nifty Low Vol 50", "Nifty Low Volatility 50"), ("NIFTY Alpha 50", "Nifty Alpha 50"),
        ("Nifty Div Opps 50", "Nifty Dividend Opportunities 50"), ("Nifty500Momentm50", "Nifty500 Momentum 50"),
        ("Nifty50 Value 20", "Nifty50 Value 20"), ("NIFTY50 EQL Wgt", "Nifty50 Equal Weight"),
    ],
    "BSE": [
        ("BSE_INDEX|BANKEX", "BSE Bankex"), ("BSE_INDEX|BSE100", "BSE 100"), ("BSE_INDEX|BSE200", "BSE 200"), ("BSE_INDEX|BSE500", "BSE 500"),
        ("BSE_INDEX|SNXT50", "BSE Sensex Next 50"), ("BSE_INDEX|SENSEX50", "BSE Sensex 50"), ("BSE_INDEX|MID150", "BSE 150 Midcap"),
        ("BSE_INDEX|SML250", "BSE 250 Smallcap"), ("BSE_INDEX|LMI250", "BSE 250 LargeMidcap"), ("BSE_INDEX|MIDSEL", "BSE Midcap Select"),
        ("BSE_INDEX|SMLSEL", "BSE Smallcap Select"), ("BSE_INDEX|AUTO", "BSE Auto"), ("BSE_INDEX|BSEIT", "BSE IT"), ("BSE_INDEX|METAL", "BSE Metal"),
        ("BSE_INDEX|REALTY", "BSE Realty"), ("BSE_INDEX|ENERGY", "BSE Energy"), ("BSE_INDEX|BSEHC", "BSE Healthcare"), ("BSE_INDEX|BSEFMC", "BSE FMCG"),
        ("BSE_INDEX|BSEPSU", "BSE PSU"), ("BSE_INDEX|FINSER", "BSE Financial Services"), ("BSE_INDEX|INFRA", "BSE India Infrastructure"),
        ("BSE_INDEX|CPSE", "BSE CPSE"), ("BSE_INDEX|TECK", "BSE Teck"), ("BSE_INDEX|OILGAS", "BSE Oil & Gas"), ("BSE_INDEX|POWER", "BSE Power"),
        ("BSE_INDEX|INDDEF", "BSE India Defence"), ("BSE_INDEX|BSECD", "BSE Consumer Durables"), ("BSE_INDEX|BSECG", "BSE Capital Goods"),
    ],
}


def _build_more():
    import re as _re
    out, seen = [], set(s for s, _ in INDICES) | set(CORE)
    for group, items in _MORE.items():
        for raw, name in items:
            if raw.startswith("BSE_INDEX|"):
                ikey, code = raw, "BSE" + _re.sub(r"[^A-Z0-9]", "", raw.split("|")[1].upper()).replace("BSE", "", 1)
            else:
                ikey, code = "NSE_INDEX|" + raw, _re.sub(r"[^A-Z0-9]", "", raw.upper())
            if code in seen:
                code = code + "IDX"
            seen.add(code)
            out.append((code, name, group, ikey))
    return out


MORE_INDICES = _build_more()
for _c, _n, _g, _k in MORE_INDICES:
    NAME[_c] = _n
    INDEX_SET.add(_c)
    nse_service.upstox.INDEX_KEYS[_c] = _k


def bg(fn):
    """Run a worker as a low-priority background job (see the request throttle in upstox_service)."""
    import functools

    @functools.wraps(fn)
    def wrapper(*a, **k):
        _BG.on = getattr(_BG, "on", 0) + 1
        try:
            return fn(*a, **k)
        finally:
            _BG.on -= 1
    return wrapper


ACRONYMS = {
    "HDFC", "ICICI", "SBI", "LIC", "ITC", "TCS", "NTPC", "ONGC", "BHEL", "HAL", "BEL", "BDL", "IRCTC", "IRFC", "IDFC", "IDBI", "PNB", "UPL",
    "DLF", "GAIL", "NMDC", "SAIL", "MRF", "TVS", "NHPC", "SJVN", "PFC", "REC", "JSW", "JK", "CESC", "HCL", "KPIT", "KEI", "NCC", "NBCC",
    "NALCO", "MCX", "CDSL", "BSE", "IEX", "IGL", "MGL", "HUDCO", "RVNL", "CAMS", "ABB", "ACC", "AU", "IIFL", "IREDA", "CG", "GMR", "GNFC",
    "HFCL", "IOC", "BPCL", "HPCL", "AMC", "LTD", "GIC", "ICICIPRU", "SRF", "PI", "APL", "OFSS", "UNO", "RBL", "IDFC", "L&T", "M&M", "JSPL",
    "TATA", "NMDC", "CRISIL", "BSE", "NSE", "ITI", "IRB", "GE", "SBFC", "DCM", "KFIN", "PG", "LTTS", "NLC", "NMDC", "UTI",
}
SMALL_WORDS = {"OF", "AND", "THE", "FOR", "IN", "&", "TO", "AT"}
SPECIAL_NAMES = {
    "M&M": "Mahindra & Mahindra", "BAJAJ-AUTO": "Bajaj Auto", "LT": "Larsen & Toubro", "HINDUNILVR": "Hindustan Unilever",
    "HDFCBANK": "HDFC Bank", "ICICIBANK": "ICICI Bank", "SBIN": "State Bank of India", "KOTAKBANK": "Kotak Mahindra Bank",
    "AXISBANK": "Axis Bank", "TCS": "Tata Consultancy Services", "INFY": "Infosys", "RELIANCE": "Reliance Industries",
    "TMPV": "Tata Motors Passenger Vehicles", "TMCV": "Tata Motors Commercial Vehicles", "ETERNAL": "Eternal (Zomato)", "BHARTIARTL": "Bharti Airtel",
    "NESTLEIND": "Nestle India", "ASIANPAINT": "Asian Paints", "MARUTI": "Maruti Suzuki India", "SUNPHARMA": "Sun Pharmaceutical",
    "POWERGRID": "Power Grid Corporation", "HCLTECH": "HCL Technologies", "TECHM": "Tech Mahindra", "BAJFINANCE": "Bajaj Finance",
    "BAJAJFINSV": "Bajaj Finserv", "ULTRACEMCO": "UltraTech Cement", "DRREDDY": "Dr. Reddy's Laboratories", "DIVISLAB": "Divi's Laboratories",
    "HDFCLIFE": "HDFC Life Insurance", "SBILIFE": "SBI Life Insurance", "ICICIGI": "ICICI Lombard General Insurance", "ICICIPRULI": "ICICI Prudential Life Insurance",
    "LICI": "Life Insurance Corporation of India", "LICHSGFIN": "LIC Housing Finance", "ADANIENT": "Adani Enterprises", "ADANIPORTS": "Adani Ports & SEZ",
    "INDUSINDBK": "IndusInd Bank", "BANKBARODA": "Bank of Baroda", "PNB": "Punjab National Bank", "HEROMOTOCO": "Hero MotoCorp", "EICHERMOT": "Eicher Motors",
    "TATASTEEL": "Tata Steel", "TATAPOWER": "Tata Power", "TATACONSUM": "Tata Consumer Products", "JSWSTEEL": "JSW Steel", "COALINDIA": "Coal India",
    "NIFTY": "Nifty 50", "BANKNIFTY": "Nifty Bank", "FINNIFTY": "Nifty Financial Services", "MIDCPNIFTY": "Nifty Midcap Select", "NIFTYNXT50": "Nifty Next 50",
    "SENSEX": "BSE Sensex", "INDIAVIX": "India VIX",
}


def _nice(name, sym):
    """Proper Indian company name: acronyms stay upper-case (HDFC, ICICI, ABB), small words lower-case, legal suffixes dropped."""
    if sym in SPECIAL_NAMES:
        return SPECIAL_NAMES[sym]
    if not name:
        return sym
    import re as _re
    t = _re.sub(r"\b(LIMITED|LTD\.?|CORPORATION OF INDIA|PRIVATE|PVT)\b\.?", "", name.upper()).strip(" .,-")
    words = []
    for w in t.split():
        if w in ACRONYMS or (len(w) <= 3 and any(ch.isdigit() for ch in w)):
            words.append(w)
        elif w in SMALL_WORDS and words:
            words.append(w.lower())
        else:
            words.append(w.capitalize())
    out = " ".join(words).strip()
    return out or sym


def ensure_universe():
    """Every stock with listed options (~210) from Upstox's instrument master, refreshed every 6 hours."""
    if time.time() - _uni["t"] < 6 * 3600 and len(STOCKS) > len(CORE):
        return
    try:
        fo = nse_service.upstox.fo_universe()
        if not fo["stocks"]:
            return
        new = sorted(((sym, CORE_NAME.get(sym) or _nice(nm, sym), CORE_SECTOR.get(sym, "F&O")) for sym, nm in fo["stocks"].items()), key=lambda x: x[0])
        STOCKS[:] = new
        for sym, nm, sec in new:
            NAME[sym] = nm
            SECTOR[sym] = sec
        for sym, nm in nse_service.upstox.eq_names().items():   # every listed NSE equity (also non-F&O):
            if sym not in NAME:                                  # quotes/plans for the cash-universe Picks
                NAME[sym] = _nice(nm, sym)                       # and the stock trader work on any instance
        _uni["t"] = time.time()
    except Exception as exc:
        print("[universe] refresh failed:", exc)
        _uni["t"] = time.time() - 6 * 3600 + 300   # retry in 5 minutes


_cache = {}
_QSYM = {}    # symbol -> (time, quote): requests with overlapping symbol sets share upstream calls
_QLAST = {}   # last good quote payloads, served (flagged stale) when Upstox rate-limits us


def _cached_ok(key, ttl, fn, short=15):
    """fn returns (value, complete). Incomplete results (e.g. a failed chunk after a 429) are only cached briefly."""
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < hit[2]:
        return hit[1]
    val, ok = fn()
    _cache[key] = (time.time(), val, ttl if ok else short)
    return val


def _cached(key, ttl, fn):
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < (hit[2] if len(hit) > 2 else ttl):
        return hit[1]
    val = fn()
    _cache[key] = (time.time(), val, ttl)
    return val


def _shared(key, ttl, fn):
    """Share one Upstox answer between every server instance for `ttl` seconds (Redis, or a local file without Redis).
    N instances used to make N identical Upstox calls per refresh; now the first one asks and the rest read."""
    got = shared_cache.get(key)
    if got is not None:
        return got
    val = fn()
    if val:
        shared_cache.set(key, val, max(1, int(ttl)))
    return val


_REFRESH_AT = {}


def _known_quote(s):
    """Symbols of the app's own universe (F&O stocks, indices, extra indices)."""
    return s in NAME or any(s == i for i, _ in INDICES) or any(s == c for c, _n, _g, _k in MORE_INDICES)


def _allow_refresh(name, gap_live=30, gap_closed=180):
    """`?refresh=true` skips the cache. A user (or a stuck script) pressing Refresh in a loop used to re-run the whole scan every
    time - hundreds of Upstox calls each - and burn the 30-minute budget for everyone. A refresh inside the gap is answered from the cache."""
    now, gap = time.time(), gap_live if market_open() else gap_closed
    if now - _REFRESH_AT.get(name, 0) < gap:
        return False
    _REFRESH_AT[name] = now
    return True


def _key(sym):
    key, _is_index = nse_service.upstox._resolve_underlying(sym)
    return key


def market_open():
    import nse_calendar
    return nse_calendar.session_open(datetime.now(IST))      # exchange holidays count as closed


def _num(v, d=0.0):
    try:
        return float(v) if v is not None else d
    except (TypeError, ValueError):
        return d


@router.get("/universe")
def universe():
    ensure_universe()
    return {
        "stocks": [{"s": s, "n": n, "sec": sec} for s, n, sec in STOCKS],
        "indices": [{"s": s, "n": n} for s, n in INDICES],
        "more": [{"s": c, "n": n, "g": g} for c, n, g, _k in MORE_INDICES],
    }


def _year_range(symbol, key):
    """52-week high/low computed from daily candles.

    Upstox's live quote payload only carries year_high/year_low for equity
    instruments, not for indices - index quotes always come back 0/0 there.
    Falls back to scanning ~370 days of daily candles for those. Cached per
    calendar day (this barely moves intraday) so it's one extra network call
    per index per day, not per request.
    """
    def compute():
        try:
            end = date.today()
            start = end - timedelta(days=370)
            rows = nse_service.upstox.fetch_historical_candles(key, "days", "1", end.isoformat(), start.isoformat())
            highs = [_num(r.get("high")) for r in rows if _num(r.get("high")) > 0]
            lows = [_num(r.get("low")) for r in rows if _num(r.get("low")) > 0]
            return (max(highs), min(lows)) if highs and lows else (0.0, 0.0)
        except Exception:
            return (0.0, 0.0)
    return shared_cache.fetch(f"yr52|{symbol}|{date.today().isoformat()}", 20 * 3600, compute)


_YR_QUEUE, _YR_BUSY = [], threading.Event()


def _year_range_lazy(symbol, key):
    """52-week range without blocking the quote answer: use the cached value if there is one, otherwise queue it for a
    single background worker (a first quote request of the day used to make ~100 candle calls in a row, in the foreground,
    and starve the charts). Until it is filled the range shows as unknown."""
    hit = shared_cache.get(f"yr52|{symbol}|{date.today().isoformat()}")
    if hit:
        return tuple(hit)
    if (symbol, key) not in _YR_QUEUE:
        _YR_QUEUE.append((symbol, key))
    if not _YR_BUSY.is_set():
        _YR_BUSY.set()

        def worker():
            try:
                with background():
                    while _YR_QUEUE:
                        sy, ky = _YR_QUEUE.pop(0)
                        _year_range(sy, ky)
                        time.sleep(0.35)
            finally:
                _YR_BUSY.clear()
        threading.Thread(target=worker, daemon=True, name="yr52-fill").start()
    return (0.0, 0.0)


@router.get("/quotes")
def quotes(symbols: str = ""):
    ensure_universe()
    syms = [x.strip().upper() for x in symbols.split(",") if x.strip()] or \
        [s for s, _ in INDICES] + [c for c, _n, _g, _k in MORE_INDICES] + [s for s, _, _ in STOCKS]
    syms = syms[:500]

    def fetch(names):
        keymap = {}
        for s in names:
            try:
                if not _known_quote(s) and not nse_service.upstox.is_listed_equity(s):
                    continue                         # not a real NSE equity (REIT / typo): never send it to Upstox
                keymap[_key(s)] = s
            except Exception:
                continue
        if not keymap:
            return []
        raw = nse_service.upstox._full_quotes(list(keymap.keys()))
        out = []
        for k, q in raw.items():
            s = keymap.get(k)
            if not s:
                continue
            o = q.get("ohlc") or {}
            last = _num(q.get("last_price"))
            net = _num(q.get("net_change"))
            prev = _num(q.get("prev_close_price")) or (last - net if last else 0.0)
            yh, yl = _num(q.get("year_high")), _num(q.get("year_low"))
            if not yh or not yl:
                yh, yl = _year_range_lazy(s, k)
            out.append({
                "s": s, "last": last, "prev": prev,
                "open": _num(o.get("open")), "high": _num(o.get("high")), "low": _num(o.get("low")),
                "vol": _num(q.get("volume")) or _num(o.get("volume")),
                "bid": _num(((q.get("depth") or {}).get("buy") or [{}])[0].get("price")),
                "ask": _num(((q.get("depth") or {}).get("sell") or [{}])[0].get("price")),
                "yh": yh, "yl": yl,
            })
        if not out and keymap:
            raise RuntimeError("Upstox returned no quotes")     # never cache an empty answer
        return out

    explicit = bool(symbols.strip())
    ck = "q|" + ",".join(syms)
    slast = "qs-last|" + hashlib.md5(",".join(syms).encode()).hexdigest()
    stale, why = False, ""
    try:
        ttl = 8.0 if market_open() else 300        # live: 8s (was 4s); Upstox allows ~2000 calls / 30 min for the whole app - 4s polling of every
                                                   # symbol set by every open screen used most of it and tripped 429s ("Delayed")
        now = time.time()
        have, missing = {}, []
        for s in syms:
            h = _QSYM.get(s)
            if h and now - h[0] < ttl:
                have[s] = h[1]
            else:
                missing.append(s)
        if missing:
            qttl = 8 if market_open() else 120
            qkey = "qs|" + hashlib.md5(",".join(missing).encode()).hexdigest()
            got = _cached("qf|" + ",".join(missing), 7 if market_open() else 45, lambda: _shared(qkey, qttl, lambda: fetch(missing)))
            t0 = time.time()
            for q in got:
                _QSYM[q["s"]] = (t0, q)
                have[q["s"]] = q
        data = [have[s] for s in syms if s in have]
        if not data and syms and explicit and len(syms) <= 20:
            return {"quotes": [], "missing": syms, "marketOpen": market_open(), "asOf": datetime.now(IST).isoformat(), "stale": False}
        if not data and syms:
            raise RuntimeError("no quotes available")
        _QLAST[ck] = (time.time(), data)
        if missing:                       # we really refreshed: keep a copy every instance can fall back on (30 min)
            shared_cache.set(slast, {"t": time.time(), "data": data}, 1800)
    except Exception as e:
        last = _QLAST.get(ck)
        if not last:                      # a fresh serverless instance has no memory of its own: use the shared copy
            sh = shared_cache.get(slast)
            if sh:
                last = (sh["t"], sh["data"])
                _QLAST[ck] = last
        if last and time.time() - last[0] < 1800:
            data, stale, why = last[1], True, str(e)[:160]
        else:
            raise HTTPException(503, f"Live prices are temporarily unavailable: {str(e)[:160]}")
    out = {"quotes": data, "marketOpen": market_open(), "asOf": datetime.now(IST).isoformat(), "stale": stale}
    if stale:
        out["quotesAsOf"] = datetime.fromtimestamp(_QLAST[ck][0], IST).isoformat()
        out["reason"] = why
    return out


def quote_map(extra=()):
    """Quotes for internal callers (God's Eye, stock trader) WITHOUT extra Upstox calls: they read the same all-symbols batch
    that every open screen already refreshes (shared cache). Only symbols that batch does not cover are asked for, together."""
    out = {}
    try:
        out = {q["s"]: q for q in (quotes() or {}).get("quotes") or []}
    except Exception:
        pass
    miss = sorted({s.upper() for s in extra} - set(out))
    if miss:
        try:
            out.update({q["s"]: q for q in (quotes(symbols=",".join(miss[:60])) or {}).get("quotes") or []})
        except Exception:
            pass
    return out


# tf -> (kind, base interval minutes, history days, request window days, resample factor)
# Upstox serves daily+ history for decades but intraday only back to Jan 2022, and
# caps one request at ~1 month (<=15m) / ~85 days (60m).
TF = {
    "1m": ("min", "1", 28, 28, 1), "5m": ("min", "5", 90, 28, 1), "15m": ("min", "15", 365, 28, 1),
    "1H": ("min", "60", 1830, 85, 1), "4H": ("min", "60", 1830, 85, 4),
    "1D": ("day", "1", 1830, 0, 1), "1W": ("day", "1", 1830, 0, 1), "1M": ("day", "1", 1830, 0, 1),
}
HIST_TTL = 6 * 3600
_LAST_GOOD = {}     # last non-empty candle response per request, served if upstream fails
MAX_HIST_DAYS = 14610     # 40 years: the longest chart history offered


NATIVE_MIN = {1, 2, 3, 5, 10, 15, 30, 45, 60}   # intervals Upstox serves directly
BASE_DAYS = {1: 28, 2: 60, 3: 90, 5: 90, 10: 180, 15: 365, 30: 730, 45: 730, 60: 1830}


def _parse_tf(tf):
    """Any timeframe like 1m, 7m, 2H, 3D, 2W, 3M -> how to build it from Upstox data."""
    m = re.fullmatch(r"(\d{1,3})([mHDWM])", tf or "")
    if not m:
        raise HTTPException(400, "Timeframe must look like 5m, 2H, 3D, 2W or 3M")
    n, u = int(m.group(1)), m.group(2)
    lim = {"m": 720, "H": 24, "D": 30, "W": 8, "M": 12}
    if n < 1 or n > lim[u]:
        raise HTTPException(400, f"{u} timeframe must be between 1 and {lim[u]}")
    if u in "mH":
        mins = n if u == "m" else n * 60
        if mins in NATIVE_MIN:
            base, factor = mins, 1
        else:
            base = next(b for b in (60, 30, 15, 10, 5, 3, 2, 1) if mins % b == 0)
            factor = mins // base
        return {"kind": "min", "interval": str(base), "days": BASE_DAYS.get(base, 90),
                "window": 28 if base <= 15 else 85, "factor": factor, "unit": u, "n": n, "sec": mins * 60}
    return {"kind": "day", "interval": "1", "days": 1830, "window": 0, "factor": 1, "unit": u, "n": n,
            "sec": n * {"D": 86400, "W": 604800, "M": 2592000}[u]}


def _group_n(bars, n, keyfn):
    """Merge consecutive bars into n-period buckets anchored to the calendar (stable as data slides)."""
    out, cur, k0 = [], None, None
    for b in bars:
        k = keyfn(_bar_date(b)) // n
        if k != k0:
            if cur:
                out.append(cur)
            k0 = k
            cur = dict(b)
        else:
            cur["h"] = max(cur["h"], b["h"])
            cur["l"] = min(cur["l"], b["l"])
            cur["c"] = b["c"]
            cur["v"] += b["v"]
    if cur:
        out.append(cur)
    return out


def _bar(c):
    t = datetime.fromisoformat(c["time"]).timestamp() * 1000
    return {"t": int(t), "o": c["open"], "h": c["high"], "l": c["low"], "c": c["close"], "v": c["volume"]}


def _resample(bars, n):
    out, cur, day = [], None, None
    for b in bars:
        d = datetime.fromtimestamp(b["t"] / 1000, IST).date()
        if cur is None or d != day or cur["n"] >= n:
            if cur:
                out.append(cur)
            cur = {**b, "n": 1}
            day = d
        else:
            cur["h"] = max(cur["h"], b["h"])
            cur["l"] = min(cur["l"], b["l"])
            cur["c"] = b["c"]
            cur["v"] += b["v"]
            cur["n"] += 1
    if cur:
        out.append(cur)
    for b in out:
        b.pop("n", None)
    return out


def _ist_midnight_ms(d):
    return int(datetime(d.year, d.month, d.day, tzinfo=IST).timestamp() * 1000)


def _bar_date(b):
    return datetime.fromtimestamp(b["t"] / 1000, IST).date()


def _group(daily, keyfn):
    out, cur, k0 = [], None, None
    for b in daily:
        k = keyfn(_bar_date(b))
        if k != k0:
            if cur:
                out.append(cur)
            k0 = k
            d = _bar_date(b)
            anchor = d - timedelta(days=d.weekday()) if isinstance(k, tuple) and k[0] == "w" else d.replace(day=1)
            cur = {"t": _ist_midnight_ms(anchor), "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b["v"]}
        else:
            cur["h"] = max(cur["h"], b["h"])
            cur["l"] = min(cur["l"], b["l"])
            cur["c"] = b["c"]
            cur["v"] += b["v"]
    if cur:
        out.append(cur)
    return out


def _weekly(daily):
    return _group(daily, lambda d: ("w", d - timedelta(days=d.weekday())))


def _monthly(daily):
    return _group(daily, lambda d: ("m", d.year, d.month))


def _dedupe(rows):
    seen, bars = set(), []
    for c in rows:
        b = _bar(c)
        if b["t"] in seen:
            continue
        seen.add(b["t"])
        bars.append(b)
    bars.sort(key=lambda b: b["t"])
    return bars


_HIST_FAILS = []


def _hist_rows(key, unit, interval, days, window):
    """Historical candles up to YESTERDAY, fetched in parallel request windows."""
    up = upstox_service
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=days)
    if not window:
        return up.fetch_historical_candles(key, unit, interval, end.isoformat(), start.isoformat())
    spans, hi = [], end
    while hi > start:
        lo = max(start, hi - timedelta(days=window))
        spans.append((hi, lo))
        hi = lo - timedelta(days=1)

    def one(span):
        for attempt in range(2):
            try:
                return up.fetch_historical_candles(key, unit, interval, span[0].isoformat(), span[1].isoformat())
            except Exception as exc:
                if "UDAPI1148" in str(exc):          # outside the window Upstox serves: genuinely no data
                    return []
                time.sleep(1.0 + attempt)
        _HIST_FAILS.append(span)
        return []

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        parts = list(pool.map(one, spans))
    return [c for part in parts for c in part]


def _today_daily_bar(key):
    now = datetime.now(IST)
    if not (__import__("nse_calendar").is_trading_day(now.date()) and now.hour * 60 + now.minute >= 9 * 60 + 15):
        return None
    try:
        mins = sorted(upstox_service.fetch_intraday_candles(key, "minutes", "1"), key=lambda c: c["time"])
    except Exception:
        return None
    if not mins:
        return None
    return {"t": _ist_midnight_ms(now.date()), "o": mins[0]["open"], "h": max(m["high"] for m in mins),
            "l": min(m["low"] for m in mins), "c": mins[-1]["close"], "v": sum(m["volume"] for m in mins)}


@router.get("/candles")
def candles(symbol: str = "", tf: str = "1D", ikey: str = "", frm: str = Query("", alias="from"), to: str = "", recent: int = 0):
    """recent=N (intraday only): just the last N calendar days - one Upstox request instead of up to a dozen - so a chart can paint
    at once; the client then asks for the full history in the background and swaps it in."""
    cfg = _parse_tf(tf)
    kind, interval, days, window, factor = cfg["kind"], cfg["interval"], cfg["days"], cfg["window"], cfg["factor"]
    sym = symbol.upper()
    if ikey:
        # Option / derivative contract: history only exists for the contract's life
        if not re.match(r"^(NSE|BSE)_FO\|\d+$", ikey):
            raise HTTPException(400, "ikey must look like NSE_FO|12345")
        days = min(days, 120)
        sym = ikey
    elif not sym:
        raise HTTPException(400, "symbol or ikey required")
    quick = bool(recent) and kind == "min" and not frm and not to
    if quick:
        days = max(3, min(int(recent), 30))
        window = max(window, days + 1)                  # a single request window
    d_from = d_to = None
    try:
        if frm:
            d_from = date.fromisoformat(frm)
        if to:
            d_to = date.fromisoformat(to)
    except ValueError:
        raise HTTPException(400, "from / to must be YYYY-MM-DD")
    capped = False
    if d_from and d_from > date.today():
        raise HTTPException(400, "from must not be in the future")
    if d_from and d_from < date.today() - timedelta(days=MAX_HIST_DAYS):
        d_from, capped = date.today() - timedelta(days=MAX_HIST_DAYS), True   # history is capped at 40 years
    if d_to and d_from and d_to < d_from:
        raise HTTPException(400, "to must not be before from")
    if d_from and not ikey:
        need = (date.today() - d_from).days
        if kind == "day":
            days = min(max(need, 30), MAX_HIST_DAYS)
        else:
            cap = {"1": 365, "2": 365, "3": 365, "5": 730}.get(interval, 1830)   # intraday exists only from Jan 2022
            days = min(max(need, days), cap)
    span = 3600 if kind == "day" and days > 3650 else window

    def fetch():
        key = ikey or _key(sym)
        today = date.today().isoformat()
        if kind == "day":
            def _dh():
                n0 = len(_HIST_FAILS)
                rows = _dedupe(_hist_rows(key, "days", "1", days, span if kind == "day" else 0))
                return rows, len(_HIST_FAILS) == n0 and bool(rows)
            def _dh_shared():
                k2 = f"hd|{ikey or sym}|{days}|{today}"
                got = shared_cache.get(k2)
                if got:
                    return got, True
                rows, ok = _dh()
                if ok and rows:
                    shared_cache.set(k2, rows, 20 * 3600)
                return rows, ok
            hist = _cached_ok(f"hd|{ikey or sym}|{days}|{today}", HIST_TTL, _dh_shared)
            bars = list(hist)
            tb = None if (d_to and d_to < date.today()) else _today_daily_bar(key)
            if tb and (not bars or _bar_date(bars[-1]) < _bar_date(tb)):
                bars.append(tb)
            elif tb and _bar_date(bars[-1]) == _bar_date(tb):
                bars[-1] = tb
            u, nn = cfg["unit"], cfg["n"]
            if u == "D" and nn > 1:
                bars = _group_n(bars, nn, lambda d: d.toordinal())
            elif u == "W":
                bars = _weekly(bars)
                if nn > 1:
                    bars = _group_n(bars, nn, lambda d: (d - timedelta(days=d.weekday())).toordinal() // 7)
            elif u == "M":
                bars = _monthly(bars)
                if nn > 1:
                    bars = _group_n(bars, nn, lambda d: d.year * 12 + d.month - 1)
            if d_from:
                lo = _ist_midnight_ms(d_from)
                bars = [b for b in bars if b["t"] >= lo]
            if d_to:
                hi = _ist_midnight_ms(d_to) + 86399000
                bars = [b for b in bars if b["t"] <= hi]
            return bars
        def _mh():
            n0 = len(_HIST_FAILS)
            rows = _dedupe(_hist_rows(key, "minutes", interval, days, window))
            return rows, len(_HIST_FAILS) == n0
        def _mh_shared():
            k2 = f"hm|{ikey or sym}|{interval}|{days}|{today}"
            got = shared_cache.get(k2)
            if got:
                return got, True
            rows, ok = _mh()
            if ok and rows:
                shared_cache.set(k2, rows, 20 * 3600)
            return rows, ok
        hist = _cached_ok(f"hm|{ikey or sym}|{interval}|{days}|{today}", HIST_TTL, _mh_shared)
        try:
            live = _dedupe(upstox_service.fetch_intraday_candles(key, "minutes", interval))
        except Exception:
            live = []
        tmap = {b["t"]: b for b in hist}
        for b in live:
            tmap[b["t"]] = b
        bars = [tmap[k] for k in sorted(tmap)]
        if factor > 1:
            bars = _resample(bars, factor)
        # honour the requested window exactly (it used to be ignored for intraday bars)
        if d_from:
            lo = _ist_midnight_ms(d_from)
            bars = [b for b in bars if b["t"] >= lo]
        if d_to:
            hi = _ist_midnight_ms(d_to) + 86399000
            bars = [b for b in bars if b["t"] <= hi]
        return bars

    ckey = f"c|{sym}|{tf}|{frm}|{to}" + (f"|r{days}" if quick else "")

    def fetch_checked():
        b = fetch()
        if not b and not ikey:
            # an empty answer for a normal symbol is an upstream hiccup (rate limit at the open, a dropped chunk),
            # never a real "no data" - raising keeps it out of the cache so the next request tries again
            raise RuntimeError("Upstox returned no candles")
        return b

    try:
        bars = _cached(ckey, 4 if market_open() else 60, fetch_checked)
        if bars:
            _LAST_GOOD[ckey] = bars
    except Exception as e:
        bars = _LAST_GOOD.get(ckey)                  # serve the last good chart rather than a blank one
        if not bars:
            raise HTTPException(503, f"Candles are temporarily unavailable, retrying: {str(e)[:120]}")
    first = bars[0]["t"] if bars else None
    note = "Charts show at most 40 years of history; the start date was moved to " + d_from.isoformat() + "." if capped else None
    if note:
        pass
    elif d_from and kind == "min" and d_from < date(2022, 1, 1):
        note = "Intraday history is available from Jan 2022 only."
    elif d_from and first and (first - _ist_midnight_ms(d_from)) > 7 * 86400000:
        note = "History for this timeframe starts " + datetime.fromtimestamp(first / 1000, IST).strftime("%d %b %Y") + "; earlier data is not provided by the data source."
    return {"symbol": sym, "tf": tf, "bars": bars, "from": frm or None, "to": to or None, "first": first, "note": note}


# ----------------------------- Option chain -----------------------------
@router.get("/chain")
def chain(symbol: str = "NIFTY", expiry: str = ""):
    ensure_universe()
    sym = symbol.upper().strip()
    if sym not in {s for s, _, _ in STOCKS} | {s for s, _ in INDICES if s != "INDIAVIX"}:
        raise HTTPException(400, f"{sym} has no option chain here")

    def build():
        data = nse_service.upstox.fetch_option_chain(sym, expiry or None)
        by = {}
        for r in data["rows"]:
            side = "ce" if r["type"] == "CE" else "pe"
            by.setdefault(r["strike"], {"strike": r["strike"]})[side] = {
                "key": r["instrumentKey"], "ltp": r["close"], "prev": r.get("prevClose") or 0,
                "open": r["open"], "high": r["high"], "low": r["low"], "oi": r["oi"],
                "oiChg": r.get("oiChgRaw") or 0, "vol": r["vol"], "bid": r.get("bid") or 0, "ask": r.get("ask") or 0,
            }
        rows = [by[k] for k in sorted(by)]
        spot = data.get("spot") or 0
        atm = min(rows, key=lambda x: abs(x["strike"] - spot))["strike"] if rows and spot else None
        lot = int(data.get("lotSize") or 0)          # straight from the contract list (also covers BSE: SENSEX)
        if lot < 1:
            try:
                lot = int((nse_service.upstox.fo_universe().get("lots") or {}).get(sym) or 1)
            except Exception:
                lot = 1
        out = {"symbol": sym, "lot": lot, "spot": spot, "expiry": data.get("targetExpiry"), "expiries": data.get("expiryDates") or [],
               "atm": atm, "rows": rows, "provider": "Upstox", "asOf": datetime.now(IST).isoformat()}
        try:                                     # expiry diary: remember the contract keys while they still trade
            import expiry_book
            expiry_book.record_chain_book(out)
        except Exception:
            pass
        return out

    def shared_build():
        # second tier shared by every serverless instance: a cold instance answers from Upstash instead of
        # making three Upstox calls (contracts, chain, ~200 quotes) before the page can show anything
        import shared_cache
        sk, ttl = f"chain:v1:{sym}:{expiry}", (6 if market_open() else 600)
        try:
            hit = shared_cache.get(sk)
            if hit and time.time() - hit.get("_ts", 0) < ttl:
                return hit
        except Exception:
            pass
        val = build()
        try:
            shared_cache.set(sk, dict(val, _ts=time.time()), ttl + 5)
        except Exception:
            pass
        return val

    try:
        return _cached(f"chain|{sym}|{expiry}", 3 if market_open() else 45, shared_build)
    except Exception as e:
        raise HTTPException(502, f"Option chain failed: {e}")


@router.get("/oquote")
def oquote(keys: str):
    ks = [k.strip() for k in keys.split(",") if re.match(r"^(NSE|BSE)_FO\|\d+$", k.strip())][:30]
    if not ks:
        raise HTTPException(400, "keys required")
    try:
        okey = "oqs|" + hashlib.md5(",".join(sorted(ks)).encode()).hexdigest()
        raw = _cached("oq|" + ",".join(sorted(ks)), 8 if market_open() else 120,       # 8 s (was 4 s): see quotes()
                      lambda: _shared(okey, 8 if market_open() else 120, lambda: nse_service.upstox._full_quotes(ks)))
    except Exception as e:
        raise HTTPException(503, f"Option prices are temporarily unavailable: {str(e)[:140]}")
    out = []
    for k, q in raw.items():
        o = q.get("ohlc") or {}
        last = _num(q.get("last_price"))
        out.append({"key": k, "last": last, "prev": _num(q.get("prev_close_price")) or (last - _num(q.get("net_change"))),
                    "open": _num(o.get("open")), "high": _num(o.get("high")), "low": _num(o.get("low")),
                    "vol": _num(q.get("volume")) or _num(o.get("volume")), "oi": _num(q.get("oi")),
                    "oiPrev": _num(q.get("previous_oi")),
                    "bid": _num(((q.get("depth") or {}).get("buy") or [{}])[0].get("price")),
                    "ask": _num(((q.get("depth") or {}).get("sell") or [{}])[0].get("price"))})
    return {"quotes": out, "marketOpen": market_open(), "asOf": datetime.now(IST).isoformat()}


BOARD_FUT = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"]


@router.get("/futures/board")
def futures_board():
    """Index futures for the Picks screen: near and next month of each index with price, change, basis to spot and OI change.
    One quote request for every contract and spot together (cached 4 s while the market is open)."""
    def build():
        up = nse_service.upstox
        plan, keys = [], []
        for und in BOARD_FUT:
            try:
                cons = up.futures_for(und)[:2]
                spot_key = _key(und)
            except Exception:
                continue
            if cons:
                plan.append((und, spot_key, cons))
                keys += [spot_key] + [c["key"] for c in cons]
        raw = up._full_quotes(keys) if keys else {}
        q = lambda k: raw.get(k) or {}
        items = []
        for und, sk, cons in plan:
            spot = _num(q(sk).get("last_price"))
            rows = []
            for c in cons:
                r = q(c["key"])
                last = _num(r.get("last_price"))
                if not last:
                    continue
                prev = _num(r.get("prev_close_price")) or (last - _num(r.get("net_change")))
                oi, oi0 = _num(r.get("oi")), _num(r.get("previous_oi"))
                rows.append({"key": c["key"], "label": c["label"], "expiry": c["expiry"], "lot": c["lot"], "last": last,
                             "chgPct": round((last / prev - 1) * 100, 2) if prev else None,
                             "basis": round(last - spot, 2) if spot else None, "basisPct": round((last / spot - 1) * 100, 3) if spot else None,
                             "oi": oi, "oiChgPct": round((oi / oi0 - 1) * 100, 2) if oi and oi0 else None,
                             "vol": _num(r.get("volume"))})
            if rows:
                items.append({"und": und, "spot": spot, "contracts": rows})
        if not items:
            raise RuntimeError("no futures quotes")
        return items
    try:
        items = _cached("futboard", 4 if market_open() else 120, lambda: _shared("futboard", 4 if market_open() else 120, build))
    except Exception as e:
        raise HTTPException(503, f"Futures are temporarily unavailable: {str(e)[:140]}")
    return {"items": items, "marketOpen": market_open(), "asOf": datetime.now(IST).isoformat()}


@router.get("/futures")
def futures(symbol: str = "NIFTY"):
    """Futures contracts (all listed expiries, nearest first) of an index / F&O stock with their live quotes - the Trade screen opens
    any of them as a chart (same candles / indicators as the options: /candles?ikey=NSE_FO|...)."""
    sym = symbol.upper().strip()
    try:
        cons = nse_service.upstox.futures_for(sym)
    except Exception as e:
        raise HTTPException(503, f"Futures list is temporarily unavailable: {str(e)[:140]}")
    if not cons:
        raise HTTPException(404, f"{sym} has no listed futures")
    cons = cons[:3]                                  # near / next / far month - what NSE trades actively
    keys = [c["key"] for c in cons]
    quotes = {}
    try:
        okey = "fq|" + hashlib.md5(",".join(keys).encode()).hexdigest()
        raw = _cached("fq|" + ",".join(keys), 4 if market_open() else 120,
                      lambda: _shared(okey, 4 if market_open() else 120, lambda: nse_service.upstox._full_quotes(keys)))
        for k, q in raw.items():
            o = q.get("ohlc") or {}
            last = _num(q.get("last_price"))
            quotes[k] = {"last": last, "prev": _num(q.get("prev_close_price")) or (last - _num(q.get("net_change"))),
                         "open": _num(o.get("open")), "high": _num(o.get("high")), "low": _num(o.get("low")),
                         "vol": _num(q.get("volume")) or _num(o.get("volume")), "oi": _num(q.get("oi")), "oiPrev": _num(q.get("previous_oi")),
                         "bid": _num(((q.get("depth") or {}).get("buy") or [{}])[0].get("price")),
                         "ask": _num(((q.get("depth") or {}).get("sell") or [{}])[0].get("price"))}
    except Exception:
        pass                                         # contracts still list; prices arrive with the next poll
    return {"symbol": sym, "contracts": [dict(c, **(quotes.get(c["key"]) or {})) for c in cons],
            "marketOpen": market_open(), "asOf": datetime.now(IST).isoformat()}


# ----------------------------- Daily scan: Open = High / Open = Low -----------------------------
@router.get("/daily-scan")
def daily_scan(refresh: bool = False, limit: int = 16):
    """F&O stocks and indices trading with Open = Low (bullish) or Open = High (bearish) today,
    plus the ATM CE/PE contracts of each so the user can act on them straight away."""
    ensure_universe()
    limit = max(5, min(limit, 40))

    def build():
        up = nse_service.upstox
        names = [s for s, _ in INDICES if s != "INDIAVIX"] + [s for s, _, _ in STOCKS]
        keymap = {}
        for s in names:
            try:
                keymap[_key(s)] = s
            except Exception:
                pass
        qs = up._full_quotes(list(keymap.keys()))
        found = []
        for k, q in qs.items():
            sym = keymap.get(k)
            o = q.get("ohlc") or {}
            last, op, hi, lo = _num(q.get("last_price")), _num(o.get("open")), _num(o.get("high")), _num(o.get("low"))
            prev = _num(q.get("prev_close_price")) or (last - _num(q.get("net_change")))
            if not sym or last <= 0 or op <= 0 or hi <= lo or (hi - lo) < last * 0.001:
                continue
            # User rule (20 Oct 2026): Open = Low allows the low to sit up to 10 points under the open (and price is back
            # at / above the open) -> BUY; Open = High allows the high up to 10 points over the open (price at / below
            # the open) -> SELL. Stop-loss 3 points. 'exact' marks a true Open = Low / High.
            tol = max(0.05, last * 0.0002)
            is_ol = lo >= op - 10 and last >= op
            is_oh = hi <= op + 10 and last <= op and not is_ol
            if not (is_oh or is_ol):
                continue
            exact = abs(op - lo) <= tol if is_ol else abs(op - hi) <= tol
            chg = (last / prev - 1) * 100 if prev else 0.0
            found.append({
                "symbol": sym, "name": NAME.get(sym, sym), "type": "Index" if sym in INDEX_SET else "Stock",
                "sector": SECTOR.get(sym, ""), "ltp": round(last, 2), "prev": round(prev, 2), "chg": round(chg, 2),
                "open": op, "high": hi, "low": lo, "vol": _num(q.get("volume")) or _num(o.get("volume")),
                "status": "OPEN_LOW" if is_ol else "OPEN_HIGH", "exact": exact,
                "entry": round(last, 2), "sl": round(last - 3 if is_ol else last + 3, 2),
                "t1": round(last + 6 if is_ol else last - 6, 2), "t2": round(last + 9 if is_ol else last - 9, 2),
                "bias": "Bullish" if is_ol else "Bearish",
                "idea": (("Opened at the day low" if exact else "Low stayed within 10 points of the open") + " and price is back at or above the open — "
                         "buyers in control."
                         if is_ol else ("Opened at the day high" if exact else "High stayed within 10 points of the open") + " and price is at or below the open — "
                         "sellers in control."),
            })
        found.sort(key=lambda r: (not r["exact"], -abs(r["chg"])))
        total = len(found)
        deadline = time.time() + 20

        @bg
        def with_options(r):
            if time.time() > deadline:
                r["options"] = None
                return r
            try:
                c = chain(symbol=r["symbol"], expiry="")
                rows = c["rows"]
                i = next((n for n, x in enumerate(rows) if x["strike"] == c["atm"]), None)
                legs = []
                if i is not None:
                    for x in rows[max(0, i - 2): i + 3]:
                        for side in ("ce", "pe"):
                            leg = x.get(side)
                            if not leg or leg["ltp"] <= 0:
                                continue
                            t = 0.05
                            legs.append({"strike": x["strike"], "side": side.upper(), "key": leg["key"], "ltp": leg["ltp"],
                                         "prev": leg["prev"], "chg": round((leg["ltp"] / leg["prev"] - 1) * 100, 2) if leg["prev"] else 0.0,
                                         "open": leg["open"], "high": leg["high"], "low": leg["low"], "oi": leg["oi"], "vol": leg["vol"],
                                         "oh": leg["high"] > leg["low"] and abs(leg["open"] - leg["high"]) <= t,
                                         "ol": leg["high"] > leg["low"] and abs(leg["open"] - leg["low"]) <= t,
                                         "ol10": leg["open"] > 0 and leg["low"] >= leg["open"] - 10 and leg["ltp"] >= leg["open"],
                                         "sl": round(max(0.05, leg["ltp"] - 3), 2)})
                r["options"] = {"expiry": c["expiry"], "atm": c["atm"], "spot": c["spot"], "legs": legs}
            except Exception:
                r["options"] = None
            return r

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            top = list(pool.map(with_options, found[:limit]))
        return {"rows": top + [dict(r, options=None) for r in found[limit:]], "total": total, "detailed": len(top),
                "marketOpen": market_open(), "asOf": datetime.now(IST).isoformat()}

    if refresh and _allow_refresh("daily"):
        _cache.pop("daily", None)
    try:
        return _cached("daily", 60 if market_open() else 600, build)
    except Exception as e:
        old = _cache.get("daily")                         # budget used up / Upstox hiccup: show the last scan rather than an error
        if old:
            return {**old[1], "stale": True, "reason": str(e)[:120]}
        raise HTTPException(503 if isinstance(e, UpstoxRateLimited) else 502, f"Daily scan failed: {e}")


# ----------------------------- Global markets & futures (GIFT Nifty, US futures, Nasdaq ...) -----------------------------
GLOBAL_ITEMS = [
    ("NSEIX:NIFTY1!", "GIFT Nifty", "Index futures"), ("NSEIX:BANKNIFTY1!", "GIFT Bank Nifty", "Index futures"),
    ("CBOT_MINI:YM1!", "Dow Fut", "US futures"), ("CME_MINI:ES1!", "S&P 500 Fut", "US futures"),
    ("CME_MINI:NQ1!", "Nasdaq 100 Fut", "US futures"), ("NASDAQ:IXIC", "Nasdaq", "US indices"),
    ("NASDAQ:NDX", "Nasdaq 100", "US indices"), ("SP:SPX", "S&P 500", "US indices"), ("DJ:DJI", "Dow Jones", "US indices"),
    ("CBOE:VIX", "US VIX", "US indices"), ("MCX:GOLD1!", "Gold (MCX)", "Commodities"), ("MCX:CRUDEOIL1!", "Crude Oil (MCX)", "Commodities"),
    ("MCX:SILVER1!", "Silver (MCX)", "Commodities"), ("COMEX:GC1!", "Gold (COMEX)", "Commodities"), ("NYMEX:CL1!", "Crude (NYMEX)", "Commodities"), ("COMEX:SI1!", "Silver (COMEX)", "Commodities"),
    ("BITSTAMP:BTCUSD", "Bitcoin", "Crypto"), ("FX_IDC:USDINR", "USD / INR", "Currency"),
]


def _in_fmt(v, d=2):
    try:
        neg = v < 0
        whole, frac = f"{abs(v):.{d}f}".split(".") if d else (f"{abs(v):.0f}", "")
        if len(whole) > 3:
            head, tail = whole[:-3], whole[-3:]
            parts = []
            while len(head) > 2:
                parts.insert(0, head[-2:])
                head = head[:-2]
            if head:
                parts.insert(0, head)
            whole = ",".join(parts + [tail])
        return ("-" if neg else "") + whole + ("." + frac if d else "")
    except Exception:
        return str(v)


def _tv_global():
    import json as _json
    import urllib.request as _rq
    tickers = [t for t, _, _ in GLOBAL_ITEMS]
    body = _json.dumps({"symbols": {"tickers": tickers},
                        "columns": ["close", "change", "change_abs", "high", "low", "open", "update_mode"]}).encode()
    req = _rq.Request("https://scanner.tradingview.com/global/scan", data=body,
                      headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    raw = _json.load(_rq.urlopen(req, timeout=8))
    got = {x["s"]: x["d"] for x in raw.get("data", [])}
    out = []
    for t, name, grp in GLOBAL_ITEMS:
        d = got.get(t)
        if not d or d[0] is None:
            continue                                  # not returned -> not shown (nothing fabricated)
        mode = str(d[6] or "")
        out.append({"id": t, "name": name, "group": grp, "chart": not t.startswith("MCX:"), "price": d[0], "chgPct": round(d[1] or 0.0, 2), "chg": round(d[2] or 0.0, 2),
                    "high": d[3], "low": d[4], "open": d[5],
                    "mode": "live" if mode == "streaming" else "delayed", "delay": "10-15 min" if "delayed" in mode else None})
    return out


@router.get("/global")
def global_markets():
    try:
        items = _cached("global", 2, _tv_global)
    except Exception as e:
        raise HTTPException(502, f"Global markets unavailable: {e}")
    return {"items": items, "asOf": datetime.now(IST).isoformat(), "source": "TradingView feed (GIFT Nifty / MCX / crypto live, US instruments ~10 min delayed)"}


# ----------------------------- Global instrument candles (TradingView history, no login) -----------------------------
TV_RES = {"m": lambda n: str(n), "H": lambda n: str(n * 60), "D": lambda n: "1D" if n == 1 else f"{n}D", "W": lambda n: "1W" if n == 1 else f"{n}W", "M": lambda n: "1M" if n == 1 else f"{n}M"}
TV_IDS = {t for t, _, _ in GLOBAL_ITEMS if not t.startswith("MCX:")}


def _tv_history(symbol, resolution, count):
    import json as _json
    import random
    import re as _re
    import string
    import websocket

    def frame(m):
        return f"~m~{len(m)}~m~{m}"

    def msg(name, params):
        return frame(_json.dumps({"m": name, "p": params}, separators=(",", ":")))

    ws = websocket.create_connection("wss://data.tradingview.com/socket.io/websocket", origin="https://www.tradingview.com",
                                     timeout=10, header={"User-Agent": "Mozilla/5.0"})
    sid = "cs_" + "".join(random.choice(string.ascii_lowercase) for _ in range(12))
    try:
        ws.send(msg("set_auth_token", ["unauthorized_user_token"]))
        ws.send(msg("chart_create_session", [sid, ""]))
        ws.send(msg("resolve_symbol", [sid, "sds_sym_1", "=" + _json.dumps({"symbol": symbol, "adjustment": "splits"})]))
        ws.send(msg("create_series", [sid, "sds_1", "s1", "sds_sym_1", resolution, count, ""]))
        bars, t0 = [], time.time()
        while time.time() - t0 < 12:
            try:
                raw = ws.recv()
            except Exception:
                break
            for part in _re.split(r"~m~\d+~m~", raw):
                if not part:
                    continue
                if part.startswith("~h~"):
                    ws.send(frame(part))
                    continue
                try:
                    d = _json.loads(part)
                except Exception:
                    continue
                m = d.get("m")
                if m in ("timescale_update", "du"):
                    for _k, v in d["p"][1].items():
                        if isinstance(v, dict) and "s" in v:
                            bars = [x["v"] for x in v["s"]]
                elif m == "symbol_error":
                    raise HTTPException(403, "No chart data is available for this instrument")
                elif m in ("series_completed", "critical_error"):
                    return bars
        return bars
    finally:
        try:
            ws.close()
        except Exception:
            pass


@router.get("/gcandles")
def gcandles(id: str, tf: str = "1D", count: int = 1500):
    """Candles for GIFT Nifty, US futures / indices, Bitcoin and other global instruments."""
    if id not in TV_IDS:
        raise HTTPException(400, "Unsupported instrument (MCX charts need an exchange licence)")
    cfg = _parse_tf(tf)
    n, u = cfg["n"], cfg["unit"]
    if u in "mH":                                   # only these minute intervals reliably come back from the free feed
        mins = n if u == "m" else n * 60            # (10m, 45m, 2H, 3H return nothing) - everything else is built from a base
        plans = [(str(b), mins // b) for b in (240, 60, 30, 15, 5, 1) if mins % b == 0]
    else:
        plans = [(TV_RES[u](1), 1)]                # D / W / M: fetch the 1-period series and group it ourselves
    res, factor = plans[0]
    count = max(50, min(count, 5000))

    def fetch():
        rows = []
        coarse = [(r, 1) for r in ("15", "60") if u in "mH" and int(r) > mins]   # thin contracts (GIFT Bank Nifty) have no 1m/5m bars
        for pres, pf in plans[:2] + coarse:         # a base that comes back empty falls through to the next one
            rows = _tv_history(id, pres, min(5000, count * pf))
            if rows:
                break
        else:
            pf = 1
        out = [{"t": int(r[0] * 1000), "o": r[1], "h": r[2], "l": r[3], "c": r[4], "v": (r[5] if len(r) > 5 else 0) or 0} for r in rows]
        if pf > 1:
            out = _resample(out, pf)
        if u == "D" and n > 1:
            out = _group_n(out, n, lambda d: d.toordinal())
        elif u == "W" and n > 1:
            out = _group_n(out, n, lambda d: (d - timedelta(days=d.weekday())).toordinal() // 7)
        elif u == "M" and n > 1:
            out = _group_n(out, n, lambda d: d.year * 12 + d.month - 1)
        return out, bool(out)

    bars = _cached_ok(f"g|{id}|{res}|{factor}|{count}", 10, fetch, short=3)
    if not bars:
        raise HTTPException(502, "Global candles are unavailable right now")
    return {"id": id, "tf": tf, "bars": bars}


# ----------------------------- Token health -----------------------------
@router.get("/health")
def health():
    """Upstox token status for the UI banner. Never returns the token itself."""
    import base64
    import json
    import os

    tok = os.getenv("UPSTOX_ACCESS_TOKEN", "")
    out = {"configured": bool(tok), "state": "missing", "expiresAt": None, "daysLeft": None,
           "extended": None, "message": "UPSTOX_ACCESS_TOKEN is not set."}
    if not tok:
        return out
    if tok.count(".") == 2:
        try:
            part = tok.split(".")[1]
            d = json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
            if "exp" in d:
                exp = datetime.fromtimestamp(d["exp"], IST)
                out["expiresAt"] = exp.isoformat()
                out["daysLeft"] = round((exp - datetime.now(IST)).total_seconds() / 86400, 2)
            out["extended"] = bool(d.get("isExtended"))
        except Exception:
            pass

    def probe():
        # one probe per 5 minutes for ALL instances. Running out of request budget is not a broken feed: the
        # app keeps serving the last known prices, so it must not raise the red "Data feed issue" banner.
        try:
            nse_service.upstox._full_quotes([_key("NIFTY")])
            return {"e": ""}
        except UpstoxRateLimited:
            return {"e": "", "busy": True}
        except Exception as e:
            m = str(e)[:160]
            # a passing blip (rate limit worded differently, timeout, Upstox 5xx) is not a broken feed: the app keeps serving the
            # last prices - it used to raise the red "Data feed issue" banner for 5 minutes (and the page kept it for 30)
            if any(x in m.lower() for x in ("429", "rate", "too many", "last known", "timed out", "timeout", "502", "503", "504", "temporarily")):
                return {"e": "", "busy": True}
            return {"e": m}

    res = _cached("token-probe", 300, lambda: _shared("token-probe", 300, probe))
    err = res.get("e")
    if err:
        expired = "401" in err or "nvalid" in err or "xpired" in err
        out["state"] = "expired" if expired else "error"
        out["message"] = ("The Upstox token has expired or is invalid. Generate a new one and update UPSTOX_ACCESS_TOKEN in Vercel."
                          if expired else "Upstox is not responding right now: " + err)
    elif out["daysLeft"] is not None and out["daysLeft"] <= 7:
        hrs = max(0, out["daysLeft"] * 24)
        when = f"in {hrs:.0f} hour(s)" if out["daysLeft"] < 2 else f"in {out['daysLeft']:.0f} days"
        out["state"] = "expiring"
        out["message"] = f"The Upstox token expires {when}. Update UPSTOX_ACCESS_TOKEN in Vercel before then" + \
                         ("." if out["extended"] else " (use an extended token to avoid daily updates).")
    else:
        out["state"] = "ok"
        out["message"] = "Upstox connected." + (" Busy right now - prices may be a few seconds old." if res.get("busy") else "")
    return out


# ----------------------------- Recommendations -----------------------------
def _ema(vals, n):
    if len(vals) < n:
        return None
    k = 2 / (n + 1)
    e = sum(vals[:n]) / n
    for v in vals[n:]:
        e = v * k + e * (1 - k)
    return e


def _rsi(vals, n=14):
    if len(vals) <= n:
        return None
    g = l = 0.0
    for i in range(1, n + 1):
        d = vals[i] - vals[i - 1]
        g += max(d, 0)
        l += max(-d, 0)
    g /= n
    l /= n
    for i in range(n + 1, len(vals)):
        d = vals[i] - vals[i - 1]
        g = (g * (n - 1) + max(d, 0)) / n
        l = (l * (n - 1) + max(-d, 0)) / n
    return 100.0 if l == 0 else 100 - 100 / (1 + g / l)


def _atr(rows, n=14):
    trs = []
    for i in range(1, len(rows)):
        h, lo, pc = rows[i]["high"], rows[i]["low"], rows[i - 1]["close"]
        trs.append(max(h - lo, abs(h - pc), abs(lo - pc)))
    if not trs:
        return None
    a = sum(trs[:n]) / min(n, len(trs))
    for t in trs[n:]:
        a = (a * (n - 1) + t) / n
    return a


def _pick(sym, q, rows):
    o = q.get("ohlc") or {}
    ltp = _num(q.get("last_price"))
    if ltp <= 0 or len(rows) < 25:
        return None
    op, hi, lo = _num(o.get("open")), _num(o.get("high")), _num(o.get("low"))
    prev = _num(q.get("prev_close_price")) or (ltp - _num(q.get("net_change")))
    chg = (ltp - prev) / prev * 100 if prev else 0.0
    closes = [r["close"] for r in rows]
    e20, e50 = _ema(closes, 20), _ema(closes, 50)
    rsi = _rsi(closes)
    atr = _atr(rows) or ltp * 0.015
    avgv = sum(r["volume"] for r in rows[-21:-1]) / max(1, len(rows[-21:-1]))
    vol = _num(q.get("volume")) or _num(o.get("volume"))
    volx = vol / avgv if avgv else 0.0

    reasons, score = [], 0
    rng = hi - lo
    pos = (ltp - lo) / rng * 100 if rng > 0 else 50
    intra = 0
    if op > 0 and ltp > op and pos >= 60:
        intra = 1
        reasons.append(f"Trading above today's open, upper {100 - round(pos)}% of day range")
    elif op > 0 and ltp < op and pos <= 40:
        intra = -1
        reasons.append(f"Trading below today's open, lower {round(pos)}% of day range")
    short = long_ = 0
    if e20:
        d = (ltp - e20) / e20 * 100
        short = 1 if d >= 1 else -1 if d <= -1 else 0
        if short:
            reasons.append(f"{d:+.1f}% vs 20-day EMA")
    if e50:
        d = (ltp - e50) / e50 * 100
        long_ = 1 if d >= 1 else -1 if d <= -1 else 0
        if long_:
            reasons.append(f"{d:+.1f}% vs 50-day EMA")
    score = intra + short + long_
    if volx >= 1.5 and chg != 0:
        score += 1 if chg > 0 else -1
        reasons.append(f"Volume {volx:.1f}x the 20-day average")
    if rsi is not None:
        if rsi > 75 and score > 0:
            score -= 1
            reasons.append(f"RSI {rsi:.0f} is overbought, chasing risk")
        elif rsi < 25 and score < 0:
            score += 1
            reasons.append(f"RSI {rsi:.0f} is oversold, bounce risk")
    signal = "BUY" if score >= 2 else "SELL" if score <= -2 else "NEUTRAL"
    long_side = score >= 0
    sgn = 1 if long_side else -1
    entry = ltp
    # structure-aware stop: beyond the last 5 completed sessions' swing, but never tighter than
    # 1.5 ATR nor wider than 3 ATR; targets are R-multiples of that real risk (1.5R / 2.5R)
    prev5 = rows[-6:-1] or rows[-5:]
    if long_side:
        stop = min(ltp - 1.5 * atr, min(r["low"] for r in prev5) - 0.25 * atr)
        stop = max(stop, ltp - 3 * atr)
    else:
        stop = max(ltp + 1.5 * atr, max(r["high"] for r in prev5) + 0.25 * atr)
        stop = min(stop, ltp + 3 * atr)
    risk = abs(entry - stop)
    t1, t2 = entry + sgn * 1.5 * risk, entry + sgn * 2.5 * risk
    plans = _horizon_plans(ltp, hi, lo, atr, rows, intra, short, long_, score, e20)
    _horizon_fit(plans, ltp, prev, hi, lo, op, atr, closes, rows, volx, rsi, e20, e50, pos)
    return {
        "s": sym, "n": NAME.get(sym, sym), "sec": SECTOR.get(sym, ""),
        "ltp": round(ltp, 2), "chg": round(chg, 2), "prev": round(prev, 2),
        "signal": signal, "score": score, "strength": min(100, abs(score) * 25 + (10 if volx >= 1.5 else 0)),
        "intraday": {1: "Bullish", -1: "Bearish", 0: "Neutral"}[intra],
        "swing": {1: "Bullish", -1: "Bearish", 0: "Neutral"}[short],
        "positional": {1: "Bullish", -1: "Bearish", 0: "Neutral"}[long_],
        "entry": round(entry, 2), "stop": round(stop, 2),
        "target": round(t1, 2), "target2": round(t2, 2),
        "rr": 1.5, "risk": round(risk, 2),
        "open": round(op, 2), "high": round(hi, 2), "low": round(lo, 2),                     # today's range: the Open = Low / Open = High screens read these
        "hi20": round(max(r["high"] for r in rows[-21:-1]), 2), "lo20": round(min(r["low"] for r in rows[-21:-1]), 2),   # last 20 completed sessions: how much room is left to run
        "rsi": round(rsi, 1) if rsi is not None else None,
        "volx": round(volx, 2), "atr": round(atr, 2), "reasons": reasons,
        "spark": [round(c, 2) for c in closes[-20:]],
        "plans": plans,
    }


def _horizon_plans(ltp, hi, lo, atr, rows, intra, short, long_, score, e20):
    """One plan per holding period, each with its own direction, stop, targets and how long to hold.
      Intraday   - today's trend vs open / day range; stop just beyond today's low (high), 0.3-0.6 ATR; targets 1R / 2R;
                   square off by 15:15.
      Swing      - 20-day EMA side; stop beyond the last 5 sessions' swing, 1.5-3 ATR; targets 1.5R / 2.5R; 3-10 sessions.
      Positional - 50-day EMA side; stop beyond the last 20 sessions' swing, 2.5-5 ATR; targets 2R / 3R; 2-6 weeks,
                   trail under the 20-day EMA.
    Expected time to target uses a normal pace of ~0.5 ATR of progress a session (intraday: ~1 ATR a day)."""
    def mk(d, risk, k1, k2, hold, exit_rule, pace):
        if d == 0:
            d = 1 if score > 0 else -1 if score < 0 else 0
        if d == 0:
            return {"side": "WAIT", "hold": {"swing": "-", "positional": "-"}.get(hold, hold), "exit": "No clear direction on this time frame - wait."}
        stop = ltp - d * risk
        t1, t2 = ltp + d * k1 * risk, ltp + d * k2 * risk
        n1 = max(1, math.ceil(k1 * risk / max(pace, 1e-9)))
        n2 = max(n1, math.ceil(k2 * risk / max(pace, 1e-9)))
        if hold == "swing":
            hold = f"about {n1}-{min(n2, 15)} sessions (T1 ~{n1}, T2 ~{n2} at a normal pace); review after 15"
        elif hold == "positional":
            w1, w2 = max(1, math.ceil(n1 / 5)), max(2, math.ceil(n2 / 5))
            hold = f"about {w1}-{min(w2, 8)} weeks (T1 ~{n1} sessions, T2 ~{n2})"
        return {"side": "BUY" if d > 0 else "SELL", "entry": round(ltp, 2), "stop": round(stop, 2), "t1": round(t1, 2), "t2": round(t2, 2),
                "rr": k1, "riskPct": round(risk / ltp * 100, 2), "hold": hold, "exit": exit_rule, "eta": (n1, n2)}
    # intraday: risk to just beyond today's extreme, kept within 0.3-0.6 ATR
    di = intra if intra else 0
    ext = (ltp - lo) if di >= 0 else (hi - ltp)
    r_i = min(max(ext + 0.1 * atr, 0.3 * atr), 0.6 * atr)
    p_i = mk(di, r_i, 1.0, 2.0, "Today only", "Square off by 15:15 even if no target or stop is hit.", 1e9)
    if p_i.get("eta"):
        p_i["eta"] = None
    # swing: 5-session structure
    prev5 = rows[-6:-1] or rows[-5:]
    ds = short or (1 if score > 0 else -1 if score < 0 else 0)
    if ds >= 0:
        r_s = ltp - min(ltp - 1.5 * atr, min(r["low"] for r in prev5) - 0.25 * atr)
    else:
        r_s = max(ltp + 1.5 * atr, max(r["high"] for r in prev5) + 0.25 * atr) - ltp
    r_s = min(max(r_s, 1.5 * atr), 3 * atr, 0.07 * ltp)            # never more than 7% of the price
    p_s = mk(short, r_s, 1.5, 2.5, "swing", "Exit on a daily close beyond the stop; book half at Target 1 and move the stop to entry.", 0.5 * atr)
    # positional: 20-session structure
    prev20 = rows[-21:-1] or rows[-20:]
    dp = long_ or (1 if score > 0 else -1 if score < 0 else 0)
    if dp >= 0:
        r_p = ltp - (min(r["low"] for r in prev20) - 0.25 * atr)
    else:
        r_p = (max(r["high"] for r in prev20) + 0.25 * atr) - ltp
    r_p = min(max(r_p, 2.5 * atr), 5 * atr, 0.12 * ltp)            # never more than 12% of the price (3R target stays above 0)
    trail = f" (now {e20:,.2f})" if e20 else ""
    p_p = mk(long_, r_p, 2.0, 3.0, "positional", f"Hold while the weekly close stays on the right side of the 20-day EMA{trail}; exit on a weekly close beyond the stop.", 0.5 * atr)
    return {"intraday": p_i, "swing": p_s, "positional": p_p}


def _horizon_fit(plans, ltp, prev, hi, lo, op, atr, closes, rows, volx, rsi, e20, e50, pos):
    """Each horizon has its own entry test, so the three lists are different stocks, ranked by their own score:
      Intraday   - today's momentum: move >= 0.4x the normal daily range in the plan's direction, volume at least normal,
                   trading in the top (bottom) 35% of today's range.  Score: move in ATRs, volume, closeness to the extreme.
      Swing      - a pullback or a fresh breakout inside the 20-day trend, NOT a stock that has already run: price within
                   1 ATR of the 20-day EMA on the trend side, moved back toward it over the last 3 sessions, RSI 40-65
                   (35-60 for sells), or a close beyond the last
                   5 sessions' high (low) on 1.3x volume.  Score: room left to run + breakout bonus.
      Positional - an established trend: 50-day EMA rising (falling) > 1% over 10 sessions, 3-month return > 8% in the same
                   direction, 20-day EMA on the right side of the 50-day, and not more than 3 ATR stretched.
                   Score: 3-month return + slope of the 50-day EMA."""
    atr = atr or ltp * 0.015
    chg = (ltp - prev) / prev * 100 if prev else 0.0
    atr_pct = atr / ltp * 100 if ltp else 1.5
    # intraday
    p = plans.get("intraday") or {}
    d = 1 if p.get("side") == "BUY" else -1 if p.get("side") == "SELL" else 0
    mom = chg / atr_pct if atr_pct else 0.0
    edge = pos if d > 0 else 100 - pos
    ok = d != 0 and d * mom >= 0.4 and volx >= 1.0 and edge >= 65 and (op <= 0 or d * (ltp - op) > 0)
    p.update(ok=bool(ok), fit=round(max(0.0, d * mom) * 40 + min(volx, 3) * 15 + max(0.0, edge - 65), 1),
             why=f"Today {chg:+.2f}% = {abs(mom):.1f}x a normal day, volume {volx:.1f}x, {'top' if d >= 0 else 'bottom'} {100 - edge:.0f}% of the range")
    # swing
    p = plans.get("swing") or {}
    d = 1 if p.get("side") == "BUY" else -1 if p.get("side") == "SELL" else 0
    ext = (ltp - e20) / atr if e20 else 0.0
    prev5 = rows[-6:-1] or rows[-5:]
    brk = d > 0 and ltp > max(r["high"] for r in prev5) and volx >= 1.3 or d < 0 and ltp < min(r["low"] for r in prev5) and volx >= 1.3
    rsi_ok = rsi is not None and ((40 <= rsi <= 65) if d > 0 else (35 <= rsi <= 60))
    back = len(closes) >= 4 and d * (ltp - closes[-4]) < 0          # moved against the trend over the last 3 sessions = a real pullback
    pull = d != 0 and 0 <= d * ext <= 1.0 and rsi_ok and back
    ok = d != 0 and (pull or (brk and d * ext <= 2.5))
    p.update(ok=bool(ok), fit=round(max(0.0, 1.5 - abs(ext)) * 30 + (25 if brk else 0) + (10 if rsi_ok else 0), 1),
             why=("Fresh 5-session breakout on volume" if brk else f"Pullback: {abs(ext):.1f} ATR from the 20-day EMA, RSI {rsi:.0f}" if rsi is not None else "Pullback to the 20-day EMA")
             if ok else (f"Already {abs(ext):.1f} ATR from the 20-day EMA - extended, wait for a pullback" if abs(ext) > 1.5 else "No pullback or breakout setup"))
    # positional
    p = plans.get("positional") or {}
    d = 1 if p.get("side") == "BUY" else -1 if p.get("side") == "SELL" else 0
    e50_old = _ema(closes[:-10], 50) if len(closes) >= 60 else None
    slope = (e50 - e50_old) / e50_old * 100 if e50 and e50_old else 0.0
    base = closes[-61] if len(closes) >= 61 else closes[0]
    r60 = (ltp / base - 1) * 100 if base else 0.0
    stack = e20 and e50 and d * (e20 - e50) > 0
    ok = d != 0 and d * slope > 1.0 and d * r60 > 8 and bool(stack) and d * ext <= 3
    p.update(ok=bool(ok), fit=round(max(0.0, d * r60) + max(0.0, d * slope) * 10, 1),
             why=f"3-month {r60:+.1f}%, 50-day EMA {slope:+.1f}% in 10 sessions" + ("" if ok else (" - trend not established" if d * slope <= 1.0 or d * r60 <= 8 else " - too stretched")))
    best = max(("intraday", "swing", "positional"), key=lambda k: (plans[k].get("ok", False), plans[k].get("fit", 0)))
    for k in plans:
        plans[k]["best"] = k == best and plans[k].get("ok", False)


PICK_INDICES = ("NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX")
CALL_INDICES = ("NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX")
FLOW_MIN_PCT = 55.0          # one side must hold >= 55% of ATM-window option volume
FLOW_WINDOW = 5             # strikes either side of ATM that count towards the flow
OPT_T1, OPT_T2, OPT_SL = 1.09, 1.18, 0.95   # same +9% / +18% / -5% premium rule used across the app


_PK = {"data": None, "t": 0.0, "busy": False, "partial": [], "total": 0,
       "lock": threading.Lock(), "done": threading.Event()}


def _picks_payload(res, universe, complete):
    buys = sorted([r for r in res if r["signal"] == "BUY"], key=lambda r: (-r.get("score", 0), -r.get("volx", 0)))
    sells = sorted([r for r in res if r["signal"] == "SELL"], key=lambda r: (r.get("score", 0), -r.get("volx", 0)))
    return {
        "picks": list(res), "buy": buys, "sell": sells, "complete": complete,
        "count": len(res), "universe": universe, "marketOpen": market_open(),
        "asOf": datetime.now(IST).isoformat(),
        "note": "Rule-based screen on EMA trend, day-range position, volume and RSI. Not investment advice.",
    }


PICK_EXTRA_FLOOR_VOL = 25000      # cash-universe liquidity floor: today's traded shares (non-F&O names)
PICK_EXTRA_FLOOR_LTP = 20         # ...and a minimum price, so penny names stay out of the Stock Trader
PICK_CASH_MIN_STRENGTH = 55       # cash picks below this confluence strength are dropped (user: show 50-60+ only)


def _extra_equity_syms():
    """Every listed NSE equity NOT in the F&O universe, sorted, with names registered - the Picks
    screen scans these after the F&O set so the Stock Trader sees candidates from the whole market."""
    try:
        eq = nse_service.upstox._load_equity_keys() or {}
        names = nse_service.upstox.eq_names()
        fno = {s for s, _, _ in STOCKS} | set(PICK_INDICES)
        return sorted(((s, names.get(s) or s) for s in eq if s not in fno), key=lambda x: x[0])
    except Exception:
        return []


class _BuildBudget(RuntimeError):
    """This build's cap on fresh Upstox candle calls is used up (not a real failure: retry in the next build)."""


def _picks_compute_inner(deadline_s, progress=None):
    """Screen indices first, then the curated liquid stocks, then the rest. Rate-limited requests are
    retried and swept again in a gentle second pass, so a symbol is never silently dropped.
    After the F&O set, the scan continues into the WHOLE listed NSE market (cash universe) with a
    per-day cursor in shared cache: every build advances the frontier, the daily candle cache makes
    already-scanned symbols free, and rows are tagged universe=fno/cash so the Stock Trader can
    act on strong non-F&O stocks."""
    t_start = time.time()                            # deadline_s counts from here, NOT after the slow setup below
    up = nse_service.upstox
    import equity_bhav
    keymap = {}
    for s in list(PICK_INDICES) + [s for s, _, _ in STOCKS]:
        try:
            keymap[_key(s)] = s
        except Exception:
            pass
    fno_n = len(keymap)
    extra = _extra_equity_syms()
    cursor = int(shared_cache.get(f"picks:extra-cursor|{date.today().isoformat()}") or 0)
    if cursor >= len(extra):
        cursor = 0                                   # a fresh day re-walks the market (daily cache makes it cheap)
    # pace the walk: each NEW symbol needs its own daily-candle call from Upstox, and the shared
    # rate budget is finite - a small batch per build (the daily candle cache makes repeats free,
    # so the frontier advances build over build until the whole market is covered for the day)
    bhav = bhav_diag = None
    if extra:
        import equity_bhav
        try:
            on_vercel = bool(os.environ.get("VERCEL"))
            if on_vercel and shared_cache.get("bhav:cooldown"):
                bhav_diag = {"have": len(shared_cache.get("bhav:sessions") or []), "skipped": "cooldown"}
            else:
                # on serverless the whole build must fit the 30 s cap: give the downloads at most ~1/3 of the budget
                bhav_diag = equity_bhav.warm(max_downloads=14 if on_vercel else 10, target_sessions=60,       # 29 Oct: 5 sessions per build was too slow (25 needed): more per build, a build takes ~7 s of its 30
                                             budget_s=max(4, deadline_s * 0.55) if on_vercel else None)
                if on_vercel and not bhav_diag.get("downloaded") and bhav_diag.get("have", 0) < 25:
                    shared_cache.set("bhav:cooldown", 1, 300)      # archive blocked/slow: do not burn every request on it
        except Exception as e:
            bhav_diag = {"error": str(e)[:140]}
        bhav = bhav_diag if (isinstance(bhav_diag, dict) and bhav_diag.get("have", 0) >= 25) else None
    take = 0 if not (extra and bhav) else min(len(extra) - cursor, 120 if os.environ.get("VERCEL") else 300)
    slice_syms = [s for s, _nm in extra[cursor:cursor + take]]
    for s in slice_syms:                             # one batched quotes call covers all of them (500/batch)
        try:
            keymap.setdefault(_key(s), s)
        except Exception:
            pass
    qs = up._full_quotes(list(keymap.keys()))
    qs_vol = {}                                          # today's traded shares, keyed by SYMBOL (the floors look up by symbol)
    for k, q in qs.items():
        o = q.get("ohlc") or {}
        v = _num(q.get("volume")) or _num(o.get("volume"))
        qs_vol[k] = v
        if k in keymap:
            qs_vol[keymap[k]] = v
    deadline = t_start + deadline_s
    _PK["total"] = len(keymap)
    _PK["coverage"] = {"fno": fno_n, "extra_total": len(extra), "extra_from": cursor, "extra_to": cursor + take}

    today_s = date.today().isoformat()
    today_iso = today_s
    pre = shared_cache.get_many([f"dc|{k}|{today_s}" for k in keymap])       # ONE Redis command for every symbol

    _fresh_calls = [0]
    FRESH_CAP = 40 if os.environ.get("VERCEL") else 400

    def daily(k):
        key = f"dc|{k}|{today_s}"
        if key in pre:
            return pre[key]
        if _fresh_calls[0] >= FRESH_CAP:
            # the Upstox budget (~66 calls/min) is shared with every user-facing candle/strategy call: a cold
            # build must not burn it all (that made RELIANCE & co. fail with "no candles"). The rest is
            # fetched by the next builds; the daily cache (dc|...) makes already-fetched symbols free.
            raise _BuildBudget("fresh-candle budget for this build used")
        _fresh_calls[0] += 1
        rows = _cached(key, 6 * 3600, lambda: up.get_candles(k, "day"))
        if rows:
            shared_cache.set(key, rows, 20 * 3600)
        return rows

    failed = {}
    fno_syms = set(PICK_INDICES) | {s for s, _, _ in STOCKS}
    extra_done = set()                               # extras that got data this build (cursor advances past them)
    fallback_used = set()                            # extras that fell back to the Upstox candle path this build
    bhav_days = None                                 # loaded once per build: 1 GET per session, not per symbol

    @bg
    def one(item):
        nonlocal bhav_days
        k, sym = item
        q = qs.get(k)
        if not q:
            return None
        if time.time() > deadline:
            failed[k] = sym
            return None
        if sym not in fno_syms and bhav:
            if bhav_days is None:
                bhav_days = equity_bhav.load_days()  # one shared-store read per session for the WHOLE build
            rows = equity_bhav.history(sym, days=bhav_days)
            if rows is not None and market_open():   # LIVE data guarantee: during the session the bhavcopy
                o = q.get("ohlc") or {}              # history ends at yesterday - append TODAY's live bar so
                ltp_now = _num(q.get("last_price"))  # the cash indicators are as fresh as the F&O ones
                if ltp_now > 0:
                    vol_now = _num(q.get("volume")) or _num(o.get("volume"))
                    hi_q = _num(o.get("high")) or ltp_now
                    lo_q = _num(o.get("low")) or ltp_now
                    op_q = _num(o.get("open")) or ltp_now
                    rows = rows + [{"date": today_iso, "open": op_q, "high": max(hi_q, ltp_now),
                                    "low": min(lo_q, ltp_now), "close": ltp_now, "volume": vol_now}]
            if rows is None and len(fallback_used) < 25:
                # the bhav read failed for this symbol (store hiccup): fall back to the Upstox
                # candle path, capped per build so a store outage cannot blow the rate budget
                fallback_used.add(sym)
                try:
                    rows = daily(k)
                except Exception:
                    rows = None
            if rows is None:
                failed[k] = sym                      # bhav not warmed for this session count yet: retry next build
                return None
        else:
            rows = None
            for attempt in range(3):
                try:
                    rows = daily(k)
                    break
                except _BuildBudget:
                    break                            # no point retrying (or sleeping): the next build continues
                except Exception:
                    time.sleep(0.4 * (attempt + 1))
            if rows is None:
                failed[k] = sym
                return None
        r = _pick(sym, q, rows)
        if r:
            r["kind"] = "index" if sym in PICK_INDICES else "stock"
            r["universe"] = "fno" if sym in fno_syms else "cash"
            if sym not in fno_syms:                  # cash universe: liquidity + strength floors keep junk out
                extra_done.add(sym)
                if (qs_vol.get(sym) or 0) < PICK_EXTRA_FLOOR_VOL or r["ltp"] < PICK_EXTRA_FLOOR_LTP:
                    return None
                if (r.get("strength") or 0) < PICK_CASH_MIN_STRENGTH:
                    return None
        return r

    res = []

    def run(items, workers):
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            for fut in concurrent.futures.as_completed([pool.submit(one, it) for it in items]):
                r = fut.result()
                if r:
                    res.append(r)
                    if progress and len(res) % 8 == 0:
                        progress(res)

    run(list(keymap.items()), 6)
    for _ in range(2):
        if not failed or time.time() > deadline:
            break
        retry = list(failed.items())
        failed.clear()
        time.sleep(1.0)
        run(retry, 3)
    if progress:
        progress(res)
    # "complete" means the F&O core was fully screened - the cash-universe walk is progressive
    # by design (a rate-limited extra must never stop the day's payload from being stored)
    core_got = sum(1 for r in res if r.get("universe") != "cash")
    out = _picks_payload(res, len(keymap), core_got >= 0.95 * fno_n)
    if not extra:
        try:
            shared_cache.set(f"picks:walk|{date.today().isoformat()}", {"at": datetime.now(IST).isoformat(), "extraTotal": 0,
                                                                         "bhavNote": "the list of cash symbols is empty (instrument master not loaded)"}, 6 * 3600)
        except Exception:
            pass
    if extra:
        done = sum(1 for s in slice_syms if s in extra_done)        # only symbols that actually got data
        nxt = (cursor + done) if done else cursor                   # rate-limited ones retry in the next build
        shared_cache.set(f"picks:extra-cursor|{date.today().isoformat()}", nxt, 20 * 3600)
        coverage = {"fno": fno_n, "extra_total": len(extra), "extra_done": nxt,
                    "bhav": bhav, "bhav_diag": bhav_diag, "failed": len(failed),
                    "days": len(bhav_days) if isinstance(bhav_days, dict) else 0,
                    "fallback": len(fallback_used)}
        try:
            shared_cache.set(f"picks:walk|{date.today().isoformat()}",              # last build's walk numbers, read by /api/m/cash-seed (why is no cash data coming?)
                             {"at": datetime.now(IST).isoformat(), "extraTotal": len(extra), "from": cursor, "took": take, "advancedTo": nxt, "failed": len(failed),
                              "bhavSessions": (bhav_diag or {}).get("have") if isinstance(bhav_diag, dict) else None,
                              "bhavDownloaded": (bhav_diag or {}).get("downloaded") if isinstance(bhav_diag, dict) else None,
                              "bhavNote": ((bhav_diag or {}).get("skipped") or (bhav_diag or {}).get("error")) if isinstance(bhav_diag, dict) else None,
                              "bhavReady": bool(bhav), "newRows": sum(1 for r in res if r.get("universe") == "cash")}, 6 * 3600)
            print("picks walk:", {k: (v if not isinstance(v, dict) else "dict") for k, v in coverage.items()}, flush=True)
        except Exception:
            pass        # diagnostics go to the logs only - the public payload must not reveal the scan mechanics
        # the day's cash picks ACCUMULATE: each build's slice would otherwise replace the previous
        # one, and strong names found earlier today would vanish from the screen on the next build
        cash_day_key = f"picks:cash|{date.today().isoformat()}"
        cash_day = shared_cache.get(cash_day_key) or {}
        if not cash_day:
            seed_file = _static_path("picks_cash_seed.json")
            if os.path.exists(seed_file):
                try:
                    with open(seed_file, "r", encoding="utf-8") as f:
                        cash_day = json.load(f)
                    shared_cache.set(cash_day_key, cash_day, 20 * 3600)
                except Exception:
                    pass
        for r in res:
            if r.get("universe") == "cash" and r.get("score") is not None:
                cash_day[r["s"]] = r
        if cash_day:
            shared_cache.set(cash_day_key, cash_day, 20 * 3600)
        res = [r for r in res if r.get("universe") != "cash"] +               [r for r in cash_day.values() if (r.get("strength") or 0) >= PICK_CASH_MIN_STRENGTH]
        out = _picks_payload(res, len(keymap), core_got >= 0.95 * fno_n)
    if not any(r.get("universe") == "cash" for r in res):
        cash_day_key = f"picks:cash|{date.today().isoformat()}"
        cash_day = shared_cache.get(cash_day_key) or {}
        if not cash_day:
            seed_file = _static_path("picks_cash_seed.json")
            if not os.path.exists(seed_file):
                seed_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "picks_cash_seed.json")
            if os.path.exists(seed_file):
                try:
                    with open(seed_file, "r", encoding="utf-8") as f:
                        cash_day = json.load(f)
                    shared_cache.set(cash_day_key, cash_day, 20 * 3600)
                except Exception:
                    pass
        if cash_day:
            res = [r for r in res if r.get("universe") != "cash"] +                   [r for r in cash_day.values() if (r.get("strength") or 0) >= PICK_CASH_MIN_STRENGTH]
            out = _picks_payload(res, len(keymap), core_got >= 0.95 * fno_n)
    return out


def _picks_compute(deadline_s, progress=None):
    """Runs one picks build and ALWAYS leaves a note of how it ended (/api/m/cash-seed -> lastBuild): 'walk: null' used to be all anyone could see
    when a build ran out of time or failed before it reached the point where the walk numbers are written."""
    t0 = time.time()
    note = {"at": datetime.now(IST).isoformat(), "budgetS": deadline_s}
    try:
        v = _picks_compute_inner(deadline_s, progress)
        note.update(ok=True, tookS=round(time.time() - t0, 1), count=v.get("count"), complete=v.get("complete"))
        return v
    except Exception as e:
        note.update(ok=False, tookS=round(time.time() - t0, 1), error=f"{type(e).__name__}: {str(e)[:160]}")
        raise
    finally:
        try:
            shared_cache.set(f"picks:build|{date.today().isoformat()}", note, 6 * 3600)
        except Exception:
            pass


def _picks_run():
    try:
        data = _picks_compute(120, progress=lambda r: _PK.__setitem__("partial", list(r)))
        if data["count"]:
            _PK["data"], _PK["t"] = data, time.time()
    except Exception as e:
        print(f"[picks] background build failed: {e}")
    finally:
        _PK["busy"] = False
        _PK["done"].set()


def _picks_kick():
    with _PK["lock"]:
        if _PK["busy"]:
            return
        _PK["busy"] = True
        _PK["done"].clear()
        _PK["partial"] = []
    threading.Thread(target=_picks_run, daemon=True, name="picks-build").start()


def warm_picks():
    """Called at server start so the first user request finds the screen ready. On Vercel every cold start would otherwise launch a ~200-quote
    build (even at night, even on a holiday); the request path builds inline and caches for an hour when the market is shut, so nothing is warmed there."""
    if os.environ.get("VERCEL"):
        return
    try:
        ensure_universe()
    except Exception:
        pass
    _picks_kick()


def _add_industry(data):
    """Every pick row gets an industry: the F&O core keeps its hand-made sector, all other names get one from industry.py (explicit table, then company-name keywords)."""
    try:
        import industry
        for r in (data.get("picks") or []) if isinstance(data, dict) else []:
            if r.get("kind") == "index":
                continue
            if r.get("sec") in (None, "", "F&O") or r.get("s") in industry.EXPLICIT:
                ind = industry.of(r.get("s"), r.get("n") or NAME.get(r.get("s"), ""))
                if ind:
                    r["sec"] = ind
                    r["ind"] = ind
            else:
                r["ind"] = r["sec"]
    except Exception:
        pass
    return data


@router.get("/stock-lookup")
def stock_lookup(q: str = ""):
    """Find ANY listed NSE equity by symbol or company name (also names with no setup today, which the Picks list hides): symbol, name, industry, and
    whether it is in today's picks. The screen then asks /quotes for the live price."""
    import industry
    ensure_universe()
    q = (q or "").strip().lower()
    if len(q) < 2:
        return {"q": q, "items": []}
    names = dict(NAME)
    src = "master"
    try:
        eq = nse_service.upstox.eq_names() or {}
    except Exception:
        eq = {}
    if eq:
        for s, n in eq.items():
            names.setdefault(s, n)
        try:
            if not shared_cache.get("eq-names"):
                shared_cache.set("eq-names", eq, 12 * 3600)          # a copy for instances whose own instrument-master download fails
        except Exception:
            pass
    else:
        try:
            eq = shared_cache.get("eq-names") or {}
        except Exception:
            eq = {}
        for s, n in eq.items():
            names.setdefault(s, n)
        if not eq:                                                   # last resort: symbols from the newest stored bhavcopy (symbol search only)
            src = "symbols"
            try:
                for d in sorted(shared_cache.get("bhav:sessions") or [])[-1:]:
                    for s in (shared_cache.get(f"bhav:day2|{d}") or {}):
                        names.setdefault(s, "")
            except Exception:
                pass
    hits = [(s, n) for s, n in names.items() if q in s.lower() or q in (n or "").lower()]
    hits.sort(key=lambda x: (not x[0].lower().startswith(q), not (x[1] or "").lower().startswith(q), len(x[0]), x[0]))
    return {"q": q, "src": src, "items": [{"s": s, "n": n, "ind": industry.of(s, n) or SECTOR.get(s, "")} for s, n in hits[:8]]}


def _inject_cash_seed_if_needed(data):
    if not isinstance(data, dict):
        return data
    picks = data.get("picks")
    if not isinstance(picks, list):
        return data
    if any(r.get("universe") == "cash" for r in picks):
        return data
    seed_file = _static_path("picks_cash_seed.json")
    if not os.path.exists(seed_file):
        alt = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "picks_cash_seed.json")
        if os.path.exists(alt):
            seed_file = alt
    if os.path.exists(seed_file):
        try:
            with open(seed_file, "r", encoding="utf-8") as f:
                c_seed = json.load(f)
            cash_items = [r for r in c_seed.values() if (r.get("strength") or 0) >= PICK_CASH_MIN_STRENGTH]
            all_picks = list(picks) + cash_items
            data["picks"] = all_picks
            data["buy"] = sorted([r for r in all_picks if r.get("signal") == "BUY"], key=lambda r: (-r.get("score", 0), -r.get("volx", 0)))
            data["sell"] = sorted([r for r in all_picks if r.get("signal") == "SELL"], key=lambda r: (r.get("score", 0), -r.get("volx", 0)))
            data["count"] = len(all_picks)
        except Exception:
            pass
    return data


TOP_LOCK_LATE = 9 * 60 + 45
TOP_LOCK_FROM = 9 * 60 + 20            # IST minutes: from 09:20 the opening range (Open = Low / High) is known, so the day's shortlist is fixed
_TOPF = {"day": None, "rows": None, "checked": 0.0}
_TOP_LIVE = ("ltp", "chg")             # a locked row keeps its levels / reason / rank; only the price and % change keep moving


def _locked_top(v, top):
    """The day's 10-15 shortlist must not reshuffle as strengths and prices tick: the first COMPLETE scan taken once the session is open
    (>= 09:20) is stored for the day and served unchanged - same stocks, same order, same entry/stop/target - with only the live price
    and % change refreshed. Before that (pre-market, holiday, half-built scan) the list is the plain live selection and nothing is stored."""
    import morning_picks
    today = date.today().isoformat()
    if _TOPF["day"] != today:
        _TOPF.update(day=today, rows=None, checked=0.0)
    key = f"picks:top|{today}"
    if _TOPF["rows"] is None and time.time() - _TOPF["checked"] > 60:       # not locked yet: look in the shared store at most once a minute
        _TOPF["checked"] = time.time()
        try:
            got = shared_cache.get(key)
            if isinstance(got, dict) and got.get("rows"):
                _TOPF["rows"] = got["rows"]
        except Exception:
            pass
    if _TOPF["rows"] is None:
        now = datetime.now(IST)
        built = v.get("_t")                                                  # when the scan was built (serverless path); a 09:16 scan must not be locked at 09:21
        lock_ts = now.replace(hour=TOP_LOCK_FROM // 60, minute=TOP_LOCK_FROM % 60, second=0, microsecond=0).timestamp()
        mins = now.hour * 60 + now.minute
        # a complete scan locks from 09:20; the 18 s serverless build is often NOT flagged complete (rate limits), so from 09:45 a full
        # enough list (>= MIN_PICKS) locks anyway - otherwise the day's list could stay live (and keep reshuffling) all session
        fresh = (market_open() and mins >= TOP_LOCK_FROM and not v.get("stale") and (v.get("complete") or mins >= TOP_LOCK_LATE)
                 and (not built or built >= lock_ts))
        if fresh and len(top) >= morning_picks.MIN_PICKS:
            _TOPF["rows"] = [dict(r) for r in top]
            try:
                shared_cache.set(key, {"rows": _TOPF["rows"], "at": now.isoformat()}, 20 * 3600)
            except Exception:
                pass
        else:
            return top, False
    live = {r.get("s"): r for r in v.get("picks") or []}
    out = []
    for r in _TOPF["rows"]:
        r = dict(r)
        lv = live.get(r.get("s")) or {}
        for k in _TOP_LIVE:
            if lv.get(k) is not None:
                r[k] = lv[k]
        out.append(r)
    return out, True


def _add_shortlist(v):
    """`top`: the 10-15 stock trades to act on first (morning_picks.py), locked for the day once the session is open (_locked_top).
    Added on read, so cached payloads from before this existed get it too."""
    try:
        import morning_picks
        top = morning_picks.select([r for r in v.get("picks") or [] if r.get("universe") != "cash"])
        top, v["topLocked"] = _locked_top(v, top)
        v["top"] = [{k: r.get(k) for k in ("s", "n", "sec", "ltp", "chg", "signal", "strength", "tier", "side", "why", "room", "rank", "entry", "stop", "target", "target2",
                                           "risk", "rr", "volx", "rsi", "open", "high", "low")} for r in top]
        v["topSummary"] = morning_picks.summary(top)
    except Exception as e:
        print(f"[picks] shortlist failed: {e}")
        v.setdefault("top", [])
    return v


@router.get("/cash-seed")
def cash_seed_status():
    """Is the cash-picks seed file there? (the file the picks screen falls back on until today's whole-market walk is done)"""
    fp = _static_path("picks_cash_seed.json")
    n = 0
    d = {}
    try:
        with open(fp, "r", encoding="utf-8") as f:
            d = json.load(f)
        n = len(d) if isinstance(d, (dict, list)) else 0
    except Exception:
        pass
    live = {"rows": 0, "changed": 0}                   # today's accumulating list on the server vs the committed file: "changed" > 0 = the whole-market walk is bringing fresh prices
    try:
        day = shared_cache.get(f"picks:cash|{date.today().isoformat()}") or {}
        seed = d if isinstance(d, dict) else {}
        live = {"rows": len(day), "changed": sum(1 for k, v in day.items() if isinstance(v, dict) and (seed.get(k) or {}).get("ltp") != v.get("ltp"))}
    except Exception:
        pass
    walk = None
    try:
        walk = shared_cache.get(f"picks:walk|{date.today().isoformat()}")
    except Exception:
        pass
    lastb = None
    try:
        lastb = shared_cache.get(f"picks:build|{date.today().isoformat()}")
    except Exception:
        pass
    return {"file": bool(fp), "symbols": n, "modified": datetime.fromtimestamp(os.path.getmtime(fp), IST).isoformat() if fp else None, "today": live, "walk": walk,
            "lastBuild": lastb, "why": None if walk else ("no build has finished its walk today - see lastBuild (error / time taken); open Picks and refresh once" if lastb else "no picks build has run since this server started - open God's Eye > Today's Picks and tap refresh")}


@router.get("/cash-seed/export")
def cash_seed_export():
    """Today's whole-market cash rows (the day's accumulating list the picks walk keeps in the shared cache) in the exact format of
    static/picks_cash_seed.json - open it while the market is live, save the file and it can be committed as the next seed. Read only."""
    d = shared_cache.get(f"picks:cash|{date.today().isoformat()}") or {}
    d = d if isinstance(d, dict) else {}
    return Response(content=json.dumps(d, separators=(",", ":")), media_type="application/json",
                    headers={"Content-Disposition": "attachment; filename=picks_cash_seed.json", "Cache-Control": "no-store", "X-Rows": str(len(d))})


@router.get("/picks")
def picks(refresh: bool = False, response: Response = None):
    if response and not refresh:
        response.headers["Cache-Control"] = "public, s-maxage=30, stale-while-revalidate=60"
    ensure_universe()
    def _public(v):
        # never publish scan diagnostics (also cleans copies built before this was private)
        if isinstance(v, dict):
            v.pop("coverage", None)
            v.pop("bhav_diag", None)
            _inject_cash_seed_if_needed(v)
            _add_shortlist(v)
            _add_industry(v)
        return v
    if os.environ.get("VERCEL"):
        # serverless freezes background threads after the response: build inline within the 30s cap
        if refresh and _allow_refresh("picks", 20, 120):
            _cache.pop("picks", None)

        ttl_s = 600 if market_open() else 3600
        sk = "picks|" + date.today().isoformat()
        # a list built before today's 09:15 (app opened pre-market) holds yesterday's prices / open-high-low: once the session is open
        # it is stale at once, so the 09:15 auto-trade cycle and the screen rebuild from live prices instead of serving it for 10 minutes
        opened_at = datetime.now(IST).replace(hour=9, minute=15, second=0, microsecond=0).timestamp() if market_open() else 0
        mem = _cache.get("picks")
        if mem and mem[0] < opened_at:
            _cache.pop("picks", None)

        def build_ok():
            got = shared_cache.get(sk)                                  # another instance already built it
            if got:
                _inject_cash_seed_if_needed(got)
            if got and not refresh and time.time() - got.get("_t", 0) < ttl_s and got.get("_t", 0) >= opened_at:
                return _public(got), True
            have_lock = shared_cache.lock("picks-build", 40)
            if not have_lock:                                           # someone else is building: serve what exists
                if got:
                    return _public(got), True
                time.sleep(4)
                got = shared_cache.get(sk)
                if got:
                    _inject_cash_seed_if_needed(got)
                    return _public(got), True
            try:
                v = _picks_compute(18)                                  # + response/serialisation must stay well under the 30 s cap
            except Exception as e:
                # the rebuild failed (rate limit / upstream timeout): show the last good list rather than a 502
                stale = got or (mem[1] if mem else None)
                if isinstance(stale, dict) and stale.get("picks"):
                    print(f"[picks] rebuild failed, serving the last good list: {e}")
                    return _public({**stale, "stale": True}), False     # not complete -> only cached for a few seconds, retried soon
                raise
            finally:
                if have_lock:                                           # only release a lock this request took (and always, even on failure)
                    shared_cache.unlock("picks-build")
            _inject_cash_seed_if_needed(v)
            if v.get("count", 0) >= 20:
                v["_t"] = time.time()
                shared_cache.set(sk, v, 20 * 3600 if v.get("complete") else 300)
            return _public(v), v.get("complete", False)
        try:
            # memory TTL is short on purpose: build_ok re-reads the shared store first (cheap),
            # so every instance catches up with the advancing cash walk within a few minutes
            # instead of serving its own hour-old copy on a closed day
            return _cached_ok("picks", 120 if market_open() else 240, build_ok, short=20)
        except Exception as e:
            raise HTTPException(502, f"Picks failed: {e}")

    ttl = 900 if market_open() else 3600
    d = _PK["data"]
    if d is None or (refresh and _allow_refresh("picks", 20, 120)) or time.time() - _PK["t"] > ttl:
        _picks_kick()                              # stale-while-revalidate: a refresh never blocks the user
    if d is not None:
        return _public({**d, "refreshing": _PK["busy"]})
    _PK["done"].wait(timeout=20)                   # very first load: wait for the full screen, else show what is ready
    if _PK["data"] is not None:
        return _public({**_PK["data"], "refreshing": False})
    partial_res = list(_PK["partial"])
    if not any(r.get("universe") == "cash" for r in partial_res):
        seed_file = _static_path("picks_cash_seed.json")
        if os.path.exists(seed_file):
            try:
                with open(seed_file, "r", encoding="utf-8") as f:
                    c_seed = json.load(f)
                partial_res.extend(c_seed.values())
            except Exception:
                pass
    return _public({**_picks_payload(partial_res, _PK["total"], False), "refreshing": True})


# ----------------------------- Index F&O calls (Recommendation for the Day) -----------------------------
def _index_call(sym, tech):
    """One index -> one decision. A BUY CALL / BUY PUT is only issued when the daily-chart signal
    (EMA trend, range position, volume, RSI) AND the live option-chain flow point the same way;
    a single-sided read is shown as WATCH and anything else as NO SIGNAL."""
    ch = chain(sym, "")
    rows = ch.get("rows") or []
    atm = ch.get("atm")
    if not rows or atm is None:
        return {"instrument": sym, "signal": "NO SIGNAL", "reason": "Option chain not available right now"}
    ai = min(range(len(rows)), key=lambda i: abs(rows[i]["strike"] - atm))
    win = rows[max(0, ai - FLOW_WINDOW): ai + FLOW_WINDOW + 1]
    cv = sum((r.get("ce") or {}).get("vol") or 0 for r in win)
    pv = sum((r.get("pe") or {}).get("vol") or 0 for r in win)
    tot = cv + pv
    call_pct = cv / tot * 100 if tot else None
    put_pct = 100 - call_pct if call_pct is not None else None
    flow = "NEUTRAL"
    if call_pct is not None:
        if call_pct >= FLOW_MIN_PCT:
            flow = "BULLISH"
        elif put_pct >= FLOW_MIN_PCT:
            flow = "BEARISH"
    tsig = (tech or {}).get("signal", "NEUTRAL")
    want = "BUY CALL" if (tsig == "BUY" and flow == "BULLISH") else "BUY PUT" if (tsig == "SELL" and flow == "BEARISH") else None
    basis, confidence = "daily chart and option flow agree", "high"
    pct = max(call_pct or 0, put_pct or 0)
    if not want and tsig == "NEUTRAL" and flow in ("BULLISH", "BEARISH") and pct >= 60:
        # flow-led: the chart has no view, the option market is clearly one-sided (never taken against the chart)
        want = "BUY CALL" if flow == "BULLISH" else "BUY PUT"
        basis, confidence = f"option flow {pct:.0f}% one-sided, chart neutral", "medium"
    out = {
        "instrument": sym, "kind": "index", "tech": tsig, "flow": flow,
        "callPct": round(call_pct, 1) if call_pct is not None else None,
        "putPct": round(put_pct, 1) if put_pct is not None else None,
        "spot": ch.get("spot"), "expiry": ch.get("expiry"), "lot": ch.get("lot"),
        "marketOpen": market_open(),
    }
    if not want:
        if tsig in ("BUY", "SELL") and flow != "NEUTRAL":
            out.update(signal="WATCH", reason=f"Chart says {tsig} but option flow is {flow.lower()} -- no agreement, stay out")
        elif tsig in ("BUY", "SELL"):
            out.update(signal="WATCH", reason=f"Chart says {tsig}; option volume is balanced so there is no flow confirmation yet")
        elif flow != "NEUTRAL":
            out.update(signal="WATCH", reason=f"Option flow is {flow.lower()} but the chart trend is neutral")
        else:
            out.update(signal="NO SIGNAL", reason="Chart trend and option flow are both neutral -- rangebound")
        return out
    side = "ce" if want == "BUY CALL" else "pe"
    leg = (rows[ai].get(side) or {})
    if not (leg.get("ltp") or 0) > 0:
        out.update(signal="NO SIGNAL", reason="ATM contract has no traded price yet")
        return out
    entry = float(leg["ltp"])
    out.update(
        signal=want, contract=f"{sym} {int(rows[ai]['strike'])} {'CE' if side == 'ce' else 'PE'}",
        strike=rows[ai]["strike"], key=leg.get("key"), entry=round(entry, 2),
        target1=round(entry * OPT_T1, 2), target2=round(entry * OPT_T2, 2), stopLoss=round(entry * OPT_SL, 2),
        underlying={"entry": tech.get("entry"), "stop": tech.get("stop"), "target": tech.get("target"), "target2": tech.get("target2")},
        strength=tech.get("strength") if confidence == "high" else round(pct / 2), basis=basis, confidence=confidence, opening915=_opening_levels(leg.get("key")) if leg.get("key") else None,
        reasons=(tech.get("reasons") or [])[:3] + [f"Option volume near ATM: {call_pct:.0f}% calls / {put_pct:.0f}% puts"],
    )
    return out


@router.get("/day-calls")
def day_calls(refresh: bool = False):
    ensure_universe()
    try:
        tech = {p["s"]: p for p in quick_screen(list(CALL_INDICES), 8)}     # 5 symbols, candles come from the shared cache
    except Exception:
        tech = {}

    def build():
        res = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            futs = {sym: pool.submit(_index_call, sym, tech.get(sym) or {}) for sym in CALL_INDICES}
            for sym, f in futs.items():
                try:
                    res.append(f.result())
                except Exception as e:
                    res.append({"instrument": sym, "signal": "NO SIGNAL", "reason": f"Data unavailable: {str(e)[:120]}"})
        order = {"BUY CALL": 0, "BUY PUT": 0, "WATCH": 1, "NO SIGNAL": 2}
        res.sort(key=lambda r: (order.get(r["signal"], 3), -(r.get("strength") or 0)))
        return {"calls": res, "marketOpen": market_open(), "asOf": datetime.now(IST).isoformat(),
                "rule": f"Call/Put only when the daily chart signal and ATM±{FLOW_WINDOW} option-volume flow (>= {FLOW_MIN_PCT:.0f}%) agree. "
                        "Premium levels: T1 +9%, T2 +18%, SL -5%. Paper-trading aid, not advice."}

    if refresh and _allow_refresh("daycalls", 15, 120):
        _cache.pop("daycalls", None)

    def build_ok():
        v = build()
        return v, all(sym in tech for sym in CALL_INDICES)   # not cached for long if the index charts were not ready
    return _cached_ok("daycalls", 20 if market_open() else 300, build_ok, short=5)


# ----------------------------- Option Scanner: low range + Open=Low / Open=High -----------------------------
@router.get("/option-low-range")
def option_low_range(symbol: str = "NIFTY", expiry: str = "", lowFrom: float = 5.80, lowTo: float = 8.45,
                     usePrev: bool = True, prevFrom: float = 38.0, prevTo: float = 48.0, tol: float = 0.0,
                     each: int = 8, show: str = "all"):
    """Port of the 'Option Scanner - Low Range + Open=Low / Open=High' Pine script on live Upstox chain data.
    A contract MATCHES when its day low is inside [lowFrom, lowTo] and (if usePrev) the previous close is
    inside [prevFrom, prevTo]. O=L / O=H flag contracts whose open equals the day low / high (within tol)."""
    each = max(1, min(int(each), 12))
    ch = chain(symbol, expiry)
    rows = ch.get("rows") or []
    atm = ch.get("atm")
    if not rows or atm is None:
        raise HTTPException(502, "Option chain not available right now")
    ai = min(range(len(rows)), key=lambda i: abs(rows[i]["strike"] - atm))
    win = rows[max(0, ai - each): ai + each + 1]

    def side(leg):
        if not leg:
            return None
        o, h, l, pc = leg.get("open"), leg.get("high"), leg.get("low"), leg.get("prev")
        has = l is not None and l > 0
        match = has and lowFrom <= l <= lowTo and (not usePrev or (pc is not None and prevFrom <= pc <= prevTo))
        ol = bool(o) and has and abs(o - l) <= tol
        oh = bool(o) and bool(h) and abs(o - h) <= tol
        return {"ltp": leg.get("ltp"), "open": o, "high": h, "low": l, "prev": pc, "vol": leg.get("vol"),
                "match": bool(match), "ol": ol, "oh": oh, "key": leg.get("key"),
                "signal": "O=L=H" if ol and oh else "O=L" if ol else "O=H" if oh else ""}

    out, lists = [], {"match": [], "ol": [], "oh": []}
    for r in win:
        ce, pe = side(r.get("ce")), side(r.get("pe"))
        for tag, d in (("CE", ce), ("PE", pe)):
            if not d:
                continue
            name = f"{int(r['strike'])}{tag}"
            for k in ("match", "ol", "oh"):
                if d[k]:
                    lists[k].append(name)
        keep = {"all": True, "matches": bool((ce and ce["match"]) or (pe and pe["match"])),
                "ol": bool((ce and ce["ol"]) or (pe and pe["ol"])), "oh": bool((ce and ce["oh"]) or (pe and pe["oh"])),
                "any": any(d and (d["match"] or d["ol"] or d["oh"]) for d in (ce, pe))}.get(show, True)
        if keep:
            out.append({"strike": r["strike"], "atm": r["strike"] == atm, "ce": ce, "pe": pe})
    return {"symbol": ch["symbol"], "spot": ch.get("spot"), "expiry": ch.get("expiry"), "expiries": ch.get("expiries"),
            "atm": atm, "lot": ch.get("lot"), "rows": out, "match": lists["match"], "openLow": lists["ol"],
            "openHigh": lists["oh"], "marketOpen": market_open(), "asOf": datetime.now(IST).isoformat(),
            "params": {"lowFrom": lowFrom, "lowTo": lowTo, "usePrev": usePrev, "prevFrom": prevFrom, "prevTo": prevTo, "tol": tol}}


def _opening_levels(key):
    """High/Low of the 09:15-09:30 candle of an option contract (today) divided by 2 / 3 / 4 -
    the HL/2/3/4 levels of the RJ Best script, which are meant for option premiums."""
    try:
        mins = nse_service.upstox.fetch_intraday_candles(key, "minutes", "1")
    except Exception:
        return None
    first = []
    for c in mins:
        try:
            dt = datetime.fromisoformat(c["time"]).astimezone(IST)
        except Exception:
            continue
        if dt.date() == datetime.now(IST).date() and 9 * 60 + 15 <= dt.hour * 60 + dt.minute < 9 * 60 + 30:
            first.append(c)
    if not first:
        return None
    h, l = max(c["high"] for c in first), min(c["low"] for c in first)
    return {"high": round(h, 2), "low": round(l, 2),
            "h2": round(h / 2, 2), "h3": round(h / 3, 2), "h4": round(h / 4, 2),
            "l2": round(l / 2, 2), "l3": round(l / 3, 2), "l4": round(l / 4, 2)}


# ----------------------------- fast screens for the auto trader -----------------------------
def quick_screen(symbols, deadline_s=12):
    """Same scoring as /picks but only for the given symbols, so it finishes in a few seconds."""
    ensure_universe()
    up = nse_service.upstox
    keymap = {}
    for s in symbols:
        try:
            keymap[_key(s)] = s
        except Exception:
            pass
    if not keymap:
        return []
    qs = up._full_quotes(list(keymap))
    end = time.time() + deadline_s
    fno_syms = set(PICK_INDICES) | {s for s, _, _ in STOCKS}     # these three used to be undefined here: every symbol that produced a pick
    extra_done = set()                                          # raised NameError, so the index call/put screen for the auto trader never returned
    qs_vol = {keymap[k]: (_num(q.get("volume")) or _num((q.get("ohlc") or {}).get("volume"))) for k, q in qs.items() if k in keymap}

    @bg
    def one(item):
        k, sym = item
        q = qs.get(k)
        if not q or time.time() > end:
            return None
        try:
            rows = shared_cache.fetch(f"dc|{k}|{date.today().isoformat()}", 20 * 3600, lambda: up.get_candles(k, "day"))
        except Exception:
            return None
        r = _pick(sym, q, rows)
        if r:
            r["kind"] = "index" if sym in PICK_INDICES else "stock"
            r["universe"] = "fno" if sym in fno_syms else "cash"
            if sym not in fno_syms:                  # cash universe: liquidity + strength floors keep junk out
                extra_done.add(sym)
                if (qs_vol.get(sym) or 0) < PICK_EXTRA_FLOOR_VOL or r["ltp"] < PICK_EXTRA_FLOOR_LTP:
                    return None
                if (r.get("strength") or 0) < PICK_CASH_MIN_STRENGTH:
                    return None
        return r

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        return [r for r in pool.map(one, keymap.items()) if r]


def quick_index_calls(deadline_s=8):
    """Index CALL / PUT ideas (daily chart and ATM option flow agree) without screening all 218 symbols."""
    tech = {p["s"]: p for p in quick_screen(list(CALL_INDICES), deadline_s)}
    out = []
    for sym in CALL_INDICES:
        try:
            r = _index_call(sym, tech.get(sym) or {})
            if sym not in tech and r.get("signal") in ("WATCH", "NO SIGNAL") and r.get("reason"):
                r["reason"] += " (the daily-chart screen gave no result in time - it is read as neutral)"
            out.append(r)
        except Exception as e:
            out.append({"instrument": sym, "signal": "NO SIGNAL", "reason": str(e)[:80]})
    return out


@router.get("/kv-health")
def kv_health():
    """Is the shared store (Upstash) answering? Used to explain 'Delayed' prices / missing auto-trader state."""
    return shared_cache.diagnose()


@router.get("/kv-cleanup")
def kv_cleanup():
    """Removes leftover rl2:* rate-limit counters (junk) and the broken first-generation bhavcopy
    day cache (bhav:day|* - parsed with the wrong volume column, every row volume=0) from Upstash.
    Never touches any other key."""
    out = shared_cache.cleanup_junk()
    try:
        out["bhav_day_junk"] = shared_cache.cleanup_prefix("bhav:day|")
    except Exception as e:
        out["bhav_day_junk"] = {"ok": False, "reason": str(e)[:120]}
    return out


@router.api_route("/kv-migrate", methods=["GET", "POST"])
def kv_migrate(overwrite: int = 0, authorization: str = Header(default=""), x_admin_key: str = Header(default="")):
    """One-time copy of the auto trader / stock trader / push state from the old Upstash database to the new one.
    It can overwrite the live books, so it needs the server's CRON_SECRET (Authorization: Bearer ...) or GODS_EYE_ADMIN_KEY (X-Admin-Key);
    with neither configured it is disabled."""
    secrets = [x for x in (os.environ.get("CRON_SECRET"), os.environ.get("GODS_EYE_ADMIN_KEY")) if x]
    given = [authorization[7:] if authorization.lower().startswith("bearer ") else authorization, x_admin_key]
    if not secrets or not any(g and hmac.compare_digest(g.encode(), sec.encode()) for g in given for sec in secrets):
        raise HTTPException(403, "Admin only: send CRON_SECRET as a Bearer token or GODS_EYE_ADMIN_KEY as X-Admin-Key (disabled when neither is set on the server)")
    r = shared_cache.migrate_state(bool(overwrite))
    if r.get("ok"):
        try:                                     # drop any copy the state modules hold in memory so the moved data shows at once
            import auto_trader, stock_trader
            auto_trader._RC.clear(); stock_trader._RC.clear()
        except Exception:
            pass
    return r


@router.get("/budget")
def budget():
    """How much of the shared Upstox request budget is in use right now."""
    from upstox_service import budget_usage, call_stats
    return {**budget_usage(), "calls": call_stats()}
