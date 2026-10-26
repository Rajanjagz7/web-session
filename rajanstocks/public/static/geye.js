/* GOD'S EYE tab - FII / DII money flows, participant positioning, options OI and the next-day / expiry read-out,
   with the market signal cards. Data: /api/ge/dashboard (gods_eye_tab.py). Every derived number carries its rule
   (hover / tap the ⓘ). Missing inputs show "N/A", never 0. Informational only - not investment advice. */
(function () {
  'use strict';
  const E = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const LS = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const SS = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { } };
  const G = { data: LS('ge-cache', null), busy: false, err: null, ts: 0, seq: 0, tab: LS('ge-tab', 'overview'), open: null, sort: 'score', filt: 'ALL', opt: null, optExp: '' };
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
  const colOf = l => l === 'BULLISH' ? 'var(--up,#22ab94)' : l === 'BEARISH' ? 'var(--down,#f7525f)' : 'var(--text-3,#8a93a6)';
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
    if (my === G.seq) { G.busy = false; paint(); }
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
    return `<div class="ge-tick" role="list">${cards.map(c => `<button type="button" class="ge-tk" role="listitem" data-gecard="${E(c.key)}"><b>${E(c.name || c.key)}</b>
      <span class="num">${isN(c.price) ? n2(c.price, c.price >= 1000 ? 1 : 2) : NA}</span><span class="num ${cc(c.chgPct)}">${pc(c.chgPct)}</span></button>`).join('')}</div>`;
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
        <div class="ge-oc-a"><small>Next day</small><b class="ge-oc-l">${E(o.label)} <span class="num">${sg(o.score)}</span></b>${tip('outlook')}
          <i class="ge-meter ge-meter-s" aria-label="Score ${sg(o.score)} on -10 to +10"><i style="left:${pos}%"></i></i><span class="ge-oc-c">${E(o.confidence)} · ${o.agree}/${o.of} agree</span></div>
        ${x && opt ? `<div class="ge-oc-b"><small>Expiry ${E(dShort(x.expiry))}${left ? ' · ' + left : ''}</small>
          <span>Range <b class="num">${opt.range ? n0(opt.range[0]) + '–' + n0(opt.range[1]) : NA}</b></span><span>Put wall <b class="num up">${n0(opt.putWall)}</b></span><span>Max pain <b class="num">${n0(opt.maxPain)}</b></span><span>Call wall <b class="num down">${n0(opt.callWall)}</b></span></div>` : ''}
        <button type="button" class="ge-oc-t" data-geout="1" aria-expanded="${open}">${open ? 'Hide details ▴' : 'Why ▾'}</button>
      </div>
      <div class="ge-chips">${o.parts.map(p => `<span class="ge-chip ${cc(p.pts)}" title="${E(p.why)}">${E(p.name)} <b class="num">${sg(p.pts)}</b></span>`).join('')}</div>
      ${open ? `<div class="ge-parts">${o.parts.map(p => `<div class="ge-part"><span>${E(p.name)}</span><i class="ge-pb"><b class="${p.pts >= 0 ? 'up' : 'down'}" style="width:${Math.min(50, Math.abs(p.pts) / 3 * 50)}%;${p.pts >= 0 ? 'left:50%' : 'right:50%'}"></b></i><em class="num ${cc(p.pts)}">${sg(p.pts)}</em><small>${E(p.why)}</small></div>`).join('')}</div>
        ${x ? `<div class="ge-exp"><h4>Expiry ${E(dShort(x.expiry))}${tip('expected')}</h4><ul>${x.lines.map(l => `<li>${E(l)}</li>`).join('')}</ul></div>` : ''}` : ''}
    </section>`;
  }

  function overview(d) {
    return `${outlookBlock(d.outlook, d.expiry, d.options)}
      <div class="ge-cards ge-cards-w">${(d.cards || []).map(card).join('')}</div>
      <div class="ge-grid4">${pOptionsOI(d.options)}${pPCR(d.options)}${pRetail(d.positioning)}${pInst(d.positioning)}</div>`;
  }

  function fiiTab(d) {
    const c = d.cash, p = d.positioning;
    const flows = c ? (() => {
      const days = c.days || [], m = Math.max(1, ...days.map(x => Math.max(Math.abs(x.fii || 0), Math.abs(x.dii || 0))));
      return `<section class="ge-p"><h3>FII / DII cash market · ${E(dShort(c.date))}${tip('cash')}</h3>
        <div class="ge-tw"><table class="ge-t"><thead><tr><th></th><th class="r">Buy</th><th class="r">Sell</th><th class="r">Net</th><th class="r">5 days</th><th class="r">20 days</th></tr></thead><tbody>
          <tr><td><b>FII / FPI</b></td><td class="r num">${n0(c.fii.buy)}</td><td class="r num">${n0(c.fii.sell)}</td><td class="r num ${cc(c.fii.net)}"><b>${cr(c.fii.net)}</b></td><td class="r num ${cc(c.fii5)}">${cr(c.fii5)}</td><td class="r num ${cc(c.fii20)}">${cr(c.fii20)}</td></tr>
          <tr><td><b>DII</b></td><td class="r num">${n0(c.dii.buy)}</td><td class="r num">${n0(c.dii.sell)}</td><td class="r num ${cc(c.dii.net)}"><b>${cr(c.dii.net)}</b></td><td class="r num ${cc(c.dii5)}">${cr(c.dii5)}</td><td class="r num ${cc(c.dii20)}">${cr(c.dii20)}</td></tr>
          <tr><td>Combined</td><td></td><td></td><td class="r num ${cc(c.combined)}"><b>${cr(c.combined)}</b></td><td colspan="2" class="r muted">FII ${E(c.fiiStreak.side)} ${c.fiiStreak.days} day${c.fiiStreak.days > 1 ? 's' : ''} in a row</td></tr>
        </tbody></table></div>
        <div class="ge-flows" aria-label="FII and DII net, last ${days.length} sessions">${days.map(x => `<div class="ge-fd" title="${E(x.date)} · FII ${cr(x.fii)} · DII ${cr(x.dii)}"><i class="f ${x.fii >= 0 ? 'up' : 'down'}" style="height:${Math.abs(x.fii || 0) / m * 100}%"></i><i class="d ${x.dii >= 0 ? 'up' : 'down'}" style="height:${Math.abs(x.dii || 0) / m * 100}%"></i><small>${E(dShort(x.date))}</small></div>`).join('')}</div>
        <p class="ge-sub"><span class="ge-key f"></span>FII <span class="ge-key d"></span>DII · Rs crore, NSE provisional · ${c.sessions} session${c.sessions === 1 ? '' : 's'} stored so far (one is added every trading day; 5 / 20-day totals appear once there are enough)</p></section>`;
    })() : `<section class="ge-p"><h3>FII / DII cash market</h3><p class="ge-na">N/A - not published yet</p></section>`;
    const parts = p ? `<section class="ge-p"><h3>Participant positioning · index F&O · ${E(dShort(p.date))}${tip('fiiFutures')}</h3>
      <div class="ge-tw"><table class="ge-t"><thead><tr><th>Who</th><th class="r">Fut long %</th><th class="r">Fut net</th><th class="r">Δ vs ${E(dShort(p.prevDate || ''))}</th><th class="r">Call net</th><th class="r">Put net</th></tr></thead><tbody>
      ${p.participants.map(x => `<tr><td><b>${E(x.who)}</b></td><td class="r num">${isN(x.futLongPct) ? x.futLongPct + '%' : NA}</td><td class="r num ${cc(x.futNet)}">${sg(x.futNet, 0)}</td><td class="r num ${cc(x.futNetChg)}">${sg(x.futNetChg, 0)}</td><td class="r num ${cc(x.callNet)}">${sg(x.callNet, 0)}</td><td class="r num ${cc(x.putNet)}">${sg(x.putNet, 0)}</td></tr>`).join('')}
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

  function sigTab(d) {
    let list = (d.cards || []).filter(c => isN(c.score) && (G.filt === 'ALL' || c.label === G.filt));
    list = list.slice().sort((a, b) => G.sort === 'name' ? String(a.name).localeCompare(b.name) : (b.score - a.score));
    return `<div class="ge-bar2"><div class="ge-seg">${['ALL', 'BULLISH', 'NEUTRAL', 'BEARISH'].map(f => `<button type="button" class="${G.filt === f ? 'on' : ''}" data-gefilt="${f}">${f[0] + f.slice(1).toLowerCase()}</button>`).join('')}</div>
      <div class="ge-seg">${[['score', 'By score'], ['name', 'By name']].map(([k, l]) => `<button type="button" class="${G.sort === k ? 'on' : ''}" data-gesort="${k}">${l}</button>`).join('')}</div></div>
      <section class="ge-p"><div class="ge-tw"><table class="ge-t ge-sig"><thead><tr><th>Instrument</th><th class="r">Score</th><th>Signal</th><th class="r">Price</th><th class="r">Change</th><th>Action</th></tr></thead><tbody>
      ${list.map(c => `<tr data-gecard="${E(c.key)}" tabindex="0"><td><b>${E(c.name)}</b>${c.divergence ? ' <small class="' + (c.divergence === 'BULLISH' ? 'up' : 'down') + '">⚡ div</small>' : ''}</td><td class="r num ${cc(c.score)}"><b>${sg(c.score)}</b></td>
        <td><span class="ge-badge ${lab(c.label)}">${E(c.label)}</span></td><td class="r num">${isN(c.price) ? n2(c.price, c.price >= 1000 ? 1 : 2) : NA}</td><td class="r num ${cc(c.chgPct)}">${pc(c.chgPct)}</td><td>${c.action ? E(c.action.label) : '—'}</td></tr>`).join('') || '<tr><td colspan="6" class="muted">No instruments match.</td></tr>'}
      </tbody></table></div></section>`;
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
  function host() { return typeof App !== 'undefined' && App.view === 'godseye' ? document.getElementById('v-godseye') : null; }
  function paint() {
    const el = host(); if (!el) return;
    const d = G.data;
    const tabs = [['overview', 'Overview'], ['fii', 'FII / DII'], ['options', 'Options & Expiry'], ['signals', 'Signals']];
    let body;
    if (!d) body = G.err ? `<div class="ge-p"><p class="ge-na">God's Eye is unavailable: ${E(G.err)}</p><button class="btn" data-gerefresh="1">Retry</button></div>`
      : `<div class="ge-cards">${'<article class="ge-card ge-skel"></article>'.repeat(10)}</div><p class="muted">Reading markets, FII / DII and option data…</p>`;
    else body = ({ overview, fii: fiiTab, options: optTab, signals: sigTab }[G.tab] || overview)(d);
    el.innerHTML = `<div class="page ge">
      <div class="ge-head"><div class="ge-brand"><svg viewBox="0 0 48 28" class="ge-eye" aria-hidden="true"><path d="M2 14C9 4 39 4 46 14C39 24 9 24 2 14Z" fill="none" stroke="currentColor" stroke-width="3"/><circle cx="24" cy="14" r="6" fill="none" stroke="currentColor" stroke-width="3"/><circle cx="24" cy="14" r="2.2" fill="currentColor"/></svg>
        <div><h1>THE GOD'S EYE <span>– OBSERVER</span></h1><p>FII / DII · positioning · options · signals</p></div></div>
        <div class="ge-st">${status()}<span class="ge-upd">${G.busy ? 'Updating…' : d ? 'Updated ' + E(IST(d.asOf)) : ''}</span><button type="button" class="ge-ref" data-gerefresh="1" aria-label="Refresh" ${G.busy ? 'disabled' : ''}>↻</button></div></div>
      ${d ? ticker(d.cards || []) : ''}
      ${G.err && d ? `<p class="ge-warn">Last refresh failed (${E(G.err)}) - showing data from ${E(IST(d.asOf))}.</p>` : ''}
      <div class="ge-tabs" role="tablist">${tabs.map(([k, l]) => `<button type="button" role="tab" aria-selected="${G.tab === k}" class="${G.tab === k ? 'on' : ''}" data-getab="${k}">${l}</button>`).join('')}</div>
      ${body}
      <p class="ge-disc">Informational only - built from public NSE data, broker quotes and rule-based scores; not a forecast or investment advice.</p>
      ${G.open ? detail() : ''}</div>`;
    document.body.classList.toggle('ge-noscroll', !!G.open);
  }
  window.renderGodsEyeTab = function () { paint(); if (!G.data || Date.now() - G.ts > 60e3) load(false); };
  /* Picks shows a one-line summary only - the full God's Eye lives in its own tab (no duplicate screen) */
  window.geStrip = function (el) {
    if (!el) return;
    const draw = items => {
      const list = (items || []).filter(c => isN(c.score));
      el.innerHTML = `<button type="button" class="ge-strip" data-geopen="1" aria-label="Open God's Eye"><span class="ge-strip-h"><svg viewBox="0 0 48 28" class="ge-eye" aria-hidden="true"><path d="M2 14C9 4 39 4 46 14C39 24 9 24 2 14Z" fill="none" stroke="currentColor" stroke-width="3"/><circle cx="24" cy="14" r="6" fill="none" stroke="currentColor" stroke-width="3"/></svg>GOD'S EYE</span>
        <span class="ge-strip-l">${list.length ? list.map(c => `<span class="${lab(c.label)}"><b>${E(c.name)}</b> <em class="num">${sg(c.score)}</em></span>`).join('') : '<span class="muted">Loading…</span>'}</span><span class="ge-strip-go">Open ›</span></button>`;
    };
    draw(G.data && G.data.cards);
    if (!G.data || Date.now() - G.ts > 300e3) fetch('/api/observer').then(r => r.ok ? r.json() : null).then(d => { if (d && d.items && document.body.contains(el)) draw((G.data && G.data.cards) || d.items); }).catch(() => { });
  };
  document.addEventListener('click', e => { if (e.target.closest('[data-geopen]') && typeof go === 'function') go('godseye'); });

  document.addEventListener('click', e => {
    if (!e.target.closest('#v-godseye')) return;
    const t = e.target, q = s => t.closest(s);
    const cl = q('[data-geclose]');
    if (cl && (cl.tagName === 'BUTTON' || t === cl)) { G.open = null; return paint(); }   // the backdrop itself or a close button - not every button inside the drawer
    if (q('.ge-det')) { const ch = q('[data-gechart]'); if (ch) openChart(ch.dataset.gechart); return; }
    const c = q('[data-gecard]'); if (c) { G.open = c.dataset.gecard; return paint(); }
    if (q('[data-geout]')) { G.outOpen = !G.outOpen; return paint(); }
    const tb = q('[data-getab]'); if (tb) { G.tab = tb.dataset.getab; SS('ge-tab', G.tab); return paint(); }
    if (q('[data-gerefresh]')) return load(true);
    const ex = q('[data-geexp]'); if (ex) return loadOpt(ex.dataset.geexp);
    const f = q('[data-gefilt]'); if (f) { G.filt = f.dataset.gefilt; return paint(); }
    const s = q('[data-gesort]'); if (s) { G.sort = s.dataset.gesort; return paint(); }
    if (q('[data-gechain]') && typeof go === 'function') { try { OPT.sym = 'NIFTY'; OPT.expiry = G.optExp || ''; OPT.chain = null; OPT.sel = null; OPT.osym = null; } catch (x) { } go('options'); }
    const tp = q('[data-getip]'); if (tp && typeof toast === 'function') toast(tp.title, 'info');
  });
  document.addEventListener('keydown', e => {
    if (!host()) return;
    if (e.key === 'Escape' && G.open) { G.open = null; paint(); }
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
    if (!host() || document.hidden || G.busy) return;
    const open = typeof MKT !== 'undefined' && MKT.open;
    if (Date.now() - G.ts > (open ? 60e3 : 300e3)) load(false);
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
  .ge-ref{width:34px;height:34px;border-radius:50%;border:1px solid var(--line);background:var(--panel);color:var(--text);cursor:pointer;font-size:16px}
  .ge-tick{display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;padding:2px 0 8px;margin-bottom:6px}
  .ge-tk{flex:0 0 auto;display:flex;gap:8px;align-items:baseline;padding:7px 11px;border-radius:9px;border:1px solid var(--line);background:var(--panel);color:var(--text);cursor:pointer;font-size:12.5px;white-space:nowrap}
  .ge-tk b{font-size:11.5px;letter-spacing:.04em}
  .ge-tabs{display:flex;gap:6px;overflow-x:auto;scrollbar-width:none;margin:4px 0 12px;border-bottom:1px solid var(--line)}
  .ge-tabs button{flex:0 0 auto;padding:9px 14px;border:0;background:none;color:var(--text-2,inherit);font-weight:600;font-size:13.5px;cursor:pointer;border-bottom:2px solid transparent}
  .ge-tabs button.on{color:var(--text);border-bottom-color:var(--ge-cy)}
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
  .ge-flows{display:flex;gap:3px;align-items:flex-end;height:110px;margin-top:12px;overflow-x:auto}
  .ge-fd{flex:1 0 22px;display:grid;grid-template-columns:1fr 1fr;grid-template-rows:1fr auto;gap:1px;align-items:end;height:100%}
  .ge-fd i{display:block;border-radius:2px 2px 0 0;min-height:1px}.ge-fd i.f.up{background:var(--brand)}.ge-fd i.f.down{background:color-mix(in srgb,var(--brand) 45%,var(--down))}
  .ge-fd i.d.up{background:var(--ge-cy)}.ge-fd i.d.down{background:color-mix(in srgb,var(--ge-cy) 40%,var(--down))}.ge-fd small{grid-column:1/-1;font-size:9px;color:var(--text-3);text-align:center;white-space:nowrap}
  .ge-key{display:inline-block;width:10px;height:10px;border-radius:2px;margin:0 4px 0 8px;vertical-align:-1px}.ge-key.f{background:var(--brand)}.ge-key.d{background:var(--ge-cy)}
  .ge-seg{display:inline-flex;gap:4px;flex-wrap:wrap;margin-bottom:10px}.ge-seg button{padding:6px 12px;border-radius:8px;border:1px solid var(--line);background:var(--panel);color:var(--text-2,inherit);font-size:12.5px;cursor:pointer}
  .ge-seg button.on{background:var(--brand);border-color:var(--brand);color:#fff}.ge-bar2{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap}
  .ge-sched,.ge-disc{font-size:11.5px;color:var(--text-3);margin:10px 2px}.ge-warn{font-size:12px;color:var(--warn,#f5b942);margin:0 0 8px}
  .ge-dbg{position:fixed;inset:0;z-index:300;background:rgba(0,0,0,.55);display:flex;justify-content:flex-end}
  .ge-det{width:min(560px,100%);height:100%;overflow-y:auto;background:var(--bg,#0b0e14);border-left:1px solid var(--line);padding:18px 18px 40px}
  .ge-dh{display:flex;justify-content:space-between;gap:10px}.ge-dh h3{margin:2px 0;font-size:20px;display:flex;gap:8px;align-items:center}.ge-dh small{font-size:11px;color:var(--text-3)}
  .ge-x{width:36px;height:36px;border-radius:50%;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:20px;cursor:pointer}
  .ge-det .ge-spark{height:120px;margin:10px 0}.ge-kv{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:8px 0}.ge-kv small{display:block;font-size:10.5px;color:var(--text-3)}
  .ge-play{border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin:10px 0}.ge-play.bull{border-color:color-mix(in srgb,var(--up) 50%,var(--line))}.ge-play.bear{border-color:color-mix(in srgb,var(--down) 50%,var(--line))}
  .ge-play b{display:block}.ge-play span{font-size:12px;color:var(--text-2)}.ge-dact{display:flex;gap:8px;margin-top:12px}
  .ge-outc{padding:10px 14px}.ge-oc{display:flex;align-items:center;gap:10px 22px;flex-wrap:wrap}
  .ge-oc-a,.ge-oc-b{display:flex;align-items:center;gap:6px 12px;flex-wrap:wrap;font-size:12.5px}.ge-oc small{font-size:10.5px;text-transform:uppercase;letter-spacing:.08em;color:var(--text-3)}
  .ge-oc-l{font-size:17px}.ge-out.bull .ge-oc-l{color:var(--up)}.ge-out.bear .ge-oc-l{color:var(--down)}.ge-oc-c{font-size:11.5px;color:var(--text-3)}
  .ge-meter-s{display:inline-block;flex:0 0 110px;min-width:110px;height:6px;margin:0}.ge-meter-s i{width:11px;height:11px;margin:-5.5px 0 0 -5.5px}
  .ge-oc-b b{font-size:13px}.ge-oc-t{margin-left:auto;border:1px solid var(--line);background:var(--panel);color:var(--text-2);border-radius:8px;padding:5px 10px;font-size:12px;cursor:pointer}
  .ge-chips{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}.ge-chip{font-size:11.5px;padding:3px 8px;border-radius:12px;background:var(--panel-2,rgba(255,255,255,.06));color:var(--text-2)}
  .ge-chip.up b{color:var(--up)}.ge-chip.down b{color:var(--down)}
  .ge-cards-w{margin-bottom:12px}.ge-grid4{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
  @media (max-width:1100px){.ge-grid4{grid-template-columns:repeat(2,minmax(0,1fr))}}
  .ge-tick::-webkit-scrollbar{display:none}
  @media (max-width:640px){.ge-grid4{grid-template-columns:1fr}.ge-oc-t{margin-left:0}.ge-chips{display:none}}   /* phones: the chips are in 'Why' */
  body.ge-noscroll{overflow:hidden}
  .ge-strip{display:flex;align-items:center;gap:12px;width:100%;padding:10px 14px;margin:6px 0 12px;border:1px solid var(--line);border-radius:12px;background:var(--panel);color:var(--text);cursor:pointer;text-align:left}
  .ge-strip:hover{border-color:#22d3ee}.ge-strip-h{display:flex;align-items:center;gap:6px;font-weight:800;font-size:12.5px;letter-spacing:.06em;color:#22d3ee;flex:0 0 auto}.ge-strip .ge-eye{width:26px;height:16px;color:#22d3ee}
  .ge-strip-l{display:flex;gap:14px;overflow-x:auto;scrollbar-width:none;flex:1;font-size:12px}.ge-strip-l span{white-space:nowrap}.ge-strip-l em{font-style:normal;font-weight:700}
  .ge-strip-l .bull em{color:var(--up)}.ge-strip-l .bear em{color:var(--down)}.ge-strip-go{flex:0 0 auto;font-size:12px;font-weight:700;color:var(--brand)}
  .ge .up{color:var(--up)}.ge .down{color:var(--down)}.ge .bull{}.ge b.bull,.ge-sub b.bull{color:var(--up)}.ge b.bear,.ge-sub b.bear{color:var(--down)}
  @media (max-width:1280px){.ge-grid3{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}.ge-cards{grid-column:1/-1;order:-1}.ge-cards{grid-template-columns:repeat(5,minmax(0,1fr))}}
  @media (max-width:900px){.ge-cards{grid-template-columns:repeat(3,minmax(0,1fr))}.ge-parts{grid-template-columns:1fr}}
  @media (max-width:640px){.ge-grid3,.ge-grid2,.ge-2{grid-template-columns:1fr}.ge-cards{grid-template-columns:repeat(2,minmax(0,1fr))}.ge-brand h1{font-size:20px}.ge-brand h1 span{font-size:14px}
    .ge-part{grid-template-columns:110px 1fr 40px}.ge-cs{font-size:24px}.ge-kv{grid-template-columns:repeat(2,1fr)}.ge-row{grid-template-columns:86px 1fr auto}.ge-head{align-items:flex-start}}
  `;
  const st = document.createElement('style'); st.id = 'ge-css'; st.textContent = css; document.head.appendChild(st);
})();
