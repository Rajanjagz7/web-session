/* GOD'S EYE — The Observer.
   One score per market (-10 .. +10) from real daily price history: trend, momentum, MACD, 5-day move and
   place in the 20-day range, all ATR-normalised; bias BULLISH >= +2.5, BEARISH <= -2.5; RSI divergence flag.
   Data: /api/godseye/board (gods_eye_board.py). Informational only — not a forecast or advice. */
(function () {
  'use strict';
  const E = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const LS = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const SS = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const G = { data: LS('gx-cache', null), busy: false, err: null, ts: 0, view: LS('gx-view', 'cards'), grp: LS('gx-grp', 'All'), open: null, how: false };

  const num = (v, d = 2) => v == null || isNaN(v) ? '—' : Number(v).toLocaleString('en-IN', { minimumFractionDigits: d, maximumFractionDigits: d });
  const pct = v => v == null || isNaN(v) ? '—' : (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(2) + '%';
  const sgn = v => (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(1);
  const bc = b => b === 'BULLISH' ? 'bull' : b === 'BEARISH' ? 'bear' : 'neu';
  const cc = v => v > 0 ? 'up' : v < 0 ? 'down' : '';
  const dp = it => it.price >= 1000 ? 2 : it.price >= 10 ? 2 : 4;

  function live(it) {  // overlay the app's live tick for Indian indices while NSE is open
    try {
      if (!it.app_sym || typeof SYM !== 'function' || typeof MKT === 'undefined' || !MKT.open) return it;
      const s = SYM(it.app_sym); if (!s || !(s.last > 0) || !(s.prev > 0)) return it;
      return Object.assign({}, it, { price: s.last, chg_pct: (s.last / s.prev - 1) * 100, liveTick: true });
    } catch (e) { return it; }
  }

  function spark(vals, w, h, col) {
    const v = (vals || []).filter(x => x != null); if (v.length < 2) return '';
    const lo = Math.min(...v), hi = Math.max(...v), r = hi - lo || 1;
    const pts = v.map((x, i) => `${(i / (v.length - 1) * (w - 4) + 2).toFixed(1)},${(h - 3 - (x - lo) / r * (h - 6)).toFixed(1)}`).join(' ');
    return `<svg class="gx-spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true"><polyline points="${pts}" fill="none" stroke="${col}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke"/></svg>`;
  }
  const colOf = b => b === 'BULLISH' ? 'var(--up)' : b === 'BEARISH' ? 'var(--down)' : 'var(--text-3)';

  /* ---------- data ---------- */
  async function load(force) {
    if (G.busy) return; G.busy = true; paint();
    try { G.data = await api('/api/godseye/board' + (force ? '?refresh=true' : '')); G.err = null; G.ts = Date.now(); SS('gx-cache', G.data); }
    catch (e) { G.err = 'Market data could not be loaded right now. Try Refresh in a minute.'; }
    G.busy = false; paint();
  }

  /* ---------- pieces ---------- */
  function card(raw) {
    if (!raw.ok) return `<div class="gx-card gx-off"><div class="gx-k">${E(raw.name)}</div><div class="gx-na">Data unavailable</div><small>${E(raw.error || '')}</small></div>`;
    const it = live(raw), c = bc(it.bias), dv = it.divergence;
    return `<button class="gx-card gx-${c}" data-gx="${E(it.key)}" aria-label="${E(it.name)} score ${sgn(it.score)} ${E(it.bias)}">
      <div class="gx-top"><span class="gx-k">${E(it.key)}</span><span class="gx-px num">${num(it.price, dp(it))} <em class="${cc(it.chg_pct)}">${pct(it.chg_pct)}</em></span></div>
      <div class="gx-score num">${sgn(it.score)}</div>
      <div class="gx-bias">${E(it.bias)}${it.strength === 'strong' ? ' · strong' : ''}</div>
      ${dv ? `<div class="gx-div ${dv.type}">⚡ ${dv.type === 'bearish' ? 'Bearish' : 'Bullish'} divergence</div>` : '<div class="gx-div none"></div>'}
      ${spark(it.spark, 160, 34, colOf(it.bias))}
      <div class="gx-more">Click for details ▸</div>
    </button>`;
  }

  function heatRow(raw) {
    if (!raw.ok) return `<tr><td><b>${E(raw.name)}</b></td><td colspan="7" class="muted">Data unavailable</td></tr>`;
    const it = live(raw), w = Math.min(50, Math.abs(it.score) * 5), ind = it.indicators;
    return `<tr data-gx="${E(it.key)}" class="gx-row">
      <td><b>${E(it.name)}</b><small>${E(it.group)}</small></td>
      <td class="r num">${num(it.price, dp(it))}<small class="${cc(it.chg_pct)}">${pct(it.chg_pct)}</small></td>
      <td class="gx-barc"><div class="gx-bar"><i class="${it.score >= 0 ? 'pos' : 'neg'} gx-${bc(it.bias)}" style="${it.score >= 0 ? 'left:50%' : 'right:50%'};width:${w}%"></i><span class="gx-mid"></span></div></td>
      <td class="r num gx-sc gx-t-${bc(it.bias)}">${sgn(it.score)}</td>
      <td><span class="gx-pill gx-${bc(it.bias)}">${E(it.bias)}</span></td>
      <td class="r num">${num(ind.rsi, 1)}</td>
      <td>${ind.ema20 >= ind.ema50 ? '<span class="up">Up</span>' : '<span class="down">Down</span>'}</td>
      <td>${it.divergence ? `<span class="gx-dv ${it.divergence.type}">⚡ ${it.divergence.type}</span>` : '<span class="muted">—</span>'}</td>
      <td>${spark(it.spark, 90, 26, colOf(it.bias))}</td></tr>`;
  }

  function gauge(score) {  // semicircle -10..+10
    const a = Math.PI * (1 - (Math.max(-10, Math.min(10, score)) + 10) / 20), cx = 90, cy = 86, r = 70;
    const x = cx + r * Math.cos(a), y = cy - r * Math.sin(a), arc = (f0, f1, col) => {
      const a0 = Math.PI * (1 - f0), a1 = Math.PI * (1 - f1);
      return `<path d="M${cx + r * Math.cos(a0)} ${cy - r * Math.sin(a0)} A${r} ${r} 0 0 1 ${cx + r * Math.cos(a1)} ${cy - r * Math.sin(a1)}" stroke="${col}" stroke-width="12" fill="none"/>`; };
    return `<svg viewBox="0 0 180 100" class="gx-gauge" aria-hidden="true">${arc(0, 0.375, 'var(--down)')}${arc(0.375, 0.625, 'var(--line)')}${arc(0.625, 1, 'var(--up)')}
      <line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" stroke="var(--text)" stroke-width="3" stroke-linecap="round"/><circle cx="${cx}" cy="${cy}" r="5" fill="var(--text)"/>
      <text x="16" y="98" class="gx-gt">−10</text><text x="164" y="98" text-anchor="end" class="gx-gt">+10</text></svg>`;
  }

  function histChart(h) {
    if (!h || h.length < 2) return '';
    const W = 340, H = 100, L = 26, n = h.length, X = i => L + i / (n - 1) * (W - L - 6), Y = v => 6 + (10 - v) / 20 * (H - 12);
    const line = h.map((v, i) => `${i ? 'L' : 'M'}${X(i).toFixed(1)} ${Y(v).toFixed(1)}`).join('');
    return `<svg viewBox="0 0 ${W} ${H}" class="gx-hist" aria-hidden="true">
      <rect x="${L}" y="${Y(10)}" width="${W - L - 6}" height="${Y(2.5) - Y(10)}" fill="var(--up)" opacity=".08"/><rect x="${L}" y="${Y(-2.5)}" width="${W - L - 6}" height="${Y(-10) - Y(-2.5)}" fill="var(--down)" opacity=".08"/>
      ${[10, 2.5, 0, -2.5, -10].map(v => `<line x1="${L}" x2="${W - 6}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--line)" ${v ? 'stroke-dasharray="3 3"' : ''}/><text x="${L - 4}" y="${Y(v) + 3.5}" text-anchor="end" class="gx-gt">${v > 0 ? '+' : ''}${v}</text>`).join('')}
      <path d="${line}" fill="none" stroke="var(--brand)" stroke-width="2"/><circle cx="${X(n - 1)}" cy="${Y(h[n - 1])}" r="3.5" fill="var(--brand)"/></svg>`;
  }

  function meaning(it) {
    const s = it.score, d = it.divergence, ind = it.indicators;
    let t = s >= 6 ? 'Strong uptrend: price, trend and momentum all agree.' : s >= 2.5 ? 'Leaning up: more signals point higher than lower.'
      : s <= -6 ? 'Strong downtrend: price, trend and momentum all agree.' : s <= -2.5 ? 'Leaning down: more signals point lower than higher.'
      : 'No clear edge: the signals are mixed, so the market is likely range-bound.';
    if (d) t += d.type === 'bearish' ? ' Watch the bearish divergence: the rally is losing momentum, which often comes before a pullback.' : ' Watch the bullish divergence: selling is losing force, which often comes before a bounce.';
    if (ind.rsi >= 70) t += ' RSI is overbought.'; else if (ind.rsi <= 30) t += ' RSI is oversold.';
    return t;
  }

  function detail() {
    const raw = ((G.data && G.data.items) || []).find(x => x.key === G.open); if (!raw || !raw.ok) return '';
    const it = live(raw), ind = it.indicators, r = ind.range20, prev = it.score_hist && it.score_hist.length > 5 ? it.score_hist[it.score_hist.length - 6] : null;
    return `<div class="gx-dbg" data-gxclose="1"><div class="gx-det" role="dialog" aria-modal="true" aria-label="${E(it.name)} details">
      <header><div><b>${E(it.name)}</b><small>${E(it.group)} · ${E(it.source)}${it.liveTick ? ' · live tick' : ''} · daily bars to ${E(it.as_of_bar)}</small></div><button class="ibtn" data-gxclose="1" aria-label="Close">✕</button></header>
      <div class="gx-dtop">
        <div class="gx-dg">${gauge(it.score)}<div class="gx-dgs num gx-t-${bc(it.bias)}">${sgn(it.score)}</div><div class="gx-dgb">${E(it.bias)} · ${E(it.strength)}</div></div>
        <div class="gx-dpx"><small>Price</small><b class="num">${num(it.price, dp(it))} ${E(it.currency || '')}</b><span class="${cc(it.chg_pct)}">${pct(it.chg_pct)} today</span>
          <div class="gx-dsp">${spark(it.spark, 300, 70, colOf(it.bias))}</div><small>Last 30 sessions</small></div>
        <div class="gx-dh"><small>Score, last ${it.score_hist.length} sessions${prev != null ? ` · ${it.score - prev >= 0 ? 'up' : 'down'} ${Math.abs(it.score - prev).toFixed(1)} in 5 sessions` : ''}</small>${histChart(it.score_hist)}</div>
      </div>
      <p class="gx-mean">${E(meaning(it))}</p>
      ${it.divergence ? `<div class="gx-dvbox ${it.divergence.type}">⚡ <b>${it.divergence.type === 'bearish' ? 'Bearish' : 'Bullish'} divergence</b> · ${E(it.divergence.text)}</div>` : ''}
      <h4>What makes the score</h4>
      <div class="gx-comps">${it.components.map(c => { const w = Math.abs(c.points) / c.max * 50; return `<div class="gx-comp">
        <span class="gx-cn">${E(c.name)}<small>${E(c.text)}</small></span>
        <span class="gx-cb"><span class="gx-bar"><i class="${c.points >= 0 ? 'pos gx-bull' : 'neg gx-bear'}" style="${c.points >= 0 ? 'left:50%' : 'right:50%'};width:${w}%"></i><span class="gx-mid"></span></span></span>
        <b class="num ${cc(c.points)}">${c.points > 0 ? '+' : c.points < 0 ? '−' : ''}${Math.abs(c.points).toFixed(1)}<small> / ±${c.max}</small></b></div>`; }).join('')}
        <div class="gx-comp gx-tot"><span class="gx-cn">Total</span><span></span><b class="num gx-t-${bc(it.bias)}">${sgn(it.score)}<small> / ±10</small></b></div></div>
      <h4>Key numbers</h4>
      <div class="gx-kv">
        <div><small>RSI (14)</small><b class="num">${num(ind.rsi, 1)}</b></div>
        <div><small>EMA 20 / 50</small><b class="num">${num(ind.ema20)} / ${num(ind.ema50)}</b></div>
        <div><small>MACD histogram</small><b class="num ${cc(ind.macd_hist)}">${num(ind.macd_hist, 2)}</b></div>
        <div><small>ATR (14)</small><b class="num">${num(ind.atr)} <small>${ind.atr_pct}%</small></b></div>
        <div><small>20-day high</small><b class="num">${num(r.hi)}</b></div>
        <div><small>20-day low</small><b class="num">${num(r.lo)}</b></div>
      </div>
      <p class="gx-note">Informational summary of trend and momentum from daily prices. It is not a forecast or a trade signal on its own.</p>
    </div></div>`;
  }

  function howItWorks() {
    return `<details class="gx-how" ${G.how ? 'open' : ''}><summary>How the score is made</summary>
      <p>Each market gets a score from −10 to +10 built from its own daily price history. Every part is measured in ATRs (average daily range), so a quiet index and a volatile coin are judged on the same scale.</p>
      <table class="gx-ht"><thead><tr><th>Part</th><th>What it reads</th><th class="r">Points</th></tr></thead><tbody>
        <tr><td>Price vs 20-day EMA</td><td>How far price is above or below its 20-day average</td><td class="r">±1</td></tr>
        <tr><td>20 vs 50-day EMA</td><td>Whether the short trend is above the longer trend</td><td class="r">±1</td></tr>
        <tr><td>Momentum (RSI 14)</td><td>RSI above or below 50</td><td class="r">±2</td></tr>
        <tr><td>MACD histogram</td><td>Whether momentum is accelerating up or down</td><td class="r">±2</td></tr>
        <tr><td>5-day move</td><td>The last week's move compared with normal daily range</td><td class="r">±2</td></tr>
        <tr><td>Place in 20-day range</td><td>Near the 20-day high (+) or low (−)</td><td class="r">±2</td></tr></tbody></table>
      <p><b>Bias:</b> +2.5 or more is BULLISH, −2.5 or less is BEARISH, anything between is NEUTRAL. <b>⚡ Divergence:</b> price makes a new high (low) but RSI does not; flagged when it happened in the last 10 sessions.</p></details>`;
  }

  /* ---------- page ---------- */
  function paint() {
    const el = document.getElementById('v-godseye'); if (!el || (typeof App !== 'undefined' && App.view !== 'godseye')) return;
    const d = G.data, items = (d && d.items) || [], grps = ['All'].concat([...new Set(items.map(x => x.group))]);
    const list = items.filter(x => G.grp === 'All' || x.group === G.grp), s = d && d.summary;
    const upd = d ? new Date(d.as_of).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '';
    const status = d ? (d.nse_open ? '<span class="gx-st on">● Market Open</span>' : `<span class="gx-st">● Market Closed${d.holiday ? ' · ' + E(d.holiday) : ''}</span>`) : '';
    let body;
    if (!d && G.busy) body = `<div class="gx-grid">${'<div class="gx-card gx-skel"></div>'.repeat(8)}</div><p class="gx-load">Reading 8 markets…</p>`;
    else if (!d) body = `<div class="empty">${E(G.err || 'Loading…')} <button class="btn-xs" data-gxr="1">Retry</button></div>`;
    else body = `
      <div class="gx-sum">
        <div class="gx-mood"><span class="gx-bull" style="flex:${s.bullish || 0.001}"></span><span class="gx-neu" style="flex:${s.neutral || 0.001}"></span><span class="gx-bear" style="flex:${s.bearish || 0.001}"></span></div>
        <span><b class="up">${s.bullish}</b> bullish</span><span><b>${s.neutral}</b> neutral</span><span><b class="down">${s.bearish}</b> bearish</span><span><b>${s.divergences}</b> ⚡ divergence${s.divergences === 1 ? '' : 's'}</span>
        <span class="gx-grow"></span>
        <div class="seg">${grps.map(g => `<button class="${G.grp === g ? 'on' : ''}" data-gxg="${E(g)}">${E(g)}</button>`).join('')}</div>
        <div class="seg">${[['cards', 'Cards'], ['heat', 'Heatmap']].map(([k, l]) => `<button class="${G.view === k ? 'on' : ''}" data-gxv="${k}">${l}</button>`).join('')}</div>
      </div>
      ${G.view === 'heat' ? `<div class="gx-tw"><table class="gx-t"><thead><tr><th>Market</th><th class="r">Price</th><th>Score −10 … +10</th><th class="r">Score</th><th>Bias</th><th class="r">RSI</th><th>Trend</th><th>Divergence</th><th>30 sessions</th></tr></thead>
        <tbody>${list.slice().sort((a, b) => (b.score ?? -99) - (a.score ?? -99)).map(heatRow).join('')}</tbody></table></div>`
        : `<div class="gx-grid">${list.map(card).join('')}</div>`}
      ${howItWorks()}`;
    el.innerHTML = `<div class="page gx">
      <div class="gx-bar0">${status}<span class="gx-upd">${G.busy && d ? 'Updating…' : upd ? 'Updated: ' + upd + ' IST' : ''}</span><button class="btn" data-gxr="1" ${G.busy ? 'disabled' : ''}>↻ Refresh</button></div>
      <div class="gx-brand"><svg viewBox="0 0 48 28" class="gx-eye" aria-hidden="true"><path d="M2 14C9 4 39 4 46 14C39 24 9 24 2 14Z" fill="none" stroke="currentColor" stroke-width="3"/><circle cx="24" cy="14" r="6" fill="none" stroke="currentColor" stroke-width="3"/><circle cx="24" cy="14" r="2.2" fill="currentColor"/></svg>
        <h1>GOD'S EYE</h1><span>— The Observer</span></div>
      ${body}
      ${G.open ? detail() : ''}
    </div>`;
    document.body.classList.toggle('gx-noscroll', !!G.open);
  }

  window.renderGodseye = function () {
    paint();
    if (!G.data || Date.now() - G.ts > 60e3) load(false);
  };

  document.addEventListener('click', e => {
    if (!e.target.closest('#v-godseye')) return;
    const t = e.target;
    if (t.closest('button[data-gxclose]') || t.classList.contains('gx-dbg')) { G.open = null; return paint(); }
    const c = t.closest('[data-gx]'); if (c && !t.closest('.gx-det')) { G.open = c.dataset.gx; return paint(); }
    const g = t.closest('[data-gxg]'); if (g) { G.grp = g.dataset.gxg; SS('gx-grp', G.grp); return paint(); }
    const v = t.closest('[data-gxv]'); if (v) { G.view = v.dataset.gxv; SS('gx-view', G.view); return paint(); }
    if (t.closest('[data-gxr]')) return load(true);
    const h = t.closest('.gx-how > summary'); if (h) { setTimeout(() => { G.how = !!t.closest('details').open; }, 0); }
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && G.open) { G.open = null; paint(); } });
  setInterval(() => {
    if (typeof App === 'undefined' || App.view !== 'godseye' || document.hidden) return;
    const age = Date.now() - G.ts, openNow = typeof MKT !== 'undefined' && MKT.open;
    if (age > (openNow ? 60e3 : 300e3)) load(false); else if (openNow && !G.open) paint();   // live ticks for Indian indices
  }, 15e3);

  const css = `
  .page.gx{max-width:2200px;padding:12px clamp(14px,2vw,32px) 48px}
  .gx .muted{color:var(--text-3)}.gx .up{color:var(--up)}.gx .down{color:var(--down)}
  .gx-bar0{display:flex;justify-content:flex-end;align-items:center;gap:12px;padding:6px 0 10px;border-bottom:1px solid var(--line);margin-bottom:14px}
  .gx-st{display:inline-flex;align-items:center;gap:6px;height:28px;padding:0 12px;border-radius:14px;font-size:12.5px;font-weight:700;background:var(--panel-2);color:var(--text-2)}
  .gx-st.on{background:color-mix(in srgb,var(--up) 20%,transparent);color:var(--up)}
  .gx-upd{color:var(--text-3);font-size:12.5px}
  .gx-brand{display:flex;align-items:center;gap:12px;margin:2px 0 18px}
  .gx-eye{width:44px;height:26px;color:#a78bfa}
  .gx-brand h1{margin:0;font-size:32px;font-weight:900;letter-spacing:-.01em;background:linear-gradient(90deg,#60a5fa,#a78bfa 55%,#34d399);-webkit-background-clip:text;background-clip:text;color:transparent}
  .gx-brand span{font-size:18px;font-weight:600;color:#8b9cf7}
  .gx-sum{display:flex;align-items:center;flex-wrap:wrap;gap:10px 16px;margin-bottom:14px;font-size:13px;color:var(--text-2)}
  .gx-mood{display:flex;width:140px;height:8px;border-radius:4px;overflow:hidden;gap:2px}.gx-mood span{display:block}
  .gx-mood .gx-bull{background:var(--up)}.gx-mood .gx-neu{background:var(--text-3)}.gx-mood .gx-bear{background:var(--down)}
  .gx-grow{flex:1}
  .gx-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}@media (max-width:1180px){.gx-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
  .gx-card{position:relative;text-align:left;display:flex;flex-direction:column;gap:6px;padding:18px 20px 14px;border-radius:16px;border:1px solid var(--line);
    background:linear-gradient(160deg,color-mix(in srgb,var(--panel) 92%,#6366f1 8%),var(--panel));box-shadow:0 6px 18px rgba(0,0,0,.18);cursor:pointer;
    transition:transform .15s,box-shadow .15s;border-left:4px solid var(--line);min-height:228px;color:inherit;font:inherit}
  .gx-card:hover{transform:translateY(-2px);box-shadow:0 10px 26px rgba(0,0,0,.28)}
  .gx-card.gx-bull{border-left-color:var(--up);background:linear-gradient(160deg,color-mix(in srgb,var(--up) 9%,var(--panel)),var(--panel))}
  .gx-card.gx-bear{border-left-color:var(--down);background:linear-gradient(160deg,color-mix(in srgb,var(--down) 9%,var(--panel)),var(--panel))}
  .gx-top{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
  .gx-k{font-size:13px;font-weight:800;letter-spacing:.06em;color:var(--text-2)}
  .gx-px{font-size:12px;color:var(--text-3);white-space:nowrap}.gx-px em{font-style:normal;font-weight:700;margin-left:4px}
  .gx-score{font-size:40px;font-weight:900;line-height:1.05;letter-spacing:-.02em;color:var(--text-2)}
  .gx-bull .gx-score{color:var(--up)}.gx-bear .gx-score{color:var(--down)}
  .gx-bias{font-size:12.5px;font-weight:800;letter-spacing:.12em;color:var(--text-3)}
  .gx-bull .gx-bias{color:var(--up)}.gx-bear .gx-bias{color:var(--down)}
  .gx-div{font-size:12.5px;font-weight:700;min-height:18px}.gx-div.bearish{color:var(--down)}.gx-div.bullish{color:var(--up)}
  .gx-spark{width:100%;height:38px;display:block;margin-top:4px}
  .gx-more{font-size:12px;color:var(--text-3);margin-top:auto}
  .gx-off{cursor:default;justify-content:center}.gx-na{font-weight:700;color:var(--text-3)}
  .gx-skel{min-height:228px;background:linear-gradient(90deg,var(--panel-2),var(--panel),var(--panel-2));background-size:200% 100%;animation:gxSk 1.2s infinite;cursor:default}
  @keyframes gxSk{to{background-position:-200% 0}}.gx-load{text-align:center;color:var(--text-3);font-size:12.5px}
  .gx-tw{overflow-x:auto;border:1px solid var(--line);border-radius:14px;background:var(--panel)}
  .gx-t{width:100%;border-collapse:collapse;font-size:13px;min-width:820px}
  .gx-t th{text-align:left;font-size:11px;color:var(--text-3);font-weight:700;padding:9px 12px;background:var(--panel-2);white-space:nowrap}
  .gx-t td{padding:9px 12px;border-top:1px solid var(--line);vertical-align:middle;white-space:nowrap}.gx-t td small{display:block;font-size:11px;color:var(--text-3)}
  .gx-t .r{text-align:right}.gx-row{cursor:pointer}.gx-row:hover{background:var(--panel-2)}
  .gx-barc{width:30%}.gx-bar{position:relative;display:block;height:10px;border-radius:5px;background:var(--panel-2);min-width:120px}
  .gx-bar i{position:absolute;top:0;bottom:0;border-radius:5px}.gx-bar i.gx-bull{background:var(--up)}.gx-bar i.gx-bear{background:var(--down)}.gx-bar i.gx-neu{background:var(--text-3)}
  .gx-mid{position:absolute;left:50%;top:-3px;bottom:-3px;width:1px;background:var(--text-3)}
  .gx-sc{font-weight:800;font-size:15px}.gx-t-bull{color:var(--up)}.gx-t-bear{color:var(--down)}.gx-t-neu{color:var(--text-2)}
  .gx-pill{font-size:10.5px;font-weight:800;letter-spacing:.06em;padding:3px 8px;border-radius:6px;background:var(--panel-2);color:var(--text-2)}
  .gx-pill.gx-bull{background:var(--up-bg);color:var(--up)}.gx-pill.gx-bear{background:var(--down-bg);color:var(--down)}
  .gx-dv{font-weight:700;font-size:12px}.gx-dv.bearish{color:var(--down)}.gx-dv.bullish{color:var(--up)}
  .gx-how{margin-top:18px;border:1px solid var(--line);border-radius:12px;background:var(--panel);padding:10px 16px;font-size:13px;color:var(--text-2)}
  .gx-how summary{cursor:pointer;font-weight:700;color:var(--text)}.gx-how p{line-height:1.55}
  .gx-ht{width:100%;border-collapse:collapse;font-size:12.5px}.gx-ht th,.gx-ht td{padding:6px 8px;border-top:1px solid var(--line);text-align:left}.gx-ht .r{text-align:right}
  body.gx-noscroll{overflow:hidden}
  .gx-dbg{position:fixed;inset:0;z-index:200;background:rgba(5,10,20,.6);display:flex;align-items:center;justify-content:center;padding:16px}
  .gx-det{background:var(--panel);border:1px solid var(--line);border-radius:16px;width:min(980px,100%);max-height:calc(100vh - 32px);overflow:auto;padding:18px 20px;box-shadow:0 20px 60px rgba(0,0,0,.4)}
  .gx-det header{display:flex;justify-content:space-between;gap:10px;margin-bottom:12px}.gx-det header b{display:block;font-size:18px}.gx-det header small{color:var(--text-3);font-size:12px}
  .gx-dtop{display:grid;grid-template-columns:200px 1fr 1fr;gap:16px;align-items:start}
  .gx-dg{text-align:center}.gx-gauge{width:180px;height:100px}.gx-gt{font-size:10px;fill:var(--text-3)}
  .gx-dgs{font-size:30px;font-weight:900;margin-top:-6px}.gx-dgb{font-size:12px;font-weight:800;letter-spacing:.08em;color:var(--text-3)}
  .gx-dpx small,.gx-dh small{display:block;color:var(--text-3);font-size:11.5px}.gx-dpx b{display:block;font-size:22px}.gx-dpx span{font-size:12.5px;font-weight:700}
  .gx-dsp .gx-spark{height:70px}.gx-hist{width:100%;height:auto;display:block;margin-top:4px}
  .gx-mean{font-size:14px;line-height:1.55;margin:14px 0 8px;padding:10px 14px;border-radius:10px;background:var(--panel-2)}
  .gx-dvbox{font-size:13px;padding:9px 13px;border-radius:10px;margin-bottom:6px}.gx-dvbox.bearish{background:var(--down-bg)}.gx-dvbox.bullish{background:var(--up-bg)}
  .gx-det h4{margin:16px 0 8px;font-size:13px}
  .gx-comps{display:flex;flex-direction:column;gap:2px}
  .gx-comp{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(120px,1fr) 92px;gap:14px;align-items:center;padding:7px 4px;border-top:1px solid var(--line)}
  .gx-cn{font-size:13px;font-weight:600}.gx-cn small{display:block;font-weight:400;font-size:11.5px;color:var(--text-3)}
  .gx-comp b{text-align:right;font-size:14px}.gx-comp b small{font-size:10.5px;color:var(--text-3);font-weight:500}
  .gx-tot{border-top:2px solid var(--line)}.gx-tot .gx-cn{font-weight:800}
  .gx-kv{display:grid;grid-template-columns:repeat(6,1fr);gap:8px}.gx-kv>div{background:var(--panel-2);border-radius:10px;padding:8px 10px}
  .gx-kv small{display:block;font-size:11px;color:var(--text-3)}.gx-kv b{font-size:14px}.gx-kv b small{display:inline;font-size:11px}
  .gx-note{color:var(--text-3);font-size:11.5px;margin:12px 0 0}
  @media (max-width:760px){
    .gx-brand h1{font-size:24px}.gx-brand span{font-size:14px}.gx-eye{width:34px}
    .gx-grid{grid-template-columns:1fr 1fr;gap:10px}.gx-card{padding:14px 14px 10px;min-height:196px;border-radius:14px}.gx-score{font-size:32px}.gx-top{flex-direction:column;gap:2px}.gx-px{font-size:11px}
    .gx-sum{gap:8px 12px}.gx-grow{display:none}
    .gx-dbg{align-items:flex-end;padding:0}.gx-det{border-radius:16px 16px 0 0;max-height:92vh;padding:14px}
    .gx-dtop{grid-template-columns:1fr}.gx-kv{grid-template-columns:repeat(2,1fr)}.gx-comp{grid-template-columns:1fr 80px;}.gx-cb{display:none}
  }`;
  const st = document.createElement('style'); st.id = 'gxCss'; st.textContent = css; document.head.appendChild(st);
})();
