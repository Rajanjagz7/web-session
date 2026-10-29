"""End-to-end checks for the Journal, Futures and God's Eye changes (web 1366x800 and mobile 390x844).

    python -m pytest test_e2e_features.py -q       # headless; starts the app on a local port like test_e2e_smoke.py
"""
import pytest

from test_e2e_smoke import Page, app, browser, server  # noqa: F401  (fixtures)

SEED_TRADES = """
() => {
  const d = new Date().toISOString().slice(0, 10), now = Date.now();
  App.positions = [
    {sym: 'NIFTY', q: 50, avg: 22600, sl: 22500, day: d, t: now},
    {sym: 'RELIANCE', q: 20, avg: 1190, sl: 1170, day: d, t: now},
    {sym: 'NIFTY 22900 PE 27 Oct', q: -75, avg: 150, day: d, t: now}];
  App.meta['NIFTY 22900 PE 27 Oct'] = {ikey: 'NSE_FO|1', und: 'NIFTY', strike: 22900, side: 'PE'};
  App.trades = [
    {id: 1004, sym: 'TCS', side: 'sell', closeQty: 5, avgBefore: 3000, price: 3010, day: d, t: now, src: 'manual', realized: 50, posAfter: 0, charges: 10},
    {id: 1005, sym: 'BANKNIFTY', side: 'sell', closeQty: 10, avgBefore: 54000, price: 54100, day: d, t: now, src: 'manual', realized: 1000, posAfter: 0, charges: 20}];
  savePaper(); saveTrades(); JV.render();
}
"""

POSITION_SYMBOLS = """
async () => {
  const tab = k => [...document.querySelectorAll('#v-journal [data-jv="tab"]')].find(x => x.textContent.trim() === k).click();
  const wait = ms => new Promise(r => setTimeout(r, ms));
  tab('Positions'); await wait(900);
  [...document.querySelectorAll('#v-journal button')].filter(b => b.textContent.trim() === '1000').forEach(b => b.click()); await wait(700);
  return [...document.querySelectorAll('#v-journal .jv-t tbody tr')].map(r => (r.querySelector('.jv-sym b') || {}).textContent).filter(Boolean);
}
"""


def _journal(app):
    app.open("journal")
    app.page.wait_for_function("window.JV && document.querySelector('#v-journal .jv')", timeout=60000)


def test_manual_paper_trades_show_in_journal_by_market(app):
    _journal(app)
    app.ev(SEED_TRADES)
    syms = app.ev(POSITION_SYMBOLS)
    # open index, stock and option positions + closed fills: the contract expiring on the 27th and fill numbers 1004 must not be treated as removed trades
    for s in ("NIFTY", "RELIANCE", "NIFTY 22900 PE 27 Oct", "TCS", "BANKNIFTY"):
        assert s in syms, f"{s} missing from the journal positions: {syms}"
    app.go("journal", 800)
    app.ev("() => [...document.querySelectorAll('#v-journal [data-jv=\"tab\"]')].find(x => x.textContent.trim() === 'Portfolio').click()")
    app.page.wait_for_timeout(700)
    app.ev("() => [...document.querySelectorAll('#v-journal button')].find(b => b.textContent.trim() === 'Filters').click()")
    app.page.wait_for_timeout(600)
    got = {}
    for market in ("Index", "Options", "Equity Intraday"):
        app.ev("""(m) => { const s = document.querySelector('[data-jf="market"]'); s.value = m; s.dispatchEvent(new Event('change', {bubbles: true})); }""", market)
        app.page.wait_for_timeout(700)
        got[market] = app.ev("() => { const t = [...document.querySelectorAll('#v-journal .jv-t')].pop(); return [...t.querySelectorAll('tbody tr')].map(r => (r.querySelector('.jv-sym b') || {}).textContent); }")   # last table = 'Recent trades', the one the market filter applies to
    assert "NIFTY" in got["Index"] and "BANKNIFTY" in got["Index"] and "RELIANCE" not in got["Index"], got
    assert "NIFTY 22900 PE 27 Oct" in got["Options"] and "NIFTY" not in got["Options"], got
    assert "RELIANCE" in got["Equity Intraday"] and "TCS" in got["Equity Intraday"], got


def test_journal_reset_clears_everything_on_the_device(app):
    _journal(app)
    app.ev(SEED_TRADES)
    assert app.ev("JV.totals().open") >= 3
    app.ev("window.confirm = () => true")
    app.ev("() => document.querySelector('[data-jv=\"reset\"]').click()")
    app.page.wait_for_function("JV.totals().open === 0 && App.positions.length === 0 && App.trades.length === 0", timeout=20000)
    t = app.ev("JV.totals()")
    assert t["booked"] == 0 and t["unr"] == 0 and t["today"] == 0, t
    stores = app.ev("() => [JSON.parse(localStorage.getItem('rs-paper-v1') || '{}').positions.length, JSON.parse(localStorage.getItem('rs-trades-v1') || '[]').length]")
    assert stores == [0, 0], f"device stores not cleared: {stores}"


def test_reset_query_wipes_the_device(app, server):
    _journal(app)
    app.ev(SEED_TRADES)
    app.page.goto(server + "/?reset=1#journal")
    app.page.wait_for_function("!document.getElementById('boot')", timeout=120000)
    assert "reset=1" not in app.page.url
    assert app.ev("App.positions.length") == 0 and app.ev("App.trades.length") == 0


def test_nse_futures_open_as_charts_on_the_trade_screen(app):
    app.open("options")
    # futures are a dropdown on the Trade screen (#optFut): pick the near contract
    app.page.wait_for_function("document.querySelectorAll('#optFut option[value^=\"NSE_FO|\"]').length >= 2", timeout=60000)
    app.ev("(() => { const s = document.getElementById('optFut'); s.value = s.querySelector('option[value^=\"NSE_FO|\"]').value; s.dispatchEvent(new Event('change', {bubbles: true})); })()")
    app.page.wait_for_function("OPT.sel && OPT.sel.fut && OPT.osym && (CACHE[OPT.osym.s + '|' + OPT.tf.k] || []).length > 20", timeout=60000)
    assert app.ev("!!document.getElementById('opBuy')") is False, "futures must not show the option order ticket"
    assert "chart-only" in app.ev("document.getElementById('opTrade').innerText")
    assert app.ev("document.getElementById('opName').textContent").startswith(app.ev("OPT.sym") + " FUT")
    # back to an option: the order ticket returns
    app.ev("[...document.querySelectorAll('#opSw button')].find(b => b.textContent.trim() === 'CE').click()")
    app.page.wait_for_function("OPT.sel && !OPT.sel.fut && document.getElementById('opBuy')", timeout=30000)


@pytest.mark.parametrize("card", ["NIFTY", "BANKNIFTY", "GOLD", "NASDAQ"])
def test_overview_cards_open_their_chart(app, card):
    # Today's Picks leads with the God's Eye overview cards (indices, gold, crude, Nasdaq ...): card -> detail drawer -> Chart
    app.open("picks")
    app.page.wait_for_selector(f'#v-picks .ge-card[data-gecard="{card}"]', timeout=90000)
    app.ev(f"document.querySelector('#v-picks .ge-card[data-gecard=\"{card}\"]').click()")
    app.page.wait_for_selector(".ge-det [data-gechart]", timeout=10000)
    app.ev("document.querySelector('.ge-det [data-gechart]').click()")
    app.page.wait_for_function("['trade', 'options'].includes(App.view) && App.sym && (CACHE[App.sym.s + '|' + App.tf.k] || []).length > 20", timeout=90000)


def test_app_opens_on_todays_picks_under_the_gods_eye_tab_bar(app):
    # God's Eye is the first nav tab and its Today's Picks tab is the home screen; Picks / Markets are not separate nav tabs
    app.open("picks")
    assert app.ev("VIEWS[0][0]") == "godseye" and not app.ev("VIEWS.some(v => v[0] === 'picks' || v[0] === 'markets')")
    assert app.ev("[...document.querySelectorAll('#v-picks .ge-pkbar [data-gegrp]')].map(b => b.dataset.gegrp).join(',')") == "picks,money,stocks,world"
    assert app.ev("!!document.querySelector('#v-picks #pkPanel') && !!document.querySelector('#v-picks .nws')"), "Today's Picks lost its filters or news"
    app.no_overflow("God's Eye > Today's Picks")
    app.ev("document.querySelector('#v-picks .ge-pkbar [data-gegrp=\"money\"]').click()")
    app.page.wait_for_function("App.view === 'godseye' && /FII/.test(document.querySelector('#v-godseye .ge-tabs button.on').textContent)", timeout=30000)
    app.ev("document.querySelector('#v-godseye .ge-tabs [data-gegrp=\"picks\"]').click()")
    app.page.wait_for_function("App.view === 'picks'", timeout=30000)


def test_picks_shows_the_overview_once(app):
    # one block, not two: the God's Eye overview at the top of Today's Picks - no old index tiles, no ticker, no second strip
    app.open("picks")
    app.page.wait_for_function("document.querySelectorAll('#v-picks .ge-card[data-gecard]').length >= 8", timeout=120000)
    assert app.ev("document.querySelectorAll('#v-picks .ge-out').length") == 1, "next-day read-out missing or repeated"
    assert not app.ev("!!document.querySelector('#v-picks .ixs, #pkGodseye, .ge-strip, .ob-grid, .ge-tick')"), "Picks still shows a second indices / God's Eye block"
    assert not app.ev("/Signal Throughput|Data feeds/.test(document.querySelector('#v-picks').innerText)"), "throughput / data-feed panels should be hidden"
    app.no_overflow("Picks overview")


def test_journal_exit_buttons_stay_on_screen_on_phones(app):
    if app.kind != "mobile":
        pytest.skip("mobile layout only")
    _journal(app)
    app.ev(SEED_TRADES)
    app.ev("() => [...document.querySelectorAll('#v-journal [data-jv=\"tab\"]')].find(x => x.textContent.trim() === 'Positions').click()")
    app.page.wait_for_timeout(900)
    boxes = app.ev("() => [...document.querySelectorAll('#v-journal .jv-exit')].filter(b => b.offsetParent).map(b => { const r = b.getBoundingClientRect(); return [r.left, r.right]; })")
    assert boxes, "no Exit buttons rendered"
    assert all(0 <= l and r <= 390 for l, r in boxes), f"Exit buttons off screen: {boxes}"


def test_gods_eye_tabs_show_flows_options_and_signals(app):
    app.open("picks")
    app.page.wait_for_function("document.querySelectorAll('#v-picks .ge-card[data-gecard]').length >= 8", timeout=120000)
    for tab, marker in (("fii", "FII / DII cash market"), ("fno", "levels"), ("signals", "Stocks by sector"), ("movers", "Top gainers"), ("stocklist", "NSE stocks"), ("range", "Where price sits")):
        app.ev(f"geOpenTab('{tab}'); go('godseye')")
        app.page.wait_for_timeout(1500)
        assert app.ev("App.view") == "godseye", f"{tab} did not open God's Eye"
        assert marker.lower() in app.ev("document.querySelector('#v-godseye').innerText").lower(), f"{tab} tab did not render"
        app.no_overflow("God's Eye " + tab)
    app.ev("go('picks')")
    app.page.wait_for_selector('#v-picks .ge-card[data-gecard]', timeout=30000)
    app.ev("document.querySelector('#v-picks .ge-card[data-gecard]').click()")
    app.page.wait_for_selector(".ge-det", timeout=5000)
    app.ev("document.querySelector('.ge-det .ge-x').click()")
    app.page.wait_for_timeout(300)
    assert not app.ev("!!document.querySelector('.ge-det')"), "details drawer did not close"
    app.check_clean()
