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
 * ┌─────────────────────────────────────────────────────────────────┐
 * │ FASE 3: FORMULAÇÃO DE RESPOSTA (Confirmation + Patch)          │
 * │  • Recebe APV do Oráculo (antígeno processado)                 │
 * │  • Confirma vulnerabilidade via ast-grep (determinístico)      │
 * │  • Gera contramedida:                                           │
 * │    - Dependency upgrade (semver-aware)                          │
 * │    - Code patch (LLM APPATCH methodology)                       │
 * │  • Aplica Protocolo Coagulação (WAF temporária)                │
 * └─────────────────────────────────────────────────────────────────┘
 *
 * ┌─────────────────────────────────────────────────────────────────┐
 * │ FASE 4: CRISOL DE WARGAMING (Two-Phase Validation)             │
 * │  • Provisiona K8s ephemeral staging environment                 │
 * │  • Executa test suite completa (pytest)                         │
 * │  • Two-phase adversarial simulation:                            │
 * │    1. Attack vulnerable version → MUST succeed                  │
 * │    2. Attack patched version → MUST fail                        │
 * │  • Valida zero breaking changes                                 │
 * └─────────────────────────────────────────────────────────────────┘
 *
 * ┌─────────────────────────────────────────────────────────────────┐
 * │ FASE 5: INTERFACE HITL (Human-in-the-Loop)                     │
 * │  • Pull Request automatizado (PyGithub)                         │
 * │  • Markdown description contextualmente rica                    │
 * │  • Decisão humana = validação, NÃO investigação                │
 * │  • Git history como immutable audit trail                       │
 * └─────────────────────────────────────────────────────────────────┘
 *
 * KPIs CRÍTICOS:
 * - Auto-Remediation Rate: 70%+ (target: 85%)
 * - Patch Validation Pass: 100% (two-phase attack simulation)
 * - Regression Test Pass: >95%
 * - Mean Time To PR (MTTP): <15min (vs 3-48h manual)
 * - False Positive Rate: <2%
 * - Wargaming Success Rate: 100% (fail-safe validation)
 *
 * ARQUITETURA:
 * - Backend: backend/services/maximus_eureka/
 * - API Endpoints: FastAPI port 8024
 * - WebSocket: Real-time wargaming updates
 * - Database: PostgreSQL adaptive_immunity_db
 * - Git Integration: PyGithub automation
 */

import React, { useState, useEffect, useCallback } from 'react';
import logger from '@/utils/logger';
import './Panels.css';

export const EurekaPanel = ({ aiStatus, setAiStatus }) => {
  // === STATE MANAGEMENT ===
  const [viewMode, setViewMode] = useState('dashboard'); // dashboard | apvs | wargaming | history | prs
  const [stats, setStats] = useState({
    totalRemediations: 0,
    successfulPatches: 0,
    prsGenerated: 0,
    avgTimeToRemedy: 0,         // MTTP (Mean Time To PR)
    autoRemediationRate: 0,      // Target: 70%+
    regressionTestPassRate: 0,   // Target: >95%
    patchValidationRate: 0,      // Target: 100%
    wargamingSuccessRate: 0,     // Target: 100%
    falsePositiveRate: 0,        // Target: <2%
    lastRemediationTime: null
  });
  const [pendingApvs, setPendingApvs] = useState([]);
  const [remediationHistory, setRemediationHistory] = useState([]);
  const [pullRequests, setPullRequests] = useState([]);
  const [selectedApv, setSelectedApv] = useState(null);
  const [isRemediating, setIsRemediating] = useState(false);
  const [wargamingResults, setWargamingResults] = useState(null);
  const [liveWargaming, setLiveWargaming] = useState(null); // WebSocket real-time updates

  // === DATA FETCHING ===
  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8024/api/v1/eureka/stats');
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          setStats(data.data);
        }
      }
    } catch (error) {
      logger.error('[Eureka] Failed to fetch stats:', error);
    }
  }, []);

  const fetchPendingApvs = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8024/api/v1/eureka/pending-apvs');
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          setPendingApvs(data.data.apvs || []);
        }
      }
    } catch (error) {
      logger.error('[Eureka] Failed to fetch pending APVs:', error);
    }
  }, []);

  const fetchRemediationHistory = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8024/api/v1/eureka/history?limit=50');
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          setRemediationHistory(data.data.history || []);
        }
      }
    } catch (error) {
      logger.error('[Eureka] Failed to fetch remediation history:', error);
    }
  }, []);

  const fetchPullRequests = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8024/api/v1/eureka/pull-requests?limit=20');
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          setPullRequests(data.data.prs || []);
        }
      }
    } catch (error) {
      logger.error('[Eureka] Failed to fetch pull requests:', error);
    }
  }, []);

  // === WEBSOCKET - Real-time Wargaming Updates ===
  useEffect(() => {
    let ws = null;
    
    const connectWebSocket = () => {
      try {
        ws = new WebSocket('ws://localhost:8024/ws/wargaming');
        
        ws.onopen = () => {
          logger.info('[Eureka] WebSocket connected - live wargaming updates enabled');
        };
        
        ws.onmessage = (event) => {
          const message = JSON.parse(event.data);
          if (message.type === 'wargaming_update') {
            setLiveWargaming(message.data);
            logger.debug('[Eureka] Wargaming update received:', message.data);
          }
        };
        
        ws.onerror = (error) => {
          logger.error('[Eureka] WebSocket error:', error);
        };
        
        ws.onclose = () => {
          logger.warn('[Eureka] WebSocket closed - attempting reconnect in 5s...');
          setTimeout(connectWebSocket, 5000);
        };
      } catch (error) {
        logger.error('[Eureka] Failed to establish WebSocket:', error);
      }
    };
    
    connectWebSocket();
    
    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  useEffect(() => {
    fetchStats();
    fetchPendingApvs();
    fetchRemediationHistory();
    fetchPullRequests();
    
    const statsInterval = setInterval(fetchStats, 10000);
    const apvsInterval = setInterval(fetchPendingApvs, 15000);
    const historyInterval = setInterval(fetchRemediationHistory, 30000);
    const prsInterval = setInterval(fetchPullRequests, 20000);

    return () => {
      clearInterval(statsInterval);
      clearInterval(apvsInterval);
      clearInterval(historyInterval);
      clearInterval(prsInterval);
    };
  }, [fetchStats, fetchPendingApvs, fetchRemediationHistory, fetchPullRequests]);

  // === ACTIONS ===
  const triggerAutoRemediation = async (apvId, options = {}) => {
    setIsRemediating(true);
    setAiStatus(prev => ({
      ...prev,
      eureka: { ...prev.eureka, status: 'running', currentTask: 'Remediating APV' }
    }));

    try {
      logger.info(`[Eureka] Starting auto-remediation for APV ${apvId}`);
      
      const response = await fetch(`http://localhost:8024/api/v1/eureka/remediate/${apvId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mode: options.mode || 'auto',           // auto | manual | review
          runWargaming: options.wargaming !== false,  // Default true
          generatePR: options.createPR !== false,     // Default true
          strategy: options.strategy || 'smart',  // smart | upgrade | patch
          skipCoagulation: options.skipCoagulation || false
        })
      });

      if (response.ok) {
        const result = await response.json();
        if (result.status === 'success') {
          logger.info('[Eureka] Auto-remediation completed successfully:', result.data);
          
          // Store wargaming results
          if (result.data.wargaming_results) {
            setWargamingResults(result.data.wargaming_results);
          }
          
          // Refresh all data
          await Promise.all([
            fetchStats(),
            fetchPendingApvs(),
            fetchRemediationHistory(),
            fetchPullRequests()
          ]);
          
          // Show success notification (você pode adicionar um toast aqui)
          logger.success(`[Eureka] Remediation complete! PR #${result.data.pr_number} created`);
        } else {
          logger.error('[Eureka] Remediation failed:', result.message);
        }
      } else {
        const errorText = await response.text();
        logger.error('[Eureka] Remediation request failed:', errorText);
      }
    } catch (error) {
      logger.error('[Eureka] Error during remediation:', error);
    } finally {
      setIsRemediating(false);
      setAiStatus(prev => ({
        ...prev,
        eureka: { 
          ...prev.eureka, 
          status: 'idle', 
          lastRun: new Date().toLocaleTimeString(),
          currentTask: null
        }
      }));
    }
  };

  const viewApvDetails = (apv) => {
    setSelectedApv(apv);
    logger.debug('[Eureka] Viewing APV details:', apv);
  };

  const dismissApv = async (apvId) => {
    try {
      const response = await fetch(`http://localhost:8024/api/v1/eureka/dismiss/${apvId}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        logger.info(`[Eureka] APV ${apvId} dismissed`);
        await fetchPendingApvs();
      }
    } catch (error) {
      logger.error('[Eureka] Error dismissing APV:', error);
    }
  };

  // === UTILITY FUNCTIONS ===
  const getSeverityColor = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'CRITICAL': return 'severity-critical';
      case 'HIGH': return 'severity-high';
      case 'MEDIUM': return 'severity-medium';
      case 'LOW': return 'severity-low';
      default: return 'severity-info';
    }
  };

  const getRemediationStatusColor = (status) => {
    switch (status) {
      case 'success': return 'text-green-400';
      case 'pending': return 'text-yellow-400';
      case 'failed': return 'text-red-400';
      case 'in_progress': return 'text-orange-400 animate-pulse';
      case 'wargaming': return 'text-red-400 animate-pulse';
      default: return 'text-gray-400';
    }
  };

  const getStrategyIcon = (strategy) => {
    switch (strategy) {
      case 'upgrade': return '📦';
      case 'patch': return '🔧';
      case 'coagulation': return '🛡️';
      case 'smart': return '🧠';
      default: return '⚙️';
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const formatDuration = (milliseconds) => {
    if (!milliseconds) return 'N/A';
    const seconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const getHealthScore = () => {
    // Calculate overall health based on KPIs
    const scores = [
      stats.autoRemediationRate >= 70 ? 100 : (stats.autoRemediationRate / 70) * 100,
      stats.regressionTestPassRate >= 95 ? 100 : (stats.regressionTestPassRate / 95) * 100,
      stats.patchValidationRate >= 100 ? 100 : stats.patchValidationRate,
      stats.wargamingSuccessRate >= 100 ? 100 : stats.wargamingSuccessRate,
      stats.falsePositiveRate <= 2 ? 100 : (1 - (stats.falsePositiveRate / 2)) * 100
    ];
    
    const avgScore = scores.reduce((a, b) => a + b, 0) / scores.length;
    return Math.round(avgScore);
  };

  const getHealthColor = (score) => {
    if (score >= 90) return 'health-excellent';
    if (score >= 70) return 'health-good';
    if (score >= 50) return 'health-warning';
    return 'health-critical';
  };

  return (
    <div className="eureka-panel adaptive-immunity-panel">
      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* CLASSIFICATION BANNER */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      <div className="panel-classification-banner eureka-banner">
        <div className="banner-content">
          <span className="banner-icon">🦠</span>
          <div className="banner-text">
            <span className="banner-title">EUREKA - CÉLULAS T EFETORAS</span>
            <span className="banner-subtitle">Resposta Automatizada de Vulnerabilidades | Fases 3-5</span>
          </div>
          <div className="banner-health">
            <span className="health-label">Sistema</span>
            <div className={`health-indicator ${getHealthColor(getHealthScore())}`}>
              {getHealthScore()}%
            </div>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* KPI METRICS GRID */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      <div className="kpi-metrics-grid">
        <div className="kpi-metric kpi-primary">
          <div className="kpi-icon">🎯</div>
          <div className="kpi-content">
            <div className="kpi-label">Taxa Auto-Remediação</div>
            <div className="kpi-value">
              {stats.autoRemediationRate || 0}
              <span className="kpi-unit">%</span>
            </div>
            <div className="kpi-target">Target: ≥70% | Elite: ≥85%</div>
          </div>
          <div className={`kpi-status ${stats.autoRemediationRate >= 70 ? 'kpi-success' : 'kpi-warning'}`}>
            {stats.autoRemediationRate >= 85 ? '🏆 ELITE' : stats.autoRemediationRate >= 70 ? '✅ OK' : '⚠️ BELOW'}
          </div>
        </div>

        <div className="kpi-metric kpi-success">
          <div className="kpi-icon">✅</div>
          <div className="kpi-content">
            <div className="kpi-label">Patch Validation</div>
            <div className="kpi-value">
              {stats.patchValidationRate || 0}
              <span className="kpi-unit">%</span>
            </div>
            <div className="kpi-target">Target: 100% (fail-safe)</div>
          </div>
          <div className={`kpi-status ${stats.patchValidationRate === 100 ? 'kpi-success' : 'kpi-danger'}`}>
            {stats.patchValidationRate === 100 ? '✅ PERFECT' : '❌ CRITICAL'}
          </div>
        </div>

        <div className="kpi-metric kpi-info">
          <div className="kpi-icon">🧪</div>
          <div className="kpi-content">
            <div className="kpi-label">Regression Tests</div>
            <div className="kpi-value">
              {stats.regressionTestPassRate || 0}
              <span className="kpi-unit">%</span>
            </div>
            <div className="kpi-target">Target: &gt;95%</div>
          </div>
          <div className={`kpi-status ${stats.regressionTestPassRate >= 95 ? 'kpi-success' : 'kpi-warning'}`}>
            {stats.regressionTestPassRate >= 95 ? '✅ OK' : '⚠️ BELOW'}
          </div>
        </div>

        <div className="kpi-metric kpi-warning">
          <div className="kpi-icon">⚡</div>
          <div className="kpi-content">
            <div className="kpi-label">MTTP (Time To PR)</div>
            <div className="kpi-value">
              {stats.avgTimeToRemedy || 0}
              <span className="kpi-unit">min</span>
            </div>
            <div className="kpi-target">Target: &lt;15min | Manual: 3-48h</div>
          </div>
          <div className={`kpi-status ${stats.avgTimeToRemedy < 15 ? 'kpi-success' : 'kpi-info'}`}>
            {stats.avgTimeToRemedy < 15 ? '⚡ FAST' : '✓ OK'}
          </div>
        </div>

        <div className="kpi-metric kpi-purple">
          <div className="kpi-icon">🎮</div>
          <div className="kpi-content">
            <div className="kpi-label">Wargaming Success</div>
            <div className="kpi-value">
              {stats.wargamingSuccessRate || 0}
              <span className="kpi-unit">%</span>
            </div>
            <div className="kpi-target">Target: 100% (both phases)</div>
          </div>
          <div className={`kpi-status ${stats.wargamingSuccessRate === 100 ? 'kpi-success' : 'kpi-danger'}`}>
            {stats.wargamingSuccessRate === 100 ? '✅ VALIDATED' : '❌ FAILED'}
          </div>
        </div>

        <div className="kpi-metric kpi-danger">
          <div className="kpi-icon">🚨</div>
          <div className="kpi-content">
            <div className="kpi-label">False Positive Rate</div>
            <div className="kpi-value">
              {stats.falsePositiveRate || 0}
              <span className="kpi-unit">%</span>
            </div>
            <div className="kpi-target">Target: &lt;2%</div>
          </div>
          <div className={`kpi-status ${stats.falsePositiveRate < 2 ? 'kpi-success' : 'kpi-warning'}`}>
            {stats.falsePositiveRate < 2 ? '✅ EXCELLENT' : '⚠️ HIGH'}
          </div>
        </div>

        <div className="kpi-metric kpi-neutral">
          <div className="kpi-icon">📊</div>
          <div className="kpi-content">
            <div className="kpi-label">Total Remediations</div>
            <div className="kpi-value">{stats.totalRemediations || 0}</div>
            <div className="kpi-detail">
              {stats.successfulPatches || 0} successful | {stats.prsGenerated || 0} PRs
            </div>
          </div>
        </div>

        <div className="kpi-metric kpi-cyan">
          <div className="kpi-icon">⏰</div>
          <div className="kpi-content">
            <div className="kpi-label">Last Remediation</div>
            <div className="kpi-value-small">
              {stats.lastRemediationTime ? formatTimestamp(stats.lastRemediationTime) : 'Never'}
            </div>
            <div className="kpi-detail">
              {stats.lastRemediationTime 
                ? `${Math.round((Date.now() - new Date(stats.lastRemediationTime)) / 60000)}min ago`
                : 'Awaiting first APV'
              }
            </div>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* VIEW MODE NAVIGATION */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      <div className="view-mode-nav eureka-nav">
        <button
          className={`view-btn ${viewMode === 'dashboard' ? 'view-btn-active' : ''}`}
          onClick={() => setViewMode('dashboard')}
        >
          <span className="view-icon">📊</span>
          <span>Dashboard</span>
        </button>
        <button
          className={`view-btn ${viewMode === 'apvs' ? 'view-btn-active' : ''}`}
          onClick={() => setViewMode('apvs')}
        >
          <span className="view-icon">⚠️</span>
          <span>Pending APVs ({pendingApvs.length})</span>
        </button>
        <button
          className={`view-btn ${viewMode === 'wargaming' ? 'view-btn-active' : ''}`}
          onClick={() => setViewMode('wargaming')}
          disabled={!wargamingResults && !liveWargaming}
        >
          <span className="view-icon">🎮</span>
          <span>Wargaming</span>
          {liveWargaming && <span className="live-badge">LIVE</span>}
        </button>
        <button
          className={`view-btn ${viewMode === 'history' ? 'view-btn-active' : ''}`}
          onClick={() => setViewMode('history')}
        >
          <span className="view-icon">📜</span>
          <span>History ({remediationHistory.length})</span>
        </button>
        <button
          className={`view-btn ${viewMode === 'prs' ? 'view-btn-active' : ''}`}
          onClick={() => setViewMode('prs')}
        >
          <span className="view-icon">🔀</span>
          <span>Pull Requests ({pullRequests.length})</span>
        </button>
      </div>

      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* DASHBOARD VIEW - Overview & Quick Actions */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      {viewMode === 'dashboard' && (
        <div className="dashboard-view">
          {/* Real-time Status Bar */}
          <div className="status-bar-live">
            <div className="status-item">
              <span className="status-label">Sistema:</span>
              <span className={`status-value ${isRemediating ? 'status-active' : 'status-idle'}`}>
                {isRemediating ? '⚡ REMEDIANDO' : '✓ IDLE'}
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">APVs Pendentes:</span>
              <span className={`status-value ${pendingApvs.length > 0 ? 'status-warning' : 'status-success'}`}>
                {pendingApvs.length}
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">Last Activity:</span>
              <span className="status-value status-neutral">
                {aiStatus.eureka?.lastRun || 'Never'}
              </span>
            </div>
            {liveWargaming && (
              <div className="status-item status-item-pulse">
                <span className="status-label">🎮 Wargaming Live:</span>
                <span className="status-value status-active">
                  {liveWargaming.phase} | {liveWargaming.progress}%
                </span>
              </div>
            )}
          </div>

          {/* Quick Stats Cards */}
          <div className="quick-stats-section">
            <h3 className="section-title">📈 Performance Overview</h3>
            <div className="quick-stats-grid">
              <div className="quick-stat-card">
                <div className="quick-stat-header">
                  <span className="quick-stat-icon">⏱️</span>
                  <span className="quick-stat-label">Antes vs Depois</span>
                </div>
                <div className="quick-stat-comparison">
                  <div className="comparison-item">
                    <span className="comparison-label">Manual MTTR:</span>
                    <span className="comparison-value comparison-old">3-48h</span>
                  </div>
                  <div className="comparison-arrow">→</div>
                  <div className="comparison-item">
                    <span className="comparison-label">Auto MTTP:</span>
                    <span className="comparison-value comparison-new">{stats.avgTimeToRemedy || 0}min</span>
                  </div>
                </div>
                <div className="quick-stat-improvement">
                  🚀 {Math.round((3 * 60) / (stats.avgTimeToRemedy || 1))}x mais rápido
                </div>
              </div>

              <div className="quick-stat-card">
                <div className="quick-stat-header">
                  <span className="quick-stat-icon">🎯</span>
                  <span className="quick-stat-label">Eficácia Geral</span>
                </div>
                <div className="quick-stat-gauge">
                  <div className="gauge-circle">
                    <svg viewBox="0 0 100 100" className="gauge-svg">
                      <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(139, 92, 246, 0.2)" strokeWidth="8"/>
                      <circle 
                        cx="50" 
                        cy="50" 
                        r="40" 
                        fill="none" 
                        stroke="#8B5CF6" 
                        strokeWidth="8"
                        strokeDasharray={`${getHealthScore() * 2.51} 251`}
                        transform="rotate(-90 50 50)"
                      />
                    </svg>
                    <div className="gauge-value">{getHealthScore()}%</div>
                  </div>
                </div>
                <div className="quick-stat-detail">
                  Baseado em 5 KPIs críticos
                </div>
              </div>

              <div className="quick-stat-card">
                <div className="quick-stat-header">
                  <span className="quick-stat-icon">📊</span>
                  <span className="quick-stat-label">Throughput (24h)</span>
                </div>
                <div className="quick-stat-bars">
                  <div className="stat-bar">
                    <span className="bar-label">Remediações</span>
                    <div className="bar-container">
                      <div className="bar-fill bar-success" style={{width: `${Math.min(stats.successfulPatches, 20) * 5}%`}}></div>
                    </div>
                    <span className="bar-value">{stats.successfulPatches || 0}</span>
                  </div>
                  <div className="stat-bar">
                    <span className="bar-label">PRs Criados</span>
                    <div className="bar-container">
                      <div className="bar-fill bar-info" style={{width: `${Math.min(stats.prsGenerated, 20) * 5}%`}}></div>
                    </div>
                    <span className="bar-value">{stats.prsGenerated || 0}</span>
                  </div>
                  <div className="stat-bar">
                    <span className="bar-label">Falsos Positivos</span>
                    <div className="bar-container">
                      <div className="bar-fill bar-danger" style={{width: `${stats.falsePositiveRate * 50}%`}}></div>
                    </div>
                    <span className="bar-value">{stats.falsePositiveRate || 0}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Pending APVs Preview */}
          {pendingApvs.length > 0 && (
            <div className="pending-apvs-preview">
              <div className="preview-header">
                <h3>⚠️ APVs Aguardando Remediação (Top 5)</h3>
                <button onClick={() => setViewMode('apvs')} className="btn-view-all">
                  Ver Todos ({pendingApvs.length}) →
                </button>
              </div>
              <div className="apvs-preview-list">
                {pendingApvs.slice(0, 5).map((apv, index) => (
                  <div key={apv.id || index} className={`apv-preview-item ${getSeverityColor(apv.severity)}`}>
                    <div className="apv-preview-header">
                      <span className="apv-number">#{index + 1}</span>
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
                        <span className="meta-packages">
                          📦 {apv.affected_packages?.length || 0} packages
                        </span>
                        <span className="meta-cvss">
                          📊 CVSS: {apv.cvss_score || 'N/A'}
                        </span>
                        {apv.exploitability && (
                          <span className={`meta-exploit exploit-${apv.exploitability}`}>
                            💥 {apv.exploitability}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="apv-preview-actions">
                      <button
                        onClick={() => triggerAutoRemediation(apv.id)}
                        disabled={isRemediating}
                        className="btn-quick-remediate"
                      >
                        {isRemediating ? '⏳' : '🚀'} Auto-Remediar
                      </button>
                      <button onClick={() => viewApvDetails(apv)} className="btn-quick-details">
                        👁️ Detalhes
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Empty State */}
          {pendingApvs.length === 0 && (
            <div className="empty-state-success">
              <div className="empty-icon">✅</div>
              <h3>Nenhum APV Pendente</h3>
              <p>Sistema completamente protegido. Aguardando novas ameaças do Oráculo.</p>
              <div className="empty-stats">
                <span className="empty-stat">Total Remediações: {stats.totalRemediations || 0}</span>
                <span className="empty-stat">Taxa Sucesso: {stats.autoRemediationRate || 0}%</span>
              </div>
            </div>
          )}

          {/* Biological Analogy */}
          <div className="biological-analogy-card">
            <h4>🧬 Analogia Biológica: Células T Efetoras</h4>
            <div className="analogy-grid">
              <div className="analogy-item">
                <span className="analogy-icon">🔬</span>
                <div className="analogy-content">
                  <strong>Biologia:</strong> Células dendríticas apresentam antígenos a células T naive. 
                  Células T ativam-se, diferenciam-se em efetoras e eliminam células infectadas com precisão cirúrgica.
                </div>
              </div>
              <div className="analogy-item">
                <span className="analogy-icon">💻</span>
                <div className="analogy-content">
                  <strong>Digital:</strong> Oráculo detecta CVEs (antígenos) e gera APVs. Eureka recebe APVs,
                  confirma vulnerabilidade (ast-grep), gera patch, valida em wargaming e cria PR automatizado.
                </div>
              </div>
              <div className="analogy-item">
                <span className="analogy-icon">🧠</span>
                <div className="analogy-content">
                  <strong>Memória Adaptativa:</strong> PRs merged viram "memória imunológica". Sistema aprende
                  padrões de vulnerabilidades e melhora estratégias de remediação continuamente.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
          <div className="upload-card">
            <div className="upload-header">
              <h3>🔬 Análise Profunda de Malware</h3>
              <p>Especifique o caminho do arquivo suspeito para análise completa</p>
            </div>

            <div className="upload-form">
              <div className="form-group-full">
                <label htmlFor="input-caminho-do-arquivo-ajeqz">Caminho do Arquivo</label>
<input id="input-caminho-do-arquivo-ajeqz"
                  type="text"
                  value={filePath}
                  onChange={(e) => setFilePath(e.target.value)}
                  placeholder="/path/to/suspicious/file.exe"
                  className="form-input"
                />
                <small className="form-hint">
                  💡 Exemplo: /tmp/malware_sample.bin ou /home/user/suspicious.exe
                </small>
              </div>

              <div className="form-group-checkbox">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={generatePlaybook}
                    onChange={(e) => setGeneratePlaybook(e.target.checked)}
                  />
                  <span>Gerar Playbook de Resposta Automática (ADR-compatible)</span>
                </label>
              </div>

              <button
                onClick={analyzeFile}
                disabled={isAnalyzing || !filePath.trim()}
                className={`btn-analyze ${isAnalyzing ? 'btn-analyzing' : ''}`}
              >
                {isAnalyzing ? (
                  <>
                    <span className="spinner"></span>
                    <span>Analisando Arquivo...</span>
                  </>
                ) : (
                  <>
                    <span>🚀</span>
                    <span>Iniciar Análise EUREKA</span>
                  </>
                )}
              </button>
            </div>

            {/* Analysis Pipeline Info */}
            <div className="pipeline-info">
              <h4>🔄 Pipeline de Análise:</h4>
              <ol className="pipeline-steps">
                <li>🔍 <strong>Pattern Detection:</strong> Escaneamento de 40+ padrões maliciosos</li>
                <li>🌐 <strong>IOC Extraction:</strong> Extração de IPs, domains, hashes, CVEs, etc.</li>
                <li>🎯 <strong>Classification:</strong> Identificação de família e tipo de malware</li>
                <li>⚠️ <strong>Threat Scoring:</strong> Cálculo de score de ameaça (0-100)</li>
                <li>📋 <strong>Playbook Generation:</strong> Geração de resposta automatizada</li>
                <li>📊 <strong>Report:</strong> Relatório completo com evidências</li>
              </ol>
            </div>

            {/* Detected Patterns Info */}
            {patterns && patterns.total_patterns > 0 && (
              <div className="patterns-info">
                <h4>🎯 Padrões Disponíveis ({patterns.total_patterns}):</h4>
                <div className="patterns-grid">
                  {Object.entries(patterns.by_category || {}).map(([category, count]) => (
                    <div key={category} className="pattern-badge">
                      <span className="pattern-name">{category}</span>
                      <span className="pattern-count">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* RESULTS MODE */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      {analysisMode === 'results' && analysisResult && (
        <div className="results-section">
          {/* Classification & Threat Score */}
          <div className="results-header-card">
            <div className="classification-info">
              <h3>🦠 Classificação do Malware</h3>
              <div className="classification-details">
                <div className="detail-item">
                  <span className="detail-label">Família:</span>
                  <span className="detail-value family-tag">{analysisResult.classification.family || 'Unknown'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Tipo:</span>
                  <span className="detail-value type-tag">{analysisResult.classification.type || 'Unknown'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Severidade:</span>
                  <span className={`detail-value severity-badge ${getSeverityColor(analysisResult.severity)}`}>
                    {analysisResult.severity || 'UNKNOWN'}
                  </span>
                </div>
              </div>
            </div>

            <div className="threat-score-display">
              <div className="score-label">THREAT SCORE</div>
              <div className={`score-value ${getThreatScoreColor(analysisResult.threat_score)}`}>
                {analysisResult.threat_score}
                <span className="score-max">/100</span>
              </div>
              <div className="score-bar">
                <div
                  className={`score-fill ${getThreatScoreColor(analysisResult.threat_score)}`}
                  style={{ width: `${analysisResult.threat_score}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Malicious Patterns Detected */}
          {analysisResult.patterns_detected && analysisResult.patterns_detected.length > 0 && (
            <div className="patterns-detected-card">
              <h3>🎯 Padrões Maliciosos Detectados ({analysisResult.patterns_detected.length})</h3>
              <div className="patterns-list">
                {analysisResult.patterns_detected.map((pattern, index) => (
                  <div key={index} className={`pattern-item ${getSeverityColor(pattern.severity)}`}>
                    <div className="pattern-header">
                      <span className="pattern-name">{pattern.name}</span>
                      <span className={`pattern-severity ${getSeverityColor(pattern.severity)}`}>
                        {pattern.severity}
                      </span>
                    </div>
                    <div className="pattern-details">
                      <span className="pattern-category">📂 {pattern.category}</span>
                      <span className="pattern-confidence">🎯 Confiança: {(pattern.confidence * 100).toFixed(0)}%</span>
                      {pattern.mitre_technique && (
                        <span className="pattern-mitre">🔗 MITRE: {pattern.mitre_technique}</span>
                      )}
                    </div>
                    {pattern.matched_content && (
                      <div className="pattern-match">
                        <code>{pattern.matched_content.substring(0, 100)}...</code>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* IOCs Extracted */}
          {analysisResult.iocs && analysisResult.iocs.length > 0 && (
            <div className="iocs-card">
              <h3>🌐 Indicadores de Comprometimento (IOCs) - {analysisResult.iocs.length} encontrados</h3>
              <div className="iocs-grid">
                {analysisResult.iocs.map((ioc, index) => (
                  <div key={index} className="ioc-item">
                    <div className="ioc-type">{ioc.ioc_type}</div>
                    <div className="ioc-value">{ioc.value}</div>
                    <div className="ioc-confidence">
                      Confiança: {(ioc.confidence * 100).toFixed(0)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Playbook Generated */}
          {analysisResult.response_playbook && (
            <div className="playbook-card">
              <h3>📋 Playbook de Resposta Gerado</h3>
              <div className="playbook-info">
                <div className="playbook-header">
                  <span className="playbook-name">{analysisResult.response_playbook.name}</span>
                  <span className="playbook-priority">{analysisResult.response_playbook.priority}</span>
                </div>
                <p className="playbook-description">{analysisResult.response_playbook.description}</p>

                <div className="playbook-actions">
                  <h4>Ações Automáticas ({analysisResult.response_playbook.actions?.length || 0}):</h4>
                  <div className="actions-list">
                    {analysisResult.response_playbook.actions?.map((action, index) => (
                      <div key={index} className="action-item">
                        <span className="action-type">{action.type}</span>
                        <span className="action-desc">{action.description || action.action}</span>
                        {action.requires_approval && (
                          <span className="action-approval">⚠️ Requer Aprovação</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="playbook-mitre">
                  <strong>MITRE ATT&CK:</strong>
                  {analysisResult.response_playbook.mitre_techniques?.map((tech, i) => (
                    <span key={i} className="mitre-tag">{tech}</span>
                  ))}
                </div>
              </div>

              <button className="btn-execute-playbook">
                🚀 Enviar para ADR Core (Executar Resposta)
              </button>
            </div>
          )}

          {/* File Hashes */}
          {analysisResult.file_hashes && (
            <div className="hashes-card">
              <h3>🔐 Hashes do Arquivo</h3>
              <div className="hashes-list">
                <div className="hash-item">
                  <span className="hash-label">MD5:</span>
                  <code className="hash-value">{analysisResult.file_hashes.md5}</code>
                </div>
                <div className="hash-item">
                  <span className="hash-label">SHA1:</span>
                  <code className="hash-value">{analysisResult.file_hashes.sha1}</code>
                </div>
                <div className="hash-item">
                  <span className="hash-label">SHA256:</span>
                  <code className="hash-value">{analysisResult.file_hashes.sha256}</code>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="results-actions">
            <button
              onClick={() => {
                setAnalysisMode('upload');
                setAnalysisResult(null);
                setFilePath('');
              }}
              className="btn-new-analysis"
            >
              🔬 Nova Análise
            </button>
            <button className="btn-export-report">
              📄 Exportar Relatório
            </button>
            <button className="btn-share-threat-intel">
              🌐 Compartilhar com Threat Intel
            </button>
          </div>
        </div>
      )}

      {/* Empty State */}
      {analysisMode === 'results' && !analysisResult && (
        <div className="results-empty">
          <div className="empty-icon">🔬</div>
          <h3>Nenhuma análise realizada ainda</h3>
          <p>Execute uma análise para visualizar os resultados</p>
          <button
            onClick={() => setAnalysisMode('upload')}
            className="btn-start-analysis"
          >
            Iniciar Primeira Análise
          </button>
        </div>
      )}
    </div>
  );
};

export default EurekaPanel;
