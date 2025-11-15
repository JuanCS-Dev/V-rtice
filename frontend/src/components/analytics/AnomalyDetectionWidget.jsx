/**
 * Anomaly Detection Widget
 *
 * Detecta anomalias usando Statistical + ML
 * Métodos: Z-score, IQR, Isolation Forest, LSTM Autoencoders
 */

import React, { useState } from 'react';
import { detectAnomalies, getConfidenceBadge, formatExecutionTime } from '../../api/worldClassTools';

const AnomalyDetectionWidget = () => {
  const [dataInput, setDataInput] = useState('');
  const [method, setMethod] = useState('isolation_forest');
  const [sensitivity, setSensitivity] = useState(0.05);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const methods = [
    { value: 'zscore', label: 'Z-Score (Statistical)' },
    { value: 'iqr', label: 'IQR (Interquartile Range)' },
    { value: 'isolation_forest', label: 'Isolation Forest (ML)' },
    { value: 'lstm', label: 'LSTM Autoencoder (Deep Learning)' }
  ];

  const handleDetect = async () => {
    if (!dataInput.trim()) {
      setError('Dados são obrigatórios');
      return;
    }

    // Parse data input (comma-separated numbers)
    let data;
    try {
      data = dataInput.split(',').map(val => parseFloat(val.trim())).filter(val => !isNaN(val));

      if (data.length < 10) {
        setError('Mínimo de 10 valores necessários para análise');
        return;
      }
    } catch (err) {
      setError('Formato inválido. Use números separados por vírgula (ex: 1.2, 1.3, 15.7, 1.4)');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await detectAnomalies(data, {
        method,
        sensitivity
      });

      setResult(response.result);
    } catch (err) {
      setError(err.message || 'Erro ao detectar anomalias');
    } finally {
      setLoading(false);
    }
  };

  const confidenceBadge = result ? getConfidenceBadge(result.confidence) : null;

  // Generate sample data
  const generateSampleData = () => {
    const baseline = Array.from({ length: 40 }, () => 1.2 + Math.random() * 0.3);
    const anomalies = [15.7, 0.2, 18.3]; // Add some anomalies
    const shuffled = [...baseline.slice(0, 20), anomalies[0], ...baseline.slice(20, 30), anomalies[1], ...baseline.slice(30), anomalies[2]];
    setDataInput(shuffled.map(v => v.toFixed(2)).join(', '));
  };

  return (
    <div className="anomaly-detection-widget analytics-widget">
      {/* Header */}
      <div className="widget-header">
        <div className="header-left">
          <i className="fas fa-chart-line"></i>
          <h3>ANOMALY DETECTION</h3>
        </div>
        <div className="header-badge">
          <span className="badge-analytics">ML + STATS</span>
        </div>
      </div>

      {/* Input Section */}
      <div className="widget-body">
        <div className="input-section">
          {/* Data Input */}
          <div className="form-group">
            <label htmlFor="anomaly-data-input">Dados (separados por vírgula):</label>
            <textarea
              id="anomaly-data-input"
              className="analytics-textarea"
              placeholder="1.2, 1.3, 1.1, 15.7, 1.4, 1.3, 1.2, ..."
              value={dataInput}
              onChange={(e) => setDataInput(e.target.value)}
              rows={4}
              disabled={loading}
            />
            <button className="sample-button" onClick={generateSampleData} disabled={loading}>
              <i className="fas fa-magic"></i> Gerar Dados de Exemplo
            </button>
          </div>

          {/* Method Selection */}
          <div className="form-group">
            <label htmlFor="anomaly-method-select">Método de Detecção:</label>
            <select
              id="anomaly-method-select"
              className="analytics-select"
              value={method}
              onChange={(e) => setMethod(e.target.value)}
              disabled={loading}
            >
              {methods.map(m => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>

          {/* Sensitivity Slider */}
          <div className="form-group">
            <label htmlFor="anomaly-sensitivity-slider">Sensibilidade: {(sensitivity * 100).toFixed(0)}%</label>
            <input
              id="anomaly-sensitivity-slider"
              type="range"
              className="analytics-slider"
              min="0.01"
              max="0.2"
              step="0.01"
              value={sensitivity}
              onChange={(e) => setSensitivity(parseFloat(e.target.value))}
              disabled={loading}
            />
            <div className="slider-labels">
              <span>Baixa (1%)</span>
              <span>Alta (20%)</span>
            </div>
          </div>

          {/* Detect Button */}
          <button
            className="analytics-button primary"
            onClick={handleDetect}
            disabled={loading || !dataInput.trim()}
          >
            {loading ? (
              <><i className="fas fa-spinner fa-spin"></i> ANALISANDO...</>
            ) : (
              <><i className="fas fa-brain"></i> DETECTAR ANOMALIAS</>
            )}
          </button>
        </div>

        {/* Error */}
        {error && (
          <div className="alert error">
            <i className="fas fa-exclamation-triangle"></i>
            <span>{error}</span>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="results-section">
            {/* Status Bar */}
            <div className="status-bar">
              <div className="status-item">
                <span className="label">STATUS:</span>
                <span className={`value status-${result.status}`}>
                  {result.status === 'success' ? '✓ SUCCESS' : '✗ FAILED'}
                </span>
              </div>
              <div className="status-item">
                <span className="label">CONFIDENCE:</span>
                <span className={`value ${confidenceBadge.className}`}>
                  {confidenceBadge.icon} {result.confidence.toFixed(1)}%
                </span>
              </div>
              <div className="status-item">
                <span className="label">TEMPO:</span>
                <span className="value">{formatExecutionTime(result.execution_time_ms)}</span>
              </div>
            </div>

            {/* Summary Card */}
            <div className="summary-card">
              <div className="summary-header">
                <h4><i className="fas fa-chart-bar"></i> Resumo da Análise</h4>
              </div>
              <div className="summary-grid">
                <div className="summary-stat">
                  <span className="stat-icon icon-danger">
                    <i className="fas fa-exclamation-circle"></i>
                  </span>
                  <div className="stat-content">
                    <span className="stat-value">{result.anomalies_found || 0}</span>
                    <span className="stat-label">Anomalias Detectadas</span>
                  </div>
                </div>

                <div className="summary-stat">
                  <span className="stat-icon icon-info">
                    <i className="fas fa-database"></i>
                  </span>
                  <div className="stat-content">
                    <span className="stat-value">
                      {dataInput.split(',').filter(v => v.trim()).length}
                    </span>
                    <span className="stat-label">Pontos Analisados</span>
                  </div>
                </div>

                <div className="summary-stat">
                  <span className="stat-icon icon-warning">
                    <i className="fas fa-percentage"></i>
                  </span>
                  <div className="stat-content">
                    <span className="stat-value">
                      {result.anomalies_found && dataInput.split(',').length > 0
                        ? ((result.anomalies_found / dataInput.split(',').length) * 100).toFixed(1)
                        : 0}%
                    </span>
                    <span className="stat-label">Taxa de Anomalia</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Baseline Statistics */}
            {result.baseline_stats && (
              <div className="baseline-card">
                <h5><i className="fas fa-chart-area"></i> Estatísticas de Baseline</h5>
                <div className="baseline-grid">
                  <div className="baseline-stat">
                    <span className="label">Média:</span>
                    <span className="value">{result.baseline_stats.mean?.toFixed(3) || 'N/A'}</span>
                  </div>
                  <div className="baseline-stat">
                    <span className="label">Desvio Padrão:</span>
                    <span className="value">{result.baseline_stats.std?.toFixed(3) || 'N/A'}</span>
                  </div>
                  <div className="baseline-stat">
                    <span className="label">Mediana:</span>
                    <span className="value">{result.baseline_stats.median?.toFixed(3) || 'N/A'}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Anomalies List */}
            {result.anomalies && result.anomalies.length > 0 && (
              <div className="anomalies-list">
                <h5>
                  <i className="fas fa-exclamation-triangle"></i>
                  Anomalias Detectadas ({result.anomalies.length})
                </h5>
                {result.anomalies.map((anomaly, index) => (
                  <div key={index} className="anomaly-card" data-severity={anomaly.severity?.toLowerCase()}>
                    <div className="anomaly-header">
                      <span className="anomaly-index">#{index + 1}</span>
                      <span className={`anomaly-severity ${anomaly.severity?.toLowerCase()}`}>
                        {anomaly.severity || 'MEDIUM'}
                      </span>
                    </div>
                    <div className="anomaly-body">
                      <div className="anomaly-info">
                        <div className="info-item">
                          <span className="label">Índice:</span>
                          <span className="value">{anomaly.index}</span>
                        </div>
                        <div className="info-item">
                          <span className="label">Valor:</span>
                          <span className="value highlight">{anomaly.value?.toFixed(3)}</span>
                        </div>
                        <div className="info-item">
                          <span className="label">Score:</span>
                          <span className="value">{(anomaly.anomaly_score * 100).toFixed(1)}%</span>
                        </div>
                      </div>
                      <div className="anomaly-description">
                        {anomaly.description}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* No Anomalies Found */}
            {result.anomalies_found === 0 && (
              <div className="no-anomalies">
                <i className="fas fa-check-circle"></i>
                <p>Nenhuma anomalia detectada. Dados dentro do padrão esperado.</p>
              </div>
            )}

            {/* Recommendations */}
            {result.recommendations && result.recommendations.length > 0 && (
              <div className="recommendations">
                <h5>
                  <i className="fas fa-lightbulb"></i>
                  Recomendações
                </h5>
                {result.recommendations.map((rec, index) => (
                  <div key={index} className="recommendation-item">
                    {rec}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Styles */}
      <style jsx>{`
        .anomaly-detection-widget {
          background: linear-gradient(135deg, rgba(10, 14, 26, 0.95), rgba(0, 170, 255, 0.05));
          border: 1px solid rgba(0, 170, 255, 0.3);
          border-radius: 8px;
          padding: 20px;
          backdrop-filter: blur(10px);
          max-width: 900px;
        }

        .widget-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          padding-bottom: 15px;
          border-bottom: 1px solid rgba(0, 170, 255, 0.2);
        }

        .header-left {
          display: flex;
          align-items: center;
          gap: 12px;
          color: #00aaff;
        }

        .header-left i {
          font-size: 1.5rem;
        }

        .header-left h3 {
          margin: 0;
          font-size: 1.1rem;
          font-weight: 700;
          letter-spacing: 1px;
        }

        .badge-analytics {
          background: linear-gradient(90deg, #00aaff, #0088ff);
          color: #000;
          padding: 4px 12px;
          border-radius: 4px;
          font-size: 0.7rem;
          font-weight: bold;
          letter-spacing: 1px;
        }

        .widget-body {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .input-section {
          display: flex;
          flex-direction: column;
          gap: 15px;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .form-group label {
          font-size: 0.85rem;
          color: #8a99c0;
          font-weight: 600;
        }

        .analytics-textarea {
          background: rgba(0, 170, 255, 0.05);
          border: 1px solid rgba(0, 170, 255, 0.3);
          color: #00aaff;
          padding: 12px;
          border-radius: 4px;
          font-size: 0.85rem;
          font-family: 'Courier New', monospace;
          resize: vertical;
        }

        .analytics-textarea:focus {
          /* Boris Cherny Standard - WCAG 2.1 AAA: Focus Indicator (GAP #26) */
          outline: 3px solid #00aaff;
          outline-offset: 2px;
          border-color: #00aaff;
          box-shadow: 0 0 10px rgba(0, 170, 255, 0.3);
        }

        .sample-button {
          align-self: flex-start;
          background: rgba(0, 170, 255, 0.1);
          border: 1px solid rgba(0, 170, 255, 0.3);
          color: #00aaff;
          padding: 6px 12px;
          border-radius: 4px;
          font-size: 0.75rem;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 6px;
          transition: all 0.3s ease;
        }

        .sample-button:hover:not(:disabled) {
          background: rgba(0, 170, 255, 0.2);
          border-color: #00aaff;
        }

        .analytics-select {
          background: rgba(0, 170, 255, 0.05);
          border: 1px solid rgba(0, 170, 255, 0.3);
          color: #00aaff;
          padding: 10px;
          border-radius: 4px;
          font-size: 0.85rem;
          cursor: pointer;
        }

        .analytics-select:focus {
          /* Boris Cherny Standard - WCAG 2.1 AAA: Focus Indicator (GAP #26) */
          outline: 3px solid #00aaff;
          outline-offset: 2px;
          border-color: #00aaff;
        }

        .analytics-slider {
          width: 100%;
          height: 6px;
          border-radius: 3px;
          background: rgba(0, 170, 255, 0.1);
          /* Boris Cherny Standard - WCAG 2.1 AAA: Focus Indicator (GAP #26) */
          outline: 3px solid transparent;
          outline-offset: 2px;
          -webkit-appearance: none;
        }

        .analytics-slider:focus {
          /* Boris Cherny Standard - WCAG 2.1 AAA: Focus Indicator (GAP #26) */
          outline: 3px solid #00aaff;
          outline-offset: 2px;
          box-shadow: 0 0 10px rgba(0, 170, 255, 0.5);
        }

        .analytics-slider::-webkit-slider-thumb {
          -webkit-appearance: none;
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: #00aaff;
          cursor: pointer;
          box-shadow: 0 0 10px rgba(0, 170, 255, 0.5);
        }

        .slider-labels {
          display: flex;
          justify-content: space-between;
          font-size: 0.7rem;
          color: #8a99c0;
        }

        .analytics-button {
          background: linear-gradient(135deg, #00aaff, #0088ff);
          color: #000;
          border: none;
          padding: 12px 24px;
          border-radius: 4px;
          font-weight: bold;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          transition: all 0.3s ease;
          font-size: 0.9rem;
          letter-spacing: 1px;
        }

        .analytics-button:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 5px 15px rgba(0, 170, 255, 0.4);
        }

        .analytics-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .alert.error {
          padding: 12px 15px;
          border-radius: 4px;
          background: rgba(255, 0, 64, 0.1);
          border: 1px solid rgba(255, 0, 64, 0.3);
          color: #ff8888;
          display: flex;
          align-items: center;
          gap: 10px;
          font-size: 0.85rem;
        }

        .results-section {
          display: flex;
          flex-direction: column;
          gap: 15px;
        }

        .status-bar {
          display: flex;
          justify-content: space-between;
          background: rgba(0, 170, 255, 0.05);
          padding: 12px;
          border-radius: 4px;
          border: 1px solid rgba(0, 170, 255, 0.2);
        }

        .status-item {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .status-item .label {
          font-size: 0.7rem;
          color: #8a99c0;
          letter-spacing: 1px;
        }

        .status-item .value {
          font-size: 0.9rem;
          font-weight: bold;
          color: #00aaff;
        }

        .value.status-success {
          color: #00ff00;
        }

        .summary-card, .baseline-card, .anomalies-list, .recommendations {
          background: rgba(5, 8, 16, 0.8);
          border: 1px solid rgba(0, 170, 255, 0.2);
          border-radius: 6px;
          padding: 15px;
        }

        .summary-header h4, .baseline-card h5, .anomalies-list h5, .recommendations h5 {
          margin: 0 0 15px 0;
          color: #00aaff;
          font-size: 0.95rem;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .summary-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 15px;
        }

        .summary-stat {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          background: rgba(0, 170, 255, 0.05);
          border-radius: 4px;
        }

        .stat-icon {
          font-size: 2rem;
        }

        .stat-content {
          display: flex;
          flex-direction: column;
        }

        .stat-value {
          font-size: 1.5rem;
          font-weight: bold;
          color: #00aaff;
        }

        .stat-label {
          font-size: 0.7rem;
          color: #8a99c0;
          text-transform: uppercase;
        }

        .baseline-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
          gap: 12px;
        }

        .baseline-stat {
          display: flex;
          justify-content: space-between;
          padding: 8px 12px;
          background: rgba(0, 170, 255, 0.05);
          border-radius: 4px;
        }

        .baseline-stat .label {
          font-size: 0.8rem;
          color: #8a99c0;
        }

        .baseline-stat .value {
          font-size: 0.9rem;
          font-weight: 600;
          color: #00aaff;
        }

        .anomaly-card {
          background: rgba(255, 0, 64, 0.05);
          border: 1px solid rgba(255, 0, 64, 0.3);
          border-radius: 4px;
          padding: 12px;
          margin-bottom: 10px;
        }

        .anomaly-card:last-child {
          margin-bottom: 0;
        }

        .anomaly-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
          padding-bottom: 8px;
          border-bottom: 1px solid rgba(255, 0, 64, 0.2);
        }

        .anomaly-index {
          font-weight: bold;
          color: #ff0040;
          font-size: 0.9rem;
        }

        .anomaly-severity {
          font-size: 0.7rem;
          padding: 4px 10px;
          border-radius: 12px;
          font-weight: bold;
          text-transform: uppercase;
        }

        .anomaly-severity.critical {
          background: rgba(255, 0, 64, 0.2);
          color: #ff0040;
        }

        .anomaly-severity.high {
          background: rgba(255, 64, 0, 0.2);
          color: #ff4000;
        }

        .anomaly-severity.medium {
          background: rgba(255, 170, 0, 0.2);
          color: #ffaa00;
        }

        .anomaly-body {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .anomaly-info {
          display: flex;
          gap: 15px;
        }

        .info-item {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .info-item .label {
          font-size: 0.7rem;
          color: #8a99c0;
          text-transform: uppercase;
        }

        .info-item .value {
          font-size: 0.85rem;
          font-weight: 600;
          color: #d0d8f0;
        }

        .info-item .value.highlight {
          color: #ff0040;
          font-weight: bold;
        }

        .anomaly-description {
          font-size: 0.8rem;
          color: #d0d8f0;
          line-height: 1.4;
        }

        .no-anomalies {
          text-align: center;
          padding: 40px 20px;
          color: #00ff00;
        }

        .no-anomalies i {
          font-size: 3rem;
          margin-bottom: 15px;
        }

        .recommendation-item {
          background: rgba(0, 170, 255, 0.05);
          border-left: 3px solid #00aaff;
          padding: 10px 12px;
          margin-bottom: 8px;
          border-radius: 4px;
          color: #d0d8f0;
          font-size: 0.85rem;
        }

        .recommendation-item:last-child {
          margin-bottom: 0;
        }
      `}</style>
    </div>
  );
};

export default AnomalyDetectionWidget;