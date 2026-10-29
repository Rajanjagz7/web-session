"""End-to-end smoke + sanity tests (web 1366x800 and mobile 390x844) against a locally started server.

    python -m pytest test_e2e_smoke.py -q            # needs Chrome (or `playwright install chromium`) and an Upstox token

Each test opens a fresh browser context, watches for JavaScript errors and failing API calls, drives the screen like a user
and compares what is shown with the API / with itself (levels on the right side of price, UI numbers == API numbers).
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

import pytest

pw = pytest.importorskip("playwright.sync_api")

PORT = 8899
BASE = f"http://127.0.0.1:{PORT}"
VIEWPORTS = {
    "web": dict(viewport={"width": 1366, "height": 800}),
    "mobile": dict(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True),
}
NO_PUSH_PROMPT = """
new MutationObserver(() => { const e = document.getElementById('pushAsk'); if (e) e.remove(); })
  .observe(document, {childList: true, subtree: true});
"""


def _api(path, timeout=60):
    with urllib.request.urlopen(BASE + path, timeout=timeout) as r:
        return json.load(r)


@pytest.fixture(scope="module")
def server():
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", str(PORT), "--log-level", "warning"],
                            cwd=os.path.dirname(os.path.abspath(__file__)), env=env)
    for _ in range(60):
        try:
            _api("/api/cache-version", 2)
            break
        except Exception:
            time.sleep(1)
    else:
        proc.kill()
        pytest.skip("server did not start")
    try:
        _api("/api/m/quotes", 120)                      # warm the quote cache so the first screen is not a cold start
    except Exception:
        pass
    yield BASE
    proc.terminate()
    proc.wait(timeout=20)


@pytest.fixture(scope="module")
def browser():
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch(channel="chrome")
        except Exception:
            try:
                b = p.chromium.launch()
            except Exception as e:
                pytest.skip(f"no browser available: {str(e)[:80]}")
        yield b
        b.close()


class Page:
    """A page that records JS errors and failing API calls."""

    def __init__(self, browser, kind):
        self.ctx = browser.new_context(**VIEWPORTS[kind])
        self.ctx.add_init_script(NO_PUSH_PROMPT)
        self.ctx.add_init_script("try{if(localStorage.getItem('rs-opt-sym')===null&&!/nogate/.test(location.search))localStorage.setItem('rs-opt-sym','NIFTY')}catch(e){}")   # a brand-new device is asked what to trade; the other tests start with a choice made
        self.page = self.ctx.new_page()
        self.kind = kind
        self.js, self.http = [], []
        self.page.on("pageerror", lambda e: self.js.append(str(e)[:200]))
        self.page.on("console", lambda m: self.js.append("console: " + m.text[:200]) if m.type == "error" and "Failed to load resource" not in m.text and "ERR_NETWORK" not in m.text else None)
        self.page.on("response", lambda r: self.http.append(f"{r.status} {r.url.replace(BASE, '')[:90]}") if r.status >= 400 and "/api/" in r.url else None)

    def open(self, view="picks"):
        self.page.goto(BASE + "/#" + view)
        self.page.wait_for_function("!document.getElementById('boot')", timeout=120000)
        self.go(view)

    def go(self, view, wait=1500):
        self.page.evaluate(f"go('{view}')")
        self.page.wait_for_timeout(wait)

    def ev(self, js, *a):
        return self.page.evaluate(js, *a) if a else self.page.evaluate(js)

    def check_clean(self):
        assert not self.js, "JavaScript errors: " + " | ".join(self.js[:5])
        bad = [h for h in self.http if not h.startswith("503 /api/m/oquote")]
        assert not bad, "failing API calls: " + " | ".join(bad[:6])

    def no_overflow(self, what):
        o = self.ev("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        assert o <= 0, f"{what}: page is {o}px wider than the screen"

    def close(self):
        self.ctx.close()


@pytest.fixture(params=["web", "mobile"])
def app(request, server, browser):
    a = Page(browser, request.param)
    yield a
    a.close()


# ----------------------------------------------------------------------------------------------------------------
def test_every_screen_opens_clean_and_fits_the_screen(app):
    app.open("picks")
    # "trade" is the option-chain Trade screen (the old full-chart screen only opens for symbols without options)
    for v, shown in [("picks", "picks"), ("trade", "options"), ("markets", "godseye"), ("ipo", "ipo"), ("journal", "journal"), ("indicators", "indicators"),
                     ("vedic", "vedic"), ("options", "options"), ("portfolio", "portfolio"), ("orders", "orders"), ("alerts", "alerts"), ("daily", "daily"), ("stocks", "godseye")]:
        app.go(v, 1800)
        assert app.ev("document.querySelector('.view.on') && document.querySelector('.view.on').id") == "v-" + shown, f"{v} did not open {shown}"
        try:                                            # slow screens (Vedic computes on first open) get up to 20 s to fill in
            app.page.wait_for_function("document.querySelector('.view.on') && document.querySelector('.view.on').innerText.length > 120", timeout=20000)
        except Exception:
            pass
        text = app.ev("document.querySelector('.view.on').innerText.length")
        assert text > 120, f"{v} looks empty ({text} characters)"
        app.no_overflow(v)
    app.check_clean()


def _open_trade(app, sym=None):
    app.open("options")
    app.page.wait_for_selector(".opx-oc tbody tr", timeout=60000)
    if sym:
        app.page.select_option("#optSym", sym)
        app.page.wait_for_function(f"OPT.chain && OPT.chain.symbol === '{sym}'", timeout=60000)
    app.page.wait_for_function("OPT.sel && OPT.ochart && (OPT.ochart.data || []).length > 30", timeout=60000)


def test_trade_screen_chain_matches_the_quote_api(app):
    for sym in ("NIFTY", "BANKNIFTY", "RELIANCE"):
        _open_trade(app, sym)
        quote = {q["s"]: q for q in _api(f"/api/m/quotes?symbols={sym}")["quotes"]}[sym]
        chain = app.ev("OPT.chain")
        assert abs(chain["spot"] / quote["last"] - 1) < 0.01, f"{sym}: chain spot {chain['spot']} vs quote {quote['last']}"
        strikes = [r["strike"] for r in chain["rows"]]
        assert strikes == sorted(strikes) and len(set(strikes)) == len(strikes)
        assert chain["atm"] in strikes and min(abs(k - chain["spot"]) for k in strikes) == abs(chain["atm"] - chain["spot"])
        assert chain["lot"] >= 1 and len(chain["expiries"]) >= 2
        shown = app.ev("[...document.querySelectorAll('.opx-oc td.ltp')].slice(0, 6).map(td => td.innerText.replace(/[^0-9.]/g, ''))")
        assert any(x for x in shown), f"{sym}: no premiums on screen"
        sel = app.ev("OPT.sel")
        leg = next(r for r in chain["rows"] if r["strike"] == sel["strike"])[sel["side"].lower()]
        assert abs(app.ev("OPT.osym.last") - leg["ltp"]) / max(leg["ltp"], 1) < 0.2, f"{sym}: header price vs chain differ"
    app.check_clean()


def test_option_chart_paints_fast_and_indicators_are_finite(app):
    _open_trade(app, "NIFTY")
    rows = app.ev("OPT.chain.rows.map(r => r.strike)")
    atm = app.ev("OPT.chain.atm")
    for side, off, tf in [("CE", 0, "5m"), ("PE", 1, "15m"), ("CE", -1, "1m")]:
        strike = rows[rows.index(atm) + off]
        t0 = time.time()
        app.ev(f"OPT.tf = TFS.find(t => t.k === '{tf}'); selectOption('{side}', {strike}, true)")
        key = app.ev("OPT.osym.s + '|" + tf + "'")
        app.page.wait_for_function(f"(CACHE['{key}'] || []).length > 20", timeout=30000)
        assert time.time() - t0 < 4, f"{side} {strike} {tf}: first candles took {time.time() - t0:.1f}s"
        app.page.wait_for_function(f"!CACHE['{key}']._partial", timeout=40000)
        bars = app.ev("OPT.ochart.data")
        assert len(bars) > 50 and all(b["h"] >= max(b["o"], b["c"]) - 1e-6 and b["l"] <= min(b["o"], b["c"]) + 1e-6 for b in bars[-300:])
        last = app.ev("OPT.osym.last")
        assert abs(bars[-1]["c"] / last - 1) < 0.3, f"last candle {bars[-1]['c']} vs premium {last}"
    bad = app.ev("""(() => { const tf = OPT.tf, d = OPT.ochart.data, out = [];
      for (const k of Object.keys(DEFS).filter(k => !k.startsWith('S:'))) { const D = DEFS[k], p = {}; D.params.forEach(x => p[x.k] = x.v);
        const r = D.calc(d, p, {tf: tf.sec || 86400});
        for (const l of D.lines) { const a = r[l.k]; const sparse = k.startsWith('gann-');   // Gann angle lines are anchored at pivots: sparse by design, but never short or missing
          if (!a || a.length !== d.length || (!sparse && a.filter(Number.isFinite).length < Math.min(d.length * 0.3, d.length - 30))) out.push(k + '.' + l.k); } }
      return out; })()""")
    assert not bad, f"indicators with empty/short output on an option chart: {bad}"
    app.check_clean()


def test_option_buy_attaches_protection_exit_and_engine(app):
    _open_trade(app, "NIFTY")
    app.ev("App.cash = 1000000; App.positions = []; App.orders = []; App.history = []; App.trades = []")
    if app.kind == "mobile":
        app.ev("opxTab('order')")                      # on a phone the order panel is its own tab
        app.page.wait_for_timeout(400)
    app.page.locator("#opBuy").click()
    app.page.wait_for_timeout(600)
    assert app.ev("App.positions.length") == 1, "Buy did not open a position"
    pos = app.ev("App.positions[0]")
    assert pos["q"] > 0 and pos["q"] % app.ev("OPT.chain.lot") == 0, "quantity must be whole lots"
    assert pos["sl"] and pos["tp"], f"'Attach stop-loss and target' is ticked but the position has sl={pos.get('sl')} tp={pos.get('tp')}"
    assert pos["sl"] < pos["avg"] < pos["tp"]
    assert "You hold" in app.page.locator("#opPos").inner_text()
    sym = pos["sym"]
    app.ev(f"(() => {{ const s = SYM('{sym}'); const pv = s.last; s.last = {pos['sl'] * 0.98}; trig(s, pv); }})()")
    assert app.ev("App.positions.length") == 0 and app.ev("App.history.slice(-1)[0].src") in ("SL", "TSL")
    tr = app.ev("App.trades.slice(-1)[0]")
    assert tr["realized"] < 0 and tr["charges"] > 0 and tr["net"] < tr["realized"]
    app.page.locator("#opSell").click()
    app.page.wait_for_timeout(500)
    assert app.ev("App.positions.length") == 1 and app.ev("App.positions[0].q") < 0, "Sell (write) did not open a short position"
    app.page.locator("#opExit").click()
    app.page.wait_for_timeout(400)
    assert app.ev("App.positions.length") == 0
    app.page.locator('[data-optype="limit"]').click()
    app.page.locator("#opLmt").fill(str(round(app.ev("OPT.osym.last") * 0.5, 2)))
    app.page.locator("#opBuy").click()
    app.page.wait_for_timeout(400)
    assert app.ev("App.orders.length") == 1
    app.page.locator("[data-opcancel]").first.click()
    assert app.ev("App.orders.length") == 0
    app.ev("App.cash = 1000000; App.positions = []; App.orders = []; App.history = []; App.trades = []; savePaper()")
    app.check_clean()


def test_picks_levels_match_api_and_sit_on_the_right_side(app):
    app.open("picks")
    app.page.wait_for_selector(".view.on", timeout=30000)
    picks = _api("/api/m/picks")["picks"]
    sig = [p for p in picks if p["signal"] in ("BUY", "SELL")]
    assert sig, "no BUY/SELL picks at all"
    for p in sig:
        buy = p["signal"] == "BUY"
        assert (p["stop"] < p["entry"]) if buy else (p["stop"] > p["entry"]), f"{p['s']} stop on the wrong side"
        assert (p["target"] > p["entry"]) if buy else (p["target"] < p["entry"]), f"{p['s']} target on the wrong side"
        assert (p["target2"] > p["target"]) if buy else (p["target2"] < p["target"]), f"{p['s']} target2 not beyond target"
        assert p["rr"] >= 1.0 and p["ltp"] > 0
    # the first signal's numbers appear in the page
    app.page.wait_for_timeout(2500)
    text = app.ev("document.querySelector('.view.on').innerText")
    top = [p for p in picks if p["s"] in text][:1]
    assert top, "no pick from the API is shown on the Picks screen"
    app.check_clean()


def test_indicator_screen_headlines_equal_the_api(app):
    app.open("indicators")
    app.page.wait_for_selector(".st-card .st-hl", timeout=60000)
    sym = app.ev("document.getElementById('stSym').value")
    app.page.wait_for_timeout(4000)
    shown = app.ev("[...document.querySelectorAll('.st-card')].map(c => ({k: (c.querySelector('[data-st^=\"chart:\"]') || {dataset: {}}).dataset.st, hl: (c.querySelector('.st-hl') || {}).textContent}))")
    checked = 0
    for c in shown:
        if not c["k"] or not c["hl"]:
            continue
        key = c["k"].split(":")[1]
        api = _api(f"/api/m/strategy?key={key}&symbol={sym}")
        # the screen words daily-bar counts as sessions; the API says bars
        norm = lambda s: "".join(ch for ch in s.replace("bar(s)", "sessions").replace("bars", "sessions") if ch.isalnum()).lower()
        assert norm(api["headline"])[:40] == norm(c["hl"])[:40] or norm(c["hl"])[:25] in norm(api["headline"]), f"{key}: UI '{c['hl'][:60]}' vs API '{api['headline'][:60]}'"
        checked += 1
    assert checked >= 5, f"only {checked} indicator cards had a result"
    app.check_clean()


def test_other_screens_show_live_data(app):
    app.open("markets")   # the old Markets screen now opens God's Eye > Markets > All stocks
    app.page.wait_for_selector("#geSL .sb-row", state="attached", timeout=30000)
    app.page.wait_for_timeout(2500)
    rows = app.ev("document.querySelectorAll('#geSL .sb-row').length")
    assert rows >= 10
    prices = app.ev("[...document.querySelectorAll('#geSL .sb-row:not(.sb-head) .c-ltp')].slice(0, 20).map(e => e.textContent.trim())")
    assert sum(1 for p in prices if p and p != "—") >= 10, "markets list shows no prices"
    app.go("vedic", 5000)
    vedic_text = app.ev("document.querySelector('.view.on').innerText").lower()   # labels are upper-cased by CSS
    assert "tithi" in vedic_text or "panchang" in vedic_text
    app.go("ipo", 4000)
    assert app.ev("document.querySelectorAll('.ipf-card').length") > 0
    app.go("journal", 1500)
    assert app.ev("document.querySelectorAll('.jv-tabs button').length") >= 3
    app.check_clean()


def test_mobile_layout_basics(server, browser):
    a = Page(browser, "mobile")
    try:
        _open_trade(a, "NIFTY")
        a.page.wait_for_function("document.querySelector('.opx-mtabs') && document.querySelector('.opx-mtabs').offsetParent", timeout=20000)
        tabs = a.ev("[...document.querySelectorAll('.opx-mtabs button')].map(b => b.textContent.trim())")
        assert tabs == ["Chain", "Chart", "Order", "Signals"], tabs
        assert a.page.locator("#opxDock").is_visible(), "Buy/Sell dock missing on the phone"
        small = a.ev("[...document.querySelectorAll('.nav button, #opxDock button, .opx-mtabs button')].filter(b => b.offsetParent).map(b => b.getBoundingClientRect()).filter(r => r.height < 36).length")
        assert small == 0, f"{small} bottom-bar buttons are shorter than 36px"
        for tab in ("chain", "chart", "order", "signals"):
            a.ev(f"opxTab('{tab}')")
            a.page.wait_for_timeout(500)
            a.no_overflow("trade/" + tab)
        a.check_clean()
    finally:
        a.close()


def test_front_end_files_have_no_stray_control_characters():
    # a '\b' typed through a patch script becomes a backspace and silently breaks the regex (the Index filter did exactly that)
    import pathlib
    root = pathlib.Path(__file__).parent / "public"
    for f in [root / "index.html", *sorted((root / "static").glob("*.js"))]:
        txt = f.read_text(encoding="utf-8")
        bad = sorted({hex(ord(c)) for c in txt if ord(c) < 32 and c not in "\r\n\t"})
        assert not bad, f"{f.name} contains control characters {bad}"


def test_start_up_survives_a_saved_position_without_contract_data(app):
    # a saved paper position whose option is no longer listed used to throw at start-up and leave the loader on screen for good
    app.open("picks")
    app.page.add_init_script("""try { localStorage.setItem('rs-paper-v1', JSON.stringify({cash: 900000, oid: 3, watch: [], alerts: [], orders: [], history: [],
        positions: [{sym: 'NIFTY 22,750 CE 27 Oct', q: 65, avg: 83.2}], meta: {}})) } catch (e) {}""")
    app.page.reload()
    app.page.wait_for_function("!document.getElementById('boot')", timeout=60000)
    assert app.ev("!!SYM('NIFTY 22,750 CE 27 Oct')"), "the saved contract was not restored"
