from datetime import datetime

_EXPIRY_FORMATS = ("%Y-%m-%d", "%d-%b-%Y", "%d-%m-%Y")


def normalize_expiry(value):
    if not value:
        return None
    value = str(value).strip()
    for fmt in _EXPIRY_FORMATS:
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return value


def normalize_strike(value):
    if value is None or value == "":
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return int(f) if f == int(f) else round(f, 2)


def to_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def record_key(record):
    return (record["symbol"], record["expiry"], record["strike"], record["type"])


REMOVED_TRADE_NUMBERS = ("27", "1004", "1009")
REMOVED_TRADES_UNTIL = "2026-10-26"            # the removed trades are from on/before this day; later trades reusing a number are real


def is_removed_trade(t):
    """True for the explicitly removed trades (number 27 / 1004 / 1009, e.g. A-1023-27-W, S-20261023-27).
    Bounded by date so a future trade that happens to get one of those numbers is never hidden."""
    import re
    tid = str(t.get("id", ""))
    nums = re.findall(r"\d+", tid)
    if tid not in REMOVED_TRADE_NUMBERS and not (nums and nums[-1] in REMOVED_TRADE_NUMBERS):
        return False
    m = re.search(r"(?<!\d)(20\d{2})-?(\d{2})-?(\d{2})(?!\d)", tid)
    day = str(t.get("date") or "") or (f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else "")
    return not day or day <= REMOVED_TRADES_UNTIL
