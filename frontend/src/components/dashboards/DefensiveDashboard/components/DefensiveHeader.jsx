/**
 * DefensiveHeader - Blue Team Ops Header
 * Displays defensive metrics, module navigation, and control buttons
 * Memoized for performance optimization
 * SOURCE OF TRUTH: Landing Page Pattern (Purple + Cyan)
 */

import React from 'react';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import styles from './DefensiveHeader.module.css';

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
    <header className={styles.header}>
      <div className={styles.topBar}>
        <div className={styles.titleSection}>
          <button
            onClick={() => setCurrentView('main')}
            className={styles.backButton}
            aria-label={t('navigation.back_to_hub')}
          >
            ← {t('common.back', 'BACK').toUpperCase()}
          </button>
          <div className={styles.title}>
            <span className={styles.icon} aria-hidden="true">🛡️</span>
            <div>
              <h1>{t('dashboard.defensive.title', 'DEFENSIVE OPERATIONS')}</h1>
              <p className={styles.subtitle}>
                {t('dashboard.defensive.subtitle', 'Blue Team - Threat Detection & Monitoring')} | {currentTime.toLocaleTimeString()}
              </p>
            </div>
          </div>
        </div>

        <div className={styles.metrics}>
          <div className={styles.metric}>
            <span className={styles.metricLabel}>{t('dashboard.defensive.metrics.threats', 'THREATS')}</span>
            <span className={styles.metricValue}>
              {metricsLoading ? '...' : metrics.threats || 0}
            </span>
          </div>
          <div className={styles.metric}>
            <span className={styles.metricLabel}>{t('dashboard.defensive.metrics.suspiciousIPs', 'SUSPICIOUS IPs')}</span>
            <span className={styles.metricValue}>
              {metricsLoading ? '...' : metrics.suspiciousIPs || 0}
            </span>
          </div>
          <div className={styles.metric}>
            <span className={styles.metricLabel}>{t('dashboard.defensive.metrics.domains', 'DOMAINS')}</span>
            <span className={styles.metricValue}>
              {metricsLoading ? '...' : metrics.domains || 0}
            </span>
          </div>
          <div className={styles.metric}>
            <span className={styles.metricLabel}>{t('dashboard.defensive.metrics.monitored', 'MONITORED')}</span>
            <span className={styles.metricValue}>
              {metricsLoading ? '...' : metrics.monitored || 0}
            </span>
          </div>
        </div>
      </div>

      <nav className={styles.moduleNav} role="navigation" aria-label={t('dashboard.defensive.title', 'DEFENSIVE OPERATIONS')}>
        {modules.map((module) => (
          <button
            key={module.id}
            onClick={() => setActiveModule(module.id)}
            className={`${styles.moduleButton} ${activeModule === module.id ? styles.active : ''}`}
            aria-label={`${t('navigation.access_module', 'Access module')}: ${module.name}`}
            aria-current={activeModule === module.id ? 'page' : undefined}
          >
            <span className={styles.moduleIcon} aria-hidden="true">{module.icon}</span>
            <span>{module.name}</span>
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
