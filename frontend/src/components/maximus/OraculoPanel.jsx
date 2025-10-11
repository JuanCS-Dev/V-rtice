/**
import logger from '@/utils/logger';
 * ═══════════════════════════════════════════════════════════════════════════
 * ORÁCULO PANEL - Self-Improvement Visualization
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Visualiza o sistema de auto-melhoria do MAXIMUS:
 * - Sugestões geradas pela AI
 * - Implementações pendentes de aprovação
 * - Histórico de melhorias aplicadas
 * - Estatísticas de self-improvement
 */

import React, { useState, useEffect } from 'react';
import './Panels.css';

export const OraculoPanel = ({ aiStatus, setAiStatus }) => {
  const [suggestions, setSuggestions] = useState([]);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [stats, setStats] = useState({
    totalSessions: 0,
    filesScanned: 0,
    suggestionsGenerated: 0,
    suggestionsImplemented: 0,
    successRate: 0
  });
  const [analysisConfig, setAnalysisConfig] = useState({
    focusCategory: 'all',
    maxSuggestions: 5,
    minConfidence: 0.8,
    dryRun: true
  });
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [lastSession, setLastSession] = useState(null);

  // Fetch Oráculo stats
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('http://localhost:8099/api/v1/oraculo/stats');
        if (response.ok) {
          const data = await response.json();
          if (data.status === 'success') {
            setStats(data.data);
          }
        }
      } catch (error) {
        logger.error('Failed to fetch Oráculo stats:', error);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 15000);
    return () => clearInterval(interval);
  }, []);

  // Fetch pending approvals
  useEffect(() => {
    const fetchPending = async () => {
      try {
        const response = await fetch('http://localhost:8099/api/v1/oraculo/pending-approvals');
        if (response.ok) {
          const data = await response.json();
          if (data.status === 'success') {
            setPendingApprovals(data.data.pending_approvals || []);
          }
        }
      } catch (error) {
        logger.error('Failed to fetch pending approvals:', error);
      }
    };

    fetchPending();
    const interval = setInterval(fetchPending, 10000);
    return () => clearInterval(interval);
  }, []);

  // Run self-improvement analysis
  const runAnalysis = async () => {
    setIsAnalyzing(true);
    setAiStatus(prev => ({
      ...prev,
      oraculo: { ...prev.oraculo, status: 'running' }
    }));

    try {
      const response = await fetch('http://localhost:8099/api/v1/oraculo/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          focus_category: analysisConfig.focusCategory === 'all' ? null : analysisConfig.focusCategory,
          max_suggestions: analysisConfig.maxSuggestions,
          min_confidence: analysisConfig.minConfidence,
          dry_run: analysisConfig.dryRun
        })
      });

      if (response.ok) {
        const result = await response.json();
        if (result.status === 'success') {
          setLastSession(result.data);
          // Refresh stats
          const statsResponse = await fetch('http://localhost:8099/api/v1/oraculo/stats');
          if (statsResponse.ok) {
            const statsData = await statsResponse.json();
            setStats(statsData.data);
          }
        }
      } else {
        logger.error('Analysis failed:', await response.text());
      }
    } catch (error) {
      logger.error('Error running analysis:', error);
    } finally {
      setIsAnalyzing(false);
      setAiStatus(prev => ({
        ...prev,
        oraculo: { ...prev.oraculo, status: 'idle', lastRun: new Date().toLocaleTimeString() }
      }));
    }
  };

  // Approve suggestion
  const approveSuggestion = async (suggestionId) => {
    try {
      const response = await fetch(`http://localhost:8099/api/v1/oraculo/approve/${suggestionId}`, {
        method: 'POST'
      });

      if (response.ok) {
        const result = await response.json();
        logger.debug('Suggestion approved:', result);
        // Refresh pending approvals
        const pendingResponse = await fetch('http://localhost:8099/api/v1/oraculo/pending-approvals');
        if (pendingResponse.ok) {
          const pendingData = await pendingResponse.json();
          setPendingApprovals(pendingData.data.pending_approvals || []);
        }
      }
    } catch (error) {
      logger.error('Error approving suggestion:', error);
    }
  };

  const categories = [
    { value: 'all', label: 'Todas as Categorias', icon: '🎯' },
    { value: 'security', label: 'Segurança', icon: '🔒' },
    { value: 'performance', label: 'Performance', icon: '⚡' },
    { value: 'features', label: 'Features', icon: '✨' },
    { value: 'refactoring', label: 'Refatoração', icon: '🔧' },
    { value: 'documentation', label: 'Documentação', icon: '📚' },
    { value: 'testing', label: 'Testes', icon: '🧪' }
  ];

  return (
    <div className="oraculo-panel">
      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* TOP SECTION - Stats & Controls */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      <div className="panel-top">
        {/* Statistics Cards */}
        <div className="stats-grid">
          <div className="stat-card stat-primary">
            <div className="stat-icon">🔮</div>
            <div className="stat-content">
              <div className="stat-label">Sugestões Geradas</div>
              <div className="stat-value">{stats.suggestionsGenerated || 0}</div>
            </div>
          </div>

          <div className="stat-card stat-success">
            <div className="stat-icon">✅</div>
            <div className="stat-content">
              <div className="stat-label">Implementadas</div>
              <div className="stat-value">{stats.suggestionsImplemented || 0}</div>
            </div>
          </div>

          <div className="stat-card stat-warning">
            <div className="stat-icon">⏳</div>
            <div className="stat-content">
              <div className="stat-label">Pendentes Aprovação</div>
              <div className="stat-value">{pendingApprovals.length}</div>
            </div>
          </div>

          <div className="stat-card stat-info">
            <div className="stat-icon">📊</div>
            <div className="stat-content">
              <div className="stat-label">Taxa de Sucesso</div>
              <div className="stat-value">{stats.successRate || 0}%</div>
            </div>
          </div>
        </div>

        {/* Analysis Control Panel */}
        <div className="analysis-control">
          <div className="control-header">
            <h3>🎯 Executar Análise de Self-Improvement</h3>
            <div className="control-status">
              {aiStatus.oraculo.lastRun && (
                <span className="last-run">Última análise: {aiStatus.oraculo.lastRun}</span>
              )}
            </div>
          </div>

          <div className="control-form">
            <div className="form-row">
              <div className="form-group">
                <label>Categoria de Foco</label>
                <select
                  value={analysisConfig.focusCategory}
                  onChange={(e) => setAnalysisConfig({ ...analysisConfig, focusCategory: e.target.value })}
                  className="form-select"
                >
                  {categories.map(cat => (
                    <option key={cat.value} value={cat.value}>
                      {cat.icon} {cat.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Máximo de Sugestões</label>
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={analysisConfig.maxSuggestions}
                  onChange={(e) => setAnalysisConfig({ ...analysisConfig, maxSuggestions: parseInt(e.target.value) })}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label>Confiança Mínima</label>
                <input
                  type="number"
                  min="0"
                  max="1"
                  step="0.1"
                  value={analysisConfig.minConfidence}
                  onChange={(e) => setAnalysisConfig({ ...analysisConfig, minConfidence: parseFloat(e.target.value) })}
                  className="form-input"
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group-checkbox">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={analysisConfig.dryRun}
                    onChange={(e) => setAnalysisConfig({ ...analysisConfig, dryRun: e.target.checked })}
                  />
                  <span>Modo Dry Run (apenas análise, sem implementação)</span>
                </label>
              </div>

              <button
                onClick={runAnalysis}
                disabled={isAnalyzing}
                className={`btn-analyze ${isAnalyzing ? 'btn-analyzing' : ''}`}
              >
                {isAnalyzing ? (
                  <>
                    <span className="spinner"></span>
                    <span>Analisando...</span>
                  </>
                ) : (
                  <>
                    <span>🚀</span>
                    <span>Iniciar Análise</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* MIDDLE SECTION - Last Session Results */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      {lastSession && (
        <div className="session-results">
          <div className="results-header">
            <h3>📋 Última Sessão de Análise</h3>
            <span className="session-id">ID: {lastSession.session_id}</span>
          </div>

          <div className="results-grid">
            <div className="result-item">
              <span className="result-label">Arquivos Escaneados:</span>
              <span className="result-value">{lastSession.files_scanned}</span>
            </div>
            <div className="result-item">
              <span className="result-label">Sugestões Geradas:</span>
              <span className="result-value">{lastSession.suggestions_generated}</span>
            </div>
            <div className="result-item">
              <span className="result-label">Aguardando Aprovação:</span>
              <span className="result-value">{lastSession.suggestions_awaiting_approval}</span>
            </div>
            <div className="result-item">
              <span className="result-label">Duração:</span>
              <span className="result-value">{lastSession.duration_seconds.toFixed(2)}s</span>
            </div>
          </div>

          <div className="session-message">
            ✅ Análise concluída com sucesso! {lastSession.suggestions_generated} sugestões foram geradas.
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* BOTTOM SECTION - Pending Approvals */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      <div className="pending-approvals">
        <div className="approvals-header">
          <h3>⏳ Sugestões Pendentes de Aprovação Humana</h3>
          <span className="approvals-count">{pendingApprovals.length} pendentes</span>
        </div>

        <div className="approvals-list">
          {pendingApprovals.length === 0 ? (
            <div className="approvals-empty">
              <div className="empty-icon">✅</div>
              <p>Nenhuma sugestão pendente de aprovação</p>
              <small>Execute uma análise para gerar novas sugestões</small>
            </div>
          ) : (
            pendingApprovals.map((approval, index) => (
              <div key={approval.suggestion_id} className="approval-card">
                <div className="approval-header">
                  <span className="approval-id">#{index + 1}</span>
                  <span className="approval-suggestion-id">ID: {approval.suggestion_id}</span>
                </div>

                <div className="approval-content">
                  <div className="approval-info">
                    <div className="info-item">
                      <span className="info-label">Arquivos Modificados:</span>
                      <span className="info-value">{approval.files_modified.length}</span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Branch:</span>
                      <span className="info-value">{approval.branch_name}</span>
                    </div>
                  </div>

                  <div className="approval-files">
                    <span className="files-label">Arquivos:</span>
                    <div className="files-list">
                      {approval.files_modified.map((file, i) => (
                        <span key={i} className="file-tag">{file}</span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="approval-actions">
                  <button
                    onClick={() => approveSuggestion(approval.suggestion_id)}
                    className="btn-approve"
                  >
                    ✅ Aprovar & Implementar
                  </button>
                  <button className="btn-review">
                    👁️ Revisar Código
                  </button>
                  <button className="btn-reject">
                    ❌ Rejeitar
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default OraculoPanel;
