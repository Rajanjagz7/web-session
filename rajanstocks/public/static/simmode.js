/* SIM MODE - a fake live market so the paper-trading screens can be tested any time (weekends, nights).
   Open the app with  ?sim=1  to start it, use the panel (bottom-right) to pick a scenario, and "Exit sim" to come back.

   What it does
   - Clock: the app's Date is moved to a trading day (09:15 IST) and can run fast (x1 .. x600).
   - Prices: /api/m/quotes, /api/m/chain, /api/m/oquote, /api/m/expiries and option candles are answered here with a scenario path
     (trend up, trend down, chop, V, inverted V, gap, crash). Stocks follow the index by their own beta plus their own noise.
   - Safety: this device's saved data is backed up on entry and restored on exit, and every request that WRITES on the server
     (reset / run / cron / POST) is answered with a fake "ok" - a sim can never touch the real paper books on the server.
   What it does NOT do: the strategy / indicator / auto-trader code runs on the server on real data; see sim_strategy_lab.py for that. */
(function () {
  'use strict';
  var LS = window.localStorage, KEEP = /^sim-/;
  var q = /[?&]sim=(1|0)(&|$)/.exec(location.search);
  var on = false;
  try { on = LS.getItem('sim-on') === '1'; } catch (e) { }

  function exitSim() {
    try {
      var b = JSON.parse(LS.getItem('sim-backup') || '{}');
      var drop = []; for (var i = 0; i < LS.length; i++) drop.push(LS.key(i));
      drop.forEach(function (k) { LS.removeItem(k); });
      Object.keys(b).forEach(function (k) { LS.setItem(k, b[k]); });
    } catch (e) { console.warn('sim restore', e); }
    location.replace(location.pathname + location.hash);
  }
  if (q && q[1] === '0') { if (on) return exitSim(); }
  if (q && q[1] === '1' && !on) {
    try {      // back up the real data once, then start from an empty device
      var bk = {}, ks = []; for (var i = 0; i < LS.length; i++) ks.push(LS.key(i));
      ks.forEach(function (k) { if (!KEEP.test(k)) bk[k] = LS.getItem(k); });
      LS.setItem('sim-backup', JSON.stringify(bk));
      ks.forEach(function (k) { if (!KEEP.test(k) && k !== 'sim-backup') LS.removeItem(k); });
      LS.setItem('sim-on', '1'); on = true;
    } catch (e) { console.warn('sim start', e); }
  }
  if (!on) return;
  try { history.replaceState(null, '', location.pathname + location.hash); } catch (e) { }

  /* ---------------- clock ---------------- */
  var RealDate = Date, realFetch = window.fetch.bind(window);
  var IST = 330 * 60000, SESSION = 375;                         // 09:15 - 15:30
  var clk = { speed: 30, paused: false, base: 0, at: 0 };       // base = sim ms at real time `at`
  function sessionOpen() {                                      // the most recent weekday, 09:15 IST, as a UTC ms value
    var d = new RealDate(RealDate.now() + IST);
    while (d.getUTCDay() === 0 || d.getUTCDay() === 6) d = new RealDate(d.getTime() - 864e5);
    return RealDate.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate(), 9, 15) - IST;
  }
  var open0 = sessionOpen();
  try { var sv = +LS.getItem('sim-clock'); if (sv && sv >= open0 && sv <= open0 + SESSION * 60000) { clk.base = sv; } else clk.base = open0; } catch (e) { clk.base = open0; }
  clk.at = RealDate.now();
  function simNow() {
    if (clk.paused) return clk.base;
    var t = clk.base + (RealDate.now() - clk.at) * clk.speed;
    var end = open0 + SESSION * 60000; return t > end ? end : t;
  }
  function SimDate() {
    if (!(this instanceof SimDate)) return new RealDate(simNow()).toString();
    var a = arguments;
    if (!a.length) return new RealDate(simNow());
    if (a.length === 1) return new RealDate(a[0]);
    return new (Function.prototype.bind.apply(RealDate, [null].concat([].slice.call(a))))();
  }
  SimDate.prototype = RealDate.prototype; SimDate.now = simNow; SimDate.UTC = RealDate.UTC; SimDate.parse = RealDate.parse;
  window.Date = SimDate;
  function rebase(newBase, speed) { clk.base = newBase; clk.at = RealDate.now(); if (speed) clk.speed = speed; }

  /* ---------------- market model ---------------- */
  var INDEX = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX'];
  var STEP = { NIFTY: 50, BANKNIFTY: 100, FINNIFTY: 50, MIDCPNIFTY: 25, SENSEX: 100 };
  var LOT = { NIFTY: 75, BANKNIFTY: 30, FINNIFTY: 65, MIDCPNIFTY: 120, SENSEX: 20 };
  var BETA = { NIFTY: 1, BANKNIFTY: 1.15, FINNIFTY: 1.05, MIDCPNIFTY: 1.25, SENSEX: 0.98 };
  var FALLBACK = { NIFTY: 24500, BANKNIFTY: 53000, FINNIFTY: 25000, MIDCPNIFTY: 12500, SENSEX: 80500, INDIAVIX: 14 };
  var SCEN = {
    up:     { label: 'Trend up',      path: function (p) { return 0.015 * p; } },
    down:   { label: 'Trend down',    path: function (p) { return -0.015 * p; } },
    chop:   { label: 'Chop',          path: function (p) { return 0.002 * Math.sin(p * 18); } },
    v:      { label: 'V reversal',    path: function (p) { return p < .45 ? -0.012 * (p / .45) : -0.012 + 0.022 * ((p - .45) / .55); } },
    invv:   { label: 'Inverted V',    path: function (p) { return p < .45 ? 0.012 * (p / .45) : 0.012 - 0.022 * ((p - .45) / .55); } },
    gapup:  { label: 'Gap up + fade', path: function (p) { return 0.012 - 0.014 * p; }, gap: 0.012 },
    crash:  { label: 'Crash',         path: function (p) { return p < .25 ? -0.035 * (p / .25) : -0.035 - 0.01 * (p - .25); } },
    steps:  { label: 'Up with pullbacks', path: function (p) { return 0.018 * p + 0.004 * Math.sin(p * 30); } }
  };
  var M = { base: null, q: {}, scen: 'up', noise: {}, idio: {}, rng: 1, hist: {}, lastP: -1, loading: null, wall: {} };
  function rnd() { M.rng = (M.rng * 1664525 + 1013904223) % 4294967296; return M.rng / 4294967296; }
  function gauss() { var u = 0; for (var i = 0; i < 6; i++) u += rnd(); return (u - 3) / 0.7071; }
  var r2 = function (v, d) { var m = Math.pow(10, d == null ? 2 : d); return Math.round(v * m) / m; };

  function loadBase() {
    if (M.base) return Promise.resolve();
    if (M.loading) return M.loading;
    M.loading = realFetch('/api/m/quotes', { cache: 'no-store' }).then(function (r) { return r.json(); }).then(function (j) {
      var b = {}; (j.quotes || []).forEach(function (x) { if (x && x.s && x.last > 0) b[x.s] = x; }); M.base = b;
    }).catch(function () { M.base = {}; }).then(function () {
      INDEX.concat(['INDIAVIX']).forEach(function (s) { if (!M.base[s]) M.base[s] = { s: s, last: FALLBACK[s], prev: FALLBACK[s], yh: FALLBACK[s] * 1.15, yl: FALLBACK[s] * .8 }; });
      reset(M.scen);
    });
    return M.loading;
  }
  function reset(scen) {
    M.scen = scen || M.scen; var S = SCEN[M.scen];
    try { LS.setItem('sim-scen', M.scen); } catch (e) { }
    M.q = {}; M.hist = {}; M.noise = {}; M.idio = {}; M.rng = 7; M.fnoise = 0; KEYS = {};
    Object.keys(M.base).forEach(function (s) {
      var b = M.base[s], prev = b.last, o = prev * (1 + (s === 'INDIAVIX' ? -6 : (BETA[s] || 1)) * S.path(0));
      M.q[s] = { s: s, last: o, prev: prev, open: o, high: o, low: o, vol: 0, yh: b.yh || prev * 1.2, yl: b.yl || prev * .8, dp: prev < 100 ? 2 : 2 };
      M.noise[s] = 0; M.idio[s] = (rnd() - .5) * .012;       // each name has its own day drift (+-0.6 %)
      M.hist[s] = [];
    });
    M.lastP = -1; M.mtx = null;
  }
  function progress() { return Math.max(0, Math.min(1, (simNow() - open0) / (SESSION * 60000))); }
  var STEP_MS = 15000, stepped = -1;
  function advance() {
    if (!M.base) return;
    var now = simNow(), n = Math.floor((now - open0) / STEP_MS);
    if (stepped < 0 || n < stepped) stepped = Math.max(-1, n - 1);       // clock moved back: re-sync
    var guard = 0;
    while (stepped < n && guard++ < 400) {
      stepped++;
      var p = Math.min(1, (stepped * STEP_MS) / (SESSION * 60000)), S = SCEN[M.scen], target = S.path(p);
      var f = M.fnoise = (M.fnoise || 0) * .9 + gauss() * .00025;       // index-wide noise, smoothed
      var idx = target + f;
      Object.keys(M.q).forEach(function (s) {
        var q = M.q[s], b = M.base[s]; if (!q) return;
        var ret;
        if (s === 'INDIAVIX') ret = -idx * 6 + (M.noise[s] = M.noise[s] * .9 + gauss() * .003);
        else {
          var beta = BETA[s] || (0.7 + (hash(s) % 70) / 100), nz = M.noise[s] = M.noise[s] * .92 + gauss() * (INDEX.indexOf(s) >= 0 ? .00008 : .0007);
          ret = beta * idx + (INDEX.indexOf(s) >= 0 ? 0 : M.idio[s] * p) + nz;
        }
        var px = Math.max(0.05, b.last * (1 + ret));      // b.last = the previous close; the path already contains the opening gap
        q.last = px; if (px > q.high) q.high = px; if (px < q.low) q.low = px; q.vol += Math.round(1000 * (1 + rnd()) * (1 + Math.abs(ret) * 200));
        if (stepped % 4 === 0) { var h = M.hist[s]; h.push([open0 + stepped * STEP_MS, px]); if (h.length > 4000) h.shift(); }
      });
    }
  }
  function hash(s) { var h = 0; for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0; return h; }

  function quoteOf(s) {
    var q = M.q[s]; if (!q) return null;
    var sp = Math.max(.01, q.last * .00012);
    return { s: s, last: r2(q.last), prev: r2(q.prev), open: r2(q.open), high: r2(q.high), low: r2(q.low), vol: q.vol,
      bid: r2(q.last - sp / 2), ask: r2(q.last + sp / 2), yh: r2(q.yh), yl: r2(q.yl) };
  }

  /* ---------------- options (Black-Scholes at a fixed days-to-expiry) ---------------- */
  function cnd(x) { var t = 1 / (1 + .2316419 * Math.abs(x)), d = .3989423 * Math.exp(-x * x / 2), p = d * t * (.3193815 + t * (-.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274)))); return x > 0 ? 1 - p : p; }
  function bs(S, K, T, iv, call) {
    if (T <= 0) return Math.max(0, call ? S - K : K - S);
    var r = .07, d1 = (Math.log(S / K) + (r + iv * iv / 2) * T) / (iv * Math.sqrt(T)), d2 = d1 - iv * Math.sqrt(T);
    return call ? S * cnd(d1) - K * Math.exp(-r * T) * cnd(d2) : K * Math.exp(-r * T) * cnd(-d2) - S * cnd(-d1);
  }
  function expiries() {                                               // next 3 Thursdays at least 1 day out, as YYYY-MM-DD
    var out = [], d = new RealDate(open0 + IST); d.setUTCHours(0, 0, 0, 0);
    for (var i = 1; out.length < 3 && i < 40; i++) { var x = new RealDate(d.getTime() + i * 864e5); if (x.getUTCDay() === 4) out.push(x.toISOString().slice(0, 10)); }
    return out;
  }
  function daysTo(exp) { var e = RealDate.parse(exp + 'T10:00:00Z'); return Math.max(.2, (e - (simNow() + IST)) / 864e5 + .2); }
  var KEYS = {};                                                       // numeric key -> contract (kept, so its open / high / low survive between calls)
  function contract(sym, exp, strike, side) {
    var id = 'NSE_FO|' + (9000000 + (hash(sym + exp + strike + side) % 900000));
    return KEYS[id] || (KEYS[id] = { id: id, sym: sym, exp: exp, strike: strike, side: side });
  }
  function premium(c, spot) {
    var q = M.q[c.sym]; if (!q) return 0; var S = spot || q.last;
    var vix = (M.q.INDIAVIX ? M.q.INDIAVIX.last : 14) / 100, iv = c.sym in STEP ? vix * .95 : vix * 1.6 + .08;
    var T = daysTo(c.exp) / 365, m = Math.abs(Math.log(S / c.strike)); iv *= 1 + m * 2;       // a little smile
    return Math.max(.05, bs(S, c.strike, T, iv, c.side === 'CE'));
  }
  function stepFor(sym) { if (STEP[sym]) return STEP[sym]; var p = (M.q[sym] || { last: 500 }).last; return p < 250 ? 5 : p < 1000 ? 10 : p < 3000 ? 20 : 50; }
  function optQuote(c) {
    var key = c.id, p = premium(c), sp = Math.max(.05, p * .004);
    if (c.prevPx == null) { c.prevPx = premium(c, M.q[c.sym].prev); c.open = p; c.hi = p; c.lo = p; }     // previous close = the premium at the previous close of the underlying
    c.hi = Math.max(c.hi, p); c.lo = Math.min(c.lo, p);
    return { key: key, last: r2(p), prev: r2(c.prevPx), open: r2(c.open), high: r2(c.hi), low: r2(c.lo), vol: 100000 + (hash(key) % 90000), oi: 500000 + (hash(key) % 400000), oiPrev: 480000 + (hash(key) % 400000),
      bid: r2(Math.max(.05, p - sp / 2)), ask: r2(p + sp / 2) };
  }
  function chainFor(sym, exp) {
    var q = M.q[sym]; if (!q) return null; var ex = expiries(), e = exp && ex.indexOf(exp) >= 0 ? exp : ex[0];
    var st = stepFor(sym), atm = Math.round(q.last / st) * st, rows = [];
    for (var k = -12; k <= 12; k++) {
      var K = atm + k * st, row = { strike: K };
      ['CE', 'PE'].forEach(function (side) {
        var c = contract(sym, e, K, side), o = optQuote(c), key = c.id;
        row[side.toLowerCase()] = { key: key, ltp: o.last, prev: o.prev, open: o.open, high: o.high, low: o.low, oi: o.oi, oiChg: o.oi - o.oiPrev, vol: o.vol, bid: o.bid, ask: o.ask };
      });
      rows.push(row);
    }
    return { symbol: sym, lot: LOT[sym] || 500, spot: r2(q.last), expiry: e, expiries: ex, atm: atm, rows: rows, provider: 'SIM', asOf: new RealDate(simNow()).toISOString() };
  }
  function optBars(c, tfSec) {
    var h = M.hist[c.sym] || [], out = [], cur = null, sec = (tfSec || 300) * 1000;
    h.forEach(function (pt) {
      var px = bs(pt[1], c.strike, daysTo(c.exp) / 365, ((M.q.INDIAVIX ? M.q.INDIAVIX.last : 14) / 100) * .95, c.side === 'CE'); px = Math.max(.05, px);
      var t = Math.floor(pt[0] / sec) * sec;
      if (!cur || cur.t !== t) { cur = { t: t, o: px, h: px, l: px, c: px, v: 1000 }; out.push(cur); } else { cur.h = Math.max(cur.h, px); cur.l = Math.min(cur.l, px); cur.c = px; cur.v += 500; }
    });
    return out.slice(-300).map(function (b) { return { t: b.t, o: r2(b.o), h: r2(b.h), l: r2(b.l), c: r2(b.c), v: b.v }; });
  }

  /* ---------------- fetch interception ---------------- */
  function jres(obj, status) { return new Response(JSON.stringify(obj), { status: status || 200, headers: { 'Content-Type': 'application/json' } }); }
  var WRITE = /\/(reset|run|cron|subscribe|unsubscribe|send|save|clear|toggle|config|auto\/(start|stop|run))\b/i;
  window.fetch = function (input, init) {
    var url = typeof input === 'string' ? input : (input && input.url) || '', method = ((init && init.method) || (input && input.method) || 'GET').toUpperCase();
    var u; try { u = new URL(url, location.origin); } catch (e) { return realFetch(input, init); }
    if (u.origin !== location.origin || u.pathname.indexOf('/api/') !== 0) return realFetch(input, init);
    var path = u.pathname, P = u.searchParams;
    if (method !== 'GET' && method !== 'HEAD') return Promise.resolve(jres({ ok: true, sim: true, note: 'blocked in sim mode' }));
    if (WRITE.test(path)) return Promise.resolve(jres({ ok: true, sim: true, note: 'blocked in sim mode' }));
    if (path === '/api/m/quotes') return loadBase().then(function () {
      advance(); var want = (P.get('symbols') || '').split(',').map(function (x) { return x.trim().toUpperCase(); }).filter(Boolean);
      var syms = want.length ? want : Object.keys(M.q), out = [];
      syms.forEach(function (s) { var x = quoteOf(s); if (x) out.push(x); });
      return jres({ quotes: out, marketOpen: true, asOf: new RealDate(simNow()).toISOString(), stale: false, sim: true });
    });
    if (path === '/api/m/chain') return loadBase().then(function () {
      advance(); var c = chainFor((P.get('symbol') || 'NIFTY').toUpperCase(), P.get('expiry') || '');
      return c ? jres(c) : jres({ detail: 'no chain' }, 400);
    });
    if (path === '/api/m/oquote') return loadBase().then(function () {
      advance(); var out = []; (P.get('keys') || '').split(',').forEach(function (k) { var c = KEYS[k.trim()]; if (c) out.push(optQuote(c)); });
      return jres({ quotes: out, marketOpen: true, asOf: new RealDate(simNow()).toISOString() });
    });
    if (path === '/api/m/expiries') return Promise.resolve(jres({ symbol: P.get('symbol'), expiries: [] }));
    if (path === '/api/m/candles' && P.get('ikey') && KEYS[P.get('ikey')]) return loadBase().then(function () {
      advance(); var tf = P.get('tf') || '5m', sec = /1D/i.test(tf) ? 86400 : /15/.test(tf) ? 900 : /60|1H/i.test(tf) ? 3600 : /^1m/i.test(tf) ? 60 : 300;
      return jres({ symbol: P.get('ikey'), tf: tf, bars: optBars(KEYS[P.get('ikey')], sec), first: null, note: 'sim' });
    });
    return realFetch(input, init);
  };

  /* ---------------- panel ---------------- */
  function hm(ms) { var d = new RealDate(ms + IST); return ('0' + d.getUTCHours()).slice(-2) + ':' + ('0' + d.getUTCMinutes()).slice(-2); }
  function panel() {
    if (document.getElementById('simPanel')) return;
    var css = document.createElement('style');
    css.textContent = '#simPanel{position:fixed;right:12px;bottom:12px;z-index:99999;width:268px;font:12px/1.35 Inter,system-ui,sans-serif;color:#e6e8ee;background:rgba(17,20,30,.96);border:1px solid #f59e0b;border-radius:14px;box-shadow:0 12px 40px rgba(0,0,0,.5);backdrop-filter:blur(8px)}' +
      '#simPanel.min .sbody{display:none}#simPanel .sh{display:flex;align-items:center;gap:8px;padding:9px 11px;cursor:pointer;font-weight:700}#simPanel .sh b{color:#f59e0b;letter-spacing:.06em}#simPanel .sh span{margin-left:auto;font-variant-numeric:tabular-nums}' +
      '#simPanel .sbody{padding:0 11px 11px}#simPanel .sg{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin:6px 0}#simPanel button{font:inherit;padding:6px 4px;border-radius:8px;border:1px solid #3a4052;background:#1d2231;color:#e6e8ee;cursor:pointer}' +
      '#simPanel button.on{background:#f59e0b;color:#111;border-color:#f59e0b;font-weight:700}#simPanel button.x{border-color:#ef4444;color:#ef4444}#simPanel small{color:#8b93a7;display:block;margin-top:6px}' +
      '#simPanel .sr{display:flex;gap:5px;margin:6px 0}#simPanel .sr button{flex:1}#simPanel .sp{height:6px;border-radius:4px;background:#2a3042;overflow:hidden;margin:6px 0}#simPanel .sp i{display:block;height:100%;background:linear-gradient(90deg,#f59e0b,#ef4444)}';
    document.head.appendChild(css);
    var el = document.createElement('div'); el.id = 'simPanel'; if (LS.getItem('sim-min') === '1') el.className = 'min';
    el.innerHTML = '<div class="sh" data-s="min"><b>🧪 SIM</b><em style="color:#8b93a7;font-style:normal" id="simScen"></em><span id="simClk"></span></div><div class="sbody"><div class="sp"><i id="simBar" style="width:0"></i></div>' +
      '<div class="sg">' + Object.keys(SCEN).map(function (k) { return '<button data-sc="' + k + '">' + SCEN[k].label + '</button>'; }).join('') + '</div>' +
      '<div class="sr">' + [[1, 'x1'], [30, 'x30'], [60, 'x60'], [300, 'x300']].map(function (s) { return '<button data-sp="' + s[0] + '">' + s[1] + '</button>'; }).join('') + '<button data-s="pause" id="simPause">Pause</button></div>' +
      '<div class="sr"><button data-s="jump">+30 min</button><button data-s="restart">Restart day</button></div>' +
      '<div class="sr"><button class="x" data-s="exit">Exit sim (restore my data)</button></div>' +
      '<small>Sim prices and a fake clock. Server writes are blocked. Your real data is restored on exit.</small></div>';
    document.body.appendChild(el);
    el.addEventListener('click', function (e) {
      var b = e.target.closest('[data-sc],[data-sp],[data-s]'); if (!b) return;
      if (b.dataset.sc) { rebase(open0, null); stepped = -1; reset(b.dataset.sc); }
      else if (b.dataset.sp) { rebase(simNow(), +b.dataset.sp); try { LS.setItem('sim-speed', b.dataset.sp); } catch (x) { } }
      else if (b.dataset.s === 'min') { el.classList.toggle('min'); try { LS.setItem('sim-min', el.classList.contains('min') ? '1' : '0'); } catch (x) { } }
      else if (b.dataset.s === 'pause') { var t = simNow(); clk.paused = !clk.paused; rebase(t); }
      else if (b.dataset.s === 'jump') { rebase(Math.min(open0 + SESSION * 60000, simNow() + 30 * 60000)); advance(); }
      else if (b.dataset.s === 'restart') { rebase(open0); stepped = -1; reset(M.scen); }
      else if (b.dataset.s === 'exit') { if (confirm('Leave sim mode? Your own saved data is put back.')) { try { LS.removeItem('sim-on'); } catch (x) { } exitSim(); } }
    });
    try { var sp = +LS.getItem('sim-speed'); if (sp) clk.speed = sp; } catch (x) { }
    setInterval(function () {
      advance();
      try { LS.setItem('sim-clock', String(simNow())); } catch (x) { }
      var t = simNow(); document.getElementById('simClk').textContent = hm(t) + ' IST' + (t >= open0 + SESSION * 60000 ? ' · closed' : '');
      document.getElementById('simScen').textContent = SCEN[M.scen].label; document.getElementById('simBar').style.width = (progress() * 100) + '%';
      el.querySelectorAll('[data-sc]').forEach(function (b) { b.classList.toggle('on', b.dataset.sc === M.scen); });
      el.querySelectorAll('[data-sp]').forEach(function (b) { b.classList.toggle('on', +b.dataset.sp === clk.speed); });
      document.getElementById('simPause').textContent = clk.paused ? 'Resume' : 'Pause';
    }, 500);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', panel); else panel();
  window.SIM = { state: M, scenarios: SCEN, now: simNow, rebase: rebase, reset: function (s) { stepped = -1; reset(s); }, exit: exitSim };
  try { var sc = LS.getItem('sim-scen'); if (sc && SCEN[sc]) M.scen = sc; } catch (e) { }
})();
