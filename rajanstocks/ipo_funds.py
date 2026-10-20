"""IPO + Mutual Fund hub: IPO pipeline with grey market premium (GMP) and listing performance, mutual fund
returns and SIP / lumpsum calculators from real NAV history.

Sources (all public, fetched server-side and cached):
  - NSE  /api/ipo-current-issue, /api/all-upcoming-issues, /api/public-past-issues - official dates, price band,
    subscription and final issue price (via nse_service's cookie session).
  - ipowatch.in GMP table - grey market premium. GMP is unofficial, informal market chatter, never a guarantee.
  - Yahoo Finance daily bars - listing-day open/close and the latest price of a listed IPO.
  - mfapi.in (AMFI NAV history) - scheme search and full daily NAV history for mutual funds.
"""
import html as _html
import math
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser

import requests
from fastapi import APIRouter, HTTPException, Query

import shared_cache

router = APIRouter()
IST = timezone(timedelta(hours=5, minutes=30))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
      "Accept-Language": "en-IN,en;q=0.9"}
_http = requests.Session()
_http.headers.update(UA)

_mem = {}
_mem_lock = threading.Lock()
_VERCEL = bool(os.environ.get("VERCEL"))


def _today():
    return datetime.now(IST).date()


def _cached(key, ttl, fn, shared=True):
    """Memory first, then Upstash, then compute. Stores in both."""
    now = time.time()
    with _mem_lock:
        hit = _mem.get(key)
    if hit and now - hit[0] < ttl:
        return hit[1]
    val = shared_cache.get(key) if shared else None
    if val is None:
        val = fn()
        if not val:
            return val          # never cache an empty result - the next call retries the sources
        if shared:
            shared_cache.set(key, val, ttl)
    with _mem_lock:
        _mem[key] = (now, val)
    return val


def _num(s):
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    m = re.search(r"-?\d[\d,]*\.?\d*(?:[eE][+-]?\d+)?", str(s).replace("₹", ""))
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


def _band(s):
    """'Rs.327 to Rs.344' -> (327, 344); 'Rs.1000' -> (1000, 1000)."""
    nums = [float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*\.?\d*", str(s or ""))]
    if not nums:
        return None, None
    return min(nums), max(nums)


def _d(s):
    if not s or s.strip() in ("-", ""):
        return None
    for fmt in ("%d-%b-%Y", "%d-%B-%Y", "%Y-%m-%d", "%d %b %Y"):
        try:
            return datetime.strptime(s.strip().title() if "%b" in fmt or "%B" in fmt else s.strip(), fmt).date()
        except ValueError:
            continue
    return None


_STOP = {"limited", "ltd", "ipo", "the", "private", "pvt", "and", "&", "co", "company", "sme", "nse", "bse", "india", "of"}


def _norm(name):
    t = re.sub(r"[^a-z0-9 ]", " ", (name or "").lower())
    return [w for w in t.split() if w not in _STOP]


def _same(a, b):
    ta, tb = _norm(a), _norm(b)
    if not ta or not tb:
        return 0.0
    if ta[0] != tb[0]:
        return 0.0
    sa, sb = set(ta), set(tb)
    return len(sa & sb) / max(1, min(len(sa), len(sb)))


def _key(name):
    return " ".join(_norm(name)[:4])


# ----------------------------------------------------------------------------- GMP (ipowatch)
class _Tables(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables, self._row, self._cell, self._in = [], None, None, 0

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._in += 1
            self.tables.append([])
        elif tag == "tr" and self._in:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []
        elif tag == "br" and self._cell is not None:
            self._cell.append(" ")

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(re.sub(r"\s+", " ", "".join(self._cell)).strip())
            self._cell = None
        elif tag == "tr" and self._row is not None and self._in:
            if self._row:
                self.tables[-1].append(self._row)
            self._row = None
        elif tag == "table" and self._in:
            self._in -= 1

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


_STATUS_RE = re.compile(r"\b(upcoming|open|closed|listed|close|opens? today|closes? today)\b", re.I)


def _parse_gmp_html(text):
    p = _Tables()
    p.feed(text)
    out = []
    for tbl in p.tables:
        if not tbl:
            continue
        head = [h.lower() for h in tbl[0]]
        if not any("gmp" in h for h in head) or not any("company" in h or "ipo" in h for h in head):
            continue
        ci = next(i for i, h in enumerate(head) if "company" in h or "ipo" in h)
        gi = next(i for i, h in enumerate(head) if "gmp" in h)
        pi = next((i for i, h in enumerate(head) if "price" in h), None)
        ei = next((i for i, h in enumerate(head) if "gain" in h or "listing" in h), None)
        di = next((i for i, h in enumerate(head) if "date" in h), None)
        for r in tbl[1:]:
            if len(r) <= max(ci, gi):
                continue
            raw = _html.unescape(r[ci])
            st = _STATUS_RE.findall(raw)
            status = (st[-1].lower() if st else "").replace("close", "closed").replace("closedd", "closed")
            if "open" in status:
                status = "open"
            name = _STATUS_RE.sub("", raw)
            sme = bool(re.search(r"\bSME\b", name, re.I))
            name = re.sub(r"\b(BSE|NSE)?\s*SME\b|\bIPO\b", "", name, flags=re.I)
            name = re.sub(r"\s+", " ", name).strip(" -|")
            if not name:
                continue
            gmp_txt = r[gi]
            gmp = None if re.fullmatch(r"\W*-?\W*", gmp_txt.replace("₹", "")) else _num(gmp_txt)
            price = _num(r[pi]) if pi is not None and pi < len(r) else None
            est_txt = r[ei] if ei is not None and ei < len(r) else ""
            est = _num(est_txt)
            pct = re.search(r"\((-?\d+\.?\d*)%\)", est_txt)
            out.append({"name": name, "status": status or None, "sme": sme, "gmp": gmp, "price": price,
                        "est_listing": est if est and price and est > 0 else (price + gmp if price and gmp is not None else None),
                        "est_gain_pct": float(pct.group(1)) if pct else (round(gmp / price * 100, 2) if price and gmp is not None else None),
                        "dates": r[di] if di is not None and di < len(r) else ""})
        if out:
            break
    return out


GMP_URLS = ["https://ipowatch.in/ipo-grey-market-premium-latest-ipo-gmp/"]


def fetch_gmp():
    for url in GMP_URLS:
        try:
            r = _http.get(url, timeout=12)
            r.raise_for_status()
            rows = _parse_gmp_html(r.text)
            if rows:
                return {"rows": rows, "source": url}
        except Exception:
            continue
    return {"rows": [], "source": None}


def _update_gmp_history(rows):
    """Keep the GMP seen each day per IPO (up to 15 points) so a listed IPO can be compared with its last GMP."""
    if not rows:
        return {}
    hist = shared_cache.get("ipo:gmphist") or {}
    today = _today().isoformat()
    for r in rows:
        if r["gmp"] is None:
            continue
        k = _key(r["name"])
        h = hist.get(k) or {"name": r["name"], "pts": []}
        pts = [p for p in h.get("pts", []) if p[0] != today]
        pts.append([today, r["gmp"]])
        h.update({"name": r["name"], "price": r["price"], "pts": pts[-15:], "last": r["gmp"], "seen": today})
        hist[k] = h
    cutoff = (_today() - timedelta(days=200)).isoformat()
    hist = {k: v for k, v in hist.items() if v.get("seen", "") >= cutoff}
    shared_cache.set("ipo:gmphist", hist, 200 * 86400)
    return hist


# ----------------------------------------------------------------------------- NSE
def _nse(path):
    from nse_service import nse_service
    return nse_service._get_json("https://www.nseindia.com" + path)


def fetch_nse_current():
    out = {}
    for path in ("/api/ipo-current-issue", "/api/all-upcoming-issues?category=ipo"):
        try:
            data = _nse(path)
        except Exception:
            continue
        rows = data if isinstance(data, list) else (data.get("data") or [])
        for x in rows:
            sym = x.get("symbol")
            if not sym:
                continue
            cur = out.setdefault(sym, {})
            lo, hi = _band(x.get("issuePrice"))
            cur.update({k: v for k, v in {
                "symbol": sym, "name": x.get("companyName") or x.get("company"), "series": x.get("series"),
                "open_date": (_d(x.get("issueStartDate")) or None), "close_date": _d(x.get("issueEndDate")),
                "band_lo": lo, "band_hi": hi, "issue_size": _num(x.get("issueSize")), "nse_status": x.get("status"),
            }.items() if v is not None})
            if x.get("noOfTime") not in (None, "", "-"):
                cur["subscribed_x"] = round(_num(x.get("noOfTime")) or 0, 2)
    for v in out.values():
        for k in ("open_date", "close_date"):
            if isinstance(v.get(k), date):
                v[k] = v[k].isoformat()
    return list(out.values())


def fetch_nse_past(days=120):
    try:
        data = _nse("/api/public-past-issues")
    except Exception:
        return []
    rows = data if isinstance(data, list) else (data.get("data") or [])
    since = _today() - timedelta(days=days)
    out = []
    for x in rows:
        if (x.get("securityType") or "").upper() not in ("EQ", "SME", "BE", "SM", "ST"):
            continue
        ld = _d(x.get("listingDate"))
        if not ld or ld < since or ld > _today():
            continue
        lo, hi = _band(x.get("priceRange"))
        out.append({"symbol": x.get("symbol"), "name": x.get("companyName") or x.get("company"),
                    "series": "SME" if (x.get("securityType") or "").upper() in ("SME", "SM", "ST") else "EQ",
                    "open_date": (_d(x.get("ipoStartDate")) or ld).isoformat(), "close_date": (_d(x.get("ipoEndDate")) or ld).isoformat(),
                    "listing_date": ld.isoformat(), "issue_price": _num(x.get("issuePrice")) or hi, "band_lo": lo, "band_hi": hi})
    out.sort(key=lambda r: r["listing_date"], reverse=True)
    return out


# ----------------------------------------------------------------------------- listing performance (Yahoo)
def _pick(row, *keys):
    for k in keys:
        if row.get(k) not in (None, "", "-"):
            return row[k]
    return None


def _nse_bars(symbol, since):
    """Daily OHLC from NSE's own history API - covers SME (SM/ST series) that Yahoo barely has."""
    out = {}
    start, end = since - timedelta(days=1), _today()
    while start <= end:
        stop = min(end, start + timedelta(days=360))
        q = requests.utils.quote(symbol)
        f, t = start.strftime('%d-%m-%Y'), stop.strftime('%d-%m-%Y')
        js = None
        for path in (f"/api/historicalOR/generateSecurityWiseHistoricalData?from={f}&to={t}&symbol={q}&type=priceVolumeDeliverable&series=ALL",
                     f"/api/historical/securityArchives?from={f}&to={t}&symbol={q}&dataType=priceVolumeDeliverable&series=ALL",
                     f"/api/historical/cm/equity?symbol={q}&series=[%22EQ%22,%22BE%22,%22SM%22,%22ST%22]&from={f}&to={t}"):
            try:
                cand = _nse(path)
                rows = cand.get("data") if isinstance(cand, dict) else None
                if rows:
                    js = cand
                    break
            except Exception:
                continue
        for r in (js or {}).get("data") or []:
            dd = _d(str(r.get("mTIMESTAMP") or "")[:11])  # "13-Oct-2026" - the trading day itself
            if not dd:
                d = str(_pick(r, "CH_TIMESTAMP", "TIMESTAMP") or "")
                try:  # ISO, possibly a UTC instant ("2026-10-12T18:30:00Z" is 13 Oct in IST)
                    dd = datetime.fromisoformat(d.replace("Z", "+00:00")).astimezone(IST).date() if "T" in d else date.fromisoformat(d[:10])
                except ValueError:
                    dd = _d(d[:11])
            o, h, l, c = (_num(_pick(r, *k)) for k in (("CH_OPENING_PRICE", "OPEN_PRICE"), ("CH_TRADE_HIGH_PRICE", "HIGH_PRICE"),
                                                      ("CH_TRADE_LOW_PRICE", "LOW_PRICE"), ("CH_CLOSING_PRICE", "CLOSE_PRICE")))
            if dd and None not in (o, h, l, c) and c > 0:
                out[dd.isoformat()] = {"date": dd.isoformat(), "open": o, "high": h, "low": l, "close": c}
        start = stop + timedelta(days=1)
    return [out[k] for k in sorted(out)]


def _price_bars(symbol, since):
    """Yahoo first; NSE history when Yahoo has (almost) nothing - typical for SME listings."""
    bars, live = _yahoo_bars(symbol, since)
    if len([b for b in bars if b["date"] >= since.isoformat()]) < 3 and (_today() - since).days >= 3:
        nb = _nse_bars(symbol, since)
        if nb and len(nb) >= len(bars):  # official NSE bars win a tie
            return nb, None
    return bars, live


def _yahoo_bars(symbol, since):
    p1 = int(datetime.combine(since - timedelta(days=2), datetime.min.time(), tzinfo=timezone.utc).timestamp())
    p2 = int(time.time()) + 86400
    for ys in (f"{symbol}.NS", f"{symbol}-SM.NS", f"{symbol}.BO"):
        try:
            r = _http.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{ys}",
                          params={"period1": p1, "period2": p2, "interval": "1d"}, timeout=10)
            if r.status_code != 200:
                continue
            res = (r.json().get("chart") or {}).get("result") or []
            if not res or not res[0].get("timestamp"):
                continue
            q = res[0]["indicators"]["quote"][0]
            bars = []
            for i, ts in enumerate(res[0]["timestamp"]):
                o, h, l, c = (q.get(k, [None])[i] for k in ("open", "high", "low", "close"))
                if None in (o, h, l, c):
                    continue
                bars.append({"date": datetime.fromtimestamp(ts, IST).date().isoformat(), "open": o, "high": h, "low": l, "close": c})
            if bars:
                meta = res[0].get("meta") or {}
                return bars, meta.get("regularMarketPrice")
        except Exception:
            continue
    return [], None


def _range_stats(bars, cur):
    """High/low since listing and over the last 52 weeks (= since listing when it listed under a year ago)."""
    if not bars:
        return {}
    cut = (_today() - timedelta(days=365)).isoformat()
    yr = [b for b in bars if b["date"] >= cut] or bars
    hi_b, lo_b = max(bars, key=lambda b: b["high"]), min(bars, key=lambda b: b["low"])
    h52, l52 = max(yr, key=lambda b: b["high"]), min(yr, key=lambda b: b["low"])
    out = {"high_since": round(hi_b["high"], 2), "high_since_date": hi_b["date"], "low_since": round(lo_b["low"], 2), "low_since_date": lo_b["date"],
           "hi52": round(h52["high"], 2), "hi52_date": h52["date"], "lo52": round(l52["low"], 2), "lo52_date": l52["date"],
           "w52_partial": bars[0]["date"] > cut}
    if cur:
        out["from_hi52_pct"] = round((cur / h52["high"] - 1) * 100, 2)
        out["from_lo52_pct"] = round((cur / l52["low"] - 1) * 100, 2)
    return out


def _listing_perf(item):
    ld = date.fromisoformat(item["listing_date"])
    bars, live = _price_bars(item["symbol"], ld)
    bars = [b for b in bars if b["date"] >= item["listing_date"]]
    if not bars:
        return item
    b0, last = bars[0], bars[-1]
    ip = item.get("issue_price")
    cur = live or last["close"]
    item.update({"list_open": round(b0["open"], 2), "list_close": round(b0["close"], 2), "list_high": round(b0["high"], 2),
                 "list_low": round(b0["low"], 2), "current": round(cur, 2),
                 "spark": [round(b["close"], 2) for b in bars[-30:]]})
    item.update(_range_stats(bars, cur))
    if ip:
        item["listing_gain_pct"] = round((b0["open"] - ip) / ip * 100, 2)
        item["day1_close_pct"] = round((b0["close"] - ip) / ip * 100, 2)
        item["return_pct"] = round((cur - ip) / ip * 100, 2)
    return item


# ----------------------------------------------------------------------------- IPO dashboard
def _status_of(row, today):
    od, cd = row.get("open_date"), row.get("close_date")
    if od and cd:
        if today < date.fromisoformat(od):
            return "upcoming"
        if today <= date.fromisoformat(cd):
            return "open"
        return "closed"
    s = (row.get("gmp_status") or "").lower()
    return s if s in ("upcoming", "open", "closed", "listed") else "upcoming"


def build_ipo_dashboard():
    today = _today()
    with ThreadPoolExecutor(3) as ex:
        f_gmp, f_cur, f_past = ex.submit(fetch_gmp), ex.submit(fetch_nse_current), ex.submit(fetch_nse_past)
        gmp, cur, past = f_gmp.result(), f_cur.result(), f_past.result()
    gmp_rows = gmp["rows"]
    hist = _update_gmp_history(gmp_rows)
    used = set()

    def match(name):
        best, bi = 0.0, None
        for i, g in enumerate(gmp_rows):
            if i in used:
                continue
            s = _same(name, g["name"])
            if s > best:
                best, bi = s, i
        if bi is not None and best >= 0.5:
            used.add(bi)
            return gmp_rows[bi]
        return None

    def hist_of(name):
        k = _key(name)
        if k in hist:
            return hist[k]
        for hk, hv in hist.items():
            if _same(name, hv.get("name", "")) >= 0.6:
                return hv
        return None

    past_syms = {p["symbol"] for p in past}
    live = []
    for c in cur:
        if c.get("symbol") in past_syms:
            continue
        g = match(c.get("name", ""))
        row = dict(c)
        row["sme"] = (c.get("series") or "").upper() in ("SME", "SM", "ST") or bool(g and g["sme"])
        row["price"] = c.get("band_hi") or (g and g["price"])
        if g:
            row.update({"gmp": g["gmp"], "gmp_status": g["status"], "dates_text": g["dates"]})
        live.append(row)
    for i, g in enumerate(gmp_rows):  # IPOs only the GMP feed knows (BSE-only, SME, not yet on NSE)
        if i in used or g["status"] == "listed":
            continue
        if any(_same(g["name"], p["name"]) >= 0.5 for p in past):
            continue
        live.append({"name": g["name"], "sme": g["sme"], "price": g["price"], "gmp": g["gmp"], "gmp_status": g["status"],
                     "dates_text": g["dates"]})
    for row in live:
        h = hist_of(row["name"])
        row["gmp_trend"] = [p[1] for p in (h or {}).get("pts", [])]
        p, gm = row.get("price"), row.get("gmp")
        if p and gm is not None:
            row["expected_listing"] = round(p + gm, 2)
            row["expected_gain_pct"] = round(gm / p * 100, 2)
        row["status"] = _status_of(row, today)

    with ThreadPoolExecutor(8) as ex:
        listed = list(ex.map(_listing_perf, past[:45]))
    for row in listed:
        row["sme"] = row.get("series") == "SME"
        row["status"] = "listed"
        h = hist_of(row["name"])
        if h and h.get("last") is not None:
            row["last_gmp"] = h["last"]
            row["gmp_trend"] = [p[1] for p in h.get("pts", [])]
            ip = row.get("issue_price")
            if ip:
                row["expected_listing"] = round(ip + h["last"], 2)
                row["expected_gain_pct"] = round(h["last"] / ip * 100, 2)
                if row.get("list_open") is not None:
                    row["gmp_error_pct"] = round(row["listing_gain_pct"] - row["expected_gain_pct"], 2)

    order = {"open": 0, "upcoming": 1, "closed": 2}
    live.sort(key=lambda r: (order.get(r["status"], 3), r.get("close_date") or "9999", r["name"]))
    gains = [r["listing_gain_pct"] for r in listed if r.get("listing_gain_pct") is not None]
    errs = [abs(r["gmp_error_pct"]) for r in listed if r.get("gmp_error_pct") is not None]
    return {
        "as_of": datetime.now(IST).isoformat(timespec="seconds"),
        "gmp_source": gmp["source"],
        "ipos": live + listed,
        "counts": {s: sum(1 for r in live + listed if r["status"] == s) for s in ("open", "upcoming", "closed", "listed")},
        "stats": {
            "listed_count": len(gains),
            "avg_listing_gain_pct": round(sum(gains) / len(gains), 2) if gains else None,
            "positive_listing_share": round(sum(1 for g in gains if g > 0) / len(gains) * 100, 1) if gains else None,
            "gmp_avg_abs_error_pct": round(sum(errs) / len(errs), 2) if errs else None,
            "gmp_compared": len(errs),
        },
    }


_DASH_KEY, _DASH_TTL, _DASH_STALE = "ipo:dash:v4", 900, 6 * 3600
_dash_busy = threading.Event()


def _dash_store(data):
    shared_cache.set(_DASH_KEY, data, _DASH_TTL)
    shared_cache.set(_DASH_KEY + ":stale", data, _DASH_STALE)
    with _mem_lock:
        _mem[_DASH_KEY] = (time.time(), data)


def _dash_refresh():
    """Rebuild the dashboard (about 7 s: three slow public sources) and keep a long-lived stale copy beside the fresh one."""
    try:
        data = build_ipo_dashboard()
        if data:
            _dash_store(data)
        return data
    finally:
        _dash_busy.clear()


def warm_dashboard():
    """Server start (own-server mode): build it in the background so the first visit is instant."""
    if not _dash_busy.is_set():
        _dash_busy.set()
        threading.Thread(target=_dash_refresh, daemon=True, name="ipo-warm").start()


@router.get("/api/ipo/dashboard")
def ipo_dashboard(refresh: bool = False):
    """Fresh copy when we have one; otherwise the last good copy straight away while a background rebuild runs
    (serverless instances cannot run background work, so there it rebuilds inline)."""
    try:
        if not refresh:
            with _mem_lock:
                hit = _mem.get(_DASH_KEY)
            if hit and time.time() - hit[0] < _DASH_TTL:
                return hit[1]
            fresh = shared_cache.get(_DASH_KEY)
            if fresh:
                with _mem_lock:
                    _mem[_DASH_KEY] = (time.time(), fresh)
                return fresh
            stale = shared_cache.get(_DASH_KEY + ":stale")
            if stale and not _VERCEL:
                if not _dash_busy.is_set():
                    warm_dashboard()
                return {**stale, "stale": True}
        _dash_busy.set()
        return _dash_refresh()
    except Exception as e:
        raise HTTPException(502, f"Could not load IPO data: {e}")


@router.get("/api/ipo/chart")
def ipo_chart(symbol: str = Query(..., min_length=1, max_length=30, pattern=r"^[A-Za-z0-9&\-]+$"),
              listing_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"), issue_price: float = 0):
    key = f"ipochart:{symbol.upper()}:{listing_date}"

    def build():
        bars, live = _price_bars(symbol.upper(), date.fromisoformat(listing_date))
        bars = [b for b in bars if b["date"] >= listing_date]
        if not bars:
            return None
        cur = live or bars[-1]["close"]
        b0 = bars[0]
        st = {"current": round(cur, 2), "list_open": round(b0["open"], 2), "list_high": round(b0["high"], 2),
              "list_low": round(b0["low"], 2), "list_close": round(b0["close"], 2), "days": len(bars)}
        st.update(_range_stats(bars, cur))
        if issue_price:
            st["issue_price"] = issue_price
            st["return_pct"] = round((cur / issue_price - 1) * 100, 2)
        return {"symbol": symbol.upper(), "listing_date": listing_date, "stats": st,
                "bars": [[b["date"], round(b["open"], 2), round(b["high"], 2), round(b["low"], 2), round(b["close"], 2)] for b in bars]}

    try:
        data = _cached(key, 900, build, shared=False)
    except Exception as e:
        raise HTTPException(502, f"Could not load prices: {e}")
    if not data:
        raise HTTPException(404, "No price history for this symbol yet")
    return data


# ----------------------------------------------------------------------------- Mutual funds
MF_API = "https://api.mfapi.in/mf"

FUNDS = [
    ("Large Cap", ["Nippon India Large Cap Fund", "Nippon India Large Cap"]),
    ("Large Cap", [120586]),  # ICICI Prudential Large Cap (erstwhile Bluechip)
    ("Large Cap", ["Mirae Asset Large Cap Fund"]),
    ("Flexi Cap", ["Parag Parikh Flexi Cap Fund"]),
    ("Flexi Cap", ["HDFC Flexi Cap Fund"]),
    ("Flexi Cap", ["Kotak Flexicap Fund", "Kotak Flexi Cap"]),
    ("Mid Cap", [127042]),  # Motilal Oswal Midcap
    ("Mid Cap", ["HDFC Mid Cap Fund", "HDFC Mid-Cap Opportunities Fund"]),
    ("Mid Cap", [119775]),  # Kotak Mid Cap (erstwhile Emerging Equity)
    ("Small Cap", ["Nippon India Small Cap Fund"]),
    ("Small Cap", ["SBI Small Cap Fund"]),
    ("Small Cap", ["Quant Small Cap Fund"]),
    ("Index", ["UTI Nifty 50 Index Fund"]),
    ("Index", ["Motilal Oswal Nifty Midcap 150 Index Fund"]),
    ("Index", ["Navi Nifty 50 Index Fund", "HDFC Nifty 50 Index Fund"]),
    ("ELSS Tax Saver", ["Mirae Asset ELSS Tax Saver Fund"]),
    ("ELSS Tax Saver", ["Quant ELSS Tax Saver Fund"]),
    ("ELSS Tax Saver", ["DSP ELSS Tax Saver Fund"]),
    ("Hybrid", ["ICICI Prudential Balanced Advantage Fund"]),
    ("Hybrid", ["HDFC Balanced Advantage Fund"]),
    ("Hybrid", [119609]),  # SBI Aggressive Hybrid (erstwhile Equity Hybrid)
    ("Debt", ["HDFC Corporate Bond Fund"]),
    ("Debt", [120692]),  # ICICI Prudential Corporate Bond
    ("Debt", ["SBI Liquid Fund"]),
    ("Gold", ["SBI Gold Fund", "Nippon India Gold Savings Fund"]),
    ("Gold", ["HDFC Gold ETF Fund of Fund", "HDFC Gold Fund"]),
]


def _is_direct_growth(n):
    n = n.lower()
    return "direct" in n and "growth" in n and not re.search(r"idcw|dividend|bonus|payout|reinvest", n)


def mf_search(q, direct_growth=True):
    last = None
    for attempt in range(3):
        try:
            r = _http.get(f"{MF_API}/search", params={"q": q}, timeout=10)
            r.raise_for_status()
            items = r.json() or []
            break
        except Exception as e:  # mfapi.in rate-limits bursts: back off and retry
            last = e
            time.sleep(0.6 * (attempt + 1))
    else:
        raise last
    if direct_growth:
        items = [i for i in items if _is_direct_growth(i.get("schemeName", ""))]
    return items


_PASSIVE = {"index", "nifty", "etf", "fof", "sensex", "50", "150", "100"}
# words that change what kind of fund it is - an extra one means a different scheme ("Large & Mid Cap" is not "Large Cap")
_KIND = _PASSIVE | {"large", "mid", "midcap", "small", "smallcap", "multi", "flexi", "flexicap", "hybrid", "balanced", "advantage",
                    "equity", "value", "focused", "focus", "dividend", "yield", "contra", "momentum", "quality", "overseas", "global"}


def _resolve(names):
    """First query whose words ALL appear in a Direct-Growth scheme name; passive funds only when asked for."""
    for q in names:
        if isinstance(q, int):  # pinned AMFI scheme code (mfapi search misses some renamed schemes)
            return q, ""
        try:
            items = mf_search(q)
        except Exception:
            continue
        toks = set(_norm(q)) - {"fund"}
        ok = []
        for i in items:
            nt = set(_norm(i["schemeName"].replace("-", " ")))
            if toks <= nt and not ((nt - toks) & _KIND):
                ok.append(i)
        if ok:
            ok.sort(key=lambda i: len(i["schemeName"]))
            return ok[0]["schemeCode"], ok[0]["schemeName"]
    return None, None


def _resolve_all():
    with ThreadPoolExecutor(4) as ex:
        res = list(ex.map(lambda f: _resolve(f[1]), FUNDS))
    out, seen = [], set()
    for (cat, _), (c, n) in zip(FUNDS, res):
        if c and c not in seen:
            seen.add(c)
            out.append({"category": cat, "code": c, "scheme": n})
    return out


def _nav_history(code):
    """[(date, nav)] oldest first. Memory-cached for 6 h (too big for the shared cache)."""
    key = f"nav:{code}"
    now = time.time()
    with _mem_lock:
        hit = _mem.get(key)
    if hit and now - hit[0] < 6 * 3600:
        return hit[1]
    r = _http.get(f"{MF_API}/{code}", timeout=15)
    r.raise_for_status()
    js = r.json()
    rows = []
    for x in js.get("data") or []:
        try:
            rows.append((datetime.strptime(x["date"], "%d-%m-%Y").date(), float(x["nav"])))
        except (KeyError, ValueError):
            continue
    rows.sort()
    out = {"meta": js.get("meta") or {}, "navs": rows}
    with _mem_lock:
        _mem[key] = (now, out)
    return out


def _nav_on(navs, d):
    """NAV on d or the last trading day before it (binary search)."""
    lo, hi = 0, len(navs) - 1
    if hi < 0 or navs[0][0] > d:
        return None
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if navs[mid][0] <= d:
            lo = mid
        else:
            hi = mid - 1
    return navs[lo]


def _nav_from(navs, d):
    """First NAV on or after d."""
    lo, hi = 0, len(navs)
    while lo < hi:
        mid = (lo + hi) // 2
        if navs[mid][0] < d:
            lo = mid + 1
        else:
            hi = mid
    return navs[lo] if lo < len(navs) else None


def _add_months(d, n):
    y, m = divmod(d.month - 1 + n, 12)
    y += d.year
    m += 1
    import calendar
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def _cagr(navs, years):
    if not navs:
        return None
    end_d, end_v = navs[-1]
    start = _nav_on(navs, end_d - timedelta(days=round(365.25 * years)))
    if not start or (end_d - start[0]).days < 365 * years - 10:
        return None
    if years <= 1:
        return round((end_v / start[1] - 1) * 100, 2)
    return round(((end_v / start[1]) ** (1 / years) - 1) * 100, 2)


def xirr(flows):
    """flows: [(date, amount)] with investments negative. Annualised rate as a fraction."""
    if not flows or not any(a > 0 for _, a in flows) or not any(a < 0 for _, a in flows):
        return None
    d0 = flows[0][0]

    def npv(r):
        return sum(a / (1 + r) ** ((d - d0).days / 365.0) for d, a in flows)

    lo, hi = -0.99, 10.0
    f_lo, f_hi = npv(lo), npv(hi)
    if f_lo * f_hi > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        f_mid = npv(mid)
        if abs(f_mid) < 1e-7:
            break
        if f_lo * f_mid < 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2


def sip_sim(navs, amount, years=None, start=None, step_up_pct=0.0, day=None, max_n=None):
    """Monthly SIP on the first NAV date on/after the instalment day. Returns the result and a monthly series."""
    if not navs:
        return None
    end_d, end_v = navs[-1]
    first = navs[0][0]
    if start is None:
        start = _add_months(end_d, -12 * int(years))
    if max_n is None and years:
        max_n = 12 * int(years)
    if start < first:
        start = first
    day = day or start.day
    units = invested = 0.0
    flows, series = [], []
    k, amt = 0, float(amount)
    while True:
        due = _add_months(date(start.year, start.month, 1), k)
        due = due.replace(day=min(day, 28)) if day > 28 else due.replace(day=day)
        if due > end_d or (max_n and k >= max_n):
            break
        if k and k % 12 == 0 and step_up_pct:
            amt *= 1 + step_up_pct / 100
        pt = _nav_from(navs, due)
        if not pt or pt[0] > end_d:
            break
        units += amt / pt[1]
        invested += amt
        flows.append((pt[0], -amt))
        series.append({"date": pt[0].isoformat(), "invested": round(invested), "value": round(units * pt[1])})
        k += 1
    if not flows:
        return None
    value = units * end_v
    series.append({"date": end_d.isoformat(), "invested": round(invested), "value": round(value)})
    r = xirr(flows + [(end_d, value)])
    lump_nav = _nav_from(navs, flows[0][0])
    lump_value = invested / lump_nav[1] * end_v if lump_nav else None
    lump_years = max(0.01, (end_d - flows[0][0]).days / 365.25)
    return {
        "start": flows[0][0].isoformat(), "end": end_d.isoformat(), "instalments": len(flows),
        "invested": round(invested), "value": round(value), "gain": round(value - invested),
        "abs_return_pct": round((value / invested - 1) * 100, 2), "xirr_pct": round(r * 100, 2) if r is not None else None,
        "lumpsum": {"invested": round(invested), "value": round(lump_value) if lump_value else None,
                    "cagr_pct": round(((lump_value / invested) ** (1 / lump_years) - 1) * 100, 2) if lump_value else None},
        "series": series,
    }


def _nav_stats(navs):
    end_d, cur = navs[-1]
    yr = [x for x in navs if x[0] >= end_d - timedelta(days=365)]
    h52, l52 = max(yr, key=lambda x: x[1]), min(yr, key=lambda x: x[1])
    ath = max(navs, key=lambda x: x[1])
    return {"hi52": round(h52[1], 4), "hi52_date": h52[0].isoformat(), "lo52": round(l52[1], 4), "lo52_date": l52[0].isoformat(),
            "ath": round(ath[1], 4), "ath_date": ath[0].isoformat(), "dd_pct": round((cur / ath[1] - 1) * 100, 2),
            "from_hi52_pct": round((cur / h52[1] - 1) * 100, 2), "from_lo52_pct": round((cur / l52[1] - 1) * 100, 2)}


def _fund_summary(f):
    try:
        h = _nav_history(f["code"])
    except Exception:
        return None
    navs = h["navs"]
    if not navs:
        return None
    meta = h["meta"]
    out = dict(f)
    out.update({
        "name": re.sub(r"\s*-\s*Direct Plan\s*-?\s*Growth.*$|\s*-\s*Direct\s*-?\s*Growth.*$", "", meta.get("scheme_name") or f["scheme"], flags=re.I).strip(),
        "fund_house": meta.get("fund_house"), "scheme_category": meta.get("scheme_category"),
        "nav": navs[-1][1], "nav_date": navs[-1][0].isoformat(), "inception": navs[0][0].isoformat(),
        "r1y": _cagr(navs, 1), "r3y": _cagr(navs, 3), "r5y": _cagr(navs, 5), "r10y": _cagr(navs, 10),
    })
    out.update(_nav_stats(navs))
    prev = _nav_on(navs, navs[-1][0] - timedelta(days=1))
    if prev and prev[0] != navs[-1][0]:
        out["day_pct"] = round((navs[-1][1] / prev[1] - 1) * 100, 2)
    for y in (1, 3, 5):
        s = sip_sim(navs, 1000, years=y)
        if s and (navs[-1][0] - navs[0][0]).days >= 365 * y - 10:
            out[f"sip{y}y_xirr"] = s["xirr_pct"]
            out[f"sip{y}y_mult"] = round(s["value"] / s["invested"], 4)
    return out


def build_funds():
    codes = _cached("mf:codes:v3", 7 * 86400, _resolve_all)
    if not codes:
        raise RuntimeError("mfapi.in did not answer the scheme search")
    with ThreadPoolExecutor(8) as ex:
        rows = [r for r in ex.map(_fund_summary, codes) if r]
    return {"as_of": datetime.now(IST).isoformat(timespec="seconds"), "funds": rows,
            "categories": list(dict.fromkeys(f[0] for f in FUNDS))}


@router.get("/api/funds/list")
def funds_list(refresh: bool = False):
    key = "mf:list:v4"
    if refresh:
        with _mem_lock:
            _mem.pop(key, None)
        data = build_funds()
        shared_cache.set(key, data, 6 * 3600)
        return data
    try:
        return _cached(key, 6 * 3600, build_funds)
    except Exception as e:
        raise HTTPException(502, f"Could not load fund data: {e}")


@router.get("/api/funds/search")
def funds_search(q: str = Query(..., min_length=2, max_length=60), all_plans: bool = False):
    try:
        items = mf_search(q, direct_growth=not all_plans)
    except Exception as e:
        raise HTTPException(502, f"Fund search is unavailable: {e}")
    return {"items": [{"code": i["schemeCode"], "scheme": i["schemeName"]} for i in items[:25]]}


@router.get("/api/funds/nav")
def funds_nav(code: int, years: int = Query(0, ge=0, le=40)):
    """NAV series for the chart (years=0 -> since launch), thinned to ~500 points, plus range stats."""
    try:
        h = _nav_history(code)
    except Exception as e:
        raise HTTPException(502, f"Could not load NAV history: {e}")
    navs = h["navs"]
    if not navs:
        raise HTTPException(404, "No NAV history for this scheme")
    end = navs[-1][0]
    sel = [x for x in navs if x[0] >= end - timedelta(days=round(365.25 * years))] if years else navs
    step = max(1, math.ceil(len(sel) / 500))
    pts = sel[::step]
    if pts[-1] != sel[-1]:
        pts.append(sel[-1])
    lo_p, hi_p = min(sel, key=lambda x: x[1]), max(sel, key=lambda x: x[1])
    meta = h["meta"]
    st = _nav_stats(navs)
    st.update({"nav": navs[-1][1], "nav_date": end.isoformat(), "inception": navs[0][0].isoformat(),
               "range_high": round(hi_p[1], 4), "range_high_date": hi_p[0].isoformat(),
               "range_low": round(lo_p[1], 4), "range_low_date": lo_p[0].isoformat(),
               "range_return_pct": round((sel[-1][1] / sel[0][1] - 1) * 100, 2),
               "r1y": _cagr(navs, 1), "r3y": _cagr(navs, 3), "r5y": _cagr(navs, 5)})
    return {"code": code, "scheme": meta.get("scheme_name"), "fund_house": meta.get("fund_house"), "category": meta.get("scheme_category"),
            "years": years, "stats": st, "points": [[d.isoformat(), v] for d, v in pts]}


@router.get("/api/funds/sip")
def funds_sip(code: int, amount: float = Query(10000, ge=100, le=10_000_000), years: int = Query(5, ge=1, le=30),
              step_up: float = Query(0, ge=0, le=50), day: int = Query(5, ge=1, le=28)):
    try:
        h = _nav_history(code)
    except Exception as e:
        raise HTTPException(502, f"Could not load NAV history: {e}")
    navs = h["navs"]
    if not navs:
        raise HTTPException(404, "No NAV history for this scheme")
    end = navs[-1][0]
    start = _add_months(date(end.year, end.month, 1), -12 * years)
    if start.replace(day=day) <= _add_months(end, -12 * years):
        start = _add_months(start, 1)
    res = sip_sim(navs, amount, start=start, step_up_pct=step_up, day=day, max_n=12 * years)
    if not res:
        raise HTTPException(404, "Not enough history for this period")
    meta = h["meta"]
    res.update({"code": code, "scheme": meta.get("scheme_name"), "fund_house": meta.get("fund_house"),
                "category": meta.get("scheme_category"), "amount": amount, "years": years, "step_up": step_up,
                "requested_start": start.isoformat(), "inception": navs[0][0].isoformat(),
                "short_history": navs[0][0] > start})
    # thin the series to at most ~120 points for the chart
    s = res["series"]
    if len(s) > 121:
        step = math.ceil(len(s) / 120)
        res["series"] = s[::step] + ([s[-1]] if (len(s) - 1) % step else [])
    return res
