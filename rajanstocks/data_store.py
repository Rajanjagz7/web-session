import csv
import glob
import os

from common import normalize_expiry, normalize_strike, to_float, record_key

# Bundled, read-only baseline (ships with the deploy — always present, even on
# Vercel's read-only filesystem). WRITE_DIR is where freshly downloaded/
# uploaded bhavcopy files get saved; on a normal server this is the same
# folder, but on Vercel set BHAV_CACHE_WRITE_DIR to a /tmp path since only
# /tmp is writable there. Files in either directory are picked up on reload.
DATA_DIR = os.path.join(os.path.dirname(__file__), "data_cache")
WRITE_DIR = os.environ.get("BHAV_CACHE_WRITE_DIR", DATA_DIR)
INDEX_SYMBOLS = {"NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "NIFTYNXT50"}


def _rows_from_reader(reader):
    rows = []
    for row in reader:
        opt_type = (row.get("OptnTp") or "").strip()
        if opt_type not in ("CE", "PE"):
            continue
        symbol = (row.get("TckrSymb") or "").strip()
        oi = to_float(row.get("OpnIntrst"))
        change_oi = to_float(row.get("ChngInOpnIntrst"))
        rows.append({
            "symbol": symbol,
            "isIndex": symbol in INDEX_SYMBOLS or (row.get("FinInstrmTp") or "").strip() == "IDO",
            "expiry": normalize_expiry(row.get("XpryDt")),
            "strike": normalize_strike(row.get("StrkPric")),
            "type": opt_type,
            "open": to_float(row.get("OpnPric")),
            "high": to_float(row.get("HghPric")),
            "low": to_float(row.get("LwPric")),
            "close": to_float(row.get("ClsPric")),
            "prevCloseFile": to_float(row.get("PrvsClsgPric")),
            "spot": to_float(row.get("UndrlygPric")),
            "oi": oi,
            "changeOi": change_oi,
            "volume": to_float(row.get("TtlTradgVol")),
            "tradeDate": (row.get("TradDt") or "").strip(),
        })
    return rows


def parse_bhavcopy_file(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return _rows_from_reader(csv.DictReader(fh))


def build_lookup(rows):
    lookup = {}
    for r in rows:
        lookup[record_key(r)] = r
    return lookup


def bhav_row_to_record(row, prev_lookup):
    prev_row = prev_lookup.get(record_key(row))
    if prev_row is not None:
        prev_close = prev_row["close"]
        prev_oi = prev_row["oi"]
    else:
        prev_close = row["prevCloseFile"]
        prev_oi = None
        if row["oi"] is not None and row["changeOi"] is not None:
            prev_oi = row["oi"] - row["changeOi"]

    oi_pct = None
    if prev_oi:
        oi_pct = (row["oi"] - prev_oi) / prev_oi * 100

    return {
        "symbol": row["symbol"],
        "isIndex": row["isIndex"],
        "expiry": row["expiry"],
        "strike": row["strike"],
        "type": row["type"],
        "open": row["open"],
        "high": row["high"],
        "low": row["low"],
        "close": row["close"],
        "prevCloseUsed": prev_close,
        "spot": row["spot"],
        "oi": row["oi"],
        "oiPct": oi_pct,
        "volume": row["volume"],
    }


class BhavStore:
    def __init__(self):
        self.today_rows = []
        self.today_date = None
        self.prev_rows = []
        self.prev_date = None
        self.prev_lookup = {}
        self.reload()

    def _cache_files(self):
        paths = set(glob.glob(os.path.join(DATA_DIR, "BhavCopy_NSE_FO_*.csv")))
        paths |= set(glob.glob(os.path.join(WRITE_DIR, "BhavCopy_NSE_FO_*.csv")))
        return sorted(paths)

    def _date_from_filename(self, path):
        name = os.path.basename(path)
        for part in name.split("_"):
            if len(part) == 8 and part.isdigit():
                return part
        return None

    def reload(self):
        dated = [(self._date_from_filename(f), f) for f in self._cache_files()]
        dated = sorted((d for d in dated if d[0]), key=lambda x: x[0])
        if not dated:
            return
        today_date, today_path = dated[-1]
        self.set_today(parse_bhavcopy_file(today_path), today_date)
        if len(dated) >= 2:
            prev_date, prev_path = dated[-2]
            self.set_prev(parse_bhavcopy_file(prev_path), prev_date)

    def set_today(self, rows, trade_date):
        self.today_rows = rows
        self.today_date = trade_date

    def set_prev(self, rows, trade_date):
        self.prev_rows = rows
        self.prev_date = trade_date
        self.prev_lookup = build_lookup(rows)

    def today_lookup(self):
        return build_lookup(self.today_rows)

    def symbols(self):
        return sorted({r["symbol"] for r in self.today_rows})

    def is_loaded(self):
        return bool(self.today_rows)

    def today_records(self):
        return [bhav_row_to_record(r, self.prev_lookup) for r in self.today_rows]


store = BhavStore()
