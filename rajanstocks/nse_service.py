import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date as date_cls
from datetime import datetime, timedelta, timezone

import requests

from common import normalize_expiry, normalize_strike
from data_store import INDEX_SYMBOLS, store
from upstox_service import UpstoxService

IST = timezone(timedelta(hours=5, minutes=30))

# Curated top NSE F&O stock symbols — used when no bhavcopy is loaded
TOP_FO_STOCKS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "ITC",
    "SBIN", "BHARTIARTL", "KOTAKBANK", "LT", "AXISBANK", "BAJFINANCE",
    "MARUTI", "SUNPHARMA", "TITAN", "WIPRO", "HCLTECH", "ASIANPAINT",
    "ADANIPORTS", "POWERGRID", "NTPC", "ONGC", "TMPV",
    "BAJAJFINSV", "TECHM", "DIVISLAB", "DRREDDY", "GRASIM", "CIPLA",
    "EICHERMOT", "HEROMOTOCO", "HINDALCO", "INDUSINDBK", "NESTLEIND",
    "TRENT", "ETERNAL", "BEL", "APOLLOHOSP", "SHRIRAMFIN", "JSWSTEEL",
]

BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/option-chain",
}


def _to_nse_expiry_param(iso_date):
    return datetime.strptime(iso_date, "%Y-%m-%d").strftime("%d-%b-%Y")


class OHLCTracker:
    """NSE's live option-chain feed only exposes LTP/OI per strike, not
    open/high/low. This derives a running intraday open/high/low from the
    LTPs observed across successive polls, reset whenever the trade date
    changes."""

    def __init__(self):
        self._day = None
        self._data = {}
        self._lock = threading.Lock()

    def update(self, identifier, ltp, trade_date):
        if ltp is None:
            return self._data.get(identifier)
        with self._lock:
            if trade_date != self._day:
                self._day = trade_date
                self._data = {}
            rec = self._data.get(identifier)
            if rec is None:
                rec = {"open": ltp, "high": ltp, "low": ltp}
                self._data[identifier] = rec
            else:
                if ltp > rec["high"]:
                    rec["high"] = ltp
                if ltp < rec["low"]:
                    rec["low"] = ltp
            return dict(rec)


class NSEService:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(BASE_HEADERS)
        self._cookie_ts = 0.0
        self._cookie_ttl = 240
        self._cookie_lock = threading.Lock()
        self.ohlc = OHLCTracker()
        self.upstox = UpstoxService()

    def refresh_cookies(self, force=False):
        with self._cookie_lock:
            if not force and (time.time() - self._cookie_ts) < self._cookie_ttl:
                return
            self.session.get("https://www.nseindia.com/", timeout=10)
            self.session.get("https://www.nseindia.com/option-chain", timeout=10)
            self._cookie_ts = time.time()

    def _get_json(self, url, params=None):
        self.refresh_cookies()
        resp = self.session.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            self.refresh_cookies(force=True)
            resp = self.session.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def get_market_status(self):
        try:
            data = self._get_json("https://www.nseindia.com/api/marketStatus")
            for m in data.get("marketState", []):
                if m.get("market") == "Capital Market":
                    is_open = str(m.get("marketStatus", "")).strip().lower() == "open"
                    return {
                        "marketStatus": "Open" if is_open else "Closed",
                        "tradeDate": (m.get("tradeDate") or "").strip(),
                    }
        except Exception:
            pass
        now = datetime.now(IST)
        minutes = now.hour * 60 + now.minute
        is_open = __import__("nse_calendar").is_trading_day(now.date()) and 9 * 60 + 15 <= minutes <= 15 * 60 + 30
        return {
            "marketStatus": "Open" if is_open else "Closed",
            "tradeDate": now.strftime("%d-%b-%Y"),
        }

    def fetch_option_chain(self, symbol, expiry_param=None):
        """Fetch NSE option chain. If expiry_param is None, NSE uses the nearest expiry."""
        symbol = symbol.upper()
        chain_type = "Indices" if symbol in INDEX_SYMBOLS else "Equities"
        url = "https://www.nseindia.com/api/option-chain-v3"
        params = {"symbol": symbol, "type": chain_type}
        if expiry_param:
            params["expiry"] = expiry_param
        return self._get_json(url, params=params)

    def get_all_indices(self):
        raw = self._get_json("https://www.nseindia.com/api/allIndices")
        return {row["index"]: row for row in raw.get("data", [])}

    def _resolve_nearest_expiry(self, symbol):
        """Return (nearest_iso, prefetched_raw_or_None).

        1. Check bhavcopy for upcoming expiries (fast, no network).
        2. If not found, call NSE without expiry (avoids a second call since
           we can reuse the response data for the chain itself).
        """
        today_iso = date_cls.today().isoformat()

        # Try bhavcopy — only accept upcoming expiries (past ones cause NSE to reject)
        if store.today_rows:
            candidates = sorted({
                r["expiry"] for r in store.today_rows
                if r["symbol"] == symbol and r["expiry"]
            })
            upcoming = [e for e in candidates if e >= today_iso]
            if upcoming:
                return upcoming[0], None  # caller fetches chain data

        # Fall back: call NSE without expiry, it returns the nearest expiry's chain
        raw = self.fetch_option_chain(symbol)
        expiry_dates = raw.get("records", {}).get("expiryDates", [])
        nearest_iso = None
        for ed in expiry_dates:
            try:
                ed_iso = datetime.strptime(ed, "%d-%b-%Y").strftime("%Y-%m-%d")
                if ed_iso >= today_iso:
                    nearest_iso = ed_iso
                    break
            except ValueError:
                continue
        return nearest_iso, raw  # raw already fetched — reuse it, no second call needed

    def _upstox_live_records(self, symbol, expiry_override=None):
        """Option-chain rows from Upstox (works from cloud hosts where NSE blocks us)."""
        chain = self.upstox.fetch_option_chain(symbol, expiry_override)
        is_index = symbol in INDEX_SYMBOLS
        out = []
        for r in chain["rows"]:
            oi, chg = r.get("oi"), r.get("oiChgRaw") or 0.0
            prev_oi = (oi - chg) if oi is not None else None
            out.append({
                "symbol": symbol,
                "isIndex": is_index,
                "expiry": r["expiry"],
                "strike": normalize_strike(r["strike"]),
                "type": r["type"],
                "open": r.get("open") or None,
                "high": r.get("high") or None,
                "low": r.get("low") or None,
                "close": r.get("close"),
                "prevClose": r.get("prevClose"),
                "spot": r.get("spot"),
                "oi": oi,
                "changeOi": chg,
                "pChangeOi": (chg / prev_oi * 100) if prev_oi else None,
                "volume": r.get("vol"),
            })
        return out, datetime.now(IST).strftime("%d-%b-%Y")

    def get_live_records(self, symbol, expiry_override=None):
        symbol = symbol.upper()

        if self.upstox.is_configured():
            try:
                return self._upstox_live_records(symbol, expiry_override)
            except Exception as exc:
                print(f"[Upstox] falling back to NSE for {symbol}: {exc}")

        if expiry_override:
            nearest_iso = expiry_override
            raw = self.fetch_option_chain(symbol, _to_nse_expiry_param(nearest_iso))
        else:
            nearest_iso, raw = self._resolve_nearest_expiry(symbol)
            if not nearest_iso:
                raise RuntimeError(
                    f"No upcoming expiry found for {symbol}. "
                    "NSE option chain may be unavailable for this symbol."
                )
            if raw is None:
                # Got expiry from bhavcopy — fetch the chain for that specific expiry
                raw = self.fetch_option_chain(symbol, _to_nse_expiry_param(nearest_iso))

        records_block = raw.get("records", {})
        underlying_value = records_block.get("underlyingValue")
        trade_date = (records_block.get("timestamp") or "").split(" ")[0]
        is_index = symbol in INDEX_SYMBOLS

        out = []
        for row in records_block.get("data", []):
            expiry = normalize_expiry(row.get("expiryDates")) or nearest_iso
            strike = normalize_strike(row.get("strikePrice"))
            for opt_type in ("CE", "PE"):
                leg = row.get(opt_type)
                if not leg:
                    continue
                identifier = leg.get("identifier") or f"{symbol}{expiry}{strike}{opt_type}"
                ltp = leg.get("lastPrice")
                ohlc = self.ohlc.update(identifier, ltp, trade_date)
                out.append({
                    "symbol": symbol,
                    "isIndex": is_index,
                    "expiry": expiry,
                    "strike": strike,
                    "type": opt_type,
                    "open": ohlc["open"] if ohlc else None,
                    "high": ohlc["high"] if ohlc else None,
                    "low": ohlc["low"] if ohlc else None,
                    "close": ltp,
                    "spot": underlying_value,
                    "oi": leg.get("openInterest"),
                    "changeOi": leg.get("changeinOpenInterest"),
                    "pChangeOi": leg.get("pchangeinOpenInterest"),
                    "volume": leg.get("totalTradedVolume"),
                })
        return out, trade_date

    def _fetch_symbol_records(self, symbol):
        """Fetch live records for one symbol. Returns (symbol, records, trade_date, error)."""
        try:
            records, td = self.get_live_records(symbol)
            return symbol, records, td, None
        except Exception as exc:
            return symbol, [], "", str(exc)

    def scan_live_all(self, inst_idx=True, inst_stk=True, sym_filter="__ALL__", max_stocks=40):
        """Fetch live NSE option chains for multiple symbols in parallel.

        Returns (all_records, trade_date, errors_list).
        """
        symbols = []
        if inst_idx:
            symbols.extend(sorted(INDEX_SYMBOLS))
        if inst_stk:
            # Use bhavcopy stock symbols if loaded (fuller list), else TOP_FO_STOCKS
            if store.today_rows:
                stock_syms = sorted({r["symbol"] for r in store.today_rows if not r["isIndex"]})
            else:
                stock_syms = list(TOP_FO_STOCKS)
            symbols.extend(stock_syms[:max_stocks])

        # Apply symbol filter
        if sym_filter and sym_filter not in ("__ALL__", ""):
            sym_up = sym_filter.upper()
            symbols = [s for s in symbols if s == sym_up]

        if not symbols:
            return [], "", ["No symbols selected — check Instrument type filter"]

        all_records = []
        trade_date = ""
        errors = []

        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {executor.submit(self._fetch_symbol_records, sym): sym for sym in symbols}
            for future in as_completed(futures):
                sym, records, td, err = future.result()
                if err:
                    errors.append(f"{sym}: {err}")
                else:
                    all_records.extend(records)
                    if td:
                        trade_date = td

        return all_records, trade_date, errors


nse_service = NSEService()
