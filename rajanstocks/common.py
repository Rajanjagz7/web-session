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
REMOVED_TRADES_UNTIL = "2026-10-25"            # untimed trades dated on/before this day
REMOVED_TRADES_BEFORE = "2026-10-26T13:30:00+05:30"   # the removal was requested at ~13:26 IST; anything opened after is real


def is_removed_trade(t):
    """True for the explicitly removed trades (number 27 / 1004 / 1009, e.g. A-1023-27-W, S-20261023-27).
    Bounded by date so a future trade that happens to get one of those numbers is never hidden."""
    import re
    tid = str(t.get("id", ""))
    nums = re.findall(r"\d+", tid)
    if tid not in REMOVED_TRADE_NUMBERS and not (nums and nums[-1] in REMOVED_TRADE_NUMBERS):
        return False
    m = re.search(r"(?<!\d)(20\d{2})-?(\d{2})-?(\d{2})(?!\d)", tid)
    ts = str(t.get("openedAt") or t.get("at") or "")
    if ts:
        return ts < REMOVED_TRADES_BEFORE                  # same +05:30 offset, so ISO strings compare chronologically
    day = str(t.get("date") or "") or (f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else "")
    return not day or day <= REMOVED_TRADES_UNTIL


FRESH_START = "2026-10-28T09:00:00+05:30"   # from 28 Oct 2026 the paper books start at zero: every trade created before this instant is void
FRESH_START_DAY = "2026-10-27"
FRESH_START_FROM = "2026-10-27T21:00:00+05:30"   # the rule only acts from this instant (the request time), never on earlier clocks


def fresh_start_active(now):
    return now.isoformat() >= FRESH_START_FROM


def before_fresh_start(t):
    """True for a paper trade created before the 28 Oct 2026 fresh start (anything opened from tomorrow's session on is kept)."""
    ts = str(t.get("openedAt") or t.get("at") or "")
    if ts:
        return ts < FRESH_START                            # every timestamp is IST (+05:30), so ISO strings compare chronologically
    day = str(t.get("date") or "")
    return bool(day) and day <= FRESH_START_DAY
