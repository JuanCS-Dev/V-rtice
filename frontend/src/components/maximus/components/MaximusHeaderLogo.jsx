/**
 * MaximusHeaderLogo - MAXIMUS AI Logo & Title Section
 *
 * Displays animated brain logo with pulsing effect and title.
 */

import React from 'react';
import { useTranslation } from 'react-i18next';

export const MaximusHeaderLogo = () => {
  const { t } = useTranslation();

  return (
    <div className="header-left">
      <div className="maximus-logo">
        <div className="logo-icon">
          <span className="logo-brain">🧠</span>
          <div className="logo-pulse"></div>
        </div>
      </div>
      <div className="header-title-section">
        <h1 className="maximus-title">
          {t('dashboard.maximus.title')}
          <span className="title-version">v1.0.0</span>
        </h1>
        <p className="maximus-subtitle">{t('dashboard.maximus.subtitle')}</p>
      </div>
    </div>
  );
};

export default MaximusHeaderLogo;
