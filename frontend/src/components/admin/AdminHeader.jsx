/**
 * AdminHeader - Administration Dashboard Header (MODULAR)
 *
 * Three-tier design:
 * - Top Bar: Logo, Clock, Actions (Back Button)
 * - Breadcrumb: Navigation path
 * - Nav Bar: Module Navigation
 *
 * 🎯 ZERO INLINE STYLES - 100% CSS Variables
 * ✅ Tema-agnóstico (Matrix + Enterprise)
 * ✅ Responsivo nato
 * ✅ Admin theme (yellow/gold accent)
 */

import React from 'react';
import PropTypes from 'prop-types';
import { useTranslation } from 'react-i18next';
import { Breadcrumb } from '../shared/Breadcrumb';
import { CompactLanguageSelector } from '../maximus/components/CompactLanguageSelector';
import styles from './AdminHeader.module.css';

export const AdminHeader = ({
  currentTime,
  activeModule,
  modules,
  setActiveModule,
  setCurrentView,
  getItemProps
}) => {
  const { t } = useTranslation();

  // Format time
  const timeString = currentTime.toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
  const dateString = currentTime.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });

  // Find active module
  const activeModuleData = modules.find(m => m.id === activeModule);

  return (
    <header className={styles.header}>
      {/* TOP BAR - Branding & Actions */}
      <div className={styles.topBar}>
        {/* LEFT - Logo & Branding */}
        <div className={styles.branding}>
          <div className={styles.logoContainer}>
            <span className={styles.logoIcon}>A</span>
          </div>
          <div className={styles.logoText}>
            <h1 className={styles.logoTitle}>{t('dashboard.admin.title')}</h1>
            <p className={styles.logoSubtitle}>{t('dashboard.admin.subtitle')}</p>
          </div>
        </div>

        {/* RIGHT - Time & Actions */}
        <div className={styles.actions}>
          {/* Clock */}
          <div className={styles.clock}>
            <span className={styles.clockTime}>{timeString}</span>
            <span className={styles.clockDate}>{dateString}</span>
          </div>

          {/* Language Selector */}
          <CompactLanguageSelector />

          {/* Back Button */}
          <button
            onClick={() => setCurrentView('main')}
            className={styles.backButton}
            aria-label={t('navigation.back_to_hub')}
          >
            ← {t('common.back').toUpperCase()}
          </button>
        </div>
      </div>

      {/* BREADCRUMB BAR - Navigation Path */}
      <div className={styles.breadcrumbBar}>
        <Breadcrumb
          items={[
            { label: 'VÉRTICE', icon: '🏠', onClick: () => setCurrentView('main') },
            { label: 'ADMINISTRAÇÃO', icon: '⚙️' },
            {
              label: activeModuleData?.name.toUpperCase() || 'OVERVIEW',
              icon: activeModuleData?.icon
            }
          ]}
          className={styles.breadcrumb}
        />
      </div>

      {/* NAVIGATION BAR - Module Selection */}
      <div className={styles.navBar}>
        {modules.map((module, index) => {
          const isActive = activeModule === module.id;
          const itemProps = getItemProps ? getItemProps(index, {
            onClick: () => setActiveModule(module.id),
            role: 'tab',
            'aria-selected': isActive,
            'aria-controls': `panel-${module.id}`
          }) : {};

          return (
            <button
              key={module.id}
              onClick={() => setActiveModule(module.id)}
              {...itemProps}
              className={`${styles.navButton} ${isActive ? styles.active : styles.inactive}`}
              role="tab"
              aria-selected={isActive}
              aria-controls={`panel-${module.id}`}
              aria-label={`Navigate to ${module.name}`}
            >
              <span className={styles.navIcon} aria-hidden="true">{module.icon}</span>
              <span className={styles.navLabel}>{module.name}</span>
            </button>
          );
        })}
      </div>
    </header>
  );
};

AdminHeader.propTypes = {
  currentTime: PropTypes.instanceOf(Date).isRequired,
  activeModule: PropTypes.string.isRequired,
  modules: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    icon: PropTypes.string.isRequired
  })).isRequired,
  setActiveModule: PropTypes.func.isRequired,
  setCurrentView: PropTypes.func.isRequired,
  getItemProps: PropTypes.func
};

export default AdminHeader;
