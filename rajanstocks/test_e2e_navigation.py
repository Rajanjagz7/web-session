"""Redirection checks: every screen survives a refresh, the Back button returns where you came from, and nothing opens a chart by itself.

    python -m pytest test_e2e_navigation.py -q
"""
import pytest

from test_e2e_smoke import Page, app, browser, server  # noqa: F401  (fixtures)

BOOTED = "!document.getElementById('boot')"


def _reload(app):
    app.page.reload()
    app.page.wait_for_function(BOOTED, timeout=120000)
    app.page.wait_for_timeout(1500)


@pytest.mark.parametrize("view", ["godseye", "options", "ipo", "journal", "indicators", "vedic"])
def test_each_screen_survives_a_refresh(app, view):
    app.open(view)
    app.page.wait_for_timeout(1200)
    before = app.ev("App.view")
    _reload(app)
    assert app.ev("App.view") == before, f"{view}: a refresh moved to another screen"
    assert app.ev("location.hash.slice(1)") == before


@pytest.mark.parametrize("view", ["godseye", "ipo", "journal", "indicators", "vedic"])
def test_a_refresh_off_the_trade_screen_shows_no_chart_and_loads_no_nifty_data(app, view):
    app.open(view)
    seen = []
    app.page.on("request", lambda r: seen.append(r.url) if ("/api/m/chain" in r.url or "/api/m/candles?ikey" in r.url) else None)
    _reload(app)
    app.page.wait_for_timeout(5000)
    assert not app.ev("[...document.querySelectorAll('canvas')].some(c => c.offsetParent)"), f"{view}: a chart showed up after a refresh"
    assert not seen, f"{view}: a refresh fetched option / contract data: {seen[:3]}"


def test_gods_eye_tab_is_kept_over_a_refresh(app):
    app.open("picks")
    app.page.wait_for_selector("#v-picks .ge-pkbar [data-gegrp]", timeout=90000)
    for grp, label in (("money", "FII"), ("stocks", "Signals"), ("world", "Markets"), ("picks", "Today")):
        app.ev(f"document.querySelector('#v-picks .ge-pkbar [data-gegrp=\"{grp}\"], #v-godseye [data-gegrp=\"{grp}\"]').click()")
        app.page.wait_for_timeout(1200)
        _reload(app)
        assert label.lower() in app.ev("(document.querySelector('.ge-tabs button.on, .ge-pkbar button.on') || {}).textContent").lower(), grp


def test_card_to_chart_and_back_returns_to_gods_eye(app):
    app.open("picks")
    app.page.wait_for_selector('#v-picks .ge-card[data-gecard="NIFTY"]', timeout=90000)
    app.ev("document.querySelector('#v-picks .ge-card[data-gecard=\"NIFTY\"]').click()")
    app.page.wait_for_selector(".ge-det [data-gechart]", timeout=10000)
    app.ev("document.querySelector('.ge-det [data-gechart]').click()")
    app.page.wait_for_function("App.view === 'options'", timeout=30000)
    app.page.go_back()
    app.page.wait_for_function("App.view === 'picks'", timeout=30000)
    assert not app.ev("!!document.querySelector('.ge-det')")
    _reload(app)
    assert app.ev("App.view") == "picks"
    assert not app.ev("[...document.querySelectorAll('canvas')].some(c => c.offsetParent)")


def test_every_nav_tab_click_lands_on_its_own_screen(app):
    app.open("picks")
    names = app.ev("VIEWS.map(v => v[0])")
    for v in names:
        app.ev(f"document.querySelector('#nav [data-v=\"{v}\"], nav [data-v=\"{v}\"]') ? document.querySelector('#nav [data-v=\"{v}\"], nav [data-v=\"{v}\"]').click() : go('{v}')")
        app.page.wait_for_timeout(700)
        got = app.ev("App.view")
        assert got in (v, "picks") if v == "godseye" else got == v, f"{v} landed on {got}"
