/* GOD'S EYE - The Observer
   A grid of cards: one momentum score (-10 .. +10), a Bullish / Neutral / Bearish label, a divergence flag and a sparkline
   per instrument. Data: GET /api/observer (see observer_api.py for exactly how the score is built).
   Mounted inside Vedic Astro (tab "God's Eye") and on the God's Eye screen. */
(function () {
  'use strict';
  const O = { data: null, err: null, busy: false, open: null, timer: null, ts: 0, retries: 0, retry: null };
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const fmt = (v, d) => v == null || !isFinite(v) ? '—' : Number(v).toLocaleString('en-IN', { minimumFractionDigits: d, maximumFractionDigits: d });
  const sgn = (v, d) => (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(d == null ? 1 : d);
  const cls = l => l === 'BULLISH' ? 'bull' : l === 'BEARISH' ? 'bear' : 'neut';
  const nice = l => l === 'BULLISH' ? 'Bullish' : l === 'BEARISH' ? 'Bearish' : 'Neutral';

  function spark(vals, color) {
    if (!vals || vals.length < 2) return '';
    const w = 120, h = 34, lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals), r = hi - lo || 1;
    const pts = vals.map((v, i) => `${(i / (vals.length - 1) * w).toFixed(1)},${(h - 3 - (v - lo) / r * (h - 6)).toFixed(1)}`).join(' ');
    return `<svg class="ob-spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true"><polyline points="${pts}" fill="none" stroke="${color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke"/></svg>`;
  }

  function detail(i) {
    const d = i.detail || {}, p = d.parts || {};
    const part = (name, v, max) => `<div class="ob-part"><span>${name}</span><i class="ob-pbar"><b class="${v >= 0 ? 'up' : 'down'}" style="width:${Math.min(100, Math.abs(v) / max * 100)}%;${v >= 0 ? 'left:50%' : 'right:50%'}"></b></i><em class="${v >= 0 ? 'up' : 'down'}">${sgn(v)}</em></div>`;
    return `<div class="ob-detail">
      <div class="ob-kv"><div><small>Price</small><b>${esc(i.ccy)}${fmt(i.price, i.price >= 1000 ? 0 : 2)}</b></div><div><small>Day change</small><b class="${i.chgPct >= 0 ? 'up' : 'down'}">${sgn(i.chgPct, 2)}%</b></div>
        <div><small>RSI (14)</small><b>${d.rsi != null ? d.rsi : '—'}</b></div><div><small>vs 20-day avg</small><b class="${d.vsEma20Pct >= 0 ? 'up' : 'down'}">${sgn(d.vsEma20Pct, 2)}%</b></div>
        <div><small>20-day high</small><b>${fmt(d.high20, d.high20 >= 1000 ? 0 : 2)}</b></div><div><small>20-day low</small><b>${fmt(d.low20, d.low20 >= 1000 ? 0 : 2)}</b></div></div>
      ${play(i)}
      <div class="ob-parts"><div class="ob-ph">How the ${sgn(i.score)} was built</div>${part('Day move', p.dayMove || 0, 3)}${part('Intraday pressure', p.intraday || 0, 2)}${part('Vs 20-day avg', p.trend || 0, 3)}${part('RSI bias', p.rsi || 0, 2)}</div>
      <ul class="ob-why">${(d.reasons || []).map(r => `<li>${esc(r)}</li>`).join('')}</ul></div>`;
  }

  function play(i) {
    const a = i.action; if (!a) return '';
    const dp = v => fmt(v, v >= 1000 ? 0 : 2), c = i.ccy || '';
    if (a.side === 'WAIT') return `<div class="ob-play wait"><b>WAIT</b><span>${esc(a.why)}</span></div>`;
    return `<div class="ob-play ${a.side === 'SELL' ? 'bear' : 'bull'}"><b>${esc(a.label)}</b><span>${esc(a.why)}</span>
      <div class="ob-lv"><div><small>${a.side === 'SELL' ? 'Sell zone' : 'Buy zone'}</small><em>${c}${dp(a.zone[0])} – ${dp(a.zone[1])}</em></div><div><small>Stop-loss</small><em class="down">${c}${dp(a.sl)}</em></div><div><small>Targets</small><em class="up">${a.targets.map(t => c + dp(t)).join(' · ')}</em></div></div></div>`;
  }

  function card(i) {
    if (i.pending) return `<article class="ob-card ob-skel" aria-busy="true"><div class="ob-name">${esc(i.name)}</div><div class="ob-tip">Loading…</div></article>`;
    if (i.error) return `<article class="ob-card neut"><div class="ob-name">${esc(i.name)}</div><div class="ob-score">—</div><div class="ob-lab">No data</div><div class="ob-tip">${esc(i.error)}</div></article>`;
    const c = cls(i.label), open = O.open === i.key, col = c === 'bull' ? 'var(--up,#22ab94)' : c === 'bear' ? 'var(--down,#f7525f)' : 'var(--text-3,#8a93a6)';
    return `<article class="ob-card ${c}${open ? ' open' : ''}" data-ob="${esc(i.key)}" tabindex="0" role="button" aria-expanded="${open}" aria-label="${esc(i.name)} ${nice(i.label)} score ${sgn(i.score)}. Show details">
      <div class="ob-name">${esc(i.name)}${i.stale ? ' <em class="ob-old" title="Showing the last good reading; live data was slow">delayed</em>' : ''}</div>
      <div class="ob-score">${sgn(i.score)}</div>
      <div class="ob-lab">${nice(i.label).toUpperCase()}</div>
      ${i.action ? `<div class="ob-act ${i.action.side === 'SELL' ? 'bear' : i.action.side === 'BUY' ? 'bull' : 'neut'}">${esc(i.action.label)}</div>` : ''}
      <div class="ob-div ${i.divergence ? (i.divergence === 'BULLISH' ? 'bull' : 'bear') : 'none'}">${i.divergence ? `⚡ ${nice(i.divergence)} divergence` : '&nbsp;'}</div>
      ${spark(i.spark, col)}
      <div class="ob-tip">${open ? 'Hide details ▴' : 'Click for details ▾'}</div>
      ${open ? detail(i) : ''}</article>`;
  }

  function stamp(d) {
    try { return new Date(d.asOf).toLocaleString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit', timeZone: 'Asia/Kolkata' }).replace(/\bam\b/, 'AM').replace(/\bpm\b/, 'PM') + ' IST'; } catch (e) { return ''; }
  }

  function howCard(m) {
    if (!m) return '';
    return `<details class="ob-how"><summary>How is this made?</summary>
      <ol><li><b>Data.</b> ${esc(m.source)}</li><li><b>Score.</b> ${esc(m.summary)}</li><li><b>Label.</b> ${esc(m.label)}</li>${m.action ? `<li><b>Action.</b> ${esc(m.action)}</li>` : ''}<li><b>Divergence ⚡.</b> ${esc(m.divergence)}</li><li><b>Sparkline.</b> ${esc(m.sparkline)}</li></ol>
      <p class="ob-note">${esc(m.note)}</p></details>`;
  }

  function paint(host) {
    if (!host) return;
    const d = O.data;
    const head = `<div class="ob-head"><h2><span class="ob-eye">👁</span> <span class="ob-grad">GOD'S EYE</span> <small>— The Observer</small></h2>
      <div class="ob-meta">${d ? `<span class="ob-badge ${d.marketOpen ? 'on' : ''}"><i></i>${d.marketOpen ? 'Market Open' : 'Market Closed'}</span><span class="ob-upd">Updated: ${esc(stamp(d))}</span>` : ''}
      ${host.closest('#pkGodseye') ? (O.busy ? '<span class="ob-upd">Updating…</span>' : '') : `<button type="button" class="ob-ref" data-ob-refresh title="Refresh now" aria-label="Refresh">${O.busy ? '…' : '↻'}</button>`}</div></div>`;
    let body;
    if (!d && O.busy) body = `<div class="ob-grid">${Array.from({ length: 8 }, () => '<div class="ob-card ob-skel"></div>').join('')}</div>`;
    else if (!d) body = `<div class="ob-empty">Could not load the Observer${O.err ? ': ' + esc(O.err) : ''}. <button type="button" class="btn" data-ob-refresh>Retry</button></div>`;
    else body = `<div class="ob-grid">${d.items.map(card).join('')}</div>${howCard(d.method)}`;
    host.innerHTML = `<div class="ob">${head}${body}</div>`;
  }

  async function load(force) {
    if (O.busy) return;
    O.busy = true; O.err = null; paintAll();
    try {
      const r = await fetch('/api/observer' + (force ? '?refresh=true' : ''), { cache: 'no-store' });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const j = await r.json(); if (!j || !Array.isArray(j.items)) throw new Error('bad response');
      O.data = j; O.ts = Date.now();
      if (O.data.items.some(x => x.pending) && O.retries++ < 8) { clearTimeout(O.retry); O.retry = setTimeout(() => load(false), 4000); } else if (!O.data.items.some(x => x.pending)) O.retries = 0;
    } catch (e) { O.err = e.message || 'network error'; }
    O.busy = false; paintAll();
  }
  const hosts = () => Array.from(document.querySelectorAll('[data-ob-host]')).filter(h => h.offsetParent !== null);
  function paintAll() { hosts().forEach(paint); }

  window.obsRefresh = () => load(true);        // the Picks page Refresh button refreshes the Observer too
  window.obsMount = function (host) {
    if (!host) return;
    host.setAttribute('data-ob-host', '1'); paint(host);
    if (!O.data || Date.now() - O.ts > 60000) load(false);
    clearInterval(O.timer); O.timer = setInterval(() => { if (hosts().length && !document.hidden) load(false); }, 90000);
  };

  /* standalone God's Eye screen: the Observer on top, the older pre-market forecast ledger behind a button */
  window.renderObserverPage = function () {
    const el = document.getElementById('v-godseye'); if (!el) return;
    el.innerHTML = `<div class="page ob-page"><div data-ob-host="1"></div>
      <div class="ob-legacy"><button type="button" class="btn" data-ob-legacy>Open pre-market forecast ledger (demo)</button></div></div>`;
    window.obsMount(el.querySelector('[data-ob-host]'));
  };

  document.addEventListener('click', e => {
    const r = e.target.closest('[data-ob-refresh]'); if (r) { load(true); return; }
    const lg = e.target.closest('[data-ob-legacy]'); if (lg) { if (window.renderGodseye) window.renderGodseye(); return; }
    const c = e.target.closest('[data-ob]'); if (!c) return;
    O.open = O.open === c.dataset.ob ? null : c.dataset.ob; paintAll();
  });
  document.addEventListener('keydown', e => {
    if ((e.key === 'Enter' || e.key === ' ') && e.target.matches && e.target.matches('.ob-card[data-ob]')) { e.preventDefault(); e.target.click(); }
  });

  const st = document.createElement('style');
  st.textContent = `
  .ob{max-width:1100px;margin:0 auto}
  .ob-act{align-self:flex-start;font-size:11px;font-weight:800;letter-spacing:.04em;padding:3px 8px;border-radius:6px;background:var(--panel-2,rgba(255,255,255,.06));color:var(--text-2,inherit)}
  .ob-act.bear{background:color-mix(in srgb,var(--down,#f7525f) 18%,transparent);color:var(--down,#f7525f)}.ob-act.bull{background:color-mix(in srgb,var(--up,#22ab94) 18%,transparent);color:var(--up,#22ab94)}
  .ob-play{margin:10px 0 4px;padding:10px 12px;border-radius:10px;border:1px solid var(--line);display:flex;flex-direction:column;gap:6px;font-size:13px}
  .ob-play>b{font-size:14px;letter-spacing:.03em}.ob-play.bear>b{color:var(--down,#f7525f)}.ob-play.bull>b{color:var(--up,#22ab94)}.ob-play>span{color:var(--text-2,inherit)}
  .ob-play.bear{background:color-mix(in srgb,var(--down,#f7525f) 7%,transparent)}.ob-play.bull{background:color-mix(in srgb,var(--up,#22ab94) 7%,transparent)}
  .ob-lv{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.ob-lv small{display:block;font-size:10.5px;color:var(--text-3,#8a93a6)}.ob-lv em{font-style:normal;font-weight:700;font-size:13px}
  @media(max-width:520px){.ob-lv{grid-template-columns:1fr 1fr}.ob-lv>div:last-child{grid-column:1/-1}}
  .ob-head{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:10px 16px;margin:4px 0 14px}
  .ob-head h2{margin:0;font-size:26px;font-weight:800;letter-spacing:-.3px;display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
  .ob-head h2 small{font-size:15px;font-weight:600;color:var(--text-3,#8a93a6)}
  .ob-grad{background:linear-gradient(90deg,#7c9cff,#9b7cff 45%,#34d6a0);-webkit-background-clip:text;background-clip:text;color:transparent}
  .ob-eye{font-size:24px}
  .ob-meta{display:flex;align-items:center;gap:10px;flex-wrap:wrap;font-size:12.5px;color:var(--text-3,#8a93a6)}
  .ob-badge{display:inline-flex;align-items:center;gap:6px;padding:5px 12px;border-radius:14px;font-weight:700;background:var(--panel-2,rgba(255,255,255,.06));color:var(--text-2,inherit)}
  .ob-badge i{width:8px;height:8px;border-radius:50%;background:var(--text-3,#8a93a6)}
  .ob-badge.on{background:color-mix(in srgb,var(--up,#22ab94) 22%,transparent);color:var(--up,#22ab94)}.ob-badge.on i{background:var(--up,#22ab94);box-shadow:0 0 0 3px color-mix(in srgb,var(--up,#22ab94) 30%,transparent)}
  .ob-ref{width:40px;height:40px;border-radius:50%;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:18px;cursor:pointer}
  .ob-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
  .ob-card{position:relative;display:flex;flex-direction:column;gap:5px;background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--text-3,#8a93a6);border-radius:14px;padding:14px 14px 12px;cursor:pointer;min-width:0;text-align:left;transition:transform .12s,border-color .12s}
  .ob-card:hover{transform:translateY(-1px)}.ob-card:focus-visible{outline:2px solid var(--brand,#4f8ef7);outline-offset:2px}
  .ob-card.bull{border-left-color:var(--up,#22ab94);background:linear-gradient(180deg,color-mix(in srgb,var(--up,#22ab94) 9%,var(--panel)),var(--panel))}
  .ob-card.bear{border-left-color:var(--down,#f7525f);background:linear-gradient(180deg,color-mix(in srgb,var(--down,#f7525f) 9%,var(--panel)),var(--panel))}
  .ob-card.open{grid-column:1/-1;cursor:default}
  .ob-name{font-size:12.5px;font-weight:700;letter-spacing:.06em;color:var(--text-2,inherit)}
  .ob-score{font-size:34px;font-weight:800;line-height:1.05;font-variant-numeric:tabular-nums;color:var(--text-2,inherit)}
  .ob-card.bull .ob-score,.ob-card.bull .ob-lab{color:var(--up,#22ab94)}.ob-card.bear .ob-score,.ob-card.bear .ob-lab{color:var(--down,#f7525f)}
  .ob-lab{font-size:12px;font-weight:800;letter-spacing:.08em;color:var(--text-3,#8a93a6)}
  .ob-div{font-size:12px;font-weight:600;min-height:17px}.ob-div.bear{color:var(--down,#f7525f)}.ob-div.bull{color:var(--up,#22ab94)}
  .ob-spark{width:100%;height:34px;margin:2px 0}
  .ob-old{font-style:normal;font-size:10px;font-weight:700;padding:1px 6px;border-radius:8px;margin-left:6px;background:var(--panel-2,rgba(255,255,255,.08));color:var(--text-3,#8a93a6);letter-spacing:0}
  .ob-tip{font-size:11.5px;color:var(--text-3,#8a93a6)}
  .ob-skel{min-height:170px;animation:obp 1.2s ease-in-out infinite;cursor:default}@keyframes obp{50%{opacity:.5}}
  .ob-detail{margin-top:10px;padding-top:12px;border-top:1px solid var(--line);display:grid;grid-template-columns:1.2fr 1fr;gap:14px 20px;cursor:default}
  .ob-kv{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.ob-kv small{display:block;font-size:10.5px;color:var(--text-3,#8a93a6);text-transform:uppercase;letter-spacing:.05em}.ob-kv b{font-size:14px;font-variant-numeric:tabular-nums}
  .ob-parts{display:flex;flex-direction:column;gap:8px}.ob-ph{font-size:12px;color:var(--text-3,#8a93a6);font-weight:600}
  .ob-part{display:grid;grid-template-columns:92px 1fr 38px;align-items:center;gap:8px;font-size:12px}
  .ob-pbar{position:relative;height:8px;border-radius:4px;background:var(--panel-2,rgba(255,255,255,.07))}.ob-pbar b{position:absolute;top:0;bottom:0;border-radius:4px;max-width:50%}.ob-pbar b.up{background:var(--up,#22ab94)}.ob-pbar b.down{background:var(--down,#f7525f)}
  .ob-part em{font-style:normal;font-weight:700;text-align:right;font-variant-numeric:tabular-nums}.ob .up{color:var(--up,#22ab94)}.ob .down{color:var(--down,#f7525f)}
  .ob-why{grid-column:1/-1;margin:0;padding-left:18px;font-size:12.5px;color:var(--text-2,inherit);display:grid;gap:3px}
  .ob-how{margin-top:14px;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:0 14px}.ob-how summary{padding:13px 0;font-weight:700;font-size:13.5px;cursor:pointer}
  .ob-how ol{margin:0 0 8px;padding-left:20px;font-size:13px;line-height:1.55;color:var(--text-2,inherit)}.ob-note{margin:0 0 14px;font-size:12px;color:var(--text-3,#8a93a6)}
  .ob-empty{padding:30px 16px;text-align:center;color:var(--text-3,#8a93a6);background:var(--panel);border:1px dashed var(--line);border-radius:14px}
  .ob-legacy{margin:18px 0 90px;text-align:center}.ob-page{padding-top:8px}
  @media (max-width:900px){.ob-grid{grid-template-columns:repeat(2,1fr)}.ob-detail{grid-template-columns:1fr}}
  @media (max-width:430px){.ob-head h2{font-size:22px}.ob-score{font-size:30px}.ob-card{padding:12px 11px 10px}.ob-kv{grid-template-columns:repeat(2,1fr)}.ob-part{grid-template-columns:80px 1fr 36px}}
  `;
  document.head.appendChild(st);
})();
