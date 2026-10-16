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


def parse_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def parse_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def record_key(record):
    return (record["symbol"], record["expiry"], record["strike"], record["type"])
