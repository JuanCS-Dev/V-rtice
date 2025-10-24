/**
 * DefensiveHeader - Blue Team Ops Header
 * Displays defensive metrics, module navigation, and control buttons
 * Memoized for performance optimization with MemoizedMetricCard
 * SOURCE OF TRUTH: Landing Page Pattern (Purple + Cyan)
 */

import React from 'react';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import { MemoizedMetricCard } from '../../../optimized/MemoizedMetricCard';
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
          <MemoizedMetricCard
            label={t('dashboard.defensive.metrics.threats', 'THREATS')}
            value={metrics.threats || 0}
            icon="🚨"
            loading={metricsLoading}
          />
          <MemoizedMetricCard
            label={t('dashboard.defensive.metrics.suspiciousIPs', 'SUSPICIOUS IPs')}
            value={metrics.suspiciousIPs || 0}
            icon="🎯"
            loading={metricsLoading}
          />
          <MemoizedMetricCard
            label={t('dashboard.defensive.metrics.domains', 'DOMAINS')}
            value={metrics.domains || 0}
            icon="🌐"
            loading={metricsLoading}
          />
          <MemoizedMetricCard
            label={t('dashboard.defensive.metrics.monitored', 'MONITORED')}
            value={metrics.monitored || 0}
            icon="🛡️"
            loading={metricsLoading}
          />
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
