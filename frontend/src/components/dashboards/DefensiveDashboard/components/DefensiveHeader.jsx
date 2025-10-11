/**
 * Defensive Dashboard Header
 * Navigation, Metrics, Module Selection
 * Memoized for performance optimization
 */

import React from 'react';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';

const DefensiveHeader = React.memo(({
  currentTime,
  setCurrentView,
  activeModule,
  setActiveModule,
  modules,
  metrics,
  metricsLoading
}) => {
  const { t } = useTranslation();
  return (
    <header className="dashboard-header">
      {/* Title & Back Button */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="header-title">
            <span className="header-title-icon">🛡️</span>
            {t('dashboard.defensive.title')}
          </h1>
          <p className="header-subtitle">
            {t('dashboard.defensive.subtitle')} | {currentTime.toLocaleTimeString()}
          </p>
        </div>

        <button
          onClick={() => setCurrentView('main')}
          className="btn btn-primary"
        >
          ← {t('navigation.back_to_hub').toUpperCase()}
        </button>
      </div>

      {/* Real-time Metrics */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-value metric-value-danger">
            {metricsLoading ? '...' : metrics.threats}
          </div>
          <div className="metric-label">{t('dashboard.defensive.metrics.threats')}</div>
        </div>

        <div className="metric-card">
          <div className="metric-value metric-value-warning">
            {metricsLoading ? '...' : metrics.suspiciousIPs}
          </div>
          <div className="metric-label">{t('dashboard.defensive.metrics.suspiciousIPs')}</div>
        </div>

        <div className="metric-card">
          <div className="metric-value metric-value-warning">
            {metricsLoading ? '...' : metrics.domains}
          </div>
          <div className="metric-label">{t('dashboard.defensive.metrics.domains')}</div>
        </div>

        <div className="metric-card">
          <div className="metric-value metric-value-info">
            {metricsLoading ? '...' : metrics.monitored}
          </div>
          <div className="metric-label">{t('dashboard.defensive.metrics.monitored')}</div>
        </div>
      </div>

      {/* Module Navigation */}
      <nav className="module-nav">
        {modules.map((module) => (
          <button
            key={module.id}
            onClick={() => setActiveModule(module.id)}
            className={`module-btn ${activeModule === module.id ? 'active' : ''}`}
          >
            <span className="module-btn-icon">{module.icon}</span>
            {module.name}
          </button>
        ))}
      </nav>
    </header>
  );
});

DefensiveHeader.displayName = 'DefensiveHeader';

DefensiveHeader.propTypes = {
  currentTime: PropTypes.instanceOf(Date).isRequired,
  setCurrentView: PropTypes.func.isRequired,
  activeModule: PropTypes.string.isRequired,
  setActiveModule: PropTypes.func.isRequired,
  modules: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
      icon: PropTypes.string.isRequired
    })
  ).isRequired,
  metrics: PropTypes.shape({
    threats: PropTypes.number,
    suspiciousIPs: PropTypes.number,
    domains: PropTypes.number,
    monitored: PropTypes.number
  }).isRequired,
  metricsLoading: PropTypes.bool.isRequired
};

export default DefensiveHeader;
