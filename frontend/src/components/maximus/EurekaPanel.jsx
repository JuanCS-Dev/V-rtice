/**
 * ═══════════════════════════════════════════════════════════════════════════
 * EUREKA PANEL - Deep Malware Analysis Interface
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Interface para análise profunda de malware:
 * - Upload e análise de arquivos suspeitos
 * - Detecção de padrões maliciosos (40+ patterns)
 * - Extração de IOCs (IPs, domains, hashes, etc.)
 * - Geração de playbooks de resposta
 * - Visualização de resultados de análise
 */

import React, { useState, useEffect } from 'react';
import './Panels.css';

export const EurekaPanel = ({ aiStatus, setAiStatus }) => {
  const [analysisMode, setAnalysisMode] = useState('upload'); // 'upload' or 'results'
  const [selectedFile, setSelectedFile] = useState(null);
  const [filePath, setFilePath] = useState('');
  const [generatePlaybook, setGeneratePlaybook] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [stats, setStats] = useState({
    totalAnalyses: 0,
    threatsDetected: 0,
    playbooksGenerated: 0,
    avgThreatScore: 0
  });
  const [patterns, setPatterns] = useState([]);

  // Fetch Eureka stats
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('http://localhost:8099/api/v1/eureka/stats');
        if (response.ok) {
          const data = await response.json();
          if (data.status === 'success') {
            setStats(data.data);
          }
        }
      } catch (error) {
        console.error('Failed to fetch Eureka stats:', error);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 15000);
    return () => clearInterval(interval);
  }, []);

  // Fetch available patterns
  useEffect(() => {
    const fetchPatterns = async () => {
      try {
        const response = await fetch('http://localhost:8099/api/v1/eureka/patterns');
        if (response.ok) {
          const data = await response.json();
          if (data.status === 'success') {
            setPatterns(data.data);
          }
        }
      } catch (error) {
        console.error('Failed to fetch patterns:', error);
      }
    };

    fetchPatterns();
  }, []);

  // Handle file analysis
  const analyzeFile = async () => {
    if (!filePath.trim()) {
      alert('Por favor, especifique o caminho do arquivo');
      return;
    }

    setIsAnalyzing(true);
    setAiStatus(prev => ({
      ...prev,
      eureka: { ...prev.eureka, status: 'running' }
    }));

    try {
      const response = await fetch('http://localhost:8099/api/v1/eureka/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_path: filePath,
          generate_playbook: generatePlaybook
        })
      });

      if (response.ok) {
        const result = await response.json();
        if (result.status === 'success') {
          setAnalysisResult(result.data);
          setAnalysisMode('results');

          // Refresh stats
          const statsResponse = await fetch('http://localhost:8099/api/v1/eureka/stats');
          if (statsResponse.ok) {
            const statsData = await statsResponse.json();
            setStats(statsData.data);
          }
        }
      } else {
        const errorData = await response.json();
        alert(`Erro na análise: ${errorData.detail || 'Erro desconhecido'}`);
      }
    } catch (error) {
      console.error('Error analyzing file:', error);
      alert(`Erro: ${error.message}`);
    } finally {
      setIsAnalyzing(false);
      setAiStatus(prev => ({
        ...prev,
        eureka: { ...prev.eureka, status: 'idle', lastAnalysis: new Date().toLocaleTimeString() }
      }));
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return 'severity-critical';
      case 'high': return 'severity-high';
      case 'medium': return 'severity-medium';
      case 'low': return 'severity-low';
      default: return 'severity-info';
    }
  };

  const getThreatScoreColor = (score) => {
    if (score >= 80) return 'threat-critical';
    if (score >= 60) return 'threat-high';
    if (score >= 40) return 'threat-medium';
    if (score >= 20) return 'threat-low';
    return 'threat-minimal';
  };

  return (
    <div className="eureka-panel">
      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* TOP SECTION - Stats */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      <div className="panel-top">
        <div className="stats-grid">
          <div className="stat-card stat-primary">
            <div className="stat-icon">🔬</div>
            <div className="stat-content">
              <div className="stat-label">Análises Realizadas</div>
              <div className="stat-value">{stats.totalAnalyses || 0}</div>
            </div>
          </div>

          <div className="stat-card stat-danger">
            <div className="stat-icon">⚠️</div>
            <div className="stat-content">
              <div className="stat-label">Ameaças Detectadas</div>
              <div className="stat-value">{stats.threatsDetected || 0}</div>
            </div>
          </div>

          <div className="stat-card stat-info">
            <div className="stat-icon">📋</div>
            <div className="stat-content">
              <div className="stat-label">Playbooks Gerados</div>
              <div className="stat-value">{stats.playbooksGenerated || 0}</div>
            </div>
          </div>

          <div className="stat-card stat-warning">
            <div className="stat-icon">📊</div>
            <div className="stat-content">
              <div className="stat-label">Score Médio de Ameaça</div>
              <div className="stat-value">{stats.avgThreatScore || 0}</div>
            </div>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* MODE TOGGLE */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      <div className="mode-toggle">
        <button
          className={`mode-btn ${analysisMode === 'upload' ? 'mode-btn-active' : ''}`}
          onClick={() => setAnalysisMode('upload')}
        >
          📤 Nova Análise
        </button>
        <button
          className={`mode-btn ${analysisMode === 'results' ? 'mode-btn-active' : ''}`}
          onClick={() => setAnalysisMode('results')}
          disabled={!analysisResult}
        >
          📊 Resultados
        </button>
      </div>

      {/* ═══════════════════════════════════════════════════════════════ */}
      {/* UPLOAD MODE */}
      {/* ═══════════════════════════════════════════════════════════════ */}
      {analysisMode === 'upload' && (
        <div className="upload-section">
          <div className="upload-card">
            <div className="upload-header">
              <h3>🔬 Análise Profunda de Malware</h3>
              <p>Especifique o caminho do arquivo suspeito para análise completa</p>
            </div>

            <div className="upload-form">
              <div className="form-group-full">
                <label>Caminho do Arquivo</label>
                <input
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
