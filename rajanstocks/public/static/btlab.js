/* Backtest lab (31 Oct): build your own strategy from rules, backtest it on 4 / 8 years or as far back as the data goes, keep it for the next session.
   Runs entirely in this browser on the app's own daily candles (/api/m/candles). Nothing is sent anywhere and the LIVE auto trader is not touched:
   a strategy saved here is only tested here (and can be "followed" = checked for tomorrow's signals). Option results are an ESTIMATE: historical option prices do not
   exist, so the premium, time decay and expiry calendar come from the same model as the app's backtest (ATR based, delta 0.5, 0.05 % cost). */
(function () {
  'use strict';
  const LS = 'bt-lab-strategies-v1', LSUI = 'bt-lab-run-v1';
  const INDEX = ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY', 'SENSEX'];
  const STOCKS = ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'SBIN', 'BHARTIARTL', 'ITC', 'KOTAKBANK', 'LT', 'AXISBANK', 'BAJFINANCE', 'MARUTI', 'SUNPHARMA', 'TITAN', 'HCLTECH', 'TATASTEEL', 'M&M', 'ADANIENT', 'ONGC'];
  const MARKETS = { idx: 'Index options', sopt: 'Stock options', cash: 'Stocks only' };
  const DELTA = 0.5, MIN_DTE = 3, OPT_COST = 0.0005;
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const inr = (v, d = 0) => '₹' + Number(v).toLocaleString('en-IN', { maximumFractionDigits: d, minimumFractionDigits: d });
  const sinr = v => (v >= 0 ? '+' : '−') + inr(Math.abs(v));
  const f2 = v => Number(v).toLocaleString('en-IN', { maximumFractionDigits: 2, minimumFractionDigits: 2 });
  const load = k => { try { return JSON.parse(localStorage.getItem(k) || 'null'); } catch (e) { return null; } };
  const save = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { } };
  const uid = () => 's' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);

  /* ---------------- rules ---------------- */
  const RULES = {
    ma_rel: { label: 'Price vs moving average', p: [{ k: 'type', s: ['sma', 'ema'], d: 'sma' }, { k: 'n', d: 50, min: 2, max: 400 }, { k: 'rel', s: ['above', 'below'], d: 'above' }], txt: c => `close ${c.rel} ${c.type.toUpperCase()}(${c.n})` },
    ma_cross: { label: 'Moving average cross', p: [{ k: 'type', s: ['ema', 'sma'], d: 'ema' }, { k: 'fast', d: 9, min: 1, max: 200 }, { k: 'slow', d: 21, min: 3, max: 400 }, { k: 'dir', s: ['up', 'down'], d: 'up' }], txt: c => `${c.type.toUpperCase()}(${c.fast}) crosses ${c.dir === 'up' ? 'above' : 'below'} ${c.type.toUpperCase()}(${c.slow})` },
    rsi: { label: 'RSI level', p: [{ k: 'n', d: 14, min: 2, max: 50 }, { k: 'op', s: ['<', '>'], d: '<' }, { k: 'v', d: 30, min: 1, max: 99 }], txt: c => `RSI(${c.n}) ${c.op} ${c.v}` },
    breakout: { label: 'N-day breakout', p: [{ k: 'n', d: 20, min: 1, max: 250 }, { k: 'dir', s: ['high', 'low'], d: 'high' }], txt: c => `close beyond the ${c.n}-day ${c.dir}` },
    gap: { label: 'Opening gap', p: [{ k: 'dir', s: ['up', 'down'], d: 'down' }, { k: 'pct', d: 1, min: 0.1, max: 20, step: 0.1 }], txt: c => `opens ${c.pct}%+ ${c.dir} vs yesterday's close` },
    volume: { label: 'Volume surge', p: [{ k: 'n', d: 20, min: 3, max: 100 }, { k: 'mult', d: 1.5, min: 0.5, max: 10, step: 0.1 }], txt: c => `volume ≥ ${c.mult}× its ${c.n}-day average` },
    candle: { label: 'Candle colour', p: [{ k: 'dir', s: ['green', 'red'], d: 'green' }], txt: c => `${c.dir} candle (close ${c.dir === 'green' ? '>' : '<'} open)` },
    ibs: { label: 'Close position in range (IBS)', p: [{ k: 'op', s: ['<', '>'], d: '<' }, { k: 'v', d: 0.1, min: 0, max: 1, step: 0.05 }], txt: c => `IBS ${c.op} ${c.v} (0 = closed at the low, 1 = at the high)` },
    macd: { label: 'MACD cross', p: [{ k: 'fast', d: 12, min: 2, max: 100 }, { k: 'slow', d: 26, min: 3, max: 200 }, { k: 'sig', d: 9, min: 2, max: 50 }, { k: 'dir', s: ['up', 'down'], d: 'up' }], txt: c => `MACD(${c.fast},${c.slow},${c.sig}) crosses ${c.dir === 'up' ? 'above' : 'below'} its signal line` },
    boll: { label: 'Bollinger band break', p: [{ k: 'n', d: 20, min: 5, max: 100 }, { k: 'k', d: 2, min: 0.5, max: 5, step: 0.1 }, { k: 'dir', s: ['above', 'below'], d: 'below' }], txt: c => `close ${c.dir === 'above' ? 'above the upper' : 'below the lower'} Bollinger band (${c.n}, ${c.k})` },
    roc: { label: 'Price change over N days', p: [{ k: 'n', d: 10, min: 1, max: 250 }, { k: 'op', s: ['>', '<'], d: '>' }, { k: 'pct', d: 5, min: 0.5, max: 100, step: 0.5 }], txt: c => `price change over ${c.n} days ${c.op} ${c.op === '<' ? '-' : '+'}${c.pct}%` },
    supertrend: { label: 'Supertrend', p: [{ k: 'n', d: 10, min: 2, max: 50 }, { k: 'mult', d: 3, min: 0.5, max: 10, step: 0.5 }, { k: 'dir', s: ['up', 'down', 'is up', 'is down'], d: 'up' }], txt: c => `Supertrend(${c.n}, ${c.mult}) ${c.dir.startsWith('is') ? 'is ' + c.dir.slice(3) + ' (green/red state)' : 'flips ' + c.dir}` },
    atrp: { label: 'Volatility (ATR % of price)', p: [{ k: 'n', d: 14, min: 2, max: 50 }, { k: 'op', s: ['>', '<'], d: '>' }, { k: 'v', d: 1.5, min: 0.1, max: 20, step: 0.1 }], txt: c => `ATR(${c.n}) ${c.op} ${c.v}% of price` }
  };
  const LBL = { n: 'Length', v: 'Value', pct: 'Percent', mult: 'Times', op: 'Is', dir: 'Direction', rel: 'Is', fast: 'Fast', slow: 'Slow', type: 'Type', sig: 'Signal length', k: 'Std devs' };
  const newRule = t => { const c = { t }; RULES[t].p.forEach(p => c[p.k] = p.d); return c; };
  const R_ = (t, o) => Object.assign(newRule(t), o || {});
  const TEMPLATES = {
    ema_cross: { desc: 'Rides trends: buys when a fast average crosses above a slow one, sells when it crosses below.', name: 'Trend follower (EMA 9/21 cross)', side: 'both', long: [R_('ma_cross', { dir: 'up' })], short: [R_('ma_cross', { dir: 'down' })], exitIf: [], stop: { type: 'atr', k: 1.5, pct: 2 }, target: { on: false, r: 2 }, trail: { on: true, start: 1, dist: 1.5 }, maxHold: 20 },
    rsi2: { desc: 'Buys a sharp short dip inside a strong uptrend and sells when it bounces (the Larry Connors idea).', name: 'Buy the dip (RSI(2) pullback)', side: 'long', long: [R_('ma_rel', { type: 'sma', n: 200, rel: 'above' }), R_('rsi', { n: 2, op: '<', v: 10 }), R_('ma_rel', { type: 'sma', n: 5, rel: 'below' })], short: [], exitIf: [R_('ma_rel', { type: 'sma', n: 5, rel: 'above' })], stop: { type: 'atr', k: 2.5, pct: 2 }, target: { on: false, r: 2 }, trail: { on: false, start: 1, dist: 1.5 }, maxHold: 10 },
    donchian: { desc: 'Buys when the price breaks its 20-day high, sells when it breaks the 20-day low, and trails the stop.', name: '20-day breakout', side: 'both', long: [R_('breakout', { n: 20, dir: 'high' })], short: [R_('breakout', { n: 20, dir: 'low' })], exitIf: [], stop: { type: 'atr', k: 2, pct: 2 }, target: { on: false, r: 3 }, trail: { on: true, start: 1, dist: 2 }, maxHold: 30 },
    ibs: { desc: 'Buys shares that closed near the bottom of the day and sells when they recover.', name: 'Bounce from weak closes (IBS)', side: 'long', long: [R_('ibs', { op: '<', v: 0.1 })], short: [], exitIf: [R_('ibs', { op: '>', v: 0.9 })], stop: { type: 'atr', k: 2.5, pct: 2 }, target: { on: false, r: 2 }, trail: { on: false, start: 1, dist: 1.5 }, maxHold: 6 },
    supertrend: { desc: 'From a video, daily version: buys when Supertrend turns green above the 200-day average, exits when it turns red.', name: 'Supertrend + 200-day average', side: 'long', long: [R_('supertrend', { n: 10, mult: 3, dir: 'up' }), R_('ma_rel', { type: 'ema', n: 200, rel: 'above' })], short: [], exitIf: [R_('supertrend', { n: 10, mult: 3, dir: 'down' })], stop: { type: 'atr', k: 2, pct: 2 }, target: { on: false, r: 2 }, trail: { on: false, start: 1, dist: 1.5 }, maxHold: 60 },
    must: { desc: 'From a video, daily version: buys when the price climbs back above the 10-day average while Supertrend is green.', name: 'Supertrend pullback (MUST)', side: 'long', long: [R_('supertrend', { n: 10, mult: 3, dir: 'is up' }), R_('ma_cross', { type: 'sma', fast: 1, slow: 10, dir: 'up' })], short: [], exitIf: [R_('ma_rel', { type: 'sma', n: 10, rel: 'below' })], stop: { type: 'atr', k: 2, pct: 2 }, target: { on: false, r: 2 }, trail: { on: false, start: 1, dist: 1.5 }, maxHold: 30 },
    gapdown: { desc: 'Buys a stock that gapped down but turned around and closed green.', name: 'Gap-down bounce', side: 'long', long: [R_('gap', { dir: 'down', pct: 1 }), R_('candle', { dir: 'green' })], short: [], exitIf: [], stop: { type: 'atr', k: 1, pct: 2 }, target: { on: true, r: 2 }, trail: { on: false, start: 1, dist: 1.5 }, maxHold: 5 }
  };
  const blank = () => ({ id: uid(), name: 'My strategy', side: 'long', long: [newRule('ma_rel')], short: [], exitIf: [], stop: { type: 'atr', k: 1.5, pct: 2 }, target: { on: true, r: 2 }, trail: { on: false, start: 1, dist: 1.5 }, maxHold: 10, follow: true, created: Date.now() });
  const clone = o => JSON.parse(JSON.stringify(o));
  const num = (v, lo, hi, d) => { const x = parseFloat(v); return isFinite(x) ? Math.min(hi, Math.max(lo, x)) : d; };
  function cleanRule(c) {                                    // only known rule types, every parameter clamped: an uploaded file can never run code
    if (!c || typeof c !== 'object' || !RULES[c.t]) return null;
    const r = newRule(c.t); RULES[c.t].p.forEach(p => { const v = c[p.k]; r[p.k] = p.s ? (p.s.includes(String(v)) ? String(v) : p.d) : num(v, p.min, p.max, p.d); });
    if (r.t === 'ma_cross' && r.slow <= r.fast) r.slow = r.fast + 1; if (r.t === 'macd' && r.slow <= r.fast) r.slow = r.fast + 1; return r;
  }
  function cleanSpec(o) {
    if (!o || typeof o !== 'object') return { err: 'not a strategy object' };
    const e = blank(); e.name = String(o.name || 'Imported strategy').replace(/[<>]/g, '').slice(0, 60) || 'Imported strategy';
    e.side = ['long', 'short', 'both'].includes(o.side) ? o.side : 'long';
    const rl = a => (Array.isArray(a) ? a : []).slice(0, 8).map(cleanRule).filter(Boolean);
    e.long = rl(o.long); e.short = rl(o.short); e.exitIf = rl(o.exitIf);
    if (e.side !== 'short' && !e.long.length) return { err: '"' + e.name + '": needs at least one valid BUY rule (long)' };
    if (e.side !== 'long' && !e.short.length) return { err: '"' + e.name + '": needs at least one valid SELL rule (short)' };
    const st = o.stop || {}, tg = o.target || {}, tr = o.trail || {};
    e.stop = { type: st.type === 'pct' ? 'pct' : 'atr', k: num(st.k, 0.25, 10, 1.5), pct: num(st.pct, 0.25, 30, 2) };
    e.target = { on: !!tg.on, r: num(tg.r, 0.5, 20, 2) }; e.trail = { on: !!tr.on, start: num(tr.start, 0.5, 10, 1), dist: num(tr.dist, 0.25, 10, 1.5) };
    e.maxHold = Math.round(num(o.maxHold, 1, 120, 10)); e.costPct = num(o.costPct, 0, 2, 0.1); e.follow = false;        // an imported strategy starts STOPPED
    return { spec: e };
  }

  /* ---------------- Markdown / text strategies ---------------- */
  const NUM = '(\\d+(?:\\.\\d+)?)', MA = '(sma|ema)', UP = '(above|over|>|up|higher)', DN = '(below|under|<|down|lower)';
  function parseLine(line) {                          // one bullet in plain words -> one rule (or null when it is not understood)
    const t = line.toLowerCase().replace(/[`*_]/g, '').replace(/\s+/g, ' ').replace(/\bcrosses\b/g, 'crosses').trim();
    let m;
    if ((m = t.match(new RegExp('^' + MA + '\\s*\\(?(\\d+)\\)?\\s+crosses?\\s+' + UP + '\\s+(?:' + MA + ')?\\s*\\(?(\\d+)\\)?')))) return R_('ma_cross', { type: m[1], fast: +m[2], slow: +m[5], dir: 'up' });
    if ((m = t.match(new RegExp('^' + MA + '\\s*\\(?(\\d+)\\)?\\s+crosses?\\s+' + DN + '\\s+(?:' + MA + ')?\\s*\\(?(\\d+)\\)?')))) return R_('ma_cross', { type: m[1], fast: +m[2], slow: +m[5], dir: 'down' });
    if ((m = t.match(new RegExp('^(?:close|price)\\s+(?:crosses?\\s+|closes?\\s+)?' + UP + '\\s+(?:the\\s+)?' + MA + '\\s*\\(?(\\d+)\\)?')))) return R_('ma_rel', { type: m[2], n: +m[3], rel: 'above' });
    if ((m = t.match(new RegExp('^(?:close|price)\\s+(?:crosses?\\s+|closes?\\s+)?' + DN + '\\s+(?:the\\s+)?' + MA + '\\s*\\(?(\\d+)\\)?')))) return R_('ma_rel', { type: m[2], n: +m[3], rel: 'below' });
    if ((m = t.match(new RegExp('^rsi\\s*\\(?(\\d+)?\\)?\\s*(?:is\\s+)?' + DN + '\\s+' + NUM)))) return R_('rsi', { n: +(m[1] || 14), op: '<', v: +m[3] });
    if ((m = t.match(new RegExp('^rsi\\s*\\(?(\\d+)?\\)?\\s*(?:is\\s+)?' + UP + '\\s+' + NUM)))) return R_('rsi', { n: +(m[1] || 14), op: '>', v: +m[3] });
    if ((m = t.match(/(\d+)[- ]?(?:day|candle|bar)s?\s+(?:breakout\s+)?(high|low)/)) || (m = t.match(/(?:break(?:s|out)?|closes?\s+(?:above|below))\s+(?:the\s+)?(?:previous\s+)?(\d+)[- ]?(?:day|candle|bar)\s*(high|low)/))) return R_('breakout', { n: +m[1], dir: m[2] });
    if ((m = t.match(/(?:close|price)s?\s+(?:above|over)\s+(?:the\s+)?(?:previous|yesterday'?s?)\s+high/))) return R_('breakout', { n: 1, dir: 'high' });
    if ((m = t.match(/(?:close|price)s?\s+(?:below|under)\s+(?:the\s+)?(?:previous|yesterday'?s?)\s+low/))) return R_('breakout', { n: 1, dir: 'low' });
    if ((m = t.match(new RegExp('gap\\s+(up|down)\\s+(?:of\\s+)?' + NUM + '\\s*%?')))) return R_('gap', { dir: m[1], pct: +m[2] });
    if ((m = t.match(new RegExp('volume\\s+(?:is\\s+|at least\\s+|>=?\\s*)?' + NUM + '\\s*(?:x|times)')))) return R_('volume', { n: 20, mult: +m[1] });
    if ((m = t.match(/(green|bullish|red|bearish)\s+candle/))) return R_('candle', { dir: /green|bullish/.test(m[1]) ? 'green' : 'red' });
    if ((m = t.match(new RegExp('ibs\\s*(?:is\\s+)?' + DN + '\\s+' + NUM)))) return R_('ibs', { op: '<', v: +m[2] });
    if ((m = t.match(new RegExp('ibs\\s*(?:is\\s+)?' + UP + '\\s+' + NUM)))) return R_('ibs', { op: '>', v: +m[2] });
    if ((m = t.match(new RegExp('atr\\s*\\(?(\\d+)?\\)?\\s*(?:is\\s+)?' + UP + '\\s+' + NUM + '\\s*%')))) return R_('atrp', { n: +(m[1] || 14), op: '>', v: +m[3] });
    if ((m = t.match(new RegExp('atr\\s*\\(?(\\d+)?\\)?\\s*(?:is\\s+)?' + DN + '\\s+' + NUM + '\\s*%')))) return R_('atrp', { n: +(m[1] || 14), op: '<', v: +m[3] });
    if ((m = t.match(/macd\s+crosses?\s+(above|over|up)/))) return R_('macd', { dir: 'up' });
    if ((m = t.match(/macd\s+crosses?\s+(below|under|down)/))) return R_('macd', { dir: 'down' });
    if ((m = t.match(/(?:close|price)\s+(?:closes?\s+)?(above|below)\s+(?:the\s+)?(upper|lower)\s+bollinger/))) return R_('boll', { dir: m[2] === 'upper' ? 'above' : 'below' });
    if ((m = t.match(/supertrend\s+(?:flips?|turns?|changes?\s+to)\s+(?:to\s+)?(up|green|buy|down|red|sell)/))) return R_('supertrend', { dir: /up|green|buy/.test(m[1]) ? 'up' : 'down' });
    if ((m = t.match(/supertrend\s+(?:is\s+)?(green|up|red|down)/))) return R_('supertrend', { dir: /green|up/.test(m[1]) ? 'is up' : 'is down' });
    if ((m = t.match(new RegExp('(?:price|close)\\s+(up|down|rises?|falls?|gains?|drops?)\\s+' + NUM + '\\s*%\\s+(?:in|over)\\s+(\\d+)\\s+days?')))) return R_('roc', { n: +m[3], op: /up|ris|gain/.test(m[1]) ? '>' : '<', pct: +m[2] });
    return null;
  }
  function parseMd(text) {                           // "# Name / Direction / Buy when: - bullets / Stop / Target / Trail / Max days"
    const lines = text.replace(/\r/g, '').split('\n'), out = [], notes = []; let cur = null, sect = null;
    const flush = () => { if (cur) out.push(cur); cur = null; sect = null; };
    const start = name => { flush(); cur = { name: name.trim().slice(0, 60) || 'Imported strategy', side: 'long', long: [], short: [], exitIf: [], stop: { type: 'atr', k: 1.5, pct: 2 }, target: { on: false, r: 2 }, trail: { on: false, start: 1, dist: 1.5 }, maxHold: 10, _bad: [] }; };
    lines.forEach(raw => {
      const l = raw.trim(); if (!l) return; let m;
      if ((m = l.match(/^#{1,3}\s+(.+)/))) { start(m[1]); return; }
      if (!cur) start('Imported strategy');
      if ((m = l.match(/^(?:direction|side)\s*[:=]\s*(.+)/i))) { const v = m[1].toLowerCase(); cur.side = /both/.test(v) ? 'both' : /sell|short|put/.test(v) ? 'short' : 'long'; return; }
      if ((m = l.match(/^(?:buy|long|enter long|entry)\s*(?:when|if)?\s*:?\s*$/i)) || (m = l.match(/^buy when\s*:?$/i))) { sect = 'long'; return; }
      if ((m = l.match(/^(?:sell|short|enter short)\s*(?:when|if)?\s*:?\s*$/i))) { sect = 'short'; if (cur.side === 'long') cur.side = 'both'; return; }
      if ((m = l.match(/^exit\s*(?:when|if|at the close when)?\s*:?\s*$/i))) { sect = 'exitIf'; return; }
      if ((m = l.match(/^stop(?:[- ]?loss)?\s*[:=]\s*(.+)/i))) { const v = m[1].toLowerCase(), a = v.match(/(\d+(?:\.\d+)?)\s*(?:x\s*)?atr/), p = v.match(/(\d+(?:\.\d+)?)\s*%/); if (a) cur.stop = { type: 'atr', k: +a[1], pct: 2 }; else if (p) cur.stop = { type: 'pct', k: 1.5, pct: +p[1] }; else cur._bad.push('stop: ' + m[1]); return; }
      if ((m = l.match(/^target\s*[:=]\s*(.+)/i))) { const v = m[1].toLowerCase(), r = v.match(/(\d+(?:\.\d+)?)\s*r\b/) || v.match(/1\s*:\s*(\d+(?:\.\d+)?)/); cur.target = /none|no\b|off/.test(v) ? { on: false, r: 2 } : r ? { on: true, r: +r[1] } : (cur._bad.push('target: ' + m[1]), cur.target); return; }
      if ((m = l.match(/^trail(?:ing)?(?:\s*stop)?\s*[:=]\s*(.+)/i))) { const v = m[1].toLowerCase(), a = v.match(/after\s*\+?(\d+(?:\.\d+)?)\s*r.*?(\d+(?:\.\d+)?)\s*r/); cur.trail = /none|no\b|off/.test(v) ? { on: false, start: 1, dist: 1.5 } : a ? { on: true, start: +a[1], dist: +a[2] } : (cur._bad.push('trail: ' + m[1]), cur.trail); return; }
      if ((m = l.match(/^(?:max(?:imum)?\s*(?:days|sessions|hold)|hold)\s*[:=]\s*(\d+)/i))) { cur.maxHold = +m[1]; return; }
      if ((m = l.match(/^[-*+]\s+(.+)/)) && sect) { const r = parseLine(m[1]); if (r) cur[sect].push(r); else cur._bad.push(m[1]); return; }
      if (/^```/.test(l)) return;
    });
    flush(); return { out, notes };
  }
  function fencedJson(text) { const res = [], re = /```(?:json)?\s*\n([\s\S]*?)```/gi; let m; while ((m = re.exec(text))) { try { res.push(JSON.parse(m[1])); } catch (e) { } } return res; }
  const INTRADAY = /\b(\d+\s?m\b|1h\b|4h\b|scalp|renko|tick|intraday|1m|5m|15m)/i;
  function importText(text) {
    const ok = [], bad = [], notes = []; let items = [];
    const trimmed = text.trim();
    if (/^[\[{]/.test(trimmed)) {                                                       // a JSON file
      let j; try { j = JSON.parse(trimmed); } catch (err) { return 'That is not valid JSON (' + String(err.message).slice(0, 60) + ').'; }
      items = Array.isArray(j) ? j : Array.isArray(j && j.strategies) ? j.strategies : [j];
      const cat = items.filter(o => o && typeof o === 'object' && typeof o.rules === 'string' && !o.long && !o.short);     // a catalogue with the rules written as sentences
      if (cat.length) notes.push(cat.length + ' entr' + (cat.length > 1 ? 'ies are' : 'y is') + ' written as plain sentences: the lab reads only lines it understands, and only for daily candles. Entries for minute / hourly charts or ideas like order blocks, fair value gaps or liquidity sweeps cannot be tested here and are skipped.');
      items = items.map(o => {
        if (!(o && typeof o === 'object' && typeof o.rules === 'string' && !o.long && !o.short)) return o;
        if (INTRADAY.test(String(o.tf || ''))) { bad.push('"' + String(o.name || o.id).slice(0, 40) + '": needs ' + o.tf + ' data (the lab tests daily candles)'); return null; }
        const fake = '# ' + (o.name || o.id) + '\nBuy when:\n' + String(o.rules).split(/[.;]\s+/).map(x => '- ' + x).join('\n'), r = parseMd(fake).out[0];
        if (!r || !r.long.length) { bad.push('"' + String(o.name || o.id).slice(0, 40) + '": the rules are not something the lab can express (' + (o.rules.length > 60 ? o.rules.slice(0, 57) + '…' : o.rules) + ')'); return null; }
        return r;
      }).filter(Boolean);
    } else {                                                                              // Markdown / text
      const blocks = fencedJson(text);
      if (blocks.length) blocks.forEach(b => { (Array.isArray(b) ? b : Array.isArray(b && b.strategies) ? b.strategies : [b]).forEach(o => items.push(o)); });
      else {
        const p = parseMd(text); items = p.out;
        items.forEach(o => { notes.push('"' + o.name + '" read as: ' + describe(Object.assign({ stop: o.stop, target: o.target, trail: o.trail, exitIf: o.exitIf, maxHold: o.maxHold }, { side: o.side, long: o.long, short: o.short })) + (o._bad && o._bad.length ? ' | NOT understood and left out: ' + o._bad.slice(0, 4).join(' / ') : '')); });
        if (!items.length) return 'No strategy found in that text. Use a heading, then "Buy when:" with bullet lines (see the help below).';
      }
    }
    items.slice(0, 20).forEach(o => { const r = cleanSpec(o); if (r.spec) ok.push(r.spec); else bad.push(r.err); });
    ok.forEach(sp => { let nm = sp.name, k = 2; while (S.list.some(x => x.name === nm)) nm = sp.name + ' (' + (k++) + ')'; sp.name = nm; S.list.push(sp); S.run.sid = sp.id; });
    persist(); return (ok.length ? 'Imported ' + ok.length + ' strateg' + (ok.length > 1 ? 'ies' : 'y') + ': ' + ok.map(x => '"' + x.name + '"').join(', ') + '. They are STOPPED until you press Start. Check each one before you trust the result. ' : '') + notes.join(' ') + (bad.length ? ' Skipped (' + bad.length + '): ' + bad.join('; ') + '.' : '');
  }
  const EXAMPLE = { name: 'Example: EMA cross with trailing stop', side: 'both', long: [{ t: 'ma_cross', type: 'ema', fast: 9, slow: 21, dir: 'up' }], short: [{ t: 'ma_cross', type: 'ema', fast: 9, slow: 21, dir: 'down' }], exitIf: [], stop: { type: 'atr', k: 1.5 }, target: { on: false, r: 2 }, trail: { on: true, start: 1, dist: 1.5 }, maxHold: 20 };
  const describe = sp => {
    const part = (l) => l.length ? l.map(c => RULES[c.t].txt(c)).join(' AND ') : '—';
    const out = [];
    if (sp.side !== 'short') out.push('BUY when ' + part(sp.long));
    if (sp.side !== 'long') out.push('SELL when ' + part(sp.short));
    out.push('stop ' + (sp.stop.type === 'atr' ? sp.stop.k + '×ATR' : sp.stop.pct + '%') + (sp.target.on ? ' · target ' + sp.target.r + 'R' : '') + (sp.trail.on ? ` · trail after +${sp.trail.start}R at ${sp.trail.dist}R` : '') + (sp.exitIf && sp.exitIf.length ? ' · exit when ' + part(sp.exitIf) : '') + ` · max ${sp.maxHold} sessions`);
    return out.join(' · ');
  };

  /* ---------------- data ---------------- */
  const BARS = {};                                   // symbol -> {d:[iso], o,h,l,c,v}
  const iso = t => new Date(t + 19800000).toISOString().slice(0, 10);
  const dnum = s => Math.floor(Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, +s.slice(8, 10)) / 864e5);
  async function fetchBars(sym) {
    if (BARS[sym]) return BARS[sym];
    const to = iso(Date.now()), r = await fetch(`/api/m/candles?symbol=${encodeURIComponent(sym)}&tf=1D&from=2005-01-01&to=${to}`, { cache: 'no-cache' });
    if (!r.ok) throw new Error(sym + ' ' + r.status);
    const j = await r.json(), b = (j.bars || []).filter(x => x && x.c > 0 && x.h >= x.l);
    if (b.length < 60) throw new Error(sym + ': only ' + b.length + ' candles');
    return BARS[sym] = { d: b.map(x => iso(x.t)), o: b.map(x => x.o), h: b.map(x => x.h), l: b.map(x => x.l), c: b.map(x => x.c), v: b.map(x => x.v || 0) };
  }

  function supertrend(B, atr, m) {
    const n = B.c.length, dir = new Array(n).fill(0); let fu = NaN, fl = NaN, d = 1;
    for (let i = 1; i < n; i++) {
      if (!(atr[i] === atr[i])) continue; const hl2 = (B.h[i] + B.l[i]) / 2, bu = hl2 + m * atr[i], bl = hl2 - m * atr[i], pfu = fu, pfl = fl;
      fu = (!(pfu === pfu) || bu < pfu || B.c[i - 1] > pfu) ? bu : pfu; fl = (!(pfl === pfl) || bl > pfl || B.c[i - 1] < pfl) ? bl : pfl;
      if (pfu === pfu) { if (d === -1 && B.c[i] > fu) d = 1; else if (d === 1 && B.c[i] < fl) d = -1; } dir[i] = d;
    }
    return dir;
  }
  const emaRaw = (a, k) => { const o = new Array(a.length).fill(NaN), m = 2 / (k + 1); let e = NaN; for (let i = 0; i < a.length; i++) { if (!(a[i] === a[i])) continue; e = e === e ? a[i] * m + e * (1 - m) : a[i]; o[i] = e; } return o; };
  /* ---------------- indicators (memoised per symbol) ---------------- */
  function ctxOf(B) {
    const memo = {}, n = B.c.length;
    const get = (key, fn) => memo[key] || (memo[key] = fn());
    const sma = (a, k) => { const o = new Array(n).fill(NaN); let s = 0; for (let i = 0; i < n; i++) { s += a[i]; if (i >= k) s -= a[i - k]; if (i >= k - 1) o[i] = s / k; } return o; };
    const ema = (a, k) => { const o = new Array(n).fill(NaN), m = 2 / (k + 1); let e = NaN; for (let i = 0; i < n; i++) { e = i === 0 ? a[0] : a[i] * m + e * (1 - m); o[i] = i >= k - 1 ? e : NaN; } return o; };
    const rma = (a, k) => { const o = new Array(n).fill(NaN); let s = 0; for (let i = 0; i < n; i++) { if (i < k) { s += a[i]; if (i === k - 1) o[i] = s / k; } else o[i] = (o[i - 1] * (k - 1) + a[i]) / k; } return o; };
    return {
      n, B, memo: get,
      ma: (type, k) => get(type + k, () => (type === 'ema' ? ema : sma)(B.c, k)),
      rsi: k => get('rsi' + k, () => { const o = new Array(n).fill(NaN); let g = 0, l = 0; for (let i = 1; i < n; i++) { const ch = B.c[i] - B.c[i - 1], u = Math.max(ch, 0), dn = Math.max(-ch, 0); if (i <= k) { g += u / k; l += dn / k; } else { g = (g * (k - 1) + u) / k; l = (l * (k - 1) + dn) / k; } if (i >= k) o[i] = l === 0 ? 100 : 100 - 100 / (1 + g / l); } return o; }),
      atr: k => get('atr' + k, () => { const tr = B.c.map((c, i) => i === 0 ? B.h[0] - B.l[0] : Math.max(B.h[i] - B.l[i], Math.abs(B.h[i] - B.c[i - 1]), Math.abs(B.l[i] - B.c[i - 1]))); return rma(tr, k); }),
      hh: k => get('hh' + k, () => { const o = new Array(n).fill(NaN); for (let i = k; i < n; i++) { let m = -Infinity; for (let j = i - k; j < i; j++) m = Math.max(m, B.h[j]); o[i] = m; } return o; }),
      ll: k => get('ll' + k, () => { const o = new Array(n).fill(NaN); for (let i = k; i < n; i++) { let m = Infinity; for (let j = i - k; j < i; j++) m = Math.min(m, B.l[j]); o[i] = m; } return o; }),
      vavg: k => get('v' + k, () => { const o = new Array(n).fill(NaN); let s = 0; for (let i = 0; i < n; i++) { s += B.v[i]; if (i >= k) s -= B.v[i - k]; if (i >= k) o[i] = s / k; } return o; })
    };
  }
  function test(c, X, i) {                          // does rule c hold on bar i (using only data up to i)?
    const B = X.B;
    switch (c.t) {
      case 'ma_rel': { const m = X.ma(c.type, c.n)[i]; return m === m && (c.rel === 'above' ? B.c[i] > m : B.c[i] < m); }
      case 'ma_cross': { const a = X.ma(c.type, c.fast), b = X.ma(c.type, c.slow); if (i < 1 || !(a[i] === a[i]) || !(b[i] === b[i]) || !(a[i - 1] === a[i - 1]) || !(b[i - 1] === b[i - 1])) return false; return c.dir === 'up' ? (a[i - 1] <= b[i - 1] && a[i] > b[i]) : (a[i - 1] >= b[i - 1] && a[i] < b[i]); }
      case 'rsi': { const r = X.rsi(c.n)[i]; return r === r && (c.op === '<' ? r < c.v : r > c.v); }
      case 'breakout': { if (c.dir === 'high') { const h = X.hh(c.n)[i]; return h === h && B.c[i] > h; } const l = X.ll(c.n)[i]; return l === l && B.c[i] < l; }
      case 'gap': { if (i < 1) return false; const g = (B.o[i] - B.c[i - 1]) / B.c[i - 1] * 100; return c.dir === 'up' ? g >= c.pct : g <= -c.pct; }
      case 'volume': { const a = X.vavg(c.n)[i]; return a === a && a > 0 && B.v[i] >= c.mult * a; }
      case 'candle': return c.dir === 'green' ? B.c[i] > B.o[i] : B.c[i] < B.o[i];
      case 'ibs': { const r = B.h[i] - B.l[i]; if (!(r > 0)) return false; const v = (B.c[i] - B.l[i]) / r; return c.op === '<' ? v < c.v : v > c.v; }
      case 'macd': { const k = c.fast + '_' + c.slow + '_' + c.sig, M = X.memo('macd' + k, () => { const m = emaRaw(B.c, c.fast).map((v, j) => v - emaRaw(B.c, c.slow)[j]); return { m, g: emaRaw(m, c.sig) }; });
        if (i < c.slow + c.sig || i < 1) return false; const a = M.m[i], b = M.g[i], a0 = M.m[i - 1], b0 = M.g[i - 1]; return c.dir === 'up' ? (a0 <= b0 && a > b) : (a0 >= b0 && a < b); }
      case 'boll': { const sd = X.memo('sd' + c.n, () => { const o = new Array(X.n).fill(NaN); for (let j = c.n - 1; j < X.n; j++) { let s = 0, q = 0; for (let t = j - c.n + 1; t <= j; t++) { s += B.c[t]; q += B.c[t] * B.c[t]; } const mu = s / c.n; o[j] = Math.sqrt(Math.max(0, q / c.n - mu * mu)); } return o; }), mu = X.ma('sma', c.n)[i];
        if (!(sd[i] === sd[i]) || !(mu === mu)) return false; return c.dir === 'above' ? B.c[i] > mu + c.k * sd[i] : B.c[i] < mu - c.k * sd[i]; }
      case 'roc': { if (i < c.n) return false; const v = (B.c[i] / B.c[i - c.n] - 1) * 100; return c.op === '>' ? v >= c.pct : v <= -c.pct; }
      case 'supertrend': { const d = X.memo('st' + c.n + '_' + c.mult, () => supertrend(B, X.atr(c.n), c.mult)); if (i < 2 || !d[i] || !d[i - 1]) return false; if (c.dir === 'is up') return d[i] === 1; if (c.dir === 'is down') return d[i] === -1; return c.dir === 'up' ? (d[i] === 1 && d[i - 1] === -1) : (d[i] === -1 && d[i - 1] === 1); }
      case 'atrp': { const a = X.atr(c.n)[i]; if (!(a === a)) return false; const v = a / B.c[i] * 100; return c.op === '>' ? v > c.v : v < c.v; }
    }
    return false;
  }
  const allOf = (rules, X, i) => rules.length > 0 && rules.every(c => test(c, X, i));

  /* ---------------- option model (same as backtest.py) ---------------- */
  const estPrem = (atr, kind, days) => 0.32 * atr * Math.sqrt(Math.max(0, days == null ? (kind === 'index' ? 5 : 15) : days) * 5 / 7);
  const thetaR = (atr, kind, risk, dFrom, dTo) => (estPrem(atr, kind, dFrom) - estPrem(atr, kind, dTo)) / DELTA / risk;
  function lastWd(y, m, w) { const d = new Date(Date.UTC(y, m + 1, 0)); while (d.getUTCDay() !== w) d.setUTCDate(d.getUTCDate() - 1); return Math.floor(d / 864e5); }
  function expiryDay(isoDay, kind) {                // the contract the live trader would buy: nearest expiry at least 3 days away
    const d0 = dnum(isoDay);
    if (kind === 'index' && isoDay >= '2019-02-11') { const w = isoDay < '2025-09-01' ? 4 : 2; let e = d0 + ((w - new Date(d0 * 864e5).getUTCDay() + 7) % 7); while (e - d0 < MIN_DTE) e += 7; return e; }
    let y = +isoDay.slice(0, 4), m = +isoDay.slice(5, 7) - 1;
    for (let k = 0; k < 6; k++) { const end = new Date(Date.UTC(y, m + 1, 0)).toISOString().slice(0, 10), e = lastWd(y, m, end < '2025-09-01' ? 4 : 2); if (e - d0 >= MIN_DTE) return e; m++; if (m > 11) { m = 0; y++; } }
    return d0 + 30;
  }

  /* ---------------- one trade ---------------- */
  function trade(X, sp, i, side, mode, kind) {
    const B = X.B, n = X.n, atrA = X.atr(14), a = atrA[i];
    if (i + 1 >= n || !(a > 0)) return null;
    const d = side === 'long' ? 1 : -1, entry = B.o[i + 1], opt = mode !== 'cash';
    const risk = sp.stop.type === 'atr' ? sp.stop.k * a : entry * sp.stop.pct / 100;
    if (!(risk > 0) || !(entry > 0)) return null;
    const exp = opt ? expiryDay(B.d[i + 1], kind) : 0, dte = (j, fr) => exp - dnum(B.d[j]) + fr, dEntry = opt ? dte(i + 1, 0.26) : 0;
    const prem0 = opt ? estPrem(a, kind, dEntry) : 0, maxLossR = opt ? prem0 / (DELTA * risk) : Infinity;
    const costR = (opt ? OPT_COST : (sp.costPct == null ? 0.1 : sp.costPct) / 100) * entry / risk;
    let stop = entry - d * risk, best = entry, trailed = false;
    const tgt = sp.target.on ? entry + d * sp.target.r * risk : null, last = Math.min(n - 1, i + sp.maxHold);
    const fin = (px, j, why, when) => {
      let r = d * (px - entry) / risk - costR;
      if (opt) { r -= thetaR(a, kind, risk, dEntry, dte(j, { open: 0.26, mid: 0.13, close: 0 }[when || 'mid'])); r = Math.max(r, -maxLossR); }
      return { i, j, side, entry, exit: px, R: r, why, entryDate: B.d[i + 1], exitDate: B.d[j], hold: j - i, riskPct: risk / entry * 100, premPct: opt && prem0 > 0 ? 100 * DELTA * risk / prem0 : null };
    };
    for (let j = i + 1; j <= last; j++) {
      const gapped = j > i + 1 && (d > 0 ? B.o[j] <= stop : B.o[j] >= stop);
      if (gapped) return fin(B.o[j], j, trailed ? 'TSL' : 'SL', 'open');
      if (d > 0 ? B.l[j] <= stop : B.h[j] >= stop) return fin(stop, j, trailed ? 'TSL' : 'SL');
      if (tgt != null && (d > 0 ? B.h[j] >= tgt : B.l[j] <= tgt)) return fin(tgt, j, 'T');
      best = d > 0 ? Math.max(best, B.h[j]) : Math.min(best, B.l[j]);
      if (sp.trail.on && d * (best - entry) / risk >= sp.trail.start) {
        const t = d > 0 ? Math.max(entry, best - sp.trail.dist * risk) : Math.min(entry, best + sp.trail.dist * risk);
        if (d > 0 ? t > stop : t < stop) { stop = t; trailed = true; }
      }
      if (opt && dte(j, 0) <= 1) return fin(B.c[j], j, 'EXP', 'close');
      if (sp.exitIf && sp.exitIf.length && allOf(sp.exitIf, X, j)) return fin(B.c[j], j, 'RULE', 'close');
    }
    if (last === n - 1 && last < i + sp.maxHold) return null;     // still open at the end of the data
    return fin(B.c[last], last, 'TIME', 'close');
  }

  function runSymbol(sym, sp, kindOf, modes, fromDate) {
    const B = BARS[sym], X = ctxOf(B), n = X.n, kind = INDEX.includes(sym) ? 'index' : 'stock';
    let from = 0; while (from < n && B.d[from] < fromDate) from++;
    const sigL = sp.side !== 'short' ? new Array(n).fill(false) : null, sigS = sp.side !== 'long' ? new Array(n).fill(false) : null;
    for (let i = Math.max(1, from); i < n - 1; i++) { if (sigL) sigL[i] = allOf(sp.long, X, i); if (sigS) sigS[i] = allOf(sp.short, X, i); }
    const out = {};
    modes.forEach(mode => {
      const list = out[mode] = []; let busy = -1;
      for (let i = Math.max(1, from); i < n - 1; i++) {
        if (i <= busy) continue;
        const L = sigL && sigL[i], S = sigS && sigS[i]; if (L === S) continue;       // none, or both = no view
        const t = trade(X, sp, i, L ? 'long' : 'short', mode, kind); if (!t) continue;
        t.sym = sym; busy = t.j; list.push(t);
      }
    });
    return out;
  }

  function limitOpen(ts, maxOpen) {                  // a real account cannot run unlimited trades at once: later signals are skipped while maxOpen are open
    if (!(maxOpen > 0)) return ts;
    const sorted = ts.slice().sort((a, b) => a.entryDate < b.entryDate ? -1 : a.entryDate > b.entryDate ? 1 : (a.sym < b.sym ? -1 : 1)), out = []; let open = [];
    sorted.forEach(t => { const e = dnum(t.entryDate); open = open.filter(x => x > e); if (open.length < maxOpen) { out.push(t); open.push(dnum(t.exitDate)); } });
    return out;
  }
  /* ---------------- statistics ---------------- */
  function stats(ts, cap, riskPct, yearsSel) {
    const per = cap * riskPct / 100, n = ts.length;
    if (!n) return { n: 0, per };
    const sorted = ts.slice().sort((a, b) => a.exitDate < b.exitDate ? -1 : a.exitDate > b.exitDate ? 1 : 0);
    const w = sorted.filter(t => t.R > 0), l = sorted.filter(t => t.R <= 0), sw = w.reduce((p, t) => p + t.R, 0), sl = -l.reduce((p, t) => p + t.R, 0), sumR = sw - sl;
    let cum = 0, pk = 0, dd = 0; const curve = [[sorted[0].exitDate, 0]];
    sorted.forEach(t => { cum += t.R * per; pk = Math.max(pk, cum); dd = Math.max(dd, pk - cum); curve.push([t.exitDate, cum]); });
    const first = sorted.reduce((m, t) => t.entryDate < m ? t.entryDate : m, '9999'), lastD = sorted[n - 1].exitDate, yrs = Math.max(0.25, (dnum(lastD) - dnum(first)) / 365.25);
    const yr = {}; sorted.forEach(t => { const y = t.exitDate.slice(0, 4), o = yr[y] || (yr[y] = { n: 0, w: 0, net: 0 }); o.n++; o.w += t.R > 0 ? 1 : 0; o.net += t.R * per; });
    const ev = []; sorted.forEach(t => { ev.push([dnum(t.entryDate), 1]); ev.push([dnum(t.exitDate), -1]); }); ev.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    let open = 0, peakOpen = 0; ev.forEach(e => { open += e[1]; peakOpen = Math.max(peakOpen, open); });
    const cnt = k => ts.filter(t => t.why === k).length;
    return { n, per, wins: w.length, losses: l.length, winPct: 100 * w.length / n, stopPct: 100 * (cnt('SL')) / n, tgtPct: 100 * cnt('T') / n, trailPct: 100 * cnt('TSL') / n, timePct: 100 * (cnt('TIME') + cnt('EXP') + cnt('RULE')) / n,
      avgWin: w.length ? sw / w.length : 0, avgLoss: l.length ? -sl / l.length : 0, exp: sumR / n, pf: sl > 0 ? sw / sl : (sw > 0 ? Infinity : 0), sumR, net: sumR * per, ret: sumR * per / cap * 100, dd, ddPct: dd / cap * 100, yrs, perYear: sumR * per / cap * 100 / yrs,
      first, last: lastD, yr, curve, peakOpen, sorted, medPrem: (() => { const a = ts.map(t => t.premPct).filter(x => x != null).sort((p, q) => p - q); return a.length ? a[a.length >> 1] : null; })() };
  }

  /* ---------------- state + persistence ---------------- */
  const D = load(LSUI) || {};
  const S = { el: null, list: load(LS) || [], edit: null, run: Object.assign({ years: 4, markets: { idx: true, sopt: true, cash: true }, capital: 100000, riskPct: 1, maxOpen: 5, extra: '', sid: null }, D),
    res: null, busy: false, prog: '', msg: '', pg: {}, flt: {}, tab: 'idx', sig: null, openId: null };
  const persist = () => { save(LS, S.list); save(LSUI, { years: S.run.years, markets: S.run.markets, capital: S.run.capital, riskPct: S.run.riskPct, maxOpen: S.run.maxOpen, extra: S.run.extra, sid: S.run.sid }); };

  /* ---------------- run ---------------- */
  async function runBacktest() {
    const sp = specOf(S.run.sid); if (!sp) { S.msg = 'Pick a strategy first.'; paint(); return; }
    const mk = S.run.markets; if (!mk.idx && !mk.sopt && !mk.cash) { S.msg = 'Tick at least one market.'; paint(); return; }
    const extra = String(S.run.extra || '').split(/[,\s]+/).map(x => x.trim().toUpperCase()).filter(Boolean);
    const idxSyms = mk.idx ? INDEX : [], stkSyms = (mk.sopt || mk.cash) ? STOCKS.concat(extra.filter(x => !STOCKS.includes(x) && !INDEX.includes(x))) : [];
    const all = idxSyms.concat(stkSyms), t0 = performance.now(), failed = [];
    S.busy = true; S.msg = ''; S.res = null; paint();
    let done = 0; const queue = all.slice();
    const worker = async () => { while (queue.length) { const s = queue.shift(); try { await fetchBars(s); } catch (e) { failed.push(s); } done++; S.prog = `Loading price history… ${done} / ${all.length}`; paintProg(); } };
    await Promise.all([worker(), worker(), worker(), worker()]);
    S.prog = 'Running the strategy…'; paintProg(); await new Promise(r => setTimeout(r, 30));
    const lastDate = BARS.NIFTY ? BARS.NIFTY.d[BARS.NIFTY.d.length - 1] : iso(Date.now());
    const cutoff = S.run.years === 'max' ? '0000-00-00' : iso(Date.UTC(+lastDate.slice(0, 4) - S.run.years, +lastDate.slice(5, 7) - 1, +lastDate.slice(8, 10)));
    const T = { idx: [], sopt: [], cash: [] }, span = { idx: null, stk: null };
    const span2 = (k, sym) => { const B = BARS[sym], a = B.d[0], z = B.d[B.d.length - 1], o = span[k] || (span[k] = { first: a, last: z, syms: 0, earliest: a }); o.syms++; if (a < o.first) o.first = a; if (a > o.earliest) o.earliest = a; };
    idxSyms.filter(s => BARS[s]).forEach(s => { span2('idx', s); T.idx.push(...runSymbol(s, sp, null, ['idx'], cutoff).idx); });
    stkSyms.filter(s => BARS[s]).forEach(s => { span2('stk', s); const o = runSymbol(s, sp, null, [mk.sopt ? 'sopt' : null, mk.cash ? 'cash' : null].filter(Boolean), cutoff); if (o.sopt) T.sopt.push(...o.sopt); if (o.cash) T.cash.push(...o.cash); });
    const raw = { idx: T.idx.length, sopt: T.sopt.length, cash: T.cash.length };
    Object.keys(T).forEach(k => { T[k] = limitOpen(T[k], S.run.maxOpen); });
    S.res = { raw, maxOpen: S.run.maxOpen, sid: sp.id, name: sp.name, years: S.run.years, cutoff, lastDate, span, failed, secs: (performance.now() - t0) / 1000, T, cap: S.run.capital, riskPct: S.run.riskPct,
      st: Object.fromEntries(Object.keys(T).map(k => [k, stats(T[k], S.run.capital, S.run.riskPct)])) };
    S.pg = {}; S.flt = {}; S.tab = mk.idx ? 'idx' : mk.sopt ? 'sopt' : 'cash'; S.busy = false; S.prog = ''; persist(); paint();
  }

  async function checkSignals() {
    const fol = S.list.filter(x => x.follow); if (!fol.length) { S.msg = 'No strategy is started (following). Press Start on a strategy first.'; paint(); return; }
    S.busy = true; S.msg = ''; paint();
    const all = INDEX.concat(STOCKS); let done = 0; const queue = all.slice();
    const worker = async () => { while (queue.length) { const s = queue.shift(); try { await fetchBars(s); } catch (e) { } done++; S.prog = `Loading price history… ${done} / ${all.length}`; paintProg(); } };
    await Promise.all([worker(), worker(), worker(), worker()]);
    const rows = [];
    fol.forEach(sp => all.filter(s => BARS[s]).forEach(s => {
      const B = BARS[s], X = ctxOf(B), i = X.n - 1, a = X.atr(14)[i]; if (!(a > 0)) return;
      const L = sp.side !== 'short' && allOf(sp.long, X, i), Sh = sp.side !== 'long' && allOf(sp.short, X, i); if (L === Sh) return;
      const d = L ? 1 : -1, px = B.c[i], risk = sp.stop.type === 'atr' ? sp.stop.k * a : px * sp.stop.pct / 100;
      rows.push({ name: sp.name, sym: s, side: L ? 'BUY' : 'SELL', date: B.d[i], px, stop: px - d * risk, tgt: sp.target.on ? px + d * sp.target.r * risk : null, kind: INDEX.includes(s) ? 'Index' : 'Stock' });
    }));
    S.sig = { rows, at: BARS.NIFTY ? BARS.NIFTY.d[BARS.NIFTY.d.length - 1] : '', n: fol.length }; S.busy = false; S.prog = ''; paint();
  }

  /* ---------------- UI (simple: 1 pick a strategy, 2 pick the period and markets, 3 test) ---------------- */
  const SIMPLE = [
    { g: 'Trend', l: 'Price is above the 200-day average', mk: () => R_('ma_rel', { type: 'sma', n: 200, rel: 'above' }) },
    { g: 'Trend', l: 'Price is below the 200-day average', mk: () => R_('ma_rel', { type: 'sma', n: 200, rel: 'below' }) },
    { g: 'Trend', l: 'Price is above the 50-day average', mk: () => R_('ma_rel', { type: 'sma', n: 50, rel: 'above' }) },
    { g: 'Trend', l: 'Fast average (9) crosses above slow average (21)', mk: () => R_('ma_cross', { type: 'ema', fast: 9, slow: 21, dir: 'up' }) },
    { g: 'Trend', l: 'Fast average (9) crosses below slow average (21)', mk: () => R_('ma_cross', { type: 'ema', fast: 9, slow: 21, dir: 'down' }) },
    { g: 'Trend', l: 'Supertrend turns green (up)', mk: () => R_('supertrend', { n: 10, mult: 3, dir: 'up' }) },
    { g: 'Trend', l: 'Supertrend turns red (down)', mk: () => R_('supertrend', { n: 10, mult: 3, dir: 'down' }) },
    { g: 'Dips and bounces', l: 'RSI is low: the stock is oversold (below 30)', mk: () => R_('rsi', { n: 14, op: '<', v: 30 }) },
    { g: 'Dips and bounces', l: 'RSI is high: the stock is overbought (above 70)', mk: () => R_('rsi', { n: 14, op: '>', v: 70 }) },
    { g: 'Dips and bounces', l: 'Sharp short-term dip: RSI(2) below 10', mk: () => R_('rsi', { n: 2, op: '<', v: 10 }) },
    { g: 'Dips and bounces', l: 'Closed near the bottom of the day (IBS below 0.1)', mk: () => R_('ibs', { op: '<', v: 0.1 }) },
    { g: 'Dips and bounces', l: 'Price falls below the lower Bollinger band', mk: () => R_('boll', { n: 20, k: 2, dir: 'below' }) },
    { g: 'Breakouts and gaps', l: 'Price breaks above the 20-day high', mk: () => R_('breakout', { n: 20, dir: 'high' }) },
    { g: 'Breakouts and gaps', l: 'Price breaks below the 20-day low', mk: () => R_('breakout', { n: 20, dir: 'low' }) },
    { g: 'Breakouts and gaps', l: "Closes above yesterday's high", mk: () => R_('breakout', { n: 1, dir: 'high' }) },
    { g: 'Breakouts and gaps', l: 'Opens with a gap down of more than 1%', mk: () => R_('gap', { dir: 'down', pct: 1 }) },
    { g: 'Breakouts and gaps', l: 'Opens with a gap up of more than 1%', mk: () => R_('gap', { dir: 'up', pct: 1 }) },
    { g: 'Momentum and volume', l: 'Green candle (closes above its open)', mk: () => R_('candle', { dir: 'green' }) },
    { g: 'Momentum and volume', l: 'Red candle (closes below its open)', mk: () => R_('candle', { dir: 'red' }) },
    { g: 'Momentum and volume', l: 'Volume is 1.5 times normal', mk: () => R_('volume', { n: 20, mult: 1.5 }) },
    { g: 'Momentum and volume', l: 'MACD crosses above its signal line', mk: () => R_('macd', { fast: 12, slow: 26, sig: 9, dir: 'up' }) },
    { g: 'Momentum and volume', l: 'Price rose 5% in the last 10 days', mk: () => R_('roc', { n: 10, op: '>', pct: 5 }) },
    { g: 'Momentum and volume', l: 'Volatility is high (ATR above 1.5% of the price)', mk: () => R_('atrp', { n: 14, op: '>', v: 1.5 }) }
  ];
  const mirrorRules = list => clone(list).map(c => { if (c.t === 'ma_rel') c.rel = c.rel === 'above' ? 'below' : 'above'; if (c.t === 'ma_cross' || c.t === 'gap' || c.t === 'macd') c.dir = c.dir === 'up' ? 'down' : 'up'; if (c.t === 'supertrend') c.dir = ({ up: 'down', down: 'up', 'is up': 'is down', 'is down': 'is up' })[c.dir]; if (c.t === 'boll') c.dir = c.dir === 'above' ? 'below' : 'above'; if (c.t === 'breakout') c.dir = c.dir === 'high' ? 'low' : 'high'; if (c.t === 'rsi') { c.op = c.op === '<' ? '>' : '<'; c.v = 100 - c.v; } if (c.t === 'roc') c.op = c.op === '>' ? '<' : '>'; if (c.t === 'candle') c.dir = c.dir === 'green' ? 'red' : 'green'; if (c.t === 'ibs') { c.op = c.op === '<' ? '>' : '<'; c.v = +(1 - c.v).toFixed(2); } return c; });
  const specOf = sid => { if (String(sid || '').startsWith('tpl:')) { const t = TEMPLATES[sid.slice(4)]; return t ? Object.assign(clone(t), { id: sid, follow: false }) : null; } return S.list.find(x => x.id === sid) || null; };
  const short = sp => { const l = sp.long.length ? sp.long.map(c => RULES[c.t].txt(c)).join(' and ') : ''; return (sp.side === 'short' ? 'Sells when ' + sp.short.map(c => RULES[c.t].txt(c)).join(' and ') : 'Buys when ' + l) + (sp.side === 'both' ? ' and sells on the opposite' : ''); };

  function css() {
    if (document.getElementById('btlCss')) return;
    const st = document.createElement('style'); st.id = 'btlCss';
    st.textContent = `.btl{--g:linear-gradient(135deg,var(--brand,#4f8ef7),var(--brand-2,#06b6d4));font-size:15px;line-height:1.4}.btl *{box-sizing:border-box}
.btl h3{margin:0 0 4px;font-size:19px}.btl .muted{color:var(--text-3,#8a93a6)}.btl small{font-size:12px}.btl b{font-weight:700}
.btl button,.btl select,.btl input,.btl textarea{font:inherit;color:inherit}
.btl select,.btl input:not([type=checkbox]):not([type=file]),.btl textarea{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:10px 12px;min-height:44px;width:100%;color:var(--text)}
.btl label{display:flex;flex-direction:column;gap:5px;font-size:12.5px;color:var(--text-3,#8a93a6);font-weight:600;min-width:0}
.btl-top{display:flex;justify-content:space-between;align-items:flex-start;gap:10px;flex-wrap:wrap;margin-bottom:12px}
.btl-note{margin:0 0 12px;padding:10px 12px;border-radius:12px;font-size:13px;border:1px solid rgba(99,102,241,.4);background:rgba(99,102,241,.1)}
.btl-note.warn{border-color:rgba(245,158,11,.5);background:rgba(245,158,11,.1)}.btl-note.bad{border-color:rgba(239,68,68,.55);background:rgba(239,68,68,.12)}
.btl-sec{margin:0 0 14px;padding:16px;border-radius:18px;border:1px solid var(--line);background:linear-gradient(180deg,var(--panel-2),var(--panel))}
.btl-st{display:flex;align-items:center;gap:10px;margin:0 0 12px;font-size:17px;font-weight:800}.btl-st i{flex:none;width:28px;height:28px;border-radius:50%;display:grid;place-items:center;background:var(--g);color:#fff;font-style:normal;font-size:14px}
.btl-b{border:1px solid var(--line);background:var(--panel);border-radius:999px;padding:10px 18px;min-height:44px;cursor:pointer;font-weight:700;white-space:nowrap}
.btl-b:hover{filter:brightness(1.15)}.btl-b:disabled{opacity:.45;cursor:not-allowed}
.btl-b.pri{background:var(--g);border-color:transparent;color:#fff;box-shadow:0 6px 18px rgba(99,102,241,.4)}.btl-b.big{width:100%;min-height:54px;font-size:17px}
.btl-b.go{background:rgba(34,197,94,.14);border-color:rgba(34,197,94,.45);color:var(--up,#22c55e)}.btl-b.stop{background:rgba(245,158,11,.14);border-color:rgba(245,158,11,.5);color:var(--gold,#f59e0b)}
.btl-b.del{border-color:rgba(239,68,68,.5);color:var(--down,#ef4444)}.btl-b.sm{padding:7px 14px;min-height:38px;font-size:13.5px}
.btl-row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.btl-sub{margin:14px 0 8px;font-size:12.5px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:var(--text-3)}
.btl-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:10px}
.btl-pick{border:2px solid var(--line);border-radius:16px;background:var(--panel);overflow:hidden;transition:border-color .15s}.btl-pick.chosen{border-color:var(--brand,#4f8ef7);background:linear-gradient(160deg,rgba(99,102,241,.14),transparent 70%)}
.btl-pk{display:block;width:100%;text-align:left;border:0;background:none;padding:14px;cursor:pointer;min-height:76px}.btl-pk b{display:block;font-size:15.5px;margin-bottom:4px;overflow-wrap:anywhere}.btl-pk>span{display:block;font-size:13px;color:var(--text-2);line-height:1.4;overflow-wrap:anywhere}
.btl-act{display:flex;gap:6px;flex-wrap:wrap;padding:0 12px 12px}.btl-pill{font-size:11px;font-weight:800;padding:2px 8px;border-radius:999px;margin-left:6px;vertical-align:middle}.btl-pill.on{background:rgba(34,197,94,.18);color:var(--up,#22c55e)}.btl-pill.off{background:var(--panel-2);color:var(--text-3);border:1px solid var(--line)}
.btl-seg{display:flex;flex-wrap:wrap;gap:6px}.btl-seg button{flex:1 1 auto;border:2px solid var(--line);background:var(--panel);border-radius:14px;padding:10px 12px;min-height:46px;font-weight:700;cursor:pointer}.btl-seg button.on{border-color:var(--brand,#4f8ef7);background:rgba(99,102,241,.16)}
.btl-chk{display:flex;gap:8px;flex-wrap:wrap}.btl-chk label{flex:1 1 auto;flex-direction:row;align-items:center;gap:10px;padding:11px 14px;border:2px solid var(--line);border-radius:14px;background:var(--panel);color:var(--text);cursor:pointer;font-size:14px;font-weight:700}
.btl-chk input{width:20px;height:20px;min-height:0;padding:0}
.btl-g2{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.btl-more{margin:12px 0 0;border:1px solid var(--line);border-radius:14px;background:var(--panel);padding:2px 14px}.btl-more>summary{cursor:pointer;font-weight:700;padding:12px 0;font-size:14.5px;list-style:none}.btl-more>summary::-webkit-details-marker{display:none}.btl-more>summary::before{content:'▸';margin-right:8px;color:var(--brand)}.btl-more[open]>summary::before{content:'▾'}.btl-more>div{padding:0 0 14px}
.btl-chip{display:flex;align-items:flex-start;gap:8px;padding:10px 12px;border-radius:12px;background:var(--panel);border:1px solid var(--line);margin-bottom:6px;font-size:14px}.btl-chip span{flex:1;overflow-wrap:anywhere}.btl-chip button{flex:none;border:0;background:none;color:var(--down,#ef4444);font-size:18px;cursor:pointer;min-width:34px;min-height:34px}
.btl-rule{display:flex;gap:8px;flex-wrap:wrap;align-items:flex-end;padding:12px;border-radius:12px;background:var(--panel);border:1px solid var(--line);margin-bottom:8px}.btl-rule label{flex:1 1 110px}
.btl-verdict{padding:18px;border-radius:18px;margin:6px 0 12px;text-align:center;border:2px solid}.btl-verdict.ok{border-color:rgba(34,197,94,.55);background:linear-gradient(160deg,rgba(34,197,94,.18),transparent 75%)}.btl-verdict.zero{border-color:var(--line);background:var(--panel)}.btl-verdict.bad{border-color:rgba(239,68,68,.55);background:linear-gradient(160deg,rgba(239,68,68,.18),transparent 75%)}
.btl-verdict .vt{font-size:15px;font-weight:800}.btl-verdict .vb{font-size:24px;margin:6px 0;overflow-wrap:anywhere}.btl-verdict .vb b{font-size:30px}.btl-verdict .vs{font-size:13.5px;color:var(--text-2)}
.btl-four{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin:0 0 12px}.btl-four div{padding:12px;border-radius:14px;border:1px solid var(--line);background:var(--panel)}.btl-four b{display:block;font-size:22px;line-height:1.1}.btl-four small{display:block;margin-top:3px;color:var(--text-3);line-height:1.3}
.btl-tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;margin:10px 0}.btl-t{padding:10px 12px;border-radius:14px;border:1px solid var(--line);background:var(--panel)}.btl-t b{display:block;font-size:18px;overflow-wrap:anywhere}.btl-t small{display:block;color:var(--text-3);margin-top:3px;line-height:1.3}
.btl-tabs{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 12px}.btl-tabs button{flex:1 1 auto;border:2px solid var(--line);background:var(--panel);border-radius:14px;padding:10px 12px;min-height:46px;font-weight:700;cursor:pointer}.btl-tabs button.on{border-color:var(--brand,#4f8ef7);background:rgba(99,102,241,.16)}
.btl svg.btl-chart{width:100%!important;height:auto!important;aspect-ratio:600/180;display:block;border-radius:12px;background:var(--panel);border:1px solid var(--line)}
.btl-yr{width:100%;border-collapse:collapse;font-size:13.5px}.btl-yr th{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--text-3);text-align:right;padding:6px 8px;border-bottom:1px solid var(--line)}.btl-yr th:first-child,.btl-yr td:first-child{text-align:left}.btl-yr td{text-align:right;padding:8px;border-bottom:1px solid var(--line)}
.btl-tr{display:grid;grid-template-columns:1fr auto;gap:2px 10px;padding:10px 12px;border-radius:12px;border:1px solid var(--line);background:var(--panel);margin-bottom:8px;border-left:4px solid var(--line)}.btl-tr.w{border-left-color:var(--up,#22c55e)}.btl-tr.l{border-left-color:var(--down,#ef4444)}
.btl-tr .a{font-weight:700;overflow-wrap:anywhere}.btl-tr .b{font-weight:800;text-align:right;white-space:nowrap}.btl-tr .c{grid-column:1/-1;font-size:12.5px;color:var(--text-2);overflow-wrap:anywhere}
.up{color:var(--up,#22c55e)}.down{color:var(--down,#ef4444)}.btl-pg{display:flex;gap:8px;align-items:center;justify-content:center;margin:8px 0;flex-wrap:wrap}
.btl-sig{width:100%;border-collapse:collapse;font-size:13px}.btl-sig td,.btl-sig th{padding:8px;border-bottom:1px solid var(--line);text-align:left}
.btl-skel{height:70px;border-radius:14px;background:linear-gradient(90deg,var(--panel-2) 25%,var(--panel) 50%,var(--panel-2) 75%);background-size:200% 100%;animation:btlsk 1.2s linear infinite;margin:8px 0}@keyframes btlsk{to{background-position:-200% 0}}
.btl pre{white-space:pre-wrap;font-size:12px;margin:6px 0;padding:8px;border-radius:10px;background:var(--panel-2)}.btl code{font-size:11.5px;background:var(--panel-2);padding:1px 5px;border-radius:5px}
@media (max-width:720px){.btl-cards{grid-template-columns:1fr}.btl-top .btl-row{width:100%}.btl-top .btl-b{flex:1 1 0}.btl-sec{padding:14px}.btl-verdict .vb b{font-size:27px}}`;
    document.head.appendChild(st);
  }
  const optList = (list, v) => list.map(o => `<option value="${esc(o)}" ${String(o) === String(v) ? 'selected' : ''}>${esc(o)}</option>`).join('');
  const ruleRow = (side, i, c) => `<div class="btl-rule" data-rs="${side}" data-ri="${i}"><label style="flex:2 1 200px">Rule<select data-rt>${Object.keys(RULES).map(k => `<option value="${k}" ${c.t === k ? 'selected' : ''}>${esc(RULES[k].label)}</option>`).join('')}</select></label>
    ${RULES[c.t].p.map(p => `<label>${esc(LBL[p.k] || 'Type')}${p.s ? `<select data-rp="${p.k}">${optList(p.s, c[p.k])}</select>` : `<input data-rp="${p.k}" type="number" inputmode="decimal" value="${esc(c[p.k])}" min="${p.min}" max="${p.max}" step="${p.step || 1}">`}</label>`).join('')}
    <button type="button" class="btl-b del sm" data-rdel aria-label="Remove this rule" style="flex:none">✕</button></div>`;
  const ruleBlock = (title, side, list) => `<div style="margin-bottom:10px"><div style="font-weight:700;margin-bottom:6px">${title}</div>${list.map((c, i) => ruleRow(side, i, c)).join('') || '<div class="muted" style="font-size:12.5px;margin-bottom:6px">No rules yet.</div>'}<button type="button" class="btl-b sm" data-radd="${side}">+ Add a rule</button></div>`;
  const chipsHTML = (side, list) => list.map((c, i) => `<div class="btl-chip"><span>${esc(RULES[c.t].txt(c))}</span><button type="button" data-cdel="${side}" data-ci="${i}" aria-label="Remove">✕</button></div>`).join('');
  const addSelect = side => `<select data-cadd="${side}"><option value="">+ Add a condition…</option>${['Trend', 'Dips and bounces', 'Breakouts and gaps', 'Momentum and volume'].map(g => `<optgroup label="${g}">${SIMPLE.map((o, i) => o.g === g ? `<option value="${i}">${esc(o.l)}</option>` : '').join('')}</optgroup>`).join('')}</select>`;
  const choice = (key, cur, list) => { const has = list.some(o => String(o[0]) === String(cur)); return `<select data-sf="${key}">${list.map(o => `<option value="${o[0]}" ${String(o[0]) === String(cur) ? 'selected' : ''}>${esc(o[1])}</option>`).join('')}${has ? '' : `<option value="${esc(cur)}" selected>Custom (${esc(cur)})</option>`}</select>`; };

  function builderHTML() {
    const e = S.edit; if (!e) return '';
    const both = e.side === 'both', exists = S.list.some(x => x.id === e.id), adv = e.side === 'short';
    return `<div class="btl-sec" id="btlBuilder"><div class="btl-st"><i>✎</i>${exists ? 'Edit your strategy' : 'Make your own strategy'}</div>
      <label>Name<input data-f="name" value="${esc(e.name)}" maxlength="60"></label>
      <div class="btl-sub">Buy when ALL of these are true</div>${chipsHTML('long', e.long)}${e.long.length ? '' : '<div class="muted" style="margin-bottom:6px">Nothing yet: add at least one condition.</div>'}${addSelect('long')}
      <label class="btl-chk" style="margin-top:10px"><label style="flex-direction:row"><input type="checkbox" data-alsosell ${both ? 'checked' : ''} ${adv ? 'disabled' : ''}>Also sell (buy puts / short) when the opposite happens</label></label>
      <div class="btl-sub">Exit early when (optional)</div>${chipsHTML('exitIf', e.exitIf || [])}${addSelect('exitIf')}
      <div class="btl-sub">Protect the trade</div>
      <div class="btl-g2"><label>Stop-loss${choice('stop.k', e.stop.type === 'atr' ? e.stop.k : '', [[1, 'Tight'], [1.5, 'Normal'], [2.5, 'Wide']])}</label>
        <label>Profit target${choice('target', e.target.on ? e.target.r : 0, [[0, 'No target'], [2, 'Twice the risk'], [3, 'Three times the risk']])}</label>
        <label>Trailing stop${choice('trail', e.trail.on ? 1 : 0, [[0, 'Off'], [1, 'On: lock in profit as it rises']])}</label>
        <label>Hold at most${choice('maxHold', e.maxHold, [[1, '1 day'], [5, '5 days'], [10, '10 days'], [20, '20 days'], [60, '60 days']])}</label></div>
      <details class="btl-more"><summary>Advanced: exact numbers and rules</summary><div>
        <div class="btl-g2"><label>Direction<select data-f="side"><option value="long" ${e.side === 'long' ? 'selected' : ''}>Buy only</option><option value="short" ${e.side === 'short' ? 'selected' : ''}>Sell only</option><option value="both" ${e.side === 'both' ? 'selected' : ''}>Both</option></select></label>
          <label>Stop type<select data-f="stop.type"><option value="atr" ${e.stop.type === 'atr' ? 'selected' : ''}>× ATR(14)</option><option value="pct" ${e.stop.type === 'pct' ? 'selected' : ''}>% of price</option></select></label>
          ${e.stop.type === 'atr' ? `<label>Stop = × ATR<input data-f="stop.k" type="number" inputmode="decimal" step="0.25" min="0.25" max="10" value="${esc(e.stop.k)}"></label>` : `<label>Stop = % of price<input data-f="stop.pct" type="number" inputmode="decimal" step="0.25" min="0.25" max="30" value="${esc(e.stop.pct)}"></label>`}
          ${e.target.on ? `<label>Target × the risk<input data-f="target.r" type="number" inputmode="decimal" step="0.5" min="0.5" max="20" value="${esc(e.target.r)}"></label>` : ''}
          ${e.trail.on ? `<label>Trail starts after +R<input data-f="trail.start" type="number" inputmode="decimal" step="0.5" min="0.5" max="10" value="${esc(e.trail.start)}"></label><label>Trails behind by R<input data-f="trail.dist" type="number" inputmode="decimal" step="0.25" min="0.25" max="10" value="${esc(e.trail.dist)}"></label>` : ''}</div>
        <div style="height:10px"></div>${ruleBlock('Buy rules', 'long', e.long)}${e.side !== 'long' ? ruleBlock('Sell rules', 'short', e.short) : ''}${ruleBlock('Exit rules', 'exitIf', e.exitIf || [])}</div></details>
      <div class="btl-row" style="margin-top:14px"><button type="button" class="btl-b pri" data-save>Save strategy</button><button type="button" class="btl-b" data-resetform>↺ Reset</button><button type="button" class="btl-b" data-cancel>Cancel</button></div></div>`;
  }

  function chooseHTML() {
    const sel = S.run.sid;
    const card = (id, title, desc, sp) => {
      const on = sel === id;
      return `<div class="btl-pick ${on ? 'chosen' : ''}"><button type="button" class="btl-pk" data-pick="${esc(id)}"><b>${esc(title)}${sp ? `<span class="btl-pill ${sp.follow ? 'on' : 'off'}">${sp.follow ? 'STARTED' : 'STOPPED'}</span>` : ''}</b><span>${esc(desc)}</span></button>
        ${on ? `<div class="btl-act">${sp ? `<button type="button" class="btl-b sm" data-edit="${esc(id)}">Edit</button><button type="button" class="btl-b sm ${sp.follow ? 'stop' : 'go'}" data-toggle="${esc(id)}">${sp.follow ? '■ Stop' : '▶ Start'}</button><button type="button" class="btl-b sm" data-export="${esc(id)}">Export</button><button type="button" class="btl-b sm del" data-del="${esc(id)}">Remove</button>` : `<button type="button" class="btl-b sm" data-custom="${esc(id)}">Customize a copy</button>`}</div>` : ''}</div>`;
    };
    return `<div class="btl-sec"><div class="btl-st"><i>1</i>Choose a strategy</div>
      ${S.list.length ? `<div class="btl-sub" style="margin-top:0">My strategies</div><div class="btl-cards">${S.list.map(sp => card(sp.id, sp.name, short(sp), sp)).join('')}</div>` : ''}
      <div class="btl-sub" ${S.list.length ? '' : 'style="margin-top:0"'}>Ready-made</div><div class="btl-cards">${Object.keys(TEMPLATES).map(k => card('tpl:' + k, TEMPLATES[k].name, TEMPLATES[k].desc || short(TEMPLATES[k]), null)).join('')}</div>
      <div class="muted" style="font-size:13px;margin-top:12px">Want your own? Press <b>+ Add my own strategy</b> or <b>⬆ Upload a file</b> (.json or .md) at the top.</div></div>`;
  }
  function runHTML() {
    const r = S.run, sp = specOf(r.sid);
    return `<div class="btl-sec"><div class="btl-st"><i>2</i>How far back, and where?</div>
      <div class="btl-sub" style="margin-top:0">How far back</div><div class="btl-seg">${[4, 8, 'max'].map(y => `<button type="button" data-yrs="${y}" class="${r.years === y ? 'on' : ''}">${y === 'max' ? 'As far back as possible' : y + ' years'}</button>`).join('')}</div>
      <div class="btl-sub">Which markets</div><div class="btl-chk">${Object.keys(MARKETS).map(k => `<label><input type="checkbox" data-mk="${k}" ${r.markets[k] ? 'checked' : ''}>${k === 'cash' ? 'Shares' : MARKETS[k]}</label>`).join('')}</div>
      <details class="btl-more"><summary>Account settings</summary><div><div class="btl-g2"><label>Account size (₹)<input data-run="capital" type="number" inputmode="numeric" min="10000" step="10000" value="${esc(r.capital)}"></label><label>Risk per trade (% of account)<input data-run="riskPct" type="number" inputmode="decimal" min="0.1" max="10" step="0.1" value="${esc(r.riskPct)}"></label><label>Most trades open at once<input data-run="maxOpen" type="number" inputmode="numeric" min="0" max="50" step="1" value="${esc(r.maxOpen)}"></label></div>
        <label style="margin-top:10px">Extra share symbols (optional, e.g. WIPRO, DLF)<input data-run="extra" placeholder="WIPRO, DLF" value="${esc(r.extra)}"></label></div></details></div>
      <div class="btl-sec"><div class="btl-st"><i>3</i>Test it</div>
      ${sp ? `<div class="muted" style="font-size:13.5px;margin-bottom:10px"><b style="color:var(--text)">${esc(sp.name)}</b>: ${esc(short(sp))}</div>` : '<div class="muted" style="margin-bottom:10px">Choose a strategy in step 1.</div>'}
      <button type="button" class="btl-b pri big" data-run-go ${S.busy || !sp ? 'disabled' : ''}>${S.busy ? 'Testing…' : '▶ Test this strategy'}</button>
      <div id="btlProg" class="muted" style="margin-top:8px;font-size:13px">${esc(S.prog)}</div>${S.busy && S.prog ? '<div class="btl-skel"></div>' : ''}</div>`;
  }

  function resultsHTML() {
    const R = S.res; if (!R) return '';
    const tabs = Object.keys(MARKETS).filter(k => S.run.markets[k]), tab = R.st[S.tab] ? S.tab : tabs[0], st = R.st[tab], spn = tab === 'idx' ? R.span.idx : R.span.stk;
    const head = `<div class="btl-sec" id="btlResult"><div class="btl-st"><i>✓</i>Result: ${esc(R.name)}</div><div class="btl-row" style="margin:-4px 0 12px"><button type="button" class="btl-b sm" data-another>↺ Reset and test another strategy</button></div><div class="btl-tabs">${tabs.map(k => `<button type="button" data-tab="${k}" class="${tab === k ? 'on' : ''}">${k === 'cash' ? 'Shares' : MARKETS[k]}</button>`).join('')}</div>`;
    if (!st || !st.n) return head + `<div class="btl-note warn">No trades in this market for this period. The rules never fired, or only while a trade was already open. Try another strategy or a longer period.</div></div>`;
    const end = R.cap + st.net, ok = st.net >= 0;
    const note = `Tested from ${R.cutoff === '0000-00-00' ? (spn ? spn.first : st.first) : R.cutoff} to ${R.lastDate}${R.years === 'max' ? ' (as far back as the data goes)' : ''}. Each trade risked ${inr(st.per)} (${R.riskPct}% of ${inr(R.cap)})${R.maxOpen > 0 ? ', up to ' + R.maxOpen + ' open at once' : ''}.`;
    const verdict = `<div class="btl-verdict ${ok ? 'ok' : 'bad'}"><div class="vt">${ok ? '✅ This strategy made money' : '❌ This strategy lost money'}</div><div class="vb">${inr(R.cap)} → <b>${inr(Math.max(0, end))}</b></div><div class="vs">${end <= 0 ? 'The whole account would have been lost (the strategy lost ' + inr(Math.abs(st.net)) + ' on paper; in real life trading would have stopped long before). Lower the risk per trade or try another strategy.' : (ok ? '+' : '−') + Math.abs(st.ret).toFixed(0) + '% in ' + st.yrs.toFixed(1) + ' years (about ' + (st.perYear >= 0 ? '+' : '−') + Math.abs(st.perYear).toFixed(1) + '% a year)'}</div></div>`;
    const four = `<div class="btl-four"><div><b>${st.winPct.toFixed(0)}%</b><small>of ${st.n} trades made money</small></div><div><b>${st.stopPct.toFixed(0)}%</b><small>hit the stop-loss</small></div><div><b>${st.tgtPct.toFixed(0)}%</b><small>hit the profit target</small></div><div><b class="down">${inr(st.dd)}</b><small>worst drop from a peak (${Math.min(100, st.ddPct).toFixed(0)}% of the account)</small></div></div>`;
    const cv = st.curve, W = 600, H = 180, pad = 8, ys = cv.map(c => c[1]), mn = Math.min(0, ...ys), mx = Math.max(0, ...ys), rg = (mx - mn) || 1;
    const X = i => pad + (W - 2 * pad) * (cv.length < 2 ? 0 : i / (cv.length - 1)), Y = v => H - pad - (H - 2 * pad) * (v - mn) / rg, pts = cv.map((c, i) => `${X(i).toFixed(1)},${Y(c[1]).toFixed(1)}`).join(' '), zero = Y(0).toFixed(1);
    const chart = `<div style="font-weight:700;margin:4px 0">Your ${inr(R.cap)} over time</div><svg class="btl-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Equity curve"><line x1="${pad}" x2="${W - pad}" y1="${zero}" y2="${zero}" stroke="currentColor" stroke-opacity=".25" stroke-dasharray="4 4"/><polygon points="${pad},${zero} ${pts} ${W - pad},${zero}" fill="${ok ? '#22c55e' : '#ef4444'}" fill-opacity=".14"/><polyline points="${pts}" fill="none" stroke="${ok ? '#22c55e' : '#ef4444'}" stroke-width="2.2" stroke-linejoin="round"/></svg>`;
    const T = (v, l) => `<div class="btl-t"><b>${v}</b><small>${l}</small></div>`;
    const tiles = `<div class="btl-tiles">${T(isFinite(st.pf) ? '₹' + st.pf.toFixed(2) : '∞', 'won for every ₹1 lost')}${T('+' + st.avgWin.toFixed(2) + 'R / ' + st.avgLoss.toFixed(2) + 'R', 'average win / average loss (R = the amount risked)')}${T((st.exp >= 0 ? '+' : '') + st.exp.toFixed(2) + 'R', 'average result per trade')}${T(st.peakOpen, 'most trades open at the same time')}${T(st.trailPct.toFixed(0) + '% / ' + st.timePct.toFixed(0) + '%', 'ended by the trailing stop / by time or an exit rule')}${st.medPrem != null ? T(st.medPrem.toFixed(0) + '%', 'typical stop-loss as a share of the option price (estimate)') : ''}</div>`;
    const yrs = Object.keys(st.yr).sort(), yt = `<table class="btl-yr"><thead><tr><th>Year</th><th>Trades</th><th>Win %</th><th>Net</th></tr></thead><tbody>${yrs.map(y => { const o = st.yr[y]; return `<tr><td>${y}</td><td>${o.n}</td><td>${(100 * o.w / o.n).toFixed(0)}%</td><td class="${o.net >= 0 ? 'up' : 'down'}">${sinr(o.net)}</td></tr>`; }).join('')}</tbody></table>`;
    const F = S.flt[tab] || 'ALL', pass = t => F === 'ALL' || (F === 'W' && t.R > 0) || (F === 'L' && t.R <= 0) || (F === 'SL' && t.why === 'SL') || (F === 'T' && t.why === 'T');
    const list = st.sorted.filter(pass).reverse(), per = 10, pages = Math.max(1, Math.ceil(list.length / per)), pgn = Math.min(S.pg[tab] || 0, pages - 1), view = list.slice(pgn * per, pgn * per + per);
    const WHY = { SL: 'Stop-loss hit', T: 'Target hit', TSL: 'Trailing stop', TIME: 'Time limit', EXP: 'Out before expiry', RULE: 'Exit rule' };
    const fchip = (k, l) => `<button type="button" data-flt="${k}" class="${F === k ? 'on' : ''}">${l}</button>`;
    const rows = view.map(t => `<div class="btl-tr ${t.R > 0 ? 'w' : 'l'}"><div class="a">${esc(t.sym)} · ${t.side === 'long' ? (tab === 'cash' ? 'Bought' : 'Call') : (tab === 'cash' ? 'Short' : 'Put')} · ${esc(t.entryDate)} → ${esc(t.exitDate)}</div><div class="b ${t.R > 0 ? 'up' : 'down'}">${sinr(t.R * st.per)}</div><div class="c">${f2(t.entry)} → ${f2(t.exit)} · ${WHY[t.why] || t.why} · held ${t.hold} day${t.hold === 1 ? '' : 's'}</div></div>`).join('');
    const detail = `<details class="btl-more"><summary>Show details</summary><div>${tiles}<div style="margin:10px 0 4px;font-weight:700">Year by year</div><div style="overflow-x:auto">${yt}</div>
      <div style="margin:14px 0 6px;font-weight:700">Every trade</div><div class="btl-seg" style="margin-bottom:8px">${fchip('ALL', 'All ' + st.n)}${fchip('W', 'Wins ' + st.wins)}${fchip('L', 'Losses ' + st.losses)}${fchip('SL', 'Stop-loss')}${fchip('T', 'Target')}</div>${rows || '<div class="muted">No trades match.</div>'}
      <div class="btl-pg"><button type="button" class="btl-b sm" data-pg="-1" ${pgn <= 0 ? 'disabled' : ''}>‹ Newer</button><span class="muted">${list.length ? pgn * per + 1 : 0}–${Math.min(list.length, pgn * per + per)} of ${list.length}</span><button type="button" class="btl-b sm" data-pg="1" ${pgn >= pages - 1 ? 'disabled' : ''}>Older ›</button><button type="button" class="btl-b sm" data-csv>Save as CSV</button></div></div></details>`;
    const caveat = `<p class="muted" style="font-size:12px;margin:12px 2px 0">${tab === 'cash' ? 'Shares: no time decay, 0.1% cost per round trip.' : 'Option prices are ESTIMATED (no real history exists): premium from the price range, time decay to the real expiry dates, 0.05% cost, out a day before expiry. Index options use weekly expiries from Feb 2019, monthly before.'} ${R.failed.length ? 'Could not load: ' + esc(R.failed.join(', ')) + '. ' : ''}Past results do not predict future ones, and real fills, costs and lot sizes will differ.</p><button type="button" class="btl-b pri big" data-another style="margin-top:12px">↺ Reset and test another strategy</button>`;
    return head + verdict + four + `<div class="btl-note" style="font-size:12.5px">${esc(note)}${R.raw && R.raw[tab] > st.n ? ' ' + (R.raw[tab] - st.n) + ' extra signals were skipped because the account was already full.' : ''}</div>` + chart + detail + caveat + '</div>';
  }
  function zeroHTML() {
    const cap = S.run.capital, T = (v, l) => `<div><b>${v}</b><small>${l}</small></div>`;
    return `<div class="btl-sec" id="btlResult" style="opacity:.75"><div class="btl-st"><i>0</i>Result</div>
      <div class="btl-verdict zero"><div class="vt">No test yet</div><div class="vb">${inr(cap)} → <b>${inr(cap)}</b></div><div class="vs">0% in 0 years · pick a strategy above and press Test</div></div>
      <div class="btl-four">${T('0%', 'of 0 trades made money')}${T('0%', 'hit the stop-loss')}${T('0%', 'hit the profit target')}${T('₹0', 'worst drop from a peak')}</div></div>`;
  }
  function sigHTML() {
    const fol = S.list.filter(x => x.follow);
    return `<div class="muted" style="font-size:13.5px;margin-bottom:8px">${fol.length ? 'Started: ' + fol.map(x => esc(x.name)).join(', ') : 'No strategy is started yet. Pick one of yours in step 1 and press ▶ Start.'} This only lists what each started strategy would do at tomorrow's open, on the 5 indices and 20 shares. It places nothing.</div>
      <button type="button" class="btl-b pri sm" data-sig ${S.busy ? 'disabled' : ''}>Check today's signals</button>
      ${S.sig ? (S.sig.rows.length ? `<table class="btl-sig" style="margin-top:10px"><thead><tr><th>Strategy</th><th>Symbol</th><th>Side</th><th>Last close</th><th>Stop</th><th>Target</th></tr></thead><tbody>${S.sig.rows.map(r => `<tr><td>${esc(r.name)}</td><td><b>${esc(r.sym)}</b></td><td class="${r.side === 'BUY' ? 'up' : 'down'}">${r.side}</td><td>${f2(r.px)}</td><td>${f2(r.stop)}</td><td>${r.tgt == null ? '—' : f2(r.tgt)}</td></tr>`).join('')}</tbody></table><div class="muted" style="font-size:12px;margin-top:6px">As of the ${esc(S.sig.at)} close; the entry would be the next session's open.</div>` : `<div class="muted" style="margin-top:10px">No signals on the ${esc(S.sig.at)} close.</div>`) : ''}`;
  }
  function importHTML() {
    const rules = Object.keys(RULES).map(k => `<li><b>${esc(RULES[k].label)}</b> <code>${k}</code> · ${RULES[k].p.map(p => p.k).join(', ')}</li>`).join('');
    return `<p class="muted" style="font-size:13.5px;margin:0 0 8px">Have a strategy as a file? Upload a <code>.json</code> or <code>.md</code> file, or paste it. Uploaded strategies start <b>stopped</b>, and a file can never run code: only the rule types below are read.</p>
      <div class="btl-row" style="margin-bottom:8px"><button type="button" class="btl-b sm pri" data-upload>⬆ Upload a file</button></div>
      <textarea data-paste rows="6" spellcheck="false" placeholder='Paste a strategy here (JSON or Markdown)'></textarea>
      <div class="btl-row" style="margin-top:8px"><button type="button" class="btl-b sm" data-import-paste>Import pasted text</button><button type="button" class="btl-b sm" data-example>Show an example</button></div>
      <details style="margin-top:10px"><summary style="cursor:pointer;font-weight:700">Write a strategy in Markdown</summary><pre># RSI(2) pullback
Direction: buy
Buy when:
- close above SMA(200)
- RSI(2) below 10
- close below SMA(5)
Exit when:
- close above SMA(5)
Stop: 2.5 ATR
Target: none
Trail: none
Max days: 10</pre><p class="muted" style="font-size:12.5px;margin:4px 0 0">Lines it understands: close above/below SMA(n) or EMA(n) · SMA(9) crosses above SMA(21) · RSI(14) below 30 · 20-day breakout high / low · close above yesterday's high · gap down 1% · volume 1.5x · green / red candle · IBS below 0.1 · ATR(14) above 1.5% · MACD crosses above · close below the lower Bollinger band · Supertrend flips up / is green · price up 5% in 10 days. Lines it does not understand are listed and left out, never guessed.</p></details>
      <details style="margin-top:8px"><summary style="cursor:pointer;font-weight:700">Pine Script, Python, a PDF or a video?</summary><p class="muted" style="font-size:13px;margin:6px 0 0">The lab cannot run other languages, but it can test the same rules on daily candles. Send the strategy text to Claude and ask for it as a lab strategy file, then upload it here. Ideas that need minute or hourly charts (order blocks, fair value gaps, liquidity sweeps) cannot be tested here.</p></details>
      <details style="margin-top:8px"><summary style="cursor:pointer;font-weight:700">All rule types (for JSON files)</summary><ul style="margin:6px 0 0;padding-left:18px;font-size:12.5px;line-height:1.6">${rules}</ul><p class="muted" style="font-size:12px;margin:6px 0 0">Fields: <code>name</code>, <code>side</code> (long / short / both), <code>long</code>, <code>short</code>, <code>exitIf</code>, <code>stop</code> {type: atr|pct, k, pct}, <code>target</code> {on, r}, <code>trail</code> {on, start, dist}, <code>maxHold</code>.</p></details>`;
  }
  function paintProg() { const p = S.el && S.el.querySelector('#btlProg'); if (p) p.textContent = S.prog; }
  function paint() {
    if (!S.el) return; css();
    const keep = window.scrollY, openD = [...S.el.querySelectorAll('details.btl-more[open]')].map(d => d.dataset.k).filter(Boolean);
    S.el.innerHTML = `<div class="btl"><div class="btl-top"><div><h3>🧪 Backtest lab</h3><div class="muted" style="font-size:13.5px">See what ₹1,00,000 would have become with a strategy, over the past 4 or 8 years or as far back as the data goes. <span style="font-size:11px">build 2026-10-31.6</span></div></div></div>
      <div class="btl-row btl-bar" style="margin:0 0 12px"><button type="button" class="btl-b pri" data-new>+ Add my own strategy</button><button type="button" class="btl-b" data-upload>⬆ Upload a file</button><input type="file" data-file accept=".json,.md,.markdown,.txt,application/json,text/markdown,text/plain" hidden><button type="button" class="btl-b" data-resetall>↺ Reset strategy</button></div>
      <div class="btl-note">🛡️ Test only. Nothing here touches your live auto trader or your journal.${S.msg ? '<br>' + esc(S.msg) : ''}</div>
      ${builderHTML()}${chooseHTML()}${runHTML()}${S.busy && !S.res ? '' : (S.res ? resultsHTML() : zeroHTML())}
      <details class="btl-more" data-k="sig"><summary>Started strategies: tomorrow's signals</summary><div>${sigHTML()}</div></details>
      <details class="btl-more" data-k="imp"><summary>Upload or paste a strategy (.json or .md)</summary><div>${importHTML()}</div></details></div>`;
    S.el.querySelectorAll('details.btl-more[data-k]').forEach(d => { if (openD.includes(d.dataset.k)) d.open = true; });
    window.scrollTo(0, keep);
  }

  /* ---------------- events ---------------- */
  const setPath = (o, path, v) => { const k = path.split('.'); let t = o; for (let i = 0; i < k.length - 1; i++) t = t[k[i]]; t[k[k.length - 1]] = v; };
  const clampRule = c => { RULES[c.t].p.forEach(p => { if (!p.s) { let v = parseFloat(c[p.k]); if (!isFinite(v)) v = p.d; c[p.k] = Math.min(p.max, Math.max(p.min, v)); } }); if ((c.t === 'ma_cross' || c.t === 'macd') && c.slow <= c.fast) c.slow = c.fast + 1; };
  const listFor = (e, side) => side === 'exitIf' ? (e.exitIf || (e.exitIf = [])) : e[side];
  const syncSell = e => { if (e.side === 'both') e.short = mirrorRules(e.long); };
  function startEdit(spec) { S.edit = spec; S.msg = ''; paint(); const el = S.el.querySelector('#btlBuilder'); el && el.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
  function onClick(ev) {
    const b = ev.target.closest('button'); if (!b || !S.el.contains(b)) return; const e = S.edit, d = b.dataset;
    if (b.hasAttribute('data-upload')) { const f = S.el.querySelector('[data-file]'); f && f.click(); return; }
    if (b.hasAttribute('data-example')) { const ta = S.el.querySelector('[data-paste]'); if (ta) ta.value = JSON.stringify(EXAMPLE, null, 2); return; }
    if (b.hasAttribute('data-import-paste')) { const ta = S.el.querySelector('[data-paste]'); S.msg = importText(ta ? ta.value : '') || 'Nothing to import.'; paint(); return; }
    if (d.pick) { S.cleared = false; S.run.sid = d.pick; persist(); paint(); return; }
    if (d.custom) { const t = specOf(d.custom); if (t) { const c = clone(t); c.id = uid(); c.name = t.name + ' (my copy)'; c.follow = false; startEdit(c); } return; }
    if (d.edit) { const sp = S.list.find(x => x.id === d.edit); if (sp) startEdit(clone(sp)); return; }
    if (d.toggle) { const sp = S.list.find(x => x.id === d.toggle); if (sp) { sp.follow = !sp.follow; S.msg = sp.follow ? '"' + sp.name + '" started: it is included in the signal check.' : '"' + sp.name + '" stopped.'; persist(); paint(); } return; }
    if (d.del) { const sp = S.list.find(x => x.id === d.del); if (sp && confirm('Remove "' + sp.name + '"? This cannot be undone.')) { S.list = S.list.filter(x => x.id !== sp.id); if (S.run.sid === sp.id) S.run.sid = null; if (S.res && S.res.sid === sp.id) S.res = null; persist(); S.msg = 'Removed.'; paint(); } return; }
    if (d.export) { const sp = S.list.find(x => x.id === d.export); if (!sp) return; const out = clone(sp); delete out.id; delete out.created; delete out.follow; const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([JSON.stringify(out, null, 2)], { type: 'application/json' })); a.download = 'strategy_' + sp.name.replace(/\W+/g, '_') + '.json'; document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500); return; }
    if (b.hasAttribute('data-new')) { startEdit(blank()); return; }
    if (b.hasAttribute('data-cancel')) { S.edit = null; paint(); return; }
    if (b.hasAttribute('data-resetform') && e) { S.edit = Object.assign(blank(), { id: e.id }); paint(); return; }
    if (b.hasAttribute('data-save') && e) {
      syncSell(e);
      const bad = (e.side !== 'short' && !e.long.length) ? 'Add at least one "Buy when" condition.' : (e.side !== 'long' && !e.short.length) ? 'Add at least one sell condition.' : !String(e.name).trim() ? 'Give the strategy a name.' : '';
      if (bad) { S.msg = bad; paint(); return; }
      [].concat(e.long, e.short, e.exitIf || []).forEach(clampRule);
      e.maxHold = Math.min(120, Math.max(1, Math.round(+e.maxHold) || 10)); e.stop.k = Math.min(10, Math.max(0.25, +e.stop.k || 1.5)); e.stop.pct = Math.min(30, Math.max(0.25, +e.stop.pct || 2));
      e.target.r = Math.min(20, Math.max(0.5, +e.target.r || 2)); e.trail.start = Math.min(10, Math.max(0.5, +e.trail.start || 1)); e.trail.dist = Math.min(10, Math.max(0.25, +e.trail.dist || 1.5));
      const i = S.list.findIndex(x => x.id === e.id); if (i >= 0) S.list[i] = clone(e); else S.list.push(clone(e));
      S.run.sid = e.id; S.edit = null; S.msg = 'Saved "' + e.name + '". It stays on this device for your next visit.'; persist(); paint(); return;
    }
    if (b.hasAttribute('data-radd') && e) { listFor(e, d.radd).push(newRule('ma_rel')); syncSell(e); paint(); return; }
    if (b.hasAttribute('data-rdel') && e) { const r = b.closest('[data-rs]'); listFor(e, r.dataset.rs).splice(+r.dataset.ri, 1); syncSell(e); paint(); return; }
    if (d.cdel && e) { listFor(e, d.cdel).splice(+d.ci, 1); syncSell(e); paint(); return; }
    if (d.yrs) { S.run.years = d.yrs === 'max' ? 'max' : +d.yrs; persist(); paint(); return; }
    if (b.hasAttribute('data-run-go')) { runBacktest(); return; }
    if (b.hasAttribute('data-another')) { S.res = null; S.edit = null; S.pg = {}; S.flt = {}; S.run.sid = null; S.cleared = true; S.msg = 'Cleared. Choose another strategy below, then press Test.'; persist(); paint(); const h = S.el.querySelector('.btl-sec'); h && h.scrollIntoView({ behavior: 'smooth', block: 'start' }); return; }
    if (b.hasAttribute('data-resetall')) { S.run = { years: 4, markets: { idx: true, sopt: true, cash: true }, capital: 100000, riskPct: 1, maxOpen: 5, extra: '', sid: null }; S.cleared = true; S.res = null; S.edit = null; S.sig = null; S.pg = {}; S.flt = {}; S.tab = 'idx'; S.msg = 'Reset to zero: no strategy selected and no result. Your saved strategies are kept. Pick another one and press Test.'; persist(); paint(); window.scrollTo({ top: 0, behavior: 'smooth' }); return; }
    if (d.tab) { S.tab = d.tab; paint(); return; }
    if (d.flt) { S.flt[S.tab] = d.flt; S.pg[S.tab] = 0; paint(); return; }
    if (d.pg) { S.pg[S.tab] = Math.max(0, (S.pg[S.tab] || 0) + +d.pg); paint(); return; }
    if (b.hasAttribute('data-sig')) { checkSignals(); return; }
    if (b.hasAttribute('data-csv') && S.res) {
      const st = S.res.st[S.tab]; if (!st || !st.n) return;
      const rows = [['symbol', 'side', 'entry_date', 'exit_date', 'entry', 'exit', 'result', 'R', 'rupees_on_account', 'sessions_held'].join(',')].concat(st.sorted.map(t => [t.sym, t.side, t.entryDate, t.exitDate, t.entry.toFixed(2), t.exit.toFixed(2), t.why, t.R.toFixed(3), (t.R * st.per).toFixed(0), t.hold].join(',')));
      const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([rows.join('\n')], { type: 'text/csv' })); a.download = `backtest_${S.tab}_${S.res.name.replace(/\W+/g, '_')}.csv`; document.body.appendChild(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500);
    }
  }
  function onChange(ev) {
    const t = ev.target, e = S.edit;
    if (t.matches('[data-file]')) { const f = t.files && t.files[0]; if (!f) return; if (f.size > 300000) { S.msg = 'That file is too large for a strategy (max 300 KB).'; paint(); return; }
      f.text().then(txt => { S.msg = importText(txt); t.value = ''; paint(); const go = S.el.querySelector('[data-run-go]'); if (go && !go.disabled && /^Imported/.test(S.msg)) go.scrollIntoView({ behavior: 'smooth', block: 'center' }); else window.scrollTo({ top: S.el.getBoundingClientRect().top + window.scrollY - 70, behavior: 'smooth' }); }).catch(() => { S.msg = 'Could not read that file.'; paint(); }); return; }
    if (t.matches('[data-cadd]') && e) { const o = SIMPLE[+t.value]; if (o) { listFor(e, t.dataset.cadd).push(o.mk()); syncSell(e); paint(); } return; }
    if (t.matches('[data-alsosell]') && e) { e.side = t.checked ? 'both' : 'long'; if (t.checked) e.short = mirrorRules(e.long); else e.short = []; paint(); return; }
    if (t.matches('[data-sf]') && e) { const k = t.dataset.sf, v = parseFloat(t.value);
      if (k === 'stop.k') { e.stop.type = 'atr'; e.stop.k = v; } else if (k === 'target') { e.target = { on: v > 0, r: v > 0 ? v : e.target.r }; } else if (k === 'trail') { e.trail.on = v === 1; } else if (k === 'maxHold') e.maxHold = v; paint(); return; }
    if (t.matches('[data-f]') && e) { const k = t.dataset.f; let v = t.value; setPath(e, k, t.type === 'number' ? parseFloat(v) : v); if (k === 'side') { if (e.side === 'both') e.short = mirrorRules(e.long); if (e.side === 'long') e.short = []; } if (['side', 'stop.type'].includes(k)) paint(); return; }
    const row = t.closest('[data-rs]');
    if (row && e) { const c = listFor(e, row.dataset.rs)[+row.dataset.ri]; if (!c) return;
      if (t.matches('[data-rt]')) { listFor(e, row.dataset.rs)[+row.dataset.ri] = newRule(t.value); syncSell(e); paint(); return; }
      if (t.matches('[data-rp]')) { const p = RULES[c.t].p.find(x => x.k === t.dataset.rp); c[t.dataset.rp] = p && p.s ? t.value : parseFloat(t.value); syncSell(e); } return; }
    if (t.matches('[data-run]')) { const k = t.dataset.run; S.run[k] = k === 'maxOpen' ? Math.min(50, Math.max(0, Math.round(parseFloat(t.value)) || 0)) : (k === 'capital' || k === 'riskPct') ? Math.max(k === 'capital' ? 10000 : 0.1, parseFloat(t.value) || (k === 'capital' ? 100000 : 1)) : t.value; persist(); return; }
    if (t.matches('[data-mk]')) { S.run.markets[t.dataset.mk] = t.checked; persist(); return; }
  }
  function mount(el) {
    if (S.el !== el) { S.el = el; el.addEventListener('click', onClick); el.addEventListener('change', onChange); }
    if (!S.run.sid && !S.cleared) S.run.sid = S.list.length ? S.list[0].id : 'tpl:ema_cross';
    paint();
  }
  window.BTLab = { mount, startNew: () => { if (S.el) startEdit(blank()); }, state: S, _test: { parseLine, parseMd, cleanSpec, importText, ctxOf, test, trade, expiryDay, estPrem, thetaR, stats, RULES, TEMPLATES, BARS, runSymbol, INDEX, STOCKS } };
})();
