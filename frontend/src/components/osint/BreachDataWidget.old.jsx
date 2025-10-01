/**
 * Breach Data Search Widget
 *
 * Busca em 12B+ registros de vazamentos de dados
 * Fontes: Have I Been Pwned, DeHashed, Snusbase, IntelX
 */

import React, { useState } from 'react';
import { searchBreachData, getConfidenceBadge, formatExecutionTime, getSeverityColor } from '../../api/worldClassTools';

const BreachDataWidget = () => {
  const [query, setQuery] = useState('');
  const [queryType, setQueryType] = useState('email');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const queryTypes = [
    { value: 'email', label: 'E-mail', placeholder: 'user@example.com', icon: '📧' },
    { value: 'username', label: 'Username', placeholder: 'john_doe', icon: '👤' },
    { value: 'phone', label: 'Telefone', placeholder: '+55 11 99999-9999', icon: '📱' },
    { value: 'domain', label: 'Domínio', placeholder: 'example.com', icon: '🌐' }
  ];

  const currentQueryType = queryTypes.find(qt => qt.value === queryType);

  const handleSearch = async () => {
    if (!query.trim()) {
      setError('Query é obrigatória');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await searchBreachData(query.trim(), { queryType });
      setResult(response.result);
    } catch (err) {
      setError(err.message || 'Erro ao buscar breach data');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const confidenceBadge = result ? getConfidenceBadge(result.confidence) : null;

  // Format data types
  const formatDataTypes = (types) => {
    if (!types || types.length === 0) return 'N/A';
    return types.join(', ');
  };

  return (
    <div className="breach-data-widget osint-widget">
      {/* Header */}
      <div className="widget-header">
        <div className="header-left">
          <i className="fas fa-database"></i>
          <h3>BREACH DATA SEARCH</h3>
        </div>
        <div className="header-badge">
          <span className="badge-breach">12B+ RECORDS</span>
        </div>
      </div>

      {/* Search Section */}
      <div className="widget-body">
        <div className="search-section">
          {/* Query Type Selector */}
          <div className="query-type-selector">
            {queryTypes.map(type => (
              <button
                key={type.value}
                className={`type-button ${queryType === type.value ? 'active' : ''}`}
                onClick={() => setQueryType(type.value)}
                disabled={loading}
              >
                <span className="type-icon">{type.icon}</span>
                <span className="type-label">{type.label}</span>
              </button>
            ))}
          </div>

          {/* Search Input */}
          <div className="input-group">
            <input
              type="text"
              className="breach-input"
              placeholder={currentQueryType?.placeholder}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
            />
            <button
              className="breach-button primary"
              onClick={handleSearch}
              disabled={loading || !query.trim()}
            >
              {loading ? (
                <><i className="fas fa-spinner fa-spin"></i> BUSCANDO...</>
              ) : (
                <><i className="fas fa-search"></i> BUSCAR</>
              )}
            </button>
          </div>

          <p className="input-hint">
            <i className="fas fa-shield-alt"></i>
            Busca em fontes: HIBP, DeHashed, Snusbase, IntelX
          </p>
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
                <span className="value" style={{ color: confidenceBadge.color }}>
                  {confidenceBadge.icon} {result.confidence.toFixed(1)}%
                </span>
              </div>
              <div className="status-item">
                <span className="label">TEMPO:</span>
                <span className="value">{formatExecutionTime(result.execution_time_ms)}</span>
              </div>
            </div>

            {/* Query Info */}
            <div className="query-info-card">
              <div className="info-header">
                <h4>
                  <i className={`fas ${queryType === 'email' ? 'fa-envelope' : 'fa-user'}`}></i>
                  {result.query}
                </h4>
                {result.credentials_exposed && (
                  <span className="exposed-badge critical">
                    <i className="fas fa-exclamation-circle"></i>
                    CREDENCIAIS EXPOSTAS
                  </span>
                )}
              </div>

              <div className="exposure-summary">
                <div className="summary-stat">
                  <div className="stat-icon" style={{ color: '#ff0040' }}>
                    <i className="fas fa-database"></i>
                  </div>
                  <div className="stat-content">
                    <span className="stat-value">{result.breaches_found || 0}</span>
                    <span className="stat-label">Breaches Encontrados</span>
                  </div>
                </div>

                <div className="summary-stat">
                  <div className="stat-icon" style={{ color: '#ff4000' }}>
                    <i className="fas fa-key"></i>
                  </div>
                  <div className="stat-content">
                    <span className="stat-value">{result.total_exposures || 0}</span>
                    <span className="stat-label">Exposições Totais</span>
                  </div>
                </div>

                <div className="summary-stat">
                  <div className="stat-icon" style={{ color: result.credentials_exposed ? '#ff0040' : '#00ff00' }}>
                    <i className={`fas ${result.credentials_exposed ? 'fa-unlock' : 'fa-lock'}`}></i>
                  </div>
                  <div className="stat-content">
                    <span className="stat-value" style={{ color: result.credentials_exposed ? '#ff0040' : '#00ff00' }}>
                      {result.credentials_exposed ? 'SIM' : 'NÃO'}
                    </span>
                    <span className="stat-label">Credenciais Vazadas</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Breaches List */}
            {result.breaches && result.breaches.length > 0 ? (
              <div className="breaches-list">
                <h5>
                  <i className="fas fa-exclamation-triangle"></i>
                  Vazamentos Detectados ({result.breaches.length})
                </h5>
                {result.breaches.map((breach, index) => (
                  <div key={index} className="breach-card" data-severity={breach.severity?.toLowerCase()}>
                    <div className="breach-header">
                      <div className="breach-source">
                        <i className="fas fa-database"></i>
                        <span className="source-name">{breach.source}</span>
                      </div>
                      <div className="breach-meta">
                        <span className="breach-date">
                          <i className="far fa-calendar"></i>
                          {new Date(breach.date).toLocaleDateString('pt-BR')}
                        </span>
                        <span className={`severity-badge ${breach.severity?.toLowerCase()}`}>
                          {breach.severity || 'MEDIUM'}
                        </span>
                      </div>
                    </div>

                    <div className="breach-body">
                      <div className="breach-stats">
                        <div className="stat-item">
                          <i className="fas fa-users"></i>
                          <span>{breach.records_leaked?.toLocaleString() || 'N/A'} registros</span>
                        </div>
                        <div className="stat-item">
                          <i className="fas fa-fingerprint"></i>
                          <span>{formatDataTypes(breach.data_types)}</span>
                        </div>
                      </div>

                      {/* Data Types Pills */}
                      {breach.data_types && breach.data_types.length > 0 && (
                        <div className="data-types-pills">
                          {breach.data_types.map((dataType, idx) => (
                            <span key={idx} className="data-pill">
                              {dataType}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="no-breaches">
                <i className="fas fa-shield-alt"></i>
                <p>Nenhum vazamento encontrado. Dados aparentemente seguros.</p>
              </div>
            )}

            {/* Recommendations */}
            {result.recommendations && result.recommendations.length > 0 && (
              <div className="recommendations">
                <h5>
                  <i className="fas fa-shield-alt"></i>
                  Recomendações de Segurança
                </h5>
                {result.recommendations.map((rec, index) => (
                  <div key={index} className="recommendation-item">
                    {rec}
                  </div>
                ))}
              </div>
            )}

            {/* Warnings */}
            {result.warnings && result.warnings.length > 0 && (
              <div className="warnings-section">
                {result.warnings.map((warning, index) => (
                  <div key={index} className="alert warning">
                    <i className="fas fa-exclamation-triangle"></i>
                    <span>{warning}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Styles */}
      <style jsx>{`
        .breach-data-widget {
          background: linear-gradient(135deg, rgba(10, 14, 26, 0.95), rgba(255, 0, 64, 0.05));
          border: 1px solid rgba(255, 0, 64, 0.3);
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
          border-bottom: 1px solid rgba(255, 0, 64, 0.2);
        }

        .header-left {
          display: flex;
          align-items: center;
          gap: 12px;
          color: #ff0040;
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

        .badge-breach {
          background: linear-gradient(90deg, #ff0040, #ff4000);
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

        .search-section {
          display: flex;
          flex-direction: column;
          gap: 15px;
        }

        .query-type-selector {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
          gap: 10px;
        }

        .type-button {
          background: rgba(255, 0, 64, 0.05);
          border: 1px solid rgba(255, 0, 64, 0.3);
          color: #d0d8f0;
          padding: 12px;
          border-radius: 6px;
          cursor: pointer;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 6px;
          transition: all 0.3s ease;
        }

        .type-button:hover:not(:disabled) {
          border-color: #ff0040;
          background: rgba(255, 0, 64, 0.1);
        }

        .type-button.active {
          background: rgba(255, 0, 64, 0.2);
          border-color: #ff0040;
          color: #ff0040;
          font-weight: bold;
        }

        .type-icon {
          font-size: 1.5rem;
        }

        .type-label {
          font-size: 0.8rem;
          text-transform: uppercase;
        }

        .input-group {
          display: flex;
          gap: 10px;
        }

        .breach-input {
          flex: 1;
          background: rgba(255, 0, 64, 0.05);
          border: 1px solid rgba(255, 0, 64, 0.3);
          color: #ff0040;
          padding: 10px 15px;
          border-radius: 4px;
          font-size: 0.9rem;
        }

        .breach-input:focus {
          outline: none;
          border-color: #ff0040;
          box-shadow: 0 0 10px rgba(255, 0, 64, 0.3);
        }

        .breach-button {
          background: linear-gradient(135deg, #ff0040, #ff4000);
          color: #fff;
          border: none;
          padding: 10px 20px;
          border-radius: 4px;
          font-weight: bold;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 8px;
          transition: all 0.3s ease;
          font-size: 0.85rem;
          letter-spacing: 1px;
        }

        .breach-button:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 5px 15px rgba(255, 0, 64, 0.4);
        }

        .breach-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .input-hint {
          font-size: 0.75rem;
          color: #8a99c0;
          margin: 0;
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .alert {
          padding: 12px 15px;
          border-radius: 4px;
          display: flex;
          align-items: center;
          gap: 10px;
          font-size: 0.85rem;
        }

        .alert.error {
          background: rgba(255, 0, 64, 0.1);
          border: 1px solid rgba(255, 0, 64, 0.3);
          color: #ff8888;
        }

        .alert.warning {
          background: rgba(255, 170, 0, 0.1);
          border: 1px solid rgba(255, 170, 0, 0.3);
          color: #ffaa00;
        }

        .results-section {
          display: flex;
          flex-direction: column;
          gap: 15px;
        }

        .status-bar {
          display: flex;
          justify-content: space-between;
          background: rgba(255, 0, 64, 0.05);
          padding: 12px;
          border-radius: 4px;
          border: 1px solid rgba(255, 0, 64, 0.2);
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
          color: #ff0040;
        }

        .value.status-success {
          color: #00ff00;
        }

        .query-info-card {
          background: rgba(5, 8, 16, 0.8);
          border: 1px solid rgba(255, 0, 64, 0.2);
          border-radius: 6px;
          overflow: hidden;
        }

        .info-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 15px;
          background: rgba(255, 0, 64, 0.05);
          border-bottom: 1px solid rgba(255, 0, 64, 0.2);
        }

        .info-header h4 {
          margin: 0;
          color: #ff0040;
          font-size: 1.1rem;
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .exposed-badge {
          padding: 6px 12px;
          border-radius: 4px;
          font-size: 0.75rem;
          font-weight: bold;
          letter-spacing: 1px;
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .exposed-badge.critical {
          background: rgba(255, 0, 64, 0.2);
          color: #ff0040;
          border: 1px solid #ff0040;
          animation: pulse-badge 2s infinite;
        }

        @keyframes pulse-badge {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }

        .exposure-summary {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 15px;
          padding: 20px;
        }

        .summary-stat {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          background: rgba(255, 0, 64, 0.05);
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
          color: #ff0040;
        }

        .stat-label {
          font-size: 0.7rem;
          color: #8a99c0;
          text-transform: uppercase;
        }

        .breaches-list {
          background: rgba(5, 8, 16, 0.6);
          border: 1px solid rgba(255, 0, 64, 0.2);
          border-radius: 6px;
          padding: 15px;
        }

        .breaches-list h5 {
          margin: 0 0 15px 0;
          color: #ff0040;
          font-size: 0.95rem;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .breach-card {
          background: rgba(255, 0, 64, 0.05);
          border: 1px solid rgba(255, 0, 64, 0.3);
          border-left: 4px solid #ff0040;
          border-radius: 4px;
          padding: 15px;
          margin-bottom: 12px;
        }

        .breach-card:last-child {
          margin-bottom: 0;
        }

        .breach-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
          padding-bottom: 10px;
          border-bottom: 1px solid rgba(255, 0, 64, 0.1);
        }

        .breach-source {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .source-name {
          font-weight: bold;
          color: #ff0040;
          font-size: 1rem;
        }

        .breach-meta {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .breach-date {
          font-size: 0.8rem;
          color: #8a99c0;
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .severity-badge {
          font-size: 0.7rem;
          padding: 4px 10px;
          border-radius: 12px;
          font-weight: bold;
          text-transform: uppercase;
        }

        .severity-badge.critical {
          background: rgba(255, 0, 64, 0.2);
          color: #ff0040;
        }

        .severity-badge.high {
          background: rgba(255, 64, 0, 0.2);
          color: #ff4000;
        }

        .severity-badge.medium {
          background: rgba(255, 170, 0, 0.2);
          color: #ffaa00;
        }

        .breach-body {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .breach-stats {
          display: flex;
          flex-wrap: wrap;
          gap: 15px;
        }

        .stat-item {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 0.85rem;
          color: #d0d8f0;
        }

        .stat-item i {
          color: #ff0040;
        }

        .data-types-pills {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
        }

        .data-pill {
          background: rgba(255, 0, 64, 0.1);
          border: 1px solid rgba(255, 0, 64, 0.3);
          color: #ff0040;
          padding: 4px 10px;
          border-radius: 12px;
          font-size: 0.7rem;
          font-weight: 600;
        }

        .no-breaches {
          text-align: center;
          padding: 40px 20px;
          color: #00ff00;
        }

        .no-breaches i {
          font-size: 3rem;
          margin-bottom: 15px;
        }

        .recommendations {
          background: rgba(5, 8, 16, 0.6);
          border: 1px solid rgba(255, 0, 64, 0.2);
          border-radius: 6px;
          padding: 15px;
        }

        .recommendations h5 {
          margin: 0 0 15px 0;
          color: #ff0040;
          font-size: 0.95rem;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .recommendation-item {
          background: rgba(255, 0, 64, 0.05);
          border-left: 3px solid #ff0040;
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

export default BreachDataWidget;