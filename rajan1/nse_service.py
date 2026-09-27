import threading
import time
from datetime import date as date_cls
from datetime import datetime, timedelta, timezone

import requests

from common import normalize_expiry, normalize_strike
from data_store import INDEX_SYMBOLS, store

IST = timezone(timedelta(hours=5, minutes=30))

BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/option-chain",
}


def _nearest_expiry_for(symbol):
    """NSE's live option-chain endpoint requires an exact expiry string per
    request rather than defaulting to the nearest one, so it's resolved from
    the bhavcopy already cached on disk instead of a separate lookup call."""
    today_iso = date_cls.today().isoformat()
    candidates = sorted({
        r["expiry"] for r in store.today_rows
        if r["symbol"] == symbol and r["expiry"]
    })
    upcoming = [e for e in candidates if e >= today_iso]
    if upcoming:
        return upcoming[0]
    return candidates[-1] if candidates else None


def _to_nse_expiry_param(iso_date):
    return datetime.strptime(iso_date, "%Y-%m-%d").strftime("%d-%b-%Y")


class OHLCTracker:
    """NSE's live option-chain feed only exposes LTP/OI per strike, not
    open/high/low. This derives a running intraday open/high/low from the
    LTPs observed across successive polls, reset whenever the trade date
    changes. Accuracy improves the longer the server has been polling that
    contract during the session, and 'open' reflects the first price seen by
    this process rather than the official 9:15 open."""

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
        is_open = now.weekday() < 5 and 9 * 60 + 15 <= minutes <= 15 * 60 + 30
        return {
            "marketStatus": "Open" if is_open else "Closed",
            "tradeDate": now.strftime("%d-%b-%Y"),
        }

    def fetch_option_chain(self, symbol, expiry_param):
        symbol = symbol.upper()
        chain_type = "Indices" if symbol in INDEX_SYMBOLS else "Equities"
        url = "https://www.nseindia.com/api/option-chain-v3"
        return self._get_json(
            url, params={"symbol": symbol, "type": chain_type, "expiry": expiry_param}
        )

    def get_all_indices(self):
        raw = self._get_json("https://www.nseindia.com/api/allIndices")
        return {row["index"]: row for row in raw.get("data", [])}

    def get_live_records(self, symbol, expiry_override=None):
        symbol = symbol.upper()
        nearest_iso = expiry_override or _nearest_expiry_for(symbol)
        if not nearest_iso:
            raise RuntimeError(
                f"No expiry data available for {symbol} — load a bhavcopy first "
                "so the nearest expiry can be resolved"
            )
        expiry_param = _to_nse_expiry_param(nearest_iso)

        raw = self.fetch_option_chain(symbol, expiry_param)
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


nse_service = NSEService()
