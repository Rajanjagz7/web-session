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
