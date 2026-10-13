import os
import math
import time
from datetime import datetime, date, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
from urllib.parse import quote
import requests

def _load_env_file():
    candidates = [
        os.path.join(os.path.dirname(__file__), "..", ".env"),
        os.path.join(os.path.dirname(__file__), "..", ".env.local"),
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.getcwd(), ".env.local"),
        ".env",
        ".env.local"
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("'").strip('"')
                            if k not in os.environ:
                                os.environ[k] = v
            except Exception:
                pass

_load_env_file()



# ---- global request budget (Upstox allows ~50/s, 500/min, 2000/30 min per app) ----
import collections as _collections
import threading as _threading

_RL_LOCK = _threading.Lock()
_BG = _threading.local()      # set while a background job (scan / screen) runs on this thread
_RL_TIMES = _collections.deque()


class UpstoxRateLimited(RuntimeError):
    """Upstox said 429 (or our own 30-minute budget is spent). Callers should serve cached prices."""


_BLOCK_UNTIL = 0.0
_RL_LONG = _collections.deque()      # call times in the last 30 minutes


def _throttle(max_wait=8.0):
    """Blocks briefly instead of letting a burst trip Upstox's 429 limit."""
    start = time.time()
    if time.time() < _BLOCK_UNTIL:
        raise UpstoxRateLimited("Upstox is rate-limiting this app; serving the last known prices")
    while True:
        with _RL_LOCK:
            now = time.time()
            while _RL_LONG and now - _RL_LONG[0] > 1800:
                _RL_LONG.popleft()
            if len(_RL_LONG) >= 1700:
                raise UpstoxRateLimited("Upstox 30-minute request budget is used up; serving the last known prices")
            while _RL_TIMES and now - _RL_TIMES[0] > 60:
                _RL_TIMES.popleft()
            last_second = sum(1 for t in _RL_TIMES if now - t < 1.0)
            limit = 300 if getattr(_BG, 'on', 0) > 0 else 455   # background jobs leave ~1/3 of the budget for charts
            if len(_RL_TIMES) < limit and last_second < 20:
                _RL_TIMES.append(now)
                _RL_LONG.append(now)
                return
            wait = 0.06 if last_second >= 20 else max(0.1, 60 - (now - _RL_TIMES[0]))
        if time.time() - start + wait > max_wait:
            raise RuntimeError("Upstox request budget is used up for this minute; retrying shortly")
        time.sleep(min(wait, 0.5))


class UpstoxService:
    """
    REST-only Upstox integration for the existing scanner.

    Uses:
      - Instrument Search / Option Contracts to resolve the underlying
      - Put/Call Option Chain for contracts + LTP/OI/volume
      - Full Market Quotes V3 for live OHLC/previous close

    This deliberately does not create a persistent WebSocket because the
    current deployment is Vercel serverless. The existing frontend polling
    interval therefore becomes the live refresh cadence.
    """

    BASE_V2 = "https://api.upstox.com/v2"
    BASE_V3 = "https://api.upstox.com/v3"

    INDEX_KEYS = {
        "NIFTY": "NSE_INDEX|Nifty 50",
        "NIFTY 50": "NSE_INDEX|Nifty 50",
        "BANKNIFTY": "NSE_INDEX|Nifty Bank",
        "NIFTY BANK": "NSE_INDEX|Nifty Bank",
        "FINNIFTY": "NSE_INDEX|Nifty Fin Service",
        "NIFTY FIN SERVICE": "NSE_INDEX|Nifty Fin Service",
        "MIDCPNIFTY": "NSE_INDEX|NIFTY MID SELECT",
        "NIFTY MIDCAP": "NSE_INDEX|NIFTY MID SELECT",
        "NIFTY MID SELECT": "NSE_INDEX|NIFTY MID SELECT",
        "NIFTYNXT50": "NSE_INDEX|Nifty Next 50",
        "SENSEX": "BSE_INDEX|SENSEX",
        "INDIA VIX": "NSE_INDEX|India VIX",
        "INDIAVIX": "NSE_INDEX|India VIX",
        "VIX": "NSE_INDEX|India VIX",
    }

    def __init__(self):
        self.session = requests.Session()
        self.cache = {}
        self.instrument_cache = {}
        self._fo = None

    def is_configured(self):
        return bool(os.getenv("UPSTOX_ACCESS_TOKEN"))

    def _headers(self):
        token = os.getenv("UPSTOX_ACCESS_TOKEN")
        if not token:
            raise RuntimeError("UPSTOX_ACCESS_TOKEN is not configured")
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        }

    def _get(self, url, params=None, timeout=7):
        response = None
        for attempt in range(3):
            _throttle()
            response = self.session.get(
                url,
                params=params,
                headers=self._headers(),
                timeout=timeout,
            )
            if response.status_code != 429:
                break
            global _BLOCK_UNTIL
            if attempt == 0:
                time.sleep(0.8)               # one short retry, then give up fast
                continue
            _BLOCK_UNTIL = time.time() + 25   # circuit breaker: stop hammering Upstox for a bit
            raise UpstoxRateLimited("Upstox HTTP 429: too many requests; serving the last known prices")
        if response.status_code >= 400:
            body = response.text[:1000]
            raise RuntimeError(
                f"Upstox API HTTP {response.status_code}: {body}"
            )
        payload = response.json()
        if payload.get("status") not in (None, "success"):
            raise RuntimeError(f"Upstox API error: {payload}")
        return payload

    def _resolve_underlying(self, symbol):
        symbol = symbol.upper().strip()
        if symbol in self.INDEX_KEYS:
            return self.INDEX_KEYS[symbol], True

        if symbol in self.instrument_cache:
            return self.instrument_cache[symbol], False

        # NSE F&O equity underlyings always use the NSE_EQ|SYMBOL key on Upstox.
        # The old instruments/search approach was fragile (timeout on Vercel, exact
        # underlying_symbol match failures) and added a round-trip per stock.
        # Upstox actually requires the ISIN-based key (NSE_EQ|INE002A01018), so
        # look it up in the public instrument master (loaded once per instance).
        eq_map = self._load_equity_keys()
        key = eq_map.get(symbol) or f"NSE_EQ|{symbol}"
        self.instrument_cache[symbol] = key
        return key, False

    def _load_equity_keys(self):
        if getattr(self, "_eq_keys", None):
            return self._eq_keys
        import gzip, json
        try:
            resp = self.session.get(
                "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz",
                timeout=20,
            )
            try:
                rows = json.loads(gzip.decompress(resp.content))
            except OSError:
                rows = resp.json()
            self._eq_keys = {
                x["trading_symbol"].upper(): x["instrument_key"]
                for x in rows
                if x.get("segment") == "NSE_EQ" and x.get("instrument_type") == "EQ"
            }
            # every underlying that has listed options (stock + index), with company names
            names = {x["trading_symbol"].upper(): x.get("name") for x in rows
                     if x.get("segment") == "NSE_EQ" and x.get("instrument_type") == "EQ"}
            stocks, indices, lots = {}, set(), {}
            for x in rows:
                if x.get("segment") != "NSE_FO" or x.get("instrument_type") not in ("CE", "PE"):
                    continue
                u = (x.get("underlying_symbol") or "").upper()
                if x.get("lot_size"):
                    lots[u] = int(x["lot_size"])
                if x.get("underlying_type") == "INDEX":
                    indices.add(u)
                elif u in names:
                    stocks[u] = names[u]
            self._fo = {"stocks": stocks, "indices": sorted(indices), "lots": lots}
        except Exception:
            self._eq_keys = {}
        return self._eq_keys

    @staticmethod
    def _normal_expiry(value):
        if not value:
            return None
        return str(value)[:10]

    @staticmethod
    def _guess_nearest_expiry(is_index=False):
        """Return the nearest NSE expiry date without an API call.
        - Index options: nearest upcoming Thursday (weekly expiry)
        - Stock options: last Thursday of current (or next) month
        This lets fetch_option_chain skip the _get_contracts round-trip
        for the common case, reducing 3 API calls to 2.
        """
        today = date.today()
        if is_index:
            days_ahead = (3 - today.weekday()) % 7 or 7  # 3=Thursday; skip if today
            return (today + timedelta(days=days_ahead)).isoformat()
        # Last Thursday of each upcoming month
        for months_ahead in range(0, 4):
            month = today.month + months_ahead
            year = today.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            if month == 12:
                last_day = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = date(year, month + 1, 1) - timedelta(days=1)
            offset = (last_day.weekday() - 3) % 7
            last_thu = last_day - timedelta(days=offset)
            if last_thu >= today:
                return last_thu.isoformat()
        return None

    def _get_contracts(self, underlying_key, expiry=None):
        params = {"instrument_key": underlying_key}
        if expiry:
            params["expiry_date"] = expiry
        payload = self._get(
            f"{self.BASE_V2}/option/contract",
            params=params,
        )
        return payload.get("data", [])

    def _resolve_expiry(self, contracts, requested):
        expiries = sorted({
            self._normal_expiry(x.get("expiry"))
            for x in contracts
            if self._normal_expiry(x.get("expiry"))
        })
        today = date.today().isoformat()
        future = [x for x in expiries if x >= today]
        if requested and requested in expiries:
            target = requested
        elif future:
            target = future[0]
        elif expiries:
            target = expiries[0]
        else:
            raise RuntimeError("Upstox returned no option expiry dates")
        return target, expiries

    def _full_quotes(self, instrument_keys):
        result = {}
        # Upstox limits one full-quote request to 500 instruments.
        for start in range(0, len(instrument_keys), 500):
            batch = instrument_keys[start:start + 500]
            try:
                payloads = [self._get(
                    f"{self.BASE_V3}/market-quote/quotes",
                    params={"instrument_key": ",".join(batch)},
                    timeout=15,
                )]
            except UpstoxRateLimited:
                raise
            except Exception as exc:
                # One invalid key (UDAPI1087) rejects the whole batch --
                # retry per key and skip the bad ones. Anything else is a real outage: report it.
                if "UDAPI1087" not in str(exc) and "HTTP 400" not in str(exc):
                    raise
                payloads = []
                for k in batch[:60]:
                    try:
                        payloads.append(self._get(
                            f"{self.BASE_V3}/market-quote/quotes",
                            params={"instrument_key": k},
                            timeout=15,
                        ))
                    except Exception:
                        continue
            for payload in payloads:
                for key, quote in (payload.get("data") or {}).items():
                    instrument_token = quote.get("instrument_token")
                    result[instrument_token or key] = quote
        return result

    @staticmethod
    def _num(value, default=0.0):
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    def fetch_option_chain(self, symbol="NIFTY", expiry=None):
        symbol = symbol.upper().strip()
        cache_key = f"{symbol}|{expiry or ''}"
        now = time.time()

        # Keep a very short cache so two simultaneous browser requests don't
        # duplicate expensive Upstox REST calls.
        cached = self.cache.get(cache_key)
        if cached and now - cached[0] < 3:
            return cached[1]

        underlying_key, is_index = self._resolve_underlying(symbol)

        # Fast path: skip _get_contracts (saves one round-trip) by guessing
        # the nearest NSE expiry locally. If the chain comes back empty,
        # fall back to the full _get_contracts → _resolve_expiry flow.
        guessed = expiry or self._guess_nearest_expiry(is_index)
        chain_rows = []
        expiry_dates = []
        target_expiry = guessed
        if guessed:
            try:
                fast_chain = self._get(
                    f"{self.BASE_V2}/option/chain",
                    params={"instrument_key": underlying_key, "expiry_date": guessed},
                )
                chain_rows = fast_chain.get("data", [])
                if chain_rows:
                    expiry_dates = sorted({
                        self._normal_expiry(item.get("expiry"))
                        for item in chain_rows
                        if self._normal_expiry(item.get("expiry"))
                    })
            except Exception:
                chain_rows = []

        if not chain_rows:
            # Guessed expiry failed — fetch contracts to find the real expiry.
            contracts = self._get_contracts(underlying_key)
            target_expiry, expiry_dates = self._resolve_expiry(contracts, expiry)
            chain = self._get(
                f"{self.BASE_V2}/option/chain",
                params={"instrument_key": underlying_key, "expiry_date": target_expiry},
            )
            chain_rows = chain.get("data", [])

        instrument_keys = []
        for item in chain_rows:
            for side in ("call_options", "put_options"):
                option = item.get(side) or {}
                key = option.get("instrument_key")
                if key:
                    instrument_keys.append(key)

        try:
            quotes = self._full_quotes(list(dict.fromkeys(instrument_keys)))
        except Exception as e:
            # Degraded data (no day high / low / open) silently breaks every scan, so fail loudly and let callers retry
            raise RuntimeError(f"Upstox quote batch failed for {symbol}: {e}")

        rows = []
        for item in chain_rows:
            strike = self._num(item.get("strike_price"))
            spot = self._num(item.get("underlying_spot_price"))

            for opt_type, field in (("CE", "call_options"), ("PE", "put_options")):
                option = item.get(field) or {}
                key = option.get("instrument_key")
                if not key:
                    continue

                market = option.get("market_data") or {}
                quote = quotes.get(key) or quotes.get(
                    option.get("instrument_token")
                ) or {}

                ohlc = quote.get("ohlc") or {}
                ltp = self._num(
                    quote.get("last_price"),
                    self._num(market.get("ltp")),
                )
                prev_close = self._num(
                    quote.get("prev_close_price"),
                    self._num(market.get("close_price")),
                )
                open_price = self._num(ohlc.get("open"))
                high_price = self._num(ohlc.get("high"))
                low_price = self._num(ohlc.get("low"))
                volume = self._num(
                    quote.get("volume"),
                    self._num(market.get("volume")),
                )
                oi = self._num(
                    quote.get("oi"),
                    self._num(market.get("oi")),
                )
                previous_oi = self._num(
                    quote.get("previous_oi"),
                    self._num(market.get("prev_oi")),
                )
                oi_change = oi - previous_oi if previous_oi else 0.0

                rows.append({
                    "symbol": symbol,
                    "instr": "Index" if is_index else "Stock",
                    "expiry": self._normal_expiry(item.get("expiry")) or target_expiry,
                    "strike": strike,
                    "type": opt_type,
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": ltp,
                    "prevClose": prev_close,
                    "spot": spot,
                    "oi": oi,
                    "oiChgRaw": oi_change,
                    "vol": volume,
                    "bid": self._num(market.get("bid_price")),
                    "ask": self._num(market.get("ask_price")),
                    "instrumentKey": key,
                    "source": "Upstox",
                    "lastTradeTime": quote.get("last_trade_time"),
                })

        if not rows:
            raise RuntimeError(
                f"Upstox returned no option-chain contracts for {symbol} {target_expiry}"
            )

        spot_val = 0.0
        for r in rows:
            if r.get("spot") and r["spot"] > 0:
                spot_val = r["spot"]
                break

        result = {
            "symbol": symbol,
            "spot": spot_val,
            "targetExpiry": target_expiry,
            "expiryDates": expiry_dates,
            "rows": rows,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "provider": "Upstox",
            "mode": "REST",
            "underlyingKey": underlying_key,
        }
        self.cache[cache_key] = (now, result)
        return result

    def _parse_candles(self, payload):
        """Upstox returns candles most-recent-first as
        [timestamp, open, high, low, close, volume, oi]; normalize to
        chronological order with named fields. No fabricated values --
        anything not returned by the API is simply absent here."""
        raw = (payload.get("data") or {}).get("candles") or []
        out = []
        for c in raw:
            out.append({
                "time": c[0],
                "open": self._num(c[1]),
                "high": self._num(c[2]),
                "low": self._num(c[3]),
                "close": self._num(c[4]),
                "volume": self._num(c[5]) if len(c) > 5 else 0.0,
                "oi": self._num(c[6]) if len(c) > 6 else 0.0,
            })
        out.reverse()
        return out

    def fetch_intraday_candles(self, instrument_key, unit="minutes", interval="5"):
        """Today's real intraday candles from Upstox's V3 intraday endpoint."""
        encoded_key = quote(instrument_key, safe="")
        url = f"{self.BASE_V3}/historical-candle/intraday/{encoded_key}/{unit}/{interval}"
        return self._parse_candles(self._get(url))

    def fetch_historical_candles(self, instrument_key, unit="minutes", interval="30", to_date=None, from_date=None):
        """Real OHLCV candles over a date range from Upstox's V3 historical-candle endpoint."""
        encoded_key = quote(instrument_key, safe="")
        url = f"{self.BASE_V3}/historical-candle/{encoded_key}/{unit}/{interval}/{to_date}/{from_date}"
        return self._parse_candles(self._get(url))

    # Verified directly against Upstox's live V3 API (not assumed from docs) --
    # it accepts any minute count here, not just a fixed preset list.
    ALLOWED_MINUTE_INTERVALS = {"1", "2", "3", "5", "10", "15", "30", "45", "60", "75", "125", "240"}

    def get_candles(self, instrument_key, timeframe="5minute"):
        """
        Real candle series for a chart -- no synthetic/estimated points.
        timeframe: "<N>minute" for any N in ALLOWED_MINUTE_INTERVALS, or "day".
        Intraday timeframes try today's live intraday candles first, then
        fall back to the most recent trading day's historical candles
        (markets closed / weekend) so the chart still shows something real
        rather than going blank.
        """
        if timeframe == "day":
            unit, interval = "days", "1"
        else:
            n = timeframe[:-6] if timeframe.endswith("minute") else timeframe
            interval = n if n in self.ALLOWED_MINUTE_INTERVALS else "5"
            unit = "minutes"

        if timeframe == "day":
            to_d = date.today().isoformat()
            from_d = (date.today() - timedelta(days=90)).isoformat()
            return self.fetch_historical_candles(instrument_key, unit, interval, to_d, from_d)

        try:
            candles = self.fetch_intraday_candles(instrument_key, unit, interval)
            if candles:
                return candles
        except Exception as e:
            print(f"[Upstox] intraday candle fetch failed for {instrument_key}: {e}")

        try:
            to_d = date.today().isoformat()
            from_d = (date.today() - timedelta(days=7)).isoformat()
            return self.fetch_historical_candles(instrument_key, unit, interval, to_d, from_d)
        except Exception as e:
            print(f"[Upstox] historical candle fallback failed for {instrument_key}: {e}")
            return []

    def get_all_indices_quotes(self):
        """
        Fetches real-time market quotes for all major indices:
        NIFTY, BANKNIFTY, SENSEX, INDIA VIX, FINNIFTY, MIDCPNIFTY.
        Cached for 3 seconds to avoid duplicate REST requests.
        """
        if not self.is_configured():
            return {}

        now = time.time()
        cached = self.cache.get("ALL_INDICES_QUOTES")
        if cached and now - cached[0] < 3:
            return cached[1]

        keys_map = {
            "NIFTY": "NSE_INDEX|Nifty 50",
            "BANKNIFTY": "NSE_INDEX|Nifty Bank",
            "SENSEX": "BSE_INDEX|SENSEX",
            "VIX": "NSE_INDEX|India VIX",
            "FINNIFTY": "NSE_INDEX|Nifty Fin Service",
            "MIDCPNIFTY": "NSE_INDEX|NIFTY MID SELECT",
        }

        try:
            url = f"{self.BASE_V2}/market-quote/quotes"
            params = {"instrument_key": ",".join(keys_map.values())}
            res = self._get(url, params=params, timeout=8)
            raw_data = res.get("data", {})

            quotes = {}
            for sym, ikey in keys_map.items():
                quote_obj = raw_data.get(ikey)
                if not quote_obj:
                    colon_key = ikey.replace("|", ":")
                    quote_obj = raw_data.get(colon_key)

                if quote_obj:
                    last = self._num(quote_obj.get("last_price"))
                    ohlc = quote_obj.get("ohlc") or {}
                    close = self._num(ohlc.get("close"), last)
                    change = self._num(quote_obj.get("net_change"))
                    if change == 0.0 and close > 0 and last > 0:
                        change = round(last - close, 2)
                    prev_close = last - change if last > 0 else close
                    pct = round((change / prev_close) * 100.0, 2) if prev_close > 0 else 0.0

                    quotes[sym] = {
                        "symbol": sym,
                        "last": last,
                        "change": change,
                        "pct": pct,
                        "open": self._num(ohlc.get("open")),
                        "high": self._num(ohlc.get("high")),
                        "low": self._num(ohlc.get("low")),
                        "close": close,
                        "prevClose": round(prev_close, 2),
                        "dataStatus": "live",
                        "timestamp": datetime.now(IST).isoformat(),
                    }

            self.cache["ALL_INDICES_QUOTES"] = (now, quotes)
            return quotes
        except Exception as e:
            print(f"[Upstox] get_all_indices_quotes error: {e}")
            return {}

    def health(self):
        if not self.is_configured():
            return {
                "configured": False,
                "provider": "Upstox",
                "mode": "REST",
            }
        try:
            key, is_index = self._resolve_underlying("NIFTY")
            return {
                "configured": True,
                "provider": "Upstox",
                "mode": "REST",
                "connected": True,
                "underlyingKey": key,
            }
        except Exception as exc:
            return {
                "configured": True,
                "provider": "Upstox",
                "mode": "REST",
                "connected": False,
                "error": str(exc),
            }


upstox_service = UpstoxService()


def _fo_universe(self):
    """{'stocks': {SYMBOL: company name}, 'indices': [...]} for everything with listed options."""
    self._load_equity_keys()
    return self._fo or {"stocks": {}, "indices": []}


UpstoxService.fo_universe = _fo_universe
