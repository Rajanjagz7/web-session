"""Market data + recommendations API for the Rajan Stocks UI.

All numbers come from Upstox (quotes, candles). Nothing is simulated.
"""
import concurrent.futures
import re
import time
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query

from nse_service import nse_service
from upstox_service import _BG

upstox_service = nse_service.upstox

router = APIRouter(prefix="/api/m")
IST = timezone(timedelta(hours=5, minutes=30))

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
CORE = [s for s, _, _ in STOCKS]            # curated liquid set (sectors known) -> default for heavy scans
CORE_SECTOR = {s: sec for s, _, sec in STOCKS}
CORE_NAME = {s: n for s, n, _ in STOCKS}
INDICES[:] = [("NIFTY", "Nifty 50"), ("BANKNIFTY", "Nifty Bank"), ("FINNIFTY", "Nifty Fin Service"),
              ("MIDCPNIFTY", "Nifty Midcap Select"), ("NIFTYNXT50", "Nifty Next 50"), ("SENSEX", "BSE Sensex"),
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


def _key(sym):
    key, _is_index = nse_service.upstox._resolve_underlying(sym)
    return key


def market_open():
    n = datetime.now(IST)
    mins = n.hour * 60 + n.minute
    return n.weekday() < 5 and 9 * 60 + 15 <= mins <= 15 * 60 + 30


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
                keymap[_key(s)] = s
            except Exception:
                continue
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
            out.append({
                "s": s, "last": last, "prev": prev,
                "open": _num(o.get("open")), "high": _num(o.get("high")), "low": _num(o.get("low")),
                "vol": _num(q.get("volume")) or _num(o.get("volume")),
                "bid": _num(((q.get("depth") or {}).get("buy") or [{}])[0].get("price")),
                "ask": _num(((q.get("depth") or {}).get("sell") or [{}])[0].get("price")),
                "yh": _num(q.get("year_high")), "yl": _num(q.get("year_low")),
            })
        if not out and keymap:
            raise RuntimeError("Upstox returned no quotes")     # never cache an empty answer
        return out

    ck = "q|" + ",".join(syms)
    stale, why = False, ""
    try:
        ttl = 5 if market_open() else 300          # market closed: prices cannot move, keep them for minutes
        now = time.time()
        have, missing = {}, []
        for s in syms:
            h = _QSYM.get(s)
            if h and now - h[0] < ttl:
                have[s] = h[1]
            else:
                missing.append(s)
        if missing:
            got = _cached("qf|" + ",".join(missing), 2, lambda: fetch(missing))
            t0 = time.time()
            for q in got:
                _QSYM[q["s"]] = (t0, q)
                have[q["s"]] = q
        data = [have[s] for s in syms if s in have]
        if not data and syms:
            raise RuntimeError("no quotes available")
        _QLAST[ck] = (time.time(), data)
    except Exception as e:
        last = _QLAST.get(ck)
        if last and time.time() - last[0] < 1800:
            data, stale, why = last[1], True, str(e)[:160]
        else:
            raise HTTPException(503, f"Live prices are temporarily unavailable: {str(e)[:160]}")
    out = {"quotes": data, "marketOpen": market_open(), "asOf": datetime.now(IST).isoformat(), "stale": stale}
    if stale:
        out["quotesAsOf"] = datetime.fromtimestamp(_QLAST[ck][0], IST).isoformat()
        out["reason"] = why
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
    if not (now.weekday() < 5 and now.hour * 60 + now.minute >= 9 * 60 + 15):
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
def candles(symbol: str = "", tf: str = "1D", ikey: str = "", frm: str = Query("", alias="from"), to: str = ""):
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
    d_from = d_to = None
    try:
        if frm:
            d_from = date.fromisoformat(frm)
        if to:
            d_to = date.fromisoformat(to)
    except ValueError:
        raise HTTPException(400, "from / to must be YYYY-MM-DD")
    if d_from and (d_from < date(1900, 1, 1) or d_from > date.today()):
        raise HTTPException(400, "from must be between 1900-01-01 and today")
    if d_to and d_from and d_to < d_from:
        raise HTTPException(400, "to must not be before from")
    if d_from and not ikey:
        need = (date.today() - d_from).days
        if kind == "day":
            days = min(max(need, 30), 40000)
        else:
            cap = {"1": 180, "2": 180, "3": 180, "5": 365}.get(interval, 1830)   # intraday exists only from Jan 2022
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
            hist = _cached_ok(f"hd|{ikey or sym}|{days}|{today}", HIST_TTL, _dh)
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
        hist = _cached_ok(f"hm|{ikey or sym}|{interval}|{days}|{today}", HIST_TTL, _mh)
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
        return bars

    try:
        bars = _cached(f"c|{sym}|{tf}|{frm}|{to}", 4 if market_open() else 60, fetch)
    except Exception as e:
        raise HTTPException(502, f"Upstox candles failed: {e}")
    first = bars[0]["t"] if bars else None
    return {"symbol": sym, "tf": tf, "bars": bars, "from": frm or None, "to": to or None, "first": first,
            "note": ("Intraday history is available from Jan 2022 only." if d_from and kind == "min" and d_from < date(2022, 1, 1) else None)}


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
        try:
            lot = int((nse_service.upstox.fo_universe().get("lots") or {}).get(sym) or 1)
        except Exception:
            lot = 1
        return {"symbol": sym, "lot": lot, "spot": spot, "expiry": data.get("targetExpiry"), "expiries": data.get("expiryDates") or [],
                "atm": atm, "rows": rows, "provider": "Upstox", "asOf": datetime.now(IST).isoformat()}

    try:
        return _cached(f"chain|{sym}|{expiry}", 3 if market_open() else 45, build)
    except Exception as e:
        raise HTTPException(502, f"Option chain failed: {e}")


@router.get("/oquote")
def oquote(keys: str):
    ks = [k.strip() for k in keys.split(",") if re.match(r"^(NSE|BSE)_FO\|\d+$", k.strip())][:30]
    if not ks:
        raise HTTPException(400, "keys required")
    try:
        raw = _cached("oq|" + ",".join(sorted(ks)), 4 if market_open() else 120, lambda: nse_service.upstox._full_quotes(ks))
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
            tol = max(0.05, last * 0.0002)
            is_oh, is_ol = abs(op - hi) <= tol, abs(op - lo) <= tol
            if not (is_oh or is_ol):
                continue
            chg = (last / prev - 1) * 100 if prev else 0.0
            found.append({
                "symbol": sym, "name": NAME.get(sym, sym), "type": "Index" if sym in INDEX_SET else "Stock",
                "sector": SECTOR.get(sym, ""), "ltp": round(last, 2), "prev": round(prev, 2), "chg": round(chg, 2),
                "open": op, "high": hi, "low": lo, "vol": _num(q.get("volume")) or _num(o.get("volume")),
                "status": "OPEN_LOW" if is_ol else "OPEN_HIGH",
                "bias": "Bullish" if is_ol else "Bearish",
                "idea": ("Opened at the day low — buyers in control. Buy futures or buy CE; or sell PE for premium. The day low is the natural stop."
                         if is_ol else "Opened at the day high — sellers in control. Sell futures, buy PE or sell CE for premium. The day high is the natural stop."),
            })
        found.sort(key=lambda r: -abs(r["chg"]))
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
                                         "ol": leg["high"] > leg["low"] and abs(leg["open"] - leg["low"]) <= t})
                r["options"] = {"expiry": c["expiry"], "atm": c["atm"], "spot": c["spot"], "legs": legs}
            except Exception:
                r["options"] = None
            return r

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            top = list(pool.map(with_options, found[:limit]))
        return {"rows": top + [dict(r, options=None) for r in found[limit:]], "total": total, "detailed": len(top),
                "marketOpen": market_open(), "asOf": datetime.now(IST).isoformat()}

    if refresh:
        _cache.pop("daily", None)
    try:
        return _cached("daily", 60 if market_open() else 600, build)
    except Exception as e:
        raise HTTPException(502, f"Daily scan failed: {e}")


# ----------------------------- Global markets & futures (GIFT Nifty, US futures, Nasdaq ...) -----------------------------
GLOBAL_ITEMS = [
    ("NSEIX:NIFTY1!", "GIFT Nifty", "Index futures"), ("NSEIX:BANKNIFTY1!", "GIFT Bank Nifty", "Index futures"),
    ("CBOT_MINI:YM1!", "Dow Fut", "US futures"), ("CME_MINI:ES1!", "S&P 500 Fut", "US futures"),
    ("CME_MINI:NQ1!", "Nasdaq 100 Fut", "US futures"), ("NASDAQ:IXIC", "Nasdaq", "US indices"),
    ("NASDAQ:NDX", "Nasdaq 100", "US indices"), ("SP:SPX", "S&P 500", "US indices"), ("DJ:DJI", "Dow Jones", "US indices"),
    ("CBOE:VIX", "US VIX", "US indices"), ("MCX:GOLD1!", "Gold (MCX)", "Commodities"), ("MCX:CRUDEOIL1!", "Crude Oil (MCX)", "Commodities"),
    ("MCX:SILVER1!", "Silver (MCX)", "Commodities"), ("COMEX:GC1!", "Gold (COMEX)", "Commodities"), ("NYMEX:CL1!", "Crude (NYMEX)", "Commodities"),
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


def global_markets_legacy():
    """Shape the original Rajan Trading UI expects: commodities[] + INR rate."""
    items = global_markets()["items"]
    comm = []
    for it in items:
        if it["id"] == "FX_IDC:USDINR":
            continue
        dec = 0 if it["price"] >= 20000 else 2
        comm.append({"id": it["id"], "name": it["name"], "label": it["group"], "chart": it.get("chart", True), "price": it["price"], "chg": it["chg"],
                     "chgPct": it["chgPct"], "priceFormatted": _in_fmt(it["price"], dec), "available": True, "mode": it["mode"]})
    inr = next((i for i in items if i["id"] == "FX_IDC:USDINR"), None)
    return {"success": True, "commodities": comm, "inrUsd": inr["price"] if inr else None,
            "inrChgPct": inr["chgPct"] if inr else None, "items": items}


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
    factor = 1
    if u in "mH":                                   # TradingView serves only some minute intervals natively
        mins = n if u == "m" else n * 60
        if mins in (1, 2, 3, 5, 10, 15, 30, 45, 60, 120, 180, 240):
            res = str(mins)
        else:
            base = next(b for b in (240, 180, 120, 60, 45, 30, 15, 10, 5, 3, 2, 1) if mins % b == 0)
            res, factor = str(base), mins // base
    else:
        res = TV_RES[u]( 1 )                       # D / W / M: fetch the 1-period series and group it ourselves
    count = max(50, min(count, 5000))

    def fetch():
        rows = _tv_history(id, res, min(5000, count * factor))
        out = [{"t": int(r[0] * 1000), "o": r[1], "h": r[2], "l": r[3], "c": r[4], "v": (r[5] if len(r) > 5 else 0) or 0} for r in rows]
        if factor > 1:
            out = _resample(out, factor)
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
        try:
            nse_service.upstox._full_quotes([_key("NIFTY")])
            return None
        except Exception as e:
            return str(e)[:160]

    err = _cached("token-probe", 300, probe)
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
        out["message"] = "Upstox connected."
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
    stop = ltp - sgn * 1.5 * atr
    t1, t2 = ltp + sgn * 2 * atr, ltp + sgn * 3.5 * atr
    return {
        "s": sym, "n": NAME.get(sym, sym), "sec": SECTOR.get(sym, ""),
        "ltp": round(ltp, 2), "chg": round(chg, 2), "prev": round(prev, 2),
        "signal": signal, "score": score, "strength": min(100, abs(score) * 25 + (10 if volx >= 1.5 else 0)),
        "intraday": {1: "Bullish", -1: "Bearish", 0: "Neutral"}[intra],
        "swing": {1: "Bullish", -1: "Bearish", 0: "Neutral"}[short],
        "positional": {1: "Bullish", -1: "Bearish", 0: "Neutral"}[long_],
        "entry": round(entry, 2), "stop": round(stop, 2),
        "target": round(t1, 2), "target2": round(t2, 2),
        "rr": round(abs(t1 - entry) / abs(entry - stop), 2) if stop != entry else 0,
        "rsi": round(rsi, 1) if rsi is not None else None,
        "volx": round(volx, 2), "atr": round(atr, 2), "reasons": reasons,
        "spark": [round(c, 2) for c in closes[-20:]],
    }


@router.get("/picks")
def picks(refresh: bool = False):
    ensure_universe()

    def build():
        up = nse_service.upstox
        keymap = {}
        for s, _, _ in STOCKS:
            try:
                keymap[_key(s)] = s
            except Exception:
                pass
        qs = up._full_quotes(list(keymap.keys()))
        deadline = time.time() + 22          # stay well inside the serverless time limit

        def daily(k):
            return _cached(f"dc|{k}|{date.today().isoformat()}", 6 * 3600, lambda: up.get_candles(k, "day"))

        @bg
        def one(item):
            k, sym = item
            q = qs.get(k)
            if not q or time.time() > deadline:
                return None
            try:
                rows = daily(k)
            except Exception:
                return None
            return _pick(sym, q, rows)

        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
            res = [r for r in pool.map(one, keymap.items()) if r]
        buys = sorted([r for r in res if r["signal"] == "BUY"], key=lambda r: (-r["score"], -r["volx"]))
        sells = sorted([r for r in res if r["signal"] == "SELL"], key=lambda r: (r["score"], -r["volx"]))
        return {
            "picks": res, "buy": buys, "sell": sells,
            "count": len(res), "universe": len(keymap), "marketOpen": market_open(),
            "asOf": datetime.now(IST).isoformat(),
            "note": "Rule-based screen on EMA trend, day-range position, volume and RSI. Not investment advice.",
        }

    if refresh:
        _cache.pop("picks", None)
    try:
        return _cached("picks", 900 if market_open() else 3600, build)
    except Exception as e:
        raise HTTPException(502, f"Picks failed: {e}")
