"""NSE trading holidays (equity + F&O), checked against the exchange list for 2026 on 20 Oct 2026.
One place for every module: market-open checks, the auto trader, God's Eye and the Vedic report."""
from datetime import date, datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
HOLIDAYS = {
    "2026-01-26": "Republic Day", "2026-03-03": "Holi", "2026-03-26": "Shri Ram Navami",
    "2026-03-31": "Shri Mahavir Jayanti", "2026-04-03": "Good Friday", "2026-04-14": "Dr. Baba Saheb Ambedkar Jayanti",
    "2026-05-01": "Maharashtra Day", "2026-05-28": "Bakri Id", "2026-06-26": "Muharram",
    "2026-09-14": "Ganesh Chaturthi", "2026-10-02": "Mahatma Gandhi Jayanti", "2026-10-20": "Dussehra",
    "2026-11-10": "Diwali Balipratipada", "2026-11-24": "Prakash Gurpurb Sri Guru Nanak Dev", "2026-12-25": "Christmas",
}


def holiday(d=None):
    d = d or datetime.now(IST).date()
    return HOLIDAYS.get(d.isoformat() if isinstance(d, date) else str(d))


def is_trading_day(d=None):
    d = d or datetime.now(IST).date()
    return d.weekday() < 5 and not holiday(d)


def session_open(now=None):
    n = (now or datetime.now(IST)).astimezone(IST)
    mins = n.hour * 60 + n.minute
    return is_trading_day(n.date()) and 9 * 60 + 15 <= mins <= 15 * 60 + 30
