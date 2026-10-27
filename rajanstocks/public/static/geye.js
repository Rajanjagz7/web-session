/* GOD'S EYE tab - FII / DII money flows, participant positioning, options OI and the next-day / expiry read-out,
   with the market signal cards. Data: /api/ge/dashboard (gods_eye_tab.py). Every derived number carries its rule
   (hover / tap the ⓘ). Missing inputs show "N/A", never 0. Informational only - not investment advice. */
(function () {
  'use strict';
  const E = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const LS = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const SS = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { } };
  const G = { data: LS('ge-cache', null), busy: false, err: null, ts: 0, seq: 0, tab: LS('ge-tab', 'overview'), open: null, sort: 'score', filt: 'ALL', opt: null, optExp: '', sec: null, secBusy: false, secErr: null, secTs: 0, secSel: null, sigSec: LS('ge-sigsec', 'ALL'), sq: '', ssort: 'opp', slim: 25, stock: null };
  const NA = '<span class="ge-na" title="Not available right now">N/A</span>';
  const isN = v => v != null && isFinite(v);
  const n0 = v => isN(v) ? Number(v).toLocaleString('en-IN', { maximumFractionDigits: 0 }) : NA;
  const n2 = (v, d = 2) => isN(v) ? Number(v).toLocaleString('en-IN', { minimumFractionDigits: d, maximumFractionDigits: d }) : NA;
  const sg = (v, d = 1) => isN(v) ? (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toLocaleString('en-IN', { minimumFractionDigits: d, maximumFractionDigits: d }) : NA;
  const pc = v => isN(v) ? sg(v, 2) + '%' : NA;
  const cr = v => isN(v) ? sg(v, 0) + ' cr' : NA;
  const cc = v => isN(v) ? (v > 0 ? 'up' : v < 0 ? 'down' : '') : '';
  const lab = l => l === 'BULLISH' || l === 'Bullish' || l === 'Net Long' ? 'bull' : l === 'BEARISH' || l === 'Bearish' || l === 'Net Short' ? 'bear' : 'neu';
  const tip = k => { const r = G.data && G.data.rules && G.data.rules[k]; return r ? `<button type="button" class="ge-i" data-getip="${E(k)}" aria-label="How is this calculated?" title="${E(r)}">ⓘ</button>` : ''; };
  const IST = t => { try { return new Date(t).toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'Asia/Kolkata' }) + ' IST'; } catch (e) { return ''; } };
  const dShort = d => { try { return new Date(d + 'T12:00:00+05:30').toLocaleDateString('en-IN', { day: '2-digit', month: 'short' }); } catch (e) { return d; } };

  function spark(vals, w, h, col) {
    const v = (vals || []).filter(isN); if (v.length < 2) return '<div class="ge-nochart">No history</div>';
    const lo = Math.min(...v), hi = Math.max(...v), r = hi - lo || 1;
    const pts = v.map((x, i) => `${(i / (v.length - 1) * (w - 4) + 2).toFixed(1)},${(h - 3 - (x - lo) / r * (h - 6)).toFixed(1)}`).join(' ');
    return `<svg class="ge-spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true"><polyline points="${pts}" fill="none" stroke="${col}" stroke-width="2" vector-effect="non-scaling-stroke" stroke-linejoin="round"/></svg>`;
  }
  const colOf = l => l === 'BULLISH' ? 'var(--up,#22ab94)' : l === 'BEARISH' ? 'var(--down,#f7525f)' : 'var(--text-2,#c3cad6)';
  const bar = (pct, cls) => `<i class="ge-bar"><b class="${cls || ''}" style="width:${isN(pct) ? Math.max(0, Math.min(100, pct)) : 0}%"></b></i>`;

  /* ---------- data ---------- */
  async function load(force) {
    if (G.busy && !force) return;
    const my = ++G.seq; G.busy = true; G.err = null; paint();
    try {
      const r = await fetch('/api/ge/dashboard' + (force ? '?refresh=true' : ''), { cache: 'no-store' });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const d = await r.json();
      if (my !== G.seq) return;                       // a newer request finished first: never let an older one overwrite it
      if (!d || !Array.isArray(d.cards)) throw new Error('bad response');
      G.data = d; G.ts = Date.now(); SS('ge-cache', d);
    } catch (e) { if (my === G.seq) G.err = e.message || 'network error'; }
    if (my === G.seq) { G.busy = false; paint('data'); }
  }
  async function loadOpt(exp) {
    G.optExp = exp; G.opt = 'loading'; paint();
    try { const r = await fetch('/api/ge/options?symbol=NIFTY&expiry=' + encodeURIComponent(exp || ''), { cache: 'no-store' }); G.opt = r.ok ? await r.json() : { error: 'HTTP ' + r.status }; }
    catch (e) { G.opt = { error: 'network error' }; }
    paint();
  }

  /* ---------- pieces ---------- */
  function status() {
    const d = G.data, open = typeof MKT !== 'undefined' ? MKT.open : d && d.marketOpen;
    const stale = d && Date.now() - Date.parse(d.asOf) > (open ? 10 * 60e3 : 6 * 3600e3);
    const s = G.err && !d ? ['Unavailable', 'off'] : stale ? ['Stale', 'stale'] : typeof MKT !== 'undefined' && MKT.stale ? ['Delayed', 'stale'] : open ? ['Market Live', 'on'] : ['Market Closed', 'closed'];
    return `<span class="ge-pill ${s[1]}"><i></i>${s[0]}</span>`;
  }
  function ticker(cards) {
    const l = (cards || []).filter(c => isN(c.price));
    return l.length ? `<div class="ge-tick" role="list" aria-label="Markets">${l.map(c => `<button type="button" class="ge-tk" role="listitem" data-gecard="${E(c.key)}"><b>${E(c.name || c.key)}</b><span class="num">${n2(c.price, c.price >= 1000 ? 1 : 2)}</span><span class="num ${cc(c.chgPct)}">${pc(c.chgPct)}</span></button>`).join('')}</div>` : '';
  }
  function card(c) {
    if (c.pending) return `<article class="ge-card ge-skel"><div class="ge-cn">${E(c.name || c.key)}</div><small>Loading…</small></article>`;
    if (c.error || !isN(c.score)) return `<article class="ge-card"><div class="ge-cn">${E(c.name || c.key)}</div><div class="ge-cs">—</div><div class="ge-cl">UNAVAILABLE</div><small class="muted">${E(c.error || 'no data')}</small></article>`;
    const k = lab(c.label);
    return `<article class="ge-card ${k}" data-gecard="${E(c.key)}" tabindex="0" role="button" aria-label="${E(c.name)} ${E(c.label)} score ${sg(c.score)}. Open details">
      <div class="ge-cn">${E(c.name)}${c.stale ? ' <em class="ge-old">delayed</em>' : ''}</div>
      <div class="ge-cs">${sg(c.score)}</div><div class="ge-cl">${E(c.label)}</div>
      <div class="ge-cd ${c.divergence ? (c.divergence === 'BULLISH' ? 'bull' : 'bear') : ''}">${c.divergence ? '⚡ ' + (c.divergence === 'BULLISH' ? 'Bullish' : 'Bearish') + ' divergence' : '&nbsp;'}</div>
      ${c.spark ? spark(c.spark, 120, 30, colOf(c.label)) : '<div class="ge-sp0"></div>'}
      <div class="ge-cp"><span class="num">${isN(c.price) ? (c.valueLabel ? E(c.valueLabel) + ' ' : '') + n2(c.price, c.price >= 1000 ? 1 : 2) : NA}</span><span class="num ${cc(c.chgPct)}">${pc(c.chgPct)}</span></div>
      <span class="ix-f" data-ixf="${E(c.key)}"></span>
      <div class="ge-more">Click for details →</div></article>`;
  }
  function panel(title, key, body, cls) { return `<section class="ge-p ${cls || ''}"><h3>${E(title)}${key ? tip(key) : ''}</h3>${body}</section>`; }

  function pOptionsOI(o) {
    if (!o) return panel('Options OI', 'pcr', `<p class="ge-na">Option chain unavailable</p>`);
    return panel('Options OI · NIFTY', 'pcr', `<div class="ge-row"><span>Call OI</span>${bar(o.callPct, 'down')}<b class="num">${isN(o.callPct) ? o.callPct + '%' : NA}</b></div>
      <div class="ge-row"><span>Put OI</span>${bar(o.putPct, 'up')}<b class="num">${isN(o.putPct) ? o.putPct + '%' : NA}</b></div>
      <p class="ge-sub">Build-up: <b>${E(o.buildup)}</b></p>`);
  }
  function pPCR(o) {
    if (!o) return panel('PCR / OI Data', 'pcr', `<p class="ge-na">N/A</p>`);
    const tot = Math.abs(o.callOIChg || 0) + Math.abs(o.putOIChg || 0) || 1;
    return panel('PCR / OI Data', 'pcr', `<div class="ge-big num ${o.pcr >= 1.2 ? 'up' : o.pcr <= 0.8 ? 'down' : ''}">${isN(o.pcr) ? o.pcr.toFixed(2) : NA}</div>
      <div class="ge-row"><span>OI change (call)</span><b class="num ${cc(-o.callOIChg)}">${sg(o.callOIChg / 1e5, 1)} L</b></div>
      <div class="ge-row"><span>OI change (put)</span><b class="num ${cc(o.putOIChg)}">${sg(o.putOIChg / 1e5, 1)} L</b></div>
      <p class="ge-sub">${E(o.expiry)} expiry · ${n0(o.callOI / 1e5)} L calls · ${n0(o.putOI / 1e5)} L puts</p>`);
  }
  function pRetail(p) {
    const r = p && p.retail;
    if (!r) return panel('Retail Buildup', 'retail', `<p class="ge-na">N/A - participant data not published yet</p>`);
    const m = Math.max(Math.abs(r.ceBuildup || 0), Math.abs(r.peBuildup || 0), 1);
    return panel('Retail Buildup', 'retail', `<div class="ge-row"><span>CE buildup</span>${bar(Math.abs(r.ceBuildup || 0) / m * 100, r.ceBuildup >= 0 ? 'up' : 'down')}<b class="num ${cc(r.ceBuildup)}">${pc(r.ceBuildup)}</b></div>
      <div class="ge-row"><span>PE buildup</span>${bar(Math.abs(r.peBuildup || 0) / m * 100, r.peBuildup >= 0 ? 'down' : 'up')}<b class="num ${cc(-r.peBuildup)}">${pc(r.peBuildup)}</b></div>
      <p class="ge-sub">Skew: <b class="${lab(r.skew)}">${r.skew ? E(r.skew) : NA}</b> · retail index futures ${isN(r.futLongPct) ? r.futLongPct + '% long' : NA}</p>`);
  }
  function pInst(p) {
    const f = p && p.fii;
    if (!f) return panel('F&O Institutional (FII)', 'fiiFutures', `<p class="ge-na">N/A</p>`);
    return panel('F&O Institutional (FII)', 'fiiFutures', `<div class="ge-row"><span>Long</span>${bar(f.longPct, 'up')}<b class="num">${f.longPct}%</b></div>
      <div class="ge-row"><span>Short</span>${bar(f.shortPct, 'down')}<b class="num">${f.shortPct}%</b></div>
      <div class="ge-badge ${lab(f.label)}">${E(f.label)}</div>
      <p class="ge-sub">Net ${sg(f.net, 0)} contracts (${isN(f.netChg) ? sg(f.netChg, 0) + ' vs prev' : 'no prev'})${isN(f.longPctAvg20) ? ` · usual ${f.longPctAvg20}% long` : ''} · ${dShort(p.date)}</p>`);
  }

  function outlookBlock(o, x, opt) {
    if (!o) return `<section class="ge-out"><p class="ge-na">Next-day read-out: not enough inputs yet.</p></section>`;
    const pos = (o.score + 10) / 20 * 100, open = !!G.outOpen;
    const left = x && isN(x.daysLeft) ? (x.daysLeft === 0 ? 'today' : x.daysLeft + ' left') : '';
    return `<section class="ge-out ge-outc ${lab(o.label)}">
      <div class="ge-oc">
        <div class="ge-oc-a"><small>Next day</small><b class="ge-oc-l">${E(o.label)} <span class="num">${sg(o.score)}</span></b>
          <i class="ge-meter ge-meter-s" aria-label="Score ${sg(o.score)} on -10 to +10"><i style="left:${pos}%"></i></i><span class="ge-oc-c">${E(o.confidence)} · ${o.agree}/${o.of} agree</span></div>
        ${x && opt ? `<div class="ge-oc-b"><small>Expiry ${E(dShort(x.expiry))}${left ? ' · ' + left : ''}</small>
          <span>Range <b class="num">${opt.range ? n0(opt.range[0]) + '–' + n0(opt.range[1]) : NA}</b></span><span>Put wall <b class="num up">${n0(opt.putWall)}</b></span><span>Max pain <b class="num">${n0(opt.maxPain)}</b></span><span>Call wall <b class="num down">${n0(opt.callWall)}</b></span></div>` : ''}
        <button type="button" class="ge-oc-t" data-geout="1" aria-expanded="${open}">${open ? 'Hide details ▴' : 'Why ▾'}</button>
      </div>
      <div class="ge-chips">${o.parts.map(p => `<span class="ge-chip ${cc(p.pts)}" title="${E(p.why)}">${E(p.name)} <b class="num">${sg(p.pts)}</b></span>`).join('')}</div>
      ${open ? `<div class="ge-parts">${o.parts.map(p => `<div class="ge-part"><span>${E(p.name)}</span><i class="ge-pb"><b class="${p.pts >= 0 ? 'up' : 'down'}" style="width:${Math.min(50, Math.abs(p.pts) / 3 * 50)}%;${p.pts >= 0 ? 'left:50%' : 'right:50%'}"></b></i><em class="num ${cc(p.pts)}">${sg(p.pts)}</em><small>${E(p.why)}</small></div>`).join('')}</div>
        ${x ? `<div class="ge-exp"><h4>Expiry ${E(dShort(x.expiry))}</h4><ul>${x.lines.map(l => `<li>${E(l)}</li>`).join('')}</ul></div>` : ''}` : ''}
    </section>`;
  }

  function overview(d) {
    return `${outlookBlock(d.outlook, d.expiry, d.options)}
      <div class="ge-cards ge-cards-w">${(d.cards || []).map(card).join('')}</div>`;
  }
  /* ---------- Overview, mounted at the top of Today's Picks (replaces the old Indices cards) ---------- */
  function ovInner() {
    const d = G.data;
    if (!d) return G.err ? `<section class="ge-p"><p class="ge-na">God's Eye is unavailable: ${E(G.err)} <button type="button" class="btn-xs" data-gerefresh="1">Retry</button></p></section>`
      : `<div class="ge-cards ge-cards-w">${'<article class="ge-card ge-skel"></article>'.repeat(6)}</div>`;
    return overview(d);
  }
  function paintTop() {
    const t = document.getElementById('geOvTop'); if (!t) return;
    t.innerHTML = ovInner();
    let o = document.getElementById('geOvDet');
    if (G.open && G.data) { if (!o) { o = document.createElement('div'); o.id = 'geOvDet'; o.className = 'ge'; document.body.appendChild(o); } o.innerHTML = detail(); }
    else if (o) o.remove();
    document.body.classList.toggle('ge-noscroll', !!G.open);
    try { if (typeof drawPkFut === 'function') drawPkFut(true); } catch (e) { }
  }
  window.geOverviewHTML = () => {
    if ((!G.data || Date.now() - G.ts > 300e3) && !G.busy && Date.now() - (G.tryTs || 0) > 30e3) { G.tryTs = Date.now(); setTimeout(() => load(false), 0); }
    return `<div class="ge ge-ovtop" id="geOvTop">${ovInner()}</div>`;
  };
  document.addEventListener('click', e => {
    const root = e.target.closest('#geOvTop, #geOvDet'); if (!root) return;
    const t = e.target, q = s => t.closest(s);
    const cl = q('[data-geclose]'); if (cl && (cl.tagName === 'BUTTON' || t === cl)) { G.open = null; return paint(); }
    if (q('.ge-det')) { const ch = q('[data-gechart]'); if (ch) openChart(ch.dataset.gechart); return; }
    const c = q('[data-gecard]'); if (c) { G.open = c.dataset.gecard; return paint(); }
    if (q('[data-geout]')) { G.outOpen = !G.outOpen; return paint(); }
    if (q('[data-gerefresh]')) return load(true);
    const tp = q('[data-getip]'); if (tp && typeof toast === 'function') toast(tp.title, 'info');
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && G.open && document.getElementById('geOvTop')) { G.open = null; paint(); }
    if ((e.key === 'Enter' || e.key === ' ') && e.target.closest && e.target.closest('#geOvTop [data-gecard]') && !G.open) { e.preventDefault(); G.open = e.target.closest('[data-gecard]').dataset.gecard; paint(); }
  });

  function retailTab(d) {
    const r = d.positioning && d.positioning.retail, o = d.options;
    const mood = r && r.skew ? `<section class="ge-p ge-moodp ${lab(r.skew)}"><small>Retail mood</small><b class="ge-oc-l">${E(r.skew)}</b><span class="muted">${isN(r.futLongPct) ? 'Retail index futures ' + r.futLongPct + '% long' : ''}</span></section>` : '';
    return `${mood}<div class="ge-grid4">${pRetail(d.positioning)}${pPCR(o)}${pOptionsOI(o)}</div>`;
  }
  function fnoTab(d) {
    return `<div class="ge-grid4">${pInst(d.positioning)}${pOptionsOI(d.options)}${pPCR(d.options)}</div>${optTab(d)}`;
  }
  function globalTab() {
    let page = '';                                     // card layout from index.html: tile grid + sparklines + Global Market Bias card; every tile opens its chart
    try {
      if (typeof glPageHTML === 'function') page = glPageHTML();
      if (typeof GL !== 'undefined' && !GL.items && typeof loadGlobal === 'function') loadGlobal(true);
      else if (typeof loadGlobalBias === 'function') setTimeout(() => loadGlobalBias(), 0);
    } catch (e) { }
    return page || '<section class="ge-p"><p class="ge-na">Global markets unavailable right now.</p></section>';
  }
  /* the full NSE stock list (search, index constituents, multibaggers) - the old Markets screen's screener, mounted here */
  function stocklistTab() { return '<div id="geSL" class="ge-sl"></div>'; }
  window.geNeedsGlobal = () => !!host() && G.tab === 'global';
  window.geOpenTab = (tab, sub) => { G.tab = tab; if (sub) G.slTab = sub; const g = GROUPS.find(x => x.tabs.some(t => t[0] === tab)); if (g) { LAST_SUB[g.key] = tab; SS('ge-last', LAST_SUB); } SS('ge-tab', G.tab); };
  /* day / 20-day range with the price marker - from the cards' own detail block (no extra request) */
  function rangeBar(lo, hi, px, label) {
    if (![lo, hi, px].every(isN) || hi <= lo) return `<div class="ge-rg"><small>${label}</small>${NA}</div>`;
    const at = Math.max(0, Math.min(100, (px - lo) / (hi - lo) * 100));
    return `<div class="ge-rg"><small>${label}</small><span class="num">${n2(lo, lo >= 1000 ? 0 : 2)}</span><i class="ge-rgb"><b style="left:${at.toFixed(1)}%"></b></i><span class="num">${n2(hi, hi >= 1000 ? 0 : 2)}</span></div>`;
  }
  function rangeTab(d) {
    const o = d.options, x = d.expiry;
    const exp = o && o.range ? `<section class="ge-p"><h3>NIFTY expiry range ${tip('expected')}</h3>
      <div class="ge-rg2"><span>Expected <b class="num">${n0(o.range[0])} – ${n0(o.range[1])}</b></span><span>Put wall <b class="num up">${n0(o.putWall)}</b></span><span>Max pain <b class="num">${n0(o.maxPain)}</b></span><span>Call wall <b class="num down">${n0(o.callWall)}</b></span><span>Spot <b class="num">${n0(o.spot)}</b></span></div>
      ${rangeBar(o.putWall, o.callWall, o.spot, 'Walls')}${x ? `<p class="ge-sub">Expiry ${E(dShort(x.expiry))} · ${E(x.daysLeft === 0 ? 'today' : x.daysLeft + ' day(s) left')}</p>` : ''}</section>` : '';
    const rows = (d.cards || []).filter(c => c.detail && isN(c.price)).map(c => {
      const t = c.detail;
      return `<div class="ge-rr" data-gecard="${E(c.key)}" tabindex="0" role="button"><div class="ge-rn"><b>${E(c.name)}</b><span class="num ${cc(c.chgPct)}">${pc(c.chgPct)}</span></div>
        ${rangeBar(t.dayLow, t.dayHigh, c.price, 'Day')}${rangeBar(t.low20, t.high20, c.price, '20 days')}</div>`;
    }).join('');
    return `${exp}<section class="ge-p"><h3>Where price sits in its range</h3><div class="ge-rrs">${rows || '<p class="ge-na">No range data yet.</p>'}</div></section>`;
  }

  /* stock quotes for Movers / Watchlist / Fallen Stocks - one cached request for the F&O stocks the app already lists */
  const MQ = { rows: [], ts: 0, busy: false, err: null };
  const stockSyms = () => { try { return SYMS.filter(s => s.cls === 'Stocks').map(s => s.s); } catch (e) { return []; } };
  async function loadMQ(force) {
    if (MQ.busy || (!force && Date.now() - MQ.ts < 45e3)) return;
    const syms = stockSyms().slice(0, 240); if (!syms.length) return;
    MQ.busy = true;
    try {
      const r = await fetch('/api/m/quotes?symbols=' + encodeURIComponent(syms.join(',')));
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const j = await r.json(); MQ.rows = (j.quotes || []).filter(q => q.last > 0 && q.prev > 0); MQ.ts = Date.now(); MQ.err = null;
    } catch (e) { MQ.err = String(e.message || e); }
    MQ.busy = false; if (['movers', 'watch', 'fallen'].includes(G.tab)) paint();
  }
  const nameOf = sym => { try { const x = SYMS.find(s => s.s === sym); return x ? x.n : ''; } catch (e) { return ''; } };
  const qrow = (q, extra) => `<button type="button" class="ge-qr" data-sym="${E(q.s)}"><span class="ge-qn"><b>${E(q.s)}</b><small>${E(nameOf(q.s))}</small></span><span class="num">${n2(q.last)}</span>${extra}</button>`;
  const chgOf = q => (q.last / q.prev - 1) * 100;
  const MV_PG = { g: 0, l: 0, a: 0 }, MV_SIZE = 10;
  function moversTab() {
    let st = []; try { st = SYMS.filter(s => s.cls === 'Stocks' && s.last > 0 && s.prev > 0); } catch (e) { }
    if (st.length < 20) st = MQ.rows;                  // live app quotes first, the God's Eye fetch until they arrive
    if (!st.length) return `<section class="ge-p"><p class="muted">${MQ.err ? 'Quotes unavailable: ' + E(MQ.err) : 'Loading stock prices…'}</p></section>`;
    const L = { g: st.filter(q => chgOf(q) > 0).sort((a, b) => chgOf(b) - chgOf(a)), l: st.filter(q => chgOf(q) < 0).sort((a, b) => chgOf(a) - chgOf(b)) };
    if (st.some(q => q.turn > 0)) L.a = st.slice().sort((a, b) => (b.turn || 0) - (a.turn || 0));
    const T = { g: 'Top gainers', l: 'Top losers', a: 'Most active' };
    const box = id => {
      const l = L[id], pages = Math.max(1, Math.ceil(l.length / MV_SIZE)), pg = MV_PG[id] = Math.min(MV_PG[id] || 0, pages - 1);
      const rows = l.slice(pg * MV_SIZE, pg * MV_SIZE + MV_SIZE).map((q, i) => `<button type="button" class="ge-qr" data-sym="${E(q.s)}"><span class="ge-qn"><b>${pg * MV_SIZE + i + 1}. ${E(q.s)}</b><small>${E(nameOf(q.s))}</small></span><span class="num" data-px="${E(q.s)}">${n2(q.last)}</span><span class="ge-badge ${chgOf(q) >= 0 ? 'bull' : 'bear'} num" data-chg="${E(q.s)}">${pc(chgOf(q))}</span></button>`).join('');
      return `<section class="ge-p"><h3>${T[id]} <small class="muted">· ${l.length} stocks</small></h3>${rows || '<p class="ge-na">None right now</p>'}
        ${pages > 1 ? `<div class="ge-mvpg"><button type="button" class="btn-xs" data-gemvp="${id}:${pg - 1}" ${pg <= 0 ? 'disabled' : ''}>‹ Prev</button><span class="muted">${pg + 1} / ${pages}</span><button type="button" class="btn-xs" data-gemvp="${id}:${pg + 1}" ${pg >= pages - 1 ? 'disabled' : ''}>Next ›</button></div>` : ''}</section>`;
    };
    return `<div class="ge-grid3">${Object.keys(L).map(box).join('')}</div>
      <p class="ge-sub">${st.length} stocks · change vs previous close${L.a ? ' · most active by turnover' : ''}</p>`;
  }
  function watchTab() {
    let w = []; try { w = Array.from(App.watch || []); } catch (e) { }
    const items = w.map(sym => {
      const q = MQ.rows.find(x => x.s === sym); if (q) return { n: sym, px: q.last, chg: chgOf(q), sym };
      const s = (typeof SYMS !== 'undefined') && SYMS.find(x => x.s === sym);
      return s && s.last > 0 ? { n: sym, px: s.last, chg: s.prev > 0 ? (s.last / s.prev - 1) * 100 : null, sym } : null;
    }).filter(Boolean);
    if (!items.length) return `<section class="ge-p"><p class="muted">Your watchlist is empty. Add symbols from the chart screen's watchlist and they show here.</p></section>`;
    return `<div class="ge-cards ge-cards-w">${items.map(i => `<article class="ge-card ${i.chg > 0 ? 'bull' : i.chg < 0 ? 'bear' : 'neu'}" data-sym="${E(i.sym)}" tabindex="0" role="button"><div class="ge-cn">${E(i.n)}</div><div class="ge-cs num">${n2(i.px)}</div><div class="ge-cl">${isN(i.chg) ? (i.chg >= 0 ? 'UP ' : 'DOWN ') + n2(Math.abs(i.chg)) + '%' : ''}</div><div class="ge-more">Open chart →</div></article>`).join('')}</div>`;
  }
  function fallenTab() {
    if (!MQ.rows.length) return `<section class="ge-p"><p class="muted">${MQ.err ? 'Quotes unavailable: ' + E(MQ.err) : 'Loading stock prices…'}</p></section>`;
    const f = MQ.rows.filter(q => q.yh > 0).map(q => Object.assign({ off: (q.last / q.yh - 1) * 100 }, q)).sort((a, b) => a.off - b.off).slice(0, 24);
    return `<section class="ge-p"><h3>Fallen stocks <small class="muted">· furthest below the 52-week high</small></h3>
      ${f.map(q => qrow(q, `<span class="num muted ge-yh">52W high ${n2(q.yh)}</span><span class="ge-badge bear num">${pc(q.off)}</span>`)).join('')}</section>`;
  }

  function fiiTab(d) {
    const c = d.cash, p = d.positioning;
    const flows = c ? (() => {
      const days = c.days || [], m = Math.max(1, ...days.map(x => Math.max(Math.abs(x.fii || 0), Math.abs(x.dii || 0))));
      const tile = (k, name, x, d5, d20) => `<div class="ge-ct ${x.net >= 0 ? 'bull' : 'bear'}">
          <div class="ge-ct-h"><span class="ge-key ${k}"></span><b>${name}</b><em class="ge-badge ${x.net >= 0 ? 'bull' : 'bear'}">${x.net >= 0 ? 'Net buyer' : 'Net seller'}</em></div>
          <div class="ge-ct-n num ${cc(x.net)}">${cr(x.net)}</div>
          ${isN(x.buy) ? `<div class="ge-ct-bs num">Buy ${n0(x.buy)} · Sell ${n0(x.sell)}</div>` : ''}
          <div class="ge-ct-p"><span>5 days<b class="num ${cc(d5)}">${cr(d5)}</b></span><span>20 days<b class="num ${cc(d20)}">${cr(d20)}</b></span></div></div>`;
      const bar = (k, v, side) => `<i class="${k}" style="height:${(side > 0 ? v > 0 : v < 0) ? Math.max(2, Math.abs(v) / m * 100).toFixed(1) : 0}%"></i>`;
      const last = days[days.length - 1];
      return `<section class="ge-p"><h3>FII / DII cash market · ${E(dShort(c.date))}${tip('cash')}</h3>
        <div class="ge-cash2">${tile('f', 'FII / FPI', c.fii, c.fii5, c.fii20)}${tile('d', 'DII', c.dii, c.dii5, c.dii20)}</div>
        <div class="ge-comb"><span>Combined today <b class="num ${cc(c.combined)}">${cr(c.combined)}</b></span><span class="muted">FII ${E(c.fiiStreak.side)} ${c.fiiStreak.days} day${c.fiiStreak.days > 1 ? 's' : ''} in a row</span></div>
        ${days.length ? `<div class="ge-fl" role="img" aria-label="FII and DII net flows, last ${days.length} sessions">
          <div class="ge-fl-c">${days.map((x, i) => `<div class="ge-fl-d${i === days.length - 1 ? ' on' : ''}" title="${E(dShort(x.date))} · FII ${cr(x.fii)} · DII ${cr(x.dii)}"><div class="ge-fl-u">${bar('f', x.fii, 1)}${bar('d', x.dii, 1)}</div><div class="ge-fl-l">${bar('f', x.fii, -1)}${bar('d', x.dii, -1)}</div></div>`).join('')}</div>
          <div class="ge-fl-x"><small>${E(dShort(days[0].date))}</small><small>Buying ↑ · selling ↓ · scale ±${n0(m)} cr</small><small>${E(dShort(last.date))}</small></div></div>` : ''}
        <p class="ge-sub"><span class="ge-key f"></span>FII <span class="ge-key d"></span>DII · Rs crore · today NSE provisional${c.backfilled ? ', earlier sessions net flows via moneycontrol' : ''} · ${days.length} sessions</p></section>`;
    })() : `<section class="ge-p"><h3>FII / DII cash market</h3><p class="ge-na">N/A - not published yet</p></section>`;
    const parts = p ? `<section class="ge-p"><h3>Participant positioning · index F&O · ${E(dShort(p.date))}${tip('fiiFutures')}</h3>
      <div class="ge-tw"><table class="ge-t ge-tst"><thead><tr><th>Who</th><th class="r">Fut long %</th><th class="r">Fut net</th><th class="r">Δ vs ${E(dShort(p.prevDate || ''))}</th><th class="r">Call net</th><th class="r">Put net</th></tr></thead><tbody>
      ${p.participants.map(x => `<tr><td><b>${E(x.who)}</b></td><td class="r num" data-l="Fut long">${isN(x.futLongPct) ? x.futLongPct + '%' : NA}</td><td class="r num ${cc(x.futNet)}" data-l="Fut net">${sg(x.futNet, 0)}</td><td class="r num ${cc(x.futNetChg)}" data-l="Δ day">${sg(x.futNetChg, 0)}</td><td class="r num ${cc(x.callNet)}" data-l="Call net">${sg(x.callNet, 0)}</td><td class="r num ${cc(x.putNet)}" data-l="Put net">${sg(x.putNet, 0)}</td></tr>`).join('')}
      </tbody></table></div>
      <div class="ge-2"><div><small>FII index-futures long % · 20 sessions</small>${spark((p.series || []).map(x => x.fiiLongPct), 300, 60, 'var(--brand,#2f81f7)')}</div>
        <div><small>Retail index-futures long % · 20 sessions</small>${spark((p.series || []).map(x => x.clientLongPct), 300, 60, 'var(--warn,#f5b942)')}</div></div>
      <p class="ge-sub">Contracts from NSE's participant-wise open interest file. Call / put net = long − short index options.</p></section>` : `<section class="ge-p"><h3>Participant positioning</h3><p class="ge-na">N/A</p></section>`;
    return flows + `<div class="ge-grid2">${pInst(p)}${pRetail(p)}</div>` + parts +
      `<p class="ge-sched">${E(d.schedule || '')} Data last refreshed ${E(IST(d.dataUpdatedAt))}.</p>`;
  }

  function optTab(d) {
    if (G.opt == null && d.options) { G.opt = d.options; G.optExp = d.options.expiry; }
    const o = G.opt, exps = (d.options && d.options.expiries) || [];
    const sel = `<div class="ge-seg" role="group" aria-label="Expiry">${exps.map(e => `<button type="button" class="${G.optExp === e ? 'on' : ''}" data-geexp="${E(e)}">${E(dShort(e))}</button>`).join('')}</div>`;
    if (o === 'loading') return sel + `<section class="ge-p"><p class="muted">Loading ${E(dShort(G.optExp))} chain…</p></section>`;
    if (!o || o.error) return sel + `<section class="ge-p"><p class="ge-na">${E((o && o.error) || 'Option chain unavailable')}</p></section>`;
    return sel + `<div class="ge-grid2">${pOptionsOI(o)}${pPCR(o)}</div>
      <section class="ge-p"><h3>Expiry ${E(dShort(o.expiry))} levels${tip('walls')}</h3>
        <div class="ge-lv"><span>Put wall<b class="num up">${n0(o.putWall)}</b></span><span>Max pain<b class="num">${n0(o.maxPain)}</b></span><span>Spot<b class="num">${n2(o.spot, 1)}</b></span><span>Call wall<b class="num down">${n0(o.callWall)}</b></span></div>
        <p class="ge-sub">ATM straddle ${n2(o.straddle)} → expected range ${o.range ? n0(o.range[0]) + ' – ' + n0(o.range[1]) : NA}${isN(o.daysLeft) ? ' · ' + o.daysLeft + ' session(s) left' : ''} · lot ${n0(o.lot)}</p>
        <button type="button" class="btn-xs" data-gechain="1">Open the option chain</button></section>`;
  }

  /* Signals = the stock list by sector. The instrument table that used to be here repeated the Overview cards (same
     NIFTY / SENSEX / BANKNIFTY / GOLD ... scores), so it was removed. */
  function sigTab(d) {
    return stocksBlock();
  }

  /* ---------- sectors & stocks (Nifty 500 by NSE industry, /api/ge/sectors) ---------- */
  async function loadSec(force) {
    if (G.secBusy || (!force && G.sec && Date.now() - G.secTs < 90e3)) return;
    G.secBusy = true; G.secErr = null;
    try {
      const r = await fetch('/api/ge/sectors' + (force ? '?refresh=true' : ''), { cache: 'no-store' });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const d = await r.json(); if (!d || !Array.isArray(d.stocks)) throw new Error('bad response');
      G.sec = d; G.secTs = Date.now(); if (!G.secSel && d.sectors.length) G.secSel = d.sectors[0].sec;
    } catch (e) { G.secErr = e.message || 'network error'; }
    G.secBusy = false; if (host() && ['signals', 'sectors'].includes(G.tab)) paint();
  }
  const SEC_COL = ['#22d3ee', '#3b82f6', '#a855f7', '#f59e0b', '#10b981', '#ef4444', '#ec4899', '#84cc16', '#06b6d4', '#f97316', '#6366f1', '#14b8a6', '#eab308', '#8b5cf6', '#0ea5e9', '#d946ef', '#22c55e', '#fb7185', '#94a3b8', '#64748b'];
  const secCol = name => { const i = ((G.sec && G.sec.sectors) || []).findIndex(x => x.sec === name); return SEC_COL[(i < 0 ? 0 : i) % SEC_COL.length]; };
  const secOrNote = () => G.sec ? '' : `<section class="ge-p"><p class="muted">${G.secErr ? 'Sector data unavailable: ' + E(G.secErr) + ' <button type="button" class="btn-xs" data-gesecretry="1">Retry</button>' : 'Loading stocks by sector…'}</p></section>`;
  const oppB = v => isN(v) ? `<span class="ge-opp ${v >= 70 ? 'hi' : v >= 45 ? 'mid' : 'lo'}"><i style="width:${v}%"></i><b class="num">${v}</b></span>` : NA;
  const rangeMini = r => isN(r.rangePos) ? `<i class="ge-rgm" title="52-week range: ${n2(r.yl)} – ${n2(r.yh)}"><b style="left:${r.rangePos}%"></b></i>` : NA;
  function stockRows() {
    const d = G.sec, q = G.sq.trim().toUpperCase();
    const l = d.stocks.filter(r => (G.sigSec === 'ALL' || r.sec === G.sigSec) && (!q || r.s.includes(q) || String(r.n).toUpperCase().includes(q)));
    const key = { opp: r => -(r.opp ?? -1), chg: r => -(r.chg ?? -99), ret20: r => -(r.ret20 ?? -99), volx: r => -(r.volx ?? -1), name: r => r.s }[G.ssort] || (r => -(r.opp ?? -1));
    return l.slice().sort((a, b) => { const x = key(a), y = key(b); return x < y ? -1 : x > y ? 1 : 0; });
  }
  function stockTable() {
    const l = stockRows(), shown = l.slice(0, G.slim), all = G.sigSec === 'ALL';
    return `<div class="ge-tw ge-stw"><table class="ge-t ge-stk"><thead><tr><th>Stock</th>${all ? '<th>Sector</th>' : ''}<th class="r">Price</th><th class="r">Day</th><th class="r">1M</th><th>52W</th><th class="r">Vol x</th><th>Signal</th><th>Opportunity${tip('opportunity')}</th></tr></thead><tbody>
      ${shown.map(r => `<tr data-gestock="${E(r.s)}" tabindex="0"><td><b>${E(r.s)}</b><small>${E(r.n)}</small></td>${all ? `<td class="ge-sc"><i style="background:${secCol(r.sec)}"></i>${E(r.sec)}</td>` : ''}
        <td class="r num">${n2(r.last)}</td><td class="r num ${cc(r.chg)}">${pc(r.chg)}</td><td class="r num ${cc(r.ret20)}">${pc(r.ret20)}</td><td>${rangeMini(r)}</td>
        <td class="r num">${isN(r.volx) ? r.volx.toFixed(1) + 'x' : NA}</td><td>${r.signal && r.signal !== 'NEUTRAL' ? `<span class="ge-badge ${r.signal === 'BUY' ? 'bull' : 'bear'}">${E(r.signal)}${isN(r.strength) ? ' ' + Math.round(r.strength) + '%' : ''}</span>` : '<span class="muted">—</span>'}</td><td>${oppB(r.opp)}</td></tr>`).join('') || '<tr><td colspan="9" class="muted">No stocks match.</td></tr>'}
      </tbody></table></div>
      <div class="ge-more2"><span class="muted">${shown.length} of ${l.length} stocks</span>${l.length > shown.length ? '<button type="button" class="btn-xs" data-gemore="1">Show 25 more</button>' : ''}</div>`;
  }
  function stocksBlock() {
    if (!G.sec) { loadSec(false); return secOrNote(); }
    const d = G.sec, secs = d.sectors;
    return `<section class="ge-p ge-stocks"><h3>Stocks by sector · ${E(d.universe)} <small class="muted">${d.count} stocks · ${d.adv} up / ${d.dec} down</small></h3>
      <div class="ge-secchips" role="group" aria-label="Sector"><button type="button" class="${G.sigSec === 'ALL' ? 'on' : ''}" data-gessec="ALL">All <small>${d.count}</small></button>${secs.map(x => `<button type="button" class="${G.sigSec === x.sec ? 'on' : ''}" data-gessec="${E(x.sec)}"><i style="background:${secCol(x.sec)}"></i>${E(x.sec)} <small class="${cc(x.chg)}">${pc(x.chg)}</small></button>`).join('')}</div>
      <div class="ge-stools"><input class="inp" id="geSq" placeholder="Search stock" value="${E(G.sq)}" aria-label="Search stock">
        <select class="inp" id="geSsort" aria-label="Sort">${[['opp', 'Opportunity'], ['chg', 'Day change'], ['ret20', '1-month return'], ['volx', 'Volume surge'], ['name', 'A to Z']].map(([k, l]) => `<option value="${k}" ${G.ssort === k ? 'selected' : ''}>${l}</option>`).join('')}</select></div>
      <div id="geStk">${stockTable()}</div></section>`;
  }
  function donut(secs, sel) {
    const tot = secs.reduce((a, x) => a + x.count, 0) || 1, R = 70, r = 46, C = 90;
    let a0 = -Math.PI / 2;
    const p = (rad, ang) => `${(C + rad * Math.cos(ang)).toFixed(2)},${(C + rad * Math.sin(ang)).toFixed(2)}`;
    const arcs = secs.map(x => {
      const a1 = a0 + x.count / tot * Math.PI * 2, big = a1 - a0 > Math.PI ? 1 : 0, rr = x.sec === sel ? R + 6 : R;
      const d = `M${p(rr, a0)}A${rr},${rr} 0 ${big} 1 ${p(rr, a1)}L${p(r, a1)}A${r},${r} 0 ${big} 0 ${p(r, a0)}Z`;
      a0 = a1;
      return `<path d="${d}" fill="${secCol(x.sec)}" opacity="${!sel || x.sec === sel ? 1 : .45}" data-gesec="${E(x.sec)}" tabindex="0" role="button" aria-label="${E(x.sec)}: ${x.count} companies"><title>${E(x.sec)} · ${x.count}</title></path>`;
    }).join('');
    const s = secs.find(x => x.sec === sel);
    return `<svg viewBox="0 0 180 180" class="ge-donut">${arcs}<text x="90" y="88" text-anchor="middle" class="ge-dn1">${s ? s.count : tot}</text><text x="90" y="105" text-anchor="middle" class="ge-dn2">${s ? s.share + '% of ' + tot : 'companies'}</text></svg>`;
  }
  function secTab() {
    if (!G.sec) { loadSec(false); return secOrNote(); }
    const d = G.sec, secs = d.sectors, s = secs.find(x => x.sec === G.secSel) || secs[0];
    const byS = sym => d.stocks.find(r => r.s === sym);
    const stand = (d.standouts || []).map(x => `<button type="button" class="ge-stand" ${x.s ? `data-gestock="${E(x.s)}"` : `data-gesec="${E(x.sec)}"`}><small>${E(x.title)}</small><b>${E(x.s || x.sec)}</b>${x.n ? `<span class="muted">${E(x.n)}</span>` : ''}<em class="num">${E(x.value)}</em><span class="ge-sub">${E(x.why)}</span></button>`).join('');
    return `<div class="ge-sum4"><div><small>Companies</small><b class="num">${d.count}</b></div><div><small>Sectors</small><b class="num">${secs.length}</b></div><div><small>Up / down today</small><b class="num"><span class="up">${d.adv}</span> / <span class="down">${d.dec}</span></b></div><div><small>Breadth${tip('breadth')}</small><b class="num">${isN(d.breadth) ? d.breadth + '%' : NA}</b></div></div>
      <div class="ge-secgrid"><section class="ge-p"><h3>Sector distribution</h3><div class="ge-dwrap">${donut(secs, s && s.sec)}
          <div class="ge-leg">${secs.map(x => `<button type="button" class="${s && x.sec === s.sec ? 'on' : ''}" data-gesec="${E(x.sec)}"><i style="background:${secCol(x.sec)}"></i><span>${E(x.sec)}</span><b class="num">${x.count}</b><em class="num ${cc(x.chg)}">${pc(x.chg)}</em></button>`).join('')}</div></div></section>
        ${s ? `<section class="ge-p ge-secd"><h3><i class="ge-dot" style="background:${secCol(s.sec)}"></i>${E(s.sec)}</h3>
          <div class="ge-kv"><div><small>Companies</small><b class="num">${s.count} <small class="muted">${s.share}%</small></b></div><div><small>Today (median)</small><b class="num ${cc(s.chg)}">${pc(s.chg)}</b></div><div><small>1 month (median)</small><b class="num ${cc(s.ret20)}">${pc(s.ret20)}</b></div>
            <div><small>Breadth</small><b class="num">${isN(s.breadth) ? s.breadth + '%' : NA}</b></div><div><small>Up / down</small><b class="num"><span class="up">${s.adv}</span> / <span class="down">${s.dec}</span></b></div><div><small>Opportunity (median)</small><b class="num">${isN(s.opp) ? Math.round(s.opp) : NA}</b></div></div>
          <h4>Top opportunities</h4>${s.top.map(byS).filter(Boolean).map(r => `<button type="button" class="ge-qr" data-gestock="${E(r.s)}"><span class="ge-qn"><b>${E(r.s)}</b><small>${E(r.n)}</small></span><span class="num ${cc(r.ret20)}">${pc(r.ret20)} 1M</span>${oppB(r.opp)}</button>`).join('') || '<p class="ge-na">No scored stocks.</p>'}
          <div class="ge-lv"><span>Best today<b>${E(s.best || '—')}</b></span><span>Worst today<b>${E(s.worst || '—')}</b></span>${s.bull || s.bear ? `<span>Picks signals<b><span class="up">${s.bull} buy</span> · <span class="down">${s.bear} sell</span></b></span>` : ''}</div>
          <button type="button" class="btn-xs" data-geseestocks="${E(s.sec)}">See all ${s.count} stocks →</button></section>` : ''}</div>
      <h3 class="ge-h3">Standouts right now</h3><div class="ge-stands">${stand || '<p class="ge-na">No standouts yet.</p>'}</div>
      <p class="ge-sub">${E(d.note)} Data as of ${E(IST(d.asOf))} · ${d.historyDays} sessions of history.${d.historyDays < 21 ? ' <b>1-month return, trend and volume need 21 sessions of prices - they show N/A until enough history has loaded (it fills in on its own, refresh in a few minutes).</b>' : ''}</p>`;
  }
  function stockDetail() {
    const r = G.sec && G.sec.stocks.find(x => x.s === G.stock); if (!r) return '';
    const sec = G.sec.sectors.find(x => x.sec === r.sec);
    return `<div class="ge-dbg" data-geclose="1"><div class="ge-det" role="dialog" aria-modal="true" aria-label="${E(r.s)} details">
      <div class="ge-dh"><div><small><i class="ge-dot" style="background:${secCol(r.sec)}"></i>${E(r.sec)}${r.fno ? ' · F&amp;O' : ''}</small><h3>${E(r.s)}</h3><p class="muted">${E(r.n)}</p>
        <p class="num"><b>${n2(r.last)}</b> <span class="${cc(r.chg)}">${pc(r.chg)}</span></p></div><button type="button" class="ge-x" data-geclose="1" aria-label="Close">×</button></div>
      <div class="ge-kv"><div><small>5 sessions</small><b class="num ${cc(r.ret5)}">${pc(r.ret5)}</b></div><div><small>1 month</small><b class="num ${cc(r.ret20)}">${pc(r.ret20)}</b></div><div><small>Sector 1M (median)</small><b class="num ${cc(sec && sec.ret20)}">${pc(sec && sec.ret20)}</b></div>
        <div><small>From 52W high</small><b class="num ${cc(r.fromHigh)}">${isN(r.fromHigh) ? sg(r.fromHigh) + '%' : NA}</b></div><div><small>Volume vs usual</small><b class="num">${isN(r.volx) ? r.volx.toFixed(2) + 'x' : NA}</b></div><div><small>Above 20-day avg</small><b>${r.aboveAvg == null ? NA : r.aboveAvg ? 'Yes' : 'No'}</b></div></div>
      ${rangeBar(r.yl, r.yh, r.last, '52 weeks')}
      ${r.signal ? `<div class="ge-play ${r.signal === 'BUY' ? 'bull' : r.signal === 'SELL' ? 'bear' : ''}"><b>Picks: ${E(r.signal)}${isN(r.strength) ? ' · strength ' + Math.round(r.strength) + '%' : ''}</b><span>${isN(r.rsi) ? 'RSI ' + r.rsi : ''}</span></div>` : ''}
      <h4>Opportunity ${isN(r.opp) ? r.opp + '/100' : 'N/A'}${tip('opportunity')}</h4>
      ${(r.oppParts || []).map(q => `<div class="ge-row"><span>${E(q.name)} <small class="muted">${q.weight}%</small></span>${bar(q.value, q.value >= 50 ? 'up' : 'down')}<b class="num">${q.value}</b></div>`).join('') || '<p class="ge-na">Not enough data to score.</p>'}
      <div class="ge-dact"><button type="button" class="btn pri" data-gestkchart="${E(r.s)}">Open chart</button>${r.fno ? `<button type="button" class="btn" data-gestkopt="${E(r.s)}">Option chain</button>` : ''}<button type="button" class="btn" data-geclose="1">Close</button></div>
      <p class="ge-sub">Price-based score; no P/E, ROCE or supplier data. Data as of ${E(IST(G.sec.asOf))}. Informational only.</p></div></div>`;
  }

  const CHART = { NIFTY: ['sym', 'NIFTY'], SENSEX: ['sym', 'SENSEX'], BANKNIFTY: ['sym', 'BANKNIFTY'], GOLD: ['gl', 'COMEX:GC1!'], SILVER: ['gl', 'COMEX:SI1!'], CRUDEOIL: ['gl', 'NYMEX:CL1!'], BITCOIN: ['gl', 'BITSTAMP:BTCUSD'], NASDAQ: ['gl', 'NASDAQ:NDX'], DJI: ['gl', 'DJ:DJI'], GLOBALRISK: ['gl', 'CBOE:VIX'] };
  function detail() {
    const c = ((G.data && G.data.cards) || []).find(x => x.key === G.open); if (!c) return '';
    const d = c.detail || {}, a = c.action || {}, dp = v => n2(v, v >= 1000 ? 1 : 2);
    return `<div class="ge-dbg" data-geclose="1"><div class="ge-det" role="dialog" aria-modal="true" aria-label="${E(c.name)} details">
      <div class="ge-dh"><div><small>${E(c.valueLabel || 'Instrument')}</small><h3>${E(c.name)} <span class="ge-badge ${lab(c.label)}">${E(c.label || 'UNAVAILABLE')}</span></h3>
        <p class="num">${isN(c.price) ? dp(c.price) : NA} <span class="${cc(c.chgPct)}">${pc(c.chgPct)}</span> · score <b class="${cc(c.score)}">${sg(c.score)}</b></p></div>
        <button type="button" class="ge-x" data-geclose="1" aria-label="Close">×</button></div>
      ${c.spark ? spark(c.spark, 600, 120, colOf(c.label)) : ''}
      <div class="ge-kv">${[['RSI (14)', d.rsi], ['vs 20-day avg', isN(d.vsEma20Pct) ? pc(d.vsEma20Pct) : null], ['20-day high', d.high20 && dp(d.high20)], ['20-day low', d.low20 && dp(d.low20)], ['Day high', d.dayHigh && dp(d.dayHigh)], ['Day low', d.dayLow && dp(d.dayLow)]]
        .map(([k, v]) => `<div><small>${k}</small><b class="num">${v == null ? NA : v}</b></div>`).join('')}</div>
      ${a.label ? `<div class="ge-play ${a.side === 'SELL' ? 'bear' : a.side === 'BUY' ? 'bull' : ''}"><b>${E(a.label)}</b><span>${E(a.why || '')}</span>
        ${a.zone ? `<div class="ge-lv"><span>Zone<b class="num">${dp(a.zone[0])} – ${dp(a.zone[1])}</b></span><span>Stop<b class="num down">${dp(a.sl)}</b></span><span>Targets<b class="num up">${(a.targets || []).map(dp).join(' · ')}</b></span></div>` : ''}</div>` : ''}
      ${(d.reasons || []).length ? `<h4>Why</h4><ul>${d.reasons.map(r => `<li>${E(r)}</li>`).join('')}</ul>` : ''}
      <div class="ge-dact">${CHART[c.key] ? `<button type="button" class="btn" data-gechart="${E(c.key)}">Open chart</button>` : ''}<button type="button" class="btn" data-geclose="1">Close</button></div>
      <p class="ge-sub">Data as of ${E(IST(G.data.asOf))}. Informational only - not a forecast or advice.</p></div></div>`;
  }

  /* ---------- page ---------- */
  const GROUPS = [
    { key: 'picks', label: "Today's Picks", tabs: [['picks', "Today's Picks"]] },
    { key: 'money', label: 'FII / DII', tabs: [['fii', 'Flows & positioning'], ['retail', 'Retail mood']] },
    { key: 'opt', label: 'Options & Expiry', tabs: [['fno', 'Options & Expiry']] },
    { key: 'stocks', label: 'Signals', tabs: [['signals', 'Signals'], ['sectors', 'Sectors'], ['movers', 'Movers'], ['fallen', 'Fallen']] },
    { key: 'world', label: 'Markets', tabs: [['global', 'Global'], ['stocklist', 'All stocks'], ['range', 'Range']] },
  ];
  const LAST_SUB = LS('ge-last', {});                  // a main tab reopens on the sub-tab used last
  function host() { return typeof App !== 'undefined' && App.view === 'godseye' ? document.getElementById('v-godseye') : null; }
  function paint(reason) {
    const el = host(); if (!el) { paintTop(); return; }
    if (reason === 'data' && G.tab === 'stocklist' && document.getElementById('geSL')) { const u = el.querySelector('.ge-upd'); if (u && G.data) u.textContent = 'Updated ' + IST(G.data.asOf); return; }
    if (G.tab === 'watch') G.tab = 'signals';            // the Watchlist tab was removed; anyone who had it open lands on Signals
    if (G.tab === 'picks' || G.tab === 'overview') { G.tab = 'picks'; if (typeof go === 'function') go('picks'); return; }   // the Overview tab is gone: its content is the top of Today's Picks
    const d = G.data;
    const grp = GROUPS.find(g => g.tabs.some(t => t[0] === G.tab)) || GROUPS[0];
    if (!grp.tabs.some(t => t[0] === G.tab)) G.tab = grp.tabs[0][0];
    let body;
    if (!d) body = G.err ? `<div class="ge-p"><p class="ge-na">God's Eye is unavailable: ${E(G.err)}</p><button class="btn" data-gerefresh="1">Retry</button></div>`
      : `<div class="ge-cards">${'<article class="ge-card ge-skel"></article>'.repeat(10)}</div><p class="muted">Reading markets, FII / DII and option data…</p>`;
    else body = ({ overview, retail: retailTab, fno: fnoTab, fii: fiiTab, options: optTab, movers: moversTab, range: rangeTab, global: globalTab, watch: watchTab, fallen: fallenTab, signals: sigTab, sectors: secTab, stocklist: stocklistTab }[G.tab] || overview)(d);
    if (['movers', 'watch', 'fallen'].includes(G.tab)) loadMQ(false);
    el.innerHTML = `<div class="page ge">
      ${headHTML(G.busy ? 'Updating…' : d ? 'Updated ' + E(IST(d.asOf)) : '', 'data-gerefresh="1"', G.busy)}
      ${G.err && d ? `<p class="ge-warn">Last refresh failed (${E(G.err)}) - showing data from ${E(IST(d.asOf))}.</p>` : ''}
      <div class="ge-tabs" role="tablist">${GROUPS.map(g => `<button type="button" role="tab" aria-selected="${g === grp}" class="${g === grp ? 'on' : ''}" data-getab="${g.tabs[0][0]}" data-gegrp="${g.key}">${g.label}</button>`).join('')}</div>
      ${grp.tabs.length > 1 ? `<div class="ge-sub2" role="tablist">${grp.tabs.map(([k, l]) => `<button type="button" role="tab" aria-selected="${G.tab === k}" class="${G.tab === k ? 'on' : ''}" data-getab="${k}">${l}</button>`).join('')}</div>` : ''}
      ${body}
      ${G.tab === 'global' ? '' : `<p class="ge-disc">Informational only - built from public NSE data, broker quotes and rule-based scores; not a forecast or investment advice.</p>`}
      ${G.open ? detail() : G.stock ? stockDetail() : ''}</div>`;
    document.body.classList.toggle('ge-noscroll', !!(G.open || G.stock));
    if (G.tab === 'stocklist' && window.SB) { try { SB.page(document.getElementById('geSL'), G.slTab || undefined); G.slTab = null; } catch (e) { } }
  }
  window.renderGodsEyeTab = function () { paint(); if (!G.data || Date.now() - G.ts > 60e3) load(false); };
  /* Picks shows a one-line summary only - the full God's Eye lives in its own tab (no duplicate screen) */
  window.geTags = function (root) {
    if (!root) return;
    const draw = items => (items || []).filter(c => isN(c.score)).forEach(c => root.querySelectorAll(`[data-getag="${c.key}"]`).forEach(el => {
      el.className = 'ge-tag ' + lab(c.label); el.innerHTML = `God's Eye <b class="num">${sg(c.score)}</b> ${E(c.label.charAt(0) + c.label.slice(1).toLowerCase())}`;
    }));
    draw(G.data && G.data.cards);
    if (!G.data || Date.now() - G.ts > 300e3) fetch('/api/observer').then(r => r.ok ? r.json() : null).then(d => { if (d && d.items && document.body.contains(root)) draw((G.data && G.data.cards) || d.items); }).catch(() => { });
  };
  document.addEventListener('click', e => { if (e.target.closest('[data-geopen]') && typeof go === 'function') { G.tab = 'picks'; SS('ge-tab', G.tab); go('picks'); } });
  /* Today's Picks = the Picks screen under the same God's Eye tab bar; the other tabs go back to #v-godseye */
  /* one header for every God's Eye screen, Today's Picks included (its ↻ refreshes the picks) */
  function headHTML(upd, refAttr, busy) {
    return `<div class="ge-head"><div class="ge-brand"><svg viewBox="0 0 48 28" class="ge-eye" aria-hidden="true"><path d="M2 14C9 4 39 4 46 14C39 24 9 24 2 14Z" fill="none" stroke="currentColor" stroke-width="3"/><circle cx="24" cy="14" r="6" fill="none" stroke="currentColor" stroke-width="3"/><circle cx="24" cy="14" r="2.2" fill="currentColor"/></svg>
        <div><h1><b class="ge-gt">GOD'S EYE</b> <span>– The Observer</span></h1></div></div>
        <div class="ge-st">${status()}<span class="ge-upd">${upd}</span><button type="button" class="ge-ref" ${refAttr} aria-label="Refresh" title="Refresh" ${busy ? 'disabled' : ''}>↻</button></div></div>`;
  }
  window.geTabsHTML = (o = {}) => `<div class="ge ge-pkbar">${headHTML(E(o.upd || ''), 'data-act="rpicks"', o.busy)}<div class="ge-tabs" role="tablist">${GROUPS.map(g => `<button type="button" role="tab" aria-selected="${g.key === 'picks'}" class="${g.key === 'picks' ? 'on' : ''}" data-getab="${g.tabs[0][0]}" data-gegrp="${g.key}">${g.label}</button>`).join('')}</div></div>`;
  window.geHome = () => (G.tab === 'picks' || G.tab === 'overview') ? 'picks' : 'godseye';
  document.addEventListener('click', e => {
    const tb = e.target.closest('#v-picks .ge-pkbar [data-gegrp]'); if (!tb || typeof go !== 'function') return;
    const g = GROUPS.find(x => x.key === tb.dataset.gegrp); if (!g) return;
    G.tab = LAST_SUB[g.key] && g.tabs.some(t => t[0] === LAST_SUB[g.key]) ? LAST_SUB[g.key] : g.tabs[0][0];
    SS('ge-tab', G.tab); go(G.tab === 'picks' ? 'picks' : 'godseye');
  });

  document.addEventListener('click', e => {
    if (!e.target.closest('#v-godseye')) return;
    const t = e.target, q = s => t.closest(s);
    const cl = q('[data-geclose]');
    if (cl && (cl.tagName === 'BUTTON' || t === cl)) { G.open = null; G.stock = null; return paint(); }   // the backdrop itself or a close button - not every button inside the drawer
    if (q('.ge-det')) {
      const ch = q('[data-gechart]'); if (ch) openChart(ch.dataset.gechart);
      const sc = q('[data-gestkchart]'); if (sc && typeof switchSym === 'function') { G.stock = null; document.body.classList.remove('ge-noscroll'); switchSym(sc.dataset.gestkchart); }
      const so = q('[data-gestkopt]'); if (so && typeof go === 'function') { G.stock = null; document.body.classList.remove('ge-noscroll'); try { OPT.sym = so.dataset.gestkopt; OPT.expiry = ''; OPT.chain = null; OPT.sel = null; OPT.osym = null; } catch (x) { } go('options'); }
      return;
    }
    const st = q('[data-gestock]'); if (st) { G.stock = st.dataset.gestock; return paint(); }
    const sx = q('[data-gesec]'); if (sx) { G.secSel = sx.dataset.gesec; return paint(); }
    const ss = q('[data-gessec]'); if (ss) { G.sigSec = ss.dataset.gessec; G.slim = 25; SS('ge-sigsec', G.sigSec); return paint(); }
    const see = q('[data-geseestocks]'); if (see) { G.sigSec = see.dataset.geseestocks; G.slim = 25; G.tab = 'signals'; LAST_SUB.stocks = 'signals'; SS('ge-last', LAST_SUB); SS('ge-tab', G.tab); SS('ge-sigsec', G.sigSec); paint(); const b = document.querySelector('.ge-stocks'); if (b) b.scrollIntoView({ behavior: 'smooth', block: 'start' }); return; }
    if (q('[data-gemore]')) { G.slim += 25; const h = document.getElementById('geStk'); if (h) h.innerHTML = stockTable(); return; }
    if (q('[data-gesecretry]')) return loadSec(true);
    const c = q('[data-gecard]'); if (c) { G.open = c.dataset.gecard; return paint(); }
    if (q('[data-geout]')) { G.outOpen = !G.outOpen; return paint(); }
    const mp = q('[data-gemvp]'); if (mp && !mp.disabled) { const [id, pg] = mp.dataset.gemvp.split(':'); MV_PG[id] = +pg; return paint(); }
    const tb = q('[data-getab]'); if (tb) {
      const g = tb.dataset.gegrp ? GROUPS.find(x => x.key === tb.dataset.gegrp) : null;
      G.tab = g && LAST_SUB[g.key] && g.tabs.some(t => t[0] === LAST_SUB[g.key]) ? LAST_SUB[g.key] : tb.dataset.getab;
      const gg = GROUPS.find(x => x.tabs.some(t => t[0] === G.tab)); if (gg) { LAST_SUB[gg.key] = G.tab; SS('ge-last', LAST_SUB); }
      SS('ge-tab', G.tab); if (G.tab === 'picks' && typeof go === 'function') return go('picks');
      return paint();
    }
    const pk = q('[data-gepick]'); if (pk && typeof switchSym === 'function') { switchSym(pk.dataset.gepick); return; }
    if (q('[data-gegopicks]') && typeof go === 'function') { go('picks'); return; }
    if (q('[data-gerefresh]')) { if (['signals', 'sectors'].includes(G.tab)) loadSec(true); if (G.tab === 'picks' && typeof loadPicks === 'function') Promise.resolve(loadPicks(true)).finally(() => paint()); return load(true); }
    const ex = q('[data-geexp]'); if (ex) return loadOpt(ex.dataset.geexp);
    const f = q('[data-gefilt]'); if (f) { G.filt = f.dataset.gefilt; return paint(); }
    const s = q('[data-gesort]'); if (s) { G.sort = s.dataset.gesort; return paint(); }
    if (q('[data-gechain]') && typeof go === 'function') { try { OPT.sym = 'NIFTY'; OPT.expiry = G.optExp || ''; OPT.chain = null; OPT.sel = null; OPT.osym = null; } catch (x) { } go('options'); }
    const tp = q('[data-getip]'); if (tp && typeof toast === 'function') toast(tp.title, 'info');
  });
  let sqT = 0;
  document.addEventListener('input', e => {
    if (e.target.id === 'geSq') { G.sq = e.target.value; G.slim = 25; clearTimeout(sqT); sqT = setTimeout(() => { const h = document.getElementById('geStk'); if (h) h.innerHTML = stockTable(); }, 150); }
  });
  document.addEventListener('change', e => {
    if (e.target.id === 'geSsort') { G.ssort = e.target.value; G.slim = 25; const h = document.getElementById('geStk'); if (h) h.innerHTML = stockTable(); }
  });
  document.addEventListener('keydown', e => {
    if (!host()) return;
    if (e.key === 'Escape' && (G.open || G.stock)) { G.open = null; G.stock = null; paint(); }
    if ((e.key === 'Enter' || e.key === ' ') && e.target.closest && e.target.closest('#v-godseye [data-gestock],#v-godseye path[data-gesec]') && !G.open && !G.stock) {
      e.preventDefault(); const tt = e.target.closest('[data-gestock],[data-gesec]'); if (tt.dataset.gestock) G.stock = tt.dataset.gestock; else G.secSel = tt.dataset.gesec; paint(); return;
    }
    if ((e.key === 'Enter' || e.key === ' ') && e.target.closest && e.target.closest('#v-godseye [data-gecard]') && !G.open) { e.preventDefault(); G.open = e.target.closest('[data-gecard]').dataset.gecard; paint(); }
  });
  function openChart(key) {
    const m = CHART[key]; if (!m) return; G.open = null; document.body.classList.remove('ge-noscroll');
    if (m[0] === 'sym' && typeof switchSym === 'function') { switchSym(m[1]); return; }
    if (typeof openGlobal === 'function') {
      const gl = () => (typeof GL !== 'undefined' && GL.items) || null;      // GL is a top-level const of the main script: not on window
      const run = () => { if (gl() && gl().some(i => i.id === m[1])) openGlobal(m[1]); else if (typeof toast === 'function') toast('Chart not available for ' + key, 'info'); };
      if (gl()) run(); else if (typeof loadGlobal === 'function') loadGlobal(true).then(run);
    }
  }
  setInterval(() => {
    const onPk = typeof App !== 'undefined' && App.view === 'picks' && document.getElementById('geOvTop');
    if ((!host() && !onPk) || document.hidden || G.busy) return;
    const open = typeof MKT !== 'undefined' && MKT.open;
    if (Date.now() - G.ts > (open ? 60e3 : 300e3)) load(false);
    if (!onPk && ['signals', 'sectors'].includes(G.tab) && Date.now() - G.secTs > (open ? 120e3 : 900e3)) loadSec(false);
  }, 15e3);

  const css = `
  .ge{--ge-cy:#22d3ee;padding-bottom:40px}
  .ge-head{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:10px}
  .ge-brand{display:flex;align-items:center;gap:12px}.ge-eye{width:52px;height:30px;color:var(--ge-cy)}
  .ge-brand h1{margin:0;font-size:26px;letter-spacing:.02em;background:linear-gradient(90deg,var(--brand,#2f81f7),var(--ge-cy));-webkit-background-clip:text;background-clip:text;color:transparent}
  .ge-brand h1 span{font-size:18px}.ge-brand p{margin:2px 0 0;font-size:11.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--text-3,#8a93a6)}
  .ge-st{display:flex;align-items:center;gap:10px;font-size:12.5px;color:var(--text-3,#8a93a6)}
  .ge-pill{display:inline-flex;align-items:center;gap:6px;padding:4px 11px;border-radius:14px;font-weight:700;font-size:12px;background:var(--panel-2,rgba(255,255,255,.06))}
  .ge-pill i{width:8px;height:8px;border-radius:50%;background:var(--text-3)}.ge-pill.on{color:var(--up)}.ge-pill.on i{background:var(--up);box-shadow:0 0 0 3px color-mix(in srgb,var(--up) 30%,transparent)}
  .ge-pill.stale{color:var(--warn,#f5b942)}.ge-pill.stale i{background:var(--warn,#f5b942)}.ge-pill.off{color:var(--down)}.ge-pill.off i{background:var(--down)}
  .ge-ovtop{padding-bottom:0;margin-bottom:12px}.ge-card .ix-f{display:flex;flex-wrap:wrap;gap:1px 8px;margin-top:2px;font-size:10.5px;color:var(--text-3)}.ge-card .ix-f:empty{display:none}.ge-card .ix-f b{font-size:11px;font-weight:600;color:var(--text-2)}.ge-card .ix-f .up{color:var(--up)}.ge-card .ix-f .down{color:var(--down)}
  .ge-ref{width:34px;height:34px;border-radius:50%;border:1px solid var(--line);background:var(--panel);color:var(--text);cursor:pointer;font-size:16px}
  .ge-tag{display:block;margin-top:4px;font-size:11px;font-weight:600;color:var(--text-3)}.ge-tag b{font-size:12px}.ge-tag.bull,.ge-tag.bull b{color:var(--up)}.ge-tag.bear,.ge-tag.bear b{color:var(--down)}
  .ge-tabs{display:flex;flex-wrap:wrap;gap:6px 4px;margin:4px 0 14px}
  .ge-tabs button{flex:0 0 auto;padding:7px 13px;border:1px solid transparent;border-radius:999px;background:none;color:var(--text-2,inherit);font-weight:700;font-size:13.5px;cursor:pointer}
  .ge-tabs button:hover{color:var(--text);background:var(--panel)}
  @media(max-width:560px){.ge-tabs{gap:4px 2px}.ge-tabs button{padding:6px 9px;font-size:12.5px}}
  .ge-tabs button.on{color:var(--text);background:var(--panel);border-color:var(--ge-cy);box-shadow:0 0 0 1px var(--ge-cy) inset}
  .ge-moodp{display:flex;align-items:baseline;gap:12px;margin-bottom:12px;border-left:3px solid var(--text-3)}.ge-moodp.bull{border-left-color:var(--up)}.ge-moodp.bear{border-left-color:var(--down)}
  .ge-qr{display:flex;align-items:center;gap:10px;width:100%;padding:8px 2px;border:0;border-bottom:1px solid var(--line);background:none;color:var(--text);cursor:pointer;text-align:left;font-size:13.5px}
  .ge-qr:last-child{border-bottom:0}.ge-qn{flex:1;min-width:0;display:flex;flex-direction:column}.ge-qn small{color:var(--text-3);font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .ge-yh{font-size:11.5px}
  .ge-rrs{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
  .ge-rr{padding:10px 12px;border:1px solid var(--line);border-radius:10px;cursor:pointer;background:var(--panel)}.ge-rn{display:flex;justify-content:space-between;margin-bottom:6px;font-size:13px}
  .ge-rg{display:flex;align-items:center;gap:8px;font-size:11.5px;margin:4px 0}.ge-rg small{width:48px;color:var(--text-3)}.ge-rg .num{white-space:nowrap}
  .ge-rgb{position:relative;flex:1;height:6px;border-radius:3px;background:var(--line);min-width:40px}.ge-rgb b{position:absolute;top:-3px;width:3px;height:12px;border-radius:2px;background:var(--ge-cy,#4ea1ff);transform:translateX(-50%)}
  .ge-rg2{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:13px;margin-bottom:8px}.ge-rg2 b{margin-left:5px}
  .ge-grid3{display:grid;grid-template-columns:230px minmax(0,1fr) 250px;gap:12px;align-items:start}
  .ge-col{display:flex;flex-direction:column;gap:12px;min-width:0}
  .ge-cards{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;min-width:0}
  .ge-grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}
  .ge-2{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px}.ge-2 small{font-size:11px;color:var(--text-3)}
  .ge-p{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 14px;min-width:0;margin-bottom:0}
  .ge-col .ge-p,.ge-grid2 .ge-p{margin:0}.ge>.ge-p,.ge>section.ge-p{margin-bottom:12px}
  .ge-p h3{display:flex;align-items:center;gap:6px;margin:0 0 10px;font-size:13px;font-weight:700}
  .ge-i{border:0;background:none;color:var(--text-3);cursor:help;font-size:12px;padding:0 2px}
  .ge-sub{margin:8px 0 0;font-size:11.5px;color:var(--text-3,#8a93a6);line-height:1.45}
  .ge-na{color:var(--text-3,#8a93a6);font-style:italic}
  .ge-row{display:grid;grid-template-columns:96px 1fr auto;align-items:center;gap:8px;font-size:12.5px;margin:6px 0}.ge-row b{text-align:right;white-space:nowrap}
  .ge-bar{position:relative;height:8px;border-radius:4px;background:var(--panel-2,rgba(255,255,255,.07));overflow:hidden}.ge-bar b{position:absolute;left:0;top:0;bottom:0;border-radius:4px;background:var(--brand)}
  .ge-bar b.up{background:var(--up)}.ge-bar b.down{background:var(--down)}
  .ge-big{font-size:30px;font-weight:800;text-align:center;margin:2px 0 8px}
  .ge-ring{position:relative;width:96px;height:96px;margin:4px auto}.ge-ring svg{width:96px;height:96px;transform:rotate(-90deg)}
  .ge-ring circle{fill:none;stroke-width:9}.ge-ring .bg{stroke:var(--panel-2,rgba(255,255,255,.08))}.ge-ring .fg{stroke:var(--ge-cy);stroke-linecap:round}
  .ge-ring b{position:absolute;inset:0;display:grid;place-items:center;font-size:20px}
  .ge-card{position:relative;display:flex;flex-direction:column;gap:3px;background:var(--panel);border:1px solid var(--line);border-top:3px solid var(--text-3);border-radius:12px;padding:11px 12px 10px;cursor:pointer;min-width:0}
  .ge-card:focus-visible{outline:2px solid var(--ge-cy);outline-offset:2px}.ge-card:hover{transform:translateY(-1px)}
  .ge-card.bull{border-top-color:var(--up);background:linear-gradient(180deg,color-mix(in srgb,var(--up) 8%,var(--panel)),var(--panel))}
  .ge-card.bear{border-top-color:var(--down);background:linear-gradient(180deg,color-mix(in srgb,var(--down) 8%,var(--panel)),var(--panel))}
  .ge-cn{font-size:11.5px;font-weight:800;letter-spacing:.06em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .ge-cs{font-size:28px;font-weight:800;line-height:1.05}.ge-card.bull .ge-cs,.ge-card.bull .ge-cl{color:var(--up)}.ge-card.bear .ge-cs,.ge-card.bear .ge-cl{color:var(--down)}
  .ge-cl{font-size:11px;font-weight:800;letter-spacing:.08em;color:var(--text-3)}
  .ge-cd{font-size:11px;font-weight:600;min-height:15px}.ge-cd.bull{color:var(--up)}.ge-cd.bear{color:var(--down)}
  .ge-spark{width:100%;height:30px}.ge-sp0{height:30px}.ge-nochart{font-size:11px;color:var(--text-3);padding:8px 0}
  .ge-cp{display:flex;justify-content:space-between;gap:6px;font-size:11.5px}.ge-more{font-size:11px;color:var(--text-3)}
  .ge-old{font-style:normal;font-size:9.5px;padding:1px 5px;border-radius:6px;background:var(--panel-2);color:var(--text-3)}
  .ge-skel{min-height:150px;animation:gep 1.2s ease-in-out infinite}@keyframes gep{50%{opacity:.5}}
  .ge-badge{display:inline-block;padding:3px 9px;border-radius:7px;font-size:11px;font-weight:800;letter-spacing:.05em;background:var(--panel-2);color:var(--text-2)}
  .ge-badge.bull{background:color-mix(in srgb,var(--up) 20%,transparent);color:var(--up)}.ge-badge.bear{background:color-mix(in srgb,var(--down) 20%,transparent);color:var(--down)}
  .ge-p .ge-badge{margin-top:6px}
  .ge-feed{display:grid;grid-template-columns:10px 1fr auto;gap:8px;align-items:center;font-size:12px;margin:7px 0}.ge-feed small{display:block;font-size:10.5px;color:var(--text-3)}
  .ge-feed>i{width:9px;height:9px;border-radius:50%}.ge-feed i.up{background:var(--up)}.ge-feed i.warn{background:var(--warn,#f5b942)}.ge-feed i.down{background:var(--down)}
  .ge-feed b.warn{color:var(--warn,#f5b942)}
  .ge-out{background:linear-gradient(135deg,color-mix(in srgb,var(--ge-cy) 8%,var(--panel)),var(--panel));border:1px solid var(--line);border-left:4px solid var(--text-3);border-radius:14px;padding:14px 16px;margin-bottom:12px}
  .ge-out.bull{border-left-color:var(--up)}.ge-out.bear{border-left-color:var(--down)}
  .ge-oh{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;align-items:center}
  .ge-oh small{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--text-3)}.ge-oh h3{margin:2px 0 0;font-size:22px;display:flex;align-items:center;gap:8px}
  .ge-out.bull h3{color:var(--up)}.ge-out.bear h3{color:var(--down)}
  .ge-meter{position:relative;flex:0 1 300px;min-width:200px;height:8px;border-radius:4px;background:linear-gradient(90deg,var(--down),var(--line) 50%,var(--up));margin-bottom:14px}
  .ge-meter i{position:absolute;top:50%;width:14px;height:14px;margin:-7px 0 0 -7px;border-radius:50%;background:var(--text);border:2px solid var(--panel)}
  .ge-meter span{position:absolute;top:12px;font-size:10px;color:var(--text-3)}.ge-meter span:nth-of-type(1){left:0}.ge-meter span:nth-of-type(2){left:50%;transform:translateX(-50%)}.ge-meter span:nth-of-type(3){right:0}
  .ge-parts{display:grid;grid-template-columns:1fr 1fr;gap:4px 22px;margin-top:12px}
  .ge-part{display:grid;grid-template-columns:130px 90px 40px;gap:8px;align-items:center;font-size:12.5px}.ge-part small{grid-column:1/-1;font-size:11px;color:var(--text-3);margin:-2px 0 4px}
  .ge-part em{font-style:normal;font-weight:700;text-align:right}
  .ge-pb{position:relative;height:7px;border-radius:4px;background:var(--panel-2,rgba(255,255,255,.07))}.ge-pb b{position:absolute;top:0;bottom:0;border-radius:4px}.ge-pb b.up{background:var(--up)}.ge-pb b.down{background:var(--down)}
  .ge-exp{margin-top:12px;padding-top:12px;border-top:1px solid var(--line)}.ge-exp h4{display:flex;align-items:center;gap:6px;margin:0 0 6px;font-size:13px}
  .ge-exp ul,.ge-det ul{margin:0 0 6px;padding-left:18px;font-size:12.5px;line-height:1.55;color:var(--text-2,inherit)}
  .ge-lv{display:flex;flex-wrap:wrap;gap:8px 22px;margin-top:6px}.ge-lv span{font-size:11px;color:var(--text-3)}.ge-lv b{display:block;font-size:15px;color:var(--text)}.ge-lv b.up{color:var(--up)}.ge-lv b.down{color:var(--down)}
  .ge-tw{overflow-x:auto}.ge-t{width:100%;border-collapse:collapse;font-size:12.5px}.ge-t th{font-size:10.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--text-3);text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);white-space:nowrap}
  .ge-t td{padding:7px 8px;border-bottom:1px solid var(--line);white-space:nowrap}.ge-t .r{text-align:right}.ge-sig tr[data-gecard]{cursor:pointer}.ge-sig tr[data-gecard]:hover{background:var(--panel-2)}
  /* FII / DII cash: two tiles + a buying-up / selling-down bar chart (FII blue, DII amber) */
  .ge{--ge-fii:#4f8dff;--ge-dii:#f5a524}
  .ge-cash2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
  .ge-ct{position:relative;padding:12px 12px 10px 15px;border:1px solid var(--line);border-radius:10px;background:var(--panel-2,var(--panel));overflow:hidden;min-width:0}
  .ge-ct::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--up)}.ge-ct.bear::before{background:var(--down)}
  .ge-ct-h{display:flex;align-items:center;gap:6px;flex-wrap:wrap}.ge-ct-h b{font-size:13px}.ge-ct-h .ge-key{margin:0}.ge-ct-h em{margin-left:auto;font-style:normal}
  .ge-ct-n{font-family:'DM Mono',ui-monospace,Menlo,Consolas,monospace;font-size:24px;font-weight:700;letter-spacing:-.5px;margin:8px 0 2px}
  .ge-ct-bs{font-size:11.5px;color:var(--text-3)}
  .ge-ct-p{display:flex;gap:14px;margin-top:9px;padding-top:8px;border-top:1px dashed var(--line);font-size:11px;color:var(--text-3)}
  .ge-ct-p span{display:flex;flex-direction:column;gap:1px}.ge-ct-p b{font-size:13px;font-family:'DM Mono',ui-monospace,Menlo,Consolas,monospace}
  .ge-comb{display:flex;justify-content:space-between;flex-wrap:wrap;gap:4px 12px;margin:10px 2px 4px;font-size:12.5px}
  .ge-fl{margin-top:10px}.ge-fl-c{display:flex;gap:2px;height:150px}
  .ge-fl-d{flex:1 1 0;min-width:0;display:flex;flex-direction:column;border-radius:4px}.ge-fl-d.on{background:color-mix(in srgb,var(--ge-cy) 9%,transparent)}
  .ge-fl-u,.ge-fl-l{flex:1;display:flex;justify-content:center;gap:2px}.ge-fl-u{align-items:flex-end;border-bottom:1px solid var(--text-3)}.ge-fl-l{align-items:flex-start}
  .ge-fl-d i{display:block;width:min(9px,40%)}.ge-fl-u i{border-radius:3px 3px 0 0}.ge-fl-l i{border-radius:0 0 3px 3px}
  .ge-fl-d i.f{background:var(--ge-fii)}.ge-fl-d i.d{background:var(--ge-dii)}
  .ge-fl-x{display:flex;justify-content:space-between;gap:8px;margin-top:4px;font-size:10.5px;color:var(--text-3)}
  .ge-key{display:inline-block;width:10px;height:10px;border-radius:3px;margin:0 4px 0 8px;vertical-align:-1px}.ge-key.f{background:var(--ge-fii)}.ge-key.d{background:var(--ge-dii)}
  .ge-ct-p b,.ge-ct-n{white-space:nowrap}
  @media (max-width:640px){.ge-ct{padding:10px 9px 9px 12px}.ge-ct-n{font-size:19px}.ge-ct-h b{flex:1 0 calc(100% - 20px)}.ge-ct-h em{margin-left:0}
    .ge-ct-bs{font-size:10.5px}.ge-ct-p{gap:10px}.ge-ct-p b{font-size:11.5px;letter-spacing:-.3px}.ge-fl-c{height:120px;gap:1px}.ge-fl-x small:nth-child(2){display:none}
    .ge-tst thead{display:none}.ge-tst,.ge-tst tbody{display:block}.ge-tst tr{display:grid;grid-template-columns:repeat(3,1fr);gap:6px 8px;padding:9px 2px;border-bottom:1px solid var(--line)}
    .ge-tst td{padding:0;border:0;text-align:left!important;display:flex;flex-direction:column;align-items:flex-start;justify-content:flex-start;justify-self:stretch!important;font-size:13px}.ge-tst td:first-child{grid-column:1/-1}
    .ge-tst td[data-l]::before{content:attr(data-l);font-size:10px;letter-spacing:.04em;text-transform:uppercase;color:var(--text-3);font-family:Inter,system-ui,sans-serif}}
  :root[data-theme="light"] .ge{--ge-fii:#2563eb;--ge-dii:#d97706}
  /* ---- Observer look (UI mockup): gradient title, glass signal cards with corner brackets and a glow by signal ---- */
  .ge-brand h1{font-size:34px;font-weight:800;letter-spacing:.01em;background:none;color:inherit}
  .ge-brand h1 .ge-gt{font-weight:800;background:linear-gradient(90deg,#22d3ee 0%,#a78bfa 55%,#4ade80 100%);-webkit-background-clip:text;background-clip:text;color:transparent}
  .ge-brand h1 span{font-size:22px;font-weight:600;background:linear-gradient(90deg,#22d3ee,#a78bfa);-webkit-background-clip:text;background-clip:text;color:transparent}
  .ge-eye{filter:drop-shadow(0 0 8px color-mix(in srgb,var(--ge-cy) 60%,transparent))}
  .ge-pill{border-radius:999px;padding:6px 14px;font-weight:700}.ge-pill.on{border:1.5px solid #22c55e;color:#4ade80;box-shadow:0 0 14px rgba(34,197,94,.25)}
  .ge .ge-card{--gc:148,163,184;padding:14px 16px 12px;border:1.5px solid rgba(var(--gc),.38);border-radius:14px;
    background:linear-gradient(160deg,rgba(var(--gc),.10),rgba(var(--gc),.02) 60%),var(--panel);
    box-shadow:inset 0 1px 0 rgba(255,255,255,.06),0 8px 22px rgba(0,0,0,.28);transition:transform .15s,box-shadow .15s,border-color .15s}
  .ge .ge-card.bear{--gc:239,68,68;border-color:rgba(var(--gc),.75);box-shadow:0 0 18px rgba(var(--gc),.22),inset 0 0 28px rgba(var(--gc),.10)}
  .ge .ge-card.bull{--gc:34,197,94;border-color:rgba(var(--gc),.7);box-shadow:0 0 18px rgba(var(--gc),.2),inset 0 0 28px rgba(var(--gc),.09)}
  .ge .ge-card::before,.ge .ge-card::after{content:'';position:absolute;width:13px;height:13px;pointer-events:none;background:none;border-color:rgba(226,232,240,.65);border-style:solid;border-width:0}
  .ge .ge-card::before,.ge .ge-card.bull::before,.ge .ge-card.bear::before{left:9px;top:9px;bottom:auto;background:none;border-left-width:2px;border-top-width:2px;border-top-left-radius:3px}
  .ge .ge-card::after{right:9px;bottom:9px;border-right-width:2px;border-bottom-width:2px;border-bottom-right-radius:3px}
  .ge .ge-card:hover{transform:translateY(-2px);border-color:var(--ge-cy);box-shadow:0 0 22px color-mix(in srgb,var(--ge-cy) 30%,transparent)}
  .ge .ge-cn{font-size:14px;font-weight:800;letter-spacing:.05em;text-transform:uppercase;margin-top:4px}
  .ge .ge-cs{font-family:'DM Mono',ui-monospace,Menlo,Consolas,monospace;font-size:32px;font-weight:700;line-height:1.05;letter-spacing:-1px;margin-top:4px;color:var(--text)}
  .ge .ge-cl{font-size:13.5px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:var(--text-2)}
  .ge .ge-card.bear .ge-cs,.ge .ge-card.bear .ge-cl{color:#f87171}.ge .ge-card.bull .ge-cs,.ge .ge-card.bull .ge-cl{color:#4ade80}
  .ge .ge-cd.bull{color:#4ade80;font-weight:700}.ge .ge-cd.bear{color:#f87171;font-weight:700}
  .ge .ge-more{color:#93c5fd;font-size:12.5px;margin-top:2px}
  @media (max-width:640px){.ge-brand h1{font-size:24px}.ge-brand h1 span{font-size:15px}.ge .ge-cs{font-size:26px}.ge .ge-card{padding:12px 12px 10px}.ge .ge-cn{font-size:12.5px}.ge .ge-cl{font-size:12px}}
  :root[data-theme="light"] .ge .ge-card{box-shadow:0 4px 14px rgba(15,23,42,.08)}
  :root[data-theme="light"] .ge .ge-card::before,:root[data-theme="light"] .ge .ge-card::after{border-color:rgba(15,23,42,.35)}
  :root[data-theme="light"] .ge .ge-card.bear{box-shadow:0 0 14px rgba(239,68,68,.15)}:root[data-theme="light"] .ge .ge-card.bull{box-shadow:0 0 14px rgba(34,197,94,.15)}
  :root[data-theme="light"] .ge .ge-card.bear .ge-cs,:root[data-theme="light"] .ge .ge-card.bear .ge-cl{color:#dc2626}:root[data-theme="light"] .ge .ge-card.bull .ge-cs,:root[data-theme="light"] .ge .ge-card.bull .ge-cl{color:#16a34a}
  :root[data-theme="light"] .ge .ge-more{color:#2563eb}:root[data-theme="light"] .ge-brand h1 .ge-gt{background-image:linear-gradient(90deg,#0891b2,#7c3aed 55%,#16a34a)}:root[data-theme="light"] .ge-brand h1 span{background-image:linear-gradient(90deg,#0891b2,#7c3aed)}
  :root[data-theme="light"] .ge-pill.on{color:#15803d}
  .ge-seg{display:inline-flex;gap:4px;flex-wrap:wrap;margin-bottom:10px}.ge-seg button{padding:6px 12px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text-2,inherit);font-size:12.5px;cursor:pointer}
  .ge-seg button.on{background:var(--brand);border-color:var(--brand);color:#fff}.ge-bar2{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap}
  .ge-sched,.ge-disc{font-size:11.5px;color:var(--text-3);margin:10px 2px}.ge-warn{font-size:12px;color:var(--warn,#f5b942);margin:0 0 8px}
  .ge-dbg{position:fixed;inset:0;z-index:300;background:rgba(0,0,0,.55);display:flex;justify-content:flex-end}
  .ge-det{width:min(560px,100%);height:100%;overflow-y:auto;background:var(--bg,#0b0e14);border-left:1px solid var(--line);padding:18px 18px 40px}
  .ge-dh{display:flex;justify-content:space-between;gap:10px}.ge-dh h3{margin:2px 0;font-size:20px;display:flex;gap:8px;align-items:center}.ge-dh small{font-size:11px;color:var(--text-3)}
  .ge-x{width:36px;height:36px;border-radius:50%;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:20px;cursor:pointer}
  .ge-det .ge-spark{height:120px;margin:10px 0}.ge-kv{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:8px 0}.ge-kv small{display:block;font-size:10.5px;color:var(--text-3)}
  .ge-play{border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin:10px 0}.ge-play.bull{border-color:color-mix(in srgb,var(--up) 50%,var(--line))}.ge-play.bear{border-color:color-mix(in srgb,var(--down) 50%,var(--line))}
  .ge-play b{display:block}.ge-play span{font-size:12px;color:var(--text-2)}
  .ge-play.bull{background:color-mix(in srgb,var(--up) 8%,transparent)}.ge-play.bull b{color:var(--up)}.ge-play.bear{background:color-mix(in srgb,var(--down) 8%,transparent)}.ge-play.bear b{color:var(--down)}
  .ge-p .ge-badge.ge-act,.ge-ct-h .ge-badge{margin-top:0;white-space:nowrap}.ge-badge.ge-act{border:1px solid currentColor;font-size:10.5px}.ge-dact{display:flex;gap:8px;margin-top:12px}
  .ge-outc{padding:10px 14px}.ge-oc{display:flex;align-items:center;gap:10px 22px;flex-wrap:wrap}
  .ge-oc-a,.ge-oc-b{display:flex;align-items:center;gap:6px 12px;flex-wrap:wrap;font-size:12.5px}.ge-oc small{font-size:10.5px;text-transform:uppercase;letter-spacing:.08em;color:var(--text-3)}
  .ge-oc-l{font-size:17px}.ge-out.bull .ge-oc-l{color:var(--up)}.ge-out.bear .ge-oc-l{color:var(--down)}.ge-oc-c{font-size:11.5px;color:var(--text-3)}
  .ge-meter-s{display:inline-block;flex:0 0 110px;min-width:110px;height:6px;margin:0}.ge-meter-s i{width:11px;height:11px;margin:-5.5px 0 0 -5.5px}
  .ge-oc-b b{font-size:13px}.ge-oc-t{margin-left:auto;border:1px solid var(--line);background:var(--panel);color:var(--text-2);border-radius:8px;padding:5px 10px;font-size:12px;cursor:pointer}
  .ge-chips{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}.ge-chip{font-size:11.5px;padding:3px 8px;border-radius:12px;background:var(--panel-2,rgba(255,255,255,.06));color:var(--text-2)}
  .ge-chip.up b{color:var(--up)}.ge-chip.down b{color:var(--down)}
  .ge-cards-w{margin-bottom:12px}.ge-grid4{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
  @media (max-width:1100px){.ge-grid4{grid-template-columns:repeat(2,minmax(0,1fr))}}
  @media (max-width:640px){.ge-grid4{grid-template-columns:1fr}.ge-oc-t{margin-left:0}.ge-chips{display:none}}   /* phones: the chips are in 'Why' */
  .ge-sl{min-height:300px}.ge.ge-pkbar{padding-bottom:0}.ge-pkbar .ge-tabs{margin:0 0 10px}.ge-grid3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.ge-grid3 .ge-qr{grid-template-columns:minmax(0,1fr) auto auto}
  .ge-mvpg{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:8px;font-size:12px}
  @media (max-width:980px){.ge-grid3{grid-template-columns:1fr}}.ge .gl-wrap{margin-bottom:12px}
  body.ge-noscroll{overflow:hidden}
  /* terminal look from the UI kit: mono numbers, accent bar on cards, corner bracket on panels */
  .ge .ge-cs,.ge .ge-big,.ge-sum4 b,.ge-stand em,.ge-dn1,.ge-ring b{font-family:'DM Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;letter-spacing:-.5px}
  .ge-card{border-top-width:1px;overflow:hidden}.ge-card::before{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--text-3)}
  .ge-card.bull::before{background:var(--up)}.ge-card.bear::before{background:var(--down)}.ge-card.bear{border-color:color-mix(in srgb,var(--down) 45%,var(--line))}.ge-card.bull{border-color:color-mix(in srgb,var(--up) 40%,var(--line))}
  .ge-p{position:relative}.ge-p::before{content:'';position:absolute;left:-1px;top:-1px;width:12px;height:12px;border-left:2px solid var(--ge-cy);border-top:2px solid var(--ge-cy);border-top-left-radius:12px;opacity:.8;pointer-events:none}
  .ge-p h3{text-transform:uppercase;letter-spacing:.06em;font-size:11.5px;color:var(--text-2,inherit)}
  .ge-tick{display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;padding:2px 0 8px;margin-bottom:4px}.ge-tick::-webkit-scrollbar{display:none}
  .ge-tk{flex:0 0 auto;display:flex;gap:8px;align-items:baseline;padding:6px 10px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text);cursor:pointer;font-size:12px;white-space:nowrap}
  .ge-tk b{font-size:11px;letter-spacing:.04em}
  /* light theme: same layout, darker accent so cyan text keeps its contrast on white */
  :root[data-theme="light"] .ge{--ge-cy:#0e7490}
  :root[data-theme="light"] .ge-card.bull{background:linear-gradient(180deg,color-mix(in srgb,var(--up) 7%,var(--panel)),var(--panel))}
  :root[data-theme="light"] .ge-card.bear{background:linear-gradient(180deg,color-mix(in srgb,var(--down) 7%,var(--panel)),var(--panel))}
  :root[data-theme="light"] .ge-dbg{background:rgba(15,23,42,.35)}
  :root[data-theme="light"] .ge-det{background:var(--panel);box-shadow:-12px 0 40px rgba(15,23,42,.18)}
  :root[data-theme="light"] .ge-out{background:linear-gradient(135deg,color-mix(in srgb,var(--ge-cy) 6%,var(--panel)),var(--panel))}
  .ge-tabs{flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none;margin-bottom:8px}.ge-tabs::-webkit-scrollbar{display:none}
  .ge-sub2{display:flex;gap:4px;overflow-x:auto;scrollbar-width:none;margin:0 0 12px;padding-bottom:2px;border-bottom:1px solid var(--line)}.ge-sub2::-webkit-scrollbar{display:none}
  .ge-sub2 button{flex:0 0 auto;padding:7px 12px;border:0;background:none;color:var(--text-2,inherit);font-weight:600;font-size:13px;cursor:pointer;border-bottom:2px solid transparent}
  .ge-sub2 button.on{color:var(--text);border-bottom-color:var(--ge-cy)}
  .ge-pk{display:grid;grid-template-columns:minmax(0,1fr) auto 92px minmax(0,1.3fr);gap:10px;align-items:center;width:100%;padding:8px 2px;border:0;border-bottom:1px solid var(--line);background:none;color:var(--text);cursor:pointer;text-align:left;font-size:13px}
  .ge-pk:last-child{border-bottom:0}.ge-pk:hover{background:var(--panel-2)}
  .ge-pkp{display:flex;flex-direction:column;align-items:flex-end}.ge-pkp small{font-size:11px}
  .ge-pkl{display:flex;flex-wrap:wrap;gap:2px 6px;align-items:baseline;justify-content:flex-end;font-size:12px}.ge-pkl small{font-size:10px;color:var(--text-3)}.ge-pkl em{font-style:normal}
  .ge-grid2 .ge-pk{grid-template-columns:minmax(0,1fr) auto 88px}.ge-grid2 .ge-pkl{display:none}
  @media (max-width:640px){.ge-tabs{flex-wrap:wrap}.ge-pk{grid-template-columns:minmax(0,1fr) auto 80px}.ge-pkl{grid-column:1/-1;justify-content:flex-start}.ge-tabs button{padding:6px 11px}}
  .ge-stocks{margin-top:12px}.ge-stocks h3 small{font-weight:500;margin-left:6px}
  .ge-secchips{display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;padding-bottom:4px;margin-bottom:8px}.ge-secchips::-webkit-scrollbar{display:none}
  .ge-secchips button{flex:0 0 auto;display:flex;align-items:center;gap:6px;padding:5px 10px;border-radius:999px;border:1px solid var(--line);background:var(--panel);color:var(--text-2,inherit);font-size:12px;cursor:pointer;white-space:nowrap}
  .ge-secchips button.on{border-color:var(--ge-cy);color:var(--text);box-shadow:0 0 0 1px var(--ge-cy) inset}.ge-secchips i,.ge-sc i,.ge-leg i,.ge-dot{display:inline-block;width:9px;height:9px;border-radius:50%;flex:0 0 auto}
  .ge-dot{margin-right:6px}.ge-secchips small{font-size:11px;color:var(--text-3)}.ge-secchips small.up{color:var(--up)}.ge-secchips small.down{color:var(--down)}
  .ge-stools{display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap}.ge-stools .inp{flex:1 1 180px;max-width:320px}.ge-stools select.inp{flex:0 1 180px}
  .ge-stk td{vertical-align:middle}.ge-stk td small{display:block;font-size:10.5px;color:var(--text-3);max-width:190px;overflow:hidden;text-overflow:ellipsis}
  .ge-stk tr[data-gestock]{cursor:pointer}.ge-stk tr[data-gestock]:hover td{background:var(--panel-2)}
  .ge-stk th:first-child,.ge-stk td:first-child{position:sticky;left:0;background:var(--panel);z-index:1}
  .ge-sc{font-size:11.5px;color:var(--text-2);white-space:nowrap}.ge-sc i{margin-right:5px}
  .ge-rgm{position:relative;display:inline-block;width:64px;height:5px;border-radius:3px;background:var(--line);vertical-align:middle}.ge-rgm b{position:absolute;top:-3px;width:3px;height:11px;border-radius:2px;background:var(--ge-cy);transform:translateX(-50%)}
  .ge-opp{position:relative;display:inline-flex;align-items:center;width:74px;height:18px;border-radius:5px;background:var(--panel-2,rgba(255,255,255,.06));overflow:hidden}
  .ge-opp i{position:absolute;left:0;top:0;bottom:0;opacity:.35}.ge-opp b{position:relative;margin-left:auto;margin-right:6px;font-size:11.5px}
  .ge-opp.hi i{background:var(--up)}.ge-opp.mid i{background:var(--warn,#f5b942)}.ge-opp.lo i{background:var(--down)}
  .ge-more2{display:flex;justify-content:space-between;align-items:center;margin-top:8px;font-size:12px}
  .ge-sum4{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:12px}.ge-sum4>div{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:10px 14px}
  .ge-sum4 small{display:flex;align-items:center;gap:4px;font-size:10.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--text-3)}.ge-sum4 b{font-size:22px;color:var(--ge-cy)}
  .ge-secgrid{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);gap:12px;margin-bottom:12px}
  .ge-dwrap{display:flex;gap:14px;align-items:flex-start}.ge-donut{width:200px;height:200px;flex:0 0 200px}.ge-donut path{cursor:pointer;stroke:var(--panel);stroke-width:1}
  .ge-dn1{font-size:26px;font-weight:800;fill:var(--text)}.ge-dn2{font-size:10px;fill:var(--text-3)}
  .ge-leg{flex:1;min-width:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:2px 10px;max-height:330px;overflow-y:auto}
  .ge-leg button{display:grid;grid-template-columns:10px 1fr auto auto;gap:6px;align-items:center;padding:4px 6px;border:0;border-radius:6px;background:none;color:var(--text-2,inherit);font-size:12px;cursor:pointer;text-align:left}
  .ge-leg button span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.ge-leg button.on{background:var(--panel-2)}.ge-leg em{font-style:normal;font-size:11px}
  .ge-secd h3{font-size:15px}.ge-secd h4,.ge-det h4{margin:12px 0 4px;font-size:12.5px;display:flex;align-items:center;gap:4px}.ge-secd .btn-xs{margin-top:10px}
  .ge-h3{font-size:14px;margin:4px 2px 8px}.ge-stands{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:8px}
  .ge-stand{display:flex;flex-direction:column;gap:2px;text-align:left;padding:12px 14px;border:1px solid var(--line);border-radius:12px;background:linear-gradient(135deg,color-mix(in srgb,var(--ge-cy) 8%,var(--panel)),var(--panel));color:var(--text);cursor:pointer}
  .ge-stand small{font-size:10.5px;text-transform:uppercase;letter-spacing:.06em;color:var(--ge-cy)}.ge-stand b{font-size:16px}.ge-stand em{font-style:normal;font-size:20px;font-weight:800}.ge-stand .muted{font-size:11.5px}
  @media (max-width:1100px){.ge-stands{grid-template-columns:repeat(2,minmax(0,1fr))}.ge-secgrid{grid-template-columns:1fr}}
  @media (max-width:640px){.ge-sum4{grid-template-columns:repeat(2,minmax(0,1fr))}.ge-sum4 b{font-size:18px}.ge-dwrap{flex-direction:column;align-items:center}.ge-donut{width:180px;height:180px;flex-basis:auto}.ge-leg{width:100%;grid-template-columns:1fr 1fr;max-height:none}.ge-stands{grid-template-columns:1fr}.ge-stools .inp,.ge-stools select.inp{max-width:none}}
  .ge .up{color:var(--up)}.ge .down{color:var(--down)}.ge .bull{}.ge b.bull,.ge-sub b.bull{color:var(--up)}.ge b.bear,.ge-sub b.bear{color:var(--down)}
  @media (max-width:1280px){.ge-grid3{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}.ge-cards{grid-column:1/-1;order:-1}.ge-cards{grid-template-columns:repeat(5,minmax(0,1fr))}}
  @media (max-width:900px){.ge-cards{grid-template-columns:repeat(3,minmax(0,1fr))}.ge-parts{grid-template-columns:1fr}}
  @media (max-width:640px){.ge-grid3,.ge-grid2,.ge-2{grid-template-columns:1fr}.ge-cards{grid-template-columns:repeat(2,minmax(0,1fr))}.ge-brand h1{font-size:20px}.ge-brand h1 span{font-size:14px}
    .ge-part{grid-template-columns:110px 1fr 40px}.ge-cs{font-size:24px}.ge-kv{grid-template-columns:repeat(2,1fr)}.ge-row{grid-template-columns:86px 1fr auto}.ge-head{align-items:flex-start}}
  `;
  const st = document.createElement('style'); st.id = 'ge-css'; st.textContent = css; document.head.appendChild(st);
})();
