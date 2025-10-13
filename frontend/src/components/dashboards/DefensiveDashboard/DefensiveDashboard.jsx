/**
 * DEFENSIVE OPERATIONS DASHBOARD
 * Blue Team - Threat Detection & Monitoring
 * Production-Ready | Quality-First | Real Data Only
 */

import React, { useState, useEffect } from 'react';
import DefensiveHeader from './components/DefensiveHeader';
import DefensiveSidebar from './components/DefensiveSidebar';
import DefensiveFooter from './components/DefensiveFooter';
import ModuleContainer from './components/ModuleContainer';
import { useDefensiveMetrics } from './hooks/useDefensiveMetrics';
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

import '../../../styles/dashboards.css';
import './DefensiveDashboard.module.css';

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
  const [currentTime, setCurrentTime] = useState(new Date());
  const [activeModule, setActiveModule] = useState('threats');

  // Real data hooks (NO MOCKS)
  const { metrics, loading: metricsLoading } = useDefensiveMetrics();
  const { alerts, addAlert: _addAlert } = useRealTimeAlerts();

  // Update clock
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const activeModuleData = DEFENSIVE_MODULES.find(m => m.id === activeModule);
  const ActiveComponent = activeModuleData?.component;

  return (
    <div className="dashboard-container dashboard-defensive">
      {/* Scanline Effect */}
      <div className="scanline-overlay"></div>

      {/* Header */}
      <DefensiveHeader
        currentTime={currentTime}
        setCurrentView={setCurrentView}
        activeModule={activeModule}
        setActiveModule={setActiveModule}
        modules={DEFENSIVE_MODULES}
        metrics={metrics}
        metricsLoading={metricsLoading}
      />

      {/* Main Content Area */}
      <main className="dashboard-main">
        {/* Sidebar - Real-time Alerts */}
        <DefensiveSidebar
          alerts={alerts}
          metrics={metrics}
        />

        {/* Active Module Content */}
        <div className="dashboard-content">
          <ModuleContainer>
            {ActiveComponent ? <ActiveComponent /> : <div>Module not found</div>}
          </ModuleContainer>
        </div>
      </main>

      {/* Footer */}
      <DefensiveFooter
        alertsCount={alerts.length}
        metrics={metrics}
      />
    </div>
  );
};

export default DefensiveDashboard;
