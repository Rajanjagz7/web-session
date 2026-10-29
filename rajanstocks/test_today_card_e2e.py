"""'Today's profit' must not flicker: the share trader's row showed the book's whole open loss since ENTRY (-16,667) for a moment, then today's move (-31)
once the per-trade list arrived; odd share ticks and older cached copies from another server instance must not move it either."""
import time

import pytest

from test_journal_exit_e2e import (BASE, TODAY, YDAY, World, browser, open_journal, pw, server, set_sym)  # noqa: F401

CARRIED = dict(id="S-9", sym="TCS", side="BUY", hz="positional", status="OPEN", entry=80.0, stop=70.0, t1=110.0, t2=120.0, qty=1000, last=100.0,
               openedAt=f"{YDAY}T09:30:00+05:30", holdSessions=1, net=0, R=0, costPctEff=0.1)


class StockWorld(World):
    """Stock-trader status with a book total (since entry, +20,000) that is NOT today's move; the main status can be slowed down."""
    def __init__(self, delay_auto=0.0, last_run="2026-10-29T09:25:00+05:30"):
        super().__init__(opens=[], stocks=[dict(CARRIED)])
        self.delay_auto, self.last_run, self.sb_calls = delay_auto, last_run, 0

    def handle(self, route):
        u = route.request.url
        if "/api/stockbot/status" in u:
            self.sb_calls += 1
            return route.fulfill(json={"open": self.stocks, "closed": [], "byHorizon": {"positional": {}}, "unrealised": 20000, "booked": 0, "used": 80000,
                                       "cash": 0, "equity": 0, "capital": 500000, "lastRun": self.last_run})
        return super().handle(route)


WATCH = ("window.__seen=[];addEventListener('DOMContentLoaded',()=>{new MutationObserver(()=>{const e=document.getElementById('jvToday');"
         "if(e)window.__seen.push(e.innerText.replace(/\\s+/g,' '))}).observe(document.documentElement,{childList:true,subtree:true,characterData:true})});")


def seen(pg):
    return pg.evaluate("window.__seen")


SLOW_STATUS = ("const _f=window.fetch;window.fetch=function(u,o){const r=_f.apply(this,arguments);"
               "return String(u).includes('/api/auto/status')?new Promise(ok=>setTimeout(()=>ok(r),3500)).then(x=>x):r};")


def test_today_card_never_shows_the_since_entry_total(server, browser):
    w = StockWorld()                               # the stock book arrives first, the per-trade list (main status) 3.5 s later
    c = browser.new_context(viewport={"width": 1000, "height": 900})
    c.add_init_script("window.rjMkt=function(){return true};" + WATCH + SLOW_STATUS)
    pg = c.new_page()
    pg.route("**/api/**", w.handle)
    pg.goto(BASE + "/#journal")
    pg.wait_for_selector("[data-jv=tab][data-k=portfolio]", timeout=20000)
    pg.click("[data-jv=tab][data-k=portfolio]")
    pg.wait_for_selector("#jvToday")
    set_sym(pg, "TCS", 100)
    pg.wait_for_timeout(7000)
    txt = " | ".join(seen(pg))
    assert "Stock trader" in txt and "20,000" not in txt and "19,9" not in txt, txt   # the book's since-entry open profit never reached the card
    c.close()


def test_running_figure_is_today_move_only(server, browser):
    w = StockWorld()
    c, pg, errs = open_journal(browser, w, tab="portfolio", sym_prices={"TCS": 100})
    pg.wait_for_function("document.querySelector('#jvToday') && /Stock trader/.test(document.querySelector('#jvToday').innerText)", timeout=15000)
    pg.wait_for_timeout(2500)
    txt = pg.inner_text("#jvToday")
    assert "20,000" not in txt and not errs
    c.close()


def test_a_wild_share_tick_does_not_move_the_figure(server, browser):
    w = StockWorld()
    c, pg, errs = open_journal(browser, w, tab="portfolio", sym_prices={"TCS": 100})
    pg.wait_for_timeout(2500)
    before = pg.evaluate("JV.todayTotal ? JV.todayTotal().total : null")
    set_sym(pg, "TCS", 1000)                      # 10x: a stale / wrong tick, not a price
    after = pg.evaluate("JV.todayTotal ? JV.todayTotal().total : null")
    if before is not None:
        assert abs(after - before) < 1, (before, after)
    c.close()


def test_an_older_cached_copy_from_another_instance_is_ignored(server, browser):
    w = StockWorld(last_run="2026-10-29T09:25:00+05:30")
    c, pg, errs = open_journal(browser, w, tab="portfolio", sym_prices={"TCS": 100})
    pg.wait_for_function("JV.stockCount() === 1", timeout=15000)
    older = {"open": [], "closed": [], "lastRun": "2026-10-29T09:20:00+05:30"}      # another instance's older copy: it has no trade yet
    assert pg.evaluate("o => JV.takeStock(o)", older) is False and pg.evaluate("JV.stockCount()") == 1
    newer = {"open": [], "closed": [], "lastRun": "2026-10-29T09:30:00+05:30"}      # a newer copy (the trade was closed): taken
    assert pg.evaluate("o => JV.takeStock(o)", newer) is True and pg.evaluate("JV.stockCount()") == 0
    assert not errs
    c.close()
