/**
 * PurpleHeader - Purple Team Operations Header
 * Displays metrics for both offensive and defensive operations
 * Memoized for performance optimization
 * i18n: Fully internationalized with pt-BR and en-US support
 */

import React from 'react';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import useKeyboardNavigation from '../../../../hooks/useKeyboardNavigation';
import styles from './PurpleHeader.module.css';

export const PurpleHeader = React.memo(({ onBack, activeView, onViewChange, stats }) => {
  const { t } = useTranslation();

  const views = ['split', 'timeline', 'analysis'];
  const { getItemProps } = useKeyboardNavigation({
    itemCount: views.length,
    onSelect: (index) => onViewChange(views[index]),
    orientation: 'horizontal',
    loop: true
  });

  return (
    <header className={styles.header}>
      <div className={styles.topBar}>
        <div className={styles.titleSection}>
          <button
            onClick={onBack}
            className={styles.backButton}
            aria-label={t('navigation.back_to_hub')}
          >
            ← {t('common.back').toUpperCase()}
          </button>
          <div className={styles.title}>
            <span className={styles.icon} aria-hidden="true">🟣</span>
            <div>
              <h1>{t('dashboard.purple.title')}</h1>
              <p className={styles.subtitle}>
                {t('dashboard.purple.subtitle')}
              </p>
            </div>
          </div>
        </div>

        <div className={styles.metrics}>
          <div className={`${styles.metric} ${styles.redMetric}`}>
            <span className={styles.metricLabel}>{t('dashboard.purple.metrics.activeAttacks')}</span>
            <span className={styles.metricValue}>{stats.activeAttacks || 0}</span>
          </div>
          <div className={`${styles.metric} ${styles.blueMetric}`}>
            <span className={styles.metricLabel}>{t('dashboard.purple.metrics.detections')}</span>
            <span className={styles.metricValue}>{stats.detections || 0}</span>
          </div>
          <div className={`${styles.metric} ${styles.purpleMetric}`}>
            <span className={styles.metricLabel}>{t('dashboard.purple.metrics.coverage')}</span>
            <span className={styles.metricValue}>{stats.coverage || 0}%</span>
          </div>
          <div className={`${styles.metric} ${styles.greenMetric}`}>
            <span className={styles.metricLabel}>{t('dashboard.purple.metrics.correlations')}</span>
            <span className={styles.metricValue}>{stats.correlations || 0}</span>
          </div>
        </div>
      </div>

      <nav className={styles.viewNav} role="navigation" aria-label={t('dashboard.purple.title')}>
        <button
          {...getItemProps(0, {
            onClick: () => onViewChange('split'),
            className: `${styles.viewButton} ${activeView === 'split' ? styles.active : ''}`,
            'aria-label': `${t('navigation.access_view')}: ${t('dashboard.purple.views.split')}`,
            'aria-current': activeView === 'split' ? 'page' : undefined
          })}
        >
          <span className={styles.viewIcon} aria-hidden="true">⚔️</span>
          <span>{t('dashboard.purple.views.split')}</span>
        </button>
        <button
          {...getItemProps(1, {
            onClick: () => onViewChange('timeline'),
            className: `${styles.viewButton} ${activeView === 'timeline' ? styles.active : ''}`,
            'aria-label': `${t('navigation.access_view')}: ${t('dashboard.purple.views.timeline')}`,
            'aria-current': activeView === 'timeline' ? 'page' : undefined
          })}
        >
          <span className={styles.viewIcon} aria-hidden="true">⏱️</span>
          <span>{t('dashboard.purple.views.timeline')}</span>
        </button>
        <button
          {...getItemProps(2, {
            onClick: () => onViewChange('analysis'),
            className: `${styles.viewButton} ${activeView === 'analysis' ? styles.active : ''}`,
            'aria-label': `${t('navigation.access_view')}: ${t('dashboard.purple.views.analysis')}`,
            'aria-current': activeView === 'analysis' ? 'page' : undefined
          })}
        >
          <span className={styles.viewIcon} aria-hidden="true">📊</span>
          <span>{t('dashboard.purple.views.analysis')}</span>
        </button>
      </nav>
    </header>
  );
});

PurpleHeader.displayName = 'PurpleHeader';

PurpleHeader.propTypes = {
  onBack: PropTypes.func.isRequired,
  activeView: PropTypes.string.isRequired,
  onViewChange: PropTypes.func.isRequired,
  stats: PropTypes.shape({
    activeAttacks: PropTypes.number,
    detections: PropTypes.number,
    coverage: PropTypes.number,
    correlations: PropTypes.number
  })
};
