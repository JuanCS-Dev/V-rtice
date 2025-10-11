/**
 * ModuleGrid - Grid de Módulos Disponíveis
 */

import React from 'react';
import { useTranslation } from 'react-i18next';

export const ModuleGrid = ({ setCurrentView }) => {
  const { t } = useTranslation();

  const modules = [
    {
      id: 'maximus',
      name: t('modules.maximus.name'),
      description: t('modules.maximus.description'),
      icon: '🧠',
      color: 'gradient-ai',
      features: t('modules.maximus.features', { returnObjects: true })
    },
    {
      id: 'defensive',
      name: t('modules.defensive.name'),
      description: t('modules.defensive.description'),
      icon: '🛡️',
      color: 'cyan',
      features: t('modules.defensive.features', { returnObjects: true })
    },
    {
      id: 'offensive',
      name: t('modules.offensive.name'),
      description: t('modules.offensive.description'),
      icon: '⚔️',
      color: 'red',
      features: t('modules.offensive.features', { returnObjects: true })
    },
    {
      id: 'purple',
      name: t('modules.purple.name'),
      description: t('modules.purple.description'),
      icon: '🟣',
      color: 'purple',
      features: t('modules.purple.features', { returnObjects: true })
    },
    {
      id: 'osint',
      name: t('modules.osint.name'),
      description: t('modules.osint.description'),
      icon: '🕵️',
      color: 'blue',
      features: t('modules.osint.features', { returnObjects: true })
    },
    {
      id: 'admin',
      name: t('modules.admin.name'),
      description: t('modules.admin.description'),
      icon: '⚙️',
      color: 'yellow',
      features: t('modules.admin.features', { returnObjects: true })
    }
  ];

  return (
    <div className="module-section">
      <h2 className="section-title">
        <span className="title-icon">⚡</span>
        {t('navigation.available_modules')}
      </h2>

      <div className="module-grid">
        {modules.map((module) => (
          <div
            key={module.id}
            className={`module-card module-${module.color}`}
            onClick={() => setCurrentView(module.id)}
          >
            <div className="module-header">
              <span className="module-icon">{module.icon}</span>
              <h3 className="module-name">{module.name}</h3>
            </div>

            <p className="module-description">{module.description}</p>

            <div className="module-features">
              {module.features.map((feature, i) => (
                <span key={i} className="feature-tag">
                  {feature}
                </span>
              ))}
            </div>

            <div className="module-action">
              <span>{t('navigation.access_module').toUpperCase()}</span>
              <i className="fas fa-arrow-right"></i>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
