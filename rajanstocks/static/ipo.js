/* Rajan Algo — IPO & Funds hub.
   IPO tracker (NSE dates, subscription, grey market premium, listing performance) + mutual fund returns + SIP calculator.
   Data: /api/ipo/dashboard, /api/funds/list, /api/funds/search, /api/funds/sip (see ipo_funds.py).
   GMP is unofficial grey-market data; fund returns are past performance. Nothing here is advice. */
(function () {
  'use strict';
  const LS = (k, d) => { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } };
  const SS = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const E = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const TABS = [['ipo', 'IPOs'], ['mf', 'Mutual Funds'], ['sip', 'SIP Calculator']];
  const SIZES = [5, 15, 30, 100];
  const S = {
    tab: LS('ipf-tab', 'ipo'),
    ipo: null, ipoErr: null, ipoBusy: false, ipoTs: 0,
    mf: null, mfErr: null, mfBusy: false,
    stage: LS('ipf-stage', 'all'), board: LS('ipf-board', 'all'), q: '', size: LS('ipf-size', 15), pg: { live: 0, listed: 0, mf: 0 },
    cat: LS('ipf-cat', 'All'), sort: LS('ipf-sort', 'r3y'), mq: '', amt: LS('ipf-amt', 10000),
    calc: LS('ipf-calc', { code: null, name: '', amount: 10000, years: 5, step: 0, day: 5 }), sipRes: null, sipErr: null, sipBusy: false,
    found: [], seq: 0,
  };
  window.IPF = S;

  /* ---------- formatting ---------- */
  const inr = (v, d = 0) => v == null || isNaN(v) ? '—' : '₹' + Number(v).toLocaleString('en-IN', { maximumFractionDigits: d, minimumFractionDigits: d });
  const inrS = v => { if (v == null || isNaN(v)) return '—'; const a = Math.abs(v); const s = v < 0 ? '−' : ''; if (a >= 1e7) return s + '₹' + (a / 1e7).toFixed(2) + ' Cr'; if (a >= 1e5) return s + '₹' + (a / 1e5).toFixed(2) + ' L'; return s + inr(a); };
  const pct = (v, d = 2, plus = true) => v == null || isNaN(v) ? '—' : (v > 0 && plus ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(d) + '%';
  const cls = v => v == null || isNaN(v) ? '' : v > 0 ? 'up' : v < 0 ? 'down' : '';
  const pc = (v, d) => `<span class="num ${cls(v)}">${pct(v, d)}</span>`;
  const dt = s => { if (!s) return '—'; const d = new Date(s + 'T00:00:00'); return isNaN(d) ? E(s) : d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }); };
  const dty = s => { if (!s) return '—'; const d = new Date(s + 'T00:00:00'); return isNaN(d) ? E(s) : d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }); };
  const ic = (n, s) => (typeof I === 'function' ? I(n, s || 15) : '');
  const tip = t => `title="${E(t)}"`;

  function spark(vals, w = 84, h = 24) {
    const v = (vals || []).filter(x => x != null && !isNaN(x));
    if (v.length < 2) return '';
    const lo = Math.min(...v), hi = Math.max(...v), r = hi - lo || 1;
    const pts = v.map((x, i) => `${(i / (v.length - 1) * (w - 2) + 1).toFixed(1)},${(h - 2 - (x - lo) / r * (h - 4)).toFixed(1)}`).join(' ');
    const c = v[v.length - 1] >= v[0] ? 'var(--up)' : 'var(--down)';
    return `<svg class="ipf-spark" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" aria-hidden="true"><polyline points="${pts}" fill="none" stroke="${c}" stroke-width="1.6" stroke-linejoin="round"/></svg>`;
  }

  function pager(key, total) {
    const size = S.size, pages = Math.max(1, Math.ceil(total / size));
    if (S.pg[key] >= pages) S.pg[key] = pages - 1;
    const p = S.pg[key], from = total ? p * size + 1 : 0, to = Math.min(total, (p + 1) * size);
    return `<div class="ipf-pager"><span class="muted">${from}–${to} of ${total}</span><span class="ipf-pg-r">
      <label class="muted" for="ipfSize-${key}">Rows</label><select class="ipf-sel" id="ipfSize-${key}" data-ipf-size>${SIZES.map(n => `<option ${n === size ? 'selected' : ''}>${n}</option>`).join('')}</select>
      <button class="btn-xs" data-ipf-pg="${key}:-1" ${p <= 0 ? 'disabled' : ''} aria-label="Previous page">‹</button><span class="num">${p + 1}/${pages}</span><button class="btn-xs" data-ipf-pg="${key}:1" ${p >= pages - 1 ? 'disabled' : ''} aria-label="Next page">›</button></span></div>`;
  }
  const slice = (key, list) => list.slice(S.pg[key] * S.size, (S.pg[key] + 1) * S.size);

  /* ---------- data ---------- */
  async function loadIpo(force) {
    if (S.ipoBusy) return; S.ipoBusy = true; paint();
    try { S.ipo = await api('/api/ipo/dashboard' + (force ? '?refresh=true' : '')); S.ipoErr = null; S.ipoTs = Date.now(); }
    catch (e) { S.ipoErr = 'IPO data could not be loaded right now. Try Refresh in a minute.'; }
    S.ipoBusy = false; paint();
  }
  async function loadMf(force) {
    if (S.mfBusy) return; S.mfBusy = true; paint();
    try { S.mf = await api('/api/funds/list' + (force ? '?refresh=true' : '')); S.mfErr = null; }
    catch (e) { S.mfErr = 'Fund data could not be loaded right now. Try Refresh in a minute.'; }
    S.mfBusy = false; paint();
  }
  async function runSip() {
    const c = S.calc; if (!c.code) { S.sipRes = null; paint(); return; }
    const my = ++S.seq; S.sipBusy = true; S.sipErr = null; paint();
    try {
      const r = await api(`/api/funds/sip?code=${encodeURIComponent(c.code)}&amount=${c.amount}&years=${c.years}&step_up=${c.step}&day=${c.day}`);
      if (my !== S.seq) return; S.sipRes = r;
    } catch (e) { if (my !== S.seq) return; S.sipErr = 'Could not calculate this SIP. The fund may not have enough NAV history.'; S.sipRes = null; }
    S.sipBusy = false; paint();
  }
  let fTimer = 0;
  function findFunds(q) {
    clearTimeout(fTimer);
    if (q.trim().length < 3) { S.found = []; paintFound(); return; }
    fTimer = setTimeout(async () => {
      try { S.found = (await api('/api/funds/search?q=' + encodeURIComponent(q.trim()))).items || []; } catch (e) { S.found = []; }
      paintFound();
    }, 350);
  }

  /* ---------- IPO tab ---------- */
  const STAGES = [['all', 'All'], ['open', 'Open'], ['upcoming', 'Upcoming'], ['closed', 'Awaiting listing'], ['listed', 'Listed']];
  const STAGE_TXT = { open: 'Open now', upcoming: 'Upcoming', closed: 'Awaiting listing', listed: 'Listed' };
  function ipoFiltered() {
    const list = (S.ipo && S.ipo.ipos) || [], q = S.q.trim().toLowerCase();
    return list.filter(r => (S.stage === 'all' || r.status === S.stage) && (S.board === 'all' || (S.board === 'sme') === !!r.sme) && (!q || (r.name || '').toLowerCase().includes(q) || (r.symbol || '').toLowerCase().includes(q)));
  }
  function ipoCard(r) {
    const gm = r.gmp, has = gm != null;
    const dates = r.open_date && r.close_date ? `${dt(r.open_date)} – ${dt(r.close_date)}` : E(r.dates_text || 'Dates to be announced');
    const band = r.band_lo && r.band_hi && r.band_lo !== r.band_hi ? `${inr(r.band_lo)} – ${inr(r.band_hi)}` : inr(r.price);
    return `<article class="ipf-card ipf-${r.status}">
      <header><div class="ipf-nm"><b>${E(r.name)}</b>${r.symbol ? `<small>${E(r.symbol)}</small>` : ''}</div>
        <span class="ipf-badges"><span class="ipf-tag ${r.sme ? 'sme' : 'main'}">${r.sme ? 'SME' : 'Mainboard'}</span><span class="ipf-stage ${r.status}">${STAGE_TXT[r.status] || ''}</span></span></header>
      <div class="ipf-gmp ${has ? cls(gm) : 'mute'}" ${tip('Grey market premium: unofficial price traders quote before listing')}>
        <div><small>GMP</small><b class="num">${has ? (gm > 0 ? '+' : gm < 0 ? '−' : '') + inr(Math.abs(gm)) : '—'}</b></div>
        <div><small>Expected listing</small><b class="num">${inr(r.expected_listing)}</b></div>
        <div><small>Expected gain</small><b class="num ${cls(r.expected_gain_pct)}">${pct(r.expected_gain_pct, 1)}</b></div>
        ${r.gmp_trend && r.gmp_trend.length > 1 ? `<div class="ipf-trend" ${tip('GMP over the last ' + r.gmp_trend.length + ' days')}>${spark(r.gmp_trend, 54, 24)}</div>` : ''}
      </div>
      <dl class="ipf-dl">
        <div><dt>Dates</dt><dd>${dates}</dd></div>
        <div><dt>Price band</dt><dd class="num">${band}</dd></div>
        <div><dt>Subscribed</dt><dd class="num">${r.subscribed_x != null ? r.subscribed_x.toFixed(2) + '×' : '—'}</dd></div>
        <div><dt>Issue size</dt><dd class="num" ${tip('Shares on offer')}>${r.issue_size ? (r.issue_size / 1e5).toFixed(2) + ' L sh' : '—'}</dd></div>
      </dl></article>`;
  }
  function listedTable(list) {
    if (!list.length) return '<div class="empty">No listed IPOs match these filters.</div>';
    return `<div class="ipf-tw"><table class="ipf-t"><thead><tr>
      <th>IPO</th><th ${tip('Listing date on NSE')}>Listed</th><th class="r" ${tip('Final issue price')}>Issue</th>
      <th class="r" ${tip('Last grey market premium seen before listing')}>Last GMP</th><th class="r" ${tip('Issue price + last GMP')}>Expected</th>
      <th class="r" ${tip('Opening price on listing day')}>List open</th><th class="r" ${tip('(List open − issue) ÷ issue')}>Listing gain</th>
      <th class="r" ${tip('Listing-day close vs issue price')}>Day-1 close</th><th class="r">Now</th><th class="r" ${tip('Current price vs issue price')}>Return</th>
      <th class="r" ${tip('Actual listing gain minus the gain GMP predicted, in percentage points')}>GMP error</th><th>Trend</th></tr></thead><tbody>
      ${list.map(r => `<tr><td><b>${E(r.name)}</b><small class="ipf-sub">${E(r.symbol || '')} · <span class="ipf-tag ${r.sme ? 'sme' : 'main'}">${r.sme ? 'SME' : 'Main'}</span></small></td>
        <td>${dt(r.listing_date)}</td><td class="r num">${inr(r.issue_price)}</td>
        <td class="r num ${cls(r.last_gmp)}">${r.last_gmp != null ? inr(r.last_gmp) : '—'}</td>
        <td class="r num">${inr(r.expected_listing)}${r.expected_gain_pct != null ? `<small class="ipf-sub">${pct(r.expected_gain_pct, 1)}</small>` : ''}</td>
        <td class="r num">${inr(r.list_open, 2)}</td><td class="r">${pc(r.listing_gain_pct, 1)}</td><td class="r">${pc(r.day1_close_pct, 1)}</td>
        <td class="r num">${inr(r.current, 2)}</td><td class="r">${pc(r.return_pct, 1)}</td>
        <td class="r num">${r.gmp_error_pct != null ? (r.gmp_error_pct > 0 ? '+' : r.gmp_error_pct < 0 ? '−' : '') + Math.abs(r.gmp_error_pct).toFixed(1) + ' pts' : '—'}</td>
        <td>${spark(r.spark)}</td></tr>`).join('')}</tbody></table></div>`;
  }
  function ipoTab() {
    if (!S.ipo && S.ipoBusy) return skeleton();
    if (!S.ipo) return `<div class="empty">${E(S.ipoErr || 'Loading…')} <button class="btn-xs" data-ipf="ipo-refresh">Retry</button></div>`;
    const d = S.ipo, c = d.counts || {}, st = d.stats || {};
    const all = ipoFiltered(), live = all.filter(r => r.status !== 'listed'), listed = all.filter(r => r.status === 'listed');
    const kp = (l, v, sub, t, k) => `<div class="card ipf-kpi" ${tip(t)}><small>${l}</small><b class="num ${k || ''}">${v}</b>${sub ? `<span class="muted">${sub}</span>` : ''}</div>`;
    return `<div class="ipf-kpis">
        ${kp('Open now', c.open || 0, 'apply before close', 'IPOs accepting bids today')}
        ${kp('Upcoming', c.upcoming || 0, 'dates announced', 'IPOs that open soon')}
        ${kp('Awaiting listing', c.closed || 0, 'allotment stage', 'Bidding closed, not listed yet')}
        ${kp('Avg listing gain', pct(st.avg_listing_gain_pct, 1), `${st.listed_count || 0} IPOs, 120 days`, 'Average of (listing open − issue) ÷ issue', cls(st.avg_listing_gain_pct))}
        ${kp('Listed above issue', st.positive_listing_share != null ? st.positive_listing_share.toFixed(0) + '%' : '—', 'share of listings', 'Share of recent IPOs that opened above the issue price')}
        ${kp('GMP avg error', st.gmp_avg_abs_error_pct != null ? st.gmp_avg_abs_error_pct.toFixed(1) + ' pts' : '—', st.gmp_compared ? st.gmp_compared + ' IPOs compared' : 'builds up as IPOs list', 'Average gap between GMP-expected and actual listing gain')}
      </div>
      <div class="ipf-bar">
        <div class="seg ipf-scroll" role="tablist" aria-label="IPO stage">${STAGES.map(([k, l]) => `<button class="${S.stage === k ? 'on' : ''}" data-ipf-stage="${k}" aria-pressed="${S.stage === k}">${l}${k !== 'all' && c[k] != null ? ` <span class="ipf-n">${c[k]}</span>` : ''}</button>`).join('')}</div>
        <div class="seg" aria-label="Board">${[['all', 'All'], ['main', 'Mainboard'], ['sme', 'SME']].map(([k, l]) => `<button class="${S.board === k ? 'on' : ''}" data-ipf-board="${k}">${l}</button>`).join('')}</div>
        <input class="inp ipf-q" id="ipfQ" placeholder="Search IPO" value="${E(S.q)}" aria-label="Search IPO">
      </div>
      ${S.stage !== 'listed' ? `<h3 class="ipf-h">Open, upcoming and awaiting listing <span class="muted">· ${live.length}</span></h3>
        ${live.length ? `<div class="ipf-grid">${slice('live', live).map(ipoCard).join('')}</div>${pager('live', live.length)}` : '<div class="empty">No live IPOs match these filters.</div>'}` : ''}
      ${S.stage === 'all' || S.stage === 'listed' ? `<h3 class="ipf-h">Listed in the last 120 days <span class="muted">· ${listed.length} · how GMP compared with the actual listing</span></h3>
        ${listedTable(slice('listed', listed))}${listed.length ? pager('listed', listed.length) : ''}` : ''}
      <p class="ipf-note">${ic('eye', 13)} GMP is unofficial grey-market data${d.gmp_source ? ` (source: <a href="${E(d.gmp_source)}" target="_blank" rel="noopener">ipowatch.in</a>)` : ''} and often changes daily; it is not a guarantee of listing price. Dates, price band and subscription come from NSE; listing prices from daily market data. Updated ${d.as_of ? new Date(d.as_of).toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : ''}.</p>`;
  }

  /* ---------- Mutual funds tab ---------- */
  const SORTS = [['r1y', '1Y return'], ['r3y', '3Y CAGR'], ['r5y', '5Y CAGR'], ['sip3y_xirr', 'SIP 3Y XIRR'], ['sip5y_xirr', 'SIP 5Y XIRR'], ['name', 'Name']];
  function mfFiltered() {
    const f = ((S.mf && S.mf.funds) || []).filter(x => (S.cat === 'All' || x.category === S.cat) && (!S.mq || (x.name + ' ' + (x.fund_house || '')).toLowerCase().includes(S.mq.toLowerCase())));
    const k = S.sort;
    return f.sort((a, b) => k === 'name' ? a.name.localeCompare(b.name) : (b[k] ?? -1e9) - (a[k] ?? -1e9));
  }
  function mfTab() {
    if (!S.mf && S.mfBusy) return skeleton();
    if (!S.mf) return `<div class="empty">${E(S.mfErr || 'Loading…')} <button class="btn-xs" data-ipf="mf-refresh">Retry</button></div>`;
    const cats = ['All'].concat(S.mf.categories || []), list = mfFiltered(), amt = S.amt;
    return `<div class="ipf-bar">
        <div class="ipf-chips ipf-scroll" aria-label="Category">${cats.map(c => `<button class="chip ${S.cat === c ? 'on' : ''}" data-ipf-cat="${E(c)}">${E(c)}</button>`).join('')}</div>
      </div>
      <div class="ipf-bar">
        <label class="ipf-amt" ${tip('Monthly SIP amount used for the "value today" columns')}><span class="muted">SIP / month</span><span class="ipf-rs">₹</span><input class="inp num" id="ipfAmt" type="number" min="100" step="500" value="${amt}" inputmode="numeric"></label>
        <label class="ipf-amt"><span class="muted">Sort</span><select class="ipf-sel" id="ipfSort">${SORTS.map(([k, l]) => `<option value="${k}" ${S.sort === k ? 'selected' : ''}>${l}</option>`).join('')}</select></label>
        <input class="inp ipf-q" id="ipfMq" placeholder="Filter these funds" value="${E(S.mq)}" aria-label="Filter funds">
        <div class="ipf-find"><input class="inp" id="ipfFind" placeholder="Search any fund in India…" aria-label="Search any mutual fund" autocomplete="off"><div class="ipf-found" id="ipfFound"></div></div>
      </div>
      <div class="ipf-tw"><table class="ipf-t ipf-mf"><thead><tr>
        <th>Fund</th><th class="r" ${tip('Latest NAV, Direct plan, Growth option')}>NAV</th><th class="r">1D</th>
        <th class="r" ${tip('Point-to-point return over 1 year')}>1Y</th><th class="r" ${tip('Compound annual growth over 3 years')}>3Y CAGR</th><th class="r" ${tip('Compound annual growth over 5 years')}>5Y CAGR</th>
        <th class="r" ${tip('Annualised return of a monthly SIP over 3 years')}>SIP 3Y XIRR</th><th class="r" ${tip('Annualised return of a monthly SIP over 5 years')}>SIP 5Y XIRR</th>
        <th class="r" ${tip(inr(amt) + ' a month for 5 years: total invested and value today')}>${inrS(amt)}/mo · 5Y</th><th></th></tr></thead><tbody>
        ${slice('mf', list).map(f => { const inv = amt * 60, val = f.sip5y_mult ? inv * f.sip5y_mult : null; return `<tr>
          <td><b>${E(f.name)}</b><small class="ipf-sub">${E(f.category)}${f.fund_house ? ' · ' + E(f.fund_house.replace(/ Mutual Fund$/, '')) : ''}</small></td>
          <td class="r num">${f.nav != null ? f.nav.toFixed(2) : '—'}<small class="ipf-sub">${dt(f.nav_date)}</small></td>
          <td class="r">${pc(f.day_pct)}</td><td class="r">${pc(f.r1y, 1)}</td><td class="r">${pc(f.r3y, 1)}</td><td class="r">${pc(f.r5y, 1)}</td>
          <td class="r">${pc(f.sip3y_xirr, 1)}</td><td class="r">${pc(f.sip5y_xirr, 1)}</td>
          <td class="r num">${val ? `<b class="${cls(val - inv)}">${inrS(val)}</b><small class="ipf-sub">of ${inrS(inv)}</small>` : '<span class="muted">under 5Y</span>'}</td>
          <td><button class="btn-xs" data-ipf-calc="${f.code}" data-ipf-name="${E(f.name)}">SIP calc</button></td></tr>`; }).join('') || '<tr><td colspan="10"><div class="empty">No funds match.</div></td></tr>'}
        </tbody></table></div>${pager('mf', list.length)}
      <p class="ipf-note">${ic('eye', 13)} Returns are calculated from each fund's daily NAV history (AMFI, via mfapi.in) for the Direct plan, Growth option. Past returns do not guarantee future returns. NAVs as of ${S.mf.funds && S.mf.funds[0] ? dty(S.mf.funds[0].nav_date) : '—'}.</p>`;
  }
  function paintFound() {
    const el = document.getElementById('ipfFound'); if (!el) return;
    el.innerHTML = S.found.length ? S.found.slice(0, 10).map(i => `<button data-ipf-calc="${i.code}" data-ipf-name="${E(i.scheme)}">${E(i.scheme)}</button>`).join('') : '';
    el.classList.toggle('on', !!S.found.length);
  }

  /* ---------- SIP calculator tab ---------- */
  function sipChart(r) {
    const s = r.series || []; if (s.length < 2) return '';
    const sm = window.innerWidth < 700, W = sm ? 420 : 1000, H = sm ? 250 : 290, L = sm ? 58 : 70, R = 12, T = 14, B = 30;
    const t0 = Date.parse(s[0].date), t1 = Date.parse(s[s.length - 1].date), mx = Math.max(...s.map(p => Math.max(p.value, p.invested))) * 1.06;
    const X = d => L + (Date.parse(d) - t0) / ((t1 - t0) || 1) * (W - L - R), Y = v => T + (1 - v / mx) * (H - T - B);
    const line = k => s.map((p, i) => `${i ? 'L' : 'M'}${X(p.date).toFixed(1)} ${Y(p[k]).toFixed(1)}`).join('');
    const area = line('value') + `L${X(s[s.length - 1].date).toFixed(1)} ${Y(0)}L${X(s[0].date).toFixed(1)} ${Y(0)}Z`;
    const ticks = [0, .25, .5, .75, 1].map(f => mx / 1.06 * f);
    const yrs = []; const y0 = new Date(t0).getFullYear(), y1 = new Date(t1).getFullYear(), stepY = Math.max(1, Math.ceil((y1 - y0 + 1) / 8));
    for (let y = y0 + 1; y <= y1; y += stepY) yrs.push(y);
    const gain = r.value >= r.invested;
    return `<svg class="ipf-chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="SIP value versus amount invested">
      ${ticks.map(v => `<line x1="${L}" x2="${W - R}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--line)"/><text x="${L - 8}" y="${Y(v) + 4}" text-anchor="end" class="ipf-ax">${inrS(v)}</text>`).join('')}
      ${yrs.map(y => { const x = X(y + '-01-01'); return `<text x="${x}" y="${H - 10}" text-anchor="middle" class="ipf-ax">${y}</text>`; }).join('')}
      <path d="${area}" fill="${gain ? 'var(--up)' : 'var(--down)'}" fill-opacity=".1"/>
      <path d="${line('value')}" fill="none" stroke="${gain ? 'var(--up)' : 'var(--down)'}" stroke-width="2.2" stroke-linejoin="round"/>
      <path d="${line('invested')}" fill="none" stroke="var(--text-3)" stroke-width="1.6" stroke-dasharray="5 4"/>
    </svg><div class="ipf-legend"><span><i class="v ${gain ? 'up' : 'down'}"></i>Value</span><span><i class="inv"></i>Invested</span></div>`;
  }
  function sipTab() {
    const c = S.calc, r = S.sipRes, funds = (S.mf && S.mf.funds) || [];
    const opts = funds.slice().sort((a, b) => a.category.localeCompare(b.category) || a.name.localeCompare(b.name));
    const inList = funds.some(f => String(f.code) === String(c.code));
    const kv = (l, v, k, t) => `<div class="card ipf-kpi" ${t ? tip(t) : ''}><small>${l}</small><b class="num ${k || ''}">${v}</b></div>`;
    return `<div class="ipf-calc card">
      <div class="ipf-form">
        <label class="ipf-f ipf-f-wide"><span>Fund</span><select class="ipf-sel" id="ipfFund"><option value="">Choose a fund…</option>
          ${!inList && c.code ? `<option value="${E(c.code)}" selected>${E(c.name)}</option>` : ''}
          ${(S.mf ? S.mf.categories : []).map(cat => `<optgroup label="${E(cat)}">${opts.filter(f => f.category === cat).map(f => `<option value="${f.code}" ${String(f.code) === String(c.code) ? 'selected' : ''}>${E(f.name)}</option>`).join('')}</optgroup>`).join('')}
        </select></label>
        <label class="ipf-f"><span>Monthly SIP</span><span class="ipf-rsw"><span class="ipf-rs">₹</span><input class="inp num" id="ipfCAmt" type="number" min="100" step="500" value="${c.amount}" inputmode="numeric"></span></label>
        <div class="ipf-f"><span>Period</span><div class="seg">${[1, 3, 5, 7, 10, 15].map(y => `<button class="${c.years === y ? 'on' : ''}" data-ipf-yrs="${y}">${y}Y</button>`).join('')}</div></div>
        <label class="ipf-f" ${tip('Raise the SIP by this % every 12 months')}><span>Yearly step-up</span><span class="ipf-rsw"><input class="inp num" id="ipfStep" type="number" min="0" max="50" step="5" value="${c.step}"><span class="ipf-pc">%</span></span></label>
        <label class="ipf-f"><span>SIP date</span><select class="ipf-sel" id="ipfDay">${[1, 5, 10, 15, 20, 25, 28].map(d => `<option ${c.day === d ? 'selected' : ''}>${d}</option>`).join('')}</select></label>
      </div>
      <div class="ipf-find ipf-find-c"><input class="inp" id="ipfFind" placeholder="Or search any fund in India…" aria-label="Search any mutual fund" autocomplete="off"><div class="ipf-found" id="ipfFound"></div></div>
    </div>
    ${!c.code ? '<div class="empty">Pick a fund above to see what your SIP would be worth today.</div>' : S.sipBusy && !r ? skeleton() : S.sipErr ? `<div class="empty">${E(S.sipErr)}</div>` : r ? `
      <h3 class="ipf-h">${E(r.scheme || c.name)} <span class="muted">· ${E(r.category || '')}</span></h3>
      ${r.short_history ? `<div class="ipf-warn">This fund started on ${dty(r.inception)}, so the SIP runs from launch: ${r.instalments} instalments instead of ${c.years * 12}.</div>` : ''}
      <div class="ipf-kpis">
        ${kv('Total invested', inrS(r.invested), '', r.instalments + ' monthly instalments from ' + dty(r.start))}
        ${kv('Value today', inrS(r.value), cls(r.gain), 'At the NAV of ' + dty(r.end))}
        ${kv('Gain', (r.gain >= 0 ? '+' : '−') + inrS(Math.abs(r.gain)).replace('−', ''), cls(r.gain))}
        ${kv('XIRR', pct(r.xirr_pct), cls(r.xirr_pct), 'Annualised return that accounts for when each instalment went in')}
        ${kv('Absolute return', pct(r.abs_return_pct, 1), cls(r.abs_return_pct), 'Value ÷ invested − 1')}
        ${kv('Same money as lumpsum', inrS(r.lumpsum && r.lumpsum.value), cls(r.lumpsum && r.lumpsum.value - r.invested), 'If the full ' + inrS(r.invested) + ' had gone in on ' + dty(r.start) + (r.lumpsum && r.lumpsum.cagr_pct != null ? ' · CAGR ' + pct(r.lumpsum.cagr_pct) : ''))}
      </div>
      <div class="card ipf-chartw">${sipChart(r)}</div>
      <p class="ipf-note">${ic('eye', 13)} Each instalment buys units at the first NAV on or after the SIP date${c.step ? `, rising ${c.step}% every 12 months` : ''}. Value uses the NAV of ${dty(r.end)}. Calculated from real NAV history; ignores exit load and tax. Past returns do not guarantee future returns.</p>` : ''}`;
  }

  function skeleton() { return '<div class="ipf-skel"><i></i><i></i><i></i><i></i></div>'; }

  /* ---------- page ---------- */
  function paint() {
    const el = document.getElementById('v-ipo'); if (!el || App.view !== 'ipo') return;
    const ae = document.activeElement, fid = ae && ae.id, pos = ae && ae.selectionStart;
    const body = S.tab === 'mf' ? mfTab() : S.tab === 'sip' ? sipTab() : ipoTab();
    el.innerHTML = `<div class="page ipf">
      ${pageHead('IPO &amp; Funds', 'IPO grey market premium, expected and actual listing returns, mutual fund returns and SIP calculator.', `<button class="btn" data-ipf="refresh" ${S.ipoBusy || S.mfBusy ? 'disabled' : ''}>${ic('reset', 15)}${S.ipoBusy || S.mfBusy ? 'Refreshing…' : 'Refresh'}</button>`)}
      <div class="ipf-tabs" role="tablist">${TABS.map(([k, l]) => `<button role="tab" aria-selected="${S.tab === k}" class="${S.tab === k ? 'on' : ''}" data-ipf-tab="${k}">${l}</button>`).join('')}</div>
      <div class="ipf-body">${body}</div></div>`;
    if (fid) { const n = document.getElementById(fid); if (n) { n.focus(); try { if (pos != null) n.setSelectionRange(pos, pos); } catch (e) {} } }
    if (fid === 'ipfFind') paintFound();
    if (typeof renderHere === 'function') renderHere();
  }
  window.ipfSubLabel = () => (TABS.find(t => t[0] === S.tab) || [])[1] || '';

  function setTab(t) {
    S.tab = t; SS('ipf-tab', t);
    if ((t === 'mf' || t === 'sip') && !S.mf) loadMf(false);
    if (t === 'sip' && S.calc.code && !S.sipRes) runSip();
    paint();
  }

  window.renderIpo = function () {
    paint();
    if (!S.ipo || Date.now() - S.ipoTs > 15 * 60e3) loadIpo(false);
    if ((S.tab === 'mf' || S.tab === 'sip') && !S.mf) loadMf(false);
    if (S.tab === 'sip' && S.calc.code && !S.sipRes) runSip();
  };

  function openCalc(code, name) {
    S.calc = Object.assign({}, S.calc, { code: String(code), name: name || '' }); SS('ipf-calc', S.calc);
    S.found = []; S.sipRes = null; setTab('sip'); runSip();
  }

  document.addEventListener('click', e => {
    const t = e.target.closest('[data-ipf],[data-ipf-tab],[data-ipf-stage],[data-ipf-board],[data-ipf-pg],[data-ipf-cat],[data-ipf-calc],[data-ipf-yrs]');
    if (!t || !t.closest('#v-ipo')) return;
    const d = t.dataset;
    if (d.ipfTab) return setTab(d.ipfTab);
    if (d.ipfStage) { S.stage = d.ipfStage; SS('ipf-stage', S.stage); S.pg.live = S.pg.listed = 0; return paint(); }
    if (d.ipfBoard) { S.board = d.ipfBoard; SS('ipf-board', S.board); S.pg.live = S.pg.listed = 0; return paint(); }
    if (d.ipfPg) { const [k, n] = d.ipfPg.split(':'); S.pg[k] = Math.max(0, S.pg[k] + Number(n)); paint(); const h = document.querySelector('#v-ipo .ipf-body'); return; }
    if (d.ipfCat) { S.cat = d.ipfCat; SS('ipf-cat', S.cat); S.pg.mf = 0; return paint(); }
    if (d.ipfCalc) return openCalc(d.ipfCalc, d.ipfName);
    if (d.ipfYrs) { S.calc.years = Number(d.ipfYrs); SS('ipf-calc', S.calc); return runSip(); }
    if (d.ipf === 'refresh') { if (S.tab === 'ipo') loadIpo(true); else loadMf(true); if (S.tab === 'sip') runSip(); return; }
    if (d.ipf === 'ipo-refresh') return loadIpo(true);
    if (d.ipf === 'mf-refresh') return loadMf(true);
  });
  let qT = 0;
  document.addEventListener('input', e => {
    const id = e.target.id; if (!e.target.closest('#v-ipo')) return;
    if (id === 'ipfQ') { S.q = e.target.value; S.pg.live = S.pg.listed = 0; clearTimeout(qT); qT = setTimeout(paint, 200); }
    else if (id === 'ipfMq') { S.mq = e.target.value; S.pg.mf = 0; clearTimeout(qT); qT = setTimeout(paint, 200); }
    else if (id === 'ipfFind') findFunds(e.target.value);
  });
  document.addEventListener('change', e => {
    const id = e.target.id, v = e.target.value; if (!e.target.closest('#v-ipo')) return;
    if (e.target.hasAttribute('data-ipf-size')) { S.size = Number(v); SS('ipf-size', S.size); S.pg = { live: 0, listed: 0, mf: 0 }; return paint(); }
    if (id === 'ipfAmt') { S.amt = Math.max(100, Number(v) || 10000); SS('ipf-amt', S.amt); return paint(); }
    if (id === 'ipfSort') { S.sort = v; SS('ipf-sort', v); return paint(); }
    if (id === 'ipfFund') { const f = ((S.mf && S.mf.funds) || []).find(x => String(x.code) === v); if (v) openCalc(v, f ? f.name : ''); return; }
    if (id === 'ipfCAmt') { S.calc.amount = Math.min(1e7, Math.max(100, Number(v) || 10000)); SS('ipf-calc', S.calc); return runSip(); }
    if (id === 'ipfStep') { S.calc.step = Math.min(50, Math.max(0, Number(v) || 0)); SS('ipf-calc', S.calc); return runSip(); }
    if (id === 'ipfDay') { S.calc.day = Number(v) || 5; SS('ipf-calc', S.calc); return runSip(); }
  });
  setInterval(() => { if (typeof App !== 'undefined' && App.view === 'ipo' && S.tab === 'ipo' && !document.hidden && Date.now() - S.ipoTs > 15 * 60e3) loadIpo(false); }, 60e3);

  /* ---------- styles ---------- */
  const css = `
  .ipf .muted{color:var(--text-3)}
  .ipf-tabs{display:flex;gap:4px;border-bottom:1px solid var(--line);margin:-4px 0 16px;overflow-x:auto;scrollbar-width:none}
  .ipf-tabs button{height:38px;padding:0 14px;font-weight:600;color:var(--text-2);border-bottom:2px solid transparent;margin-bottom:-1px;white-space:nowrap}
  .ipf-tabs button.on{color:var(--brand);border-bottom-color:var(--brand)}
  .ipf-kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:14px}
  .ipf-kpi{padding:11px 13px}.ipf-kpi small{display:block;color:var(--text-3);font-size:11.5px}.ipf-kpi b{display:block;font-size:19px;margin-top:2px}.ipf-kpi span{font-size:11.5px}
  .ipf-bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:12px}
  .ipf-scroll{max-width:100%;overflow-x:auto;scrollbar-width:none}
  .ipf-n{display:inline-block;min-width:16px;padding:0 4px;border-radius:8px;background:var(--panel-2);font-size:10.5px;color:var(--text-2)}
  .seg button.on .ipf-n{background:var(--brand-2);color:var(--brand)}
  .ipf-q{max-width:220px;height:30px}
  .ipf-chips{display:flex;gap:6px}.ipf-chips .chip{white-space:nowrap}.ipf-chips .chip.on{background:var(--brand-2);color:var(--brand);border-color:transparent}
  .ipf-h{font-size:14px;margin:18px 0 10px}.ipf-h .muted{font-weight:500}
  .ipf-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:12px}
  .ipf-card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:13px 14px;display:flex;flex-direction:column;gap:11px}
  .ipf-card.ipf-open{border-color:color-mix(in srgb,var(--up) 45%,var(--line))}
  .ipf-card header{display:flex;gap:8px;justify-content:space-between;align-items:flex-start}
  .ipf-nm b{display:block;font-size:14px;line-height:1.3}.ipf-nm small{color:var(--text-3);font-size:11.5px}
  .ipf-badges{display:flex;flex-direction:column;align-items:flex-end;gap:4px;flex:none}
  .ipf-tag{font-size:10px;font-weight:700;letter-spacing:.03em;padding:2px 6px;border-radius:5px;text-transform:uppercase}
  .ipf-tag.main{background:var(--brand-2);color:var(--brand)}.ipf-tag.sme{background:color-mix(in srgb,#e8b84a 20%,transparent);color:#b7861d}
  .ipf-stage{font-size:11px;font-weight:600;color:var(--text-2)}.ipf-stage.open{color:var(--up)}.ipf-stage.closed{color:#b7861d}
  .ipf-gmp{display:flex;flex-wrap:wrap;gap:6px 14px;align-items:center;padding:9px 11px;border-radius:9px;background:var(--panel-2)}
  .ipf-gmp small{display:block;font-size:10.5px;color:var(--text-3);white-space:nowrap}.ipf-gmp b{font-size:15px;white-space:nowrap}
  .ipf-gmp.up{background:var(--up-bg)}.ipf-gmp.up>div:first-child b{color:var(--up)}.ipf-gmp.down{background:var(--down-bg)}.ipf-gmp.down>div:first-child b{color:var(--down)}
  .ipf-trend{margin-left:auto}
  .ipf-dl{display:grid;grid-template-columns:1fr 1fr;gap:8px 14px;margin:0}.ipf-dl dt{font-size:10.5px;color:var(--text-3)}.ipf-dl dd{margin:1px 0 0;font-size:12.5px;font-weight:500}
  .ipf-tw{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--panel)}
  .ipf-t{width:100%;border-collapse:collapse;font-size:12.5px;min-width:860px}
  .ipf-t th{position:sticky;top:0;background:var(--panel-2);color:var(--text-3);font-weight:600;font-size:11px;text-align:left;padding:8px 10px;white-space:nowrap;cursor:help}
  .ipf-t td{padding:8px 10px;border-top:1px solid var(--line);vertical-align:middle;white-space:nowrap}
  .ipf-t .r{text-align:right}.ipf-t td:first-child{white-space:normal;min-width:170px}
  .ipf-t tbody tr:hover{background:var(--panel-2)}
  .ipf-sub{display:block;color:var(--text-3);font-size:11px;font-weight:400;margin-top:1px}
  .ipf .up{color:var(--up)}.ipf .down{color:var(--down)}
  .ipf-pager{display:flex;justify-content:space-between;align-items:center;gap:8px;margin:10px 2px 4px;font-size:12px}
  .ipf-pg-r{display:flex;align-items:center;gap:6px}
  .ipf-sel{height:30px;border:1px solid var(--line);border-radius:8px;background:var(--panel);color:var(--text);padding:0 6px}
  .ipf-amt{display:flex;align-items:center;gap:6px;font-size:12px}.ipf-amt .inp{width:104px;height:30px}
  .ipf-rs{color:var(--text-3)}
  .ipf-find{position:relative;flex:1 1 220px;max-width:340px}.ipf-find .inp{height:30px}
  .ipf-found{display:none;position:absolute;z-index:20;left:0;right:0;top:34px;background:var(--panel);border:1px solid var(--line);border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.18);max-height:320px;overflow:auto}
  .ipf-found.on{display:block}.ipf-found button{display:block;width:100%;text-align:left;padding:8px 11px;font-size:12.5px;border-top:1px solid var(--line)}.ipf-found button:first-child{border-top:0}.ipf-found button:hover{background:var(--panel-2)}
  .ipf-note{color:var(--text-3);font-size:11.5px;margin:14px 2px 0;line-height:1.55}.ipf-note svg{vertical-align:-2px;margin-right:4px}.ipf-note a{color:var(--brand)}
  .ipf-calc{padding:14px;margin-bottom:14px}
  .ipf-form{display:flex;flex-wrap:wrap;gap:12px 16px;align-items:flex-end}
  .ipf-f{display:flex;flex-direction:column;gap:5px;font-size:12px}.ipf-f>span:first-child{color:var(--text-3);font-weight:600;font-size:11px}
  .ipf-f-wide{flex:1 1 260px}.ipf-f-wide .ipf-sel{width:100%;height:34px}
  .ipf-rsw{display:flex;align-items:center;gap:5px}.ipf-rsw .inp{width:110px;height:32px}
  .ipf-find-c{margin-top:12px;max-width:none}
  .ipf-warn{padding:9px 12px;border-radius:9px;background:color-mix(in srgb,#e8b84a 16%,transparent);color:var(--text);font-size:12.5px;margin-bottom:12px}
  .ipf-chartw{padding:12px 12px 8px}.ipf-chart{width:100%;height:auto;display:block}.ipf-ax{font-size:11px;fill:var(--text-3)}
  .ipf-legend{display:flex;gap:16px;font-size:12px;color:var(--text-2);padding:2px 6px}.ipf-legend i{display:inline-block;width:16px;height:3px;border-radius:2px;margin-right:6px;vertical-align:middle}
  .ipf-legend i.v.up{background:var(--up)}.ipf-legend i.v.down{background:var(--down)}.ipf-legend i.inv{background:repeating-linear-gradient(90deg,var(--text-3) 0 5px,transparent 5px 9px)}
  .ipf-skel{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}.ipf-skel i{height:150px;border-radius:12px;background:linear-gradient(90deg,var(--panel-2),var(--panel),var(--panel-2));background-size:200% 100%;animation:ipfSk 1.2s infinite}
  @keyframes ipfSk{to{background-position:-200% 0}}
  @media (max-width:760px){
    .ipf-q{max-width:none;flex:1 1 140px}.ipf-find{max-width:none;flex-basis:100%}
    .ipf-kpis{grid-template-columns:1fr 1fr}.ipf-grid{grid-template-columns:1fr}
    .ipf-gmp{gap:10px}.ipf-gmp b{font-size:14px}
    .ipf-form{gap:10px}.ipf-f{flex:1 1 40%}.ipf-f-wide{flex-basis:100%}
    .ipf-pager{flex-wrap:wrap}
  }`;
  const st = document.createElement('style'); st.id = 'ipfCss'; st.textContent = css; document.head.appendChild(st);
})();
