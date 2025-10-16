/**
 * ═══════════════════════════════════════════════════════════════════════════
 * 🦠 EUREKA PANEL - CÉLULAS T EFETORAS DO ACTIVE IMMUNE SYSTEM
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * BIOLOGICAL ANALOGY: Células T (T cells) do sistema imune adaptativo
 * - Recebem antígenos processados de células dendríticas (Oráculo)
 * - Diferenciam-se em células efetoras que eliminam patógenos
 * - Geram resposta específica, precisa e memorizada
 *
 * DIGITAL IMPLEMENTATION: Resposta Automatizada de Vulnerabilidades
 * 
 * FASE 3: Formulação de Resposta
 * FASE 4: Crisol de Wargaming  
 * FASE 5: Interface HITL (Human-in-the-Loop)
 *
 * KPIs: Auto-Remediation 70%+, Patch Validation 100%, MTTP <15min
 */

import React, { useState, useEffect, useCallback } from 'react';
import logger from '@/utils/logger';
import { useAPVStream } from '../../hooks/useAPVStream';
import './Panels.css';
import './AdaptiveImmunity.css';

const API_KEY = import.meta.env.VITE_API_KEY || '';

export const EurekaPanel = ({ aiStatus, setAiStatus }) => {
  // WEBSOCKET STREAM - Real-time APV updates
  const {
    status: wsStatus,
    apvs: _liveApvs,
    metrics: _liveMetrics,
    isConnected,
    error: _wsError,
    reconnectAttempts
  } = useAPVStream({
    autoConnect: true,
    onApv: (apv) => {
      logger.info('[Eureka] New APV received via WebSocket:', apv);
      // Add to pending list
      setPendingApvs(prev => [apv, ...prev]);
    },
    onPatch: (patch) => {
      logger.info('[Eureka] Patch update received:', patch);
      // Update remediation history
      setRemediationHistory(prev => [patch, ...prev]);
    },
    onMetrics: (metrics) => {
      logger.info('[Eureka] Metrics update received:', metrics);
      // Update stats from metrics
      if (metrics.eureka) {
        setStats(prev => ({ ...prev, ...metrics.eureka }));
      }
    },
    onConnect: () => {
      logger.info('[Eureka] ✅ WebSocket connected');
      setAiStatus?.(prev => ({ ...prev, eurekaStream: 'connected' }));
    },
    onDisconnect: () => {
      logger.warn('[Eureka] ⚠️ WebSocket disconnected');
      setAiStatus?.(prev => ({ ...prev, eurekaStream: 'disconnected' }));
    },
    onError: (error) => {
      logger.error('[Eureka] ❌ WebSocket error:', error);
      setAiStatus?.(prev => ({ ...prev, eurekaStream: 'error' }));
    }
  });

  // STATE
  const [viewMode, setViewMode] = useState('dashboard');
  const [stats, setStats] = useState({
    totalRemediations: 0,
    successfulPatches: 0,
    prsGenerated: 0,
    avgTimeToRemedy: 0,
    autoRemediationRate: 0,
    regressionTestPassRate: 0,
    patchValidationRate: 0,
    wargamingSuccessRate: 0,
    falsePositiveRate: 0,
    lastRemediationTime: null
  });
  const [pendingApvs, setPendingApvs] = useState([]);
  const [remediationHistory, setRemediationHistory] = useState([]);
  const [pullRequests, setPullRequests] = useState([]);
  const [_selectedApv, setSelectedApv] = useState(null);
  const [isRemediating, setIsRemediating] = useState(false);
  const [wargamingResults, setWargamingResults] = useState(null);
  const [liveWargaming, setLiveWargaming] = useState(null);

  // DATA FETCHING
  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8024/api/v1/eureka/stats');
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') setStats(data.data);
      }
    } catch (error) {
      logger.error('[Eureka] Stats fetch failed:', error);
    }
  }, []);

  const fetchPendingApvs = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8024/api/v1/eureka/pending-apvs');
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') setPendingApvs(data.data.apvs || []);
      }
    } catch (error) {
      logger.error('[Eureka] APVs fetch failed:', error);
    }
  }, []);

  const fetchHistory = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8024/api/v1/eureka/history?limit=50');
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') setRemediationHistory(data.data.history || []);
      }
    } catch (error) {
      logger.error('[Eureka] History fetch failed:', error);
    }
  }, []);

  const fetchPRs = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8024/api/v1/eureka/pull-requests?limit=20');
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') setPullRequests(data.data.prs || []);
      }
    } catch (error) {
      logger.error('[Eureka] PRs fetch failed:', error);
    }
  }, []);

  // WEBSOCKET - Real-time wargaming updates
  useEffect(() => {
    let ws = null;
    
    const connect = () => {
      try {
        ws = new WebSocket('ws://localhost:8024/ws/wargaming');
        ws.onopen = () => logger.info('[Eureka] WebSocket connected');
        ws.onmessage = (event) => {
          const msg = JSON.parse(event.data);
          if (msg.type === 'wargaming_update') {
            setLiveWargaming(msg.data);
          }
        };
        ws.onclose = () => {
          logger.warn('[Eureka] WebSocket closed - reconnecting...');
          setTimeout(connect, 5000);
        };
      } catch (error) {
        logger.error('[Eureka] WebSocket error:', error);
      }
    };
    
    connect();
    return () => ws?.close();
  }, []);

  useEffect(() => {
    fetchStats();
    fetchPendingApvs();
    fetchHistory();
    fetchPRs();
    
    const intervals = [
      setInterval(fetchStats, 10000),
      setInterval(fetchPendingApvs, 15000),
      setInterval(fetchHistory, 30000),
      setInterval(fetchPRs, 20000)
    ];
    
    return () => intervals.forEach(clearInterval);
  }, [fetchStats, fetchPendingApvs, fetchHistory, fetchPRs]);

  // ACTIONS
  const triggerRemediation = async (apvId, options = {}) => {
    setIsRemediating(true);
    setAiStatus(prev => ({
      ...prev,
      eureka: { ...prev.eureka, status: 'running', currentTask: 'Remediating' }
    }));

    try {
      const response = await fetch(`http://localhost:8024/api/v1/eureka/remediate/${apvId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': API_KEY },
        body: JSON.stringify({
          mode: options.mode || 'auto',
          runWargaming: options.wargaming !== false,
          generatePR: options.createPR !== false,
          strategy: options.strategy || 'smart'
        })
      });

      if (response.ok) {
        const result = await response.json();
        if (result.status === 'success') {
          logger.success(`[Eureka] PR #${result.data.pr_number} created!`);
          if (result.data.wargaming_results) {
            setWargamingResults(result.data.wargaming_results);
          }
          await Promise.all([fetchStats(), fetchPendingApvs(), fetchHistory(), fetchPRs()]);
        }
      }
    } catch (error) {
      logger.error('[Eureka] Remediation failed:', error);
    } finally {
      setIsRemediating(false);
      setAiStatus(prev => ({
        ...prev,
        eureka: { ...prev.eureka, status: 'idle', lastRun: new Date().toLocaleTimeString() }
      }));
    }
  };

  // UTILITIES
  const getSeverityColor = (severity) => {
    const map = {
      CRITICAL: 'severity-critical',
      HIGH: 'severity-high',
      MEDIUM: 'severity-medium',
      LOW: 'severity-low'
    };
    return map[severity?.toUpperCase()] || 'severity-info';
  };

  const getHealthScore = () => {
    const scores = [
      stats.autoRemediationRate >= 70 ? 100 : (stats.autoRemediationRate / 70) * 100,
      stats.regressionTestPassRate >= 95 ? 100 : (stats.regressionTestPassRate / 95) * 100,
      stats.patchValidationRate,
      stats.wargamingSuccessRate,
      stats.falsePositiveRate <= 2 ? 100 : (1 - stats.falsePositiveRate / 2) * 100
    ];
    return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
  };

  const formatTime = (timestamp) => {
    if (!timestamp) return 'Never';
    return new Date(timestamp).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const healthScore = getHealthScore();
  const healthColor = healthScore >= 90 ? 'health-excellent' : healthScore >= 70 ? 'health-good' : 'health-warning';

  return (
    <div className="eureka-panel adaptive-immunity-panel">
      {/* CLASSIFICATION BANNER */}
      <div className="panel-classification-banner eureka-banner">
        <div className="banner-content">
          <span className="banner-icon">🦠</span>
          <div className="banner-text">
            <span className="banner-title">EUREKA - CÉLULAS T EFETORAS</span>
            <span className="banner-subtitle">Automated Vulnerability Response | Phases 3-5</span>
          </div>
          {/* WEBSOCKET STATUS INDICATOR */}
          <div className="banner-websocket-status">
            <span className="ws-label">Stream</span>
            <div className={`ws-indicator ${wsStatus}`} title={wsStatus}>
              {isConnected && <span className="ws-dot pulse-glow"></span>}
              {wsStatus === 'reconnecting' && <span className="ws-text">Reconnecting... ({reconnectAttempts})</span>}
              {wsStatus === 'error' && <span className="ws-text">Error</span>}
              {wsStatus === 'connected' && <span className="ws-text">Live</span>}
            </div>
          </div>
          <div className="banner-health">
            <span className="health-label">Health</span>
            <div className={`health-indicator ${healthColor}`}>
              {healthScore}%
            </div>
          </div>
        </div>
      </div>

      {/* KPI METRICS */}
      <div className="kpi-metrics-grid">
        <div className="kpi-metric kpi-primary">
          <div className="kpi-icon">🎯</div>
          <div className="kpi-content">
            <div className="kpi-label">Auto-Remediation Rate</div>
            <div className="kpi-value">{stats.autoRemediationRate || 0}<span className="kpi-unit">%</span></div>
            <div className="kpi-target">Target: ≥70% | Elite: ≥85%</div>
          </div>
          <div className={`kpi-status ${stats.autoRemediationRate >= 70 ? 'kpi-success' : 'kpi-warning'}`}>
            {stats.autoRemediationRate >= 85 ? '🏆' : stats.autoRemediationRate >= 70 ? '✅' : '⚠️'}
          </div>
        </div>

        <div className="kpi-metric kpi-success">
          <div className="kpi-icon">✅</div>
          <div className="kpi-content">
            <div className="kpi-label">Patch Validation</div>
            <div className="kpi-value">{stats.patchValidationRate || 0}<span className="kpi-unit">%</span></div>
            <div className="kpi-target">Target: 100%</div>
          </div>
          <div className={`kpi-status ${stats.patchValidationRate === 100 ? 'kpi-success' : 'kpi-danger'}`}>
            {stats.patchValidationRate === 100 ? '✅' : '❌'}
          </div>
        </div>

        <div className="kpi-metric kpi-info">
          <div className="kpi-icon">🧪</div>
          <div className="kpi-content">
            <div className="kpi-label">Regression Tests</div>
            <div className="kpi-value">{stats.regressionTestPassRate || 0}<span className="kpi-unit">%</span></div>
            <div className="kpi-target">Target: &gt;95%</div>
          </div>
        </div>

        <div className="kpi-metric kpi-warning">
          <div className="kpi-icon">⚡</div>
          <div className="kpi-content">
            <div className="kpi-label">MTTP (Time To PR)</div>
            <div className="kpi-value">{stats.avgTimeToRemedy || 0}<span className="kpi-unit">min</span></div>
            <div className="kpi-target">Target: &lt;15min</div>
          </div>
        </div>

        <div className="kpi-metric kpi-purple">
          <div className="kpi-icon">🎮</div>
          <div className="kpi-content">
            <div className="kpi-label">Wargaming Success</div>
            <div className="kpi-value">{stats.wargamingSuccessRate || 0}<span className="kpi-unit">%</span></div>
            <div className="kpi-target">Target: 100%</div>
          </div>
        </div>

        <div className="kpi-metric kpi-danger">
          <div className="kpi-icon">🚨</div>
          <div className="kpi-content">
            <div className="kpi-label">False Positive Rate</div>
            <div className="kpi-value">{stats.falsePositiveRate || 0}<span className="kpi-unit">%</span></div>
            <div className="kpi-target">Target: &lt;2%</div>
          </div>
        </div>
      </div>

      {/* NAVIGATION */}
      <div className="view-mode-nav">
        {['dashboard', 'apvs', 'wargaming', 'history', 'prs'].map(mode => (
          <button
            key={mode}
            className={`view-btn ${viewMode === mode ? 'view-btn-active' : ''}`}
            onClick={() => setViewMode(mode)}
            disabled={mode === 'wargaming' && !wargamingResults && !liveWargaming}
          >
            <span className="view-icon">
              {mode === 'dashboard' && '📊'}
              {mode === 'apvs' && '⚠️'}
              {mode === 'wargaming' && '🎮'}
              {mode === 'history' && '📜'}
              {mode === 'prs' && '🔀'}
            </span>
            <span>
              {mode.charAt(0).toUpperCase() + mode.slice(1)}
              {mode === 'apvs' && ` (${pendingApvs.length})`}
              {mode === 'prs' && ` (${pullRequests.length})`}
            </span>
            {mode === 'wargaming' && liveWargaming && <span className="live-badge">LIVE</span>}
          </button>
        ))}
      </div>

      {/* DASHBOARD VIEW */}
      {viewMode === 'dashboard' && (
        <div className="dashboard-view">
          <div className="status-bar-live">
            <div className="status-item">
              <span className="status-label">Status:</span>
              <span className={`status-value ${isRemediating ? 'status-active' : 'status-idle'}`}>
                {isRemediating ? '⚡ ACTIVE' : '✓ IDLE'}
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">Pending APVs:</span>
              <span className={`status-value ${pendingApvs.length > 0 ? 'status-warning' : 'status-success'}`}>
                {pendingApvs.length}
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">Last Activity:</span>
              <span className="status-value">{aiStatus.eureka?.lastRun || 'Never'}</span>
            </div>
          </div>

          {pendingApvs.length > 0 ? (
            <div className="pending-apvs-preview">
              <div className="preview-header">
                <h3>⚠️ Pending APVs (Top 5)</h3>
                <button onClick={() => setViewMode('apvs')} className="btn-view-all">
                  View All ({pendingApvs.length}) →
                </button>
              </div>
              <div className="apvs-preview-list">
                {pendingApvs.slice(0, 5).map((apv, idx) => (
                  <div key={apv.id || idx} className={`apv-preview-item ${getSeverityColor(apv.severity)}`}>
                    <div className="apv-preview-header">
                      <span className="apv-number">#{idx + 1}</span>
                      <span className="apv-cve">{apv.cve_id}</span>
                      <span className={`apv-severity-badge ${getSeverityColor(apv.severity)}`}>
                        {apv.severity}
                      </span>
                    </div>
                    <div className="apv-preview-body">
                      <div className="apv-description-short">
                        {apv.description?.substring(0, 120)}...
                      </div>
                      <div className="apv-meta-short">
                        <span>📦 {apv.affected_packages?.length || 0} packages</span>
                        <span>📊 CVSS: {apv.cvss_score || 'N/A'}</span>
                      </div>
                    </div>
                    <div className="apv-preview-actions">
                      <button
                        onClick={() => triggerRemediation(apv.id)}
                        disabled={isRemediating}
                        className="btn-quick-remediate"
                      >
                        🚀 Auto-Remediate
                      </button>
                      <button onClick={() => setSelectedApv(apv)} className="btn-quick-details">
                        👁️ Details
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="empty-state-success">
              <div className="empty-icon">✅</div>
              <h3>No Pending APVs</h3>
              <p>All threats remediated. System fully protected.</p>
              <div className="empty-stats">
                <span>Total: {stats.totalRemediations || 0}</span>
                <span>Success Rate: {stats.autoRemediationRate || 0}%</span>
              </div>
            </div>
          )}

          {/* Biological Analogy */}
          <div className="biological-analogy-card">
            <h4>🧬 Biological Analogy: T Cells</h4>
            <div className="analogy-grid">
              <div className="analogy-item">
                <span className="analogy-icon">🔬</span>
                <strong>Biology:</strong> Dendritic cells present antigens to naive T cells.
                T cells activate, differentiate into effectors, and eliminate infected cells with surgical precision.
              </div>
              <div className="analogy-item">
                <span className="analogy-icon">💻</span>
                <strong>Digital:</strong> Oráculo detects CVEs (antigens) and generates APVs.
                Eureka receives APVs, confirms vulnerability, generates patches, validates via wargaming, and creates automated PRs.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* APVS VIEW */}
      {viewMode === 'apvs' && (
        <div className="apvs-view">
          <h3>⚠️ Pending APVs ({pendingApvs.length})</h3>
          {pendingApvs.length === 0 ? (
            <div className="empty-state">✅ No pending APVs</div>
          ) : (
            <div className="apvs-list">
              {pendingApvs.map((apv, idx) => (
                <div key={apv.id || idx} className={`apv-card ${getSeverityColor(apv.severity)}`}>
                  <div className="apv-header">
                    <span className="apv-cve">{apv.cve_id}</span>
                    <span className={`apv-severity ${getSeverityColor(apv.severity)}`}>{apv.severity}</span>
                  </div>
                  <div className="apv-body">
                    <p>{apv.description}</p>
                    <div className="apv-meta">
                      <span>📦 {apv.affected_packages?.join(', ')}</span>
                      <span>🔢 {apv.affected_versions?.join(', ')}</span>
                      <span>📊 CVSS: {apv.cvss_score}</span>
                    </div>
                  </div>
                  <div className="apv-actions">
                    <button onClick={() => triggerRemediation(apv.id)} disabled={isRemediating} className="btn-remediate">
                      🚀 Auto-Remediate
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* WARGAMING VIEW */}
      {viewMode === 'wargaming' && (wargamingResults || liveWargaming) && (
        <div className="wargaming-view">
          <h3>🎮 Wargaming Results</h3>
          {liveWargaming && (
            <div className="wargaming-live">
              <div className="live-status">LIVE: {liveWargaming.phase} - {liveWargaming.progress}%</div>
              <div className="progress-bar">
                <div className="progress-fill" style={{width: `${liveWargaming.progress}%`}}></div>
              </div>
            </div>
          )}
          {wargamingResults && (
            <div className="wargaming-results">
              <div className="result-card">
                <h4>Phase 1: Attack Vulnerable Version</h4>
                <div className={`result-status ${wargamingResults.phase1_success ? 'success' : 'failed'}`}>
                  {wargamingResults.phase1_success ? '✅ Attack Succeeded (Expected)' : '❌ Attack Failed (Unexpected)'}
                </div>
              </div>
              <div className="result-card">
                <h4>Phase 2: Attack Patched Version</h4>
                <div className={`result-status ${!wargamingResults.phase2_success ? 'success' : 'failed'}`}>
                  {!wargamingResults.phase2_success ? '✅ Attack Blocked (Expected)' : '❌ Attack Succeeded (CRITICAL)'}
                </div>
              </div>
              <div className="result-card">
                <h4>Regression Tests</h4>
                <div className="test-results">
                  Passed: {wargamingResults.tests_passed} / {wargamingResults.tests_total}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* HISTORY VIEW */}
      {viewMode === 'history' && (
        <div className="history-view">
          <h3>📜 Remediation History ({remediationHistory.length})</h3>
          <div className="history-list">
            {remediationHistory.map((item, idx) => (
              <div key={item.id || idx} className="history-item">
                <div className="history-header">
                  <span>{item.cve_id}</span>
                  <span className={getSeverityColor(item.severity)}>{item.severity}</span>
                  <span className={item.status === 'success' ? 'text-green-400' : 'text-red-400'}>
                    {item.status}
                  </span>
                </div>
                <div className="history-meta">
                  <span>Strategy: {item.strategy}</span>
                  <span>Time: {formatTime(item.timestamp)}</span>
                  <span>Duration: {item.duration_minutes}min</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* PRS VIEW */}
      {viewMode === 'prs' && (
        <div className="prs-view">
          <h3>🔀 Pull Requests ({pullRequests.length})</h3>
          <div className="prs-list">
            {pullRequests.map((pr, idx) => (
              <div key={pr.number || idx} className="pr-card">
                <div className="pr-header">
                  <span className="pr-number">PR #{pr.number}</span>
                  <span className={`pr-status pr-${pr.state}`}>{pr.state}</span>
                </div>
                <div className="pr-body">
                  <h4>{pr.title}</h4>
                  <div className="pr-meta">
                    <span>CVE: {pr.cve_id}</span>
                    <span>Created: {formatTime(pr.created_at)}</span>
                    {pr.merged_at && <span>Merged: {formatTime(pr.merged_at)}</span>}
                  </div>
                </div>
                <div className="pr-actions">
                  <a href={pr.html_url} target="_blank" rel="noopener noreferrer" className="btn-view-pr">
                    View on GitHub →
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default EurekaPanel;
