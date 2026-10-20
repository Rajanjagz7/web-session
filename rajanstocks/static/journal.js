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
  const TABS = [['open', 'Positions'], ['pending', 'Pending'], ['journal', 'History'], ['overview', 'Summary'], ['more', 'More']];
  const GROUPS = { more: [['orders', 'Orders'], ['strategy', 'Strategy'], ['tsl', 'TSL'], ['backtest', 'Backtest'], ['auto', 'Auto'], ['settings', 'Settings'], ['reports', 'Reports'], ['new', 'Full form']] };
  const TAB_TIPS = { open: 'Open trades with SL, target and a one-tap Exit', pending: 'Saved plans waiting to be entered', journal: 'All closed trades', overview: 'Win rate, net P&L and rules followed',
    more: 'Advanced tools: orders, strategy lab, backtest, auto trader, settings', orders: 'Open, filled and cancelled orders', strategy: 'Strategy Lab: results by setup', tsl: 'TSL Lab: compare trailing-stop methods',
    auto: 'Auto Trader: automated trades and settings', backtest: 'Run and review backtests', reports: 'Exports and summary reports', settings: 'Capital, risk and rule settings', new: 'The full planning form with risk checks' };
  const effTab = () => GROUPS[ui.tab] ? ui.sub[ui.tab] : ui.tab;

  const load = (k, d) => { try { const v = JSON.parse(localStorage.getItem(k)); return v == null ? d : v; } catch (e) { return d; } };
  const save = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { } };
  let S = Object.assign({}, DEFAULTS, load(SKEY, {}));
  let T = load(KEY, []);
  /* Automated trades (server side) are mirrored into the journal with every field filled in: plan, indicator evidence,
     exit, costs, R multiple and review. They are read-only and do not count toward the manual 5-a-day / loss limits. */
  const AUTO = { list: [], ts: 0, busy: false };
  const EXIT_MAP = { STOP: 'SL', TSL: 'TSL', MANUAL: 'Manual Exit', TARGET: 'T2', TIME: 'Time Exit', EXPIRY: 'Time Exit', REVERSE: 'Manual Exit', 'SQUARE-OFF': 'Time Exit' };
  function mapAuto(a) {
    const d = a.openedAt ? new Date(a.openedAt) : new Date(a.date + 'T09:20:00+05:30');
    const delta = 0.5, riskP = Math.max(0.05, Math.min(delta * (a.riskU || 0), 0.9 * a.entry));   // premium at risk per unit: delta 0.5 x underlying stop, never more than the premium itself
    const inds = (a.indicators && a.indicators.length ? a.indicators : [a.strategy]).filter(Boolean);
    const closed = a.status === 'CLOSED';
    const t = {
      id: a.id, auto: true, date: a.date, time: istTime(d), at: d.toISOString(), market: 'Options', instrument: a.sym,
      symbol: `${a.sym} ${Number(a.strike).toFixed(0)} ${a.opt} ${a.expiry}`, dir: 'Long',
      setup: a.source || a.strategy, tf: '1D', ind: inds.join(', '), entry: a.entry,
      sl: +(a.entry - riskP).toFixed(2), sl0: +(a.entry - riskP).toFixed(2),
      t1: +(a.entry + riskP).toFixed(2), t2: +(a.entry + 2 * riskP).toFixed(2), t3: +(a.entry + 3 * riskP).toFixed(2),
      qty: a.lots, mult: a.lot, initRisk: a.initialRisk, raw: a,
      tsl: a.tsl ? ({ trail: 'Distance Trail', breakeven: 'Breakeven', step: 'Step Trail' }[a.tsl.mode] || 'Off / Fixed SL') : (a.variant === 'trail' ? 'Distance Trail' : 'Off / Fixed SL'),
      why: `Auto-executed ${a.side === 'BUY' ? 'call' : 'put'} on ${a.sym}: ${inds.length} indicator(s) — ${inds.join(', ')}. ` +
           `Underlying entry ${a.entryU}, stop ${a.stopU}${a.targetU ? ', target ' + a.targetU : ', trailing exit'}.`,
      status: closed ? 'Closed' : 'Open', exits: [], hits: [], hitOrder: [], stops: [{ at: a.openedAt || d.toISOString(), from: null, to: a.stopU, note: 'underlying stop at entry' }],
      rule: (a.initialRisk || 0) > S.capital * S.riskPct / 100 + 1e-9 ? 'Partial' : 'Yes', emotion: 'Automated',
      mistakes: (a.initialRisk || 0) > S.capital * S.riskPct / 100 + 1e-9 ? 'Risk above budget (1-lot minimum)' : '', reviewer: '', ref: '', created: a.openedAt,
      plan: { entry: a.entry, sl: a.stopU, qty: a.lots }, unrl: a.unrealised,
    };
    if (closed) {
      const ex = a.closedAt ? new Date(a.closedAt) : d, type = EXIT_MAP[a.exitReason] || 'Manual Exit';
      t.exits = [{ qty: a.lots, price: a.exit, type, date: istDay(ex), time: istTime(ex) }];
      t.exitType = type; t.costOverride = a.cost || 0; t.slipOverride = 0;
      if (type === 'T2') { t.hits = ['T1', 'T2']; t.hitOrder = ['T1', 'T2']; }
      t.reviewed = true;
      t.lesson = `Automated. Exit: ${a.exitReason}. Net ${a.net >= 0 ? '+' : ''}₹${Math.round(a.net)}${a.R != null ? ' (' + (a.R >= 0 ? '+' : '') + a.R + 'R)' : ''}. ` +
                 (t.rule === 'Yes' ? 'Within the per-trade risk budget; stop set; max 5 a day.' : `Stop set and max 5 a day respected, but one lot risks about ₹${Math.round(a.initialRisk)} - above the ₹${Math.round(S.capital * S.riskPct / 100)} budget (1-lot minimum).`);
    } else { t.reviewed = false; t.lesson = ''; }
    return t;
  }
  async function syncAuto(force) {
    if (AUTO.busy || (!force && Date.now() - AUTO.ts < 30000)) return;
    AUTO.busy = true;
    try {
      const r = await fetch('/api/auto/status', { cache: 'no-store' });
      if (r.ok) {
        const a = await r.json();
        const before = JSON.stringify(AUTO.list.map(x => [x.id, x.status, x.unrl, x.exitType]));
        AUTO.list = (a.open || []).concat(a.closed || []).map(mapAuto);
        AUTO.ts = Date.now();
        if (JSON.stringify(AUTO.list.map(x => [x.id, x.status, x.unrl, x.exitType])) !== before && document.getElementById('v-journal') && !document.querySelector('.modal-bg') &&
            ['overview', 'journal', 'strategy', 'reports'].includes(effTab())) render();
      }
    } catch (e) { /* offline: keep what we have */ }
    AUTO.busy = false;
  }
  const allTrades = () => T.concat(AUTO.list);
  async function jpost(url, body) {
    try {
      const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) });
      const d = await r.json().catch(() => ({}));
      return r.ok ? { ok: true, d } : { ok: false, err: d.detail || ('Request failed (' + r.status + ')') };
    } catch (e) { return { ok: false, err: 'No internet connection.' }; }
  }
  const ui = { tab: 'open', sub: { more: 'orders' }, quick: null, sheet: null, f: { from: '', to: '', market: '', inst: '', setup: '', dir: '', exit: '', rule: '', src: '' }, sel: null, lab: null, labBusy: false };

  /* ---------- helpers ---------- */
  const E = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const num = v => { const n = parseFloat(v); return isFinite(n) ? n : null; };
  const inr = (n, d = 2) => (n < 0 ? '−' : '') + '₹' + Math.abs(n).toLocaleString('en-IN', { minimumFractionDigits: d, maximumFractionDigits: d });
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
  const live = sym => { try { const s = (typeof SYM === 'function') ? SYM(String(sym || '').toUpperCase()) : null; return s && s.last > 0 ? s.last : null; } catch (e) { return null; } };
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
  function unrealised(t) {
    if (statusOf(t) === 'Closed' || t.status === 'Planned' || t.status === 'Cancelled') return null;
    if (t.auto) return typeof t.unrl === 'number' ? t.unrl : null;          // option P&L comes from the server's live option price
    const l = live(t.symbol || t.instrument); if (l == null) return null;
    const rem = t.qty - exitedQty(t);
    return dirOf(t) * (l - t.entry) * rem * units(t);
  }
  const entered = t => t.status !== 'Planned' && t.status !== 'Cancelled';
  const realised = () => T.reduce((a, t) => a + (entered(t) ? calc(t).net : 0), 0);
  const equity = () => S.capital + realised();
  const budget = () => equity() * S.riskPct / 100;
  function dayStats(day) {
    let entries = 0, pnl = 0, unr = 0, open = 0;
    T.forEach(t => {
      if (!entered(t)) return;
      if (t.date === day) entries++;
      const u = unrealised(t); if (u != null) { unr += u; }
      if (statusOf(t) !== 'Closed') open++;
      (t.exits || []).forEach(l => { if (l.date === day) pnl += dirOf(t) * (l.price - t.entry) * l.qty * units(t) - (t.costOverride != null ? 0 : (S.cost + S.slip) * units(t) * l.qty); });
    });
    return { entries, pnl, unr, open };
  }
  function startOfDayEquity(day) {
    let p = 0;
    T.forEach(t => { if (!entered(t)) return; (t.exits || []).forEach(l => { if (l.date < day) p += dirOf(t) * (l.price - t.entry) * l.qty * units(t) - (S.cost + S.slip) * units(t) * l.qty; }); });
    return S.capital + p;
  }

  /* ---------- trade validation (FR-03/04/05, section 10) ---------- */
  function validate(f, opts) {
    const errs = [], warns = [], d = f.dir === 'Short' ? -1 : 1, m = f.mult || 1;
    ['date', 'market', 'instrument', 'dir', 'setup'].forEach(k => { if (!f[k]) errs.push('Missing: ' + k); });
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
      if (ds.entries >= S.maxTrades) blocks.push(`Daily trade limit reached (${ds.entries}/${S.maxTrades}).`);
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
    return allTrades().filter(t => (!f.src || (f.src === 'auto' ? t.auto : !t.auto)) && (!f.from || t.date >= f.from) && (!f.to || t.date <= f.to) && (!f.market || t.market === f.market) &&
      (!f.inst || (t.instrument || '').toUpperCase().includes(f.inst.toUpperCase())) && (!f.setup || t.setup === f.setup) &&
      (!f.dir || t.dir === f.dir) && (!f.exit || t.exitType === f.exit) && (!f.rule || t.rule === f.rule));
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
    const autoReal = AUTO.list.reduce((a, t) => a + (entered(t) ? calc(t).net : 0), 0);
    const booked = realised() + autoReal;
    const unr = allTrades().reduce((a, t) => a + (unrealised(t) || 0), 0);
    const autoToday = AUTO.list.reduce((a, t) => a + (entered(t) && statusOf(t) === 'Closed' && lastExit(t).slice(0, 10) === day ? calc(t).net : 0), 0);
    return { booked, unr, autoToday, eq: S.capital + booked + unr };
  }
  function refreshLive() {
    const host = document.getElementById('v-journal');
    if (!host || !host.offsetParent || document.hidden) return;
    const h = document.getElementById('jqHero'); if (h) h.outerHTML = hero();
    if (ui.tab === 'open') { const o = document.getElementById('jqOpen'); if (o) o.innerHTML = openCards(); }
  }
  setInterval(() => { refreshLive(); if (!document.hidden) syncAuto(false); }, 5000);  // syncAuto self-throttles to 30 s
  setInterval(() => { const h = document.getElementById('v-journal'); if (h && h.offsetParent && !document.hidden) syncAuto(true).then(refreshLive); }, 15000);


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

  const PG_SIZES = [5, 10, 100, 1000];
  function pagerBar(list, key) {
    ui.pg = ui.pg || {};
    const pg = ui.pg[key] || (ui.pg[key] = { p: 0, s: 10 });
    const pages = Math.max(1, Math.ceil(list.length / pg.s)); pg.p = Math.min(pg.p, pages - 1);
    const part = list.slice(pg.p * pg.s, (pg.p + 1) * pg.s);
    const bar = list.length > PG_SIZES[0] ? `<div class="jv-pg"><div class="jv-seg jv-seg-s" title="Rows per page">${PG_SIZES.map(n => `<button class="${pg.s === n ? 'on' : ''}" data-jvps="${key}:${n}">${n}</button>`).join('')}</div>
      <span class="muted">${pg.p * pg.s + 1}–${pg.p * pg.s + part.length} of ${list.length}</span>
      <span class="jv-pgb"><button data-jvpg="${key}:${pg.p - 1}" ${pg.p <= 0 ? 'disabled' : ''} aria-label="Previous page">‹</button><b>${pg.p + 1}/${pages}</b><button data-jvpg="${key}:${pg.p + 1}" ${pg.p >= pages - 1 ? 'disabled' : ''} aria-label="Next page">›</button></span></div>` : '';
    return { part, bar };
  }
  function tradeTable(list, withUnr, key) {
    key = key || 'tbl'; ui.tbl = ui.tbl || {}; ui.pg = ui.pg || {}; ui.tbl[key] = { list, withUnr };
    if (!list.length) return `<div class="jv-tw" data-jvt="${key}"><div class="empty">No trades match.</div></div>`;
    const { part, bar: pager } = pagerBar(list, key);
    const th = (l, tip, cls) => `<th class="${cls || ''}" title="${tip}">${l}</th>`;
    const rows = part.map(t => {
      const c = calc(t), st = statusOf(t), u = withUnr ? unrealised(t) : null, closedish = st === 'Closed' || c.qx;
      const v = closedish ? c.net : (u || 0), pnl = closedish ? sinr(c.net) : (u != null ? sinr(u) : '—');
      const stCls = st === 'Open' || st === 'Partial' ? 'b-up' : 'b-mute';
      const tips = [`Setup: ${t.setup || '—'}`, t.tf ? `TF ${t.tf}` : '', t.ind ? `Indicators: ${t.ind}` : ''].filter(Boolean).join(' · ');
      return `<tr data-jv="open" data-id="${t.id}" tabindex="0" title="Click for full details">
        <td class="jv-id">${t.auto ? '<span class="jv-tag" title="Placed by the auto trader">A</span>' : '<span class="jv-tag m" title="Logged manually">M</span>'}<span title="${t.id}">${String(t.id).replace(/^A-\d{4}/, 'A-')}</span>${t.edited ? ' <i title="Edited after close">✎</i>' : ''}</td>
        <td title="${t.date} ${t.time || ''}">${String(t.date).slice(5)}</td>
        <td class="jv-sym"><b>${E(t.symbol || t.instrument)}</b><small title="${E(tips)}">${E(t.setup || '')}</small></td>
        <td><span class="jv-side ${t.dir === 'Short' ? 's' : 'l'}" title="${t.dir}">${t.dir === 'Short' ? 'S' : 'L'}</span></td>
        <td class="num">${px(t.entry)}</td>
        <td class="num" title="${t.sl !== t.sl0 ? 'Initial SL ' + px(t.sl0) + ' · ' : ''}Trailing: ${E(t.tsl || 'off')}">${px(t.sl)}${t.sl !== t.sl0 ? ' <small class="up">↑</small>' : ''}</td>
        <td class="num jv-tg" title="Targets T1 / T2 / T3">${[t.t1, t.t2, t.t3].map(x => x ? px(x) : '–').join(' · ')}</td>
        <td class="num">${t.qty}</td>
        <td class="num ${cc(v)}" title="${closedish ? 'Booked P&L after costs' : 'Open P&L at live price'}"><b>${pnl}</b></td>
        <td class="num ${cc(c.R)}">${rr(c.R)}</td>
        <td><span class="badge ${stCls}">${st}</span></td>
        <td>${st !== 'Closed' && t.status !== 'Planned' && t.status !== 'Cancelled' ? `<button class="jv-exit" data-jv="${t.auto ? 'autoexit' : 'mktexit'}" data-id="${t.id}" title="Exit this position now at the live price">Exit</button>` : `<span title="${E(t.exitType || '')}">${E(t.exitType || '—')}</span>`}</td>
        <td title="${t.reviewed ? 'Reviewed' : st === 'Closed' ? 'Review pending' : 'Still open'}">${t.reviewed ? '✓' : (st === 'Closed' ? '<span class="warn">•</span>' : '')}</td></tr>`;
    }).join('');
    return `<div class="jv-tw" data-jvt="${key}"><div class="tbl-wrap"><table class="jv-t"><thead><tr>${th('ID', 'Trade ID · A = automated, M = manual')}${th('Date', 'Entry date (MM-DD)')}${th('Symbol', 'Contract, with setup underneath')}${th('Side', 'L = long, S = short')}${th('Entry', 'Entry price', 'num')}${th('SL', 'Current stop-loss (↑ = trailed)', 'num')}${th('Targets', 'T1 · T2 · T3', 'num')}${th('Qty', 'Lots / quantity', 'num')}${th('P&L', 'Booked P&L, or open P&L at live price', 'num')}${th('R', 'Result in multiples of initial risk', 'num')}${th('Status', 'Open, Partial or Closed')}${th('Exit', 'Exit an open position now, or how a closed trade ended')}${th('✓', 'Reviewed')}</tr></thead><tbody>${rows}</tbody></table></div>${pager}</div>`;
  }

  function viewNew() {
    const d = ui.draft || (ui.draft = { date: today(), time: istTime(new Date()), market: 'Equity Intraday', dir: 'Long', mult: 1, tsl: TSL_MODES[0], tslTrig: S.labTrigger, trail: '', step: '' });
    const setups = [...new Set(T.map(t => t.setup).filter(Boolean))];
    const sel = (id, arr, cur) => `<select class="inp" id="${id}">${arr.map(x => `<option ${cur === x ? 'selected' : ''}>${E(x)}</option>`).join('')}</select>`;
    const inp = (id, label, v, type = 'text', extra = '') => `<label class="fld"><span>${label}</span><input class="inp" id="${id}" type="${type}" value="${E(v == null ? '' : v)}" ${extra}></label>`;
    const syms = (typeof SYMS !== 'undefined') ? SYMS.slice(0, 500).map(s => `<option value="${E(s.s)}">`).join('') : '';
    return `<form class="jv-form" id="jvForm" autocomplete="off">
      <fieldset><legend>Setup</legend>
        ${inp('jf-date', 'Date', d.date, 'date')}${inp('jf-time', 'Entry time (IST)', d.time, 'time')}
        <label class="fld"><span>Market type</span>${sel('jf-market', MARKETS, d.market)}</label>
        <label class="fld"><span>Instrument</span><input class="inp" id="jf-inst" list="jvSyms" value="${E(d.instrument || '')}" placeholder="e.g. RELIANCE / NIFTY"><datalist id="jvSyms">${syms}</datalist></label>
        ${d.market === 'Options' ? `${inp('jf-strike', 'Strike', d.strike, 'number', 'step="any" placeholder="22600"')}
        <label class="fld"><span>Option type</span>${sel('jf-opt', ['CE', 'PE'], d.opt || 'CE')}</label>
        ${inp('jf-expiry', 'Expiry', d.expiry, 'date')}` : ''}
        ${inp('jf-sym', 'Symbol / contract', d.symbol || '', 'text', 'placeholder="e.g. NIFTY 22600 PE"')}
        <label class="fld"><span>Direction</span>${sel('jf-dir', ['Long', 'Short'], d.dir)}</label>
        <label class="fld"><span>Strategy / setup</span><input class="inp" id="jf-setup" list="jvSetups" value="${E(d.setup || '')}" placeholder="${d.market === 'Options' ? 'e.g. breakout CE buy, IV crush PE sell' : ''}"><datalist id="jvSetups">${setups.map(s => `<option value="${E(s)}">`).join('')}</datalist></label>
        ${inp('jf-tf', 'Timeframe', d.tf || '', 'text', 'placeholder="5m / 15m / 1D"')}
        ${inp('jf-ind', 'Indicator values', d.ind || '', 'text', 'placeholder="UT Bot BUY, RSI 58…"')}
      </fieldset>
      <fieldset><legend>Entry &amp; risk</legend>
        ${inp('jf-entry', 'Entry price', d.entry, 'number', 'step="any"')}${inp('jf-sl', 'Initial stop-loss (mandatory)', d.sl, 'number', 'step="any"')}
        ${inp('jf-qty', 'Quantity (shares / lots)', d.qty, 'number', 'step="1" min="1"')}${inp('jf-mult', 'Lot / contract multiplier', d.mult, 'number', 'step="any" min="1"')}
        <div class="jv-calc" id="jvCalc"></div>
      </fieldset>
      <fieldset><legend>Targets <small>(blank = ${S.t1}R / ${S.t2}R / ${S.t3}R)</small></legend>
        ${inp('jf-t1', 'T1', d.t1, 'number', 'step="any"')}${inp('jf-t2', 'T2', d.t2, 'number', 'step="any"')}${inp('jf-t3', 'T3', d.t3, 'number', 'step="any"')}
      </fieldset>
      <fieldset><legend>TSL rules</legend>
        <label class="fld"><span>TSL mode</span>${sel('jf-tsl', TSL_MODES, d.tsl)}</label>
        ${inp('jf-trig', 'Activation / breakeven trigger (R)', d.tslTrig, 'number', 'step="any"')}
        ${inp('jf-trail', 'Trail distance (price)', d.trail, 'number', 'step="any"')}${inp('jf-step', 'Step size (price)', d.step, 'number', 'step="any"')}
      </fieldset>
      <fieldset><legend>Rationale</legend>
        <label class="fld wide"><span>Why this trade (before entry)</span><textarea class="inp" id="jf-why" rows="3">${E(d.why || '')}</textarea></label>
        <label class="fld wide" id="jvOvr" hidden><span>Override reason (logged)</span><input class="inp" id="jf-ovr" value="${E(d.ovr || '')}"></label>
      </fieldset>
      <div class="jv-actions"><button type="button" class="btn" data-jv="plan">Save as plan</button><button type="button" class="btn pri" data-jv="enter">Record entry…</button><button type="button" class="btn" data-jv="resetform">Reset</button></div>
    </form>`;
  }

  function readForm() {
    const g = id => { const e = document.getElementById(id); return e ? e.value : ''; };
    const f = {
      date: g('jf-date'), time: g('jf-time'), market: g('jf-market'), instrument: g('jf-inst').trim(), symbol: g('jf-sym').trim(),
      strike: num(g('jf-strike')), opt: g('jf-opt'), expiry: g('jf-expiry'),
      dir: g('jf-dir'), setup: g('jf-setup').trim(), tf: g('jf-tf').trim(), ind: g('jf-ind').trim(),
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
    if (ds.entries >= S.maxTrades) msgs.push(`<li class="down">⛔ Daily limit reached — ${ds.entries}/${S.maxTrades} entries used.</li>`);
    box.innerHTML = `<div class="jv-calc-grid">
      <div><small>Risk budget (${S.riskPct}% of ${inr(equity(), 0)})</small><b>${inr(v.bud, 0)}</b></div>
      <div><small>Initial risk (₹)</small><b class="${v.overBudget ? 'down' : ''}">${v.risk ? inr(v.risk, 0) : '—'}</b></div>
      <div><small>Suggested quantity</small><b>${v.sugg || '—'}</b></div>
      <div><small>Planned R:R (to T2)</small><b>${v.plannedRR != null ? v.plannedRR.toFixed(2) + ':1' : '—'}</b></div>
      <div><small>Trades today</small><b>${ds.entries} / ${S.maxTrades}</b></div></div><ul class="jv-msgs">${msgs.join('') || '<li class="up">✓ Plan passes all checks</li>'}</ul>`;
    const ovr = document.getElementById('jvOvr'); if (ovr) ovr.hidden = !(v.overBudget || (v.plannedRR != null && v.plannedRR < S.minRR) || ds.entries >= S.maxTrades);
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
    T.push(buildTrade(f, 'Planned')); persist(); ui.draft = null; toast_('Plan saved (not counted as an entry)', 'ok'); ui.tab = 'open'; render();
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
      T.push(t); persist(); ui.draft = null; if (window.closeModal) window.closeModal(); toast_('Entry recorded: ' + t.id, 'ok'); ui.tab = 'open'; render();
    };
    if (window.modal) {
      window.modal('Confirm paper entry', body, { foot: '<button class="btn" data-jv="cancelmodal">Cancel</button><button class="btn pri" id="jvConfirm">Record entry</button>' });
      const b = document.getElementById('jvConfirm'); if (b) b.onclick = go;
    } else if (confirm('Record this paper entry?')) go();
  }

  /* ---------- trade detail ---------- */
  function openDetail(id) {
    const t = T.find(x => x.id === id) || AUTO.list.find(x => x.id === id); if (!t) return; ui.sel = id;
    const c = calc(t), st = statusOf(t), u = unrealised(t), rem = t.qty - c.qx;
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
      `<button class="btn" data-jv="savereview" data-id="${t.id}">Save review</button>`);
    window.modal ? window.modal(`${t.id} · ${E(t.symbol || t.instrument)} ${t.dir}`, body, { foot, wide: true }) : alert('Detail unavailable');
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
    const t = AUTO.list.find(x => x.id === id); if (!t) return;
    smallForm('Exit now · ' + t.id, `<p>Close <b>${E(t.symbol)}</b> at the live bid? This ends the paper trade; you can't undo it.</p>`, 'Exit now', () => {
      const ok = document.getElementById('jvFormOk'); ok.disabled = true; ok.textContent = 'Exiting…';
      jpost('/api/auto/trade/' + encodeURIComponent(id) + '/exit').then(async r => {
        ok.disabled = false; ok.textContent = 'Exit now';
        if (!r.ok) { const er = document.getElementById('jvFormErr'); er.textContent = r.err; er.hidden = false; return; }
        window.closeModal(); await syncAuto(true); render(); toast_(`Exited ${t.id} at ${px(r.d.exit)} · net ${sinr(r.d.net)}`, 'ok');
      });
      return null;
    });
  }
  function exitAll() {
    const open = allTrades().filter(t => entered(t) && statusOf(t) !== 'Closed');
    if (!open.length) { toast_('No open positions to exit.', 'warn'); return; }
    const unr = open.reduce((a, t) => a + (unrealised(t) || 0), 0);
    smallForm('Exit all positions', `<p>Exit <b>${open.length}</b> open position${open.length === 1 ? '' : 's'} at live prices? Open P&L right now: <b class="${cc(unr)}">${sinr(unr)}</b>. This can't be undone.</p>`, 'Exit all', () => {
      const ok = document.getElementById('jvFormOk'), er = document.getElementById('jvFormErr'); ok.disabled = true;
      (async () => {
        let done = 0, fail = []; const now = new Date();
        for (const t of open) {
          ok.textContent = `Exiting ${done + fail.length + 1}/${open.length}…`;
          if (t.auto) { const r = await jpost('/api/auto/trade/' + encodeURIComponent(t.id) + '/exit'); if (r.ok) done++; else fail.push(t.id + ': ' + r.err); }
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
  const SV = { auto: null, bt: null, btBusy: false, loading: false };
  async function jget(url, opt) { const r = await fetch(url, Object.assign({ cache: 'no-store' }, opt || {})); if (!r.ok) throw new Error(url + ' ' + r.status); return r.json(); }
  async function loadSrv(which) {
    try {
      if (which === 'auto') SV.auto = await jget('/api/auto/status');
      else { const b = await jget('/api/backtest'); SV.bt = b; SV.btBusy = !!b.running; }
    } catch (e) { if (which === 'auto') SV.auto = { error: String(e.message || e) }; else SV.bt = { error: String(e.message || e) }; }
    const eff = effTab(); if (eff === which || (which === 'bt' && eff === 'backtest')) render();
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
      ${R.executor ? twoMonthCard(R.executor, 'What a 2-month run of the 5-a-day executor would have returned', 'Proven strategies only, replayed on the out-of-sample period.') : ''}
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
    const activityList = log => { if (!log.length) return '<p class="muted" style="padding:0 14px 12px">No activity yet. The first entries are made from 09:15 IST on the next trading day.</p>';
      const { part, bar } = pagerBar(log, 'activity');
      return `<ul class="jv-stops" style="padding:0 14px 12px 30px">${part.map(l => `<li>${new Date(l.at).toLocaleString('en-IN')} — ${E(l.msg)}</li>`).join('')}</ul>${bar}`; };
    return `<div class="card"><div class="card-h"><h3>Automated paper trades — 3 index options + 2 stock options a day</h3></div>
      <div style="padding:0 14px 12px"><p>${unproven ? '<span class="badge b-down">UNPROVEN · forward test</span> ' : '<span class="badge b-up">Proven strategies</span> '}${E(A.mode)}.
        ${unproven ? 'No strategy passed the backtest, so these trades are a live, out-of-sample experiment: results here are the only evidence that can\'t be flattered by hindsight.' : ''}</p>
        <p class="muted">Simulated at live option prices — no broker is connected and no real order is ever sent. Entries start at the 09:15 open: strategy signals come from the previous session, the other slots from live screens. Exits follow the rule on the underlying. At most 5 entries a day.</p>
        <div class="jv-actions" style="padding:0"><button class="btn ${c.enabled ? '' : 'pri'}" data-jv="autotoggle">${c.enabled ? 'Pause auto trader' : 'Resume auto trader'}</button>
        <button class="btn" data-jv="autoresearch">${c.researchMode ? 'Research mode: ON (click to switch off)' : 'Research mode: OFF (click to switch on)'}</button>
        <button class="btn" data-jv="autorefresh">Refresh</button></div></div></div>
      <div class="jv-kpis">
        ${kpi('Status', c.enabled ? (A.marketOpen ? 'Running' : 'Waiting for market') : 'Paused')}
        ${kpi('Entries today', A.todayCount + ' / ' + c.maxPerDay, 'index ' + nIdx + '/' + c.indexSlots + ' · stock ' + nStk + '/' + c.stockSlots)}
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
      const mode = (t.tsl && t.tsl !== 'Off / Fixed SL') ? t.tsl : null;
      const l = live(t.symbol || t.instrument); if (l == null) return;
      const d = dirOf(t), r0 = Math.abs(t.entry - t.sl0);
      if (d > 0) t.hi = Math.max(t.hi == null ? t.entry : t.hi, l); else t.lo = Math.min(t.lo == null ? t.entry : t.lo, l);
      const ext = d > 0 ? t.hi : t.lo, fav = d * (ext - t.entry);
      let ns = null;
      if (!mode) { /* fixed stop-loss: nothing to trail */ }
      else if (mode === 'Breakeven') { if (fav >= (t.tslTrig == null ? 1 : t.tslTrig) * r0) ns = t.entry; }
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
          t.rule = t.rule || (t.validSetup === false ? 'No' : 'Yes'); t.reviewed = t.reviewed || !!t.rule;
          toast_(`${t.id}: ${type} hit — exited ${rem} at ${px(l)}`, 'warn');
        }
      } else if (tgtOf(t) && d * (l - tgtOf(t)) >= 0) {                              // target reached: book the rest
        const rem = t.qty - exitedQty(t);
        if (rem > 0) {
          const now = new Date();
          t.exits.push({ qty: rem, price: +l.toFixed(2), type: 'T2', date: istDay(now), time: istTime(now) });
          if (!t.hits.includes('T2')) { t.hits.push('T2'); t.hitOrder.push('T2'); }
          t.exitType = 'T2'; t.status = 'Closed'; t.closedAt = now.toISOString(); changed = true;
          t.rule = t.rule || (t.validSetup === false ? 'No' : 'Yes'); t.reviewed = true;
          toast_(`${t.id}: target hit — booked ${rem} at ${px(l)}`, 'ok');
        }
      }
    });
    if (changed) { persist(); if (document.getElementById('v-journal') && !document.querySelector('.modal-bg') && !document.querySelector('.jq-sheet-bg')) render(); }
  }

  /* ---------- summary strip: the same headline numbers at the top of every tab ---------- */

  /* ================= Simple trading screens: Positions / Pending / History / Summary =================
     One-screen "New trade" sheet (buy price, SL, target, R:R), one-tap Exit, one-tap Reset. */
  const isOpenT = t => entered(t) && statusOf(t) !== 'Closed';
  const tgtOf = t => t.t2 || t.t1 || t.t3 || null;
  const rrOf = t => { const r = Math.abs(t.entry - (t.sl0 || t.sl)), g = tgtOf(t) ? Math.abs(tgtOf(t) - t.entry) : 0; return r > 0 && g > 0 ? g / r : null; };
  const ltpOf = t => (t.auto ? (typeof t.ltp === 'number' ? t.ltp : null) : live(t.symbol || t.instrument));
  const guessMarket = inst => {
    const u = String(inst || '').toUpperCase();
    if (/\d\s*(CE|PE)\b/.test(u)) return 'Options';
    if (/FUT\b/.test(u)) return 'Futures';
    try { const s = typeof SYM === 'function' ? SYM(u) : null; if (s && s.cls === 'Indices') return 'Index'; } catch (e) { }
    return 'Equity Intraday';
  };
  const recentSyms = () => { const seen = []; T.slice().reverse().forEach(t => { const s = t.instrument || t.symbol; if (s && !seen.includes(s)) seen.push(s); }); return seen.slice(0, 4); };

  function hero() {
    const day = today(), L = liveTotals(day), ds = dayStats(day), all = allTrades();
    const openN = all.filter(isOpenT).length, todayAll = ds.pnl + L.autoToday + L.unr;
    return `<section class="jq-hero" id="jqHero" aria-label="Account summary">
      <div class="jq-hero-top"><span>Open profit &amp; loss</span><button type="button" class="jq-reset" data-jv="reset" title="Clear every trade and start again">Reset portfolio</button></div>
      <div class="jq-pl ${cc(L.unr)}">${sinr(L.unr)}</div>
      <div class="jq-hero-grid">
        <div><small>Balance</small><b>${inr(S.capital + L.booked, 0)}</b></div>
        <div><small>Equity</small><b>${inr(L.eq, 0)}</b></div>
        <div><small>Today</small><b class="${cc(todayAll)}">${sinr(todayAll)}</b></div>
        <div><small>Open</small><b>${openN}</b></div>
      </div></section>`;
  }

  function posCard(t) {
    const c = calc(t), u = unrealised(t), l = ltpOf(t), tg = tgtOf(t), rrv = rrOf(t);
    const pnl = (c.qx ? c.net : 0) + (u || 0), has = c.qx || u != null, rem = t.qty - c.qx;
    let bar = '';
    if (tg && l != null && t.sl > 0) {
      const lo = Math.min(t.sl, tg), hi = Math.max(t.sl, tg), p = Math.max(0, Math.min(100, (l - lo) / (hi - lo) * 100)), e = Math.max(0, Math.min(100, (t.entry - lo) / (hi - lo) * 100));
      const flip = t.sl > tg;   // short: SL is the higher price
      bar = `<div class="jq-bar" title="Left = stop-loss, right = target"><i class="jq-e" style="left:${flip ? 100 - e : e}%"></i><i class="jq-m" style="left:${flip ? 100 - p : p}%"></i></div>`;
    }
    return `<article class="jq-card${t.auto ? ' auto' : ''}" data-jv="open" data-id="${t.id}" tabindex="0" title="Tap for full details">
      <div class="jq-r1"><b>${E(t.symbol || t.instrument)}</b><span class="jq-side ${t.dir === 'Short' ? 'sell' : 'buy'}">${t.dir === 'Short' ? 'Sell' : 'Buy'} · ${rem}${rem !== t.qty ? '/' + t.qty : ''}</span><span class="jq-pnl ${cc(pnl)}">${has ? sinr(pnl) : '—'}</span></div>
      <div class="jq-r2"><span>${px(t.entry)} <i>→</i> ${l != null ? '<b>' + px(l) + '</b>' : '<em>no live price</em>'}</span>${t.auto ? '<span class="jq-tag">AUTO</span>' : ''}</div>
      ${bar}
      <div class="jq-lv"><span>SL <b class="down">${px(t.sl)}</b></span><span>TGT <b class="up">${tg ? px(tg) : '—'}</b></span><span>R:R <b>${rrv ? '1:' + rrv.toFixed(1) : '—'}</b></span></div>
      <div class="jq-r3"><small>${E(t.id)} · ${String(t.date).slice(5)} ${E(t.time || '')}</small><button type="button" class="jv-exit jq-exit" data-jv="${t.auto ? 'autoexit' : 'exitsheet'}" data-id="${t.id}">Exit</button></div>
    </article>`;
  }
  const openCards = () => {
    const list = allTrades().filter(isOpenT).sort((a, b) => (b.date + (b.time || '')).localeCompare(a.date + (a.time || '')));
    if (!list.length) return `<div class="jq-empty"><b>No open positions</b><span>Tap <b>+</b> to add a paper trade in one screen.</span><button type="button" class="btn pri" data-jv="addsheet">+ New trade</button></div>`;
    return `<div class="jq-exall"><span class="muted">${list.length} open</span><button type="button" class="jv-exit jv-exitall" data-jv="exitall">Exit all</button></div>` + list.map(posCard).join('');
  };
  function viewOpen() { return `<div id="jqOpen">${openCards()}</div>`; }

  function viewPending() {
    const list = T.filter(t => t.status === 'Planned').sort((a, b) => (b.date + (b.time || '')).localeCompare(a.date + (a.time || '')));
    if (!list.length) return `<div class="jq-empty"><b>No pending plans</b><span>Use <b>Save as plan</b> in the New trade sheet to line up a trade for later.</span></div>`;
    return list.map(t => `<article class="jq-card" data-jv="open" data-id="${t.id}" tabindex="0">
      <div class="jq-r1"><b>${E(t.symbol || t.instrument)}</b><span class="jq-side ${t.dir === 'Short' ? 'sell' : 'buy'}">${t.dir === 'Short' ? 'Sell' : 'Buy'} · ${t.qty}</span></div>
      <div class="jq-lv"><span>Entry <b>${px(t.entry)}</b></span><span>SL <b class="down">${px(t.sl)}</b></span><span>TGT <b class="up">${tgtOf(t) ? px(tgtOf(t)) : '—'}</b></span></div>
      <div class="jq-r3"><button type="button" class="btn" data-jv="cancelplan" data-id="${t.id}">Delete</button><button type="button" class="btn pri" data-jv="startplan" data-id="${t.id}">Enter at plan price</button></div></article>`).join('');
  }

  function histCard(t) {
    const c = calc(t), last = (t.exits || []).slice(-1)[0], rrv = c.R;
    return `<article class="jq-card" data-jv="open" data-id="${t.id}" tabindex="0" title="Tap for full details">
      <div class="jq-r1"><b>${E(t.symbol || t.instrument)}</b><span class="jq-side ${t.dir === 'Short' ? 'sell' : 'buy'}">${t.dir === 'Short' ? 'Sell' : 'Buy'} · ${t.qty}</span><span class="jq-pnl ${cc(c.net)}">${sinr(c.net)}</span></div>
      <div class="jq-r2"><span>${px(t.entry)} <i>→</i> <b>${last ? px(last.price) : '—'}</b></span><span class="jq-tag ${t.rule === 'Yes' ? 'ok' : t.rule === 'No' ? 'bad' : ''}">${E(t.exitType || 'Closed')}${t.rule === 'Yes' ? ' · rules ✓' : t.rule === 'No' ? ' · rule broken' : ''}</span></div>
      <div class="jq-r3"><small>${E(t.id)} · ${String(t.date).slice(5)} ${E(t.time || '')}</small><small class="${cc(rrv)}">${rr(rrv)}</small></div></article>`;
  }
  function viewHistory() {
    const list = filtered().filter(t => entered(t) && statusOf(t) === 'Closed').sort((a, b) => lastExit(b).localeCompare(lastExit(a)));
    const n = ui.histN || 20, part = list.slice(0, n);
    return filterBar() + (list.length ? part.map(histCard).join('') + (list.length > n ? `<button type="button" class="btn jq-more" data-jv="histmore">Show more (${list.length - n} left)</button>` : '')
      : `<div class="jq-empty"><b>No closed trades yet</b><span>Closed trades appear here with their result.</span></div>`);
  }

  function viewSummary() {
    const L = filtered(), m = metrics(L), cl = L.filter(t => entered(t) && statusOf(t) === 'Closed');
    let cum = 0; const curve = [S.capital]; m.sorted.forEach(r => { cum += r.c.net; curve.push(S.capital + cum); });
    const daily = {}; m.sorted.forEach(r => { const d = lastExit(r.t).slice(0, 10); daily[d] = (daily[d] || 0) + r.c.net; });
    let pk = -Infinity; const dd = curve.map(v => { pk = Math.max(pk, v); return v - pk; });
    const followed = cl.filter(t => t.rule === 'Yes'), broke = cl.filter(t => t.rule === 'No'), sum = a => a.reduce((x, t) => x + calc(t).net, 0);
    const judged = followed.length + broke.length;
    return `${filterBar()}
      <div class="jq-stats">
        <div><small>Trades</small><b>${m.n}</b></div>
        <div><small>Win rate</small><b>${(m.winRate * 100).toFixed(0)}%</b></div>
        <div><small>Net P&amp;L</small><b class="${cc(m.net)}">${sinr(m.net)}</b></div>
        <div><small>Rules followed</small><b>${judged ? Math.round(followed.length / judged * 100) + '%' : '—'}</b></div>
      </div>
      <div class="jq-note">When you followed your rules: <b>${followed.length} trade${followed.length === 1 ? '' : 's'}, ${sinr(sum(followed))}</b>. When you broke a rule: <b>${broke.length} trade${broke.length === 1 ? '' : 's'}, ${sinr(sum(broke))}</b>.</div>
      <div class="jv-kpis">${kpi('Avg win', inr(m.avgWin, 0), '', 'up')}${kpi('Avg loss', inr(m.avgLoss, 0), '', 'down')}${kpi('Profit factor', m.pf === Infinity ? '∞' : m.pf.toFixed(2), '')}${kpi('Expectancy', rr(m.expR), '', cc(m.expR))}${kpi('Max drawdown', inr(m.maxDD, 0), '', m.maxDD > 0 ? 'down' : '')}</div>
      <div class="jv-grid">
        <div class="card"><div class="card-h"><h3>Equity curve</h3></div><canvas class="jv-cv" id="jvEq"></canvas></div>
        <div class="card"><div class="card-h"><h3>Drawdown</h3></div><canvas class="jv-cv" id="jvDd"></canvas></div>
        <div class="card"><div class="card-h"><h3>Daily P&amp;L</h3></div><canvas class="jv-cv" id="jvDay"></canvas></div>
      </div>
      <div class="jq-foot"><button type="button" class="btn" data-jv="csv">Export CSV</button><button type="button" class="btn jq-danger" data-jv="reset">Reset portfolio</button></div>
      <script type="application/json" id="jvChartData">${JSON.stringify({ curve, dd, daily: Object.keys(daily).sort().map(k => daily[k]) })}</script>`;
  }

  /* ---------- bottom sheet ---------- */
  function showSheet(title, body, cls) {
    closeSheet();
    const bg = document.createElement('div'); bg.className = 'jq-sheet-bg'; bg.setAttribute('data-jqbg', '1');
    bg.innerHTML = `<div class="jq-sheet ${cls || ''}" role="dialog" aria-modal="true" aria-label="${E(title)}"><div class="jq-sheet-h"><b>${E(title)}</b><button type="button" class="jq-x" data-jv="closesheet" aria-label="Close">✕</button></div><div class="jq-sheet-b">${body}</div></div>`;
    document.body.appendChild(bg); document.body.classList.add('jq-lock');
    return bg;
  }
  function closeSheet() { const s = document.querySelector('.jq-sheet-bg'); if (s) s.remove(); document.body.classList.remove('jq-lock'); }
  document.addEventListener('click', e => { if (e.target.matches && e.target.matches('.jq-sheet-bg')) closeSheet(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && document.querySelector('.jq-sheet-bg')) closeSheet(); });

  /* ---------- New trade (quick) ---------- */
  const Q = { dir: 'Long', valid: true };
  const qv = id => { const e = document.getElementById(id); return e ? e.value : ''; };
  const qset = (id, v) => { const e = document.getElementById(id); if (e) e.value = v == null || !isFinite(v) ? '' : +(+v).toFixed(2); };
  function openAddSheet(prefill) {
    Q.dir = (prefill && prefill.dir) || 'Long'; Q.valid = true;
    const syms = (typeof SYMS !== 'undefined') ? SYMS.slice(0, 500).map(s => `<option value="${E(s.s)}">`).join('') : '';
    const quick = ['NIFTY', 'BANKNIFTY'].concat(recentSyms()).filter((v, i, a) => a.indexOf(v) === i).slice(0, 6);
    const pre = prefill || {};
    showSheet('New trade', `<form id="jqForm" autocomplete="off" onsubmit="return false">
      <label class="jq-f"><span>Instrument</span><input class="inp" id="q-inst" list="jvSyms" autocapitalize="characters" placeholder="NIFTY · RELIANCE · NIFTY 24500 CE" value="${E(pre.instrument || '')}"><datalist id="jvSyms">${syms}</datalist></label>
      <div class="jq-chips" id="q-quick">${quick.map(s => `<button type="button" class="jq-chip" data-jq="inst" data-v="${E(s)}">${E(s)}</button>`).join('')}<span class="jq-live" id="q-live"></span></div>
      <div class="jq-seg2" role="group" aria-label="Side"><button type="button" class="buy on" data-jq="side" data-v="Long">Buy</button><button type="button" class="sell" data-jq="side" data-v="Short">Sell</button></div>
      <div class="jq-grid4">
        <label class="jq-f"><span id="q-entry-l">Buy price</span><input class="inp" id="q-entry" type="number" step="any" inputmode="decimal" value="${pre.entry || ''}"></label>
        <label class="jq-f"><span>Stop-loss</span><input class="inp" id="q-sl" type="number" step="any" inputmode="decimal"></label>
        <label class="jq-f"><span>Target</span><input class="inp" id="q-tgt" type="number" step="any" inputmode="decimal"></label>
        <label class="jq-f"><span>R:R (1 : x)</span><input class="inp" id="q-rr" type="number" step="0.1" min="0" inputmode="decimal"></label>
      </div>
      <div class="jq-lbl">Stop-loss distance</div>
      <div class="jq-chips">${[0.5, 1, 2, 5, 10, 20].map(p => `<button type="button" class="jq-chip" data-jq="slpct" data-v="${p}">${p}%</button>`).join('')}</div>
      <div class="jq-lbl">Risk : Reward</div>
      <div class="jq-chips" id="q-rrchips">${[1, 1.5, 2, 3, 4].map(r => `<button type="button" class="jq-chip" data-jq="rr" data-v="${r}">1:${r}</button>`).join('')}</div>
      <div class="jq-grid4 jq-qtyrow">
        <label class="jq-f"><span>Quantity</span><input class="inp" id="q-qty" type="number" step="1" min="1" inputmode="numeric" value="${pre.qty || ''}"></label>
        <div class="jq-f"><span>Valid setup?</span><div class="jq-yn" id="q-valid"><button type="button" class="on" data-jq="valid" data-v="1">Yes</button><button type="button" data-jq="valid" data-v="0">No</button></div></div>
      </div>
      <div class="jq-calc" id="q-calc"></div>
      <details class="jq-more-d"><summary>More details (optional)</summary>
        <label class="jq-f"><span>Strategy / setup name</span><input class="inp" id="q-setup" placeholder="e.g. breakout, UT Bot"></label>
        <label class="jq-f"><span>How do you feel?</span><select class="inp" id="q-feel">${['Calm', 'Confident', 'Anxious', 'FOMO', 'Greedy', 'Revenge'].map(x => `<option>${x}</option>`).join('')}</select></label>
        <label class="jq-f"><span>Note</span><input class="inp" id="q-note" placeholder="What did you learn / why this trade?"></label>
      </details>
      <div class="jq-actions"><button type="button" class="btn" data-jq="plan">Save as plan</button><button type="button" class="btn pri jq-go" data-jq="add">Add trade</button></div>
    </form>`);
    qRefresh(); const i = document.getElementById('q-inst'); if (i && !i.value) setTimeout(() => { try { i.focus(); } catch (e) { } }, 60);
    if (i && i.value) qLive(true);
  }
  function qRead() {
    const dir = Q.dir, entry = num(qv('q-entry')), sl = num(qv('q-sl')), tgt = num(qv('q-tgt')), qty = num(qv('q-qty'));
    return { dir, entry, sl, tgt, qty, inst: qv('q-inst').trim().toUpperCase() };
  }
  function qLive(fill) {
    const inst = qv('q-inst').trim().toUpperCase(), l = inst ? live(inst) : null, box = document.getElementById('q-live');
    if (box) box.innerHTML = l != null ? `<button type="button" class="jq-chip live" data-jq="uselive" data-v="${l}">Live ${px(l)} · use</button>` : '';
    if (fill && l != null && !(num(qv('q-entry')) > 0)) { qset('q-entry', l); qRefresh(); }
    return l;
  }
  function qRefresh() {
    const f = qRead(), d = f.dir === 'Short' ? -1 : 1, lab = document.getElementById('q-entry-l'); if (lab) lab.textContent = d > 0 ? 'Buy price' : 'Sell price';
    const box = document.getElementById('q-calc'); if (!box) return;
    const msgs = [], risk1 = f.entry > 0 && f.sl > 0 ? Math.abs(f.entry - f.sl) : 0;
    if (f.entry > 0 && f.sl > 0 && d * (f.entry - f.sl) <= 0) msgs.push(`<li class="down">✖ For a ${d > 0 ? 'Buy' : 'Sell'}, stop-loss must be ${d > 0 ? 'below' : 'above'} the price.</li>`);
    if (f.tgt > 0 && f.entry > 0 && d * (f.tgt - f.entry) <= 0) msgs.push(`<li class="down">✖ Target must be ${d > 0 ? 'above' : 'below'} the price.</li>`);
    const rrv = risk1 > 0 && f.tgt > 0 ? Math.abs(f.tgt - f.entry) / risk1 : null;
    document.querySelectorAll('#q-rrchips .jq-chip').forEach(b => b.classList.toggle('on', rrv != null && Math.abs(rrv - +b.dataset.v) < 0.05));
    const risk = risk1 * (f.qty || 0), reward = rrv != null ? Math.abs(f.tgt - f.entry) * (f.qty || 0) : null, bud = budget(), sugg = risk1 > 0 ? Math.floor(bud / risk1) : 0;
    const l = f.inst ? live(f.inst) : null;
    if (l != null && f.entry > 0) {
      if (d * (l - f.sl) <= 0 && f.sl > 0) msgs.push(`<li class="warn">⚠ Live price ${px(l)} is already beyond your stop-loss — the trade would exit at once.</li>`);
      else if (Math.abs(l - f.entry) / l > 0.01) msgs.push(`<li class="warn">⚠ Your price is ${(Math.abs(l - f.entry) / l * 100).toFixed(1)}% away from the live price ${px(l)}.</li>`);
    }
    if (risk > bud + 1e-9 && f.qty > 0) msgs.push(`<li class="warn">⚠ Risk ${inr(risk, 0)} is above your ${S.riskPct}% budget ${inr(bud, 0)}.</li>`);
    const ds = dayStats(today()); if (ds.entries >= S.maxTrades) msgs.push(`<li class="warn">⚠ That is trade ${ds.entries + 1} today (your plan was ${S.maxTrades}).</li>`);
    box.innerHTML = `<div class="jq-calc-g"><div><small>Risk</small><b class="${risk > bud + 1e-9 ? 'down' : ''}">${risk ? inr(risk, 0) : '—'}</b></div><div><small>Reward</small><b class="up">${reward != null ? inr(reward, 0) : '—'}</b></div><div><small>R:R</small><b>${rrv != null ? '1:' + rrv.toFixed(2) : '—'}</b></div>
      <div><small>Suggested qty</small><b>${sugg > 0 ? `<button type="button" class="jq-link" data-jq="usesugg" data-v="${sugg}">${sugg}</button>` : '—'}</b></div></div>${msgs.length ? `<ul class="jv-msgs">${msgs.join('')}</ul>` : ''}`;
  }
  function qInput(id) {   // keep SL / target / R:R in sync as the user types
    const f = qRead(), d = f.dir === 'Short' ? -1 : 1, r = f.entry > 0 && f.sl > 0 ? Math.abs(f.entry - f.sl) : 0;
    if (id === 'q-rr') { const x = num(qv('q-rr')); if (r > 0 && x > 0) qset('q-tgt', f.entry + d * r * x); }
    else if (id === 'q-tgt' || id === 'q-sl' || id === 'q-entry') { const g = qRead(), rr2 = g.entry > 0 && g.sl > 0 ? Math.abs(g.entry - g.sl) : 0; if (rr2 > 0 && g.tgt > 0) qset('q-rr', Math.abs(g.tgt - g.entry) / rr2); else if (id !== 'q-rr' && !(g.tgt > 0)) qset('q-rr', ''); }
    qRefresh();
  }
  function qBuild(status) {
    const f = qRead(), d = f.dir === 'Short' ? -1 : 1, errs = [];
    if (!f.inst) errs.push('Pick an instrument.');
    if (!(f.entry > 0)) errs.push(`Enter the ${d > 0 ? 'buy' : 'sell'} price.`);
    if (!(f.sl > 0)) errs.push('Stop-loss is required.');
    else if (f.entry > 0 && d * (f.entry - f.sl) <= 0) errs.push(`Stop-loss must be ${d > 0 ? 'below' : 'above'} the price for a ${d > 0 ? 'Buy' : 'Sell'}.`);
    if (f.tgt > 0 && f.entry > 0 && d * (f.tgt - f.entry) <= 0) errs.push(`Target must be ${d > 0 ? 'above' : 'below'} the price.`);
    if (!(f.qty >= 1) || Math.floor(f.qty) !== f.qty) errs.push('Quantity must be a whole number (1 or more).');
    if (errs.length) { toast_(errs[0], 'err'); return null; }
    const now = new Date(), mk = guessMarket(f.inst);
    const t = buildTrade({ date: istDay(now), time: istTime(now), market: mk, instrument: f.inst, symbol: f.inst, dir: f.dir, setup: qv('q-setup').trim() || 'Quick trade', tf: '', ind: '',
      entry: f.entry, sl: f.sl, qty: f.qty, mult: 1, t1: null, t2: f.tgt > 0 ? f.tgt : null, t3: null, tsl: TSL_MODES[0], tslTrig: S.labTrigger, trail: null, step: null, why: qv('q-note').trim(), ovr: '' }, status);
    t.validSetup = Q.valid; t.emotion = qv('q-feel');
    return t;
  }
  function qAdd(status) {
    const t = qBuild(status); if (!t) return;
    T.push(t); persist(); closeSheet();
    toast_(status === 'Planned' ? 'Saved as a pending plan' : `${t.dir === 'Short' ? 'Sell' : 'Buy'} ${t.instrument} added`, 'ok');
    ui.tab = status === 'Planned' ? 'pending' : 'open'; render(); applyManualTsl();
  }

  /* ---------- one-tap Exit ---------- */
  function openExitSheet(id) {
    const t = T.find(x => x.id === id); if (!t) return;
    const rem = t.qty - exitedQty(t), l = live(t.symbol || t.instrument);
    showSheet('Exit ' + (t.symbol || t.instrument), `<form id="jqExit" data-id="${t.id}" onsubmit="return false">
      <p class="jq-sub">${t.dir === 'Short' ? 'Sell' : 'Buy'} @ ${px(t.entry)} · SL ${px(t.sl)} · TGT ${tgtOf(t) ? px(tgtOf(t)) : '—'}${l != null ? ` · live <b>${px(l)}</b>` : ''}</p>
      <div class="jq-grid4"><label class="jq-f"><span>Exit price</span><input class="inp" id="x-p" type="number" step="any" inputmode="decimal" value="${l != null ? +l.toFixed(2) : ''}"></label>
        <label class="jq-f"><span>Quantity (max ${rem})</span><input class="inp" id="x-q" type="number" step="1" min="1" max="${rem}" inputmode="numeric" value="${rem}"></label></div>
      <div class="jq-f"><span>Did you respect your stop-loss &amp; plan?</span><div class="jq-yn" id="x-rule"><button type="button" class="on" data-jq="rule" data-v="Yes">Yes</button><button type="button" data-jq="rule" data-v="No">No</button></div></div>
      <div class="jq-calc" id="x-calc"></div>
      <div class="jq-actions"><button type="button" class="btn" data-jv="closesheet">Cancel</button><button type="button" class="btn pri jq-go" data-jq="doexit">Exit trade</button></div></form>`);
    xRefresh();
  }
  function xRefresh() {
    const f = document.getElementById('jqExit'); if (!f) return; const t = T.find(x => x.id === f.dataset.id); if (!t) return;
    const p = num(qv('x-p')), q = num(qv('x-q')), box = document.getElementById('x-calc'); if (!box) return;
    if (!(p > 0) || !(q > 0)) { box.innerHTML = ''; return; }
    const g = dirOf(t) * (p - t.entry) * q * units(t);
    box.innerHTML = `<div class="jq-calc-g"><div><small>Result of this exit</small><b class="${cc(g)}">${sinr(g)}</b></div></div>`;
  }
  function doExit() {
    const f = document.getElementById('jqExit'); if (!f) return; const t = T.find(x => x.id === f.dataset.id); if (!t) return;
    const rem = t.qty - exitedQty(t), p = num(qv('x-p')), q = num(qv('x-q')), on = document.querySelector('#x-rule .on');
    if (!(p > 0)) { toast_('Enter the exit price.', 'err'); return; }
    if (!(q >= 1) || Math.floor(q) !== q || q > rem) { toast_('Quantity must be a whole number up to ' + rem + '.', 'err'); return; }
    const d = dirOf(t), type = (t.sl > 0 && d * (p - t.sl) <= 0) ? (t.sl === t.sl0 ? 'SL' : 'TSL') : (tgtOf(t) && d * (p - tgtOf(t)) >= 0 ? 'T2' : 'Manual Exit'), now = new Date();
    t.exits.push({ qty: q, price: p, type, date: istDay(now), time: istTime(now) }); t.exitType = type;
    if (type === 'T2' && !t.hits.includes('T2')) { t.hits.push('T2'); t.hitOrder.push('T2'); }
    t.rule = (on && on.dataset.v === 'No') || t.validSetup === false ? 'No' : 'Yes';
    if (statusOf(t) === 'Closed') { t.status = 'Closed'; t.closedAt = now.toISOString(); t.reviewed = true; }
    persist(); closeSheet(); toast_(`Exited ${t.symbol || t.instrument} at ${px(p)}`, 'ok'); render();
  }
  function startPlan(id) {
    const t = T.find(x => x.id === id); if (!t) return; const now = new Date();
    t.status = 'Open'; t.date = istDay(now); t.time = istTime(now); t.at = now.toISOString(); persist(); ui.tab = 'open'; toast_('Entered at plan price', 'ok'); render();
  }

  /* ---------- Reset portfolio ---------- */
  function openResetSheet() {
    showSheet('Reset portfolio', `<form id="jqReset" onsubmit="return false">
      <p class="jq-sub">This deletes <b>every manual trade, plan and review</b> on this device and starts again. Export a CSV first if you want a copy.</p>
      <label class="jq-f"><span>Starting capital (₹)</span><input class="inp" id="r-cap" type="number" step="1000" min="1000" inputmode="numeric" value="${S.capital}"></label>
      <p class="jq-sub muted">Auto-trader trades are kept on the server and are not removed here.</p>
      <div class="jq-actions"><button type="button" class="btn" data-jv="closesheet">Cancel</button><button type="button" class="btn jq-danger" data-jq="doreset">Reset everything</button></div></form>`, 'small');
  }
  function doReset() {
    const cap = num(qv('r-cap'));
    if (!(cap >= 1000)) { toast_('Enter a starting capital of at least ₹1,000.', 'err'); return; }
    T = []; S = Object.assign({}, DEFAULTS, { capital: cap }); persist(); persistS(); ui.draft = null; ui.histN = 20; closeSheet(); ui.tab = 'open';
    toast_('Portfolio reset — starting capital ' + inr(cap, 0), 'ok'); render();
  }

  /* ---------- sheet + quick-form events ---------- */
  document.addEventListener('click', e => {
    const b = e.target.closest && e.target.closest('[data-jq]'); if (!b) return;
    const a = b.dataset.jq, v = b.dataset.v; e.preventDefault();
    if (a === 'side') { Q.dir = v; document.querySelectorAll('.jq-seg2 button').forEach(x => x.classList.toggle('on', x === b)); const i = num(qv('q-sl')); qRefresh(); if (i > 0) qInput('q-sl'); }
    else if (a === 'inst') { qset('q-inst', null); document.getElementById('q-inst').value = v; document.getElementById('q-entry').value = ''; qLive(true); qRefresh(); }
    else if (a === 'uselive') { qset('q-entry', +v); qInput('q-entry'); }
    else if (a === 'slpct') { const f = qRead(); if (!(f.entry > 0)) { toast_('Enter the price first.', 'warn'); return; } const d = f.dir === 'Short' ? -1 : 1; qset('q-sl', f.entry * (1 - d * v / 100)); if (num(qv('q-rr')) > 0) qInput('q-rr'); else qInput('q-sl'); }
    else if (a === 'rr') { const f = qRead(); if (!(f.entry > 0 && f.sl > 0)) { toast_('Enter the price and stop-loss first.', 'warn'); return; } qset('q-rr', +v); qInput('q-rr'); }
    else if (a === 'usesugg') { qset('q-qty', +v); qRefresh(); }
    else if (a === 'valid') { Q.valid = v === '1'; document.querySelectorAll('#q-valid button').forEach(x => x.classList.toggle('on', x === b)); }
    else if (a === 'rule') { document.querySelectorAll('#x-rule button').forEach(x => x.classList.toggle('on', x === b)); }
    else if (a === 'add') qAdd('Open');
    else if (a === 'plan') qAdd('Planned');
    else if (a === 'doexit') doExit();
    else if (a === 'doreset') doReset();
  });
  document.addEventListener('input', e => {
    const id = e.target && e.target.id; if (!id) return;
    if (id === 'q-inst') { qLive(true); qRefresh(); }
    else if (/^q-(entry|sl|tgt|rr|qty)$/.test(id)) qInput(id);
    else if (id === 'x-p' || id === 'x-q') xRefresh();
  });
  document.addEventListener('change', e => { if (e.target && e.target.id === 'q-inst') { qLive(true); qRefresh(); } });

  /* ---------- shell ---------- */
  function render() {
    const el = document.getElementById('v-journal'); if (!el) return;
    syncAuto(false);
    applyManualTsl();
    const cnt = { open: allTrades().filter(isOpenT).length, pending: T.filter(t => t.status === 'Planned').length };
    const head = `<div class="jv-head"><h1 title="Plan, log and review paper trades">Journal</h1>${banner()}</div>`;
    const tabs = `<div class="jv-tabs" role="tablist">${TABS.map(([k, l]) => `<button role="tab" aria-selected="${ui.tab === k}" class="${ui.tab === k ? 'on' : ''}" data-jv="tab" data-k="${k}" title="${TAB_TIPS[k] || ''}">${l}${cnt[k] ? ` <i class="jq-cnt">${cnt[k]}</i>` : ''}</button>`).join('')}</div>`;
    const subtabs = GROUPS[ui.tab] ? `<div class="jv-tabs jv-subtabs" role="tablist">${GROUPS[ui.tab].map(([k, l]) => `<button role="tab" aria-selected="${ui.sub[ui.tab] === k}" class="${ui.sub[ui.tab] === k ? 'on' : ''}" data-jv="subtab" data-grp="${ui.tab}" data-k="${k}" title="${TAB_TIPS[k] || ''}">${l}</button>`).join('')}</div>` : '';
    const bodies = { open: viewOpen, pending: viewPending, journal: viewHistory, overview: viewSummary, new: viewNew, orders: viewOrders, strategy: viewStrategy, tsl: viewTsl, auto: viewAuto, backtest: viewBacktest, reports: viewReports, settings: viewSettings };
    el.innerHTML = `<div class="page jv">${head}${hero()}${tabs}${subtabs}${(bodies[effTab()] || viewOpen)()}<button type="button" class="jq-fab" data-jv="addsheet" aria-label="New trade" title="New trade">+</button></div>`;
    if (effTab() === 'overview') {
      const dEl = document.getElementById('jvChartData'); let d = { curve: [], dd: [], daily: [] };
      try { d = JSON.parse(dEl.textContent); } catch (e) { }
      requestAnimationFrame(() => {
        const a = document.getElementById('jvEq'), b = document.getElementById('jvDd'), c = document.getElementById('jvDay');
        a && drawLine(a, d.curve, css('--brand', '#4f8ef7'), true); b && drawLine(b, d.dd, css('--down', '#f7525f'), true); c && drawBars(c, d.daily);
      });
    }
    if (effTab() === 'new') renderCalc();
  }

  document.addEventListener('click', e => {
    const o = e.target.closest('[data-jvord]'); if (!o) return;
    if (typeof App !== 'undefined') App.ord = o.dataset.jvord;
    render();
  });

  /* ---------- events ---------- */
  document.addEventListener('click', e => {
    const b = e.target.closest('[data-jv]'); if (!b) return;
    const a = b.dataset.jv, id = b.dataset.id;
    if (!document.getElementById('v-journal') && !document.querySelector('.modal-bg')) return;
    if (a === 'tab') { ui.tab = b.dataset.k; const eff = effTab(); if (eff === 'auto') SV.auto = null; if (eff === 'backtest') SV.bt = null; render(); }
    else if (a === 'subtab') { ui.sub[b.dataset.grp] = b.dataset.k; if (b.dataset.k === 'auto') SV.auto = null; if (b.dataset.k === 'backtest') SV.bt = null; render(); }
    else if (a === 'open') { if (e.target.closest('[data-jv="exitsheet"],[data-jv="autoexit"],[data-jv="mktexit"]') && b.dataset.jv === 'open') return; openDetail(id); }
    else if (a === 'addsheet') openAddSheet();
    else if (a === 'closesheet') closeSheet();
    else if (a === 'exitsheet') { e.stopPropagation(); openExitSheet(id); }
    else if (a === 'reset') openResetSheet();
    else if (a === 'startplan') startPlan(id);
    else if (a === 'histmore') { ui.histN = (ui.histN || 20) + 20; render(); }
    else if (a === 'clearf') { ui.f = { from: '', to: '', market: '', inst: '', setup: '', dir: '', exit: '', rule: '' }; render(); }
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
    else if (a === 'mktexit') { window.closeModal && window.closeModal(); openExitSheet(id); }
    else if (a === 'movesl') moveSL(id);
    else if (a === 'savereview') saveReview(id);
    else if (a === 'enterplan') { const t = T.find(x => x.id === id); if (t) { ui.draft = Object.assign({}, t, { instrument: t.instrument, why: t.why, entry: t.entry, sl: t.sl0 }); T = T.filter(x => x.id !== id); persist(); window.closeModal && window.closeModal(); ui.tab = 'more'; ui.sub.more = 'new'; render(); } }
    else if (a === 'cancelplan') { const t = T.find(x => x.id === id); if (t) { t.status = 'Cancelled'; persist(); window.closeModal && window.closeModal(); render(); } }
    else if (a === 'favsave') { const t = T.find(x => x.id === id); if (t) { t.hi = num(document.getElementById('jd-hi').value); t.lo = num(document.getElementById('jd-lo').value); if (statusOf(t) === 'Closed') t.edited = true; persist(); toast_('Saved', 'ok'); } }
    else if (a === 'csv') exportCsv();
    else if (a === 'csvsum') exportSummary();
    else if (a === 'runlab') runLab();
    else if (a === 'btrun') { fetch('/api/backtest/run', { method: 'POST' }).then(() => { SV.btBusy = true; SV.bt = null; ui.tab = 'more'; ui.sub.more = 'backtest'; render(); const iv = setInterval(async () => { await loadSrv('bt'); if (SV.bt && !SV.bt.running) clearInterval(iv); }, 4000); }); }
    else if (a === 'autotoggle') { const on = !(SV.auto && SV.auto.cfg.enabled); fetch('/api/auto/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ enabled: on }) }).then(() => loadSrv('auto')); }
    else if (a === 'autoresearch') { const on = !(SV.auto && SV.auto.cfg.researchMode); fetch('/api/auto/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ researchMode: on }) }).then(() => loadSrv('auto')); }
    else if (a === 'autorefresh') { loadSrv('auto'); }
    else if (a === 'clearlog') { if (confirm('Clear the auto trader activity log? This cannot be undone.')) jpost('/api/auto/log/clear').then(() => loadSrv('auto')); }
    else if (a === 'defaults') { S = Object.assign({}, DEFAULTS); persistS(); render(); }
    else if (a === 'wipe') { if (confirm('Delete ALL journal records on this device? Export first if you need them.')) { T = []; persist(); render(); } }
  });
  document.addEventListener('change', e => {
    const h = e.target.closest('[data-jv="hit"]');
    if (h) {
      const t = T.find(x => x.id === ui.sel); if (!t) return; const k = h.dataset.k;
      if (h.checked && !t.hits.includes(k)) { t.hits.push(k); t.hitOrder.push(k); } else if (!h.checked) { t.hits = t.hits.filter(x => x !== k); t.hitOrder = t.hitOrder.filter(x => x !== k); }
      if (statusOf(t) === 'Closed') t.edited = true; persist(); return;
    }
    const f = e.target.closest('[data-jf]'); if (f) { ui.f[f.dataset.jf] = f.value; render(); return; }
    const s = e.target.closest('[data-jset]');
    if (s) { const k = s.dataset.jset; S[k] = k === 'allowOverride' ? s.value === '1' : (num(s.value) ?? DEFAULTS[k]); persistS(); if (effTab() === 'new') renderCalc(); }
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
    const [key, val] = (pg || ps).dataset[pg ? 'jvpg' : 'jvps'].split(':'), st = (ui.pg[key] = ui.pg[key] || { p: 0, s: 10 });
    if (pg) st.p = Math.max(0, +val); else { st.s = +val; st.p = 0; }
    const host = document.querySelector(`.jv-tw[data-jvt="${key}"]`), reg = ui.tbl && ui.tbl[key];
    if (host && reg) host.outerHTML = tradeTable(reg.list, reg.withUnr, key); else render();
  }, true);

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
  .jv-t{font-size:12.5px}.jv-t th{font-size:10.5px;text-transform:uppercase;letter-spacing:.04em;cursor:help;padding:6px 8px;position:sticky;top:0;background:var(--panel)}
  .jv-t td{padding:5px 8px;vertical-align:middle}.jv-t td.num,.jv-t th.num{text-align:right}
  .jv-sym b{display:block;font-size:12.5px;max-width:230px;overflow:hidden;text-overflow:ellipsis}.jv-sym small{display:block;font-size:10.5px;color:var(--text-3,#8a93a6);max-width:230px;overflow:hidden;text-overflow:ellipsis}
  .jv-tag{display:inline-grid;place-items:center;width:16px;height:16px;border-radius:4px;font-size:9.5px;font-weight:800;margin-right:5px;background:color-mix(in srgb,var(--brand,#4f8ef7) 20%,transparent);color:var(--brand,#4f8ef7)}
  .jv-tag.m{background:var(--panel-2,rgba(255,255,255,.06));color:var(--text-3,#8a93a6)}
  .jv-side{display:inline-grid;place-items:center;width:18px;height:18px;border-radius:4px;font-size:10px;font-weight:800}.jv-side.l{background:color-mix(in srgb,var(--up,#22ab94) 18%,transparent);color:var(--up,#22ab94)}.jv-side.s{background:color-mix(in srgb,var(--down,#f7525f) 18%,transparent);color:var(--down,#f7525f)}
  .jv-tg{color:var(--text-2,inherit);font-size:11.5px}
  .jv-pg{display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;padding:8px 12px;border-top:1px solid var(--line);font-size:12px}
  .jv-pgb{display:flex;align-items:center;gap:6px}.jv-pgb button{width:28px;height:28px;border:1px solid var(--line);border-radius:7px;background:var(--panel);color:var(--text);cursor:pointer;font-size:14px}.jv-pgb button:disabled{opacity:.35;cursor:not-allowed}.jv-pgb b{font-variant-numeric:tabular-nums}
  .jv-grid{grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px}.jv-cv{height:120px}
  .jv-exit{height:24px;padding:0 10px;border-radius:6px;border:1px solid color-mix(in srgb,var(--down,#f7525f) 55%,transparent);background:color-mix(in srgb,var(--down,#f7525f) 12%,transparent);color:var(--down,#f7525f);font-size:11.5px;font-weight:700;cursor:pointer}
  .jv-exit:hover{background:var(--down,#f7525f);color:#fff}.jv-exitall{height:26px}
  .jv-hr{display:flex;align-items:center;gap:10px;margin-left:auto}
  .jv-list>div{padding:7px 12px;font-size:12.5px}
  @media (max-width:600px){.jv-kpis{grid-template-columns:repeat(3,1fr)}.jv-kpi b{font-size:13.5px}.jv-search{max-width:none;order:5;flex-basis:100%}.jv-tabs{overflow-x:auto}.jv-more{display:grid;grid-template-columns:1fr 1fr}.jv-more .inp{min-width:0;width:100%}.jv-t .jv-tg,.jv-t th[title^="T1"]{display:none}}
  /* ---- simple trading UI (mobile first) ---- */
  .jq-hero{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:14px 16px;margin:6px 0 12px;text-align:center}
  .jq-hero-top{display:flex;align-items:center;justify-content:space-between;gap:8px;font-size:12.5px;color:var(--text-3,#8a93a6)}
  .jq-reset{height:30px;padding:0 12px;border-radius:15px;border:1px solid var(--line);background:var(--panel-2,transparent);color:var(--text-2,inherit);font-size:12px;font-weight:600;cursor:pointer}
  .jq-reset:hover{border-color:var(--down,#f7525f);color:var(--down,#f7525f)}
  .jq-pl{font-size:34px;font-weight:800;margin:4px 0 10px;font-variant-numeric:tabular-nums;letter-spacing:-.5px}
  .jq-hero-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;text-align:left}
  .jq-hero-grid>div{display:flex;flex-direction:column;gap:2px;min-width:0}
  .jq-hero-grid small{font-size:11px;color:var(--text-3,#8a93a6)}
  .jq-hero-grid b{font-size:14px;font-variant-numeric:tabular-nums;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .jv-tabs button{min-height:40px}
  .jq-cnt{font-style:normal;font-size:11px;font-weight:700;padding:1px 7px;border-radius:9px;margin-left:4px;background:var(--brand-2,rgba(79,142,247,.18));color:var(--brand,#4f8ef7)}
  .jv-tabs button.on .jq-cnt{background:var(--brand,#4f8ef7);color:#fff}
  .jq-card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:12px 14px;margin-bottom:10px;cursor:pointer;display:flex;flex-direction:column;gap:7px}
  .jq-card:hover,.jq-card:focus-visible{border-color:var(--brand,#4f8ef7);outline:none}
  .jq-r1{display:flex;align-items:center;gap:8px;min-width:0}
  .jq-r1>b{font-size:15px;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .jq-pnl{font-size:17px;font-weight:800;font-variant-numeric:tabular-nums;white-space:nowrap}
  .jq-side{font-size:11.5px;font-weight:700;padding:3px 9px;border-radius:6px;white-space:nowrap}
  .jq-side.buy{background:color-mix(in srgb,var(--up,#22ab94) 16%,transparent);color:var(--up,#22ab94)}
  .jq-side.sell{background:color-mix(in srgb,var(--down,#f7525f) 16%,transparent);color:var(--down,#f7525f)}
  .jq-r2{display:flex;align-items:center;justify-content:space-between;gap:8px;font-size:13px;color:var(--text-2,inherit);font-variant-numeric:tabular-nums}
  .jq-r2 i{font-style:normal;color:var(--text-3,#8a93a6);margin:0 2px}.jq-r2 em{color:var(--text-3,#8a93a6);font-size:12px}
  .jq-tag{font-size:10.5px;font-weight:700;padding:2px 8px;border-radius:999px;background:var(--panel-2,rgba(255,255,255,.06));color:var(--text-3,#8a93a6);white-space:nowrap}
  .jq-tag.ok{color:var(--up,#22ab94)}.jq-tag.bad{color:var(--down,#f7525f)}
  .jq-lv{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;font-size:12px;color:var(--text-3,#8a93a6)}
  .jq-lv b{display:block;font-size:13.5px;color:var(--text);font-variant-numeric:tabular-nums}.jq-lv b.up{color:var(--up,#22ab94)}.jq-lv b.down{color:var(--down,#f7525f)}
  .jq-bar{position:relative;height:6px;border-radius:3px;background:linear-gradient(90deg,color-mix(in srgb,var(--down,#f7525f) 55%,transparent),var(--panel-2,rgba(255,255,255,.08)) 45%,var(--panel-2,rgba(255,255,255,.08)) 55%,color-mix(in srgb,var(--up,#22ab94) 55%,transparent))}
  .jq-bar i{position:absolute;top:-3px;width:2px;height:12px;border-radius:1px;transform:translateX(-1px)}.jq-bar .jq-e{background:var(--text-3,#8a93a6)}.jq-bar .jq-m{background:var(--brand,#4f8ef7);width:4px;border-radius:2px}
  .jq-r3{display:flex;align-items:center;justify-content:space-between;gap:8px}.jq-r3 small{color:var(--text-3,#8a93a6);font-size:11.5px}
  .jq-exit{height:36px;min-width:70px;font-size:13px}
  .jq-exall{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}.jq-exall .jv-exitall{height:34px;padding:0 14px}
  .jq-empty{display:flex;flex-direction:column;align-items:center;gap:8px;text-align:center;padding:38px 16px;color:var(--text-3,#8a93a6);background:var(--panel);border:1px dashed var(--line);border-radius:14px}
  .jq-empty b{color:var(--text);font-size:15px}.jq-more{width:100%;height:42px}
  .jq-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:10px}
  .jq-stats>div{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:10px 12px;display:flex;flex-direction:column;gap:3px;min-width:0}
  .jq-stats small{font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--text-3,#8a93a6)}.jq-stats b{font-size:18px;font-variant-numeric:tabular-nums;overflow:hidden;text-overflow:ellipsis}
  .jq-note{background:color-mix(in srgb,var(--warn,#c9922c) 13%,transparent);border-radius:10px;padding:10px 12px;font-size:13px;margin-bottom:10px;line-height:1.5}
  .jq-foot{display:flex;flex-wrap:wrap;gap:8px;margin:4px 0 90px}.jq-foot .btn{height:42px}
  .jq-danger{border-color:color-mix(in srgb,var(--down,#f7525f) 55%,transparent)!important;color:var(--down,#f7525f)!important;background:color-mix(in srgb,var(--down,#f7525f) 10%,transparent)!important}
  .jq-fab{position:fixed;right:16px;bottom:calc(18px + env(safe-area-inset-bottom,0px));width:56px;height:56px;border-radius:50%;border:0;background:var(--brand,#2a78d6);color:#fff;font-size:32px;line-height:1;font-weight:300;box-shadow:0 6px 18px rgba(0,0,0,.35);cursor:pointer;z-index:40;display:grid;place-items:center}
  .jq-fab:active{transform:scale(.94)}
  body.jq-lock{overflow:hidden}
  .jq-sheet-bg{position:fixed;inset:0;z-index:120;background:rgba(5,8,14,.6);display:flex;align-items:flex-end;justify-content:center}
  .jq-sheet{width:100%;max-width:560px;max-height:94vh;max-height:94dvh;background:var(--panel);color:var(--text);border-radius:20px 20px 0 0;display:flex;flex-direction:column;box-shadow:0 -10px 40px rgba(0,0,0,.4)}
  .jq-sheet-h{display:flex;align-items:center;justify-content:space-between;padding:14px 16px 8px;font-size:17px}
  .jq-x{width:40px;height:40px;border-radius:50%;border:0;background:var(--panel-2,transparent);color:var(--text-2,inherit);font-size:16px;cursor:pointer}
  .jq-sheet-b{overflow-y:auto;padding:4px 16px calc(16px + env(safe-area-inset-bottom,0px));-webkit-overflow-scrolling:touch}
  .jq-sheet .inp{height:46px;font-size:16px;width:100%;box-sizing:border-box}
  .jq-f{display:flex;flex-direction:column;gap:5px;font-size:12px;color:var(--text-3,#8a93a6);margin-bottom:10px;min-width:0}
  .jq-lbl{font-size:12px;color:var(--text-3,#8a93a6);margin:2px 0 6px}
  .jq-grid4{display:grid;grid-template-columns:1fr 1fr;gap:0 12px}
  .jq-chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px;align-items:center}
  .jq-chip{height:38px;padding:0 14px;border-radius:19px;border:1px solid var(--line);background:var(--panel-2,transparent);color:var(--text);font-size:13.5px;font-weight:600;cursor:pointer}
  .jq-chip.on,.jq-chip:active{border-color:var(--brand,#4f8ef7);background:var(--brand-2,rgba(79,142,247,.15));color:var(--brand,#4f8ef7)}
  .jq-chip.live{border-style:dashed;color:var(--brand,#4f8ef7)}.jq-live{display:contents}
  .jq-seg2{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px}
  .jq-seg2 button{height:48px;border-radius:12px;border:2px solid var(--line);background:var(--panel-2,transparent);color:var(--text-2,inherit);font-size:16px;font-weight:800;cursor:pointer}
  .jq-seg2 .buy.on{border-color:var(--up,#22ab94);background:color-mix(in srgb,var(--up,#22ab94) 18%,transparent);color:var(--up,#22ab94)}
  .jq-seg2 .sell.on{border-color:var(--down,#f7525f);background:color-mix(in srgb,var(--down,#f7525f) 18%,transparent);color:var(--down,#f7525f)}
  .jq-yn{display:grid;grid-template-columns:1fr 1fr;gap:6px}.jq-yn button{height:46px;border-radius:10px;border:1px solid var(--line);background:var(--panel-2,transparent);color:var(--text-2,inherit);font-size:14px;font-weight:700;cursor:pointer}
  .jq-yn button.on{border-color:var(--brand,#4f8ef7);background:var(--brand-2,rgba(79,142,247,.15));color:var(--brand,#4f8ef7)}
  .jq-calc{margin:4px 0 10px}.jq-calc-g{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}
  .jq-calc-g>div{background:var(--panel-2,rgba(255,255,255,.04));border-radius:10px;padding:8px 10px;min-width:0}.jq-calc-g small{display:block;font-size:10.5px;color:var(--text-3,#8a93a6)}.jq-calc-g b{font-size:14px;font-variant-numeric:tabular-nums}
  .jq-link{border:0;background:none;color:var(--brand,#4f8ef7);font-weight:800;font-size:14px;padding:0;cursor:pointer;text-decoration:underline}
  .jq-more-d{margin:4px 0 12px;border:1px solid var(--line);border-radius:12px;padding:0 12px}.jq-more-d summary{padding:12px 0;font-size:13px;font-weight:600;cursor:pointer;color:var(--text-2,inherit)}.jq-more-d[open] summary{border-bottom:1px solid var(--line);margin-bottom:10px}
  .jq-actions{display:grid;grid-template-columns:1fr 1.6fr;gap:10px;position:sticky;bottom:0;background:var(--panel);padding:10px 0 0}.jq-actions .btn{height:50px;font-size:15px;font-weight:700}
  .jq-go{background:var(--brand,#2a78d6)!important;color:#fff!important}
  .jq-sub{font-size:13px;color:var(--text-2,inherit);line-height:1.5;margin:0 0 12px}
  @media (min-width:700px){.jq-sheet-bg{align-items:center}.jq-sheet{border-radius:20px;max-height:90vh}.jq-fab{right:28px;bottom:28px}.jq-pl{font-size:40px}}
  @media (max-width:430px){.jq-hero-grid{grid-template-columns:repeat(2,1fr)}.jq-stats{grid-template-columns:repeat(2,1fr)}.jq-calc-g{grid-template-columns:repeat(2,1fr)}.jq-pl{font-size:30px}.jq-fab{bottom:calc(76px + env(safe-area-inset-bottom,0px))}}
  .jv{padding-bottom:96px}
  @media (max-width:430px){.jv-tabs button{padding:8px 8px;font-size:12.5px}.jv-tabs button .jq-cnt{margin-left:2px;padding:1px 5px}}
`;
  document.head.appendChild(st);

  setInterval(() => { if (document.getElementById('v-journal') && document.getElementById('v-journal').offsetParent) applyManualTsl(); }, 15000);
  setInterval(() => { if (document.getElementById('v-journal') && document.getElementById('v-journal').offsetParent) syncAuto(true); }, 60000);
  window.JV = { render, sync: syncAuto, trades: () => T, settings: () => S, calc, validate,
    /* live portfolio for the header: capital + booked + open (marked to market) */
    totals: () => { const L = liveTotals(today()); return { capital: S.capital, booked: L.booked, unr: L.unr, eq: L.eq, open: allTrades().filter(t => entered(t) && statusOf(t) !== 'Closed').length }; } };
})();
