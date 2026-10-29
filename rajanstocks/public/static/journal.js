window.rjMkt=window.rjMkt||function(){try{const n=new Date(new Date().toLocaleString('en-US',{timeZone:'Asia/Kolkata'})),m=n.getHours()*60+n.getMinutes(),d=n.getDay();return d>0&&d<6&&m>=555&&m<=945}catch(e){return true}};   /* weekdays 09:15-15:45 IST: background refreshes only then */
/* Rajan Algo — Paper-Trading Journal (replaces the old Journal + Portfolio screens)
   Implements "Trading Strategy & Indicator Validation BRD" v1.0 + TradeLab UI specification.
   Everything here is a SIMULATION: no broker orders are ever sent.
   Storage: this browser (localStorage). The BRD notes production needs server-side persistence/audit. */
(function () {
  'use strict';
  const KEY = 'rj-journal-v1', SKEY = 'rj-journal-settings-v1';
  const DEFAULTS = {
    capital: 1000000, maxTrades: 5, riskPct: 0.5, dailyLossPct: 2, maxOpen: 1, minRR: 2,
    cost: 0, slip: 0, t1: 1, t2: 2, t3: 3, allowOverride: true,
    labTrigger: 1, labStep: 0.5, labTrail: 1,
  };
  const MARKETS = ['Equity Intraday', 'Index', 'Options', 'Futures', 'Other'];
  const TSL_MODES = ['Off / Fixed SL', 'Breakeven', 'Step Trail', 'Distance Trail', 'ATR-style (manual)'];
  const EXIT_TYPES = ['SL', 'TSL', 'T1', 'T2', 'T3', 'Manual Exit', 'Time Exit', 'Breakeven'];
const TABS = [['portfolio', 'Portfolio'], ['positions', 'Positions'], ['algo', 'Algo'], ['picklog', 'Picks log'], ['stocks', 'Stock trader']];
   const GROUPS = {};
   const TAB_TIPS = { picklog: 'What every pick hit today and on earlier days: SL 🚫 stop-loss hit, T1/T2 ✅ targets reached', new: 'Log a manual paper trade: entry price, SL, target, quantity - R:R and risk budget calculated for you', portfolio: 'Equity, P&L, stats and quick actions', positions: 'Current positions with SL, Target, Entry, Exit, Current Price, Exit Button', algo: 'Auto trading status, exits and trade outcomes', stocks: 'Stock paper trader - its own Rs 10 L, intraday / swing / positional' };
  const parentOf = k => Object.keys(GROUPS).find(g => GROUPS[g].some(([sk]) => sk === k)) || k;
  const effTab = () => GROUPS[ui.tab] ? ui.sub[ui.tab] : ui.tab;

  const load = (k, d) => { try { const v = JSON.parse(localStorage.getItem(k)); return v == null ? d : v; } catch (e) { return d; } };
  const save = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { } };
  let S = Object.assign({}, DEFAULTS, load(SKEY, {}));
  if (S.capV !== 202610282) { if (S.capital === 1500000) S.capital = 1000000; S.capV = 202610282; save(SKEY, S); }      // 28 Oct 2026: option buying paper money is Rs 10 L (the share trader has its own Rs 5 L)
    let T = load(KEY, []);
  /* fresh start: from 28 Oct 2026 the books begin at zero - drop journal trades created before 09:00 that morning (nothing newer is touched) */
  (function freshStart() {
    const CUT = Date.parse('2026-10-29T12:10:00+05:30'); if (Date.now() < Date.parse('2026-10-29T12:05:00+05:30') || navigator.webdriver) return;   // (automated test browsers keep their fixtures)
    const old = t => { const ts = t && (t.ts || Date.parse(t.at || t.openedAt || t.created || '')); return isFinite(ts) ? ts < CUT : String((t && (t.date || t.day)) || '') <= '2026-10-28'; };
    const n = T.length; T = T.filter(t => !old(t)); if (T.length !== n) save(KEY, T);
    try { ['mer-trades', 'mer-paper'].forEach(k => { const v = JSON.parse(localStorage.getItem(k) || '[]'); if (Array.isArray(v) && v.length) { const w = v.filter(x => !old(x)); if (w.length !== v.length) localStorage.setItem(k, JSON.stringify(w)); } }); localStorage.removeItem('rj-cap-peak'); if (!localStorage.getItem('rs-fresh-1029')) { localStorage.setItem('rs-fresh-1029', '1'); ['rs-today-total', 'rs-last-pnl'].forEach(k => localStorage.removeItem(k)); } } catch (e) { }
  })();
  const REMOVED_IDS = new Set(['27', '1004', '1009', 'TR-0027', 'TR-1004', 'TR-1009', 'PT|1004', 'PT|1009', 'PT|27', 'P|1004', 'P|1009', 'P|27']);
  const REMOVED_UNTIL = '2026-10-25';                    // untimed trades dated on/before this day
  const REMOVED_BEFORE_MS = Date.parse('2026-10-26T13:30:00+05:30');   // removal was requested ~13:26 IST: anything created after is real
  const isRemovedId = t => {
    if (!t) return false;
    const rawId = String(t.id || '');
    if (rawId.startsWith('P|')) return REMOVED_IDS.has(rawId);   // open paper position ids embed the contract name (NIFTY 22900 PE 27 Oct): the digits are strike/expiry, not a trade number
    const m = rawId.match(/\d+/g);                 // A-1023-27-W -> 27 (shortId is declared later, so not used here)
    if (!REMOVED_IDS.has(rawId) && !(m && REMOVED_IDS.has(m[m.length - 1]))) return false;
    const e = rawId.match(/(?<!\d)(20\d{2})-?(\d{2})-?(\d{2})(?!\d)/);     // dated: a later trade that reuses the number is real
    const ts = t.ts || (t.at ? Date.parse(t.at) : NaN);
    if (isFinite(ts)) return ts < REMOVED_BEFORE_MS;
    const day = String(t.date || t.day || '') || (e ? e[1] + '-' + e[2] + '-' + e[3] : '');
    return !day || day <= REMOVED_UNTIL;
  };
  // One-off purge of the removed trade IDs from this browser's stored journal / paper data
  (function purgeRemovedIds() {
    const PURGE_KEY = 'rj-purge-removed-ids-v1';
    try {
      if (localStorage.getItem(PURGE_KEY)) return;
      T = T.filter(t => !isRemovedId(t));
      save(KEY, T);
      const strip = (k, fn) => {
        const arr = JSON.parse(localStorage.getItem(k) || '[]');
        if (!Array.isArray(arr) || !arr.length) return null;
        const out = arr.filter(fn);
        localStorage.setItem(k, JSON.stringify(out));
        return out;
      };
      const pt = strip('mer-trades', t => !isRemovedId(t));
      if (pt && typeof App !== 'undefined') App.trades = pt;
      localStorage.setItem(PURGE_KEY, 'done');
    } catch (e) { }
  })();
  /* Automated trades (server side) are mirrored into the journal with every field filled in: plan, indicator evidence,
     exit, costs, R multiple and review. They are read-only and do not count toward the manual 5-a-day / loss limits. */
  const AUTO = { list: [], ts: 0, busy: false };
  const EXIT_MAP = { STOP: 'SL', TSL: 'TSL', MANUAL: 'Manual Exit', TARGET: 'T2', TIME: 'Time Exit', EXPIRY: 'Time Exit', REVERSE: 'Reversal', BREAKEVEN: 'Breakeven', 'SQUARE-OFF': 'Time Exit', 'SPREAD-STOP': 'SL', 'SPREAD-T1': 'T2', 'SPREAD-EXPIRY': 'Time Exit' };
  /* what the robot closed a trade for, in plain words. Only a real MANUAL close says "Manual Exit": anything the robot decided (a reversal, breakeven stop,
     late square-off ...) used to fall through to "Manual Exit" and looked as if the user had exited it. */
  const exitLabel = r => { r = String(r || '').trim(); if (!r) return 'Manual Exit'; if (EXIT_MAP[r]) return EXIT_MAP[r]; if (/^SQUARE-OFF/i.test(r)) return 'Time Exit'; return r.charAt(0) + r.slice(1).toLowerCase(); };
  function mapAuto(a) {
    const d = a.openedAt ? new Date(a.openedAt) : new Date(a.date + 'T09:20:00+05:30');
    // premium at risk per unit: from the server plan (delta 0.5 x the indicator's stop, capped at 30% of the premium)
    const riskP = a.premRisk > 0 ? a.premRisk : Math.max(0.05, Math.min(0.5 * (a.riskU || 0), 0.3 * a.entry));
    const inds = (a.indicators && a.indicators.length ? a.indicators : [a.strategy]).filter(Boolean);
    const closed = a.status === 'CLOSED', sh = a.pos === 'short', k = sh ? -1 : 1;   // sold option: stop above, targets below the entry
    const t = {
      id: a.id, auto: true, date: a.date, time: istTime(d), at: d.toISOString(), market: 'Options', instrument: a.sym,
      symbol: `${a.sym} ${Number(a.strike).toFixed(0)} ${a.opt} ${a.expiry}`, dir: sh ? 'Short' : 'Long',
      setup: a.source || a.strategy, tf: '1D', ind: inds.join(', '), entry: a.entry,
      sl: a.premSL > 0 ? +(+a.premSL).toFixed(2) : +(a.entry - k * riskP).toFixed(2), sl0: +(a.entry - k * riskP).toFixed(2),
      t1: +Math.max(0.05, a.entry + k * (a.tgts ? 1.5 : 1) * riskP).toFixed(2), t2: +Math.max(0.05, a.entry + k * 2 * riskP).toFixed(2), t3: +Math.max(0.05, a.entry + k * 3 * riskP).toFixed(2),   /* ladder trades: 1.5R / 2R / 3R shown here, T4-T7 (4R 5R 6R 10R) in the plan text */
      qty: a.lots, mult: a.lot, initRisk: a.initialRisk, raw: a,
      tsl: a.tsl ? ({ trail: 'Distance Trail', breakeven: 'Breakeven', step: 'Step Trail' }[a.tsl.mode] || 'Off / Fixed SL') : (a.variant === 'trail' ? 'Distance Trail' : 'Off / Fixed SL'),
      why: `Auto-executed ${sh ? 'SELL of the ' + (a.opt === 'PE' ? 'put' : 'call') + ' (paired with ' + a.pairOf + ')' : (a.side === 'BUY' ? 'call' : 'put')} on ${a.sym}: ${inds.length} indicator(s) — ${inds.join(', ')}. ` +
           `Underlying entry ${a.entryU}, stop ${a.stopU}${a.tgts ? '. Targets (underlying): ' + a.tgts.map((x, i) => 'T' + (i + 1) + ' ' + x).join(' · ') + ' = 1.5R 2R 3R 4R 5R 6R 10R; the stop trails one target behind' : a.targetU ? ', target ' + a.targetU : ', trailing exit'}.`,
      status: closed ? 'Closed' : 'Open', exits: [], hits: [], hitOrder: [], stops: [{ at: a.openedAt || d.toISOString(), from: null, to: a.stopU, note: 'underlying stop at entry' }],
      rule: (a.initialRisk || 0) > S.capital * S.riskPct / 100 + 1e-9 ? 'Partial' : 'Yes', emotion: 'Automated',
      mistakes: (a.initialRisk || 0) > S.capital * S.riskPct / 100 + 1e-9 ? 'Risk above budget (1-lot minimum)' : '', reviewer: '', ref: '', created: a.openedAt,
      plan: { entry: a.entry, sl: a.stopU, qty: a.lots }, unrl: a.unrealised,
    };
    if (closed) {
      const ex = a.closedAt ? new Date(a.closedAt) : d, type = exitLabel(a.exitReason);
      t.exits = [{ qty: a.lots, price: a.exit, type, date: istDay(ex), time: istTime(ex) }];
      t.exitType = type; t.costOverride = a.cost || 0; t.slipOverride = 0;
      if (type === 'T2') { t.hits = ['T1', 'T2']; t.hitOrder = ['T1', 'T2']; }
      if (a.tgts && a.tHit) { const hh = ['T1', 'T2', 'T3'].slice(0, Math.min(3, a.tHit)); t.hits = hh; t.hitOrder = hh.slice(); }
      t.reviewed = true;
      t.lesson = `Automated. Exit: ${a.exitReason}. Net ${a.net >= 0 ? '+' : ''}₹${Math.round(a.net)}${a.R != null ? ' (' + (a.R >= 0 ? '+' : '') + a.R + 'R)' : ''}. ` +
                 (t.rule === 'Yes' ? 'Within the per-trade risk budget; stop set.' : `Stop set, but one lot risks about ₹${Math.round(a.initialRisk)} - above the ₹${Math.round(S.capital * S.riskPct / 100)} budget (1-lot minimum).`);
    } else { t.reviewed = false; t.lesson = ''; if (a.tgts && a.tHit) { const hh = ['T1', 'T2', 'T3'].slice(0, Math.min(3, a.tHit)); t.hits = hh; t.hitOrder = hh.slice(); } }
    return t;
  }
  /* ---------- live prices for the open option trades ----------
     /api/auto/status only marks to market every couple of minutes and serves a cached copy, so the LTP on the table (and on the exit
     screen) could sit still for minutes and then jump. /api/auto/live is a read-only quote of the open contracts (last, bid, ask and the
     price an exit books); it is polled while the Journal is on screen and every 3 s while an exit screen is open. */
  AUTO.q = {}; AUTO.qTs = 0; AUTO.qOk = true;
  async function pullLive(force) {
    if (AUTO.qBusy) return;
    if (!force && (document.hidden || Date.now() - AUTO.qTs < 2500)) return;
    AUTO.qBusy = true;
    try {
      const r = await fetch('/api/auto/live', { cache: 'no-store' });
      if (!r.ok) { AUTO.qOk = false; return; }
      const d = await r.json();
      if (!d.ok) { AUTO.qOk = false; return; }
      const m = {}; (d.trades || []).forEach(x => { m[x.id] = x; });
      AUTO.q = m; AUTO.qTs = Date.now(); AUTO.qOk = true;
      applyLive();
    } catch (e) { AUTO.qOk = false; }
    finally { AUTO.qBusy = false; }
  }
  /* put the live quote into the trade (price AND open P&L together, so the table, the cost estimate and the day total agree) - never an older one over a newer one */
  function applyLive() {
    AUTO.list.forEach(t => {
      const q = AUTO.q[t.id]; if (!q || t.status === 'Closed' || !(q.ltp > 0) || !t.raw) return;
      if (t.raw.lastAt && q.at && q.at < t.raw.lastAt) return;
      t.raw.last = q.ltp; t.raw.lastAt = q.at;
      if (q.mark > 0) t.raw.mark = q.mark;
      if (typeof q.unrealised === 'number') { t.unrl = q.unrealised; t.raw.unrealised = q.unrealised; }
    });
  }
  const liveAgeS = () => AUTO.qTs ? Math.round((Date.now() - AUTO.qTs) / 1000) : null;
  async function syncAuto(force) {
    /* server load: the status read runs a mark-to-market (and, in market hours, an auto-trade cycle) - every 10 s on every screen was the biggest
       single user of Vercel Active CPU. Now: not at all from a hidden tab, every 20 s while the Journal is on screen, every 60 s elsewhere. */
    const jv = document.getElementById('v-journal'), nw = new Date(new Date().toLocaleString('en-US', { timeZone: 'Asia/Kolkata' })), mm = nw.getHours() * 60 + nw.getMinutes();
    const opening = mm >= 556 && mm <= 559;          // 09:16-09:19: buying starts at 09:16 - poll faster on any screen, even a background tab
    const every = opening ? 25000 : jv && jv.offsetParent ? 20000 : 60000;
    if (AUTO.busy || (!force && ((document.hidden && !opening) || Date.now() - AUTO.ts < every))) return;
    AUTO.busy = true;
    const stBefore = JSON.stringify([AUTO.srv || null, !!AUTO.err]);
    try {
      const [r, rStock] = await Promise.all([
        fetch('/api/auto/status', { cache: 'no-store' }).catch(() => null),
        (AUTO.srv && AUTO.srv.cfg && AUTO.srv.cfg.stockTrader === false) ? Promise.resolve(null) : fetch('/api/stockbot/status', { cache: 'no-store' }).catch(() => null)     // the share trader is off: nothing to read
      ]);
      /* a redraw only when the list itself changes (new trade, exit, status); live prices / P&L are patched in place by refreshLive -
         a price tick used to redraw the whole table every sync (the open trades kept "refreshing") */
      const shapeA = () => JSON.stringify(AUTO.list.map(x => [x.id, x.status, x.exitType, x.entry]));
      const shapeS = () => JSON.stringify((AUTO.stockTrades || []).map(x => [x.id, x.status]));
      const pricesA = () => JSON.stringify(AUTO.list.map(x => [(x.raw && x.raw.last) || x.entry, x.unrl]).concat((AUTO.stockTrades || []).map(x => [x.last, x.unrealised])));
      let before = shapeA(), beforeStock = shapeS(), beforePx = pricesA();
      if (r && r.ok) {
        const a = await r.json();
        AUTO.cand = a.cand || null;
        const prevA = {}; AUTO.list.forEach(x => { prevA[x.id] = x; });
        AUTO.list = (a.open || []).concat(a.closed || []).map(mapAuto);
        /* different serverless instances answer with different cached copies: a reply whose price is OLDER than the one already
           shown for an open trade is ignored for that trade, so P&L does not swing back and forth between instances */
        AUTO.list.forEach(n => {
          const p = prevA[n.id], pa = p && p.raw && p.raw.lastAt, na = n.raw && n.raw.lastAt;
          if (p && n.status !== 'Closed' && p.status !== 'Closed' && pa && na && na < pa) {
            n.unrl = p.unrl; n.raw.last = p.raw.last; n.raw.unrealised = p.raw.unrealised; n.raw.lastAt = pa;
          }
        });
        /* "stop moved" message in the app (user 29 Oct: it used to appear while using the app, on any screen): once for every new lock step of a running auto trade */
        try {
          const KS = 'rs-lock-seen'; const first = localStorage.getItem(KS) === null; const seenL = JSON.parse(localStorage.getItem(KS) || '{}'); let ch = false;
          AUTO.list.forEach(n => {
            const lk = n.status !== 'Closed' && n.raw && n.raw.lock; if (!lk) return;
            const sig = lk.mode + '|' + lk.keep; if (seenL[n.id] === sig) return;
            seenL[n.id] = sig; ch = true;
            if (!first && typeof toast === 'function') toast(`${n.symbol}: profit ₹${Math.round(lk.best || 0).toLocaleString('en-IN')} - stop moved to ${n.raw.premSL} (${lk.keep ? 'locks ₹' + Math.round(lk.keep).toLocaleString('en-IN') : 'breakeven'})`, 'ok');
          });
          if (ch || first) localStorage.setItem(KS, JSON.stringify(seenL));
        } catch (e) { }
        AUTO.srv = { enabled: !!(a.cfg && a.cfg.enabled), marketOpen: !!a.marketOpen, todayCount: a.todayCount || 0, dayPnl: a.dayPnl || null, sleeves: a.sleeves || [], cfg: { buyOnly: !!(a.cfg && a.cfg.buyOnly), stockOnly: !!(a.cfg && a.cfg.stockOnly), stockTrader: !(a.cfg && a.cfg.stockTrader === false) } };
        AUTO.err = false;
        AUTO.ts = Date.now();
      } else {
        AUTO.err = true;
      }
      if (rStock && rStock.ok) {
        const sb = await rStock.json();
        AUTO.stockTrades = (sb.open || []).concat(sb.closed || []).map(s => {
          const isClosed = s.status === 'CLOSED';
          return {
            id: s.id || ('stk_' + s.sym), auto: true, isStock: true,
            date: (s.openedAt || '').slice(0, 10) || today(),
            time: (s.openedAt || '').slice(11, 16) || '09:30',
            market: 'Equity ' + (s.hz ? s.hz.charAt(0).toUpperCase() + s.hz.slice(1) : 'Positional'),
            instrument: s.sym, symbol: s.sym, dir: s.side === 'SELL' ? 'Short' : 'Long',
            setup: (s.hz || 'positional') + ' stock pick', hz: s.hz || 'positional', tf: '1D',
            entry: s.entry, sl: s.stop, sl0: s.stop, t1: s.t1, t2: s.t2, qty: s.qty,
            last: s.last || s.exit || s.entry, status: isClosed ? 'Closed' : 'Open',
            exitType: (s.exitReason || s.exitWhy) ? exitLabel(s.exitReason || s.exitWhy) : '',
            raw: s, holdSessions: s.holdSessions || 0, net: s.net || 0, R: s.R || 0
          };
        });
      }
      const changed = shapeA() !== before || shapeS() !== beforeStock;
      const pxMoved = pricesA() !== beforePx;
      const ok = document.getElementById('v-journal') && !document.querySelector('.modal-bg');
      if (ok && changed && ['portfolio', 'positions', 'algo', 'stocks'].includes(effTab())) render();
      else if (ok && pxMoved && ['algo', 'stocks'].includes(effTab())) render();        // these two have no in-place price updater
      else if (ok && pxMoved) refreshLive();
    } catch (e) {
      AUTO.err = true;
    }
    AUTO.ts = Date.now();
    AUTO.busy = false;
    if (!AUTO.qTs && AUTO.list.some(t => t.status !== 'Closed')) pullLive(true).then(refreshLive);          // first look: live prices at once after a refresh, not at the next tick
    if (JSON.stringify([AUTO.srv || null, !!AUTO.err]) !== stBefore && effTab() === 'algo' && document.getElementById('v-journal') && !document.querySelector('.modal-bg')) render();
  }
  const EXIT_SRC = { TP: 'T2', SL: 'SL', TSL: 'TSL', manual: 'Manual Exit', limit: 'Limit order', stop: 'Stop order', hedge: 'Hedge closed' };
  function lockTxt(p) { return p && p.lock ? (p.lock.mode === 'trail' ? `Auto trail · locks ₹${Math.round(p.lock.keep).toLocaleString('en-IN')}` : 'Auto · breakeven') : ''; }
    /* Market of a manual paper trade, from what was actually traded: an option (CE/PE contract) -> Options,
     an index spot/futures symbol -> Index, anything else -> a stock (Equity Intraday). */
  const paperMarket = (sym, m) => {
    m = m || {};
    if (/\b(CE|PE)\b/.test(sym || '') || m.cls === 'Options' || m.ikey) return 'Options';
    let e = null;
    try { e = (typeof SYM === 'function' && SYM(sym)) || (typeof SYMS !== 'undefined' && SYMS.find(x => x.s === sym)) || null; } catch (x) { }
    if (m.sec === 'Index' || (e && (e.sec === 'Index' || e.cls === 'Indices' || e.cls === 'Index'))) return 'Index';
    return 'Equity Intraday';
  };
function paperList() {
    if (typeof App === 'undefined') return [];
    const out = [];
    const sigOf = m => (m && m.sig) ? m.sig : null;
    (App.positions || []).forEach(p => {
      if (!p || !p.q) return;
      const L = p.q > 0, m = (App.meta || {})[p.sym] || {}, sg = sigOf(m);
      const isOpt = /\b(CE|PE)\b/.test(p.sym) || (m && m.cls === 'Options');
      const mult = 1; // paper positions from Trade screen are already scaled in exact unit quantities
      const tAtStr = p.t ? istTime(new Date(p.t)) : istTime(new Date());
      out.push({
        id: 'P|' + p.sym, paper: true, symbol: p.sym, instrument: m.und || p.sym, dir: L ? 'Long' : 'Short', entry: p.avg, qty: Math.abs(p.q), mult,
        sl: p.sl || null, sl0: p.sl || p.avg, t2: p.tp || null, initRisk: p.sl ? Math.abs(p.avg - p.sl) * Math.abs(p.q) * mult : 0, status: 'Open', exits: [],
        date: p.day || today(), time: tAtStr, market: paperMarket(p.sym, m), sig: sg ? sg.name + ' · ' + sg.dir.toUpperCase() : null,
        setup: sg ? `Signal ${sg.name} · test ${sg.dir.toUpperCase()}` : L ? 'Trade screen · buy' : 'Trade screen · sell (write)',
        tsl: lockTxt(p) || (p.tsl ? `${p.tsl.v}${p.tsl.u === 'abs' ? ' ₹' : '%'} trail` : 'Off / Fixed SL'), pos: p
      });
    });
    (App.trades || []).forEach(x => {
      if (!(x.closeQty > 0) && !x.realized && x.posAfter !== 0) return;
      const m = x.meta || (App.meta || {})[x.sym] || {};
      const ty = EXIT_SRC[x.src] || (x.src === 'manual' ? 'Manual Exit' : x.src) || 'Manual Exit', sg = sigOf(m);
      const isOpt = x.kind === 'option' || /\b(CE|PE)\b/.test(x.sym) || (m && m.cls === 'Options');
      const mult = 1; // paper trades from Trade screen are already in exact unit quantities
      const entryPx = x.avgBefore > 0 ? x.avgBefore : (x.price || 0);
      const qtyVal = x.closeQty > 0 ? x.closeQty : (x.qty || 1);
      const dirVal = x.side === 'sell' ? 'Long' : 'Short';
      const tAtStr = x.t ? istTime(new Date(x.t)) : '';
      out.push({
        id: 'PT|' + x.id, ts: x.t, paper: true, symbol: x.sym, instrument: x.und || m.und || x.sym, dir: dirVal, entry: entryPx, qty: qtyVal, mult,
        sl: null, sl0: entryPx, initRisk: 0, status: 'Closed', date: x.day || istDay(x.t || Date.now()), time: tAtStr,
        market: x.kind === 'option' ? 'Options' : paperMarket(x.sym, m),
        sig: sg ? sg.name + ' · ' + sg.dir.toUpperCase() : null,
        setup: sg ? `Signal ${sg.name} · test ${sg.dir.toUpperCase()}` : dirVal === 'Long' ? 'Trade screen · buy' : 'Trade screen · sell (write)',
        exits: [{ qty: qtyVal, price: x.price, type: ty, date: x.day || today(), time: tAtStr }],
        exitType: ty, costOverride: x.charges || 0, slipOverride: 0, reviewed: true, tsl: ''
      });
    });
    return out;
  }
  const allTrades = () => T.concat(AUTO.list, (AUTO.stockTrades || []), paperList()).filter(t => !isRemovedId(t));
  async function jpost(url, body) {
    try {
      const ac = new AbortController(), to = setTimeout(() => ac.abort(), 45000);      /* never leave a button spinning forever */
      const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}), signal: ac.signal });
      clearTimeout(to);
      const d = await r.json().catch(() => ({}));
      return r.ok ? { ok: true, d } : { ok: false, err: d.detail || ('Request failed (' + r.status + ')') };
    } catch (e) { return { ok: false, err: e && e.name === 'AbortError' ? 'The server took too long - try again.' : 'No internet connection.' }; }
  }
  const ui = { tab: 'portfolio', sub: { analysis: 'strategy', config: 'auto' }, f: { from: '', to: '', market: '', inst: '', setup: '', dir: '', exit: '', rule: '', src: '' }, sel: null, lab: null, labBusy: false };

  /* ---------- helpers ---------- */
  const E = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const num = v => { const n = parseFloat(v); return isFinite(n) ? n : null; };
  const inr = (n, d = 2) => (n < 0 ? '−' : '') + '₹' + Math.abs(n).toLocaleString('en-IN', { minimumFractionDigits: d, maximumFractionDigits: d });
  const inrL = n => '₹' + (n / 100000).toLocaleString('en-IN', { maximumFractionDigits: 1 }) + ' L';
  const sinr = n => (n >= 0 ? '+' : '−') + '₹' + Math.abs(n).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const px = n => (n == null || !isFinite(n)) ? '—' : n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  const rr = n => (n == null || !isFinite(n)) ? '—' : (n >= 0 ? '+' : '−') + Math.abs(n).toFixed(2) + 'R';
  const istDay = d => new Date((d instanceof Date ? d : new Date(d)).getTime() + 330 * 60000).toISOString().slice(0, 10);
  const today = () => istDay(new Date());
  const istTime = d => new Date(d.getTime() + 330 * 60000).toISOString().slice(11, 16);
  const toast_ = (m, k) => { try { window.toast ? window.toast(m, k) : alert(m); } catch (e) { } };
  const dirOf = t => (t.dir === 'Short' ? -1 : 1);
  const persist = () => save(KEY, T);
  const persistS = () => save(SKEY, S);
  const live = sym => {
    try {
      if (!sym) return null;
      if (typeof SYM === 'function') {
        const s = SYM(String(sym)) || SYM(String(sym).toUpperCase());
        if (s && s.last > 0) return s.last;
      }
      if (typeof App !== 'undefined' && Array.isArray(App.positions)) {
        const p = App.positions.find(x => x.sym === sym);
        if (p) {
          const s = typeof SYM === 'function' && SYM(p.sym);
          if (s && s.last > 0) return s.last;
          if (typeof p.last === 'number' && p.last > 0) return p.last;
        }
      }
      return null;
    } catch (e) { return null; }
  };
  const nextId = () => 'TR-' + String(T.reduce((m, t) => Math.max(m, parseInt(String(t.id).slice(3), 10) || 0), 0) + 1).padStart(4, '0');

  /* ---------- calculation engine (BRD section 7) ---------- */
  const units = t => (t.mult || 1);
  const exitedQty = t => (t.exits || []).reduce((a, l) => a + l.qty, 0);
  function statusOf(t) {
    if (t.status === 'Cancelled' || t.status === 'Planned') return t.status;
    const q = exitedQty(t);
    return q >= t.qty ? 'Closed' : q > 0 ? 'Partial' : 'Open';
  }
  function initialRisk(t) { return t.initRisk > 0 ? t.initRisk : Math.abs(t.entry - t.sl0) * t.qty * units(t); }       // frozen: uses the ORIGINAL stop
  function calc(t) {
    const m = units(t), d = dirOf(t);
    let gross = 0, qx = 0;
    (t.exits || []).forEach(l => { gross += d * (l.price - t.entry) * l.qty * m; qx += l.qty; });
    const costs = t.costOverride != null ? t.costOverride : S.cost * m * qx;
    const slipv = t.slipOverride != null ? t.slipOverride : S.slip * m * qx;
    const net = gross - costs - slipv, risk = initialRisk(t);
    return { gross, costs, slip: slipv, net, risk, R: risk > 0 && qx > 0 ? net / risk : null, qx };
  }
  /* A price that is missing for a moment (live quote not in yet, server copy mid-refresh) must not make a position's P&L vanish
     (it was summed as 0, so the day total jumped between plus and minus): keep the last good figure for every open trade. */
  const UNR_LAST = {};
  function unrealised(t) {
    const k = String(t.id), v = unrealisedRaw(t);
    if (statusOf(t) === 'Closed' || t.status === 'Planned' || t.status === 'Cancelled') { delete UNR_LAST[k]; return null; }
    if (typeof v === 'number' && isFinite(v)) { UNR_LAST[k] = v; return v; }
    return Object.prototype.hasOwnProperty.call(UNR_LAST, k) ? UNR_LAST[k] : null;
  }
  /* Open P&L is shown AFTER the estimated cost of closing the trade now, so it matches the booked P&L it turns into
     (booked results are net of costs; open ones used to be gross, so a small open profit could close as a loss).
     Server trades use the same costPct x (entry + exit) x qty the server charges on exit; manual trades use the Settings
     cost + slippage per unit on the remaining qty (as calc() does); Trade-screen paper positions use the app's charge table. */
  function exitCostEst(t) {
    try {
      if (statusOf(t) === 'Closed' || t.status === 'Planned' || t.status === 'Cancelled') return 0;
      const rem = t.qty - exitedQty(t);
      if (t.auto) {
        const pct = t.raw && Number(t.raw.costPctEff);
        if (!(pct >= 0)) return 0;
        const cur = t.isStock ? curPx(t) : ((t.raw && t.raw.last) || t.entry);
        return pct / 100 * ((t.entry || 0) + (cur || 0)) * rem * units(t);
      }
      if (t.paper) {
        if (typeof calcCharges !== 'function' || typeof kindOf !== 'function') return 0;
        const s = (typeof SYM === 'function' && SYM(t.symbol)) || {}, cur = curPx(t) || t.entry;
        return calcCharges(kindOf(s), dirOf(t) > 0 ? 'sell' : 'buy', rem * cur).total || 0;
      }
      return (S.cost + S.slip) * units(t) * rem;
    } catch (e) { return 0; }
  }
  function unrealisedNet(t) { const u = unrealised(t); return u == null ? null : +(u - exitCostEst(t)).toFixed(2); }
  function unrealisedRaw(t) {
    if (statusOf(t) === 'Closed' || t.status === 'Planned' || t.status === 'Cancelled') return null;
    if (t.isStock) {
      const l = live(t.symbol || t.instrument);
      if (l != null && t.entry > 0) {
        return +(dirOf(t) * (l - t.entry) * (t.qty || 1) * units(t)).toFixed(2);
      }
      return typeof t.unrl === 'number' ? t.unrl : (t.raw && typeof t.raw.unrealised === 'number' ? t.raw.unrealised : null);
    }
    if (t.auto) return typeof t.unrl === 'number' ? t.unrl : (t.raw && typeof t.raw.unrealised === 'number' ? t.raw.unrealised : null);
    const l = live(t.symbol || t.instrument); if (l == null) return null;
    const rem = t.qty - exitedQty(t);
    return dirOf(t) * (l - t.entry) * rem * units(t);
  }
  const entered = t => t.status !== 'Planned' && t.status !== 'Cancelled';
  const closedTrades = () => T.filter(t => entered(t) && statusOf(t) === 'Closed');
  const realised = () => T.reduce((a, t) => a + (entered(t) ? calc(t).net : 0), 0);
  const equity = () => S.capital + realised();
  const budget = () => equity() * S.riskPct / 100;
  /* today's max drawdown: the biggest fall of today's P&L from its high so far - trades closed today in exit order, then the open
     positions' current P&L as the latest point. Starts from 0 every morning (the all-time figure never came down). */
  function dayDD(day) {
    const exitDay = t => ((t.exits || []).slice(-1)[0] || {}).date || (t.closedAt || '').slice(0, 10) || t.date;
    const closed = allTrades().filter(t => entered(t) && statusOf(t) === 'Closed' && exitDay(t) === day)
      .sort((a, b) => lastExit(a).localeCompare(lastExit(b)));
    let cum = 0, peak = 0, dd = 0;
    closed.forEach(t => { cum += calc(t).net || 0; peak = Math.max(peak, cum); dd = Math.max(dd, peak - cum); });
    const unr = allTrades().filter(t => entered(t) && statusOf(t) !== 'Closed').reduce((a, t) => a + (unrealisedNet(t) || 0), 0);
    return Math.max(dd, peak - (cum + unr));
  }
  function dayStats(day) {
    let entries = 0, pnl = 0, unr = 0, unrNet = 0, open = 0;   // unr = gross (the daily-loss-limit check uses it, unchanged); unrNet = after estimated exit costs (what is shown)
    allTrades().filter(t => !t.auto).forEach(t => {
      if (!entered(t)) return;
      if (t.date === day) entries++;
      const u = unrealised(t); if (u != null) { unr += u; unrNet += unrealisedNet(t) || 0; }
      if (statusOf(t) !== 'Closed') open++;
      (t.exits || []).forEach(l => { if (l.date === day) pnl += dirOf(t) * (l.price - t.entry) * l.qty * units(t) - (t.costOverride != null ? t.costOverride : (S.cost + S.slip) * units(t) * l.qty); });
    });
    return { entries, pnl, unr, unrNet, open };
  }
  function startOfDayEquity(day) {
    let p = 0;
    T.forEach(t => { if (!entered(t)) return; (t.exits || []).forEach(l => { if (l.date < day) p += dirOf(t) * (l.price - t.entry) * l.qty * units(t) - (S.cost + S.slip) * units(t) * l.qty; }); });
    return S.capital + p;
  }

  /* ---------- trade validation (FR-03/04/05, section 10) ---------- */
  function validate(f, opts) {
    const errs = [], warns = [], d = f.dir === 'Short' ? -1 : 1, m = f.mult || 1;
    if (!f.setup) f.setup = 'Manual';                                  // optional on the simple form
    [['date', 'date'], ['market', 'market'], ['instrument', 'stock / index'], ['dir', 'buy / sell']].forEach(([k, l]) => { if (!f[k]) errs.push('Missing: ' + l); });
    if (!(f.entry > 0)) errs.push('Entry price is required.');
    if (!(f.sl > 0)) errs.push('Stop-loss is mandatory.');
    if (f.entry > 0 && f.sl > 0) {
      if (Math.abs(f.entry - f.sl) <= 0) errs.push('Stop distance is zero — stop-loss cannot equal entry.');
      else if (d * (f.entry - f.sl) <= 0) errs.push(`For a ${f.dir.toLowerCase()} trade the stop-loss must be ${d > 0 ? 'below' : 'above'} entry.`);
    }
    if (!(f.qty >= 1) || Math.floor(f.qty) !== f.qty) errs.push('Quantity must be a whole number of shares / lots (≥ 1).');
    const bud = budget(), hasStop = f.entry > 0 && f.sl > 0 && Math.abs(f.entry - f.sl) > 0;
    const perUnit = hasStop ? Math.abs(f.entry - f.sl) * m + (S.cost + S.slip) * m : 0;
    const sugg = perUnit > 0 ? Math.floor(bud / perUnit) : 0;
    const risk = f.entry > 0 && f.sl > 0 && f.qty > 0 ? Math.abs(f.entry - f.sl) * f.qty * m : 0;
    const overBudget = risk > bud + 1e-9;
    if (hasStop && sugg < 1) errs.push('Not permitted: risk budget ' + inr(bud, 0) + ' cannot fund even one unit at this stop distance.');
    const tgt = f.t2 || f.t3 || f.t1;
    const plannedRR = tgt && f.entry && f.sl && Math.abs(f.entry - f.sl) > 0 ? Math.abs(tgt - f.entry) / Math.abs(f.entry - f.sl) : null;
    if (tgt && d * (tgt - f.entry) <= 0) errs.push('Targets must be on the profit side of entry.');
    if (plannedRR != null && plannedRR < S.minRR) warns.push(`Planned R:R ${plannedRR.toFixed(2)} is below the minimum ${S.minRR}:1 — needs an override reason.`);
    const blocks = [];
    if (opts && opts.recording) {
      const ds = dayStats(f.date), sod = startOfDayEquity(f.date), lim = sod * S.dailyLossPct / 100;
      // no daily trade limit any more
      if (ds.pnl + ds.unr <= -lim) blocks.push(`Daily loss limit reached (${sinr(ds.pnl + ds.unr)} ≤ −${inr(lim, 0)}).`);
      if (ds.open >= S.maxOpen) blocks.push(`Max open positions reached (${ds.open}/${S.maxOpen}).`);
      if (overBudget) blocks.push(`Risk ${inr(risk, 0)} exceeds the per-trade budget ${inr(bud, 0)}.`);
      if (plannedRR != null && plannedRR < S.minRR) blocks.push(`Planned R:R ${plannedRR.toFixed(2)} below minimum ${S.minRR}:1.`);
    } else if (overBudget) warns.push(`Risk ${inr(risk, 0)} exceeds the per-trade budget ${inr(bud, 0)}.`);
    return { errs, warns, blocks, bud, perUnit, sugg, risk, plannedRR, overBudget };
  }

  /* ---------- analytics ---------- */
  function metrics(list) {
    const cl = list.filter(t => entered(t) && statusOf(t) === 'Closed');
    const rows = cl.map(t => ({ t, c: calc(t) }));
    const n = rows.length, wins = rows.filter(r => r.c.net > 0), losses = rows.filter(r => r.c.net < 0);
    const gp = wins.reduce((a, r) => a + r.c.net, 0), gl = Math.abs(losses.reduce((a, r) => a + r.c.net, 0));
    const Rs = rows.map(r => r.c.R).filter(x => x != null);
    const sorted = rows.slice().sort((a, b) => lastExit(a.t).localeCompare(lastExit(b.t)));
    let cum = 0, peak = 0, dd = 0;
    sorted.forEach(r => { cum += r.c.net; peak = Math.max(peak, cum); dd = Math.max(dd, peak - cum); });
    const hit = k => cl.filter(t => (t.hits || []).includes(k)).length;
    return {
      n, net: rows.reduce((a, r) => a + r.c.net, 0), winRate: n ? wins.length / n : 0,
      avgWin: wins.length ? gp / wins.length : 0, avgLoss: losses.length ? -gl / losses.length : 0,
      pf: gl > 0 ? gp / gl : (gp > 0 ? Infinity : 0), expR: Rs.length ? Rs.reduce((a, b) => a + b, 0) / Rs.length : 0,
      maxDD: dd, t1: n ? hit('T1') / n : 0, t2: n ? hit('T2') / n : 0, t3: n ? hit('T3') / n : 0,
      slExits: cl.filter(t => t.exitType === 'SL').length, tslExits: cl.filter(t => t.exitType === 'TSL').length,
      beExits: cl.filter(t => t.exitType === 'Breakeven').length, sorted,
    };
  }
  const lastExit = t => { const l = (t.exits || []).slice(-1)[0]; return l ? (l.date + ' ' + (l.time || '')) : (t.date || ''); };

  /* ---------- filters ---------- */
  function filtered() {
    const f = ui.f;
    return allTrades().filter(t => {
      if (f.src === 'auto' && !t.auto) return false;
      if (f.src === 'manual' && t.auto) return false;
      if (f.from && t.date < f.from) return false;
      if (f.to && t.date > f.to) return false;
      if (f.market) {
        const m = t.market || '';
        if (f.market === 'Equity Intraday') {
          if (m !== 'Equity' && m !== 'Equity Intraday') return false;
        } else if (m !== f.market) {
          return false;
        }
      }
      if (f.inst && !(t.instrument || t.symbol || '').toUpperCase().includes(f.inst.toUpperCase())) return false;
      if (f.setup && t.setup !== f.setup) return false;
      if (f.dir && t.dir !== f.dir) return false;
      if (f.exit && t.exitType !== f.exit) return false;
      if (f.rule && t.rule !== f.rule) return false;
      return true;
    });
  }

  /* ---------- tiny canvas charts ---------- */
  function css(v, d) { try { return getComputedStyle(document.documentElement).getPropertyValue(v).trim() || d; } catch (e) { return d; } }
  function drawLine(cv, ys, color, fillBelow) {
    const dpr = window.devicePixelRatio || 1, W = cv.clientWidth, H = cv.clientHeight; if (!W) return;
    cv.width = W * dpr; cv.height = H * dpr; const c = cv.getContext('2d'); c.setTransform(dpr, 0, 0, dpr, 0, 0); c.clearRect(0, 0, W, H);
    if (ys.length < 2) { c.fillStyle = css('--text-3', '#8a93a6'); c.font = '12px sans-serif'; c.fillText('Not enough closed trades yet', 12, H / 2); return; }
    const lo = Math.min(...ys, 0), hi = Math.max(...ys, 0), p = 10, sx = i => p + (W - 2 * p) * i / (ys.length - 1), sy = v => H - p - (H - 2 * p) * (v - lo) / ((hi - lo) || 1);
    c.strokeStyle = css('--line', '#2a3345'); c.beginPath(); c.moveTo(p, sy(0)); c.lineTo(W - p, sy(0)); c.stroke();
    c.beginPath(); ys.forEach((v, i) => i ? c.lineTo(sx(i), sy(v)) : c.moveTo(sx(i), sy(v))); c.strokeStyle = color; c.lineWidth = 2; c.stroke();
    if (fillBelow) { c.lineTo(sx(ys.length - 1), sy(0)); c.lineTo(sx(0), sy(0)); c.closePath(); c.globalAlpha = .12; c.fillStyle = color; c.fill(); c.globalAlpha = 1; }
  }
  function drawBars(cv, vs) {
    const dpr = window.devicePixelRatio || 1, W = cv.clientWidth, H = cv.clientHeight; if (!W) return;
    cv.width = W * dpr; cv.height = H * dpr; const c = cv.getContext('2d'); c.setTransform(dpr, 0, 0, dpr, 0, 0); c.clearRect(0, 0, W, H);
    if (!vs.length) { c.fillStyle = css('--text-3', '#8a93a6'); c.font = '12px sans-serif'; c.fillText('No closed trades yet', 12, H / 2); return; }
    const lo = Math.min(...vs, 0), hi = Math.max(...vs, 0), p = 10, bw = Math.max(2, (W - 2 * p) / vs.length - 2), sy = v => H - p - (H - 2 * p) * (v - lo) / ((hi - lo) || 1);
    vs.forEach((v, i) => { c.fillStyle = v >= 0 ? css('--up', '#22ab94') : css('--down', '#f7525f'); const x = p + i * ((W - 2 * p) / vs.length); c.fillRect(x, Math.min(sy(v), sy(0)), bw, Math.max(1, Math.abs(sy(v) - sy(0)))); });
  }

  /* ---------- screens ---------- */
  const kpi = (l, v, sub, c, tip) => `<div class="jv-kpi" title="${E((tip ? tip + (sub ? ' — ' : '') : '') + (sub ? String(sub).replace(/<[^>]+>/g, '') : ''))}"><small>${l}</small><b class="${c || ''}">${v}</b>${sub ? `<span>${sub}</span>` : ''}</div>`;
  const cc = n => (n > 0 ? 'up' : n < 0 ? 'down' : '');
  function banner() { return `<span class="jv-paper" role="note" title="Paper trading: simulated results, no broker orders are sent. Virtual capital ${inr(S.capital, 0)}.">PAPER · ${inr(S.capital, 0)}</span>`; }

  /* Live P&L: equity and P&L include open positions (marked to market), and the
     overview refreshes on its own while it is on screen. */
  function liveTotals(day) {
    const autoReal = AUTO.list.concat((AUTO.stockTrades || []).filter(t => t.status === 'Closed'), paperList().filter(t => t.status === 'Closed')).reduce((a, t) => a + (entered(t) ? calc(t).net : 0), 0);
    const booked = realised() + autoReal;
    const unr = allTrades().reduce((a, t) => a + (unrealisedNet(t) || 0), 0);
    const autoToday = AUTO.list.concat((AUTO.stockTrades || []), paperList()).reduce((a, t) => a + (entered(t) && statusOf(t) === 'Closed' && lastExit(t).slice(0, 10) === day ? calc(t).net : 0), 0);
    return { booked, unr, autoToday, eq: S.capital + booked + unr };
  }
  /* Capital in use: buys (premium / share value paid), margin blocked for sells (options: max(12% of the underlying, premium)
     per unit - same rule as the order ticket; stocks: 20%), and the premium of open auto-trader trades. Today's peak is
     remembered (per device) so you can see the most capital that was tied up at once today. */
  /* Separate paper books: option BUYS (long premium) and option SELLS (short premium / written options) each get Rs 10 L */
  const SELL_CAP = 1000000;
  function sideTotals(sign) {
    let booked = 0, unr = 0;
    allTrades().forEach(t => { if (!entered(t) || t.isStock || dirOf(t) !== sign) return; const c = calc(t).net || 0;   // options books only: stock trades live in the Stock trader book (the Total tile adds it once)
      if (statusOf(t) === 'Closed') booked += c; else { booked += t.auto ? 0 : c; unr += unrealisedNet(t) || 0; } });   // manual trades can be partly booked
    return { booked, unr };
  }
  function capUse() {
    let buys = 0, sm = 0, auto = 0;
    if (typeof App !== 'undefined') (App.positions || []).forEach(p => {
      if (!p || !p.q) return;
      const s = (typeof SYM === 'function' && SYM(p.sym)) || {}, m = (App.meta || {})[p.sym] || {}, q = Math.abs(p.q);
      if (p.q > 0) buys += q * p.avg;
      else sm += m.ikey ? q * Math.max(0.12 * (m.spot || s.last || 0), p.avg) : q * p.avg * 0.2;
    });
    let autoL = 0, autoS = 0;
    AUTO.list.forEach(t => { if (!entered(t) || statusOf(t) === 'Closed') return; const v = (t.raw && t.raw.margin > 0) ? t.raw.margin : (t.entry || 0) * (t.qty || 0) * (t.mult || 1); auto += v; if (dirOf(t) < 0) autoS += v; else autoL += v; });
    const cash = (typeof App !== 'undefined' && typeof App.cash === 'number') ? App.cash : S.capital;
    const used = buys + sm + auto, avail = Math.max(0, cash - sm - auto);
    const day = today(), key = 'rj-cap-peak', now = new Date();
    let pk = load(key, null); if (!pk || pk.day !== day) pk = { day, peak: 0, at: '', left: avail };
    if (used > pk.peak + 0.5) { pk.peak = used; pk.at = istTime(now); pk.left = avail; save(key, pk); }
    const sb = sideTotals(1), ss = sideTotals(-1), buyUsed = buys + autoL, sellUsed = sm + autoS;
    const buy = { cap: S.capital, used: buyUsed, free: Math.max(0, S.capital + sb.booked - buyUsed), eq: S.capital + sb.booked + sb.unr, booked: sb.booked, unr: sb.unr };
    const sell = { cap: SELL_CAP, used: sellUsed, free: Math.max(0, SELL_CAP + ss.booked - sellUsed), eq: SELL_CAP + ss.booked + ss.unr, booked: ss.booked, unr: ss.unr };
    return { buy, sell, buys, sm, auto, used, avail, pct: used + avail > 0 ? used / (used + avail) * 100 : 0, cap: S.capital, peak: pk.peak, peakAt: pk.at, peakLeft: pk.left, peakPct: pk.peak + pk.left > 0 ? pk.peak / (pk.peak + pk.left) * 100 : 0 };
  }
  function capCard() {
    const c = capUse(), bar = (p, cl) => `<div class="jv-capbar"><i class="${cl}" style="width:${Math.min(100, p).toFixed(1)}%"></i></div>`;
    return `<div class="card jv-cap" id="jvCap"><div class="card-h"><h3>Capital</h3><span class="muted" style="font-size:12px">paper · ${inr(c.cap, 0)} starting capital</span></div>
      <div class="jv-capg">
        <div><small>In use now</small><b>${inr(c.used, 0)}</b><span class="muted">${c.pct.toFixed(1)}% · buys ${inr(c.buys, 0)} · sell margin ${inr(c.sm, 0)}${c.auto ? ' · auto ' + inr(c.auto, 0) : ''}</span>${bar(c.pct, c.pct > 80 ? 'down' : c.pct > 50 ? 'warn' : 'up')}</div>
        <div><small>Available now</small><b class="up">${inr(c.avail, 0)}</b><span class="muted">free to place new trades</span></div>
        <div><small>Max used today</small><b>${inr(c.peak, 0)}</b><span class="muted">${c.peak > 0 ? `${c.peakPct.toFixed(1)}% at ${E(c.peakAt)} · ${inr(c.peakLeft, 0)} was left then` : 'nothing used yet today'}</span>${bar(c.peakPct, 'mute')}</div>
      </div></div>`;
  }
  function kpiBlock(m, ds, day) {
    const L = liveTotals(day), todayBooked = ds.pnl + L.autoToday, todayAll = todayBooked + L.unr;
    const openN = allTrades().filter(t => entered(t) && statusOf(t) !== 'Closed').length;
    return `      ${kpi('Total profit locked in', sinr(L.booked), m.n + ' closed trades', cc(L.booked), 'Net profit of every closed trade, all time (after costs)')}
      ${kpi('Trades today', String(ds.entries + AUTO.list.concat(AUTO.stockTrades || []).filter(t => t.date === day).length), 'manual ' + ds.entries + ' · auto ' + AUTO.list.concat(AUTO.stockTrades || []).filter(t => t.date === day).length, '', 'Trades taken today')}
      ${kpi('Win rate', (m.winRate * 100).toFixed(0) + '%', 'W ' + inr(m.avgWin, 0) + ' · L ' + inr(m.avgLoss, 0), '', 'Share of closed trades that made money, with the average win (W) and average loss (L)')}
      ${kpi('Avg result per trade', rr(m.expR), 'in R', cc(m.expR), 'Average result of a trade measured in R, where 1R is the money you risked on it. Above 0 means you make money over time')}
      ${kpi('Profit factor', m.pf === Infinity ? '∞' : m.pf.toFixed(2), 'profit ÷ loss', '', 'Total profit divided by total loss. Above 1 = profitable, above 1.5 = good')}
      ${(dd => kpi('Biggest drop today', inr(dd, 0), 'all-time ' + inr(m.maxDD, 0), dd > 0 ? 'down' : '', "Largest fall of today's profit from its high so far (closed + running). Resets every day"))(dayDD(day))}`;
  }
  function refreshLive() {
    const host = document.getElementById('v-journal');
    if (!host || !host.offsetParent || document.querySelector('.modal-bg') || document.hidden) return;
    if (ui.tab === 'picklog') { const b = document.getElementById('jvPickLog'), h = window.pkLogHTML ? window.pkLogHTML() : ''; if (b && b._h !== h) { b._h = h; b.innerHTML = h; } return; }
    if (ui.tab === 'positions') { liveCap(); if (!livePositions()) render(); return; }
    if (ui.tab === 'algo' || ui.tab === 'stocks') { liveCap(); return; }
    if (ui.tab !== 'portfolio') return;
    const k = document.getElementById('jvKpis'); if (!k) return;
    liveCap();
    { const td = document.getElementById('jvToday'); if (td) { const t = document.createElement('div'); t.innerHTML = todayCard(); const n = t.firstElementChild; if (n && n.innerHTML !== td.innerHTML) td.innerHTML = n.innerHTML; } }
    { const db = document.getElementById('jvDayB'); if (db) { const v = todayTotal().total; db.textContent = 'Day ' + sinr(v); db.className = 'num ' + (v > 0 ? 'up' : v < 0 ? 'down' : ''); } }
    { const bk = document.getElementById('jvBooks'); if (bk) { sbLoad(false); const t = document.createElement('div'); t.innerHTML = booksCard(); const n = t.firstElementChild; if (n.innerHTML !== bk.innerHTML) bk.innerHTML = n.innerHTML; } }
    const day = today();
    { const ie = document.getElementById('jvInsight'); if (ie) { const t = document.createElement('div'); t.innerHTML = insightCard(metrics(filtered())); const n = t.firstElementChild; if (n && n.innerHTML !== ie.innerHTML) { ie.innerHTML = n.innerHTML; ie.className = n.className; } } }
    patchKids(k, kpiBlock(metrics(filtered()), dayStats(day), day));      // only the numbers that changed are touched - no page redraw
    const o = document.getElementById('jvOpen');
    if (o) {
      const open = allTrades().filter(t => entered(t) && statusOf(t) !== 'Closed' && sideOk(t)), ids = open.map(t => t.id).join(',');
      if (o.dataset.ids === ids && o.querySelector('table')) {
        open.forEach(t => {
          const r = o.querySelector(`tr[data-id="${CSS.escape(String(t.id))}"]`);
          if (!r) return;
          const pnlCell = r.querySelector('[data-c="pnl"]');
          const curCell = r.querySelector('[data-c="cur"]');
          const u = unrealisedNet(t), v = u == null ? '—' : sinr(u);
          if (pnlCell && pnlCell.textContent !== v) {
            pnlCell.innerHTML = `<b>${v}</b>`;
            pnlCell.className = 'num ' + cc(u || 0);
          }
          if (curCell) {
            const cp = px(curPx(t));
            if (curCell.textContent !== cp) curCell.innerHTML = `<b>${cp}</b>`;
          }
        });
      } else {
        const w = o.querySelector('.tbl-wrap,.jv-tw,[style*="overflow"]') || o.firstElementChild, x = w ? w.scrollLeft : 0;
        o.innerHTML = tradeTable(open, true, 'open'); o.dataset.ids = ids;
        const w2 = o.querySelector('.tbl-wrap,.jv-tw,[style*="overflow"]') || o.firstElementChild; if (w2) w2.scrollLeft = x;
      }
    }
    const ts = document.getElementById('jvLiveTs'); if (ts) ts.textContent = 'live · updated ' + new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }
  function patchKids(host, html) {
    const tmp = document.createElement('div'); tmp.innerHTML = html;
    const a = host.children, b = tmp.children;
    if (a.length !== b.length) { host.innerHTML = html; return; }
    for (let i = 0; i < b.length; i++) if (a[i].innerHTML !== b[i].innerHTML) { a[i].innerHTML = b[i].innerHTML; a[i].className = b[i].className; a[i].title = b[i].title; }
  }
  function curPx(t) {
    if (t.isStock) {
      const l = live(t.symbol || t.instrument);
      if (l != null && l > 0) return l;
      return (t.raw && t.raw.last) || t.last || t.entry;
    }
    if (t.auto) {
      const l = live(t.symbol);
      if (l != null && l > 0) return l;
      return (t.raw && t.raw.last) || t.entry;
    }
    return live(t.symbol || t.instrument) || (t.raw && t.raw.last) || t.entry;
  }
  /* the price an open trade's P&L is figured at: for option trades the server's mark (what a stop / exit could actually get - the bid for a bought
     option), the last traded price only when there is no mark; shares use their live price. The LTP column keeps showing the last traded price. */
  function markPx(t) {
    if (!t.isStock && t.auto && t.raw && t.raw.mark > 0) return t.raw.mark;
    return curPx(t);
  }
  function liveCap() { const el = document.getElementById('jvCap'); if (!el) { capUse(); return; } const t = document.createElement('div'); t.innerHTML = capCard(); const n = t.firstElementChild; if (n && n.innerHTML !== el.innerHTML) el.innerHTML = n.innerHTML; }
  function livePositions() {
    const tb = document.getElementById('jvPosOpen'); if (!tb) return false;
    const open = posOpenPage().part;
    if (open.map(t => t.id).join(',') !== tb.dataset.ids) return false;
    open.forEach(t => {
      const row = tb.querySelector(`tr[data-pid="${CSS.escape(String(t.id))}"]`); if (!row) return;
      const u = unrealisedNet(t) || 0, q = (k, v, c) => { const el = row.querySelector(`[data-c="${k}"]`); if (el) { el.innerHTML = v; if (c != null) el.className = 'num ' + c; } };
      q('cur', `<b>${px(curPx(t))}</b>`); q('pnl', sinr(u), u > 0 ? 'up' : u < 0 ? 'down' : ''); q('sl', px(t.sl)); q('tsl', E(tslShow(t)), '');
    });
    return true;
  }
  /* auto trades: the live state of the trailing stop - the server moves it every cycle, the column used to show only a static label */
  function autoTsl_(t) {
    const a = t.raw || {}, l = a.lock;
    if (l) return l.mode === 'trail' ? `Trail · locks ₹${Math.round(Number(l.keep) || 0).toLocaleString('en-IN')} · SL ${px(a.premSL)}` : `Breakeven · SL ${px(a.premSL)}`;
    if (a.variant === 'trail' || (a.tsl && a.tsl.mode && a.tsl.mode !== 'off')) return `Trailing · ${a.sym} stop ${px(a.stopU)}${a.stopMoved ? ' ↑' : ''}`;
    const u = unrealised(t);
    return `Arms at +₹2,500${u != null ? ' (now ' + sinr(u) + ')' : ''}`;
  }
  function tslShow(t) { if (t.auto && statusOf(t) !== 'Closed') return autoTsl_(t); if (t.paper) return t.tsl && t.tsl !== 'Off / Fixed SL' ? t.tsl : '—'; if (t.auto) { const l = t.raw && t.raw.lock; return l ? (l.mode === 'trail' ? `Auto trail · locks ₹${Number(l.keep).toLocaleString('en-IN')}` : 'Auto · breakeven') : (t.tsl && t.tsl !== 'Off / Fixed SL' ? t.tsl : '—'); } return t.tsl && t.tsl !== 'Off / Fixed SL' ? t.tsl : '—'; }
  setInterval(() => { try { capUse(); } catch (e) { } }, 20000);       // today's peak is tracked on every screen, not only the Journal
  const liveTick = () => {
    if (document.hidden || !window.rjMkt() || !AUTO.list.some(t => t.status !== 'Closed')) return;
    const h = document.getElementById('v-journal'), on = !!(h && h.offsetParent);
    if (!on && Date.now() - AUTO.qTs < 9000) return;           // other screens: a live look every 10 s keeps the header P&L chip equal to the Journal's figure
    pullLive(false).then(() => { if (on) refreshLive(); else if (typeof renderPfChip === 'function') { try { renderPfChip(); } catch (e) { } } });
  };
  setInterval(liveTick, 3000);
  setInterval(() => { refreshLive(); if (!document.hidden && window.rjMkt()) syncAuto(false); }, 5000);  // syncAuto self-throttles to 30 s
  setInterval(() => { const h = document.getElementById('v-journal'); if (h && h.offsetParent && !document.hidden && window.rjMkt()) syncAuto(true).then(refreshLive); }, 60000);   // was 15 s: each read costs shared-store requests

   function viewOverview() {
     const L = filtered(), m = metrics(L), day = today(), ds = dayStats(day);
     const LT = liveTotals(day), eq = LT.eq, unr = LT.unr, booked = LT.booked;   // same live figure as the KPI cards and the header
     let cum = 0; const curve = [S.capital]; m.sorted.forEach(r => { cum += r.c.net; curve.push(S.capital + cum); });
     const daily = {}; m.sorted.forEach(r => { const d = lastExit(r.t).slice(0, 10); daily[d] = (daily[d] || 0) + r.c.net; });
     let pk = -Infinity; const dd = curve.map(v => { pk = Math.max(pk, v); return v - pk; });
     const openAll = allTrades().filter(t => entered(t) && statusOf(t) !== 'Closed'), open = openAll.filter(sideOk);
     const dayPnl = todayTotal().total;
     const recent = L.filter(sideOk).sort((a, b) => (b.date + (b.time || '')).localeCompare(a.date + (a.time || '')));
     return `${todayCard()}
     ${booksCard()}
     <div class="jv-sec">How you're doing</div>
     ${filterBar(false)}
     ${insightCard(m)}
     ${legCard()}
     <div class="jv-kpis" id="jvKpis">${kpiBlock(m, ds, day)}    </div>
     <div class="jv-sec">Your trades</div>
     <div class="jv-pos-bar">${sideBar(L.concat(openAll.filter(t => !L.includes(t))))}<span class="muted" style="font-size:12px">Counts include closed trades · Buy = long · Sell = short / option writing</span></div>
     <div class="card"><div class="card-h"><h3>Running trades</h3><span class="jv-hr"><b id="jvDayB" class="num ${dayPnl > 0 ? 'up' : dayPnl < 0 ? 'down' : ''}" title="Today's booked P&L + open P&L of today's trades" style="font-size:13px">Day ${sinr(dayPnl)}</b><span class="muted" style="font-size:12px" id="jvLiveTs">live</span>${open.length ? `<button class="jv-exit jv-exitall" data-jv="exitall" title="Exit every open position at the live price">Exit all (${open.length})</button>` : ''}</span></div><div id="jvOpen" data-ids="${E(open.map(t => t.id).join(','))}">${tradeTable(open, true, 'open')}</div></div>
     <div class="jv-sec">Recent trades</div>
     <div class="card"><div class="card-h"><h3>Latest first</h3></div>${tradeTable(recent, true, 'recent')}</div>`;
  }

  function viewOrders() {
    if (typeof App === 'undefined' || typeof ordTable === 'undefined') return '<div class="empty">Orders are not available right now.</div>';
    const A = App, f = A.ord || 'Open', all = [...(A.orders || []), ...(A.history || [])].sort((a, b) => b.t - a.t);
    const list = f === 'All' ? all : all.filter(o => o.status === f);
    return `<div class="card"><div class="filters"><div class="seg" id="jvOrdSeg">${['Open', 'Filled', 'Cancelled', 'All'].map(s => `<button class="${f === s ? 'on' : ''}" data-jvord="${s}">${s} <span class="muted">${s === 'All' ? all.length : all.filter(o => o.status === s).length}</span></button>`).join('')}</div></div><div class="tbl-wrap">${ordTable(list, f === 'Open')}</div></div>`;
  }

  function istShift(days) { const d = new Date(Date.now() + 5.5 * 3600e3 - days * 864e5); return d.toISOString().slice(0, 10); }
  function datePreset() { const f = ui.f, t = today(); if (!f.from && !f.to) return 'all'; if (f.from === t && (!f.to || f.to === t)) return 'today';
    if (!f.to && f.from === istShift(6)) return '7d'; if (!f.to && f.from === istShift(29)) return '30d'; return 'custom'; }
  function moreCount() { const f = ui.f; return ['market', 'setup', 'dir', 'exit', 'rule'].filter(k => f[k]).length + (datePreset() === 'custom' ? 1 : 0); }
  function filterBar() {
    const f = ui.f, setups = [...new Set(allTrades().map(t => t.setup).filter(Boolean))], dp = datePreset(), mc = moreCount();
    const opt = (arr, cur, all) => `<option value="">${all}</option>` + arr.map(x => `<option ${cur === x ? 'selected' : ''}>${E(x)}</option>`).join('');
    const seg = (name, cur, opts) => `<div class="jv-seg">${opts.map(([v, l, tip]) => `<button class="${cur === v ? 'on' : ''}" data-jvq="${name}:${v}" ${tip ? `title="${tip}"` : ''}>${l}</button>`).join('')}</div>`;
    const chips = [];
    if (dp === 'custom') chips.push(['date', (f.from || '…') + ' → ' + (f.to || 'now')]);
    [['market', 'Market'], ['setup', 'Setup'], ['dir', 'Side'], ['exit', 'Exit'], ['rule', 'Rule']].forEach(([k, l]) => { if (f[k]) chips.push([k, l + ': ' + f[k]]); });
    if (f.inst) chips.push(['inst', '“' + f.inst + '”']);
    return `<div class="jv-fb">
      ${seg('d', dp, [['today', 'Today'], ['7d', '7D', 'Last 7 days'], ['30d', '30D', 'Last 30 days'], ['all', 'All', 'All dates']])}
      <label class="jv-search" title="Search by instrument or symbol"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg><input class="inp" data-jf="inst" value="${E(f.inst)}" placeholder="Search symbol" aria-label="Search symbol"></label>
      ${seg('src', f.src || '', [['', 'All'], ['manual', 'Manual', 'Trades you logged'], ['auto', 'Auto', 'Trades placed by the auto trader']])}
      <button class="jv-fbtn ${mc || ui.moreF ? 'on' : ''}" data-jv="moref" aria-expanded="${!!ui.moreF}" title="More filters: market, setup, side, exit, rule, custom dates">Filters${mc ? ` <i>${mc}</i>` : ''}</button>
    </div>
    ${ui.moreF ? `<div class="jv-more">
      <label>From<input type="date" class="inp" data-jf="from" value="${f.from}"></label><label>To<input type="date" class="inp" data-jf="to" value="${f.to}"></label>
      <label>Market<select class="inp" data-jf="market">${opt(MARKETS, f.market, 'All')}</select></label>
      <label>Setup<select class="inp" data-jf="setup">${opt(setups, f.setup, 'All')}</select></label>
      <label>Side<select class="inp" data-jf="dir">${opt(['Long', 'Short'], f.dir, 'All')}</select></label>
      <label>Exit<select class="inp" data-jf="exit">${opt(EXIT_TYPES, f.exit, 'All')}</select></label>
      <label title="Did the trade follow your rules?">Rule<select class="inp" data-jf="rule">${opt(['Yes', 'No', 'Partial'], f.rule, 'All')}</select></label>
      <button class="btn-xs" data-jv="clearf">Clear all</button></div>` : ''}
    ${chips.length ? `<div class="jv-chips">${chips.map(([k, l]) => `<button class="jv-chip" data-jvclr="${k}" title="Remove this filter">${E(l)} ✕</button>`).join('')}</div>` : ''}`;
  }

  const PG_SIZES = [5, 10, 15, 1000];
  /* Buy / Sell split: one switch for every journal table */
  /* Eagle Trades (strength >= 75 + Open = Low / High, server auto trader): a badge on every row and their own filter */
  const isEagle = t => /^Eagle/i.test(t.setup || '');
  const isIndexT = t => t.market === 'Index' || /^(NIFTY|BANKNIFTY|FINNIFTY|MIDCPNIFTY|SENSEX|BANKEX|NIFTYNXT50)\b/.test(String(t.instrument || t.symbol || '').toUpperCase());
  const eagleTag = t => isEagle(t) ? '<span class="jv-eagle" title="Eagle Trades: strength 75+ with Open = Low (buy) / Open = High (sell)">🦅 EAGLE</span>' : '';
  const sideOk = t => !ui.side || ui.side === 'all' || (ui.side === 'eagle' ? isEagle(t) : ui.side === 'index' ? isIndexT(t) : ui.side === 'sell' ? t.dir === 'Short' : t.dir !== 'Short');
  function sideBar(list) {
    const nb = list.filter(t => t.dir !== 'Short').length, ns = list.length - nb, ne = list.filter(isEagle).length, ni = list.filter(isIndexT).length, cur = ui.side || 'all';
    return `<div class="jv-seg jv-sidesw" role="group" aria-label="Buy or sell trades">${[['all', 'All', list.length], ['buy', 'Buy', nb], ['sell', 'Sell', ns]].concat(ni || cur === 'index' ? [['index', 'Index', ni]] : []).concat(ne || cur === 'eagle' ? [['eagle', '🦅 Eagle', ne]] : []).map(([k, l, n]) =>
      `<button class="${cur === k ? 'on' : ''} ${k}" data-jvside="${k}">${l} <small>${n}</small></button>`).join('')}</div>`;
  }
  document.addEventListener('click', e => { const b = e.target.closest('[data-jvside]'); if (!b || !e.target.closest('#v-journal')) return;
    ui.side = b.dataset.jvside; Object.values(ui.pg || {}).forEach(x => x.p = 0); render(); }, true);
  function pagerBar(list, key) {
    ui.pg = ui.pg || {};
    const pg = ui.pg[key] || (ui.pg[key] = { p: 0, s: 5 });
    const pages = Math.max(1, Math.ceil(list.length / pg.s)); pg.p = Math.min(pg.p, pages - 1);
    const part = list.slice(pg.p * pg.s, (pg.p + 1) * pg.s);
    const bar = list.length > PG_SIZES[0] ? `<div class="jv-pg"><div class="jv-seg jv-seg-s" title="Rows per page">${PG_SIZES.map(n => `<button class="${pg.s === n ? 'on' : ''}" data-jvps="${key}:${n}">${n}</button>`).join('')}</div>
      <span class="muted">${pg.p * pg.s + 1}–${pg.p * pg.s + part.length} of ${list.length}</span>
      <span class="jv-pgb"><button data-jvpg="${key}:${pg.p - 1}" ${pg.p <= 0 ? 'disabled' : ''} aria-label="Previous page">‹</button><b>${pg.p + 1}/${pages}</b><button data-jvpg="${key}:${pg.p + 1}" ${pg.p >= pages - 1 ? 'disabled' : ''} aria-label="Next page">›</button></span></div>` : '';
    return { part, bar };
  }
  /* ---------- trade timestamps: when it was taken, when it exited, how long it was held ---------- */
  /* open paper position ids embed the contract (strike / expiry day), so those show their entry time instead */
  const shortId = t => { const pid = String(t.id || ''); if (pid.startsWith('P|')) return (t.time || '').replace(':', '') || pid.slice(2, 6); const m = pid.match(/\d+/g); return m ? m[m.length - 1] : String(t.id || ''); };   // A-1023-43-W -> 43: the number only, the A/T/M tag already says the source
  function tStart(t) {
    if (t.openedAt || t.created) { const d = new Date(t.openedAt || t.created); if (isFinite(d)) return d; }
    if (t.date && t.time) { const d = new Date(t.date + 'T' + t.time + ':00+05:30'); if (isFinite(d)) return d; }
    return t.date ? new Date(t.date + 'T09:20:00+05:30') : null;
  }
  function entryTime(t) {
    if (t.time) return t.time;
    const d = tStart(t);
    return d && isFinite(d) ? istTime(d) : '';
  }
  function exitTime(t) {
    if (t.closedAt) { const d = new Date(t.closedAt); if (isFinite(d)) return istTime(d); }
    const ex = (t.exits || []).filter(x => x && (x.time || x.at || x.date));
    if (ex.length) { const l = ex[ex.length - 1]; return l.time || (l.at ? istTime(new Date(l.at)) : ''); }
    return '';
  }
  function heldTxt(t) {
    const s = tStart(t);
    if (!s || !isFinite(s)) return '—';
    const closed = statusOf(t) === 'Closed';
    const e = closed && t.closedAt ? new Date(t.closedAt) : new Date();
    if (!e || !isFinite(e)) return '—';
    let m = Math.max(0, Math.round((e - s) / 60000));
    const d = Math.floor(m / 1440); m -= d * 1440;
    const h = Math.floor(m / 60); m -= h * 60;
    const parts = [];
    if (d) parts.push(d + 'd');
    if (h) parts.push(h + 'h');
    if (m || !parts.length) parts.push(m + 'm');
    return parts.join(' ');
  }

  
  function getTradeOutcome(t) {
    if (!t) return { tag: 'Unknown', cls: 'b-mute', icon: '•' };
    const rawWhy = (t.raw && (t.raw.exitReason || t.raw.why || t.raw.exitWhy)) || t.exitType || '';
    const whyUpper = String(rawWhy).toUpperCase();
    const st = typeof statusOf === 'function' ? statusOf(t) : (t.status || 'Open');
    const isPositional = (t.raw && (t.raw.hz === 'positional' || t.raw.horizon === 'positional')) ||
                         (t.setup && String(t.setup).toLowerCase().includes('positional')) ||
                         (t.market && String(t.market).toLowerCase().includes('positional')) ||
                         (t.hz === 'positional');
    const isSwing = (t.raw && (t.raw.hz === 'swing' || t.raw.horizon === 'swing')) ||
                    (t.setup && String(t.setup).toLowerCase().includes('swing')) ||
                    (t.market && String(t.market).toLowerCase().includes('swing')) ||
                    (t.hz === 'swing');

    if (st === 'Closed' || t.status === 'CLOSED' || (t.exits && t.exits.length)) {
      if (whyUpper.includes('STOP') || whyUpper === 'SL' || whyUpper === 'PREMSL' || whyUpper.includes('SPREAD-STOP')) {
        return { tag: 'Stop Hit', cls: 'jv-tag-sl', icon: '🛑', isSL: true };
      }
      if (whyUpper.includes('T2') || whyUpper.includes('TARGET 2') || (whyUpper === 'TARGET' && t.t2)) {
        return { tag: 'T2 Hit', cls: 'jv-tag-t2', icon: '🎯', isTarget: true };
      }
      if (whyUpper.includes('T1') || whyUpper.includes('TARGET 1') || whyUpper.includes('SPREAD-T1') || whyUpper === 'TARGET') {
        return { tag: 'T1 Hit', cls: 'jv-tag-t1', icon: '✅', isTarget: true };
      }
      if (whyUpper.includes('TSL') || whyUpper.includes('TRAIL')) {
        return { tag: 'TSL Lock', cls: 'jv-tag-tsl', icon: '🔒', isTSL: true };
      }
      if (whyUpper.includes('TIME') || whyUpper.includes('EXPIRY') || whyUpper.includes('SQUARE-OFF')) {
        return { tag: 'Time Exit', cls: 'b-mute', icon: '⏰' };
      }
      return { tag: t.exitType || 'Exited', cls: 'b-mute', icon: '•' };
    } else {
      if (isPositional) {
        const days = t.raw && t.raw.holdSessions ? `${t.raw.holdSessions}d` : (t.holdSessions ? `${t.holdSessions}d` : '');
        return { tag: days ? `Hold · ${days}` : 'Hold', sub: 'Positional', cls: 'jv-tag-hold', icon: '⏳', isHold: true };
      }
      if (isSwing) {
        const days = t.raw && t.raw.holdSessions ? `${t.raw.holdSessions}d` : (t.holdSessions ? `${t.holdSessions}d` : '');
        return { tag: days ? `Hold · ${days}` : 'Hold', sub: 'Swing', cls: 'jv-tag-hold', icon: '⏳', isHold: true };
      }
      return { tag: 'Hold', sub: 'Active', cls: 'jv-tag-hold', icon: '⚡', isHold: true };
    }
  }

  /* an open option position -> the contract the Trade screen can chart live (underlying, expiry, strike, CE/PE); null for anything else */
  function optRef(t) {
    if (!t || statusOf(t) === 'Closed') return null;
    if (t.auto && t.raw && t.raw.strike && /^(CE|PE)$/.test(t.raw.opt || '')) return { sym: t.raw.sym, expiry: t.raw.expiry, strike: +t.raw.strike, side: t.raw.opt };
    if (t.paper && t.pos) { const m = (typeof App !== 'undefined' && App.meta && App.meta[t.pos.sym]) || null; if (m && m.ikey && m.und && m.strike && /^(CE|PE)$/.test(m.side || '')) return { sym: m.und, expiry: m.expiry, strike: +m.strike, side: m.side }; }
    return null;
  }
  const chartBtn = t => optRef(t) ? `<button type="button" class="jv-chb" data-jv="optchart" data-id="${E(String(t.id))}" title="Open this option's live chart on the Trade screen">📈 Chart</button>` : '';
  function tradeTable(list, withUnr, key) {
    key = key || 'tbl'; ui.tbl = ui.tbl || {}; ui.pg = ui.pg || {}; ui.tbl[key] = { list, withUnr };
    if (!list.length) return `<div class="jv-tw" data-jvt="${key}"><div class="empty">No trades match.</div></div>`;
    const { part, bar: pager } = pagerBar(list, key);
    const th = (l, tip, cls) => `<th class="${cls || ''}" title="${tip}">${l}</th>`;
    const rows = part.map(t => {
      const c = calc(t), st = statusOf(t), u = withUnr ? unrealisedNet(t) : null, closedish = st === 'Closed' || c.qx;
      const v = closedish ? c.net : (u || 0), pnl = closedish ? sinr(c.net) : (u != null ? sinr(u) : '—');
      const stCls = st === 'Open' || st === 'Partial' ? 'b-up' : 'b-mute';
      const tips = [`Setup: ${t.setup || '—'}`, t.tf ? `TF ${t.tf}` : '', t.ind ? `Indicators: ${t.ind}` : ''].filter(Boolean).join(' · ');
      return `<tr data-jv="open" data-id="${t.id}" tabindex="0" title="Click for full details">
        <td class="jv-id">${t.auto ? '<span class="jv-tag" title="Placed by the auto trader">A</span>' : t.paper ? '<span class="jv-tag m" title="Placed from the Trade screen">T</span>' : '<span class="jv-tag m" title="Logged manually">M</span>'}<span title="${t.id}">${shortId(t)}</span>${t.edited ? ' <i title="Edited after close">✎</i>' : ''}</td>
        <td title="Taken: ${t.date} ${entryTime(t) || ''}">${String(t.date).slice(5)}${entryTime(t) ? ` <small class="num">${entryTime(t)}</small>` : ''}</td>
        <td class="jv-sym"><b>${E(t.symbol || t.instrument)}</b>${eagleTag(t)}${chartBtn(t)}<small title="${E(tips)}">${E(t.setup || '')}</small></td>
        <td><span class="jv-side ${t.dir === 'Short' ? 's' : 'l'}" title="${t.dir}">${t.dir === 'Short' ? 'SELL' : 'BUY'}</span></td>
        <td class="num">${px(t.entry)}</td>
        <td class="num" data-c="cur" title="${closedish ? 'Exit price' : 'Last traded price (live)'}"><b>${px(curPx(t))}</b></td>
        <td class="num" title="${t.sl !== t.sl0 ? 'Initial SL ' + px(t.sl0) + ' · ' : ''}Trailing: ${E(t.tsl || 'off')}">${px(t.sl)}${t.sl !== t.sl0 ? ' <small class="up">↑</small>' : ''}</td>
        <td class="num jv-tg" title="Targets T1 / T2 / T3">${[t.t1, t.t2, t.t3].map(x => x ? px(x) : '–').join(' · ')}</td>
        <td class="num" title="Quantity taken">${qtyTxt(t)}</td>
        <td class="num ${cc(v)}" data-c="pnl" title="${closedish ? 'Booked P&L after costs' : 'Open P&L at live price'}"><b>${pnl}</b></td>
        <td class="num ${cc(c.R)}">${rr(c.R)}</td>
        <td><span class="badge ${getTradeOutcome(t).cls}">${getTradeOutcome(t).tag}</span></td>
        <td class="num" title="${closedish ? 'Held from ' + entryTime(t) + ' to ' + (exitTime(t) || 'exit') : 'Held so far (live)'}">${heldTxt(t)}</td>
        <td class="jv-xc">${st !== 'Closed' && t.status !== 'Planned' && t.status !== 'Cancelled' ? `<button class="jv-exit" data-jv="${t.auto ? 'autoexit' : t.paper ? 'paperexit' : 'mktexit'}" data-id="${E(t.id)}" title="Exit this position now at the live price">Exit</button>` : `<span class="badge ${getTradeOutcome(t).cls}" title="${E(t.exitType || getTradeOutcome(t).tag)}">${getTradeOutcome(t).tag}${exitTime(t) ? ` <small class="num">${exitTime(t)}</small>` : ''}</span>`}${!t.auto ? `<button class="btn-xs down" data-jv="deltrade" data-id="${E(t.id)}" title="Delete manual entry" style="margin-left:4px;padding:1px 5px;font-size:11px">✕</button>` : ''}</td>
        <td title="${t.reviewed ? 'Reviewed' : st === 'Closed' ? 'Review pending' : 'Still open'}">${t.reviewed ? '✓' : (st === 'Closed' ? '<span class="warn">•</span>' : '')}</td></tr>`;
    }).join('');
    return `<div class="jv-tw" data-jvt="${key}"><div class="tbl-wrap"><table class="jv-t"><thead><tr>${th('ID', 'Trade ID · A = automated, M = manual')}${th('Date', 'Entry date and time · when the trade was taken')}${th('Symbol', 'Contract, with setup underneath')}${th('Side', 'L = long, S = short')}${th('Entry', 'Entry price', 'num')}${th('LTP', 'Last traded price (live)', 'num')}${th('SL', 'Current stop-loss (↑ = trailed)', 'num')}${th('Targets', 'T1 · T2 · T3', 'num')}${th('Qty', 'Lots / quantity', 'num')}${th('P&L', 'Booked P&L, or open P&L at live price', 'num')}${th('R', 'Result in multiples of initial risk', 'num')}${th('Status', 'Open, Partial or Closed')}${th('Held', 'How long the trade was held (live while open)', 'num')}${th('Exit', 'Exit an open position now, or how a closed trade ended (with the exit time)', 'jv-xc')}${th('✓', 'Reviewed')}</tr></thead><tbody>${rows}</tbody></table></div>${pager}</div>`;
  }

  function viewNew() {
    const d = ui.draft || (ui.draft = { date: today(), time: istTime(new Date()), market: 'Equity Intraday', dir: 'Long', mult: 1, tsl: TSL_MODES[0], tslTrig: S.labTrigger, trail: '', step: '' });
    const setups = [...new Set(T.map(t => t.setup).filter(Boolean))];
    const sel = (id, arr, cur) => `<select class="inp" id="${id}">${arr.map(x => `<option ${cur === x ? 'selected' : ''}>${E(x)}</option>`).join('')}</select>`;
    const inp = (id, label, v, type = 'text', extra = '') => `<label class="fld"><span>${label}</span><input class="inp" id="${id}" type="${type}" value="${E(v == null ? '' : v)}" ${extra}></label>`;
    const syms = (typeof SYMS !== 'undefined') ? SYMS.slice(0, 500).map(s => `<option value="${E(s.s)}">`).join('') : '';
    const opt = d.market === 'Options';
    return `<form class="jv-form jv-simple" id="jvForm" autocomplete="off">
      <fieldset><legend>New trade</legend>
        <label class="fld"><span>Market</span>${sel('jf-market', MARKETS, d.market)}</label>
        <label class="fld"><span>Stock / index</span><input class="inp" id="jf-inst" list="jvSyms" value="${E(d.instrument || '')}" placeholder="e.g. RELIANCE / NIFTY"><datalist id="jvSyms">${syms}</datalist></label>
        ${opt ? `${inp('jf-strike', 'Strike', d.strike, 'number', 'step="any" placeholder="22600"')}
        <label class="fld"><span>CE / PE</span>${sel('jf-opt', ['CE', 'PE'], d.opt || 'CE')}</label>
        ${inp('jf-expiry', 'Expiry', d.expiry, 'date')}` : ''}
        <label class="fld"><span>Buy / Sell</span><select class="inp" id="jf-dir"><option value="Long" ${d.dir !== 'Short' ? 'selected' : ''}>Buy</option><option value="Short" ${d.dir === 'Short' ? 'selected' : ''}>Sell (short)</option></select></label>
        ${inp('jf-entry', opt ? 'Buy price (premium)' : 'Buy price', d.entry, 'number', 'step="any" inputmode="decimal"')}
        ${inp('jf-sl', 'Stop-loss (SL)', d.sl, 'number', 'step="any" inputmode="decimal"')}
        ${inp('jf-t2', 'Target (TGT)', d.t2, 'number', 'step="any" inputmode="decimal" placeholder="blank = ' + S.t2 + 'R"')}
        ${inp('jf-qty', opt ? 'Lots' : 'Quantity', d.qty, 'number', 'step="1" min="1" inputmode="numeric"')}
        ${inp('jf-mult', opt ? 'Lot size' : 'Multiplier', d.mult, 'number', 'step="any" min="1"')}
        <div class="jv-calc" id="jvCalc"></div>
        <label class="fld wide" id="jvOvr" hidden><span>Override reason (logged)</span><input class="inp" id="jf-ovr" value="${E(d.ovr || '')}"></label>
      </fieldset>
      <details class="jv-more"><summary>More details (optional): date, setup, T1/T3, trailing stop, notes</summary>
      <fieldset>
        ${inp('jf-date', 'Date', d.date, 'date')}${inp('jf-time', 'Entry time', d.time, 'time')}
        ${inp('jf-sym', 'Symbol / contract', d.symbol || '', 'text', 'placeholder="auto from stock / strike"')}
        <label class="fld"><span>Strategy / setup</span><input class="inp" id="jf-setup" list="jvSetups" value="${E(d.setup || '')}"><datalist id="jvSetups">${setups.map(s => `<option value="${E(s)}">`).join('')}</datalist></label>
        ${inp('jf-tf', 'Timeframe', d.tf || '', 'text', 'placeholder="5m / 15m / 1D"')}
        ${inp('jf-ind', 'Indicator values', d.ind || '', 'text', 'placeholder="UT Bot BUY, RSI 58…"')}
        ${inp('jf-t1', 'T1 (partial)', d.t1, 'number', 'step="any" placeholder="blank = ' + S.t1 + 'R"')}${inp('jf-t3', 'T3 (extended)', d.t3, 'number', 'step="any" placeholder="blank = ' + S.t3 + 'R"')}
        <label class="fld"><span>Trailing stop</span>${sel('jf-tsl', TSL_MODES, d.tsl)}</label>
        ${inp('jf-trig', 'Breakeven trigger (R)', d.tslTrig, 'number', 'step="any"')}
        ${inp('jf-trail', 'Trail distance (price)', d.trail, 'number', 'step="any"')}${inp('jf-step', 'Step size (price)', d.step, 'number', 'step="any"')}
        <label class="fld wide"><span>Why this trade</span><textarea class="inp" id="jf-why" rows="2">${E(d.why || '')}</textarea></label>
      </fieldset></details>
      <div class="jv-actions"><button type="button" class="btn pri" data-jv="enter">Add trade</button><button type="button" class="btn" data-jv="plan">Save as plan</button><button type="button" class="btn" data-jv="resetform">Clear</button></div>
    </form>`;
  }

  function readForm() {
    const g = id => { const e = document.getElementById(id); return e ? e.value : ''; };
    const f = {
      date: g('jf-date') || today(), time: g('jf-time') || istTime(new Date()), market: g('jf-market'), instrument: g('jf-inst').trim(), symbol: g('jf-sym').trim(),
      strike: num(g('jf-strike')), opt: g('jf-opt'), expiry: g('jf-expiry'),
      dir: g('jf-dir'), setup: g('jf-setup').trim() || 'Manual', tf: g('jf-tf').trim(), ind: g('jf-ind').trim(),
      entry: num(g('jf-entry')), sl: num(g('jf-sl')), qty: num(g('jf-qty')), mult: num(g('jf-mult')) || 1,
      t1: num(g('jf-t1')), t2: num(g('jf-t2')), t3: num(g('jf-t3')), tsl: g('jf-tsl'), tslTrig: num(g('jf-trig')),
      trail: num(g('jf-trail')), step: num(g('jf-step')), why: g('jf-why').trim(), ovr: g('jf-ovr').trim(),
    };
    ui.draft = Object.assign({}, f);
    return f;
  }
  function composeOptSymbol() {
    const d = readForm(); if (d.market !== 'Options' || !d.instrument || !(d.strike > 0)) return;
    const sym = document.getElementById('jf-sym'); if (!sym) return;
    sym.value = `${d.instrument} ${Number(d.strike).toFixed(0)} ${d.opt || 'CE'}${d.expiry ? ' ' + d.expiry : ''}`;
    ui.draft.symbol = sym.value;
  }
  function fillTargets(f) {
    const d = f.dir === 'Short' ? -1 : 1, r = Math.abs(f.entry - f.sl);
    if (!(r > 0)) return f;
    [['t1', S.t1], ['t2', S.t2], ['t3', S.t3]].forEach(([k, R]) => { if (f[k] == null) f[k] = +(f.entry + d * r * R).toFixed(2); });
    return f;
  }
  function renderCalc() {
    const box = document.getElementById('jvCalc'); if (!box) return;
    const f = fillTargets(Object.assign({}, readForm())), v = validate(f, { recording: false }), ds = dayStats(f.date || today());
    const msgs = v.errs.map(e => `<li class="down">✖ ${E(e)}</li>`).concat(v.warns.map(w => `<li class="warn">⚠ ${E(w)}</li>`));

    box.innerHTML = `<div class="jv-calc-grid">
      <div><small>Risk budget (${S.riskPct}% of ${inr(equity(), 0)})</small><b>${inr(v.bud, 0)}</b></div>
      <div><small>Initial risk (₹)</small><b class="${v.overBudget ? 'down' : ''}">${v.risk ? inr(v.risk, 0) : '—'}</b></div>
      <div><small>Suggested quantity</small><b>${v.sugg || '—'}</b></div>
      <div><small>R:R (to target)</small><b>${v.plannedRR != null ? v.plannedRR.toFixed(2) + ':1' : '—'}</b></div>
      <div><small>Trades today</small><b>${ds.entries}</b></div></div><ul class="jv-msgs">${msgs.join('') || '<li class="up">✓ Plan passes all checks</li>'}</ul>`;
    const ovr = document.getElementById('jvOvr'); if (ovr) ovr.hidden = !(v.overBudget || (v.plannedRR != null && v.plannedRR < S.minRR) );
  }

  function buildTrade(f, status, ovrReason, ovrFlag) {
    fillTargets(f);
    const id = nextId(), at = new Date(f.date + 'T' + (f.time || '09:15') + ':00+05:30');
    return {
      id, date: f.date, time: f.time, at: isNaN(at) ? null : at.toISOString(), market: f.market, instrument: f.instrument, symbol: f.symbol || f.instrument,
      dir: f.dir, setup: f.setup, tf: f.tf, ind: f.ind, entry: f.entry, sl: f.sl, sl0: f.sl, t1: f.t1, t2: f.t2, t3: f.t3,
      qty: f.qty, mult: f.mult || 1, tsl: f.tsl, tslTrig: f.tslTrig, trail: f.trail, step: f.step, why: f.why,
      status, exits: [], hits: [], hitOrder: [], stops: [{ at: new Date().toISOString(), from: null, to: f.sl, note: 'initial stop' }],
      hi: null, lo: null, rule: '', emotion: '', lesson: '', ref: '', mistakes: '', reviewer: '',
      plan: { entry: f.entry, sl: f.sl, qty: f.qty, t1: f.t1, t2: f.t2, t3: f.t3 },
      override: ovrFlag ? ovrReason : '', created: new Date().toISOString(),
    };
  }

  function savePlan() {
    const f = readForm(), v = validate(fillTargets(Object.assign({}, f)), { recording: false });
    if (v.errs.length) { toast_(v.errs[0], 'err'); renderCalc(); return; }
    T.push(buildTrade(f, 'Planned')); persist(); ui.draft = null; toast_('Plan saved (not counted as an entry)', 'ok'); ui.tab = 'positions'; render();
  }
  function recordEntry() {
    const f = fillTargets(readForm()), v = validate(f, { recording: true });
    if (v.errs.length) { toast_(v.errs[0], 'err'); renderCalc(); return; }
    const hardBlocks = v.blocks, canOverride = S.allowOverride;
    if (hardBlocks.length && !(canOverride && f.ovr)) {
      const ovr = document.getElementById('jvOvr'); if (ovr) ovr.hidden = false;
      toast_((hardBlocks[0]) + (canOverride ? ' Enter an override reason to proceed.' : ' Entry blocked.'), 'err'); return;
    }
    const body = `<p><b>${E(f.dir)} ${E(f.instrument)}</b> @ ${px(f.entry)} · SL ${px(f.sl)} · qty ${f.qty}${f.mult > 1 ? ' × ' + f.mult : ''}</p>
      <p>Risk ${inr(v.risk, 0)} of budget ${inr(v.bud, 0)} · planned R:R ${v.plannedRR != null ? v.plannedRR.toFixed(2) : '—'}:1</p>
      ${hardBlocks.length ? `<p class="warn">Override: ${E(f.ovr)}<br>${hardBlocks.map(E).join('<br>')}</p>` : ''}
      <p class="muted">This records a simulated entry. No order is sent to any broker.</p>`;
    const go = () => {
      const t = buildTrade(f, 'Open', f.ovr, hardBlocks.length > 0);
      if (hardBlocks.length) t.overrideNotes = hardBlocks;
      T.push(t); persist(); ui.draft = null; if (window.closeModal) window.closeModal(); toast_('Entry recorded: ' + t.id, 'ok'); ui.tab = 'positions'; render();
    };
    if (window.modal) {
      window.modal('Confirm paper entry', body, { foot: '<button class="btn" data-jv="cancelmodal">Cancel</button><button class="btn pri" id="jvConfirm">Record entry</button>' });
      const b = document.getElementById('jvConfirm'); if (b) b.onclick = go;
    } else if (confirm('Record this paper entry?')) go();
  }

  /* ---------- trade detail ---------- */
  function openDetail(id) {
    const t = allTrades().find(x => x.id === id); if (!t) return; ui.sel = id;
    const c = calc(t), st = statusOf(t), u = unrealisedNet(t), rem = t.qty - c.qx;
    const legs = (t.exits || []).map((l, i) => `<tr><td>${i + 1}</td><td>${l.date} ${l.time || ''}</td><td>${E(l.type)}</td><td>${l.qty}</td><td>${px(l.price)}</td><td class="num ${cc(dirOf(t) * (l.price - t.entry))}">${sinr(dirOf(t) * (l.price - t.entry) * l.qty * units(t))}</td></tr>`).join('') || '<tr><td colspan="6" class="muted">No exits yet</td></tr>';
    const stops = (t.stops || []).map(s => `<li>${new Date(s.at).toLocaleString('en-IN')} — ${s.from == null ? 'set' : px(s.from) + ' → '}${px(s.to)} <small>${E(s.note || '')}</small></li>`).join('');
    const lock = t.auto ? `<p class="muted">Recorded automatically by the auto trader — plan, exit, costs, R multiple and review are filled in for you. Premium levels are estimates (delta 0.5); the stop and target that actually drive the trade are on the underlying.</p>
      ${t.raw && statusOf(t) !== 'Closed' ? `<p><b>Underlying stop now ${px(t.raw.stopU)}</b>${t.raw.targetU ? ' · target ' + px(t.raw.targetU) : ' · trailing exit'}${t.raw.tsl ? ' · your TSL: ' + E(t.raw.tsl.mode) + (t.raw.tsl.trail ? ' ' + t.raw.tsl.trail + ' pts' : '') + (t.raw.tsl.step ? ' step ' + t.raw.tsl.step + ' pts' : '') + (t.raw.tsl.trigger ? ' after ' + t.raw.tsl.trigger + 'R' : '') : ''}. You can exit now, add a trailing stop, or tighten the stop; a stop can never be loosened.</p>` : ''}`
      : st === 'Closed' ? '<p class="warn">Closed trade — edits are marked on the record and the original plan is preserved.</p>' : '';
    const body = `<div class="jv-detail">
      <div class="jv-calc-grid">
        <div><small>Status</small><b>${st}${t.edited ? ' · edited' : ''}</b></div><div><small>Entry</small><b>${px(t.entry)}</b></div>
        <div><small>Stop (current / initial)</small><b>${px(t.sl)} / ${px(t.sl0)}</b></div><div><small>Qty (open)</small><b>${rem} of ${t.qty}</b></div>
        <div><small>Initial risk</small><b>${inr(c.risk, 0)}</b></div><div><small>Net P&amp;L</small><b class="${cc(c.net)}">${c.qx ? sinr(c.net) : (u != null ? sinr(u) + ' open' : '—')}</b></div>
        <div><small>R multiple</small><b class="${cc(c.R)}">${rr(c.R)}</b></div><div><small>Costs + slippage</small><b>${inr(c.costs + c.slip)}</b></div></div>
      <p><b>Targets</b>: ${['t1', 't2', 't3'].map((k, i) => `<label class="jv-chk"><input type="checkbox" data-jv="hit" data-k="T${i + 1}" ${(t.hits || []).includes('T' + (i + 1)) ? 'checked' : ''}> T${i + 1} ${px(t[k])}</label>`).join(' ')}
        <span class="muted">hit order: ${(t.hitOrder || []).join(' → ') || '—'}</span></p>
      <p><b>TSL</b>: ${E(t.tsl || 'Off')} · highest fav <input class="inp jv-s" id="jd-hi" type="number" step="any" value="${t.hi ?? ''}"> · lowest fav <input class="inp jv-s" id="jd-lo" type="number" step="any" value="${t.lo ?? ''}"> <button class="btn-xs" data-jv="favsave" data-id="${t.id}">Save</button></p>
      <h4>Exit legs</h4><div class="tbl-wrap"><table class="jv-t"><thead><tr><th>#</th><th>When</th><th>Type</th><th>Qty</th><th>Price</th><th>P&amp;L</th></tr></thead><tbody>${legs}</tbody></table></div>
      <h4>Stop history</h4><ul class="jv-stops">${stops}</ul>
      ${lock}
      <h4>Review</h4>
      <div class="jv-rev"><label class="fld"><span>Rule followed?</span><select class="inp" id="jd-rule">${['', 'Yes', 'No', 'Partial'].map(x => `<option ${t.rule === x ? 'selected' : ''}>${x}</option>`).join('')}</select></label>
        <label class="fld"><span>Emotion / state</span><input class="inp" id="jd-emo" value="${E(t.emotion)}"></label>
        <label class="fld"><span>Mistake tags</span><input class="inp" id="jd-mis" value="${E(t.mistakes)}"></label>
        <label class="fld"><span>Screenshot / reference</span><input class="inp" id="jd-ref" value="${E(t.ref)}"></label>
        <label class="fld wide"><span>Lesson</span><textarea class="inp" id="jd-les" rows="2">${E(t.lesson)}</textarea></label>
        <label class="fld wide"><span>Reviewer notes</span><textarea class="inp" id="jd-rev" rows="2">${E(t.reviewer)}</textarea></label></div>
      ${t.why ? `<p class="muted"><b>Plan rationale:</b> ${E(t.why)}</p>` : ''}${t.override ? `<p class="warn"><b>Override:</b> ${E(t.override)}</p>` : ''}
    </div>`;
    const foot = t.auto ? ((st !== 'Closed' ? `<button class="btn pri" data-jv="autoexit" data-id="${t.id}">Exit now</button><button class="btn" data-jv="autotsl" data-id="${t.id}">Set TSL</button><button class="btn" data-jv="autostop" data-id="${t.id}">Move stop</button>` : '') + '<button class="btn" data-jv="cancelmodal">Close</button>') : ((t.status === 'Planned' ? `<button class="btn pri" data-jv="enterplan" data-id="${t.id}">Record entry now</button><button class="btn" data-jv="cancelplan" data-id="${t.id}">Cancel plan</button>` :
      st !== 'Closed' && t.status !== 'Cancelled' ? `<button class="btn" data-jv="movesl" data-id="${t.id}">Move stop</button><button class="btn" data-jv="settsl" data-id="${t.id}">Set TSL</button><button class="btn" data-jv="mktexit" data-id="${t.id}">Exit at market</button><button class="btn pri" data-jv="addexit" data-id="${t.id}">Add exit</button>` : '') +
      `<button class="btn" data-jv="savereview" data-id="${t.id}">Save review</button><button class="btn down" data-jv="deltrade" data-id="${t.id}" style="margin-left:auto">Delete entry</button>`);
    window.modal ? window.modal(`#${shortId(t)} · ${E(t.symbol || t.instrument)} ${t.dir}`, body, { foot, wide: true }) : alert('Detail unavailable');
  }

  function smallForm(title, bodyHtml, submitLabel, onSubmit) {
    const foot = `<button class="btn" data-jv="cancelmodal">Cancel</button><button class="btn pri" id="jvFormOk">${submitLabel}</button>`;
    window.modal(title, bodyHtml + '<p class="warn" id="jvFormErr" hidden></p>', { foot });
    const ok = document.getElementById('jvFormOk'), er = document.getElementById('jvFormErr');
    ok.onclick = () => { const msg = onSubmit(); if (msg) { er.textContent = msg; er.hidden = false; } };
  }
  function addExit(id) {
    const t = T.find(x => x.id === id); if (!t) return;
    const rem = t.qty - exitedQty(t);
    smallForm('Add exit · ' + t.id, `<div class="jv-form">
      <label class="fld"><span>Quantity (remaining ${rem})</span><input class="inp" id="jx-q" type="number" step="1" min="1" max="${rem}" value="${rem}"></label>
      <label class="fld"><span>Exit price</span><input class="inp" id="jx-p" type="number" step="any"></label>
      <label class="fld"><span>Exit type</span><select class="inp" id="jx-t">${EXIT_TYPES.map(x => `<option ${x === 'Manual Exit' ? 'selected' : ''}>${x}</option>`).join('')}</select></label></div>`,
      'Record exit', () => {
        const q = num(document.getElementById('jx-q').value), p = num(document.getElementById('jx-p').value), type = document.getElementById('jx-t').value;
        if (!(q >= 1) || Math.floor(q) !== q || q > rem) return 'Quantity must be a whole number up to ' + rem + '.';
        if (!(p > 0)) return 'Enter the exit price.';
        const now = new Date();
        t.exits.push({ qty: q, price: p, type, date: istDay(now), time: istTime(now) });
        if (/^T[123]$/.test(type) && !t.hits.includes(type)) { t.hits.push(type); t.hitOrder.push(type); }
        t.exitType = type;
        if (statusOf(t) === 'Closed') { t.closedAt = now.toISOString(); t.status = 'Closed'; }
        persist(); window.closeModal(); toast_('Exit recorded', 'ok'); render(); openDetail(id);
      });
  }
  function moveSL(id) {
    const t = T.find(x => x.id === id); if (!t) return;
    smallForm('Move stop · ' + t.id, `<p class="muted">A stop can only be tightened (${t.dir === 'Short' ? 'lowered' : 'raised'}) — never loosened to take more risk. Current stop ${px(t.sl)}.</p>
      <div class="jv-form"><label class="fld"><span>New stop-loss</span><input class="inp" id="jm-sl" type="number" step="any" value="${t.sl}"></label></div>`,
      'Move stop', () => {
        const v = num(document.getElementById('jm-sl').value), d = dirOf(t);
        if (!(v > 0)) return 'Enter a valid price.';
        if (d * (v - t.sl) < 0) return 'Not allowed: that would loosen the stop and increase risk.';
        if (v === t.sl) return 'The stop is unchanged.';
        t.stops.push({ at: new Date().toISOString(), from: t.sl, to: v, note: 'moved' }); t.sl = v;
        persist(); window.closeModal(); render(); openDetail(id);
      });
  }
  function autoExit(id) {
    const t = AUTO.list.find(x => x.id === id) || (AUTO.stockTrades || []).find(x => x.id === id); if (!t) return;
    const stk = !!t.isStock, seen = stk ? live(t.symbol || t.instrument) : null;      // a share trade is exited through the share trader's own endpoint (the button did nothing for shares)
    smallForm('Exit now · ' + t.id, `<p>Close <b>${E(t.symbol)}</b> at the live ${stk ? 'price' : 'bid'}? This ends the paper trade; you can't undo it.</p>`, 'Exit now', () => {
      const ok = document.getElementById('jvFormOk'); ok.disabled = true; ok.textContent = 'Exiting…';
      jpost((stk ? '/api/stockbot/trade/' : '/api/auto/trade/') + encodeURIComponent(id) + '/exit', stk && seen > 0 ? { seen } : undefined).then(async r => {
        ok.disabled = false; ok.textContent = 'Exit now';
        if (!r.ok) { const er = document.getElementById('jvFormErr'); er.textContent = r.err; er.hidden = false; return; }
        window.closeModal(); await syncAuto(true); render(); toast_(`Exited ${stk ? E(t.symbol) : '#' + shortId(t)} at ${px(r.d.exit)} · net ${sinr(r.d.net)}`, 'ok');
      });
      return null;
    });
  }
  function exitAll() {
    const open = allTrades().filter(t => entered(t) && statusOf(t) !== 'Closed');
    if (!open.length) { toast_('No open positions to exit.', 'warn'); return; }
    const unr = open.reduce((a, t) => a + (unrealisedNet(t) || 0), 0);
    smallForm('Exit all positions', `<p>Exit <b>${open.length}</b> open position${open.length === 1 ? '' : 's'} at live prices? Open P&L right now: <b class="${cc(unr)}">${sinr(unr)}</b>. This can't be undone.</p>`, 'Exit all', () => {
      const ok = document.getElementById('jvFormOk'), er = document.getElementById('jvFormErr'); ok.disabled = true;
      (async () => {
        let done = 0, fail = [], autoBulk = null, stockBulk = null; const now = new Date();
        for (const t of open) {
          ok.textContent = `Exiting ${done + fail.length + 1}/${open.length}…`;
          if (t.auto && t.isStock) {
            if (stockBulk === null) {                       /* the share trader is a separate book: it needs its own bulk exit (Exit all used to skip it: "Exited 0") */
              ok.textContent = 'Exiting shares…';
              const r = await jpost('/api/stockbot/exit-all'); stockBulk = r;
              if (r.ok) { done += r.d.closed || 0; (r.d.failed || []).forEach(f => fail.push(f)); } else fail.push('Shares: ' + r.err);
            }
            continue;
          }
          if (t.auto) {
            if (autoBulk === null) {                       /* every auto trade closes in ONE request (20 single calls hung on Vercel) */
              ok.textContent = 'Exiting auto trades…';
              const r = await jpost('/api/auto/exit-all'); autoBulk = r;
              if (r.ok) { done += r.d.closed || 0; (r.d.failed || []).forEach(f => fail.push(f)); } else fail.push('Auto trades: ' + r.err);
            }
            continue;
          }
          else if (t.paper) { if (typeof closePos === 'function') { closePos(t.symbol, 'manual'); done++; } else fail.push(t.symbol + ': Trade screen not loaded'); }
          else { const l = live(t.symbol || t.instrument), rem = t.qty - exitedQty(t);
            if (l == null) { fail.push(t.id + ': no live price'); continue; }
            t.exits.push({ qty: rem, price: +l.toFixed(2), type: 'Manual Exit', date: istDay(now), time: istTime(now) }); t.exitType = 'Manual Exit'; t.status = 'Closed'; t.closedAt = now.toISOString(); done++; }
        }
        persist(); await syncAuto(true);
        if (fail.length) { ok.disabled = false; ok.textContent = 'Exit all'; er.innerHTML = `Exited ${done}. Could not exit ${fail.length}:<br>${fail.map(E).join('<br>')}`; er.hidden = false; render(); return; }
        window.closeModal(); render(); toast_(`Exited ${done} position${done === 1 ? '' : 's'}`, 'ok');
      })();
      return null;
    });
  }
  function autoTsl(id) {
    const t = AUTO.list.find(x => x.id === id); if (!t || !t.raw) return;
    const a = t.raw, cur = a.tsl || {}, risk = a.riskU || 0;
    smallForm('Trailing stop · ' + t.id, `<p class="muted">Works on the underlying (${E(a.sym)}, now stop ${px(a.stopU)}). It only ever tightens the stop. Checked on every auto-trader cycle (about every 5 minutes in market hours).</p>
      <div class="jv-form"><label class="fld"><span>Mode</span><select class="inp" id="jt-mode">
        ${[['trail', 'Distance trail — stop follows the best price'], ['breakeven', 'Breakeven — move the stop to entry after a gain'], ['step', 'Step trail — raise the stop in steps'], ['off', 'Off — remove my trailing stop']].map(([k, l]) => `<option value="${k}" ${cur.mode === k ? 'selected' : ''}>${l}</option>`).join('')}</select></label>
        <label class="fld"><span>Trail distance (underlying points)</span><input class="inp" id="jt-trail" type="number" step="any" value="${cur.trail || Math.round(risk)}"></label>
        <label class="fld"><span>Breakeven trigger (R)</span><input class="inp" id="jt-trig" type="number" step="any" value="${cur.trigger || 1}"></label>
        <label class="fld"><span>Step size (underlying points)</span><input class="inp" id="jt-step" type="number" step="any" value="${cur.step || Math.round(risk / 2)}"></label></div>`,
      'Save TSL', () => {
        const mode = document.getElementById('jt-mode').value, ok = document.getElementById('jvFormOk');
        ok.disabled = true;
        jpost('/api/auto/trade/' + encodeURIComponent(id) + '/tsl', { mode, trail: num(document.getElementById('jt-trail').value), trigger: num(document.getElementById('jt-trig').value), step: num(document.getElementById('jt-step').value) }).then(async r => {
          ok.disabled = false;
          if (!r.ok) { const er = document.getElementById('jvFormErr'); er.textContent = r.err; er.hidden = false; return; }
          window.closeModal(); await syncAuto(true); render(); toast_(mode === 'off' ? 'Trailing stop removed' : 'Trailing stop set', 'ok');
        });
        return null;
      });
  }
  function autoStop(id) {
    const t = AUTO.list.find(x => x.id === id); if (!t || !t.raw) return;
    const a = t.raw;
    smallForm('Move stop · ' + t.id, `<p class="muted">Underlying ${E(a.sym)} stop is ${px(a.stopU)}. A ${a.side === 'BUY' ? 'long' : 'short'} stop can only move ${a.side === 'BUY' ? 'up' : 'down'}.</p>
      <div class="jv-form"><label class="fld"><span>New underlying stop</span><input class="inp" id="js-stop" type="number" step="any" value="${a.stopU}"></label></div>`,
      'Move stop', () => {
        const ok = document.getElementById('jvFormOk'); ok.disabled = true;
        jpost('/api/auto/trade/' + encodeURIComponent(id) + '/stop', { stopU: num(document.getElementById('js-stop').value) }).then(async r => {
          ok.disabled = false;
          if (!r.ok) { const er = document.getElementById('jvFormErr'); er.textContent = r.err; er.hidden = false; return; }
          window.closeModal(); await syncAuto(true); render(); toast_('Stop moved to ' + px(r.d.stopU), 'ok');
        });
        return null;
      });
  }
  function setManualTsl(id) {
    const t = T.find(x => x.id === id); if (!t) return;
    const r0 = Math.abs(t.entry - t.sl0);
    smallForm('Trailing stop · ' + t.id, `<p class="muted">Follows the live price of ${E(t.symbol || t.instrument)} while this page is open, only ever tightens the stop, and exits the rest of the position if the stop is reached. For contracts without a live price here, use "Move stop" and "Add exit" instead.</p>
      <div class="jv-form"><label class="fld"><span>Mode</span><select class="inp" id="jt-mode">${TSL_MODES.map(m => `<option ${t.tsl === m ? 'selected' : ''}>${E(m)}</option>`).join('')}</select></label>
        <label class="fld"><span>Activation / breakeven trigger (R)</span><input class="inp" id="jt-trig" type="number" step="any" value="${t.tslTrig == null ? 1 : t.tslTrig}"></label>
        <label class="fld"><span>Trail distance (price)</span><input class="inp" id="jt-trail" type="number" step="any" value="${t.trail || +r0.toFixed(2)}"></label>
        <label class="fld"><span>Step size (price)</span><input class="inp" id="jt-step" type="number" step="any" value="${t.step || +(r0 / 2).toFixed(2)}"></label></div>`,
      'Save TSL', () => {
        t.tsl = document.getElementById('jt-mode').value; t.tslTrig = num(document.getElementById('jt-trig').value);
        t.trail = num(document.getElementById('jt-trail').value); t.step = num(document.getElementById('jt-step').value);
        persist(); window.closeModal(); toast_('Trailing stop saved', 'ok'); applyManualTsl(); render(); return null;
      });
  }
  function marketExit(id) {
    const t = allTrades().find(x => x.id === id); if (!t) return;
    if (t.paper) {
      const sym = String(id).replace(/^P\|/, '');
      if (typeof closePos === 'function') { closePos(sym, 'manual'); setTimeout(render, 120); return; }
    }
    const l = live(t.symbol || t.instrument), rem = t.qty - exitedQty(t);
    if (l == null) { addExit(id); return; }                           // no live quote here: ask for the exit price instead
    smallForm('Exit at market · ' + t.id, `<p>Exit the remaining <b>${rem}</b> of <b>${E(t.symbol || t.instrument)}</b> at the live price <b>${px(l)}</b>?</p>`, 'Exit now', () => {
      const now = new Date();
      t.exits.push({ qty: rem, price: +l.toFixed(2), type: 'Manual Exit', date: istDay(now), time: istTime(now) });
      t.exitType = 'Manual Exit'; t.status = 'Closed'; t.closedAt = now.toISOString();
      persist(); window.closeModal(); toast_('Exited at ' + px(l), 'ok'); render(); return null;
    });
  }
  function saveReview(id) {
    const t = T.find(x => x.id === id); if (!t) return; const g = k => document.getElementById(k).value;
    const was = statusOf(t) === 'Closed';
    t.rule = g('jd-rule'); t.emotion = g('jd-emo'); t.mistakes = g('jd-mis'); t.ref = g('jd-ref'); t.lesson = g('jd-les'); t.reviewer = g('jd-rev');
    t.reviewed = !!(t.rule && t.lesson); if (was) t.edited = true;
    persist(); if (window.closeModal) window.closeModal(); toast_('Review saved', 'ok'); render();
  }

  /* ---------- Strategy lab / reports ---------- */
  function groupBy(list, keyFn, split) {
    const g = {}; list.forEach(t => { const v = (keyFn(t) || '—').toString(); (split ? v.split(',').map(s => s.trim()).filter(Boolean) : [v]).forEach(k => (g[k] = g[k] || []).push(t)); });
    return Object.keys(g).map(k => ({ k, m: metrics(g[k]), all: g[k].length })).sort((a, b) => b.m.net - a.m.net);
  }
  function groupTable(rows, label) {
    if (!rows.length) return '<div class="empty">No data yet.</div>';
    return `<div class="tbl-wrap"><table class="jv-t"><thead><tr><th>${label}</th><th>Trades</th><th>Closed</th><th>Win rate</th><th>Net P&amp;L</th><th>Avg R</th><th>PF</th><th>Max DD</th><th>T1 hit</th></tr></thead><tbody>` +
      rows.map(r => `<tr><td>${E(r.k)}</td><td>${r.all}</td><td>${r.m.n}</td><td>${(r.m.winRate * 100).toFixed(0)}%</td><td class="num ${cc(r.m.net)}">${sinr(r.m.net)}</td><td>${rr(r.m.expR)}</td><td>${r.m.pf === Infinity ? '∞' : r.m.pf.toFixed(2)}</td><td>${inr(r.m.maxDD, 0)}</td><td>${(r.m.t1 * 100).toFixed(0)}%</td></tr>`).join('') + '</tbody></table></div>' +
      (rows.some(r => r.m.n < 30) ? '<p class="muted">Samples under 30 closed trades are not enough to draw conclusions.</p>' : '');
  }
  function viewStrategy() {
    const L = filtered();
    return `${filterBar()}<div class="card"><div class="card-h"><h3>By strategy / setup</h3></div>${groupTable(groupBy(L, t => t.setup, false), 'Setup')}</div>
      <div class="card"><div class="card-h"><h3>By indicator</h3></div>${groupTable(groupBy(L, t => t.ind, true), 'Indicator')}</div>
      <div class="card"><div class="card-h"><h3>By instrument</h3></div>${groupTable(groupBy(L, t => t.instrument, false), 'Instrument')}</div>
      <div class="card"><div class="card-h"><h3>By direction / market</h3></div>${groupTable(groupBy(L, t => t.dir + ' · ' + t.market, false), 'Segment')}</div>`;
  }
  function periodTable(L, fmt, label) {
    const g = {}; L.forEach(t => { if (!entered(t)) return; (t.exits || []).forEach(l => { const k = fmt(l.date); g[k] = (g[k] || 0) + dirOf(t) * (l.price - t.entry) * l.qty * units(t) - (S.cost + S.slip) * units(t) * l.qty; }); });
    const ks = Object.keys(g).sort().reverse();
    return ks.length ? `<div class="tbl-wrap"><table class="jv-t"><thead><tr><th>${label}</th><th>Net P&amp;L</th></tr></thead><tbody>${ks.map(k => `<tr><td>${k}</td><td class="num ${cc(g[k])}">${sinr(g[k])}</td></tr>`).join('')}</tbody></table></div>` : '<div class="empty">No realised P&amp;L yet.</div>';
  }
  const weekKey = d => { const x = new Date(d + 'T00:00:00Z'); const day = (x.getUTCDay() + 6) % 7; x.setUTCDate(x.getUTCDate() - day); return 'Week of ' + x.toISOString().slice(0, 10); };
  function viewReports() {
    const L = filtered();
    return `${filterBar()}<div class="jv-actions"><button class="btn pri" data-jv="csv">Export trades (CSV, opens in Excel)</button><button class="btn" data-jv="csvsum">Export summary (CSV)</button></div>
      <div class="jv-grid"><div class="card"><div class="card-h"><h3>Daily</h3></div>${periodTable(L, d => d, 'Day')}</div>
      <div class="card"><div class="card-h"><h3>Weekly</h3></div>${periodTable(L, weekKey, 'Week')}</div>
      <div class="card"><div class="card-h"><h3>Monthly</h3></div>${periodTable(L, d => d.slice(0, 7), 'Month')}</div></div>
      <p class="muted">Dashboard totals reconcile to the journal rows for the selected date range and filters. Costs and slippage use the assumptions in Settings.</p>`;
  }
  function download(name, text) {
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob(['﻿' + text], { type: 'text/csv' })); a.download = name; document.body.appendChild(a); a.click(); a.remove();
  }
  const csvCell = v => '"' + String(v == null ? '' : v).replace(/"/g, '""') + '"';
  function exportCsv() {
    const rows = [['Trade ID', 'Date', 'Entry time', 'Market', 'Instrument', 'Symbol', 'Direction', 'Setup', 'Timeframe', 'Indicators', 'Entry', 'Initial SL', 'Current SL', 'T1', 'T2', 'T3', 'Qty', 'Multiplier', 'Initial risk', 'TSL mode', 'Targets hit', 'Exit type', 'Gross P&L', 'Costs', 'Slippage', 'Net P&L', 'R multiple', 'Status', 'Rule followed', 'Emotion', 'Lesson', 'Override', 'Edited']];
    filtered().forEach(t => { const c = calc(t); rows.push([t.id, t.date, t.time, t.market, t.instrument, t.symbol, t.dir, t.setup, t.tf, t.ind, t.entry, t.sl0, t.sl, t.t1, t.t2, t.t3, t.qty, t.mult, c.risk.toFixed(2), t.tsl, (t.hitOrder || []).join('>'), t.exitType || '', c.gross.toFixed(2), c.costs.toFixed(2), c.slip.toFixed(2), c.net.toFixed(2), c.R == null ? '' : c.R.toFixed(2), statusOf(t), t.rule, t.emotion, t.lesson, t.override, t.edited ? 'yes' : '']); });
    download('paper-journal-' + today() + '.csv', rows.map(r => r.map(csvCell).join(',')).join('\r\n'));
  }
  function exportSummary() {
    const m = metrics(filtered());
    const rows = [['Metric', 'Value'], ['Closed trades', m.n], ['Net P&L', m.net.toFixed(2)], ['Win rate', (m.winRate * 100).toFixed(1) + '%'], ['Expectancy (R)', m.expR.toFixed(2)], ['Profit factor', m.pf === Infinity ? 'inf' : m.pf.toFixed(2)], ['Max drawdown', m.maxDD.toFixed(2)], ['T1 hit rate', (m.t1 * 100).toFixed(1) + '%'], ['T2 hit rate', (m.t2 * 100).toFixed(1) + '%'], ['T3 hit rate', (m.t3 * 100).toFixed(1) + '%'], ['SL exits', m.slExits], ['TSL exits', m.tslExits], ['Note', 'PAPER TRADING — SIMULATED RESULTS']];
    download('paper-summary-' + today() + '.csv', rows.map(r => r.map(csvCell).join(',')).join('\r\n'));
  }

  /* ---------- Settings ---------- */
  function viewSettings() {
    const n = (k, l, step, hint) => `<label class="fld"><span>${l}</span><input class="inp" data-jset="${k}" type="number" step="${step || 'any'}" value="${S[k]}"><small>${hint || ''}</small></label>`;
    return `<div class="card"><div class="card-h"><h3>Risk &amp; limits</h3></div><div class="jv-form">
      ${n('capital', 'Starting virtual capital (₹)', 1000, 'Default ₹10,00,000')}${n('maxTrades', 'Max entries per day', 1, 'Each entry / re-entry counts; partial exits do not')}
      ${n('riskPct', 'Risk per trade (% of equity)', 0.05, 'Illustrative default 0.50%')}${n('dailyLossPct', 'Daily loss limit (% of start-of-day equity)', 0.1, 'Realised + unrealised')}
      ${n('maxOpen', 'Max open positions', 1)}${n('minRR', 'Minimum planned R:R', 0.1, 'Below this needs an override reason')}
      ${n('cost', 'Estimated cost per unit (₹)', 'any', '0 is only a placeholder — enter realistic costs')}${n('slip', 'Slippage per unit (₹)', 'any')}
      ${n('t1', 'Default T1 (R)', 0.25)}${n('t2', 'Default T2 (R)', 0.25)}${n('t3', 'Default T3 (R)', 0.25)}
      <label class="fld"><span>Allow rule overrides with a logged reason</span><select class="inp" data-jset="allowOverride"><option value="1" ${S.allowOverride ? 'selected' : ''}>Yes</option><option value="0" ${!S.allowOverride ? 'selected' : ''}>No — hard block</option></select></label>
      </div></div>
      <div class="card"><div class="card-h"><h3>Data</h3></div><div class="jv-actions"><button class="btn" data-jv="defaults">Reset settings to defaults</button><button class="btn" data-jv="wipe">Delete all journal records…</button></div>
      <p class="muted" style="padding:0 14px 12px">Records are stored in this browser. Export to CSV regularly — clearing site data removes them.</p></div>`;
  }

  /* ---------- TSL Lab (candle simulation) ---------- */
  const SIM_MODELS = [['fixed', 'Fixed SL'], ['be', 'Breakeven'], ['step', 'Step trail'], ['dist', 'Distance trail']];
  function simulate(t, bars, model, P) {
    const d = dirOf(t), r0 = Math.abs(t.entry - t.sl0), buf = S.cost + S.slip, final = t.t2 || t.t3 || t.t1;
    let stop = t.sl0, ext = t.entry, exit = null, reason = null, amb = false, missed = false, hit = { T1: false, T2: false, T3: false };
    const tg = { T1: t.t1, T2: t.t2, T3: t.t3 };
    for (let i = 0; i < bars.length; i++) {
      const b = bars[i];
      if (exit == null) {
        const sH = d > 0 ? b.l <= stop : b.h >= stop, tH = final ? (d > 0 ? b.h >= final : b.l <= final) : false;
        if (sH && tH) { amb = true; exit = stop; reason = 'Ambiguous'; }
        else if (sH) { exit = d > 0 ? Math.min(stop, b.o) : Math.max(stop, b.o); reason = stop === t.sl0 ? 'SL' : (model === 'be' ? 'Breakeven' : 'TSL'); }
        else {
          Object.keys(tg).forEach(k => { if (tg[k] && (d > 0 ? b.h >= tg[k] : b.l <= tg[k])) hit[k] = true; });
          if (tH) { exit = final; reason = t.t2 ? 'T2' : (t.t3 ? 'T3' : 'T1'); }
          else {
            ext = d > 0 ? Math.max(ext, b.h) : Math.min(ext, b.l);
            const fav = d * (ext - t.entry);
            let ns = stop;
            if (model === 'be' && fav >= P.trig * r0) ns = t.entry + d * buf;
            else if (model === 'step') { const sz = Math.max(P.step * r0, 1e-9); ns = t.sl0 + d * Math.floor(fav / sz) * sz; }
            else if (model === 'dist' && fav >= P.trig * r0) ns = ext - d * (P.trail * r0);
            stop = d > 0 ? Math.max(stop, ns) : Math.min(stop, ns);
          }
        }
      } else if (final && !missed && (reason === 'TSL' || reason === 'Breakeven' || reason === 'SL')) {
        if (d > 0 ? b.h >= final : b.l <= final) missed = true;       // the trail exited, then the target was reached later
      }
    }
    if (exit == null) { exit = bars.length ? bars[bars.length - 1].c : t.entry; reason = 'Time Exit'; }
    const net = d * (exit - t.entry) * t.qty * units(t) - buf * units(t) * t.qty, risk = initialRisk(t);
    return { exit, reason, net, R: risk > 0 ? net / risk : 0, amb, missed: missed && reason !== 'SL', hit };
  }
  async function runLab() {
    if (ui.labBusy) return; ui.labBusy = true; ui.lab = { rows: [], skipped: [] }; render();
    const P = { trig: S.labTrigger, step: S.labStep, trail: S.labTrail };
    const cand = T.filter(t => entered(t) && statusOf(t) === 'Closed' && t.entry && t.sl0);
    for (const t of cand) {
      const sym = (t.instrument || '').toUpperCase().replace(/\s+/g, '');
      try {
        const last = lastExit(t).slice(0, 10) || t.date;
        const span = Math.max(1, Math.round((new Date(last) - new Date(t.date)) / 864e5) + 1);
        const tf = span > 5 ? '15m' : '5m';
        const r = await fetch(`/api/m/candles?symbol=${encodeURIComponent(sym)}&tf=${tf}&from=${t.date}&to=${last}`);
        if (!r.ok) throw new Error('no candles');
        const j = await r.json(); const startMs = t.at ? Date.parse(t.at) : Date.parse(t.date + 'T09:15:00+05:30');
        const bars = (j.bars || []).filter(b => b.t >= startMs).map(b => ({ t: b.t, o: b.o, h: b.h, l: b.l, c: b.c }));
        if (!bars.length) throw new Error('no candles in window');
        ui.lab.rows.push({ t, sims: Object.fromEntries(SIM_MODELS.map(([k]) => [k, simulate(t, bars, k, P)])) });
      } catch (e) { ui.lab.skipped.push(t.id + ' (' + (t.instrument || '?') + ')'); }
    }
    ui.labBusy = false; render();
  }
  function viewTsl() {
    const L = ui.lab;
    const params = `<div class="jv-form"><label class="fld"><span>Breakeven / distance activation (R)</span><input class="inp" data-jset="labTrigger" type="number" step="0.1" value="${S.labTrigger}"></label>
      <label class="fld"><span>Step size (R)</span><input class="inp" data-jset="labStep" type="number" step="0.1" value="${S.labStep}"></label>
      <label class="fld"><span>Trail distance (R)</span><input class="inp" data-jset="labTrail" type="number" step="0.1" value="${S.labTrail}"></label></div>`;
    let out = '';
    if (ui.labBusy) out = '<div class="empty">Simulating on real candles…</div>';
    else if (L) {
      const agg = SIM_MODELS.map(([k, name]) => {
        const rs = L.rows.map(r => r.sims[k]).filter(s => !s.amb);
        const n = rs.length, net = rs.reduce((a, s) => a + s.net, 0), Rs = rs.map(s => s.R);
        const w = rs.filter(s => s.net > 0).reduce((a, s) => a + s.net, 0), l = Math.abs(rs.filter(s => s.net < 0).reduce((a, s) => a + s.net, 0));
        let cum = 0, pk = 0, dd = 0; rs.forEach(s => { cum += s.net; pk = Math.max(pk, cum); dd = Math.max(dd, pk - cum); });
        const cap = key => n ? rs.filter(s => s.hit[key]).length / n : 0;
        return { name, n, amb: L.rows.length - n, net, exp: n ? Rs.reduce((a, b) => a + b, 0) / n : 0, pf: l > 0 ? w / l : (w > 0 ? Infinity : 0), dd,
          t1: cap('T1'), t2: cap('T2'), t3: cap('T3'), early: n ? rs.filter(s => s.missed).length / n : 0, missed: rs.filter(s => s.missed).length };
      });
      out = `<div class="card"><div class="card-h"><h3>Same ${L.rows.length} trades · same assumptions</h3></div><div class="tbl-wrap"><table class="jv-t"><thead><tr><th>Method</th><th>Net P&amp;L</th><th>Avg R</th><th>Profit factor</th><th>Max DD</th><th>T1</th><th>T2</th><th>T3</th><th>Early-exit rate</th><th>Exited before a later target</th><th>Ambiguous</th></tr></thead><tbody>` +
        agg.map(a => `<tr><td><b>${a.name}</b></td><td class="num ${cc(a.net)}">${sinr(a.net)}</td><td>${rr(a.exp)}</td><td>${a.pf === Infinity ? '∞' : a.pf.toFixed(2)}</td><td>${inr(a.dd, 0)}</td><td>${(a.t1 * 100).toFixed(0)}%</td><td>${(a.t2 * 100).toFixed(0)}%</td><td>${(a.t3 * 100).toFixed(0)}%</td><td>${(a.early * 100).toFixed(0)}%</td><td>${a.missed}</td><td>${a.amb}</td></tr>`).join('') +
        `</tbody></table></div><p class="muted" style="padding:0 14px 12px">Ambiguous = a candle touched both the stop and the target; the order inside the candle is unknown, so those trades are excluded rather than assumed favourable. Skipped (no candle data): ${L.skipped.length ? E(L.skipped.join(', ')) : 'none'}.</p></div>`;
      if (!L.rows.length) out = '<div class="empty">None of the closed trades could be matched to candle data (instrument must be an NSE symbol the app knows).</div>';
    } else out = '<div class="empty">Runs fixed SL, breakeven, step trail and distance trail on the candles of every closed trade, with identical assumptions.</div>';
    return `<div class="card"><div class="card-h"><h3>TSL Lab</h3></div>${params}<div class="jv-actions"><button class="btn pri" data-jv="runlab" ${ui.labBusy ? 'disabled' : ''}>Run simulation</button></div></div>${out}
      <p class="muted">Do not conclude one trailing method is better until it is tested on a large, representative sample with realistic costs.</p>`;
  }


  /* ---------- Backtest + Auto Trader (server side; paper only) ---------- */
  const SV = { auto: null, bt: null, btBusy: false, loading: false, openDet: { btcResult: true } };
  /* a re-render rebuilds the DOM and would close every <details>; remember the open state of the
     ones marked with data-jvopen so the backtest filter / result / upcoming blocks stay as the user left them */
  document.addEventListener('toggle', e => { const d = e.target; if (d.matches && d.matches('[data-jvopen]')) { SV.openDet[d.dataset.jvopen] = d.open; } }, true);
  const detOpen = k => SV.openDet[k] ? ' open' : '';
  async function jget(url, opt) { const r = await fetch(url, Object.assign({ cache: 'no-store' }, opt || {})); if (!r.ok) throw new Error(url + ' ' + r.status); return r.json(); }
  async function loadSrv(which) {
    try {
      if (which === 'auto') SV.auto = await jget('/api/auto/status');
      else if (which === 'btc') { SV.btc = await jget('/api/backtest/custom'); SV.btcBusy = !!SV.btc.running; if (SV.btcBusy) setTimeout(() => { if (effTab() === 'algo' && !document.hidden) loadSrv('btc'); }, 5000); }
      else { const b = await jget('/api/backtest'); SV.bt = b; SV.btBusy = !!b.running; if (SV.btBusy) setTimeout(() => { if (effTab() === 'algo' && !document.hidden) loadSrv('bt'); }, 2000); }
    } catch (e) { if (which === 'auto') SV.auto = { error: String(e.message || e) }; else if (which === 'btc') SV.btc = { error: String(e.message || e) }; else SV.bt = { error: String(e.message || e) }; }
    const eff = effTab(); if (eff === which || (which === 'bt' && (eff === 'backtest' || eff === 'algo' || eff === 'portfolio')) || (which === 'btc' && eff === 'algo')) render();
  }
  const cfgName = r => r.variant === 'fixed' ? '1.5 ATR stop · 2R target' : r.variant === 'trail' ? '2 ATR trailing stop' : '2 ATR stop · exit on opposite signal';
  const KEYNAME = k => { try { const m = (typeof ST !== 'undefined' && ST.meta) ? ST.meta.strategies.find(x => x.key === k) : null; return m ? m.name : k; } catch (e) { return k; } };
  function twoMonthCard(e, title, note) {
    if (!e) return '';
    const t = e.twoMonth, s = e.stats;
    return `<div class="card"><div class="card-h"><h3>${title}</h3></div><div style="padding:6px 14px 14px">
      <p class="muted">${note}</p>
      <div class="jv-kpis">
        ${kpi('Median 2 months', sinr(t.median), 'typical window', cc(t.median))}
        ${kpi('Middle 80% range', sinr(t.p10) + ' to ' + sinr(t.p90), t.windows + ' rolling windows')}
        ${kpi('Worst / best', sinr(t.worst) + ' / ' + sinr(t.best))}
        ${kpi('Profitable windows', (t.profitableShare * 100).toFixed(0) + '%')}
        ${kpi('Entries', e.entries, 'win ' + (s.winRate * 100).toFixed(0) + '% · avg ' + rr(s.avgR) + ' · PF ' + (s.pf >= 99 ? '∞' : s.pf))}
        ${kpi('Max drawdown', inr(e.maxDrawdown, 0), 'on ₹5,000 risk per trade', 'down')}
      </div>
      <p class="muted">Strategies: ${e.strategies.map(k => E(KEYNAME(k))).join(', ')} · period ${e.from} → ${e.to}</p></div></div>`;
  }
  function viewBacktest() {
    const B = SV.bt;
    if (!B) { loadSrv('bt'); return '<div class="empty">Loading backtest…</div>'; }
    if (B.error) return `<div class="empty">Backtest unavailable (${E(B.error)}).</div>`;
    const run = `<div class="jv-actions"><button class="btn pri" data-jv="btrun" ${B.running ? 'disabled' : ''}>${B.running ? 'Running… ' + E(B.progress || '') : 'Re-run backtest'}</button></div>`;
    const R = B.result;
    if (!R) return `<div class="card"><div class="card-h"><h3>Backtest</h3></div><p class="muted" style="padding:0 14px">${B.running ? 'Running — this takes under a minute.' : 'No backtest has been run yet.'}</p>${run}</div>`;
    const proven = R.provenKeys.length;
    const verdict = proven
      ? `<b class="up">${proven} of ${R.strategiesTested} strategies</b> passed the in-sample and out-of-sample test.`
      : `<b class="down">None of the ${R.strategiesTested} strategies passed.</b> Settings that looked good on the first 70% of history did not hold up on the last 30%.`;
    const rows = R.ranking.map(r => {
      const i = r.inSample, o = r.outOfSample;
      return `<tr><td><b>${E(KEYNAME(r.key))}</b></td><td>${E(cfgName(r))}${r.filter === 'trend200' ? ' · with 200-EMA trend' : ''}</td>
        <td class="num">${i.n}</td><td class="num ${cc(i.avgR)}">${rr(i.avgR)}</td><td class="num">${i.pf >= 99 ? '∞' : i.pf.toFixed(2)}</td>
        <td class="num">${o.n}</td><td class="num ${cc(o.avgR)}">${rr(o.avgR)}</td><td class="num">${o.pf >= 99 ? '∞' : o.pf.toFixed(2)}</td>
        <td>${r.proven ? '<span class="badge b-up">Proven</span>' : '<span class="badge b-mute">' + E(r.reason) + '</span>'}</td></tr>`;
    }).join('');
    return `${run}<div class="card"><div class="card-h"><h3>Does it work? ${R.tradesSimulated.toLocaleString('en-IN')} simulated trades, ${R.historyFrom} → ${R.historyTo}</h3></div>
      <p style="padding:0 14px">${verdict}</p>
      <div class="tbl-wrap"><table class="jv-t"><thead><tr><th>Strategy</th><th>Exit style chosen on in-sample</th><th colspan="3">In-sample (to ${R.splitDate})</th><th colspan="3">Out-of-sample (after)</th><th>Verdict</th></tr>
      <tr><th></th><th></th><th>Trades</th><th>Avg R</th><th>PF</th><th>Trades</th><th>Avg R</th><th>PF</th><th></th></tr></thead><tbody>${rows}</tbody></table></div>
      <p class="muted" style="padding:6px 14px 12px">Pass = in-sample avg ≥ +0.12R and PF ≥ 1.25, <u>and</u> out-of-sample avg ≥ +0.08R and PF ≥ 1.15. R = profit as a multiple of the initial risk.</p></div>
      ${R.executor ? twoMonthCard(R.executor, 'What a 2-month run of the auto executor (no daily limit) would have returned', 'Proven strategies only, replayed on the out-of-sample period.') : ''}
      ${R.executorResearch ? twoMonthCard(R.executorResearch, proven ? 'Research basket (top in-sample strategies)' : 'If you forward-test the best in-sample strategies anyway', 'These strategies did <b>not</b> pass the out-of-sample test, so this is a research estimate, not evidence of an edge: ' + R.executorResearch.entries + ' trades is a small sample and the result is not statistically distinguishable from luck.') : ''}
      <div class="card"><div class="card-h"><h3>Read this before relying on any number</h3></div><ul class="jv-stops" style="padding:0 14px 12px 30px">${R.caveats.map(c => `<li>${E(c)}</li>`).join('')}</ul></div>`;
  }
  function viewAuto() {
    const A = SV.auto;
    if (!A) { loadSrv('auto'); return '<div class="empty">Loading auto trader…</div>'; }
    if (A.error) return `<div class="empty">Auto trader unavailable (${E(A.error)}).</div>`;
    const c = A.cfg, s = A.summary, idx = A.open.concat(A.closed).filter(t => t.date === A.today);
    const nIdx = idx.filter(t => t.kind === 'index').length, nStk = idx.filter(t => t.kind === 'stock').length;
    const unproven = /unproven/.test(A.mode);
    const trow = (t, open) => `<tr><td>${t.date}</td><td><b>${E(t.sym)}</b> ${t.strike} ${t.opt}<div class="muted" style="font-size:11px">${E(t.expiry)} · ${t.lots} lot × ${t.lot}</div></td>
      <td>${E(KEYNAME(t.strategy))}<div class="muted" style="font-size:11px">${E(t.source || t.variant || '')}</div></td><td class="num">${px(t.entry)}</td><td class="num">${px(open ? t.last : t.exit)}</td>
      <td class="num ${cc(open ? t.unrealised : t.net)}">${sinr(open ? (t.unrealised || 0) : t.net)}</td>
      <td class="num">${px(t.stopU)}${t.targetU ? ' / ' + px(t.targetU) : ''}</td><td>${open ? 'Open' : E(t.exitReason)}</td></tr>`;
    const tbl = (list, open) => { if (!list.length) return '<div class="empty">None yet.</div>'; const { part, bar } = pagerBar(list, open ? 'auto-open' : 'auto-closed');
      return `<div class="tbl-wrap"><table class="jv-t"><thead><tr><th>Date</th><th>Contract</th><th>Strategy</th><th>Entry ₹</th><th>${open ? 'Last' : 'Exit'} ₹</th><th>P&amp;L</th><th>Stop / target (underlying)</th><th>${open ? 'Status' : 'Exit reason'}</th></tr></thead><tbody>${part.map(t => trow(t, open)).join('')}</tbody></table></div>${bar}`; };
    const activityList = log => { if (!log.length) return '<p class="muted" style="padding:0 14px 12px">No activity yet. The first entries are made from 09:16 on the next trading day.</p>';
      const { part, bar } = pagerBar(log, 'activity');
      return `<ul class="jv-stops" style="padding:0 14px 12px 30px">${part.map(l => `<li>${new Date(l.at).toLocaleString('en-IN')} — ${E(l.msg)}</li>`).join('')}</ul>${bar}`; };
    return `<div class="card"><div class="card-h"><h3>Automated paper trades — every qualifying signal, no daily limit</h3></div>
      <div style="padding:0 14px 12px"><p>${unproven ? '<span class="badge b-down">UNPROVEN · forward test</span> ' : '<span class="badge b-up">Proven strategies</span> '}${E(A.mode)}.
        ${unproven ? 'No strategy passed the backtest, so these trades are a live, out-of-sample experiment: results here are the only evidence that can\'t be flattered by hindsight.' : ''}</p>
        <p class="muted">Simulated at live option prices — no broker is connected and no real order is ever sent. Buying starts at 09:16: strategy signals come from the previous session, the other slots from live screens. Exits follow the rule on the underlying. At most 5 entries a day.</p>
        ${A.shadow && A.shadow.summary && A.shadow.summary.length ? `<div style="margin-top:10px"><b>Testing week · paper-only signals (not traded)</b><div class="muted" style="font-size:12px">Entry at the live price, stop = the signal's own stop; each trade runs to its stop or 15:25 while we record how far it got (1.5R / 2R / 3R) - use this to pick the best stop and target for each strategy. Profit factor = gains / losses if every winner is taken at 1.5R.</div>
          <div style="overflow-x:auto"><table class="jv-tbl" style="width:100%;margin-top:6px"><tr><th align="left">Strategy</th><th>Signals</th><th>Win %</th><th>Avg R</th><th>Reached 1.5R</th><th>2R</th><th>3R</th><th>Profit factor</th><th>Avg stop</th></tr>${A.shadow.summary.map(o => `<tr><td>${E(o.key)}${o.open ? ` <span class="muted">(${o.open} open)</span>` : ''}</td><td align="center">${o.n}</td><td align="center">${Math.round(o.winRate * 100)}%</td><td align="center">${o.avgR}</td><td align="center">${Math.round(o.hit15 * 100)}%</td><td align="center">${Math.round(o.hit2 * 100)}%</td><td align="center">${Math.round(o.hit3 * 100)}%</td><td align="center">${o.pf == null ? '-' : o.pf}</td><td align="center">${o.avgStopPct}%</td></tr>`).join('')}</table></div></div>` : ''}
        <div class="jv-actions" style="padding:0"><button class="btn ${c.enabled ? '' : 'pri'}" data-jv="autotoggle">${c.enabled ? 'Pause auto trader' : 'Resume auto trader'}</button>
        <button class="btn" data-jv="autoresearch">${c.researchMode ? 'Research mode: ON (click to switch off)' : 'Research mode: OFF (click to switch on)'}</button>
        <button class="btn" data-jv="autoclassic" title="Classic mode trades: 1 / 2 indicators agree, stock screen, index call/put. Picks shortlist, Eagle, Gann angle, time cycle and Z Trend do not trade; they are logged as paper-only test signals (table below) so their accuracy can be compared.">${c.classicOnly === false ? 'Classic 4 types only: OFF (all strategies trade) - switch on' : 'Classic 4 types only: ON - switch off'}</button>
        <button class="btn" data-jv="autogann">${c.gannOn === false ? 'Gann angle: OFF (click to start)' : 'Gann angle: ON (click to stop)'}</button>
        <button class="btn" data-jv="autoeagle">${c.eagleOn ? 'Eagle Trades: ON (click to stop)' : 'Eagle Trades: OFF (click to start)'}</button>
        <button class="btn" data-jv="autostock" title="The separate share (equity) paper trader and its Stock trader tab. Rs 5 L of its own, next to the Rs 10 L option-buying book.">${c.stockTrader === false ? 'Stock trader (shares): OFF - switch on' : 'Stock trader (shares): ON - switch off'}</button>
        <button class="btn" data-jv="autopair">${c.pairSell === false ? 'Option SELL leg: OFF (buy-only) - switch on' : 'Option SELL leg: ON (buy + paired sell) - switch to buy-only'}</button>
        <button class="btn" data-jv="autolock">${c.lockMode === 'new' ? 'Profit lock: NEW (lock 2.5k, trail 3.5k+) - switch to old' : 'Profit lock: OLD (lock 1.5k, trail 2k+) - switch to new'}</button>
        <button class="btn" data-jv="autorefresh">Refresh</button></div></div></div>
      <div class="jv-kpis">
        ${kpi('Status', c.enabled ? (A.marketOpen ? 'Running' : 'Waiting for market') : 'Paused')}
        ${kpi('Entries today', A.todayCount + (c.maxPerDay ? ' / ' + c.maxPerDay : ''), 'index ' + nIdx + (c.indexSlots ? '/' + c.indexSlots : '') + ' · stock ' + nStk + (c.stockSlots ? '/' + c.stockSlots : '') + (c.maxPerDay ? '' : ' · no limit'))}
        ${kpi('Net P&L (closed)', sinr(s.net), s.trades + ' trades', cc(s.net))}
        ${kpi('Open P&L', sinr(s.openPnL), '', cc(s.openPnL))}
        ${kpi('Win rate', (s.winRate * 100).toFixed(0) + '%', 'avg ' + rr(s.avgR))}
        ${kpi('Equity', inr(s.equity, 0))}
      </div>
      <div class="card"><div class="card-h"><h3>Open positions</h3></div>${tbl(A.open, true)}</div>
      <div class="card"><div class="card-h"><h3>Closed trades</h3></div>${tbl(A.closed, false)}</div>
      <div class="card"><div class="card-h"><h3>Strategies in use</h3></div><div class="jv-list">${A.activeStrategies.length ? A.activeStrategies.map(a => `<div><span>${E(KEYNAME(a.key))}</span><b>${E(a.variant)}${a.filter === 'trend200' ? ' · 200-EMA trend' : ''}</b></div>`).join('') : '<div><span>None active</span><b>—</b></div>'}</div></div>
      <div class="card"><div class="card-h"><h3>Activity</h3>${A.log.length ? '<button class="btn-xs" data-jv="clearlog">Clear</button>' : ''}</div>${activityList(A.log)}</div>`;
  }

  /* ---------- your own trailing stop on MANUAL trades: ratchets with the live price while the journal is open ---------- */
  function applyManualTsl() {
    let changed = false;
    T.forEach(t => {
      if (!entered(t) || statusOf(t) === 'Closed') return;
      const mode = t.tsl; if (!mode || mode === 'Off / Fixed SL') return;
      const l = live(t.symbol || t.instrument); if (l == null) return;
      const d = dirOf(t), r0 = Math.abs(t.entry - t.sl0);
      if (d > 0) t.hi = Math.max(t.hi == null ? t.entry : t.hi, l); else t.lo = Math.min(t.lo == null ? t.entry : t.lo, l);
      const ext = d > 0 ? t.hi : t.lo, fav = d * (ext - t.entry);
      let ns = null;
      if (mode === 'Breakeven') { if (fav >= (t.tslTrig == null ? 1 : t.tslTrig) * r0) ns = t.entry; }
      else if (mode === 'Step Trail') { const st = t.step || r0 / 2, k = Math.floor(fav / st); if (k >= 1) ns = t.entry + d * (k - 1) * st; }
      else { const tr = t.trail || r0; if (fav >= (t.tslTrig == null ? 0 : t.tslTrig) * r0) ns = ext - d * tr; }
      if (ns != null && d * (ns - t.sl) > 0 && d * (l - ns) > 0) {                // only tighten, and only behind the price
        t.stops.push({ at: new Date().toISOString(), from: t.sl, to: +ns.toFixed(2), note: 'TSL' }); t.sl = +ns.toFixed(2); changed = true;
      }
      if (d * (l - t.sl) <= 0) {                                                    // stop reached: exit what is left at the live price
        const rem = t.qty - exitedQty(t);
        if (rem > 0) {
          const now = new Date(), type = t.sl === t.sl0 ? 'SL' : 'TSL';
          t.exits.push({ qty: rem, price: +l.toFixed(2), type, date: istDay(now), time: istTime(now) });
          t.exitType = type; t.status = 'Closed'; t.closedAt = now.toISOString(); changed = true;
          toast_(`#${shortId(t)}: ${type} hit — exited ${rem} at ${px(l)}`, 'warn');
        }
      }
    });
    if (changed) { persist(); if (document.getElementById('v-journal') && !document.querySelector('.modal-bg')) render(); }
  }

  /* ---------- summary strip: the same headline numbers at the top of every tab ---------- */
  function topStrip() {
    const all = allTrades(), m = metrics(all), day = today(), ds = dayStats(day);
    const LT = liveTotals(day);
    const todayBooked = ds.pnl + LT.autoToday;
    const unr = LT.unr;
    const todayTotal = todayBooked + unr;
    const totalBooked = LT.booked;
    const totalEquity = LT.eq;
    const open = all.filter(t => entered(t) && statusOf(t) !== 'Closed');
    const openAuto = open.filter(t => t.auto).length;
    const autoToday = AUTO.list.concat(AUTO.stockTrades || []).filter(t => t.date === day).length;
    return `<div class="jv-kpis jv-top" aria-label="Journal summary">
      ${kpi('Total Equity', inr(totalEquity, 0), unr ? 'open ' + sinr(unr) : 'no open P&L', cc(totalBooked + unr), 'Total portfolio equity: Capital (' + inrL(S.capital) + ') + Total Booked P&L + Open Unrealized P&L')}
      ${kpi("Today's P&L", sinr(todayTotal), 'booked ' + sinr(todayBooked) + ' · open ' + sinr(unr), cc(todayTotal), "Today's net P&L across all closed and open positions for the current session")}
      ${kpi('Total Booked P&L', sinr(totalBooked), m.n + ' closed trades', cc(totalBooked), 'All-time cumulative net P&L of all closed trades across the journal')}
      ${kpi('Open Positions', open.length, openAuto + ' auto · ' + (open.length - openAuto) + ' manual', '', 'Current active open positions')}
      ${kpi('Win Rate', (m.winRate * 100).toFixed(0) + '%', 'PF ' + (m.pf === Infinity ? '∞' : m.pf.toFixed(2)), '', 'Win rate and profit factor across closed trades')}
      ${(dd => kpi('Max DD · today', inr(dd, 0), 'all-time ' + inr(m.maxDD, 0), dd > 0 ? 'down' : '', "Largest fall of today's P&L (booked + open) from its high so far - resets every day"))(dayDD(day))}
    </div>`;
  }

  /* ---------- shell ---------- */
  function render() {
    const el = document.getElementById('v-journal'); if (!el) return;
    syncAuto(false);
    applyManualTsl();
    const head = `<div class="jv-head"><h1 title="Plan, log and review paper trades — portfolio, risk rules and analytics in one place">Journal</h1>${banner()}</div>`;
    const tabs = `<div class="jv-tabs" role="tablist">${TABS.filter(([k]) => k !== 'stocks' || !stockHidden()).map(([k, l]) => `<button role="tab" aria-selected="${ui.tab === k}" class="${ui.tab === k ? 'on' : ''}" data-jv="tab" data-k="${k}" title="${TAB_TIPS[k] || ''}">${l}</button>`).join('')}</div>`;
    const subtabs = GROUPS[ui.tab] ? `<div class="jv-tabs jv-subtabs" role="tablist">${GROUPS[ui.tab].map(([k, l]) => `<button role="tab" aria-selected="${ui.sub[ui.tab] === k}" class="${ui.sub[ui.tab] === k ? 'on' : ''}" data-jv="subtab" data-grp="${ui.tab}" data-k="${k}" title="${TAB_TIPS[k] || ''}">${l}</button>`).join('')}</div>` : '';
    const bodies = { portfolio: viewOverview, positions: viewPositions, algo: viewAlgo, picklog: () => `<section class="jv-card" style="padding:12px 14px"><h3 style="margin:0 0 4px">Picks log</h3><p class="muted" style="margin:0 0 8px;font-size:12px">SL 🚫 = stop-loss hit · T1 / T2 ✅ = target reached. Followed while the app is open and kept on this device for 14 days.</p><div id="jvPickLog">${window.pkLogHTML ? window.pkLogHTML() : ''}</div></section>`, stocks: () => sbCard(), new: viewNew };
    if (!bodies[ui.tab] || (ui.tab === 'stocks' && stockHidden())) ui.tab = 'portfolio';   // the Stock trader tab is hidden while it is switched off - never land on it
    el.innerHTML = `<div class="page jv">${head}${tabs}${subtabs}${ui.tab === 'new' || ui.tab === 'portfolio' || ui.tab === 'stocks' || ui.tab === 'picklog' ? '' : topStrip()}${bodies[effTab()]()}</div>`;
    if (ui.tab === 'portfolio') {
      const dEl = document.getElementById('jvChartData'); let d = { curve: [], dd: [], daily: [] };
      try { d = JSON.parse(dEl.textContent); } catch (e) { }
      requestAnimationFrame(() => {
        const a = document.getElementById('jvEq'), b = document.getElementById('jvDd'), c = document.getElementById('jvDay');
        a && drawLine(a, d.curve, css('--brand', '#4f8ef7'), true); b && drawLine(b, d.dd, css('--down', '#f7525f'), true); c && drawBars(c, d.daily);
      });
    }
    if (ui.tab === 'new') renderCalc();
  }

  /* ---------- events (tabs, entry form, exits, auto trader controls) ---------- */
  document.addEventListener('click', e => {
    const o = e.target.closest('[data-jvord]'); if (!o) return;
    if (typeof App !== 'undefined') App.ord = o.dataset.jvord;
    render();
  });
  document.addEventListener('click', e => {
    const b = e.target.closest('[data-jv]'); if (!b) return;
    const a = b.dataset.jv, id = b.dataset.id;
    if (a === 'reset' || a === 'moref') return;                       // own handlers
    if (!document.getElementById('v-journal') && !document.querySelector('.modal-bg')) return;
    if (a === 'tab') { ui.tab = b.dataset.k; if (ui.tab === 'algo') { SV.auto = null; SV.bt = null; } render(); window.scrollTo(0, 0); }
    else if (a === 'subtab') { ui.sub[b.dataset.grp] = b.dataset.k; render(); }
    else if (a === 'optchart') {
      const t = allTrades().find(x => String(x.id) === String(id)), r = optRef(t);
      if (!r) { toast_('This option position is no longer open', 'err'); return; }
      if (window.closeModal) try { closeModal(); } catch (e2) { }
      if (typeof openOptionFromScan === 'function') openOptionFromScan(r.sym, r.expiry, r.strike, r.side);
    }
    else if (a === 'open') openDetail(id);
    else if (a === 'clearf') { ui.f = { from: '', to: '', market: '', inst: '', setup: '', dir: '', exit: '', rule: '', src: '' }; render(); }
    else if (a === 'plan') savePlan();
    else if (a === 'enter') recordEntry();
    else if (a === 'resetform') { ui.draft = null; render(); }
    else if (a === 'cancelmodal') window.closeModal && window.closeModal();
    else if (a === 'addexit') addExit(id);
    else if (a === 'autoexit') autoExit(id);
    else if (a === 'exitall') exitAll();
    else if (a === 'autotsl') autoTsl(id);
    else if (a === 'autostop') autoStop(id);
    else if (a === 'settsl') setManualTsl(id);
    else if (a === 'mktexit') marketExit(id);
    else if (a === 'paperexit') { const sym = String(id).replace(/^P\|/, ''); if (typeof closePos === 'function') { closePos(sym, 'manual'); setTimeout(render, 120); } }
    else if (a === 'deltrade') {
      if (confirm('Delete this trade entry from your journal?')) {
        T = T.filter(x => x.id !== id);
        persist();
        if (typeof App !== 'undefined') {
          if (App.trades) {
            App.trades = App.trades.filter(x => x.id !== id && String(x.id) !== String(id) && ('PT|' + x.id) !== id);
            try { if (typeof saveTrades === 'function') saveTrades(); } catch (e) { }                 /* the real store (rs-trades-v1): the old code wrote a dead key, so deleted entries came back after a refresh */
          }
          if (App.positions) {
            const cleanSym = String(id).replace(/^P\|/, '');
            App.positions = App.positions.filter(p => p.sym !== cleanSym && ('P|' + p.sym) !== id);
            try { if (typeof savePaper === 'function') savePaper(); } catch (e) { }
          }
        }
        if (window.closeModal) window.closeModal();
        render();
        toast_('Entry removed', 'ok');
      }
    }
    else if (a === 'movesl') moveSL(id);
    else if (a === 'savereview') saveReview(id);
    else if (a === 'enterplan') { const t = T.find(x => x.id === id); if (t) { ui.draft = Object.assign({}, t, { instrument: t.instrument, why: t.why, entry: t.entry, sl: t.sl0 }); T = T.filter(x => x.id !== id); persist(); window.closeModal && window.closeModal(); ui.tab = 'new'; render(); } }
    else if (a === 'cancelplan') { const t = T.find(x => x.id === id); if (t) { t.status = 'Cancelled'; persist(); window.closeModal && window.closeModal(); render(); } }
    else if (a === 'favsave') { const t = T.find(x => x.id === id); if (t) { t.hi = num(document.getElementById('jd-hi').value); t.lo = num(document.getElementById('jd-lo').value); if (statusOf(t) === 'Closed') t.edited = true; persist(); toast_('Saved', 'ok'); } }
    else if (a === 'csv') exportCsv();
    else if (a === 'csvsum') exportSummary();
    else if (a === 'runlab') runLab();
    else if (a === 'btrun') {
      SV.bt = { running: true, progress: 'Starting backtest…', pct: 0, elapsed: 0, result: null };
      SV.btBusy = true;
      render();
      fetch('/api/backtest/run', { method: 'POST' }).then(() => loadSrv('bt'));
    }
    else if (a === 'autotoggle') { const cur = SV.auto && SV.auto.cfg ? SV.auto.cfg.enabled : (AUTO.srv ? AUTO.srv.enabled : null); if (cur == null) return;
      fetch('/api/auto/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ enabled: !cur }) }).then(() => { loadSrv('auto'); syncAuto(true).then(render); }); }
    else if (a === 'autoclassic') { const on = (SV.auto && SV.auto.cfg.classicOnly) === false; fetch('/api/auto/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ classicOnly: on }) }).then(() => loadSrv('auto')); }
    else if (a === 'autogann') { const on = (SV.auto && SV.auto.cfg.gannOn) === false; fetch('/api/auto/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ gannOn: on }) }).then(() => loadSrv('auto')); }
    else if (a === 'autoeagle') { const on = !(SV.auto && SV.auto.cfg.eagleOn); fetch('/api/auto/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ eagleOn: on }) }).then(() => loadSrv('auto')); }
    else if (a === 'autostock') { const cur = SV.auto && SV.auto.cfg ? SV.auto.cfg.stockTrader : (AUTO.srv && AUTO.srv.cfg ? AUTO.srv.cfg.stockTrader : false), on = (cur === false); fetch('/api/auto/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ stockTrader: on }) }).then(() => syncAuto(true)).then(() => { if (SV.auto) loadSrv('auto'); render(); }); }
    else if (a === 'autopair') { const m = !(SV.auto && SV.auto.cfg.pairSell === false) ? false : true; fetch('/api/auto/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ pairSell: m }) }).then(() => loadSrv('auto')); }
    else if (a === 'autolock') { const m = (SV.auto && SV.auto.cfg.lockMode === 'new') ? 'old' : 'new'; fetch('/api/auto/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ lockMode: m }) }).then(() => loadSrv('auto')); }
    else if (a === 'autoresearch') { const on = !(SV.auto && SV.auto.cfg.researchMode); fetch('/api/auto/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ researchMode: on }) }).then(() => loadSrv('auto')); }
    else if (a === 'refreshnow') { if (!AUTO.refreshing) { AUTO.refreshing = true; pullLive(true).then(refreshLive); syncAuto(true).catch(() => { }).then(() => { AUTO.refreshing = false; render(); }); } }
    else if (a === 'autorefresh') { loadSrv('auto'); syncAuto(true).then(render); }
    else if (a === 'exitf') { AUTO.exitFilter = b.dataset.k || ''; render(); }
    else if (a === 'trf') { AUTO.trFilter = b.dataset.k || ''; render(); }
    else if (a === 'btreset') {
      SV.bt = { running: false, result: null, cleared: true };
      SV.btc = null;
      render();
      fetch('/api/backtest/reset', { method: 'POST' })
        .then(r => r.json())
        .then(() => {
          toast_('Backtest result reset', 'ok');
          loadSrv('bt');
        });
    }
    else if (a === 'btcsel') { SV.btcSel = SV.btcSel || new Set(); const k = b.dataset.k; if (SV.btcSel.has(k)) SV.btcSel.delete(k); else SV.btcSel.add(k); render(); }
    else if (a === 'btcnone') { SV.btcSel = new Set(); render(); }
    else if (a === 'btrunf') { SV.btc = null; SV.btcBusy = true; fetch('/api/backtest/run?only=' + encodeURIComponent([...(SV.btcSel || [])].join(',')), { method: 'POST' }).then(() => loadSrv('btc')); }
    else if (a === 'uprefresh') { SV.up = null; SV.upBusy = true; render(); jget('/api/auto/preview').then(r => { SV.up = r; SV.upBusy = false; if (effTab() === 'algo') render(); }).catch(() => { SV.upBusy = false; SV.up = { error: true }; if (effTab() === 'algo') render(); }); }
    else if (a === 'clearlog') { if (confirm('Clear the auto trader activity log? This cannot be undone.')) jpost('/api/auto/log/clear').then(() => loadSrv('auto')); }
    else if (a === 'defaults') { S = Object.assign({}, DEFAULTS); persistS(); render(); }
    else if (a === 'wipe') { if (confirm('Delete ALL journal records on this device? Export first if you need them.')) { T = []; persist(); render(); } }
  });

  /* Reset portfolio: one confirmation, then clear EVERYTHING that feeds the portfolio figure -
     manual journal trades, journal settings, the server's auto paper trades and the Trade screen's paper account. */
  async function resetPortfolio(confirmed) {
    if (confirmed !== true && !confirm('Reset the portfolio to ' + inr(DEFAULTS.capital, 0) + '?\n\nThis clears every journal trade, all auto paper trades (open and closed), the stock trader book and the Trade screen paper positions and orders. It cannot be undone.')) return;
    const [r, rs] = await Promise.all([jpost('/api/auto/reset', {}), jpost('/api/stockbot/reset', {})]);   // options book AND the stock trader book
    T = []; S = Object.assign({}, DEFAULTS); persist(); persistS();
    AUTO.list = []; AUTO.stockTrades = []; AUTO.ts = Date.now();
    try { SB.d = null; SB.ts = 0; } catch (e) { }
    try { localStorage.setItem('mer-trades', '[]'); localStorage.setItem('mer-paper', '[]'); localStorage.removeItem('rs-last-pnl'); } catch (e) { }
    try {
      if (typeof App !== 'undefined') {
        App.cash = S.capital || 1000000; App.positions = []; App.orders = []; App.history = []; App.trades = []; App.meta = {};
        if (typeof saveTrades === 'function') saveTrades(); if (typeof savePaper === 'function') savePaper();
        if (typeof renderBottom === 'function') renderBottom(); if (typeof renderPfChip === 'function') renderPfChip();
        if (typeof setChartLines === 'function') try { setChartLines(); } catch (e) { }
      }
    } catch (e) { }
    const bad = [!r.ok && 'auto trades: ' + r.err, !rs.ok && 'stock trader: ' + rs.err].filter(Boolean);
    toast_(!bad.length ? 'Journal reset to ' + inr(DEFAULTS.capital, 0) + ' - all trades cleared' : 'Journal cleared on this device, but the server reset failed (' + bad.join('; ') + '). Tap Reset again.', !bad.length ? 'ok' : 'err');
    try { render(); } catch (e) { console.warn('journal render after reset', e); }
    setTimeout(() => { syncAuto(true).then(render).catch(() => { }); try { sbLoad(true); } catch (e) { } }, 600);
  }
  document.addEventListener('click', e => {
    const b = e.target.closest('[data-jv="reset"]'); if (!b) return;
    e.preventDefault(); e.stopImmediatePropagation(); resetPortfolio();
  }, true);

   /* ---------- Gods Eye - Monitoring Dashboard ---------- */
   function viewGodsEye() {
     const all = allTrades();
     const day = today();
     const todayStats = dayStats(day);
     const { open: openToday } = all.filter(t => entered(t) && statusOf(t) !== 'Closed');
     const livePrices = {};

     // Get current live prices for premium and index tracking
     const symbols = [...new Set(all.map(t => t.symbol || t.instrument).filter(Boolean))];
     if (symbols.length) {
       symbols.forEach(sym => {
         const price = live(sym);
         if (price != null) livePrices[sym] = price;
       });
     }

     // Calculate premium high/low for today
     const premiumData = all.filter(t => entered(t) && statusOf(t) !== 'Closed' && t.market === 'Options');
     const premiumHigh = premiumData.length ? Math.max(...premiumData.map(t => t.entry)) : null;
     const premiumLow = premiumData.length ? Math.min(...premiumData.map(t => t.entry)) : null;

     // Calculate index high/low for today
     const indexData = all.filter(t => entered(t) && statusOf(t) !== 'Closed' && t.market === 'Index');
     const indexHigh = indexData.length ? Math.max(...indexData.map(t => t.entry)) : null;
     const indexLow = indexData.length ? Math.min(...indexData.map(t => t.entry)) : null;

     // Calculate P&L summaries
     const totalEquity = equity() + livePrices.reduce((sum, price, sym) => {
       const trade = all.find(t => (t.symbol || t.instrument) === sym && entered(t) && statusOf(t) !== 'Closed');
       if (trade) {
         const qty = trade.qty - exitedQty(trade);
         const unrealized = unrealisedNet(trade);
         return sum + (unrealized || 0);
       }
       return sum;
     }, 0);

     const realizedPNL = realised();
     const openPNL = all.reduce((sum, t) => {
       if (entered(t) && statusOf(t) !== 'Closed') {
         const unrealized = unrealisedNet(t);
         return sum + (unrealized || 0);
       }
       return sum;
     }, 0);

     return `<div class="jv-grid">
       <div class="card"><div class="card-h"><h3>🎯 Premium Summary (Today)</h3></div>
         <div class="jv-list">
           <div><span>Premium Range</span><b>${premiumHigh != null && premiumLow != null ? px(premiumHigh) + ' - ' + px(premiumLow) : 'No premium trades'}</b></div>
           <div><span>High</span><b>${premiumHigh != null ? px(premiumHigh) : '—'}</b></div>
           <div><span>Low</span><b>${premiumLow != null ? px(premiumLow) : '—'}</b></div>
           <div><span>Count</span><b>${premiumData.length}</b></div>
         </div>
       </div>
       <div class="card"><div class="card-h"><h3>📈 Index Summary (Today)</h3></div>
         <div class="jv-list">
           <div><span>Index Range</span><b>${indexHigh != null && indexLow != null ? px(indexHigh) + ' - ' + px(indexLow) : 'No index trades'}</b></div>
           <div><span>High</span><b>${indexHigh != null ? px(indexHigh) : '—'}</b></div>
           <div><span>Low</span><b>${indexLow != null ? px(indexLow) : '—'}</b></div>
           <div><span>Count</span><b>${indexData.length}</b></div>
         </div>
       </div>
       <div class="card"><div class="card-h"><h3>💰 P&L Summary</h3></div>
         <div class="jv-list">
           <div><span>Total Equity</span><b class="${cc(totalEquity - S.capital)}">${inr(totalEquity, 0)}</b></div>
           <div><span>Realized P&L</span><b class="${cc(realizedPNL)}">${sinr(realizedPNL)}</b></div>
           <div><span>Open P&L</span><b class="${cc(openPNL)}">${sinr(openPNL)}</b></div>
           <div><span>Today P&L</span><b class="${cc(todayStats.pnl + todayStats.unrNet)}">${sinr(todayStats.pnl + todayStats.unrNet)}</b></div>
         </div>
       </div>
       <div class="card"><div class="card-h"><h3>📊 Live Prices</h3></div>
         <div class="jv-list">
           ${Object.entries(livePrices).length ? Object.entries(livePrices).map(([sym, price]) => `<div><span>${sym}</span><b>${px(price)}</b></div>`).join('') : '<div><span>No live prices available</span></div>'}
         </div>
       </div>
       <div class="card"><div class="card-h"><h3>⚡ Quick Actions</h3></div>
         <div class="jv-actions">
           <button class="btn pri" data-jv="reset">Reset Portfolio</button>
           <button class="btn" data-jv="enter">New Trade</button>
           <button class="btn" data-jv="exitall">Exit All Positions</button>
           <button class="btn" data-jv="csv">Export Trades</button>
         </div>
       </div>
     </div>`;
   }
  document.addEventListener('change', e => {
    const h = e.target.closest('[data-jv="hit"]');
    if (h) {
      const t = T.find(x => x.id === ui.sel); if (!t) return; const k = h.dataset.k;
      if (h.checked && !t.hits.includes(k)) { t.hits.push(k); t.hitOrder.push(k); } else if (!h.checked) { t.hits = t.hits.filter(x => x !== k); t.hitOrder = t.hitOrder.filter(x => x !== k); }
      if (statusOf(t) === 'Closed') t.edited = true; persist(); return;
    }
    const f = e.target.closest('[data-jf]'); if (f) { ui.f[f.dataset.jf] = f.value; render(); return; }
    const s = e.target.closest('[data-jset]');
    if (s) { const k = s.dataset.jset; S[k] = k === 'allowOverride' ? s.value === '1' : (num(s.value) ?? DEFAULTS[k]); persistS(); if (ui.tab === 'new') renderCalc(); }
    if (e.target.id === 'jf-market') { readForm(); render(); return; }
    if (['jf-strike', 'jf-opt', 'jf-expiry', 'jf-inst'].includes(e.target.id)) composeOptSymbol();
  });
  document.addEventListener('input', e => {
    if (e.target.closest('#jvForm')) { renderCalc(); if (['jf-strike', 'jf-inst'].includes(e.target.id)) composeOptSymbol(); }
    if (e.target.matches('[data-jf="inst"]')) { ui.f.inst = e.target.value; }
  });
  document.addEventListener('keydown', e => { const r = e.target.closest && e.target.closest('tr[data-jv="open"]'); if (r && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); openDetail(r.dataset.id); } });

  document.addEventListener('click', e => {
    const q = e.target.closest('[data-jvq]'), c = e.target.closest('[data-jvclr]'), pg = e.target.closest('[data-jvpg]'), ps = e.target.closest('[data-jvps]'), mf = e.target.closest('[data-jv="moref"]');
    if (!(q || c || pg || ps || mf) || !e.target.closest('#v-journal')) return;
    e.preventDefault(); e.stopPropagation();
    if (mf) { ui.moreF = !ui.moreF; render(); return; }
    if (q) { const [k, v] = q.dataset.jvq.split(':'); if (k === 'src') ui.f.src = v;
      else if (k === 'd') { const t = today(); if (v === 'all') { ui.f.from = ''; ui.f.to = ''; } else if (v === 'today') { ui.f.from = t; ui.f.to = t; } else { ui.f.from = istShift(v === '7d' ? 6 : 29); ui.f.to = ''; } }
      Object.values(ui.pg || {}).forEach(x => x.p = 0); render(); return; }
    if (c) { const k = c.dataset.jvclr; if (k === 'date') { ui.f.from = ''; ui.f.to = ''; } else ui.f[k] = ''; render(); return; }
    const [key, val] = (pg || ps).dataset[pg ? 'jvpg' : 'jvps'].split(':'), st = (ui.pg[key] = ui.pg[key] || { p: 0, s: 5 });
    if (pg) st.p = Math.max(0, +val); else { st.s = +val; st.p = 0; }
    const host = document.querySelector(`.jv-tw[data-jvt="${key}"]`), reg = ui.tbl && ui.tbl[key];
    if (host && reg) host.outerHTML = tradeTable(reg.list, reg.withUnr, key); else render();
  }, true);

/* ============================================
   SIMPLIFIED JOURNAL VIEWS - 3 TABS ONLY
   ============================================ */

   function viewPortfolio() {
     const all = allTrades();
     const m = metrics(all), day = today(), ds = dayStats(day);
     const LT = liveTotals(day), eq = LT.eq, unr = LT.unr;   // capital + booked + open at live prices
     const open = all.filter(t => entered(t) && statusOf(t) !== 'Closed');
     const net = LT.booked;
     const winRate = m.winRate * 100;
     
     // Premium/Index summary (Gods Eye + Vedic combined)
     const premiumData = all.filter(t => entered(t) && t.market === 'Options');
     const indexData = all.filter(t => entered(t) && t.market === 'Index');
     const premiumHigh = premiumData.length ? Math.max(...premiumData.map(t => t.entry)) : null;
     const premiumLow = premiumData.length ? Math.min(...premiumData.map(t => t.entry)) : null;
     const indexHigh = indexData.length ? Math.max(...indexData.map(t => t.entry)) : null;
     const indexLow = indexData.length ? Math.min(...indexData.map(t => t.entry)) : null;

     // Vedic Gann signals
     const gannSignal = getGannSignal();
     
     let cum = 0; const curve = [S.capital]; m.sorted.forEach(r => { cum += r.c.net; curve.push(S.capital + cum); });
     const daily = {}; m.sorted.forEach(r => { const d = lastExit(r.t).slice(0, 10); daily[d] = (daily[d] || 0) + r.c.net; });
     let pk = -Infinity; const dd = curve.map(v => { pk = Math.max(pk, v); return v - pk; });

     return `${filterBar(false)}
     <div class="jv-kpis" id="jvKpis">
       <div class="jv-kpi"><small>Total Equity</small><b>${inr(eq, 0)}</b></div>
       <div class="jv-kpi"><small>Closed P&L</small><b class="${cc(net)}">${sinr(net)}</b></div>
       <div class="jv-kpi"><small>Open P&L</small><b class="${cc(unr)}">${unr > 0 ? '+' + inr(unr, 0) : inr(unr, 0)}</b></div>
       <div class="jv-kpi"><small>Win Rate</small><b>${winRate.toFixed(0)}%</b></div>
       <div class="jv-kpi"><small>Positions</small><b>${open.length}</b></div>
       <div class="jv-kpi"><small>Today</small><b>${ds.entries}</b></div>
     </div>
     
     <div class="jv-grid">
       <div class="card"><div class="card-h"><h3>📊 Premium / Index Summary</h3></div>
         <div class="jv-list">
           <div><span>Premium Range</span><b>${premiumHigh != null && premiumLow != null ? px(premiumHigh) + ' - ' + px(premiumLow) : 'No premium trades'}</b></div>
           <div><span>Premium High</span><b>${premiumHigh != null ? px(premiumHigh) : '—'}</b></div>
           <div><span>Premium Low</span><b>${premiumLow != null ? px(premiumLow) : '—'}</b></div>
           <div><span>Index Range</span><b>${indexHigh != null && indexLow != null ? px(indexHigh) + ' - ' + px(indexLow) : 'No index trades'}</b></div>
           <div><span>Index High</span><b>${indexHigh != null ? px(indexHigh) : '—'}</b></div>
           <div><span>Index Low</span><b>${indexLow != null ? px(indexLow) : '—'}</b></div>
         </div>
       </div>
       <div class="card"><div class="card-h"><h3>🕉️ Vedic Gann Signal</h3></div>
         <div class="jv-list">
           <div><span>Signal</span><b class="${gannSignal.color}">${gannSignal.text}</b></div>
           <div><span>Action</span><b>${gannSignal.action}</b></div>
           <div><span>Level</span><b>${gannSignal.level}</b></div>
         </div>
       </div>
       <div class="card"><div class="card-h"><h3>📈 Equity Curve</h3></div><canvas class="jv-cv" id="jvEq"></canvas></div>
       <div class="card"><div class="card-h"><h3>📉 Drawdown</h3></div><canvas class="jv-cv" id="jvDd"></canvas></div>
       <div class="card"><div class="card-h"><h3>📅 Daily P&L</h3></div><canvas class="jv-cv" id="jvDay"></canvas></div>
       <div class="card"><div class="card-h"><h3>⚡ Quick Actions</h3></div>
         <div class="jv-actions">
           <button class="btn pri" data-jv="reset">Reset Portfolio</button>
           <button class="btn" data-jv="enter">New Trade</button>
           <button class="btn" data-jv="exitall">Exit All</button>
           <button class="btn" data-jv="csv">Export</button>
         </div>
       </div>
     </div>
     <script type="application/json" id="jvChartData">${JSON.stringify({ curve, dd, daily: Object.keys(daily).sort().map(k => daily[k]) })}</script>`;
   }

   function getGannSignal() {
     // Get Gann signal from the new indicators
     try {
       const bars = JSON.parse(localStorage.getItem('gann_bars') || '[]');
       if (!bars.length) return { text: 'No Data', color: '', action: 'Wait', level: '—' };
       const last = bars[bars.length - 1];
       if (last.signal === 'SELL_ON_RISE') return { text: 'SELL ON RISE 🔴', color: 'down', action: 'Sell', level: last.d1 ? px(last.d1) : '—' };
       if (last.signal === 'BUY') return { text: 'BUY 🟢', color: 'up', action: 'Buy', level: last.u1 ? px(last.u1) : '—' };
       if (last.signal === 'SELL') return { text: 'SELL 🔴', color: 'down', action: 'Sell', level: last.d1 ? px(last.d1) : '—' };
       return { text: 'HOLD ⚪', color: '', action: 'Wait', level: '—' };
     } catch (e) {
       return { text: 'N/A', color: '', action: '—', level: '—' };
     }
   }

   function posOpenPage() {
     const open = allTrades().filter(t => entered(t) && statusOf(t) !== 'Closed' && sideOk(t));
     return { open, ...pagerBar(open, 'po') };
   }
   function viewPositions() {
     const all = allTrades();
     const sigCard = sigResults(all);
     const allOpen = all.filter(t => entered(t) && statusOf(t) !== 'Closed');
     const { open, part, bar } = posOpenPage();
     const closedAll = all.filter(t => statusOf(t) === 'Closed').sort((a, b) => lastExit(b).localeCompare(lastExit(a)));
     const closed = closedAll.filter(sideOk), pc = pagerBar(closed, 'pc');
     const sw = `<div class="jv-pos-bar">${sideBar(allOpen.concat(closedAll))}<span class="muted" style="font-size:12px">Buy = long trades · Sell = short / option writing</span></div>`;
     const openCard = `<div class="card"><div class="card-h"><h3>Current Positions (${open.length})</h3></div>
       <div class="tbl-wrap" id="jvPosOpen" data-ids="${E(part.map(t => t.id).join(','))}">${open.length ? positionTable(part) : `<div class="empty">No open ${ui.side === 'buy' ? 'buy ' : ui.side === 'sell' ? 'sell ' : ''}positions. Place trades from the <b>Trade</b> screen (buy or sell, market or limit).</div>`}</div>${bar}
       <p class="muted" style="font-size:12px;margin:6px 2px 0">Auto profit lock on every trade (buy or sell): at ₹2,500 open profit the stop moves to cost + charges; from ₹3,500 it trails with breathing room (keeping 40%–65% of the best profit).</p></div>`;
     const closedCard = closed.length ? `<div class="card"><div class="card-h"><h3>Closed Positions (${closed.length})</h3></div><div class="tbl-wrap">${positionTable(pc.part)}</div>${pc.bar}</div>` : '';
     return sw + sigCard + openCard + closedCard;
   }

   /* accuracy of the Buy / Sell test trades placed from Trade -> Signals, per signal and side */
   function sigResults(all) {
     const done = all.filter(t => t.paper && t.sig && statusOf(t) === 'Closed');
     const openN = all.filter(t => t.paper && t.sig && statusOf(t) !== 'Closed').length;
     if (!done.length && !openN) return '';
     const g = {};
     done.forEach(t => { const k = t.sig, c = calc(t); (g[k] = g[k] || { n: 0, w: 0, net: 0 }); g[k].n++; if (c.net > 0) g[k].w++; g[k].net += c.net; });
     const rows = Object.entries(g).sort((a, b) => b[1].n - a[1].n).map(([k, v]) => `<tr><td><b>${E(k)}</b></td><td class="num">${v.n}</td><td class="num ${v.w / v.n >= 0.5 ? 'up' : 'down'}">${(v.w / v.n * 100).toFixed(0)}%</td><td class="num ${cc(v.net)}">${sinr(v.net)}</td></tr>`).join('');
     return `<div class="card"><div class="card-h"><h3>Signal test results</h3><span class="muted" style="font-size:12px">${done.length} closed · ${openN} open</span></div>
       ${rows ? `<div class="tbl-wrap"><table class="jv-t"><thead><tr><th>Signal · side</th><th class="num">Trades</th><th class="num">Win %</th><th class="num">Net P&amp;L</th></tr></thead><tbody>${rows}</tbody></table></div>` : '<div class="empty">Tests are open - results show here when they close.</div>'}
       <p class="muted" style="font-size:12px;margin:6px 2px 0">From the B / S buttons in Trade → Signals. BUY = the signal as given; SELL = the opposite trade with a small stop.</p></div>`;
   }

   /* quantity taken: auto option trades as lots and units (1 lot · 65), everything else in units */
  const qtyTxt = t => { const q = Number(t.qty) || 0, m = Number(t.mult) || 1; if (!q) return '—';
    return t.auto && m > 1 ? `${q} lot${q === 1 ? '' : 's'} · ${(q * m).toLocaleString('en-IN')}` : (q * m).toLocaleString('en-IN'); };
  function positionTable(trades) {
     if (!trades.length) return '<div class="empty">No positions</div>';
     const headers = ['Symbol', 'Side', 'Qty', 'Entry · in', 'SL', 'TSL', 'Target', 'R:R', 'LTP (₹)', 'P&L', 'Held', 'Exit'];
     const rows = trades.map(t => {
       const c = calc(t);
       const status = statusOf(t);
       const open = status !== 'Closed', u = open ? unrealisedNet(t) : null;
       const currentPrice = open ? curPx(t) : ((t.exits || []).slice(-1)[0] || {}).price;
       const pnl = open ? (u || 0) : (c.net || 0);
       const r0 = Math.abs(t.entry - t.sl0), rrv = r0 > 0 && t.t2 ? Math.abs(t.t2 - t.entry) / r0 : null;
       const pnlClass = pnl > 0 ? 'up' : pnl < 0 ? 'down' : '';
       const exitBtn = status !== 'Closed' ? `<button class="btn jv-exit" data-jv="${t.auto ? 'autoexit' : t.paper ? 'paperexit' : 'mktexit'}" data-id="${E(t.id)}" title="Exit at the live price">Exit</button>` : `<span class="muted">${E(t.exitType || 'Closed')}</span>`;
       return `<tr data-pid="${E(t.id)}"${t.auto ? ' class="auto-row"' : ''}>
         <td><span class="jv-sym"><b>${E(t.symbol || t.instrument)}</b>${eagleTag(t)}${chartBtn(t)}<small>${E(t.setup || '')}</small></span></td>
         <td><span class="jv-side ${t.dir === 'Long' ? 'l' : 's'}">${t.dir === 'Long' ? 'BUY' : 'SELL'}</span></td>
         <td class="num" title="Quantity taken">${qtyTxt(t)}</td>
         <td class="num" title="Taken ${entryTime(t) ? entryTime(t) : ''}">${px(t.entry)}${entryTime(t) ? ` <small class="muted">${entryTime(t)}</small>` : ''}</td>
         <td class="num" data-c="sl">${px(t.sl)}</td>
         <td class="num" data-c="tsl">${E(open ? tslShow(t) : '—')}</td>
         <td class="num">${px(t.t2)}</td>
         <td class="num">${rrv != null ? '1:' + rrv.toFixed(1) : '—'}</td>
         <td class="num" data-c="cur"><b>${px(currentPrice)}</b></td>
         <td class="num ${pnlClass}" data-c="pnl">${sinr(pnl)}</td>
         <td class="num" title="How long the trade was held (live while open)">${heldTxt(t)}</td>
         <td class="jv-xc">${exitBtn}</td>
       </tr>`;
     }).join('');
     return `<table class="jv-t"><thead><tr>${headers.map(h => `<th${h === 'Exit' ? ' class="jv-xc"' : ''}>${h}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table>`;
   }

   /* ---- Stock paper trader (server, its own Rs 5 L): intraday / swing / positional plans from Picks ---- */
   const SB = { d: null, ts: 0, busy: false };
   /* the share paper trader is switched off (switched off in settings): hide its book and tab while it holds nothing */
   function stockHidden() { const off = !!(AUTO.srv && AUTO.srv.cfg && AUTO.srv.cfg.stockTrader === false); const d = SB.d && SB.d.byHorizon ? SB.d : null; return off && !!d && !(d.used || d.booked || d.unrealised); }
   async function sbLoad(force) {
     if (SB.busy || (!force && Date.now() - SB.ts < 60000)) return;
     SB.busy = true;
     try { const r = await fetch('/api/stockbot/status', { cache: 'no-store' }); if (r.ok) SB.d = await r.json(); else if (!SB.d) SB.d = { error: r.status }; }
     catch (e) { if (!SB.d) SB.d = { error: 'network' }; }
     SB.ts = Date.now();                    // success OR failure: the next try waits (a failure used to retry in a tight loop)
     SB.busy = false;
     { const td = document.getElementById('jvToday'); if (td) { const t = document.createElement('div'); t.innerHTML = todayCard(); td.replaceWith(t.firstElementChild); } }
     { const bk = document.getElementById('jvBooks'); if (bk) { const t = document.createElement('div'); t.innerHTML = booksCard(); bk.replaceWith(t.firstElementChild); } }
     if (effTab() === 'stocks' && document.getElementById('jvSB')) { const el = document.getElementById('jvSB'); const t = document.createElement('div'); t.innerHTML = sbCard(); el.replaceWith(t.firstElementChild); }
   }
   setInterval(() => { const h = document.getElementById('jvSB'); if (h && h.offsetParent && !document.hidden && window.rjMkt()) sbLoad(false); }, 60000);
   function sbCard() {
     const d = SB.d;
     if (d && !d.byHorizon) return `<div class="card" id="jvSB"><div class="card-h"><h3>📈 Stock trader</h3></div><div class="empty">Stock trader status is unavailable right now. <button class="btn-xs" data-sb="reload">Retry</button></div></div>`;
     if (!d) { sbLoad(false); return `<div class="card" id="jvSB"><div class="card-h"><h3>📈 Stock trader</h3></div><div class="empty">Loading…</div></div>`; }
     const HZL = { intraday: 'Intraday', swing: 'Swing', positional: 'Positional' };
     const rows = Object.entries(d.byHorizon).map(([k, v]) => `<tr><td><b>${HZL[k]}</b></td><td class="num">${v.open}</td><td class="num">${v.closed}</td><td class="num ${v.winRate == null ? '' : v.winRate >= 50 ? 'up' : 'down'}">${v.winRate == null ? '—' : v.winRate + '%'}</td><td class="num">${v.pf == null ? '—' : v.pf}</td><td class="num ${cc(v.net)}">${sinr(v.net)}</td><td class="num ${cc(v.unrealised)}">${sinr(v.unrealised)}</td></tr>`).join('');
     const pc = pagerBar(d.closed, 'sbc');
     const po = pagerBar(d.open, 'sbo');
     const closed = pc.part.map(t => `<tr><td>${HZL[t.hz]}</td><td><span class="jv-side ${t.side === 'BUY' ? 'l' : 's'}">${t.side}</span></td><td><b>${E(t.sym)}</b></td><td class="num" title="Quantity taken">${qtyTxt(t)}</td><td class="num">${px(t.entry)}</td><td class="num">${px(t.exit)}</td><td>${E(t.exitReason)}</td><td class="num ${cc(t.net)}">${sinr(t.net)}</td><td class="muted">${E(String(t.date).slice(5))}</td></tr>`).join('');
     const open = po.part.map(t => { const up = t.side === 'BUY'; return `<tr><td>${HZL[t.hz]}</td><td><span class="jv-side ${up ? 'l' : 's'}">${t.side}</span></td><td><b>${E(t.sym)}</b><small class="muted" style="display:block">${E(t.why || '')}</small></td><td class="num" title="Quantity taken">${qtyTxt(t)}</td><td class="num">${px(t.entry)}</td><td class="num">${px(t.last)}</td><td class="num down">${px(t.stop)}${t.t1Hit ? ' <small class="up" title="Target 1 hit - stop at entry">BE</small>' : ''}${t.lockMoved ? ' <small class="up" title="Auto profit lock moved the stop (breakeven / trailing)">L</small>' : ''}</td><td class="num">${px(t.t1)} · ${px(t.t2)}</td><td class="num ${cc(t.unrealised)}">${sinr(t.unrealised || 0)}</td><td><button class="btn jv-exit" data-sb="exit" data-id="${E(t.id)}">Exit</button></td></tr>`; }).join('');
     return `<div class="card" id="jvSB"><div class="card-h"><h3>📈 Stock trader · ${inrL(d.capital)} (paper)</h3><span class="jv-hr"><span class="muted" style="font-size:12px">${d.lastRun ? 'last run ' + new Date(d.lastRun).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : 'waits for market hours'}</span><button class="btn" data-sb="reset">Reset</button></span></div>
       <div class="jv-capg"><div><small>Equity</small><b class="${cc(d.equity - d.capital)}">${inr(d.equity, 0)}</b><span class="muted">booked ${sinr(d.booked)} · open ${sinr(d.unrealised)}</span></div>
         <div><small>In use</small><b>${inr(d.used, 0)}</b><span class="muted">${(d.used / d.capital * 100).toFixed(1)}% of ${inrL(d.capital)}</span></div><div><small>Free cash</small><b class="up">${inr(d.cash, 0)}</b><span class="muted">${d.all.closed} closed · ${d.all.winRate == null ? '—' : d.all.winRate + '% won'}</span></div></div>
       <div class="tbl-wrap"><table class="jv-t"><thead><tr><th>Horizon</th><th class="num">Open</th><th class="num">Closed</th><th class="num">Win %</th><th class="num">PF</th><th class="num">Booked</th><th class="num">Open P&amp;L</th></tr></thead><tbody>${rows}</tbody></table></div>
       ${d.open.length ? `<h4 class="jv-sbh">Open (${d.open.length})</h4><div class="tbl-wrap"><table class="jv-t"><thead><tr><th>Horizon</th><th>Side</th><th>Stock</th><th class="num">Qty</th><th class="num">Entry</th><th class="num">LTP</th><th class="num">SL</th><th class="num">T1 · T2</th><th class="num">P&amp;L</th><th></th></tr></thead><tbody>${open}</tbody></table></div>${po.bar}` : '<div class="empty">No open stock trades. New ones are taken 09:20-14:30 (intraday until 13:30) from the Picks plans.</div>'}
       ${closed ? `<h4 class="jv-sbh">Closed (${d.closed.length})</h4><div class="tbl-wrap"><table class="jv-t"><thead><tr><th>Horizon</th><th>Side</th><th>Stock</th><th class="num">Qty</th><th class="num">Entry</th><th class="num">Exit</th><th>Why</th><th class="num">Net</th><th>Date</th></tr></thead><tbody>${closed}</tbody></table></div>${pc.bar}` : ''}
       </div>`;
   }
   document.addEventListener('click', e => { const b = e.target.closest('[data-sb]'); if (!b || !e.target.closest('#v-journal')) return; e.preventDefault(); e.stopPropagation();
     if (b.dataset.sb === 'reload') { SB.d = null; sbLoad(true); return; }
     if (b.dataset.sb === 'exit') { b.disabled = true; jpost('/api/stockbot/trade/' + encodeURIComponent(b.dataset.id) + '/exit').then(r => { if (!r.ok) toast_(r.err, 'warn'); sbLoad(true); }); }
     else if (b.dataset.sb === 'reset') smallForm('Reset everything', '<p>This clears <b>every</b> trade - options, share trades and the Trade screen paper positions - and starts again with full paper capital. The Reset button on the Journal home does exactly the same. It cannot be undone.</p>', 'Reset all', () => { window.closeModal && window.closeModal(); resetPortfolio(true); });
   }, true);

   /* two separate paper books: options / Trade screen (this journal) and the stock trader - options Rs 10 L, stock trader Rs 5 L */
   /* "Today" card: today's profit split by book into what is BOOKED (closed trades - locked in) and what is still OPEN (moves with
      price until the trade closes). Options Buy / Options Sell come from the journal trades; the stock trader from its own server book. */
   /* TODAY's share of an automated trade is the move since the start of TODAY - not since the entry. A trade carried from an earlier day used
      to put its whole open profit (and, when it closed, its whole result) into "Today's profit". Option trades: the server remembers the
      price at the first look of the day (baseDate / basePx); share trades: yesterday's close. Same rule as the server's day P&L guard. */
   function dayBase(t) {
     const day = today();
     if (t.date === day) return t.entry;                                    // opened today: the move since the entry is all today's
     if (t.isStock) { const s = typeof SYM === 'function' ? SYM(t.symbol || t.instrument) : null; return s && s.prev > 0 ? s.prev : null; }
     const r = t.raw || {};
     return r.baseDate === day && r.basePx > 0 ? r.basePx : null;           // not marked yet today: nothing has moved today as far as we know
   }
   function autoDay(t) {
     const day = today(), sg = dirOf(t), r = t.raw || {};
     const qty = t.isStock ? (t.qty || 0) : (r.lots || 0) * (r.lot || 0);
     if (statusOf(t) === 'Closed') {
       const when = String(r.closedAt || '').slice(0, 10) || lastExit(t).slice(0, 10);
       if (when !== day) return { b: 0, o: 0 };
       const net = typeof r.net === 'number' ? r.net : (calc(t).net || 0);
       if (t.date === day) return { b: net, o: 0 };
       const b0 = dayBase(t), ex = t.isStock ? r.exit : ((t.exits || []).slice(-1)[0] || {}).price;
       if (b0 == null || !(ex > 0)) return { b: net, o: 0 };               // carried and never marked today: its whole result is the best guess
       return { b: sg * (ex - b0) * qty - (Number(r.cost) || 0), o: 0 };
     }
     if (t.date === day) return { b: 0, o: unrealisedNet(t) || 0 };
     const b0 = dayBase(t); if (b0 == null) return { b: 0, o: 0 };
     const cur = markPx(t), pct = Number(r.costPctEff) || (t.isStock ? 0.1 : 0);
     return { b: 0, o: sg * (cur - b0) * qty - pct / 100 * cur * qty };       // only the cost of closing is still ahead; the entry cost was paid on an earlier day
   }
   /* Manual journal trades and open Trade-screen positions: same rule - a position taken on an earlier day counts only the move since yesterday's
      close (the live symbol's previous close; unknown -> the old since-entry figure, never a guess). Closed Trade-screen trades carry no open
      date, so they keep their whole result on the closing day. */
   function manualDay(t) {
     const day = today(), sg = dirOf(t), m = units(t), closed = statusOf(t) === 'Closed';
     const carried = !!t.date && t.date < day && !(t.paper && closed);
     let base = t.entry;
     if (carried) { const sy = typeof SYM === 'function' ? SYM(t.symbol || t.instrument) : null; base = sy && sy.prev > 0 ? sy.prev : null; }
     let b = 0, o = 0;
     if (t.paper) { if (closed && lastExit(t).slice(0, 10) === day) b = calc(t).net || 0; }
     else (t.exits || []).forEach(l => {
       if (l.date !== day) return;
       const cost = t.costOverride != null ? t.costOverride : (S.cost + S.slip) * m * l.qty;
       b += sg * (l.price - (base == null ? t.entry : base)) * l.qty * m - cost;
     });
     if (!closed) {
       if (carried && base != null) { const cur = curPx(t), rem = t.qty - exitedQty(t); o = sg * (cur - base) * rem * m - exitCostEst(t); }
       else o = unrealisedNet(t) || 0;
     }
     return { b, o };
   }
   function todayRows() {
     const day = today(), R = { buy: { b: 0, o: 0 }, sell: { b: 0, o: 0 }, stock: null };
     let carry = 0;
     allTrades().forEach(t => {
       if (!entered(t) || t.isStock) return;
       const k = dirOf(t) < 0 ? 'sell' : 'buy', closed = statusOf(t) === 'Closed';
       if (t.auto) { const x = autoDay(t); R[k].b += x.b; R[k].o += x.o; if (!closed) carry++; return; }
       const x = manualDay(t); R[k].b += x.b; R[k].o += x.o;
       if (!closed) carry++;
     });
     if ((AUTO.stockTrades || []).length) {                                   // per trade from the share trader's status: carried shares count only today's move
       R.stock = { b: 0, o: 0 };
       AUTO.stockTrades.forEach(t => { if (!entered(t)) return; const x = autoDay(t); R.stock.b += x.b; R.stock.o += x.o; });
     }
     const d = SB.d && SB.d.byHorizon ? SB.d : null;
     /* no per-trade list yet: show what is booked today and nothing running. The book's own "unrealised" is the move since ENTRY of every
        open share - it is not today's figure and made the card jump (-16,667 for a moment, then -31) when the list arrived. */
     if (!R.stock && d) R.stock = { b: (d.closed || []).filter(t => (t.closedAt || '').slice(0, 10) === day).reduce((a, t) => a + (t.net || 0), 0), o: 0, est: true, wait: !!(d.open || []).length };
     if (!R.stock) R.stock = { b: 0, o: 0, est: true };
     R.carry = carry;
     /* inputs still arriving (the first answer from the server / the live share feed after a page refresh): a carried open trade with no "yesterday's price" yet
        counts as 0 today - that made the number start low (-13k) and jump to the real one (-31k). Flag it so nobody shows that half-built figure. */
     R.pend = !AUTO.ts || (R.stock && R.stock.wait) || allTrades().some(t => (t.auto || t.isStock) && entered(t) && statusOf(t) !== 'Closed' && t.date !== day && dayBase(t) == null);
     return R;
   }
   /* THE one "today" figure: locked in + running, all three books. The Today card, the header chip and the Running-trades header all use it. */
   function todayTotal() {
     const R = todayRows(), b = R.buy.b + R.sell.b + R.stock.b, o = R.buy.o + R.sell.o + R.stock.o, day = today();
     const ready = !R.pend || (typeof performance !== 'undefined' && performance.now() > 25000);          // never wait longer than 25 s for a feed that does not come
     if (ready) { try { localStorage.setItem('rs-today-total', JSON.stringify({ day, v: b + o })); } catch (e) { } return { booked: b, open: o, total: b + o, ready: true }; }
     let held = null; try { const j = JSON.parse(localStorage.getItem('rs-today-total') || 'null'); if (j && j.day === day && typeof j.v === 'number') held = j.v; } catch (e) { }
     return { booked: b, open: o, total: held == null ? b + o : held, ready: false, held: held != null };     // not ready: show the last complete figure, not a half-built one
   }
   /* how old the option prices on screen are: the oldest "seen at" time the server stamped on a running option trade (it re-stamps it every time it marks the trade) */
   function priceAgeS() {
     const ts = AUTO.list.filter(t => t.status !== 'Closed' && t.raw && t.raw.lastAt).map(t => Date.parse(t.raw.lastAt)).filter(x => x > 0);
     return ts.length ? Math.max(0, Math.round((Date.now() - Math.min(...ts)) / 1000)) : null;
   }
   function liveBadge(mk) {
     if (!mk || !AUTO.list.some(t => t.status !== 'Closed')) return '';
     const a = AUTO.qTs && AUTO.qOk ? liveAgeS() : priceAgeS();
     if (a == null) return '<em class="jv-mkt" id="jvLiveB" title="Waiting for the first price">updating…</em>';
     const txt = a < 60 ? a + 's' : Math.floor(a / 60) + 'm ' + (a % 60) + 's';
     if (a <= 10) return `<em class="jv-mkt on" id="jvLiveB" title="Option prices are ${txt} old">● live · ${txt}</em>`;
     return `<em class="jv-mkt" id="jvLiveB" style="color:var(--down,#e5484d)" title="Option prices are ${txt} old - tap Refresh">prices ${txt} old</em>`;
   }
   function todayCard() {
     const AL = liveTotals(today());
     const R = todayRows(), mk = (typeof MKT !== 'undefined' && typeof MKT.open === 'boolean') ? MKT.open : ((typeof window.rjMkt === 'function') ? window.rjMkt() : false);
     const bk = R.buy.b + R.sell.b + R.stock.b, op = R.buy.o + R.sell.o + R.stock.o, TT = todayTotal(), tot = TT.total;
     const cls = tot > 0 ? 'up' : tot < 0 ? 'down' : '', box = tot > 0 ? 'jv-pos' : tot < 0 ? 'jv-neg' : '';
     /* 29 Oct, simplified (user: "too many numbers"): ONE big number (today), two plain parts (closed / open), then one short line per book. */
     const row = (name, x) => !x ? `<div class="jv-hr-row"><div class="jv-hr-name"><b>${name}</b></div><div class="jv-hr-n"><span class="muted">loading…</span></div></div>`
       : `<div class="jv-hr-row"><div class="jv-hr-name"><b>${name}</b><small>closed ${TT.ready ? sinr(x.b) : '…'} · open ${TT.ready ? sinr(x.o) : '…'}</small></div><div class="jv-hr-n"><div><span class="${TT.ready ? cc(x.b + x.o) : ''}">${TT.ready ? sinr(x.b + x.o) : '…'}</span></div></div></div>`;
     const used = x => x && (x.b || x.o || x.wait);
     return `<div class="card jv-hero ${box}" id="jvToday">
       <div class="jv-hero-top"><span>Today</span><em class="jv-mkt ${mk ? 'on' : ''}">${mk ? 'Market open' : 'Market closed'}</em>${liveBadge(mk)}<button class="btn" data-jv="refreshnow" title="Read the latest prices now" style="margin-left:auto;padding:2px 10px">${AUTO.refreshing ? 'Refreshing…' : '↻ Refresh'}</button></div>
       <div class="jv-hero-big ${cls}">${sinr(tot)}${TT.ready ? '' : ' <small class="muted" style="font-size:12px;font-weight:500">updating…</small>'}</div>
       <div class="jv-chips">
         <div class="jv-chip2"><small>Closed trades</small><b class="${cc(bk)}">${TT.ready ? sinr(bk) : '…'}</b><span>final</span></div>
         <div class="jv-chip2"><small>Open trades</small><b class="${cc(op)}">${TT.ready ? sinr(op) : '…'}</b><span>moves with the market</span></div>
       </div>
       ${row('Options bought', R.buy)}${used(R.sell) ? row('Options sold', R.sell) : ''}${used(R.stock) || R.stock ? row('Shares', R.stock) : ''}
       <p class="jv-hint" id="jvAllTime">Since the very start, all trades: <b class="${cc(AL.booked + AL.unr)}">${sinr(AL.booked + AL.unr)}</b>. Open trades change with every price tick, so the numbers move every few seconds. "Today" counts only what changed since this morning.</p></div>`;
   }
   function insightCard(m) {
     if (!m || m.n < 5) return `<div class="card jv-ins" id="jvInsight"><b>How you're doing</b><p>Not enough closed trades yet (${m ? m.n : 0}). Come back after about 5 closed trades.</p></div>`;
     const w = Math.round(m.winRate * 100), W = Math.abs(m.avgWin), Lo = Math.abs(m.avgLoss), ratio = Lo > 0 ? W / Lo : null;
     let verdict = '', cl = 'ok';
     if (ratio != null) {
       const need = Math.round(Lo / (W + Lo) * 100);
       if (ratio >= 1.5) { verdict = `Your wins are bigger than your losses - you only need to win about ${need}% of trades to make money.`; cl = 'pos'; }
       else if (ratio >= 1) { verdict = `Wins are a bit bigger than losses. You need to win about ${need}% of trades to break even; you win ${w}%.`; cl = w >= need ? 'pos' : 'neg'; }
       else { verdict = `Your average win is smaller than your average loss, so you must win more than ${need}% of trades just to break even (you win ${w}%). ${w >= need ? 'You are above that line, but only just.' : 'You are below that line - this is where money leaks.'}`; cl = w >= need + 8 ? 'ok' : 'neg'; }
     }
     return `<div class="card jv-ins jv-i-${cl}" id="jvInsight"><b>Wins vs losses</b>
       <div class="jv-ins-g"><div><small>Win rate</small><b>${w}%</b></div><div><small>Average win</small><b class="up">${inr(W, 0)}</b></div><div><small>Average loss</small><b class="down">−${inr(Lo, 0)}</b></div>
       <div title="How many rupees you win for every rupee you lose, on average"><small>Win : Loss size</small><b class="${ratio != null && ratio >= 1 ? 'up' : 'down'}">${ratio == null ? '-' : ratio.toFixed(2) + ' : 1'}</b></div></div>
       <p>${verdict}</p></div>`;
   }
   /* Which part of the auto trader makes or loses the money: the entry itself, the PAIRED SELL leg the bot writes next to every entry
      (id ends -W; it is a short option on the other side of the chain, so it is NOT a hedge - it adds to the same directional bet),
      and the hedge leg of a credit spread (-X). All-time booked, booked today and running now, each on its own. */
   function legCard() {
     const day = today(), G = { main: { n: 0, b: 0, t: 0, o: 0 }, w: { n: 0, b: 0, t: 0, o: 0 }, x: { n: 0, b: 0, t: 0, o: 0 } };
     AUTO.list.forEach(t => {
       if (!entered(t)) return;
       const id = String(t.id), k = /-W$/.test(id) ? 'w' : /-X$/.test(id) ? 'x' : 'main', g = G[k];
       if (statusOf(t) === 'Closed') { const c = calc(t).net || 0; g.n++; g.b += c; if (lastExit(t).slice(0, 10) === day) g.t += c; }
       else g.o += unrealisedNet(t) || 0;
     });
     const row = (name, hint, g) => `<div class="jv-hr-row"><div class="jv-hr-name"><b>${name}</b><small>${hint}</small></div><div class="jv-hr-n"><div><small>All-time locked in</small><span class="${cc(g.b)}">${sinr(g.b)}</span></div><div><small>Today locked in</small><span class="${cc(g.t)}">${sinr(g.t)}</span></div><div><small>Running now</small><span class="${cc(g.o)}">${sinr(g.o)}</span></div></div></div>`;
     if (!G.main.n && !G.w.n && !G.x.n && !G.main.o && !G.w.o && !G.x.o) return '';
     return `<div class="card jv-hero" id="jvLegs"><div class="jv-hero-top"><span>Which trades make the money?</span></div>
       ${row('Entry trades', `${G.main.n} closed`, G.main)}${row('Paired sell legs', `${G.w.n} closed · sold next to each entry, not a hedge`, G.w)}${row('Spread hedge legs', `${G.x.n} closed`, G.x)}
       <p class="jv-hint">A paired sell leg is an option the bot sells on the other side of each entry. It makes money when your entry is right and loses money when it is wrong, so it adds to your risk instead of reducing it. If its row is negative over many trades, it is costing you.</p></div>`;
   }
   function booksCard() {
     const d = SB.d && SB.d.byHorizon ? SB.d : null; if (!d) sbLoad(false);
     const day = today(), L = liveTotals(day), c = capUse(), ds = dayStats(day), oToday = ds.pnl + L.autoToday + L.unr;
     const sCap = d ? d.capital : 500000;
     // compact: name, equity (+change), then Open, Booked, In use, Free - two cards per row on phones
     const v = (k, x, cl, fmt) => `<div><small>${k}</small><b class="${x == null ? '' : cl === 'pl' ? cc(x) : cl || ''}">${x == null ? '…' : fmt(x)}</b></div>`;
     const amt = x => inr(x, 0);
     const tile = (cls, title, eq, cap, open, booked, used, free) => `<div class="jv-book ${cls}"><b class="jv-bt">${title}</b>
       <div class="jv-beq"><span>${eq == null ? '…' : inr(eq, 0)}</span><em class="${eq == null ? '' : cc(eq - cap)}">${eq == null ? '' : sinr(eq - cap)}</em></div>
       <div class="jv-bl">${v('Running now', open, 'pl', sinr)}${v('Locked in', booked, 'pl', sinr)}${v('In trades', used, '', amt)}${v('Available', free, 'up', amt)}</div></div>`;
     const B = c.buy, Sx = c.sell;
     const ob = tile('', 'Options Buy', B.eq, B.cap, B.unr, B.booked, B.used, B.free);
     const buyOnly = !!(AUTO.srv && AUTO.srv.cfg && AUTO.srv.cfg.buyOnly), sellIdle = !(Sx.used || Sx.booked || Sx.unr);
     const hideSell = buyOnly && sellIdle;                                   // buy-only auto trader and no sold options: the sell book is not shown or counted
     const os = hideSell ? '' : tile('', 'Options Sell', Sx.eq, Sx.cap, Sx.unr, Sx.booked, Sx.used, Sx.free);
     const hideStock = stockHidden();
     const st = hideStock ? '' : tile('', 'Stock trader', d ? d.equity : null, sCap, d ? d.unrealised : null, d ? d.booked : null, d ? d.used : null, d ? d.cash : null);
     const X = hideSell ? { eq: 0, cap: 0, unr: 0, booked: 0, used: 0, free: 0 } : Sx;
     const Z = hideStock ? { equity: 0, unrealised: 0, booked: 0, used: 0, cash: 0 } : d;
     const zCap = hideStock ? 0 : sCap;
     const tot = tile('jv-btot', 'Total', d ? B.eq + X.eq + Z.equity : null, B.cap + X.cap + zCap,
       d ? B.unr + X.unr + Z.unrealised : null, d ? B.booked + X.booked + Z.booked : null,
       d ? B.used + X.used + Z.used : null, d ? B.free + X.free + Z.cash : null);
     return `<div class="card" id="jvBooks"><div class="card-h"><h3>Your money</h3><span class="muted" style="font-size:12px">paper money · ${inrL(B.cap + X.cap + zCap)} ${hideStock && hideSell ? 'options (buy only)' : 'in all'}</span><div class="jv-actions"><button class="btn" data-jv="reset" title="Reset the whole journal: options book back to its starting money and the stock trader back to ₹10 L">Reset journal</button></div></div>
       <div class="jv-books">${ob}${os}${st}${tot}</div></div>`;
   }

   function viewAlgo() {
     const auto = AUTO.list;
     const openAuto = auto.filter(t => entered(t) && statusOf(t) !== 'Closed');
     const closedAuto = auto.filter(t => statusOf(t) === 'Closed');
     
     // Backtest data: the real /api/backtest result (same one the backtest screen used)
     const srv = AUTO.srv;
     if (!srv && !AUTO.busy) setTimeout(() => syncAuto(true), 0);
     const stTxt = !srv ? (AUTO.err ? 'Server not reachable · retrying' : 'Loading…')
       : !srv.enabled ? 'Paused' : srv.marketOpen ? `Running · ${srv.todayCount} trades today` : 'On · market closed';
     const stCls = !srv ? '' : !srv.enabled ? 'down' : srv.marketOpen ? 'up' : '';


     // exit-reason breakdown + filter for the auto trades (raw server exit reasons: STOP / TSL / TARGET / TIME / EXPIRY / MANUAL)
     const autoAll = allTrades().filter(t => t.auto && entered(t));
     const closedAutoAll = autoAll.filter(t => statusOf(t) === 'Closed');
     const exKey = t => (t.raw && t.raw.exitReason) || t.exitType || '—';
     const EXF = [['', 'All'], ['STOP', 'SL'], ['TSL', 'TSL'], ['TARGET', 'Target'], ['TIME', 'Time'], ['EXPIRY', 'Expiry'], ['MANUAL', 'Manual']];
     const exitFilter = AUTO.exitFilter || '';
     const byExit = {};
     closedAutoAll.forEach(t => {
       const k = exKey(t);
       const row = byExit[k] || (byExit[k] = { n: 0, net: 0, w: 0 });
       const net = calc(t).net || 0;
       row.n++; row.net += net; if (net > 0) row.w++;
     });
     const exitRows = Object.entries(byExit).sort((a, b) => b[1].n - a[1].n).map(([k, v]) =>
       `<tr class="${exitFilter === k ? 'sel' : ''}"><td>${E(k)}</td><td class="num">${v.n}</td><td class="num ${cc(v.net)}">${sinr(v.net)}</td><td class="num">${v.n ? Math.round(v.w / v.n * 100) : 0}%</td></tr>`).join('');
     const exFiltered = exitFilter ? closedAutoAll.filter(t => exKey(t) === exitFilter) : closedAutoAll;

     return `<div class="jv-grid">
       <div class="card"><div class="card-h"><h3>🤖 Auto Trader Status</h3></div>
         <div class="jv-list">
           <div><span>Status</span><b class="${stCls}">${stTxt}</b></div>
           <div><span>Open Auto Trades</span><b>${openAuto.length}</b></div>
           <div><span>Closed Today</span><b>${closedAuto.filter(t => t.date === today()).length}</b></div>
           <div><span>Total Auto P&L</span><b class="${cc(auto.reduce((s, t) => s + (calc(t).net || 0), 0))}">${sinr(auto.reduce((s, t) => s + (calc(t).net || 0), 0))}</b></div>
           ${srv && srv.dayPnl && srv.dayPnl.limit ? `<div><span>Day P&L guard</span><b class="${srv.dayPnl.mode === 'blocked' ? 'down' : srv.dayPnl.mode === 'soft' ? '' : 'up'}" title="${E(srv.dayPnl.note || '')}">${sinr(srv.dayPnl.value)} · ±${inr(srv.dayPnl.limit, 0)}${srv.dayPnl.mode === 'blocked' ? ' · blocked' : srv.dayPnl.mode === 'soft' ? ' · soft zone' : ''}</b></div>` : ''}
         </div>
         <div class="jv-actions">
           ${srv ? `<button class="btn ${srv.enabled ? '' : 'pri'}" data-jv="autotoggle">${srv.enabled ? 'Pause auto trader' : 'Resume auto trader'}</button>` : ''}
           ${srv && srv.cfg ? `<button class="btn" data-jv="autostock" title="The separate share (equity) paper trader and its Stock trader tab. Rs 5 L of its own, next to the Rs 10 L option-buying book.">${srv.cfg.stockTrader === false ? 'Stock trader (shares): OFF - switch on' : 'Stock trader (shares): ON - switch off'}</button>` : ''}
           <button class="btn" data-jv="autorefresh">Refresh</button>
         </div>
       </div>

       ${srv && srv.sleeves && srv.sleeves.length ? `<div class="card"><div class="card-h"><h3>💼 Capital · ${inr(srv.sleeves.reduce((x, r) => x + r.capital, 0), 0)}</h3>
         <span class="muted" style="font-size:12px">${srv.cfg && srv.cfg.buyOnly ? 'buying only (calls + puts)' : 'buy + sell'} · ${srv.cfg && srv.cfg.stockOnly ? 'stock options only' : 'stock + index options'}</span></div>
         <div class="tbl-wrap"><table class="jv-t"><thead><tr><th>Sleeve</th><th class="num">In trades</th><th class="num">Open</th><th class="num">Closed P&L</th></tr></thead><tbody>
         ${srv.sleeves.map(r => `<tr><td><b>${E(r.name)}</b><br><small class="muted">${inr(r.capital, 0)}</small></td><td class="num">${inr(r.deployed, 0)}</td><td class="num">${r.open}${r.open ? `<br><small class="${cc(r.openPnL)}">${sinr(r.openPnL)}</small>` : ''}</td><td class="num ${cc(r.net)}">${sinr(r.net)}<br><small class="muted">${r.closed} closed${r.closed ? ' · ' + Math.round(r.winRate * 100) + '% won' : ''}</small></td></tr>`).join('')}
         </tbody></table></div>
         <p class="muted" style="font-size:11.5px;padding:2px 14px 10px">Each sleeve sizes and tracks its own trades; a full sleeve skips new entries instead of borrowing from another.</p></div>` : ''}

     </div>
     <div class="card"><div class="card-h"><h3>🚪 Auto trade exits</h3><span class="muted" style="font-size:12px">exit breakdown · ${closedAutoAll.length} closed</span></div>
       <div class="jv-exitf">${EXF.map(([v, l]) => `<button type="button" class="${exitFilter === v ? 'on' : ''}" data-jv="exitf" data-k="${v}" title="Show only ${E(l)} exits">${E(l)}</button>`).join('')}</div>
       <div class="tbl-wrap"><table class="jv-t"><thead><tr><th>Exit</th><th class="num">Trades</th><th class="num">Net P&L</th><th class="num">Win %</th></tr></thead><tbody>${exitRows || '<tr><td colspan="4" class="muted">No closed auto trades yet.</td></tr>'}</tbody></table></div>
       ${exFiltered.length ? tradeTable(exFiltered, true, 'algoex') : ''}
     </div>
     ${(() => {
        // Collect all tracked trades across Option Auto Trader, Stock Trader, and active candidates
        const allTracked = [];
        (AUTO.list || []).forEach(t => allTracked.push(t));
        (AUTO.stockTrades || []).forEach(t => allTracked.push(t));
        allTrades().filter(t => !t.auto).forEach(t => allTracked.push(t));

        const totalN = allTracked.length;
        const slN = allTracked.filter(t => getTradeOutcome(t).isSL).length;
        const tgtN = allTracked.filter(t => getTradeOutcome(t).isTarget).length;
        const holdN = allTracked.filter(t => getTradeOutcome(t).isHold).length;
        const tslN = allTracked.filter(t => getTradeOutcome(t).isTSL).length;

        const trf = AUTO.trFilter || '';
        const filtered = trf === 'sl' ? allTracked.filter(t => getTradeOutcome(t).isSL)
          : trf === 'tgt' ? allTracked.filter(t => getTradeOutcome(t).isTarget)
          : trf === 'hold' ? allTracked.filter(t => getTradeOutcome(t).isHold)
          : trf === 'tsl' ? allTracked.filter(t => getTradeOutcome(t).isTSL)
          : allTracked;

        const rows = filtered.map(t => {
          const oc = getTradeOutcome(t);
          const c = calc(t);
          const isOpen = statusOf(t) !== 'Closed' && !(t.exits && t.exits.length);       // open trade: live P&L (after the estimated exit cost) and live price - calc() only knows closed legs, which showed +0.00 and the entry price
          const un = isOpen ? unrealisedNet(t) : null;
          const net = isOpen ? (un == null ? 0 : un) : (c && c.net != null ? c.net : (t.net || 0));
          const ltpShown = isOpen ? curPx(t) : (t.last || (t.exits && t.exits[0] && t.exits[0].price) || t.entry);
          const segTag = t.market || (t.isStock ? 'Stock' : 'F&O');
          const hzTag = t.hz ? (t.hz.charAt(0).toUpperCase() + t.hz.slice(1)) : (t.setup && t.setup.toLowerCase().includes('positional') ? 'Positional' : 'Intraday');
          const isShort = t.dir === 'Short';
          return `<tr>
            <td class="jv-sym"><b>${E(t.symbol || t.instrument)}</b>${eagleTag(t)}<br><small class="muted">${E(t.setup || 'Auto strategy')}</small></td>
            <td><span class="badge ${t.isStock ? 'b-mute' : 'b-up'}" style="font-size:10.5px">${E(segTag)}</span> · <small>${E(hzTag)}</small></td>
            <td><span class="jv-side ${isShort ? 's' : 'l'}">${isShort ? 'SELL' : 'BUY'}</span></td>
            <td class="num"><b>${px(t.entry)}</b></td>
            <td class="num down" title="Stop Loss">${px(t.sl || t.sl0)}</td>
            <td class="num up" title="Target 1">${t.t1 ? px(t.t1) : '—'}</td>
            <td class="num up" title="Target 2">${t.t2 ? px(t.t2) : '—'}</td>
            <td class="num"><b>${px(ltpShown)}</b></td>
            <td class="num ${cc(net)}"><b>${isOpen && un == null ? '—' : sinr(net)}</b></td>
            <td><span class="${oc.cls}">${oc.icon} ${oc.tag}</span></td>
          </tr>`;
        }).join('');

        return `<div class="card" id="jvTrackerCard" style="margin-top:14px">
          <div class="card-h">
            <div>
              <h3 style="display:flex;align-items:center;gap:8px">🎯 Trade Status & Outcome Tracker <span class="badge b-up" style="font-size:10px;font-weight:700">LIVE</span></h3>
              <span class="muted" style="font-size:12px">Continuous tracking of all setups: Stop Hit, Targets (T1 / T2), and Positional Holds across Stocks, Index & F&O</span>
            </div>
          </div>
          <div class="jv-trk-kpis">
            <div class="jv-trk-kpi"><small>Total Tracked</small><b>${totalN}</b></div>
            <div class="jv-trk-kpi"><small>Targets Achieved</small><b class="up">${tgtN}</b></div>
            <div class="jv-trk-kpi"><small>Stop-Loss Hit</small><b class="down">${slN}</b></div>
            <div class="jv-trk-kpi"><small>Positional Holds</small><b style="color:#60a5fa">${holdN}</b></div>
            <div class="jv-trk-kpi"><small>Trailing SL Locked</small><b style="color:#fbbf24">${tslN}</b></div>
          </div>
          <div class="jv-exitf">
            ${[
              ['', 'All (' + totalN + ')'],
              ['sl', '🛑 Stop Hit (' + slN + ')'],
              ['tgt', '🎯 Targets T1/T2 (' + tgtN + ')'],
              ['hold', '⏳ Hold (' + holdN + ')'],
              ['tsl', '🔒 TSL Lock (' + tslN + ')']
            ].map(([v, l]) => `<button type="button" class="${trf === v ? 'on' : ''}" data-jv="trf" data-k="${v}">${l}</button>`).join('')}
          </div>
          <div class="tbl-wrap">
            <table class="jv-t">
              <thead>
                <tr>
                  <th>Instrument</th>
                  <th>Segment / Horizon</th>
                  <th>Signal</th>
                  <th class="num">Entry</th>
                  <th class="num">Stop Loss</th>
                  <th class="num">Target 1</th>
                  <th class="num">Target 2</th>
                  <th class="num">LTP / Exit</th>
                  <th class="num">P&L</th>
                  <th>Status / Outcome</th>
                </tr>
              </thead>
              <tbody>
                ${rows || '<tr><td colspan="10" class="muted" style="text-align:center;padding:16px">No trades match this filter.</td></tr>'}
              </tbody>
            </table>
          </div>
        </div>`;
      })()}`;
   }

  /* ---------- styles ---------- */
  const st = document.createElement('style');
  st.textContent = `
  .jv-banner{display:flex;flex-wrap:wrap;gap:6px 14px;align-items:center;padding:8px 12px;border:1px solid var(--warn,#c9922c);background:color-mix(in srgb,var(--warn,#c9922c) 12%,transparent);border-radius:10px;margin:10px 0;font-size:12.5px}
  .jv-tabs{display:flex;gap:6px;overflow-x:auto;margin:6px 0 12px;padding-bottom:2px;scrollbar-width:none}
  .jv-tabs button{white-space:nowrap;padding:8px 14px;border-radius:999px;border:1px solid var(--line);background:var(--panel);color:var(--text-2,inherit);font-size:13px}
  .jv-tabs button.on{background:var(--brand,#4f8ef7);border-color:var(--brand,#4f8ef7);color:#fff}
  .jv-tabs.jv-subtabs{margin-top:-6px}
  .jv-tabs.jv-subtabs button{padding:6px 12px;font-size:12px;background:none;border-color:transparent;color:var(--text-3,#8a93a6)}
  .jv-tabs.jv-subtabs button.on{background:color-mix(in srgb,var(--brand,#4f8ef7) 16%,transparent);border-color:transparent;color:var(--brand,#4f8ef7)}
  .jv-kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:12px}
  .jv-kpi{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:10px 12px;display:flex;flex-direction:column;gap:3px}
  .jv-kpi small{color:var(--text-3,#8a93a6);font-size:11.5px}.jv-kpi b{font-size:18px;font-variant-numeric:tabular-nums}.jv-kpi span{font-size:11.5px;color:var(--text-3,#8a93a6)}
  .jv-top{grid-template-columns:repeat(auto-fit,minmax(140px,1fr));margin:8px 0 6px}.jv-top .jv-kpi{padding:8px 10px}.jv-top .jv-kpi b{font-size:16px}
  .jv-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px;margin-bottom:12px}
  .jv-cv{width:100%;height:170px;display:block}
  .jv-list>div{display:flex;justify-content:space-between;padding:9px 14px;border-top:1px solid var(--line)}
  .jv-filters{display:flex;flex-wrap:wrap;gap:8px;align-items:end;margin-bottom:12px}.jv-filters label{display:flex;flex-direction:column;font-size:11px;gap:3px;color:var(--text-3,#8a93a6)}
  .jv-filters .inp{min-width:110px}
  .jv-t td,.jv-t th{white-space:nowrap}.jv-t tr[data-jv="open"]{cursor:pointer}.jv-t tr[data-jv="open"]:hover{background:var(--panel-2,rgba(255,255,255,.04))}
  .jv-form{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px 14px;padding:12px 14px}
  form.jv-form{display:block;padding:0}form.jv-form fieldset{border:1px solid var(--line);border-radius:12px;margin:0 0 12px;padding:10px 14px 14px;display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px 14px;background:var(--panel)}
  form.jv-form legend{padding:0 6px;font-weight:600;font-size:13px}.fld.wide{grid-column:1/-1}
  .jv-calc{grid-column:1/-1}.jv-calc-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px}
  .jv-calc-grid>div{background:var(--panel-2,rgba(255,255,255,.04));border-radius:10px;padding:8px 10px}.jv-calc-grid small{display:block;color:var(--text-3,#8a93a6);font-size:11px}
  .jv-msgs{list-style:none;margin:8px 0 0;padding:0;font-size:12.5px;display:grid;gap:4px}.jv-msgs .warn,.warn{color:var(--warn,#c9922c)}
  .jv-actions{display:flex;flex-wrap:wrap;gap:8px;padding:6px 14px 12px}
  .jv-detail h4{margin:14px 0 6px}.jv-rev{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px 12px}
  .jv-s{width:110px;display:inline-block}.jv-chk{margin-right:10px}.jv-stops{margin:0;padding-left:18px;font-size:12.5px}
  /* phones: keep the Exit / delete buttons on screen while the wide table scrolls sideways */
  @media (max-width:700px){.jv-t th.jv-xc,.jv-t td.jv-xc{position:sticky;right:0;z-index:2;background:var(--panel,#10141d);box-shadow:-8px 0 8px -8px rgba(0,0,0,.6);padding-left:8px}.jv-tw .jv-t th:last-child,.jv-tw .jv-t td:last-child{display:none}.jv-t td.jv-xc .btn-xs{padding:1px 6px}}
  @media (max-width:600px){.jv-kpis{grid-template-columns:1fr 1fr}.jv-form{grid-template-columns:1fr}form.jv-form fieldset{grid-template-columns:1fr}}
  /* ---- compact journal ---- */
  .jv svg{width:15px;height:15px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round}
  .jv-head{display:flex;align-items:center;gap:10px;margin:2px 0 6px}.jv-head h1{font-size:20px;margin:0}
  .jv-paper{font-size:10.5px;font-weight:700;letter-spacing:.06em;padding:3px 8px;border-radius:6px;color:var(--warn,#c9922c);background:color-mix(in srgb,var(--warn,#c9922c) 14%,transparent);cursor:help}
  .jv-tabs{gap:0;margin:0 0 10px;border-bottom:1px solid var(--line)}
  .jv-tabs button{border:0;border-radius:0;background:none;padding:8px 12px;font-size:13px;font-weight:600;color:var(--text-3,#8a93a6);border-bottom:2px solid transparent;margin-bottom:-1px}
  .jv-tabs button.on{background:none;color:var(--text);border-bottom-color:var(--brand,#4f8ef7)}
  .jv-kpis{grid-template-columns:repeat(auto-fill,minmax(104px,1fr));gap:6px;margin-bottom:10px}
  .jv-kpi{padding:7px 10px;border-radius:9px;gap:1px;cursor:help;min-width:0}
  .jv-kpi small{font-size:10px;text-transform:uppercase;letter-spacing:.05em}.jv-kpi b{font-size:15px}
  .jv-kpi span{font-size:10.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .jv-top{margin:0 0 8px}.jv-top .jv-kpi{padding:6px 10px}.jv-top .jv-kpi b{font-size:14px}
  .jv-fb{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:8px}
  .jv-seg{display:inline-flex;padding:2px;border-radius:8px;background:var(--panel-2,rgba(255,255,255,.04));border:1px solid var(--line)}
  .jv-seg button{height:26px;padding:0 10px;border:0;border-radius:6px;background:none;color:var(--text-2,inherit);font-size:12px;font-weight:600;cursor:pointer;white-space:nowrap}
  .jv-seg button.on{background:var(--panel);color:var(--text);box-shadow:0 1px 3px rgba(0,0,0,.2)}
  .jv-seg-s button{padding:0 8px;min-width:30px}
  .jv-search{display:flex;align-items:center;gap:6px;height:32px;padding:0 10px;border:1px solid var(--line);border-radius:8px;background:var(--panel);color:var(--text-3,#8a93a6);flex:1 1 160px;max-width:260px}
  .jv-search .inp{border:0;background:none;height:28px;padding:0;min-width:0;width:100%;box-shadow:none}
  .jv-fbtn{height:32px;padding:0 12px;border:1px solid var(--line);border-radius:8px;background:var(--panel);color:var(--text);font-size:12.5px;font-weight:600;cursor:pointer}
  .jv-fbtn.on{border-color:var(--brand,#4f8ef7);color:var(--brand,#4f8ef7)}.jv-fbtn i{font-style:normal;background:var(--brand,#4f8ef7);color:#fff;border-radius:8px;padding:0 6px;font-size:11px;margin-left:4px}
  .jv-more{display:flex;flex-wrap:wrap;gap:8px;align-items:end;padding:10px;margin-bottom:8px;border:1px solid var(--line);border-radius:10px;background:var(--panel)}
  .jv-more label{display:flex;flex-direction:column;font-size:10.5px;gap:3px;color:var(--text-3,#8a93a6);text-transform:uppercase;letter-spacing:.04em}.jv-more .inp{min-width:110px;height:32px}
  .jv-chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px}
  .jv-chip{height:24px;padding:0 9px;border-radius:12px;border:0;background:var(--brand-2,rgba(79,142,247,.15));color:var(--brand,#4f8ef7);font-size:11.5px;font-weight:600;cursor:pointer}
  .jv .card{margin-bottom:10px}.jv .card-h{padding:8px 12px}.jv .card-h h3{font-size:13.5px}
  .jv .card-h h3{white-space:nowrap}.jv .card-h{flex-wrap:wrap}.jv .card-h .muted{min-width:0}
  .jv-t{font-size:12.5px}.jv-t th{font-size:10.5px;text-transform:uppercase;letter-spacing:.04em;cursor:help;padding:6px 8px;position:sticky;top:0;background:var(--panel)}
  .jv-t td{padding:5px 8px;vertical-align:middle}.jv-t td.num,.jv-t th.num{text-align:right}
  .jv-eagle{display:inline-block;margin:2px 0 1px;padding:1px 7px;border-radius:6px;font-size:10px;font-weight:800;letter-spacing:.05em;color:#f5a524;background:rgba(245,165,36,.14);border:1px solid rgba(245,165,36,.5);white-space:nowrap}
  :root[data-theme="light"] .jv-eagle{color:#b45309;background:rgba(217,119,6,.1);border-color:rgba(217,119,6,.45)}
  .jv-sym b{display:block;font-size:12.5px;max-width:230px;overflow:hidden;text-overflow:ellipsis}.jv-sym small{display:block;font-size:10.5px;color:var(--text-3,#8a93a6);max-width:230px;overflow:hidden;text-overflow:ellipsis}
  .jv-tag{display:inline-grid;place-items:center;width:16px;height:16px;border-radius:4px;font-size:9.5px;font-weight:800;margin-right:5px;background:color-mix(in srgb,var(--brand,#4f8ef7) 20%,transparent);color:var(--brand,#4f8ef7)}
  .jv-tag.m{background:var(--panel-2,rgba(255,255,255,.06));color:var(--text-3,#8a93a6)}
  .jv-side{display:inline-grid;place-items:center;width:18px;height:18px;border-radius:4px;font-size:10px;font-weight:800}.jv-side.l{background:color-mix(in srgb,var(--up,#22ab94) 18%,transparent);color:var(--up,#22ab94)}.jv-side.s{background:color-mix(in srgb,var(--down,#f7525f) 18%,transparent);color:var(--down,#f7525f)}
  .jv-tg{color:var(--text-2,inherit);font-size:11.5px}
  .jv-pg{display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;padding:8px 12px;border-top:1px solid var(--line);font-size:12px}
  .jv-pgb{display:flex;align-items:center;gap:6px}.jv-pgb button{width:28px;height:28px;border:1px solid var(--line);border-radius:7px;background:var(--panel);color:var(--text);cursor:pointer;font-size:14px}.jv-pgb button:disabled{opacity:.35;cursor:not-allowed}.jv-pgb b{font-variant-numeric:tabular-nums}
  .jv-grid{grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px}.jv-cv{height:120px}
  .jv-exit{height:24px;padding:0 10px;border-radius:6px;border:1px solid color-mix(in srgb,var(--down,#f7525f) 55%,transparent);background:color-mix(in srgb,var(--down,#f7525f) 12%,transparent);color:var(--down,#f7525f);font-size:11.5px;font-weight:700;cursor:pointer}
  .jv-capg{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;padding:4px 14px 12px}.jv-capg>div{display:flex;flex-direction:column;gap:2px;min-width:0}.jv-capg small{font-size:11px;color:var(--text-3);text-transform:uppercase;letter-spacing:.04em}.jv-capg b{font-size:18px}.jv-capg span{font-size:11.5px}
  .jv-capbar{height:6px;border-radius:3px;background:var(--panel-2,rgba(255,255,255,.06));overflow:hidden;margin-top:4px}.jv-capbar i{display:block;height:100%;border-radius:3px;background:var(--up,#22ab94)}.jv-capbar i.warn{background:#f59e0b}.jv-capbar i.down{background:var(--down,#f7525f)}.jv-capbar i.mute{background:#8b5cf6}
  @media(max-width:640px){.jv-capg{grid-template-columns:1fr}}
  .jv-sec{font-size:12px;font-weight:700;color:var(--text-3);text-transform:uppercase;letter-spacing:.05em;margin:14px 2px 6px}
  .jv-books{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;padding:2px 12px 12px}.jv-book{border:1px solid var(--line);border-radius:10px;padding:8px 10px;min-width:0}
  .jv-book.jv-btot{background:var(--panel-2,rgba(255,255,255,.04))}.jv-bt{display:block;font-size:12.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .jv-beq{display:flex;align-items:baseline;gap:6px;flex-wrap:wrap;margin:3px 0 5px}.jv-beq span{font-size:15px;font-weight:800}.jv-beq em{font-style:normal;font-weight:700;font-size:11.5px}
  .jv-bl{display:grid;grid-template-columns:1fr 1fr;gap:4px 8px}.jv-bl small{display:block;font-size:10px;color:var(--text-3);text-transform:uppercase;letter-spacing:.03em}.jv-bl b{font-size:12px;white-space:nowrap}
  @media(max-width:1100px){.jv-books{grid-template-columns:repeat(2,minmax(0,1fr))}}
  .jv-tot td{border-top:2px solid var(--line)}.jv-sbh{margin:12px 14px 4px;font-size:13px}.jv-sbr{margin:8px 14px 12px;font-size:12px}.jv-sbr pre{white-space:pre-wrap;font-size:11.5px;color:var(--text-2)}
  .jv-pos-bar{display:flex;align-items:center;flex-wrap:wrap;gap:8px 14px;margin:0 0 10px}.jv-sidesw button small{opacity:.7;margin-left:2px}.jv-sidesw button.buy.on{background:color-mix(in srgb,var(--up,#22ab94) 22%,transparent);color:var(--up,#22ab94)}.jv-sidesw button.sell.on{background:color-mix(in srgb,var(--down,#f7525f) 22%,transparent);color:var(--down,#f7525f)}
  .jv-btcsel,.jv-exitf{display:flex;align-items:center;flex-wrap:wrap;gap:6px;padding:8px 14px}
  .jv-btcsel button,.jv-exitf button{height:26px;padding:0 10px;border:1px solid var(--line,#223052);border-radius:8px;background:none;color:var(--text-2,#93a4bf);font:inherit;font-size:11.5px;cursor:pointer}
  .jv-btcsel button.on,.jv-exitf button.on{background:var(--brand,#2f81f7);border-color:var(--brand,#2f81f7);color:#fff}
  .jv-exitf button.on{border-color:var(--up,#22ab94);background:color-mix(in srgb,var(--up,#22ab94) 20%,transparent);color:var(--up,#22ab94)}
  
  .jv-tag-sl{background:rgba(239,68,68,.18);color:#f87171;border:1px solid rgba(239,68,68,.35);padding:3px 8px;border-radius:6px;font-weight:700;font-size:11.5px;display:inline-flex;align-items:center;gap:4px;white-space:nowrap}
  .jv-tag-t1{background:rgba(34,197,94,.18);color:#4ade80;border:1px solid rgba(34,197,94,.35);padding:3px 8px;border-radius:6px;font-weight:700;font-size:11.5px;display:inline-flex;align-items:center;gap:4px;white-space:nowrap}
  .jv-tag-t2{background:rgba(16,185,129,.22);color:#34d399;border:1px solid rgba(16,185,129,.4);padding:3px 8px;border-radius:6px;font-weight:700;font-size:11.5px;display:inline-flex;align-items:center;gap:4px;white-space:nowrap}
  .jv-tag-hold{background:rgba(59,130,246,.18);color:#60a5fa;border:1px solid rgba(59,130,246,.35);padding:3px 8px;border-radius:6px;font-weight:700;font-size:11.5px;display:inline-flex;align-items:center;gap:4px;white-space:nowrap}
  .jv-tag-tsl{background:rgba(245,158,11,.18);color:#fbbf24;border:1px solid rgba(245,158,11,.35);padding:3px 8px;border-radius:6px;font-weight:700;font-size:11.5px;display:inline-flex;align-items:center;gap:4px;white-space:nowrap}
  .jv-trk-kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;padding:10px 14px;border-bottom:1px solid var(--line)}
  .jv-trk-kpi{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:8px 10px;display:flex;flex-direction:column;gap:2px}
  .jv-trk-kpi small{font-size:11px;color:var(--text-3);text-transform:uppercase}
  .jv-trk-kpi b{font-size:16px;font-weight:700}

  .jv-exit:hover{background:var(--down,#f7525f);color:#fff}.jv-exitall{height:26px}
  .jv-more{margin:4px 0 10px;border:1px solid var(--line);border-radius:12px;padding:8px 12px}.jv-more summary{cursor:pointer;color:var(--text-3);font-size:13px;font-weight:600}.jv-more[open] summary{margin-bottom:8px}
  .jv-hr{display:flex;align-items:center;gap:10px;margin-left:auto}
  .jv-list>div{padding:7px 12px;font-size:12.5px}
  details.jv-more{display:block !important;width:100% !important}
  details.jv-more>summary{display:flex !important;width:100% !important;align-items:center;gap:6px}
  details.jv-more>*{max-width:100% !important}
  @media (max-width:600px){.jv-kpis{grid-template-columns:repeat(3,1fr)}.jv-kpi b{font-size:13.5px}.jv-search{max-width:none;order:5;flex-basis:100%}.jv-tabs{overflow-x:auto}div.jv-more{display:grid;grid-template-columns:1fr 1fr}.jv-more .inp{min-width:0;width:100%}.jv-t .jv-tg,.jv-t th[title^="T1"]{display:none}}`
  ;
  st.textContent += `
  /* Portfolio redesign: big Today card, plain-language blocks */
  .jv-hero{padding:16px;margin-bottom:4px;border-radius:16px}
  .jv-hero.jv-pos{border-color:color-mix(in srgb,var(--up) 45%,var(--line))}.jv-hero.jv-neg{border-color:color-mix(in srgb,var(--down) 45%,var(--line))}
  .jv-hero-top{display:flex;justify-content:space-between;align-items:center;font-size:13px;font-weight:600;color:var(--text-2)}
  .jv-mkt{font-style:normal;font-size:11.5px;padding:3px 9px;border-radius:12px;background:var(--panel-2);color:var(--text-3)}.jv-mkt.on{background:var(--up-bg);color:var(--up)}
  .jv-hero-big{font-size:38px;line-height:1.1;font-weight:700;letter-spacing:-.02em;margin:8px 0 12px;font-variant-numeric:tabular-nums}
  .jv-chips{display:grid;grid-template-columns:1fr 1fr;gap:8px}
  .jv-chip2{border:1px solid var(--line);border-radius:12px;padding:10px 12px;background:var(--panel-2);min-width:0}
  .jv-chip2 small{display:block;color:var(--text-3);font-size:12px;font-weight:600}.jv-chip2 b{display:block;font-size:19px;margin:2px 0;font-variant-numeric:tabular-nums}.jv-chip2 span{font-size:11.5px;color:var(--text-3)}
  .jv-hr-row{display:flex;flex-direction:column;gap:6px;padding:10px 0;border-top:1px solid var(--line)}.jv-hr-row:first-of-type{margin-top:14px}
  .jv-hr-name{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}.jv-hr-name small{color:var(--text-3);font-size:11.5px}
  .jv-hr-n{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;font-variant-numeric:tabular-nums}
  .jv-hr-n small{display:block;font-size:10.5px;color:var(--text-3);text-transform:uppercase;letter-spacing:.03em}.jv-hr-n span{font-size:14px;font-weight:600;white-space:nowrap}
  .jv-hint{margin:10px 0 0;font-size:12px;line-height:1.5;color:var(--text-3)}
  .jv-ins{padding:14px 16px;margin-bottom:10px;border-left:4px solid var(--line)}.jv-ins.jv-i-pos{border-left-color:var(--up)}.jv-ins.jv-i-neg{border-left-color:var(--down)}.jv-ins.jv-i-ok{border-left-color:var(--brand)}
  .jv-ins>b{font-size:14px}.jv-ins p{margin:8px 0 0;font-size:13px;line-height:1.5;color:var(--text-2)}
  .jv-ins-g{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:10px}.jv-ins-g small{display:block;font-size:11px;color:var(--text-3)}.jv-ins-g b{font-size:15px;font-variant-numeric:tabular-nums}
  @media (max-width:600px){.jv-hero-big{font-size:34px}.jv-ins-g{grid-template-columns:1fr 1fr}}
`;
  document.head.appendChild(st);

  setInterval(() => { if (document.getElementById('v-journal') && document.getElementById('v-journal').offsetParent) applyManualTsl(); }, 15000);
function lastDayStats(currentDay) {
    const all = allTrades();
    const dayTotals = {};
    all.forEach(t => {
      if (!entered(t)) return;
      (t.exits || []).forEach(l => {
        const dt = l.date;
        if (dt && dt < currentDay) {
          const net = dirOf(t) * (l.price - t.entry) * l.qty * units(t) - (t.costOverride != null ? 0 : (S.cost + S.slip) * units(t) * l.qty);
          dayTotals[dt] = (dayTotals[dt] || 0) + net;
        }
      });
      if (t.auto && statusOf(t) === 'Closed') {
        const dt = t.date || (t.openedAt ? t.openedAt.slice(0, 10) : '') || lastExit(t).slice(0, 10);
        if (dt && dt < currentDay) {
          dayTotals[dt] = (dayTotals[dt] || 0) + (calc(t).net || 0);
        }
      } else if (t.paper && statusOf(t) === 'Closed') {
        const dt = t.date || lastExit(t).slice(0, 10);
        if (dt && dt < currentDay) {
          dayTotals[dt] = (dayTotals[dt] || 0) + (calc(t).net || 0);
        }
      }
    });
    const days = Object.keys(dayTotals).filter(x => x < currentDay).sort();
    if (!days.length) {
      try {
        const saved = JSON.parse(localStorage.getItem('rs-last-pnl') || 'null');
        if (saved && typeof saved.pl === 'number') return { day: saved.day || null, pnl: saved.pl };
      } catch (e) { }
      return { day: null, pnl: 0 };
    }
    const lastD = days[days.length - 1];
    return { day: lastD, pnl: dayTotals[lastD] || 0 };
  }

  window.JV = { cap: () => capUse(), render, sync: syncAuto, refreshLive, trades: () => T, settings: () => S, calc, validate,
    /* live portfolio for the header: capital + booked + open (marked to market) */
          totals: () => { const d = today(), L = liveTotals(d), ds = dayStats(d), todayBooked = ds.pnl + L.autoToday, last = lastDayStats(d);
      return { capital: S.capital, booked: L.booked, unr: L.unr, eq: L.eq, today: todayTotal().total, todayBooked, lastDay: last.day, lastDayPnl: last.pnl, open: allTrades().filter(t => entered(t) && statusOf(t) !== 'Closed').length }; } };
  setTimeout(() => { syncAuto(false).then(() => { if (typeof renderPfChip === 'function') renderPfChip(); if (typeof App !== 'undefined' && App.view === 'journal') render(); }); }, 80);
})();
