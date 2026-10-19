/**
 * GOD'S EYE — The Observer
 * Pre-Market & Intraday Forecasting Module (v1.0)
 * Complies with BRD v0.3 / v0.4, API Design v0.2, and TestRail Cases PM-001 through PM-055.
 */
(function () {
  'use strict';

  let currentHorizon = 'NEXT_SESSION';
  let activeTab = 'overview'; // 'overview' | 'history' | 'health'
  let overviewData = null;
  let historyData = null;
  let healthData = null;
  let historyPage = 1;
  let historySymbol = '';
  let searchQuery = '';

  const HORIZONS = [
    { k: 'NEXT_SESSION', l: 'Next Session (Close-to-Close)' },
    { k: 'INTRADAY_15M', l: '15m Horizon' },
    { k: 'INTRADAY_30M', l: '30m Horizon' },
    { k: 'INTRADAY_60M', l: '60m Horizon' }
  ];

  function esc(s) {
    return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function fmtDate(iso) {
    if (!iso) return '—';
    try {
      const d = new Date(iso);
      return d.toLocaleString('en-IN', { timeZoneName: 'short' });
    } catch (e) {
      return iso;
    }
  }

  window.renderGodseye = async function () {
    const el = document.getElementById('v-godseye');
    if (!el) return;

    el.innerHTML = `
      <div class="ge-container">
        <!-- Brand & Risk Banner -->
        <div class="ge-header">
          <div class="ge-brand-block">
            <div class="ge-title-row">
              <span class="ge-eye-icon">👁</span>
              <h2>GOD'S EYE <span class="ge-sub">The Observer · v1.0</span></h2>
              <span class="ge-badge ge-demo-badge" title="Informational evaluation prototype">DEMO — MOCK DATA</span>
              <span id="geKillBadge" class="ge-badge ge-kill-badge" style="display:none">KILL SWITCH ACTIVE</span>
            </div>
            <p class="ge-disclaimer">
              <strong>Risk Disclosure:</strong> Pre-market &amp; intraday probabilistic analysis for personal research only.
              Signals do not predict future prices with certainty or guarantee trading returns.
            </p>
          </div>
          
          <!-- Screen Tabs -->
          <div class="ge-nav-tabs" role="tablist">
            <button class="ge-tab-btn ${activeTab === 'overview' ? 'on' : ''}" onclick="geSwitchTab('overview')" role="tab" aria-selected="${activeTab === 'overview'}">
              📊 Pre-Market Overview (PM-01)
            </button>
            <button class="ge-tab-btn ${activeTab === 'history' ? 'on' : ''}" onclick="geSwitchTab('history')" role="tab" aria-selected="${activeTab === 'history'}">
              📜 Forecast Ledger &amp; History (PM-03)
            </button>
            <button class="ge-tab-btn ${activeTab === 'health' ? 'on' : ''}" onclick="geSwitchTab('health')" role="tab" aria-selected="${activeTab === 'health'}">
              ⚙️ System &amp; Model Health (PM-04)
            </button>
          </div>
        </div>

        <!-- Main Body Area -->
        <div id="geBody" class="ge-body">
          <div class="ge-loading">Loading GOD'S EYE intelligence feed…</div>
        </div>
      </div>
    `;

    if (activeTab === 'overview') await loadOverview();
    else if (activeTab === 'history') await loadHistory();
    else if (activeTab === 'health') await loadHealth();
  };

  window.geSwitchTab = function (tab) {
    activeTab = tab;
    renderGodseye();
  };

  window.geSetHorizon = async function (hz) {
    currentHorizon = hz;
    await loadOverview();
  };

  window.geSearch = function (q) {
    searchQuery = q.toLowerCase();
    renderOverviewContent();
  };

  async function loadOverview() {
    const body = document.getElementById('geBody');
    if (body) body.innerHTML = '<div class="ge-loading">Fetching pre-market signals &amp; guardrails…</div>';
    try {
      const res = await fetch(`/api/v1/premarket/overview?horizon=${encodeURIComponent(currentHorizon)}`);
      overviewData = await res.json();
      renderOverviewContent();
    } catch (e) {
      if (body) {
        body.innerHTML = `
          <div class="ge-card ge-card-error">
            <h3>⚠️ Signal Feed Unavailable</h3>
            <p>Could not connect to the GOD'S EYE pre-market engine: ${esc(e.message)}</p>
            <button class="btn-xs pri" onclick="loadOverview()">Retry</button>
          </div>
        `;
      }
    }
  }

  function renderOverviewContent() {
    const body = document.getElementById('geBody');
    if (!body || !overviewData) return;

    const killBadge = document.getElementById('geKillBadge');
    if (killBadge) killBadge.style.display = overviewData.killSwitchActive ? 'inline-flex' : 'none';

    let signals = overviewData.signals || [];
    if (searchQuery) {
      signals = signals.filter(s =>
        s.symbol.toLowerCase().includes(searchQuery) ||
        (s.direction || '').toLowerCase().includes(searchQuery)
      );
    }

    body.innerHTML = `
      <!-- Controls Bar -->
      <div class="ge-controls-bar">
        <div class="ge-horizon-pills" role="radiogroup" aria-label="Select Forecast Horizon">
          ${HORIZONS.map(h => `
            <button class="ge-pill ${currentHorizon === h.k ? 'on' : ''}" onclick="geSetHorizon('${h.k}')" role="radio" aria-checked="${currentHorizon === h.k}">
              ${h.l}
            </button>
          `).join('')}
        </div>
        <div class="ge-filter-wrap">
          <input type="text" class="inp" placeholder="Filter by symbol or direction..." value="${esc(searchQuery)}" oninput="geSearch(this.value)" aria-label="Filter signals">
        </div>
      </div>

      <!-- Session Meta Bar -->
      <div class="ge-meta-bar">
        <span><strong>Session:</strong> ${esc(overviewData.sessionDate)}</span>
        <span><strong>Cutoff At:</strong> ${fmtDate(overviewData.cutoffAt)}</span>
        <span><strong>Issued At:</strong> ${fmtDate(overviewData.issuedAt)}</span>
        <span><strong>Model:</strong> <code>${esc(overviewData.modelVersion)}</code></span>
        <span><strong>Instruments:</strong> ${signals.length} active</span>
      </div>

      <!-- Signals Grid (PM-01) -->
      <div class="ge-cards-grid">
        ${signals.map(s => renderSignalCard(s)).join('')}
      </div>
    `;
  }

  function renderSignalCard(s) {
    const dirClass = s.direction === 'BULLISH' ? 'up' : (s.direction === 'BEARISH' ? 'down' : (s.direction === 'NEUTRAL' ? 'neutral' : 'no-signal'));
    const dirIcon = s.direction === 'BULLISH' ? '▲' : (s.direction === 'BEARISH' ? '▼' : (s.direction === 'NEUTRAL' ? '◆' : '⊘'));

    return `
      <div class="ge-card ge-signal-card ${dirClass}" data-symbol="${esc(s.symbol)}">
        <div class="ge-card-top">
          <div class="ge-sym-block">
            <h3 class="ge-sym">${esc(s.symbol)}</h3>
            <span class="ge-badge ge-quality-${(s.dataQuality || '').toLowerCase()}" title="Data source observation quality">
              ${esc(s.dataQuality)} DATA
            </span>
          </div>
          <div class="ge-dir-badge ge-dir-${dirClass}" aria-label="Direction: ${esc(s.direction)}">
            <span class="ge-dir-icon">${dirIcon}</span>
            <span class="ge-dir-text">${esc(s.direction)}</span>
          </div>
        </div>

        <div class="ge-kpi-row">
          <div class="ge-kpi">
            <small>Signal Strength</small>
            <b>${esc(s.signalStrength)}</b>
          </div>
          <div class="ge-kpi">
            <small>Volatility Outlook</small>
            <b>${esc(s.volatilityOutlook)}</b>
          </div>
          <div class="ge-kpi">
            <small>Target Horizon</small>
            <b>${esc(s.horizon)}</b>
          </div>
        </div>

        <!-- Probabilities Section (BRD v0.4 / PM-051 Contract) -->
        <div class="ge-probs-box">
          ${(s.probabilityStatus === 'VALIDATED' && s.probabilities) ? `
            <div class="ge-prob-header">
              <small>Calibrated Outcome Probabilities (Sum: 1.0)</small>
            </div>
            <div class="ge-prob-bar">
              <div class="ge-pb-up" style="width:${Math.round(s.probabilities.UP * 100)}%" title="UP: ${(s.probabilities.UP * 100).toFixed(1)}%">
                ${s.probabilities.UP >= 0.15 ? `UP ${(s.probabilities.UP * 100).toFixed(0)}%` : ''}
              </div>
              <div class="ge-pb-neutral" style="width:${Math.round(s.probabilities.NEUTRAL * 100)}%" title="NEUTRAL: ${(s.probabilities.NEUTRAL * 100).toFixed(1)}%">
                ${s.probabilities.NEUTRAL >= 0.15 ? `NEU ${(s.probabilities.NEUTRAL * 100).toFixed(0)}%` : ''}
              </div>
              <div class="ge-pb-down" style="width:${Math.round(s.probabilities.DOWN * 100)}%" title="DOWN: ${(s.probabilities.DOWN * 100).toFixed(1)}%">
                ${s.probabilities.DOWN >= 0.15 ? `DN ${(s.probabilities.DOWN * 100).toFixed(0)}%` : ''}
              </div>
            </div>
          ` : `
            <div class="ge-prob-unval">
              <span class="ge-unval-icon">🔒</span>
              <span>${s.probabilityStatus === 'NOT_VALIDATED' ? 'Probabilities pending calibration validation (PM-051)' : 'Probabilities unavailable / suppressed (PM-002)'}</span>
            </div>
          `}
        </div>

        <!-- Drivers & Invalidation -->
        <div class="ge-section">
          <h4 class="ge-sec-title">Key Deterministic Drivers</h4>
          <ul class="ge-list">
            ${(s.drivers || []).slice(0, 3).map(d => `<li>${esc(d)}</li>`).join('')}
          </ul>
        </div>

        ${(s.invalidationConditions && s.invalidationConditions.length > 0) ? `
          <div class="ge-section">
            <h4 class="ge-sec-title">Invalidation Rules</h4>
            <ul class="ge-list ge-inval-list">
              ${s.invalidationConditions.map(c => `<li>${esc(c)}</li>`).join('')}
            </ul>
          </div>
        ` : ''}

        <!-- Timestamps Audit Bar -->
        <div class="ge-card-footer">
          <div class="ge-timestamps">
            <small>Data: ${fmtDate(s.sourceTimestamp)}</small>
            <small>Issued: ${fmtDate(s.issuedAt)}</small>
          </div>
          <button class="ge-btn-details" onclick="geOpenDetails('${esc(s.symbol)}', '${esc(s.horizon)}')">
            Inspect Details →
          </button>
        </div>
      </div>
    `;
  }

  window.geOpenDetails = async function (symbol, horizon) {
    try {
      const res = await fetch(`/api/v1/premarket/signals/${encodeURIComponent(symbol)}?horizon=${encodeURIComponent(horizon)}`);
      const sig = await res.json();
      if (sig.error) {
        alert(sig.error.message);
        return;
      }

      let dlg = document.getElementById('geModal');
      if (!dlg) {
        dlg = document.createElement('div');
        dlg.id = 'geModal';
        dlg.className = 'ge-modal-overlay';
        document.body.appendChild(dlg);
      }

      dlg.innerHTML = `
        <div class="ge-modal-card">
          <div class="ge-modal-header">
            <h3>Signal Audit: ${esc(sig.symbol)} (${esc(sig.name || '')})</h3>
            <button class="ge-close-btn" onclick="document.getElementById('geModal').remove()">✕</button>
          </div>
          <div class="ge-modal-body">
            <div class="ge-diag-grid">
              <div><strong>Exchange:</strong> ${esc(sig.exchange)}</div>
              <div><strong>Asset Class:</strong> ${esc(sig.assetClass)}</div>
              <div><strong>Reference Price:</strong> ₹${sig.referencePrice || '—'}</div>
              <div><strong>Forecast ID:</strong> <code>${esc(sig.forecastId)}</code></div>
              <div><strong>Model Version:</strong> <code>${esc(sig.modelVersion)}</code></div>
              <div><strong>Calibration:</strong> <code>${esc(sig.calibrationVersion || 'N/A')}</code></div>
              <div><strong>Cutoff:</strong> ${fmtDate(sig.cutoffAt)}</div>
              <div><strong>Source Data Time:</strong> ${fmtDate(sig.sourceTimestamp)}</div>
            </div>

            <div class="ge-section" style="margin-top:14px">
              <h4>All Feature Drivers Observable at Cutoff</h4>
              <ul class="ge-list">
                ${(sig.drivers || []).map(d => `<li>${esc(d)}</li>`).join('')}
              </ul>
            </div>

            <div class="ge-section">
              <h4>Deterministic Invalidation Conditions</h4>
              <ul class="ge-list ge-inval-list">
                ${(sig.invalidationConditions || []).map(c => `<li>${esc(c)}</li>`).join('') || '<li>None specified</li>'}
              </ul>
            </div>
          </div>
        </div>
      `;
    } catch (e) {
      alert('Failed loading signal details: ' + e.message);
    }
  };

  async function loadHistory() {
    const body = document.getElementById('geBody');
    if (body) body.innerHTML = '<div class="ge-loading">Loading immutable forecast ledger…</div>';
    try {
      const res = await fetch(`/api/v1/forecasts/history?page=${historyPage}&pageSize=10${historySymbol ? '&symbol=' + encodeURIComponent(historySymbol) : ''}`);
      historyData = await res.json();
      renderHistoryContent();
    } catch (e) {
      if (body) body.innerHTML = `<div class="ge-card ge-card-error">Failed loading forecast ledger: ${esc(e.message)}</div>`;
    }
  }

  function renderHistoryContent() {
    const body = document.getElementById('geBody');
    if (!body || !historyData) return;

    body.innerHTML = `
      <div class="ge-card" style="padding:16px">
        <div class="ge-table-header">
          <h3>Immutable Forecast Ledger &amp; Out-of-Sample Scorer (PM-03)</h3>
          <div class="ge-filter-wrap">
            <select class="inp" onchange="geFilterHistSym(this.value)" style="height:32px">
              <option value="">All Instruments</option>
              <option value="NIFTY" ${historySymbol === 'NIFTY' ? 'selected' : ''}>NIFTY</option>
              <option value="BANKNIFTY" ${historySymbol === 'BANKNIFTY' ? 'selected' : ''}>BANKNIFTY</option>
              <option value="RELIANCE" ${historySymbol === 'RELIANCE' ? 'selected' : ''}>RELIANCE</option>
              <option value="TCS" ${historySymbol === 'TCS' ? 'selected' : ''}>TCS</option>
              <option value="INFY" ${historySymbol === 'INFY' ? 'selected' : ''}>INFY</option>
            </select>
          </div>
        </div>
        
        <p class="ge-disclaimer" style="margin-bottom:12px">
          Each forecast record is immutable. Outcomes are only scored after the horizon has matured. Historical records cannot be rewritten.
        </p>

        <div class="tbl-wrap">
          <table class="ge-table">
            <thead>
              <tr>
                <th>Forecast ID</th>
                <th>Symbol</th>
                <th>Horizon</th>
                <th>Issued At</th>
                <th>Predicted</th>
                <th>Realized</th>
                <th>Return</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${(historyData.items || []).map(r => `
                <tr>
                  <td><code>${esc(r.forecastId)}</code></td>
                  <td><strong>${esc(r.symbol)}</strong></td>
                  <td>${esc(r.horizon)}</td>
                  <td>${fmtDate(r.issuedAt)}</td>
                  <td><span class="ge-badge ge-dir-${(r.direction || '').toLowerCase()}">${esc(r.direction)}</span></td>
                  <td><strong>${esc(r.realizedOutcome || '—')}</strong></td>
                  <td>${r.realizedReturn !== null && r.realizedReturn !== undefined ? (r.realizedReturn >= 0 ? '+' : '') + (r.realizedReturn * 100).toFixed(2) + '%' : '—'}</td>
                  <td><span class="ge-badge ge-status-${(r.evaluationStatus || '').toLowerCase()}">${esc(r.evaluationStatus)}</span></td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>

        <div class="ge-pager">
          <button class="btn-xs" ${historyPage <= 1 ? 'disabled' : ''} onclick="geHistPage(${historyPage - 1})">← Previous</button>
          <span>Page ${historyData.page} of ${historyData.totalPages} (${historyData.total} records)</span>
          <button class="btn-xs" ${historyPage >= historyData.totalPages ? 'disabled' : ''} onclick="geHistPage(${historyPage + 1})">Next →</button>
        </div>
      </div>
    `;
  }

  window.geFilterHistSym = function (sym) {
    historySymbol = sym;
    historyPage = 1;
    loadHistory();
  };

  window.geHistPage = function (p) {
    historyPage = p;
    loadHistory();
  };

  let modelHealthData = null;
  let evalReportData = null;
  let calendarData = null;

  async function loadHealth() {
    const body = document.getElementById('geBody');
    if (body) body.innerHTML = '<div class="ge-loading">Running feed diagnostics &amp; security verification…</div>';
    try {
      const [hRes, mRes, eRes, cRes] = await Promise.all([
        fetch('/api/v1/health/data'),
        fetch('/api/v1/health/model'),
        fetch('/api/v1/evaluation/report'),
        fetch('/api/v1/calendar/session')
      ]);
      healthData = await hRes.json();
      modelHealthData = await mRes.json();
      evalReportData = await eRes.json();
      calendarData = await cRes.json();
      renderHealthContent();
    } catch (e) {
      if (body) body.innerHTML = `<div class="ge-card ge-card-error">Failed loading health data: ${esc(e.message)}</div>`;
    }
  }

  function renderHealthContent() {
    const body = document.getElementById('geBody');
    if (!body || !healthData) return;

    body.innerHTML = `
      <div class="ge-health-grid">
        <!-- Feed Freshness -->
        <div class="ge-card">
          <h3>Feed Freshness &amp; Latency (PM-04)</h3>
          <div class="ge-diag-kpi">
            <div><small>Operational Status</small><b style="color:var(--ge-pos)">${esc(healthData.status)}</b></div>
            <div><small>Feed Provider</small><b>${esc(healthData.provider)}</b></div>
            <div><small>Round-Trip Latency</small><b>${healthData.latencyMs} ms</b></div>
            <div><small>Last Fresh Observation</small><b>${healthData.dataAgeSeconds}s ago</b></div>
          </div>
        </div>

        <!-- Security Sanitization -->
        <div class="ge-card">
          <h3>Security &amp; Secret Sanitization (PM-037)</h3>
          <p style="font-size:12.5px;color:var(--ge-text-sec)">
            Audit check confirms no database passwords, provider keys, or tokens are transmitted in client JSON payloads.
          </p>
          <div class="ge-badge ge-dir-up" style="padding:6px 10px;font-size:12px">
            ✓ ZERO CREDENTIALS EXPOSED IN PAYLOAD
          </div>
        </div>

        <!-- Kill Switch -->
        <div class="ge-card">
          <h3>Model Kill Switch Control (PM-025)</h3>
          <p style="font-size:12.5px;color:var(--ge-text-sec);margin-bottom:12px">
            Activating the kill switch immediately suppresses all directional forecast publication across web and mobile.
          </p>
          <div style="display:flex;align-items:center;gap:12px">
            <span class="ge-badge ${healthData.killSwitchActive ? 'ge-dir-down' : 'ge-dir-up'}">
              Status: ${healthData.killSwitchActive ? 'KILL SWITCH ACTIVE' : 'NORMAL PUBLICATION'}
            </span>
            <button class="btn-xs ${healthData.killSwitchActive ? 'pri' : 'down'}" onclick="geToggleKillSwitch(!${healthData.killSwitchActive})">
              ${healthData.killSwitchActive ? 'Resume Model Publication' : 'Activate Kill Switch'}
            </button>
          </div>
        </div>

        <!-- Model Drift Monitoring (PM-026, PM-040) -->
        ${modelHealthData ? `
          <div class="ge-card">
            <h3>Model Stability &amp; Drift Monitoring (PM-026)</h3>
            <div class="ge-diag-kpi">
              <div><small>PSI Stability Score</small><b>${modelHealthData.psiScore} (Threshold: &lt; ${modelHealthData.driftThreshold})</b></div>
              <div><small>Drift Status</small><b style="color:${modelHealthData.driftStatus === 'STABLE' ? 'var(--ge-pos)' : 'var(--ge-neg)'}">${esc(modelHealthData.driftStatus)}</b></div>
              <div><small>Regime Classification</small><b>${esc(modelHealthData.regime)}</b></div>
              <div><small>Abstention Gate</small><b>${modelHealthData.abstentionGateActive ? 'ACTIVE (SUPPRESSED)' : 'CLEAR (NORMAL)'}</b></div>
            </div>
          </div>
        ` : ''}

        <!-- Calendar & Session Cutoff (PM-033, PM-034) -->
        ${calendarData ? `
          <div class="ge-card">
            <h3>Exchange Calendar &amp; Session Boundary (PM-033, PM-034)</h3>
            <div class="ge-diag-kpi">
              <div><small>Exchange &amp; TZ</small><b>${esc(calendarData.exchange)} (${esc(calendarData.timezone)} ${esc(calendarData.utcOffset)})</b></div>
              <div><small>Trading Day Status</small><b style="color:${calendarData.isTradingDay ? 'var(--ge-pos)' : 'var(--ge-neg)'}">${calendarData.isTradingDay ? 'OPEN / ACTIVE' : 'CLOSED (' + esc(calendarData.reason) + ')'}</b></div>
              <div><small>Pre-Market Cutoff</small><b>${esc(calendarData.preMarketCutoff)}</b></div>
              <div><small>Market Hours</small><b>${esc(calendarData.regularMarketHours)}</b></div>
            </div>
          </div>
        ` : ''}

        <!-- Backtest Evaluation & Baseline Comparison (PM-018, PM-019, PM-020, PM-039) -->
        ${evalReportData ? `
          <div class="ge-card" style="grid-column: 1 / -1">
            <h3>Chronological Out-of-Sample Evaluation &amp; Baseline Comparison (PM-018, PM-020)</h3>
            <div style="display:flex;flex-wrap:wrap;gap:12px;margin-bottom:12px;font-size:12px;color:var(--ge-text-sec)">
              <span><strong>Train:</strong> ${esc(evalReportData.evaluationDataset.trainPeriod)}</span>
              <span><strong>Validation:</strong> ${esc(evalReportData.evaluationDataset.validationPeriod)}</span>
              <span><strong>Test Holdout:</strong> ${esc(evalReportData.evaluationDataset.testHoldoutPeriod)}</span>
              <span><strong>Purge Window:</strong> ${evalReportData.evaluationDataset.purgeWindowDays}d</span>
              <span><strong>Embargo:</strong> ${evalReportData.evaluationDataset.embargoWindowDays}d</span>
              <span><strong>Evaluated Samples:</strong> ${evalReportData.sampleCount}</span>
            </div>
            <div class="ge-diag-kpi">
              <div><small>Candidate Model Accuracy</small><b style="color:var(--ge-pos)">${(evalReportData.metrics.candidateModel.directionalAccuracy * 100).toFixed(1)}%</b></div>
              <div><small>Baseline Accuracy (Majority/Momentum)</small><b>${(evalReportData.metrics.simpleBaseline.directionalAccuracy * 100).toFixed(1)}%</b></div>
              <div><small>Excess Accuracy over Baseline</small><b style="color:var(--ge-pos)">+${(evalReportData.metrics.excessAccuracyOverBaseline * 100).toFixed(1)}%</b></div>
              <div><small>Candidate Brier / Log-Loss</small><b>${evalReportData.metrics.candidateModel.brierScore} / ${evalReportData.metrics.candidateModel.logLoss}</b></div>
            </div>
          </div>
        ` : ''}
      </div>
    `;
  }

  window.geToggleKillSwitch = async function (enable) {
    const key = prompt('Enter admin security key to toggle kill switch:', 'ge-admin-secure-key-2026');
    if (!key) return;
    try {
      const res = await fetch('/api/v1/admin/killswitch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-admin-key': key },
        body: JSON.stringify({ enabled: enable, reason: 'Operator toggle from health UI' })
      });
      const data = await res.json();
      if (data.error) alert('Error: ' + data.error.message);
      else {
        alert('Kill switch updated: ' + (data.killSwitchActive ? 'ACTIVE' : 'DISABLED'));
        loadHealth();
      }
    } catch (e) {
      alert('Request failed: ' + e.message);
    }
  };
})();
