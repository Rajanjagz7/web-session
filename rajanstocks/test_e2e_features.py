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
    app.page.wait_for_function("document.querySelectorAll('#opxFut [data-opx^=\"fut:\"]').length >= 2", timeout=60000)
    app.ev("document.querySelector('#opxFut [data-opx^=\"fut:\"]').click()")
    app.page.wait_for_function("OPT.sel && OPT.sel.fut && OPT.osym && (CACHE[OPT.osym.s + '|' + OPT.tf.k] || []).length > 20", timeout=60000)
    assert app.ev("!!document.getElementById('opBuy')") is False, "futures must not show the option order ticket"
    assert "chart-only" in app.ev("document.getElementById('opTrade').innerText")
    assert app.ev("document.getElementById('opName').textContent").startswith(app.ev("OPT.sym") + " FUT")
    # back to an option: the order ticket returns
    app.ev("[...document.querySelectorAll('#opSw button')].find(b => b.textContent.trim() === 'CE').click()")
    app.page.wait_for_function("OPT.sel && !OPT.sel.fut && document.getElementById('opBuy')", timeout=30000)


@pytest.mark.parametrize("tile", ["NSEIX:NIFTY1!", "CBOT_MINI:YM1!", "COMEX:SI1!", "NYMEX:CL1!"])
def test_global_futures_tiles_open_a_chart(app, tile):
    app.open("markets")
    app.page.wait_for_function(f"document.querySelector('#glStrip [data-gl=\"{tile}\"]')", timeout=60000)
    app.ev(f"document.querySelector('#glStrip [data-gl=\"{tile}\"]').click()")
    app.page.wait_for_function("App.view === 'trade' && App.sym && App.sym.tv && (CACHE[App.sym.s + '|' + App.tf.k] || []).length > 20", timeout=90000)


def test_godseye_details_card_is_compact(app):
    app.open("picks")
    app.page.wait_for_function("document.querySelector('.ob-card[data-ob]')", timeout=90000)
    app.ev("document.querySelector('.ob-card[data-ob]').click()")
    app.page.wait_for_selector(".ob-card.open", timeout=10000)
    h = app.ev("document.querySelector('.ob-card.open').getBoundingClientRect().height")
    limit = 480 if app.kind == "web" else 700
    assert h < limit, f"opened God's Eye card is {h:.0f}px tall (limit {limit})"
    app.no_overflow("God's Eye details")


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
