/**
 * ═══════════════════════════════════════════════════════════════════════════
 * MODULES SECTION - Premium Module Cards
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Design Philosophy:
 * - 3 colunas em desktop, 1 em mobile
 * - Hover com scale + glow effect
 * - Gradient backgrounds sutis
 * - Features como pills, não lista
 * - CTA button destacado
 * - Tema-agnóstico
 * - Micro-interactions
 */

import React from 'react';
import { useTranslation } from 'react-i18next';
import { handleKeyboardClick } from '../../../utils/accessibility';
import styles from './ModulesSection.module.css';

export const ModulesSection = ({ setCurrentView }) => {
  const { t } = useTranslation();

  const modules = [
    {
      id: 'maximus',
      name: t('modules.maximus.name'),
      description: t('modules.maximus.description'),
      icon: '🧠',
      color: 'ai',
      features: t('modules.maximus.features', { returnObjects: true })
    },
    {
      id: 'reactive-fabric',
      name: t('modules.reactive_fabric.name', 'Reactive Fabric'),
      description: t('modules.reactive_fabric.description', 'Sistema de Deception e Honeypots com Inteligência em Tempo Real'),
      icon: '🕸️',
      color: 'red',
      features: t('modules.reactive_fabric.features', {
        returnObjects: true,
        defaultValue: ['Honeypot Monitoring', 'Threat Intelligence', 'Decoy Bayou Map', 'Real-time Alerts']
      })
    },
    {
      id: 'hitl-console',
      name: t('modules.hitl_console.name', 'HITL Console'),
      description: t('modules.hitl_console.description', 'Human-in-the-Loop Authorization para Respostas de Ameaças'),
      icon: '🎯',
      color: 'purple',
      features: t('modules.hitl_console.features', {
        returnObjects: true,
        defaultValue: ['Threat Review', 'Decision Authorization', 'Real-time Alerts', 'Forensic Analysis']
      })
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

  const handleModuleClick = (moduleId) => () => {
    setCurrentView(moduleId);
  };

  return (
    <section className={styles.modules} aria-labelledby="modules-title">
      {/* Section Header */}
      <header className={styles.header}>
        <h2 id="modules-title" className={styles.title}>
          <span className={styles.titleIcon}>⚡</span>
          <span>{t('navigation.available_modules')}</span>
        </h2>
        <p className={styles.subtitle}>
          Escolha um módulo para acessar funcionalidades especializadas
        </p>
      </header>

      {/* Modules Grid */}
      <div className={styles.grid}>
        {modules.map((module, index) => (
          <ModuleCard
            key={module.id}
            module={module}
            index={index}
            onClick={handleModuleClick(module.id)}
            t={t}
          />
        ))}
      </div>
    </section>
  );
};

// Sub-component: Module Card
const ModuleCard = ({ module, index, onClick, t }) => {
  return (
    <article
      className={`${styles.card} ${styles[module.color]}`}
      onClick={onClick}
      onKeyDown={handleKeyboardClick(onClick)}
      role="button"
      tabIndex={0}
      aria-label={`${t('navigation.access_module')} ${module.name}`}
      style={{ animationDelay: `${index * 0.05}s` }}
    >
      {/* Gradient Background */}
      <div className={styles.cardBg}></div>

      {/* Header */}
      <header className={styles.cardHeader}>
        <div className={styles.icon}>{module.icon}</div>
        <h3 className={styles.name}>{module.name}</h3>
      </header>

      {/* Description */}
      <p className={styles.description}>{module.description}</p>

      {/* Features - Pills */}
      <div className={styles.features}>
        {module.features.slice(0, 4).map((feature, i) => (
          <span key={i} className={styles.featurePill}>
            {feature}
          </span>
        ))}
        {module.features.length > 4 && (
          <span className={`${styles.featurePill} ${styles.more}`}>
            +{module.features.length - 4}
          </span>
        )}
      </div>

      {/* CTA Button */}
      <div className={styles.cta}>
        <span className={styles.ctaText}>
          {t('navigation.access_module').toUpperCase()}
        </span>
        <span className={styles.ctaIcon}>→</span>
      </div>

      {/* Hover Effect */}
      <div className={styles.hoverGlow}></div>
    </article>
  );
};

export default ModulesSection;
