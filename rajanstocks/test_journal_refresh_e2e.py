"""Journal (28 Oct code + 29 Oct additions): the Today card says how old the option prices are and has a Refresh button that reads the status at once."""
from datetime import datetime, timedelta

from test_journal_exit_e2e import (IST, OPT, World, browser, open_journal, pw, server)  # noqa: F401


def stamp(sec_ago):
    return (datetime.now(IST) - timedelta(seconds=sec_ago)).strftime("%Y-%m-%dT%H:%M:%S.%f+05:30")


class W(World):
    def __init__(self, age):
        super().__init__(opens=[dict(OPT, lastAt=stamp(age))])
        self.status_calls = 0

    def handle(self, route):
        if "/api/auto/status" in route.request.url:
            self.status_calls += 1
            self.opens[0]["lastAt"] = stamp(self.fresh) if getattr(self, "fresh", None) is not None else self.opens[0]["lastAt"]
        return super().handle(route)


def test_card_shows_the_age_of_the_prices_and_refresh_reads_again(server, browser):
    w = W(45)
    w.live["ok"] = False                                                                       # the quote feed is down: the card falls back to the age of the server's price
    c, pg, errs = open_journal(browser, w, tab="portfolio")
    pg.evaluate("MKT.open = true; JV.render()")                                              # the test clock may be outside market hours
    pg.wait_for_selector("#jvLiveB", timeout=15000)
    assert "prices" in pg.inner_text("#jvLiveB") and "old" in pg.inner_text("#jvLiveB")        # 45 s: red "prices 4Xs old"
    before = w.status_calls
    w.fresh = 1                                                                               # the server now answers with a price seen a second ago
    pg.click("[data-jv=refreshnow]")
    pg.wait_for_function("document.getElementById('jvLiveB') && document.getElementById('jvLiveB').innerText.includes('live')", timeout=15000)
    assert w.status_calls > before and not errs
    c.close()


def _num(txt):
    import re
    m = re.search(r"([+\-−])?₹\s*([\d,]+(?:\.\d+)?)", txt)
    v = float(m.group(2).replace(",", ""))
    return -v if m.group(1) in ("-", "−") else v


def test_header_chip_equals_the_today_card_and_follows_live_prices_on_other_screens(server, browser):
    w = World()
    w.set_price("A-1", 120.0)
    c, pg, errs = open_journal(browser, w, tab="portfolio")
    pg.evaluate("MKT.open = true; JV.render()")
    pg.wait_for_selector("#jvToday")
    pg.wait_for_function("document.getElementById('jvLiveB') && document.getElementById('jvLiveB').innerText.includes('live')", timeout=15000)
    card = _num(pg.inner_text("#jvToday .jv-hero-big"))
    pg.evaluate("renderPfChip()")
    assert abs(_num(pg.inner_text("#pfChip")) - card) < 1.0                           # the same figure in the header and on the card
    pg.evaluate("go('picks')")                                                         # another screen: the Journal is not on show any more
    w.set_price("A-1", 80.0)                                                           # the option falls 40 points
    pg.wait_for_function("(old) => { const t = document.getElementById('pfChip').innerText; return t && t !== old }", arg=pg.inner_text("#pfChip"), timeout=20000)
    chip = _num(pg.inner_text("#pfChip"))
    assert chip < card - 1000 and not errs                                             # 2 lots x 75 x 40 = about Rs 6,000 down, without opening the Journal
    c.close()
