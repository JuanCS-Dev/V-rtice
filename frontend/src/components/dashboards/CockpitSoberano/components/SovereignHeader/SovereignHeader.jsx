/**
 * SovereignHeader - Cockpit Command Bridge Header
 * 
 * Real-time status indicators, metrics overview, and system health
 * Follows Vértice Design System v2.0
 * 
 * @version 1.0.0
 */

import React from 'react';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import styles from './SovereignHeader.module.css';

export const SovereignHeader = ({ 
  metrics, 
  loading, 
  onBack, 
  systemHealth
}) => {
  const { t } = useTranslation();

  const getHealthColor = (health) => {
    switch (health) {
      case 'OPERATIONAL': return 'var(--color-success)';
      case 'DEGRADED': return 'var(--color-warning)';
      case 'CRITICAL': return 'var(--color-danger)';
      default: return 'var(--color-text-secondary)';
    }
  };

  const formatLatency = (ms) => {
    if (ms < 100) return `${ms.toFixed(0)}ms`;
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  return (
    <header className={styles.sovereignHeader}>
      <div className={styles.topBar}>
        <div className={styles.titleSection}>
          {onBack && (
            <button 
              className={styles.backButton}
              onClick={onBack}
              aria-label={t('common.back', 'Back')}
            >
              ←
            </button>
          )}
          <div className={styles.titleContainer}>
            <h1 className={styles.title}>
              <span className={styles.titleIcon}>⚔️</span>
              {t('cockpit.title', 'COCKPIT SOBERANO')}
            </h1>
            <p className={styles.subtitle}>
              {t('cockpit.subtitle', 'Centro de Comando & Inteligência da Célula Híbrida')}
            </p>
          </div>
        </div>

        <div className={styles.systemStatus}>
          <div 
            className={styles.statusIndicator}
            style={{ '--status-color': getHealthColor(systemHealth) }}
          >
            <span className={styles.statusPulse}></span>
            <span className={styles.statusLabel}>
              {systemHealth || 'UNKNOWN'}
            </span>
          </div>
        </div>
      </div>

      <div className={styles.metricsBar}>
        {loading ? (
          <div className={styles.metricsLoading}>
            <div className={styles.spinner}></div>
            <span>{t('common.loading', 'Loading')}...</span>
          </div>
        ) : (
          <>
            <MetricCard
              icon="🤖"
              label={t('cockpit.metrics.agents', 'Agentes Ativos')}
              value={`${metrics.activeAgents}/${metrics.totalAgents}`}
              trend={metrics.activeAgents > 0 ? 'up' : 'neutral'}
            />
            <MetricCard
              icon="⚖️"
              label={t('cockpit.metrics.verdicts', 'Veredictos')}
              value={metrics.totalVerdicts}
              highlight={metrics.criticalVerdicts > 0}
              subtext={metrics.criticalVerdicts > 0 ? `${metrics.criticalVerdicts} críticos` : null}
            />
            <MetricCard
              icon="🤝"
              label={t('cockpit.metrics.alliances', 'Alianças')}
              value={metrics.alliancesDetected}
              trend={metrics.alliancesDetected > 5 ? 'up' : 'neutral'}
            />
            <MetricCard
              icon="🎭"
              label={t('cockpit.metrics.deception', 'Engano')}
              value={metrics.deceptionMarkers}
              highlight={metrics.deceptionMarkers > 0}
            />
            <MetricCard
              icon="⚡"
              label={t('cockpit.metrics.latency', 'Latência')}
              value={formatLatency(metrics.avgProcessingLatency)}
              trend={metrics.avgProcessingLatency < 500 ? 'down' : 'up'}
            />
          </>
        )}
      </div>
    </header>
  );
};

const MetricCard = ({ icon, label, value, trend, highlight, subtext }) => (
  <div className={`${styles.metricCard} ${highlight ? styles.metricHighlight : ''}`}>
    <div className={styles.metricIcon}>{icon}</div>
    <div className={styles.metricContent}>
      <div className={styles.metricLabel}>{label}</div>
      <div className={styles.metricValue}>
        {value}
        {trend && (
          <span className={`${styles.metricTrend} ${styles[`trend-${trend}`]}`}>
            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'}
          </span>
        )}
      </div>
      {subtext && <div className={styles.metricSubtext}>{subtext}</div>}
    </div>
  </div>
);

MetricCard.propTypes = {
  icon: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  trend: PropTypes.oneOf(['up', 'down', 'neutral']),
  highlight: PropTypes.bool,
  subtext: PropTypes.string
};

SovereignHeader.propTypes = {
  metrics: PropTypes.shape({
    totalAgents: PropTypes.number,
    activeAgents: PropTypes.number,
    totalVerdicts: PropTypes.number,
    criticalVerdicts: PropTypes.number,
    alliancesDetected: PropTypes.number,
    deceptionMarkers: PropTypes.number,
    avgProcessingLatency: PropTypes.number
  }),
  loading: PropTypes.bool,
  onBack: PropTypes.func,
  systemHealth: PropTypes.string
};

SovereignHeader.defaultProps = {
  metrics: {
    totalAgents: 0,
    activeAgents: 0,
    totalVerdicts: 0,
    criticalVerdicts: 0,
    alliancesDetected: 0,
    deceptionMarkers: 0,
    avgProcessingLatency: 0
  },
  loading: false,
  systemHealth: 'UNKNOWN'
};
