/**
 * DEFENSIVE OPERATIONS DASHBOARD
 * Blue Team - Threat Detection & Monitoring
 * Production-Ready | Quality-First | Real Data Only
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - Fully navigable by Maximus AI via data-maximus-* attributes
 * - WCAG 2.1 AAA compliant
 * - Semantic HTML5 structure (article, section, aside)
 * - ARIA 1.2 patterns for landmarks and live regions
 *
 * Maximus can:
 * - Identify dashboard via data-maximus-module="defensive-dashboard"
 * - Monitor threats via data-maximus-monitor="threats"
 * - Navigate tools via data-maximus-tool attributes
 * - Access real-time alerts via data-maximus-live="true"
 *
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 * @version 2.0.0 (Maximus Vision)
 */

import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import DefensiveHeader from './components/DefensiveHeader';
import DefensiveSidebar from './components/DefensiveSidebar';
import { DashboardFooter } from '../../shared/DashboardFooter';
import ModuleContainer from './components/ModuleContainer';
import SkipLink from '../../shared/SkipLink';
import { useDefensiveMetrics } from '@/hooks/services/useDefensiveService';
import { useRealTimeAlerts } from './hooks/useRealTimeAlerts';

// Import defensive modules (already exist)
import ThreatMap from '../../cyber/ThreatMap';
import CyberAlerts from '../../cyber/CyberAlerts';
import DomainAnalyzer from '../../cyber/DomainAnalyzer';
import IpIntelligence from '../../cyber/IpIntelligence';
import NetworkMonitor from '../../cyber/NetworkMonitor';
import NmapScanner from '../../cyber/NmapScanner';
import SystemSecurity from '../../cyber/SystemSecurity';
import ExploitSearchWidget from '../../cyber/ExploitSearchWidget';
import MaximusCyberHub from '../../cyber/MaximusCyberHub';

// NEW: Active Immune Core defensive tools
import BehavioralAnalyzer from '../../cyber/BehavioralAnalyzer/BehavioralAnalyzer';
import EncryptedTrafficAnalyzer from '../../cyber/EncryptedTrafficAnalyzer/EncryptedTrafficAnalyzer';

import styles from './DefensiveDashboard.module.css';

const DEFENSIVE_MODULES = [
  { id: 'threats', name: 'THREAT MAP', icon: '🗺️', component: ThreatMap },
  { id: 'behavioral', name: 'BEHAVIOR ANALYSIS', icon: '🧠', component: BehavioralAnalyzer },
  { id: 'encrypted', name: 'TRAFFIC ANALYSIS', icon: '🔐', component: EncryptedTrafficAnalyzer },
  { id: 'domain', name: 'DOMAIN INTEL', icon: '🌐', component: DomainAnalyzer },
  { id: 'ip', name: 'IP ANALYSIS', icon: '🎯', component: IpIntelligence },
  { id: 'network', name: 'NET MONITOR', icon: '📡', component: NetworkMonitor },
  { id: 'nmap', name: 'NMAP SCAN', icon: '⚡', component: NmapScanner },
  { id: 'security', name: 'SYSTEM SEC', icon: '🔒', component: SystemSecurity },
  { id: 'exploits', name: 'CVE DATABASE', icon: '🐛', component: ExploitSearchWidget },
  { id: 'maximus', name: 'MAXIMUS HUB', icon: '🤖', component: MaximusCyberHub },
];

const DefensiveDashboard = ({ setCurrentView }) => {
  const { t } = useTranslation();
  const [currentTime, setCurrentTime] = useState(new Date());
  const [activeModule, setActiveModule] = useState('threats');

  // Real data hooks (NO MOCKS)
  // Boris Cherny Standard - GAP #38 FIX: Expose isRefetching and dataUpdatedAt
  const {
    data: metricsData,
    isLoading: metricsLoading,
    isRefetching: metricsRefetching,
    dataUpdatedAt: metricsUpdatedAt,
  } = useDefensiveMetrics();
  const { alerts, addAlert: _addAlert } = useRealTimeAlerts();

  // Provide default metrics if loading or undefined
  const metrics = metricsData || {
    threats: 0,
    suspiciousIPs: 0,
    domains: 0,
    monitored: 0,
  };

  // Update clock
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const activeModuleData = DEFENSIVE_MODULES.find(m => m.id === activeModule);
  const ActiveComponent = activeModuleData?.component;

  return (
    <article
      className={styles.dashboardContainer}

      aria-labelledby="defensive-dashboard-title"
      data-maximus-module="defensive-dashboard"
      data-maximus-navigable="true"
      data-maximus-version="2.0"
      data-maximus-category="blue-team">

      <SkipLink href="#defensive-main-content">{t('accessibility.skipToMain')}</SkipLink>

      {/* Scanline Effect - Decorative */}
      <div className={styles.scanlineOverlay} aria-hidden="true"></div>

      {/* Header */}
      <DefensiveHeader
        currentTime={currentTime}
        setCurrentView={setCurrentView}
        activeModule={activeModule}
        setActiveModule={setActiveModule}
        modules={DEFENSIVE_MODULES}
        metrics={metrics}
        metricsLoading={metricsLoading}
        metricsRefetching={metricsRefetching}
        metricsUpdatedAt={metricsUpdatedAt}
      />

      {/* Main Content Area */}
      <section
        id="defensive-main-content"
        className={styles.dashboardMain}

        aria-label="Defensive operations workspace"
        data-maximus-section="workspace">

        {/* Sidebar - Real-time Alerts */}
        <aside

          aria-label="Real-time security alerts"
          data-maximus-section="sidebar"
          data-maximus-live="true"
          data-maximus-monitor="alerts">

          <DefensiveSidebar
            alerts={alerts}
            metrics={metrics}
          />
        </aside>

        {/* Active Module Content */}
        <section
          id="defensive-tool-content"
          className={styles.dashboardContent}

          aria-label="Active defensive tool"
          aria-live="polite"
          aria-atomic="false"
          data-maximus-section="active-tool"
          data-maximus-tool={activeModule}
          data-maximus-interactive="true">

          <ModuleContainer>
            {ActiveComponent ? <ActiveComponent /> : <div role="alert">Module not found</div>}
          </ModuleContainer>
        </section>
      </section>

      {/* Footer */}
      <DashboardFooter
        moduleName="DEFENSIVE OPERATIONS"
        classification="CONFIDENCIAL"
        statusItems={[
          { label: 'CONNECTION', value: 'SECURE', online: true },
          { label: 'THREAT INTEL', value: 'ACTIVE', online: true },
          { label: 'SIEM', value: 'ONLINE', online: true }
        ]}
        metricsItems={[
          { label: 'ALERTS', value: alerts.length },
          { label: 'MONITORED', value: metrics?.monitored || 0 }
        ]}
      />
    </article>
  );
};

export default DefensiveDashboard;
