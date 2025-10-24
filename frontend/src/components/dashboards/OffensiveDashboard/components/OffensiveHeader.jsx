/**
 * OffensiveHeader - Red Team Ops Header
 * Displays offensive metrics, module navigation, and control buttons
 * Memoized for performance optimization with MemoizedMetricCard
 * i18n: Fully internationalized with pt-BR and en-US support
 */

import React from 'react';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import useKeyboardNavigation from '../../../../hooks/useKeyboardNavigation';
import { MemoizedMetricCard } from '../../../optimized/MemoizedMetricCard';
import styles from './OffensiveHeader.module.css';

export const OffensiveHeader = React.memo(({
  metrics,
  loading,
  onBack,
  activeModule,
  modules,
  onModuleChange
}) => {
  const { t } = useTranslation();

  const { getItemProps } = useKeyboardNavigation({
    itemCount: modules.length,
    onSelect: (index) => onModuleChange(modules[index].id),
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
            <span className={styles.icon} aria-hidden="true">⚔️</span>
            <div>
              <h1>{t('dashboard.offensive.title')}</h1>
              <p className={styles.subtitle}>{t('dashboard.offensive.subtitle')}</p>
            </div>
          </div>
        </div>

        <div className={styles.metrics}>
          <MemoizedMetricCard
            label={t('dashboard.offensive.metrics.activeScans')}
            value={metrics.activeScans || 0}
            icon="📡"
            loading={loading}
          />
          <MemoizedMetricCard
            label={t('dashboard.offensive.metrics.exploitsFound')}
            value={metrics.exploitsFound || 0}
            icon="🎯"
            loading={loading}
          />
          <MemoizedMetricCard
            label={t('dashboard.offensive.metrics.targets')}
            value={metrics.targets || 0}
            icon="🔍"
            loading={loading}
          />
          <MemoizedMetricCard
            label={t('dashboard.offensive.metrics.sessions')}
            value={metrics.c2Sessions || 0}
            icon="⚡"
            loading={loading}
          />
        </div>
      </div>

      <nav className={styles.moduleNav} role="navigation" aria-label={t('dashboard.offensive.title')}>
        {modules.map((module, index) => (
          <button
            key={module.id}
            {...getItemProps(index, {
              onClick: () => onModuleChange(module.id),
              className: `${styles.moduleButton} ${activeModule === module.id ? styles.active : ''}`,
              'aria-label': `${t('navigation.access_module')}: ${module.name}`,
              'aria-current': activeModule === module.id ? 'page' : undefined
            })}
          >
            <span className={styles.moduleIcon} aria-hidden="true">{module.icon}</span>
            <span>{module.name}</span>
          </button>
        ))}
      </nav>
    </header>
  );
});

OffensiveHeader.displayName = 'OffensiveHeader';

OffensiveHeader.propTypes = {
  metrics: PropTypes.shape({
    activeScans: PropTypes.number,
    exploitsFound: PropTypes.number,
    targets: PropTypes.number,
    c2Sessions: PropTypes.number
  }),
  loading: PropTypes.bool,
  onBack: PropTypes.func.isRequired,
  activeModule: PropTypes.string.isRequired,
  modules: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
      icon: PropTypes.string.isRequired
    })
  ).isRequired,
  onModuleChange: PropTypes.func.isRequired
};
