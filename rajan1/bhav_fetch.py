import io
import zipfile
from datetime import date, timedelta

from data_store import WRITE_DIR
import os

ARCHIVE_URL = "https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_{date}_F_0000.csv.zip"
MAX_LOOKBACK_DAYS = 8


def _download_one(nse_service, day):
    date_str = day.strftime("%Y%m%d")
    url = ARCHIVE_URL.format(date=date_str)
    nse_service.refresh_cookies()
    resp = nse_service.session.get(url, timeout=15)
    if resp.status_code != 200 or not resp.content[:2] == b"PK":
        return None

    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        names = zf.namelist()
        if not names:
            return None
        text = zf.read(names[0]).decode("utf-8-sig")

    out_path = os.path.join(WRITE_DIR, f"BhavCopy_NSE_FO_0_0_0_{date_str}_F_0000.csv")
    os.makedirs(WRITE_DIR, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return out_path, date_str


def fetch_latest_bhavcopy(nse_service):
    today = date.today()
    last_error = None
    for offset in range(MAX_LOOKBACK_DAYS):
        day = today - timedelta(days=offset)
        try:
            result = _download_one(nse_service, day)
        except Exception as exc:
            last_error = str(exc)
            result = None
        if result:
            return result
    raise RuntimeError(
        f"No bhavcopy found on NSE archives in the last {MAX_LOOKBACK_DAYS} days."
        + (f" Last error: {last_error}" if last_error else "")
    )
