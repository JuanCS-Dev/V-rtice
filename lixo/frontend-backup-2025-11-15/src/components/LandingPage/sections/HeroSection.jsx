/**
 * ═══════════════════════════════════════════════════════════════════════════
 * HERO SECTION - TACTICAL WARFARE COMMAND CENTER
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * MISSÃO: Arsenal digital contra criminosos e terroristas cibernéticos
 * FILOSOFIA: Elegância brutal, precisão letal
 *
 * Features:
 * - Logo + Branding de combate
 * - Auth Badge integrado no comando
 * - Título TÁTICO com hierarquia militar
 * - Tags de capacidades ofensivas/defensivas
 * - Threat Globe - Mapa de alvos
 * - Tema Tactical Warfare (vermelho/preto)
 * - Responsivo mobile-first
 */

import React from 'react';
import { ThreatGlobe } from '../ThreatGlobe';
import { AuthBadge } from '../components/AuthBadge';
import { ThemeToggle } from '../components/ThemeToggle';
import styles from './HeroSection.module.css';

export const HeroSection = ({
  isAuthenticated,
  user,
  onLogin,
  onLogout,
  realThreats,
  servicesStatus,
  stats
}) => {
  return (
    <section className={styles.hero} role="banner">
      {/* Header Bar - Logo + Auth */}
      <header className={styles.headerBar}>
        {/* Logo + Branding */}
        <div className={styles.branding}>
          <div className={styles.logo}>
            <div className={styles.logoIcon}>⬡</div>
            <div className={styles.logoText}>
              <span className={styles.logoTitle}>VÉRTICE</span>
              <span className={styles.logoVersion}>v2.4.0</span>
            </div>
          </div>
        </div>

        {/* Right Side - Auth + Theme */}
        <div className={styles.headerActions}>
          <AuthBadge
            isAuthenticated={isAuthenticated}
            user={user}
            onLogin={onLogin}
            onLogout={onLogout}
          />
          <ThemeToggle />
        </div>
      </header>

      {/* Main Hero Content */}
      <div className={styles.heroContent}>
        {/* Left Column - Title & Tags */}
        <div className={styles.heroLeft}>
          {/* Status Badge */}
          <div className={styles.statusBadge}>
            <span className={styles.pulseDot}></span>
            <span>ARSENAL ARMADO</span>
          </div>

          {/* Main Title - IMPACTANTE */}
          <h1 className={styles.title}>
            <span className={styles.titleMain}>OPERAÇÃO</span>
            <span className={styles.titleHighlight}>VÉRTICE</span>
          </h1>

          {/* Subtitle */}
          <p className={styles.subtitle}>
            Guerra Total Contra Criminosos e Terroristas Digitais<br />
            Plataforma de Combate Cibernético
          </p>

          {/* Tags - Inline Flow */}
          <div className={styles.tags}>
            <span className={styles.tag}>
              <span className={styles.tagIcon}>🎯</span>
              <span>Target Lock</span>
            </span>
            <span className={styles.tag}>
              <span className={styles.tagIcon}>🔫</span>
              <span>Arsenal Ofensivo</span>
            </span>
            <span className={styles.tag}>
              <span className={styles.tagIcon}>🛡️</span>
              <span>Escudo Defensivo</span>
            </span>
            <span className={styles.tag}>
              <span className={styles.tagIcon}>⚡</span>
              <span>IA Tática</span>
            </span>
          </div>

          {/* Services Status */}
          <div className={styles.services}>
            <div className={styles.servicesHeader}>
              <span className={styles.servicesTitle}>⚡ SISTEMAS DE ARMAS</span>
              <span className={styles.servicesCount}>
                {stats.servicesOnline}/{stats.totalServices}
              </span>
            </div>
            <div className={styles.servicesGrid}>
              <ServiceIndicator
                name="IP Intel"
                online={servicesStatus.ipIntelligence}
              />
              <ServiceIndicator
                name="Threat Intel"
                online={servicesStatus.threatIntel}
              />
              <ServiceIndicator
                name="Malware"
                online={servicesStatus.malwareAnalysis}
              />
              <ServiceIndicator
                name="SSL"
                online={servicesStatus.sslMonitor}
              />
            </div>
          </div>
        </div>

        {/* Right Column - Threat Globe */}
        <div className={styles.heroRight}>
          <div className={styles.globeContainer}>
            <ThreatGlobe realThreats={realThreats} />
          </div>
        </div>
      </div>
    </section>
  );
};

// Sub-component: Service Indicator
const ServiceIndicator = ({ name, online }) => (
  <div className={`${styles.serviceItem} ${online ? styles.online : styles.offline}`}>
    <span className={styles.serviceDot}></span>
    <span className={styles.serviceName}>{name}</span>
  </div>
);

export default HeroSection;
