/* Journal > Top strategies: the kept strategies (public/static/lab_top.json, at most 10) are paper-traded every trading day.
   This screen shows their accuracy for indices and stocks apart. Read only: it never places an order. */
(function () {
  'use strict';
  const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const S = { el: null, rep: null, top: null, err: '', loading: false, t: 0 };
  const inr = v => (v < 0 ? '−' : '') + '₹' + Math.abs(Math.round(v)).toLocaleString('en-IN');
  const pct = v => v == null ? '—' : v + '%';
  const rr = v => v == null ? '—' : (v > 0 ? '+' : '') + v + 'R';
  const cls = v => v == null ? '' : v > 0 ? 'up' : v < 0 ? 'down' : '';
  function css() {
    if (document.getElementById('trpCss')) return;
    const st = document.createElement('style'); st.id = 'trpCss';
    st.textContent = `.trp{font-size:15px;line-height:1.4}.trp h3{margin:0 0 4px;font-size:21px}.trp .muted{color:var(--text-3,#8a93a6)}
.trp-note{margin:10px 0;padding:10px 12px;border-radius:12px;font-size:13px;border:1px solid rgba(99,102,241,.4);background:rgba(99,102,241,.1)}
.trp-two{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px 0}.trp-box{padding:14px;border-radius:16px;border:1px solid var(--line);background:linear-gradient(180deg,var(--panel-2),var(--panel))}
.trp-box h4{margin:0 0 8px;font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:var(--text-3)}.trp-box b.big{font-size:28px;display:block;line-height:1.1}
.trp-box small{display:block;color:var(--text-3);margin-top:4px}
.trp-st{padding:14px;border-radius:16px;border:1px solid var(--line);background:var(--panel);margin-bottom:10px}.trp-st .hd{display:flex;gap:8px;justify-content:space-between;align-items:flex-start;flex-wrap:wrap}
.trp-pill{font-size:11px;font-weight:800;padding:2px 9px;border-radius:999px;background:rgba(99,102,241,.18)}.trp-pill.p{background:rgba(34,197,94,.18);color:var(--up,#22c55e)}.trp-pill.w{background:rgba(245,158,11,.18);color:#f59e0b}
.trp-st .row{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}.trp-st .row div{padding:8px 10px;border-radius:12px;background:var(--panel-2)}.trp-st .row b{display:block}
.trp .up{color:var(--up,#22c55e)}.trp .down{color:var(--down,#ef4444)}
.trp-b{border:1px solid var(--line);background:var(--panel);border-radius:999px;padding:8px 16px;min-height:40px;cursor:pointer;font:inherit;font-weight:700;color:inherit}
@media (max-width:560px){.trp-two{grid-template-columns:1fr}}`;
    document.head.appendChild(st);
  }
  const acc = (a, label) => `<div><small class="muted">${label}</small><b class="${cls(a.avgR)}">${a.n ? a.n + ' trades' : 'none yet'}</b><span class="muted" style="font-size:12.5px">${a.closed ? `${a.closed} done · won ${pct(a.winPct)} · avg ${rr(a.avgR)}` : (a.open ? a.open + ' still open' : '')}</span></div>`;
  function paint() {
    if (!S.el) return; css();
    const r = S.rep, meta = {}; ((S.top || {}).items || []).forEach(x => { meta[x.id] = x; });
    let body;
    if (S.err) body = `<div class="trp-note">${esc(S.err)} <button type="button" class="trp-b" data-trp-reload>Try again</button></div>`;
    else if (!r) body = '<div class="muted">Loading…</div>';
    else {
      const t = r.totals, day = r.tradingDaysRecorded || 0;
      const big = (a, label) => `<div class="trp-box"><h4>${label}</h4><b class="big ${cls(a.avgR)}">${a.closed ? pct(a.winPct) + ' won' : (a.n ? a.n + ' open' : 'No trades yet')}</b><small>${a.n} trades · ${a.closed} finished${a.closed ? ' · average ' + rr(a.avgR) + ' per trade' : ''}</small></div>`;
      body = `<div class="trp-note">📄 <b>Paper trades only.</b> No real order is placed from these. ${day ? `Recorded on ${day} trading day${day === 1 ? '' : 's'} so far (since ${esc(r.since || '')}).` : 'The first trades appear on the next trading day after 9:20 am.'} Real orders only when you decide you are confident.</div>
        <div class="trp-two">${big(t.index, 'Index')}${big(t.stock, 'Stocks')}</div>
        ${r.strategies.map(s => { const m = meta[s.id] || {}, ev = m.ev || {}, cl = s.tier === 'Proven' ? 'p' : /Watch/.test(s.tier) ? 'w' : '';
          return `<div class="trp-st"><div class="hd"><b>${esc(s.name)}</b><span class="trp-pill ${cl}">${esc(s.tier || '')}</span></div>
            <div class="muted" style="font-size:13px;margin-top:4px">${esc(ev.why || '')}${ev.net ? ` 8-year test on ₹1,00,000: index options ${inr(ev.net[0])}, stock options ${inr(ev.net[1])}, shares ${inr(ev.net[2])}.` : ''}</div>
            <div class="row">${acc(s.index, 'Index paper trades')}${acc(s.stock, 'Stock paper trades')}</div>
            <div class="muted" style="font-size:12px;margin-top:6px">New signals today: ${s.today}</div></div>`; }).join('')}
        <p class="muted" style="font-size:12px">Each paper trade enters at the live price after 9:20 am, uses the strategy's ATR stop, and ends at 1.5R or the 3:25 pm close. A phone notification with these totals is sent each trading day at about 3:45 pm. Strategies kept: ${r.strategies.length} (at most 10). Last updated ${esc((r.asOf || '').slice(0, 16).replace('T', ' '))}.</p>`;
    }
    S.el.innerHTML = `<div class="trp"><h3>📅 Top strategies · daily paper accuracy</h3><div class="muted" style="font-size:13.5px">The best strategies from your lists, checked every trading day on indices and stocks.</div>${body}</div>`;
  }
  function load() {
    if (S.loading) return; S.loading = true;
    Promise.all([fetch('/api/auto/top-report', { cache: 'no-cache' }).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); }), fetch('/static/lab_top.json').then(r => r.json()).catch(() => null)])
      .then(([rep, top]) => { S.rep = rep; S.top = top; S.err = ''; S.t = Date.now(); }).catch(() => { S.err = 'The report could not be loaded right now.'; })
      .finally(() => { S.loading = false; paint(); });
  }
  function mount(el) {
    if (S.el !== el) { S.el = el; el.addEventListener('click', ev => { if (ev.target.closest('[data-trp-reload]')) { S.err = ''; load(); } }); }
    paint(); if (!S.rep || Date.now() - S.t > 60000) load();
  }
  window.TopRep = { mount, state: S };
})();
