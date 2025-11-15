/**
 * CYBER ALERTS - Real-time Security Alerts & System Status Dashboard
 *
 * Painel de alertas e status do sistema Cyber
 * Exibe status, métricas em tempo real, stream de alertas e ações rápidas
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <article> with data-maximus-tool="cyber-alerts"
 * - <section> for status panel
 * - <section> for metrics grid
 * - <section> for alerts stream
 * - <section> for quick actions
 *
 * Maximus can:
 * - Identify tool via data-maximus-tool="cyber-alerts"
 * - Monitor system status via data-maximus-status
 * - Access metrics via data-maximus-section="metrics"
 * - Interpret alert stream via semantic structure
 *
 * i18n: Ready for internationalization
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 * @version 2.0.0 (Maximus Vision)
 */

import React from 'react';
import { StatusPanel } from './components/StatusPanel';
import { MetricsGrid } from './components/MetricsGrid';
import { AlertsList } from './components/AlertsList';
import { QuickActions } from './components/QuickActions';
import styles from './CyberAlerts.module.css';

export const CyberAlerts = ({ alerts = [], threatData = {} }) => {
  return (
    <article
      className={styles.container}
      role="article"
      aria-labelledby="cyber-alerts-title"
      data-maximus-tool="cyber-alerts"
      data-maximus-category="shared"
      data-maximus-status="monitoring">

      <header className={styles.visuallyHidden}>
        <h2 id="cyber-alerts-title">Cyber Alerts Dashboard</h2>
      </header>

      <section
        role="region"
        aria-label="System status"
        data-maximus-section="status">
        <StatusPanel />
      </section>

      <section
        role="region"
        aria-label="Threat metrics"
        data-maximus-section="metrics">
        <MetricsGrid threatData={threatData} />
      </section>

      <section
        role="region"
        aria-label="Alerts stream"
        data-maximus-section="alerts">
        <AlertsList alerts={alerts} />
      </section>

      <section
        role="region"
        aria-label="Quick actions"
        data-maximus-section="actions">
        <QuickActions />
      </section>
    </article>
  );
};

export default CyberAlerts;
