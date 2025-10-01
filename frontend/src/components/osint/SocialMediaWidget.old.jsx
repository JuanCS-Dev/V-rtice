/**
 * Social Media Investigation Widget
 *
 * OSINT em 20+ plataformas sociais
 * Twitter/X, LinkedIn, GitHub, Instagram, Reddit, etc.
 */

import React, { useState } from 'react';
import { socialMediaInvestigation, getConfidenceBadge, formatExecutionTime } from '../../api/worldClassTools';

const PLATFORM_ICONS = {
  twitter: 'fab fa-twitter',
  linkedin: 'fab fa-linkedin',
  github: 'fab fa-github',
  instagram: 'fab fa-instagram',
  reddit: 'fab fa-reddit',
  facebook: 'fab fa-facebook',
  youtube: 'fab fa-youtube',
  tiktok: 'fab fa-tiktok'
};

const SocialMediaWidget = () => {
  const [target, setTarget] = useState('');
  const [platforms, setPlatforms] = useState(['twitter', 'linkedin', 'github']);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const availablePlatforms = ['twitter', 'linkedin', 'github', 'instagram', 'reddit', 'facebook'];

  const togglePlatform = (platform) => {
    setPlatforms(prev =>
      prev.includes(platform)
        ? prev.filter(p => p !== platform)
        : [...prev, platform]
    );
  };

  const handleInvestigate = async () => {
    if (!target.trim()) {
      setError('Username/Target é obrigatório');
      return;
    }

    if (platforms.length === 0) {
      setError('Selecione pelo menos uma plataforma');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await socialMediaInvestigation(target.trim(), {
        platforms,
        deepAnalysis: true
      });

      setResult(response.result);
    } catch (err) {
      setError(err.message || 'Erro ao investigar target');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleInvestigate();
    }
  };

  const confidenceBadge = result ? getConfidenceBadge(result.confidence) : null;

  return (
    <div className="social-media-widget osint-widget">
      {/* Header */}
      <div className="widget-header">
        <div className="header-left">
          <i className="fas fa-user-secret"></i>
          <h3>SOCIAL MEDIA DEEP DIVE</h3>
        </div>
        <div className="header-badge">
          <span className="badge-osint">OSINT</span>
        </div>
      </div>

      {/* Search Input */}
      <div className="widget-body">
        <div className="search-section">
          <div className="input-group">
            <input
              type="text"
              className="osint-input"
              placeholder="username ou target"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
            />
            <button
              className="osint-button primary"
              onClick={handleInvestigate}
              disabled={loading || !target.trim() || platforms.length === 0}
            >
              {loading ? (
                <><i className="fas fa-spinner fa-spin"></i> INVESTIGANDO...</>
              ) : (
                <><i className="fas fa-search"></i> INVESTIGAR</>
              )}
            </button>
          </div>

          {/* Platform Selection */}
          <div className="platform-selector">
            <span className="selector-label">Plataformas:</span>
            <div className="platform-chips">
              {availablePlatforms.map(platform => (
                <button
                  key={platform}
                  className={`platform-chip ${platforms.includes(platform) ? 'active' : ''}`}
                  onClick={() => togglePlatform(platform)}
                  disabled={loading}
                >
                  <i className={PLATFORM_ICONS[platform] || 'fas fa-globe'}></i>
                  {platform}
                </button>
              ))}
            </div>
          </div>

          <p className="input-hint">
            <i className="fas fa-info-circle"></i>
            Busca em 20+ redes sociais e plataformas públicas
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

            {/* Target Overview */}
            <div className="target-overview">
              <div className="overview-header">
                <h4>
                  <i className="fas fa-crosshairs"></i>
                  Target: {result.target}
                </h4>
                <div className="footprint-score">
                  <span>Digital Footprint</span>
                  <div className="score-circle" style={{ '--score': result.digital_footprint_score || 50 }}>
                    {result.digital_footprint_score || 0}
                  </div>
                </div>
              </div>

              <div className="overview-stats">
                <div className="stat-box">
                  <i className="fas fa-check-circle"></i>
                  <span className="stat-value">{result.profiles_found || 0}</span>
                  <span className="stat-label">Perfis Encontrados</span>
                </div>
                <div className="stat-box">
                  <i className="fas fa-calendar-alt"></i>
                  <span className="stat-value">
                    {result.profiles && result.profiles.length > 0
                      ? result.profiles[0].last_activity || 'N/A'
                      : 'N/A'}
                  </span>
                  <span className="stat-label">Última Atividade</span>
                </div>
              </div>
            </div>

            {/* Profiles Found */}
            {result.profiles && result.profiles.length > 0 ? (
              <div className="profiles-section">
                <h5>
                  <i className="fas fa-id-card"></i>
                  Perfis Encontrados ({result.profiles.length})
                </h5>
                {result.profiles.map((profile, index) => (
                  <div key={index} className="profile-card">
                    <div className="profile-header">
                      <div className="profile-platform">
                        <i className={PLATFORM_ICONS[profile.platform] || 'fas fa-globe'}></i>
                        <span>{profile.platform}</span>
                        {profile.verified && (
                          <i className="fas fa-check-circle verified-badge" title="Verificado"></i>
                        )}
                      </div>
                      <span className="profile-sentiment" data-sentiment={profile.sentiment || 'neutral'}>
                        {profile.sentiment || 'neutral'}
                      </span>
                    </div>

                    <div className="profile-body">
                      <div className="profile-info">
                        <div className="info-row">
                          <span className="label">Username:</span>
                          <span className="value">{profile.username}</span>
                        </div>
                        {profile.followers !== undefined && (
                          <div className="info-row">
                            <span className="label">Seguidores:</span>
                            <span className="value">{profile.followers.toLocaleString()}</span>
                          </div>
                        )}
                        {profile.last_activity && (
                          <div className="info-row">
                            <span className="label">Última Atividade:</span>
                            <span className="value">{profile.last_activity}</span>
                          </div>
                        )}
                      </div>

                      {profile.url && (
                        <a
                          href={profile.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="profile-link"
                        >
                          <i className="fas fa-external-link-alt"></i>
                          Visitar Perfil
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="no-results">
                <i className="fas fa-search-minus"></i>
                <p>Nenhum perfil encontrado nas plataformas selecionadas</p>
              </div>
            )}

            {/* Recommendations */}
            {result.recommendations && result.recommendations.length > 0 && (
              <div className="recommendations">
                <h5>
                  <i className="fas fa-lightbulb"></i>
                  Próximos Passos
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
        .social-media-widget {
          background: linear-gradient(135deg, rgba(10, 14, 26, 0.95), rgba(255, 0, 255, 0.05));
          border: 1px solid rgba(255, 0, 255, 0.3);
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
          border-bottom: 1px solid rgba(255, 0, 255, 0.2);
        }

        .header-left {
          display: flex;
          align-items: center;
          gap: 12px;
          color: #ff00ff;
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

        .badge-osint {
          background: linear-gradient(90deg, #ff00ff, #ff0080);
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
          gap: 12px;
        }

        .input-group {
          display: flex;
          gap: 10px;
        }

        .osint-input {
          flex: 1;
          background: rgba(255, 0, 255, 0.05);
          border: 1px solid rgba(255, 0, 255, 0.3);
          color: #ff00ff;
          padding: 10px 15px;
          border-radius: 4px;
          font-size: 0.9rem;
        }

        .osint-input:focus {
          outline: none;
          border-color: #ff00ff;
          box-shadow: 0 0 10px rgba(255, 0, 255, 0.3);
        }

        .osint-button {
          background: linear-gradient(135deg, #ff00ff, #ff0080);
          color: #000;
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

        .osint-button:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 5px 15px rgba(255, 0, 255, 0.4);
        }

        .osint-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .platform-selector {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .selector-label {
          font-size: 0.8rem;
          color: #8a99c0;
          font-weight: 600;
        }

        .platform-chips {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }

        .platform-chip {
          background: rgba(255, 0, 255, 0.05);
          border: 1px solid rgba(255, 0, 255, 0.3);
          color: #d0d8f0;
          padding: 6px 12px;
          border-radius: 20px;
          font-size: 0.75rem;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 6px;
          transition: all 0.3s ease;
          text-transform: capitalize;
        }

        .platform-chip:hover:not(:disabled) {
          border-color: #ff00ff;
          background: rgba(255, 0, 255, 0.1);
        }

        .platform-chip.active {
          background: rgba(255, 0, 255, 0.2);
          border-color: #ff00ff;
          color: #ff00ff;
          font-weight: bold;
        }

        .input-hint {
          font-size: 0.75rem;
          color: #8a99c0;
          margin: 0;
          display: flex;
          align-items: center;
          gap: 6px;
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
          background: rgba(255, 0, 255, 0.05);
          padding: 12px;
          border-radius: 4px;
          border: 1px solid rgba(255, 0, 255, 0.2);
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
          color: #ff00ff;
        }

        .value.status-success {
          color: #00ff00;
        }

        .target-overview {
          background: rgba(5, 8, 16, 0.8);
          border: 1px solid rgba(255, 0, 255, 0.2);
          border-radius: 6px;
          padding: 20px;
        }

        .overview-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .overview-header h4 {
          margin: 0;
          color: #ff00ff;
          font-size: 1.1rem;
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .footprint-score {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
        }

        .footprint-score span {
          font-size: 0.7rem;
          color: #8a99c0;
        }

        .score-circle {
          width: 60px;
          height: 60px;
          border-radius: 50%;
          background: conic-gradient(
            #ff00ff 0deg,
            #ff00ff calc(var(--score) * 3.6deg),
            rgba(255, 0, 255, 0.1) calc(var(--score) * 3.6deg)
          );
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.2rem;
          font-weight: bold;
          color: #ff00ff;
          position: relative;
        }

        .score-circle::before {
          content: '';
          position: absolute;
          width: 46px;
          height: 46px;
          border-radius: 50%;
          background: rgba(5, 8, 16, 1);
        }

        .score-circle::after {
          content: attr(style);
          position: relative;
          z-index: 1;
        }

        .overview-stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 15px;
        }

        .stat-box {
          background: rgba(255, 0, 255, 0.05);
          border: 1px solid rgba(255, 0, 255, 0.2);
          border-radius: 4px;
          padding: 15px;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          text-align: center;
        }

        .stat-box i {
          font-size: 1.5rem;
          color: #ff00ff;
        }

        .stat-value {
          font-size: 1.2rem;
          font-weight: bold;
          color: #ff00ff;
        }

        .stat-label {
          font-size: 0.75rem;
          color: #8a99c0;
          text-transform: uppercase;
        }

        .profiles-section {
          background: rgba(5, 8, 16, 0.6);
          border: 1px solid rgba(255, 0, 255, 0.2);
          border-radius: 6px;
          padding: 15px;
        }

        .profiles-section h5 {
          margin: 0 0 15px 0;
          color: #ff00ff;
          font-size: 0.95rem;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .profile-card {
          background: rgba(255, 0, 255, 0.05);
          border: 1px solid rgba(255, 0, 255, 0.2);
          border-radius: 4px;
          padding: 15px;
          margin-bottom: 12px;
        }

        .profile-card:last-child {
          margin-bottom: 0;
        }

        .profile-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
          padding-bottom: 10px;
          border-bottom: 1px solid rgba(255, 0, 255, 0.1);
        }

        .profile-platform {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #ff00ff;
          font-weight: bold;
          text-transform: capitalize;
        }

        .verified-badge {
          color: #00ff00;
          font-size: 0.9rem;
        }

        .profile-sentiment {
          font-size: 0.75rem;
          padding: 4px 10px;
          border-radius: 12px;
          font-weight: 600;
          text-transform: uppercase;
        }

        .profile-sentiment[data-sentiment="positive"] {
          background: rgba(0, 255, 0, 0.2);
          color: #00ff00;
        }

        .profile-sentiment[data-sentiment="neutral"] {
          background: rgba(0, 170, 255, 0.2);
          color: #00aaff;
        }

        .profile-sentiment[data-sentiment="negative"] {
          background: rgba(255, 0, 64, 0.2);
          color: #ff0040;
        }

        .profile-body {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .profile-info {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .info-row {
          display: flex;
          justify-content: space-between;
        }

        .info-row .label {
          font-size: 0.8rem;
          color: #8a99c0;
        }

        .info-row .value {
          font-size: 0.85rem;
          color: #d0d8f0;
          font-weight: 600;
        }

        .profile-link {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          color: #ff00ff;
          text-decoration: none;
          font-size: 0.8rem;
          transition: color 0.3s ease;
          align-self: flex-start;
        }

        .profile-link:hover {
          color: #ff0080;
        }

        .no-results {
          text-align: center;
          padding: 40px 20px;
          color: #8a99c0;
        }

        .no-results i {
          font-size: 3rem;
          margin-bottom: 15px;
          opacity: 0.5;
        }

        .recommendations {
          background: rgba(5, 8, 16, 0.6);
          border: 1px solid rgba(255, 0, 255, 0.2);
          border-radius: 6px;
          padding: 15px;
        }

        .recommendations h5 {
          margin: 0 0 15px 0;
          color: #ff00ff;
          font-size: 0.95rem;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .recommendation-item {
          background: rgba(255, 0, 255, 0.05);
          border-left: 3px solid #ff00ff;
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

export default SocialMediaWidget;