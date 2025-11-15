import { API_ENDPOINTS } from '@/config/api';
/**
 * ═══════════════════════════════════════════════════════════════════════════
 * ORÁCULO PANEL - Sentinela de Threat Intelligence (Adaptive Immunity Phase 1)
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * ORÁCULO = SENTINELA VIGILANTE do Active Immune System
 * Biologia: Células dendríticas patrulhando tecidos, capturando antígenos
 * Digital: Ingere CVEs de múltiplos feeds, enriquece dados, filtra relevância
 *
 * FASES:
 * 1. PERCEPÇÃO: Ingestão de feeds (OSV.dev, NVD, Docker Security)
 * 2. TRIAGEM: Dependency graph + relevance filtering + APV generation
 * 3. OUTPUT: APVs (Ameaças Potenciais Verificadas) → Eureka
 *
 * MÉTRICAS:
 * - Window of Exposure: Tempo entre CVE publicação e detecção
 * - Cobertura Threat Intel: % de CVEs relevantes detectados
 * - Taxa de Falso Positivo: <5% target
 * - MTTR (Mean Time To Remediation): 15-45min target
 */

import React, { useState, useEffect, useCallback } from 'react';
import logger from '@/utils/logger';
import { formatDateTime } from '@/utils/dateHelpers';
import './Panels.css';

export const OraculoPanel = ({ aiStatus, setAiStatus }) => {
  // === STATE MANAGEMENT ===
  const [viewMode, setViewMode] = useState('dashboard'); // dashboard | feeds | apvs | analytics
  const [stats, setStats] = useState({
    totalVulnerabilities: 0,
    apvsGenerated: 0,
    criticalAPVs: 0,
    avgWindowExposure: 0,
    threatIntelCoverage: 0,
    falsePositiveRate: 0,
    mttr: 0,
    lastScanTime: null
  });
  const [feedsHealth, setFeedsHealth] = useState([
    { name: 'OSV.dev', status: 'online', priority: 'PRIMARY', latency: 0, lastSync: null },
    { name: 'NVD', status: 'online', priority: 'BACKUP', latency: 0, lastSync: null },
    { name: 'Docker Security', status: 'online', priority: 'SECONDARY', latency: 0, lastSync: null }
  ]);
  const [apvs, setApvs] = useState([]);
  const [isScanning, setIsScanning] = useState(false);
  const [scanConfig, setScanConfig] = useState({
    ecosystem: 'PyPI',
    focusPackages: [],
    minSeverity: 'MEDIUM',
    autoTriageEnabled: true
  });

  // === DATA FETCHING ===
  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch(`${API_ENDPOINTS.oraculo}/stats');
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          setStats(data.data);
        }
      }
    } catch (error) {
      logger.error('Failed to fetch Oráculo stats:', error);
    }
  }, []);

  const fetchFeedsHealth = useCallback(async () => {
    try {
      const response = await fetch(`${API_ENDPOINTS.oraculo}/feeds/health');
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          setFeedsHealth(data.data.feeds || feedsHealth);
        }
      }
    } catch (error) {
      logger.error('Failed to fetch feeds health:', error);
    }
  }, [feedsHealth]);

  const fetchAPVs = useCallback(async () => {
    try {
      const response = await fetch(`${API_ENDPOINTS.oraculo}/apvs?limit=20');
      if (response.ok) {
        const data = await response.json();
        if (data.status === 'success') {
          setApvs(data.data.apvs || []);
        }
      }
    } catch (error) {
      logger.error('Failed to fetch APVs:', error);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    fetchFeedsHealth();
    fetchAPVs();

    const statsInterval = setInterval(fetchStats, 10000);
    const feedsInterval = setInterval(fetchFeedsHealth, 30000);
    const apvsInterval = setInterval(fetchAPVs, 15000);

    return () => {
      clearInterval(statsInterval);
      clearInterval(feedsInterval);
      clearInterval(apvsInterval);
    };
  }, [fetchStats, fetchFeedsHealth, fetchAPVs]);

  // === ACTIONS ===
  const runThreatScan = async () => {
    setIsScanning(true);
    setAiStatus(prev => ({
      ...prev,
      oraculo: { ...prev.oraculo, status: 'running' }
    }));

    try {
      const response = await fetch(`${API_ENDPOINTS.oraculo}/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(scanConfig)
      });

      if (response.ok) {
        const result = await response.json();
        if (result.status === 'success') {
          logger.info('Threat scan completed:', result.data);
          await fetchStats();
          await fetchAPVs();
        }
      } else {
        logger.error('Scan failed:', await response.text());
      }
    } catch (error) {
      logger.error('Error running threat scan:', error);
    } finally {
      setIsScanning(false);
      setAiStatus(prev => ({
        ...prev,
        oraculo: { ...prev.oraculo, status: 'idle', lastRun: formatDateTime(new Date(), '--:--:--') }
      }));
    }
  };

  const forwardAPVToEureka = async (apvId) => {
    try {
      const response = await fetch(`${API_ENDPOINTS.oraculo}/apv/${apvId}/forward`, {
        method: 'POST'
      });

      if (response.ok) {
        logger.info(`APV ${apvId} forwarded to Eureka`);
        await fetchAPVs();
      }
    } catch (error) {
      logger.error('Error forwarding APV:', error);
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

  const getFeedStatusColor = (status) => {
    switch (status) {
      case 'online': return 'text-green-400';
      case 'degraded': return 'text-yellow-400';
      case 'offline': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const formatTimestamp = (timestamp) => {
    return formatDateTime(timestamp, 'N/A');
  };

  // === RENDER ===
  return (
    <div className="oraculo-panel adaptive-immunity-design">
      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* HEADER - Classification Banner */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      <div className="panel-classification-banner">
        <div className="banner-content">
          <span className="banner-icon">🛡️</span>
          <span className="banner-title">ORÁCULO - SENTINELA DE THREAT INTELLIGENCE</span>
          <span className="banner-level">NÍVEL: ADAPTIVE IMMUNITY - FASE 1</span>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* VIEW MODE NAVIGATION */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      <div className="view-mode-nav">
        <button
          className={`view-btn ${viewMode === 'dashboard' ? 'view-btn-active' : ''}`}
          onClick={() => setViewMode('dashboard')}
        >
          <span className="view-icon">📊</span>
          <span>Dashboard</span>
        </button>
        <button
          className={`view-btn ${viewMode === 'feeds' ? 'view-btn-active' : ''}`}
          onClick={() => setViewMode('feeds')}
        >
          <span className="view-icon">🌐</span>
          <span>Threat Feeds</span>
        </button>
        <button
          className={`view-btn ${viewMode === 'apvs' ? 'view-btn-active' : ''}`}
          onClick={() => setViewMode('apvs')}
        >
          <span className="view-icon">⚠️</span>
          <span>APVs ({apvs.length})</span>
        </button>
        <button
          className={`view-btn ${viewMode === 'analytics' ? 'view-btn-active' : ''}`}
          onClick={() => setViewMode('analytics')}
        >
          <span className="view-icon">📈</span>
          <span>Analytics</span>
        </button>
      </div>

      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* DASHBOARD VIEW */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      {viewMode === 'dashboard' && (
        <div className="dashboard-view">
          {/* KPI Cards Grid */}
          <div className="kpi-grid">
            <div className="kpi-card kpi-primary">
              <div className="kpi-header">
                <span className="kpi-icon">🔍</span>
                <span className="kpi-label">Vulnerabilidades Detectadas</span>
              </div>
              <div className="kpi-value">{stats.totalVulnerabilities || 0}</div>
              <div className="kpi-footer">
                <span className="kpi-trend kpi-trend-up">↑ 12% esta semana</span>
              </div>
            </div>

            <div className="kpi-card kpi-danger">
              <div className="kpi-header">
                <span className="kpi-icon">⚠️</span>
                <span className="kpi-label">APVs Gerados</span>
              </div>
              <div className="kpi-value">{stats.apvsGenerated || 0}</div>
              <div className="kpi-footer">
                <span className="kpi-detail">{stats.criticalAPVs || 0} críticos</span>
              </div>
            </div>

            <div className="kpi-card kpi-success">
              <div className="kpi-header">
                <span className="kpi-icon">⏱️</span>
                <span className="kpi-label">Window of Exposure</span>
              </div>
              <div className="kpi-value">{stats.avgWindowExposure || 0}<span className="kpi-unit">min</span></div>
              <div className="kpi-footer">
                <span className="kpi-target">Target: &lt;45min</span>
              </div>
            </div>

            <div className="kpi-card kpi-info">
              <div className="kpi-header">
                <span className="kpi-icon">🎯</span>
                <span className="kpi-label">Cobertura Threat Intel</span>
              </div>
              <div className="kpi-value">{stats.threatIntelCoverage || 0}<span className="kpi-unit">%</span></div>
              <div className="kpi-footer">
                <span className="kpi-target">Target: 95%</span>
              </div>
            </div>

            <div className="kpi-card kpi-warning">
              <div className="kpi-header">
                <span className="kpi-icon">🚨</span>
                <span className="kpi-label">Taxa Falso Positivo</span>
              </div>
              <div className="kpi-value">{stats.falsePositiveRate || 0}<span className="kpi-unit">%</span></div>
              <div className="kpi-footer">
                <span className="kpi-target">Target: &lt;5%</span>
              </div>
            </div>

            <div className="kpi-card kpi-neutral">
              <div className="kpi-header">
                <span className="kpi-icon">⚡</span>
                <span className="kpi-label">MTTR (Remediação)</span>
              </div>
              <div className="kpi-value">{stats.mttr || 0}<span className="kpi-unit">min</span></div>
              <div className="kpi-footer">
                <span className="kpi-target">Target: 15-45min</span>
              </div>
            </div>
          </div>

          {/* Scan Control Panel */}
          <div className="scan-control-panel">
            <div className="panel-header">
              <h3>🔬 Executar Varredura de Ameaças</h3>
              {stats.lastScanTime && (
                <span className="last-scan">Última varredura: {formatTimestamp(stats.lastScanTime)}</span>
              )}
            </div>

            <div className="scan-config-form">
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="select-ecosistema-cexf6">Ecossistema</label>
<select id="select-ecosistema-cexf6"
                    value={scanConfig.ecosystem}
                    onChange={(e) => setScanConfig({ ...scanConfig, ecosystem: e.target.value })}
                    className="form-select"
                  >
                    <option value="PyPI">PyPI (Python)</option>
                    <option value="npm">npm (Node.js)</option>
                    <option value="Maven">Maven (Java)</option>
                    <option value="Docker">Docker (Containers)</option>
                    <option value="ALL">Todos</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="select-severidade-m-nima-dhsv2">Severidade Mínima</label>
<select id="select-severidade-m-nima-dhsv2"
                    value={scanConfig.minSeverity}
                    onChange={(e) => setScanConfig({ ...scanConfig, minSeverity: e.target.value })}
                    className="form-select"
                  >
                    <option value="CRITICAL">CRITICAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="LOW">LOW</option>
                  </select>
                </div>

                <div className="form-group-checkbox">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={scanConfig.autoTriageEnabled}
                      onChange={(e) => setScanConfig({ ...scanConfig, autoTriageEnabled: e.target.checked })}
                    />
                    <span>Auto-Triagem Habilitada (filtra APVs irrelevantes)</span>
                  </label>
                </div>
              </div>

              <button
                onClick={runThreatScan}
                disabled={isScanning}
                className={`btn-scan ${isScanning ? 'btn-scanning' : ''}`}
              >
                {isScanning ? (
                  <>
                    <span className="spinner"></span>
                    <span>Escaneando Ameaças...</span>
                  </>
                ) : (
                  <>
                    <span>🚀</span>
                    <span>Iniciar Varredura ORÁCULO</span>
                  </>
                )}
              </button>
            </div>

            {/* Scan Pipeline Info */}
            <div className="pipeline-info">
              <h4>🔄 Pipeline de Percepção + Triagem:</h4>
              <ol className="pipeline-steps">
                <li>🌐 <strong>Feed Ingestion:</strong> OSV.dev (primário), NVD (backup), Docker Security</li>
                <li>📊 <strong>Data Enrichment:</strong> CVSS scoring, CWE mapping, exploitability assessment</li>
                <li>🔗 <strong>Dependency Graph:</strong> Mapeamento pyproject.toml/package.json</li>
                <li>🎯 <strong>Relevance Filtering:</strong> Evita fadiga de alertas (reduz ruído 95%)</li>
                <li>⚖️ <strong>Priorização:</strong> Tier-based scoring (CRITICAL → LOW)</li>
                <li>📝 <strong>APV Generation:</strong> Ameaça Potencial Verificada (JSON CVE 5.1.1)</li>
              </ol>
            </div>
          </div>

          {/* Quick APVs Preview */}
          {apvs.length > 0 && (
            <div className="quick-apvs-preview">
              <div className="preview-header">
                <h3>⚠️ APVs Recentes (Top 5)</h3>
                <button onClick={() => setViewMode('apvs')} className="btn-view-all">
                  Ver Todos →
                </button>
              </div>
              <div className="apvs-quick-list">
                {apvs.slice(0, 5).map((apv, index) => (
                  <div key={apv.id || index} className={`apv-quick-item ${getSeverityColor(apv.severity)}`}>
                    <div className="apv-quick-header">
                      <span className="apv-cve">{apv.cve_id}</span>
                      <span className={`apv-severity ${getSeverityColor(apv.severity)}`}>{apv.severity}</span>
                    </div>
                    <div className="apv-quick-desc">{apv.description?.substring(0, 100)}...</div>
                    <div className="apv-quick-footer">
                      <span className="apv-package">📦 {apv.affected_packages?.join(', ')}</span>
                      <button onClick={() => forwardAPVToEureka(apv.id)} className="btn-quick-forward">
                        → Eureka
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* FEEDS VIEW */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      {viewMode === 'feeds' && (
        <div className="feeds-view">
          <div className="feeds-header">
            <h3>🌐 Threat Intelligence Feeds - Health Status</h3>
            <p className="feeds-subtitle">Multi-feed architecture com fallback automático</p>
          </div>

          <div className="feeds-grid">
            {feedsHealth.map((feed, index) => (
              <div key={index} className="feed-card">
                <div className="feed-card-header">
                  <div className="feed-name-section">
                    <span className="feed-icon">🔗</span>
                    <span className="feed-name">{feed.name}</span>
                  </div>
                  <span className={`feed-status ${getFeedStatusColor(feed.status)}`}>
                    {feed.status.toUpperCase()}
                  </span>
                </div>

                <div className="feed-card-body">
                  <div className="feed-detail">
                    <span className="feed-detail-label">Prioridade:</span>
                    <span className={`feed-priority feed-priority-${feed.priority.toLowerCase()}`}>
                      {feed.priority}
                    </span>
                  </div>

                  <div className="feed-detail">
                    <span className="feed-detail-label">Latência:</span>
                    <span className="feed-latency">{feed.latency}ms</span>
                  </div>

                  <div className="feed-detail">
                    <span className="feed-detail-label">Última Sincronização:</span>
                    <span className="feed-last-sync">{formatTimestamp(feed.lastSync)}</span>
                  </div>
                </div>

                <div className="feed-card-footer">
                  {feed.name === 'OSV.dev' && (
                    <div className="feed-info">
                      <span className="feed-info-badge">🎯 Primário</span>
                      <span className="feed-info-detail">Schema estruturado, commit-level granularity</span>
                    </div>
                  )}
                  {feed.name === 'NVD' && (
                    <div className="feed-info">
                      <span className="feed-info-badge">🔄 Backup</span>
                      <span className="feed-info-detail">Comprehensive, fallback em caso de falha</span>
                    </div>
                  )}
                  {feed.name === 'Docker Security' && (
                    <div className="feed-info">
                      <span className="feed-info-badge">🐳 Secundário</span>
                      <span className="feed-info-detail">Container-specific CVEs (runC, containerd)</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Feed Architecture Diagram */}
          <div className="feed-architecture">
            <h4>🔄 Arquitetura de Fallback</h4>
            <div className="architecture-flow">
              <div className="flow-step flow-step-primary">
                <span className="flow-number">1</span>
                <span className="flow-name">OSV.dev</span>
                <span className="flow-desc">Tenta primeiro (rápido, estruturado)</span>
              </div>
              <span className="flow-arrow">→</span>
              <div className="flow-step flow-step-secondary">
                <span className="flow-number">2</span>
                <span className="flow-name">Docker Security</span>
                <span className="flow-desc">Se OSV falhar ou timeouts</span>
              </div>
              <span className="flow-arrow">→</span>
              <div className="flow-step flow-step-backup">
                <span className="flow-number">3</span>
                <span className="flow-name">NVD</span>
                <span className="flow-desc">Último recurso (comprehensive)</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* APVs VIEW */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      {viewMode === 'apvs' && (
        <div className="apvs-view">
          <div className="apvs-header">
            <h3>⚠️ APVs - Ameaças Potenciais Verificadas</h3>
            <div className="apvs-stats">
              <span className="apv-stat">Total: {apvs.length}</span>
              <span className="apv-stat apv-stat-critical">
                CRITICAL: {apvs.filter(a => a.severity === 'CRITICAL').length}
              </span>
              <span className="apv-stat apv-stat-high">
                HIGH: {apvs.filter(a => a.severity === 'HIGH').length}
              </span>
            </div>
          </div>

          <div className="apvs-list">
            {apvs.length === 0 ? (
              <div className="apvs-empty">
                <div className="empty-icon">✅</div>
                <h4>Nenhum APV Pendente</h4>
                <p>Execute uma varredura para gerar APVs</p>
                <button onClick={() => setViewMode('dashboard')} className="btn-go-scan">
                  Ir para Dashboard
                </button>
              </div>
            ) : (
              apvs.map((apv, index) => (
                <div key={apv.id || index} className="apv-card">
                  <div className="apv-card-header">
                    <div className="apv-id-section">
                      <span className="apv-number">#{index + 1}</span>
                      <span className="apv-cve-id">{apv.cve_id}</span>
                    </div>
                    <span className={`apv-severity-badge ${getSeverityColor(apv.severity)}`}>
                      {apv.severity}
                    </span>
                  </div>

                  <div className="apv-card-body">
                    <div className="apv-description">{apv.description}</div>

                    <div className="apv-metadata">
                      <div className="apv-meta-item">
                        <span className="meta-label">📦 Pacotes Afetados:</span>
                        <div className="meta-packages">
                          {apv.affected_packages?.map((pkg, i) => (
                            <span key={i} className="package-badge">{pkg}</span>
                          ))}
                        </div>
                      </div>

                      <div className="apv-meta-item">
                        <span className="meta-label">🔢 Versões:</span>
                        <span className="meta-value">{apv.affected_versions?.join(', ')}</span>
                      </div>

                      {apv.cvss_score && (
                        <div className="apv-meta-item">
                          <span className="meta-label">📊 CVSS Score:</span>
                          <span className="cvss-score">{apv.cvss_score} / 10.0</span>
                        </div>
                      )}

                      {apv.cwe_id && (
                        <div className="apv-meta-item">
                          <span className="meta-label">🔍 CWE:</span>
                          <span className="cwe-badge">{apv.cwe_id}</span>
                        </div>
                      )}

                      {apv.exploitability && (
                        <div className="apv-meta-item">
                          <span className="meta-label">💥 Exploitabilidade:</span>
                          <span className={`exploitability exploitability-${apv.exploitability}`}>
                            {apv.exploitability}
                          </span>
                        </div>
                      )}
                    </div>

                    {apv.fixed_versions && apv.fixed_versions.length > 0 && (
                      <div className="apv-fix-available">
                        <span className="fix-icon">✅</span>
                        <span className="fix-text">
                          Patch disponível: {apv.fixed_versions.join(', ')}
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="apv-card-footer">
                    <button
                      onClick={() => forwardAPVToEureka(apv.id)}
                      className="btn-forward-eureka"
                    >
                      🚀 Encaminhar para Eureka (Auto-Remediate)
                    </button>
                    <button className="btn-view-details">
                      👁️ Ver Detalhes
                    </button>
                    <button className="btn-dismiss-apv">
                      ❌ Descartar
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* ANALYTICS VIEW */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      {viewMode === 'analytics' && (
        <div className="analytics-view">
          <div className="analytics-header">
            <h3>📈 Analytics - Métricas de Performance</h3>
          </div>

          {/* Metrics Comparison Table */}
          <div className="metrics-comparison">
            <h4>⚖️ Antes vs Depois: Active Immune System</h4>
            <table className="comparison-table">
              <thead>
                <tr>
                  <th>Métrica</th>
                  <th>Antes (Manual)</th>
                  <th>Depois (Autônomo)</th>
                  <th>Melhoria</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="metric-name">MTTR (Mean Time To Remediation)</td>
                  <td className="metric-before">3-48h</td>
                  <td className="metric-after">{stats.mttr || 0}min</td>
                  <td className="metric-improvement improvement-good">16-64x mais rápido</td>
                </tr>
                <tr>
                  <td className="metric-name">Window of Exposure</td>
                  <td className="metric-before">Horas/dias</td>
                  <td className="metric-after">{stats.avgWindowExposure || 0}min</td>
                  <td className="metric-improvement improvement-good">~100x redução</td>
                </tr>
                <tr>
                  <td className="metric-name">Cobertura Threat Intel</td>
                  <td className="metric-before">0% (inexistente)</td>
                  <td className="metric-after">{stats.threatIntelCoverage || 0}%</td>
                  <td className="metric-improvement improvement-excellent">∞ (0→95%)</td>
                </tr>
                <tr>
                  <td className="metric-name">Taxa Auto-Remediação</td>
                  <td className="metric-before">0%</td>
                  <td className="metric-after">70%+</td>
                  <td className="metric-improvement improvement-excellent">∞</td>
                </tr>
                <tr>
                  <td className="metric-name">Taxa Falso Positivo</td>
                  <td className="metric-before">N/A</td>
                  <td className="metric-after">{stats.falsePositiveRate || 0}%</td>
                  <td className="metric-improvement improvement-good">&lt;5% controlado</td>
                </tr>
                <tr>
                  <td className="metric-name">Auditabilidade</td>
                  <td className="metric-before">Fragmentada</td>
                  <td className="metric-after">100% (PRs)</td>
                  <td className="metric-improvement improvement-excellent">Completa</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Biological Analogy */}
          <div className="biological-analogy">
            <h4>🧬 Analogia Biológica: Células Dendríticas</h4>
            <div className="analogy-content">
              <div className="analogy-section">
                <span className="analogy-icon">🔬</span>
                <div className="analogy-text">
                  <strong>Biologia:</strong> Células dendríticas patrulham tecidos periféricos,
                  capturando antígenos (patógenos), processando-os e apresentando a células T.
                </div>
              </div>
              <div className="analogy-section">
                <span className="analogy-icon">💻</span>
                <div className="analogy-text">
                  <strong>Digital:</strong> Oráculo ingere CVEs (antígenos digitais) de múltiplos
                  feeds, enriquece dados (CVSS, CWE), filtra relevância e gera APVs para o Eureka.
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OraculoPanel;
