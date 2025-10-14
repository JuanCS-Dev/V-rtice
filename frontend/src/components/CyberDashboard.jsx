// /home/juan/vertice-dev/frontend/src/components/CyberDashboard.jsx

import React, { useState, useEffect } from 'react';
import CyberHeader from './cyber/CyberHeader';
import { DashboardFooter } from './shared/DashboardFooter';
import DomainAnalyzer from './cyber/DomainAnalyzer';
import IpIntelligence from './cyber/IpIntelligence';
import NetworkMonitor from './cyber/NetworkMonitor';
import NmapScanner from './cyber/NmapScanner';
import ThreatMap from './cyber/ThreatMap';
import CyberAlerts from './cyber/CyberAlerts';
import VulnerabilityScanner from './cyber/VulnerabilityScanner';
import SocialEngineering from './cyber/SocialEngineering';
import MaximusCyberHub from './cyber/MaximusCyberHub';
import ExploitSearchWidget from './cyber/ExploitSearchWidget';
// OFFENSIVE SECURITY ARSENAL
import NetworkRecon from './cyber/NetworkRecon';
import VulnIntel from './cyber/VulnIntel';
import WebAttack from './cyber/WebAttack';
import C2Orchestration from './cyber/C2Orchestration';
import BAS from './cyber/BAS';
import OffensiveGateway from './cyber/OffensiveGateway';
import styles from './CyberDashboard.module.css';

const CyberDashboard = ({ setCurrentView }) => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [activeModule, setActiveModule] = useState('maximus'); // AI-FIRST: Maximus AI Core como landing page
  const [cyberAlerts, setCyberAlerts] = useState([]);
  const [threatData] = useState({
    totalThreats: 127,
    activeDomains: 23,
    suspiciousIPs: 45,
    networkAlerts: 8
  });

  // Atualiza relógio
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Simula alertas cyber em tempo real
  useEffect(() => {
    const alertTimer = setInterval(() => {
      if (Math.random() > 0.9) {
        const alertTypes = [
          { type: 'MALWARE', message: 'Domínio malicioso detectado', severity: 'critical' },
          { type: 'PHISHING', message: 'Tentativa de phishing identificada', severity: 'high' },
          { type: 'BOTNET', message: 'Atividade de botnet detectada', severity: 'high' },
          { type: 'SCAN', message: 'Port scan detectado', severity: 'medium' },
          { type: 'INTEL', message: 'Nova inteligência de ameaça', severity: 'info' }
        ];
        
        const randomAlert = alertTypes[Math.floor(Math.random() * alertTypes.length)];
        const newAlert = {
          id: Date.now(),
          ...randomAlert,
          timestamp: new Date().toLocaleTimeString(),
          source: `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`
        };
        setCyberAlerts(prev => [newAlert, ...prev.slice(0, 19)]);
      }
    }, 5000);
    return () => clearInterval(alertTimer);
  }, []);

  const moduleComponents = {
    overview: <CyberOverview threatData={threatData} />,
    maximus: <MaximusCyberHub />,
    domain: <DomainAnalyzer />,
    ip: <IpIntelligence />,
    network: <NetworkMonitor />,
    nmap: <NmapScanner />,
    threats: <ThreatMap />,
    vulnscan: <VulnerabilityScanner />,
    socialeng: <SocialEngineering />,
    exploits: <ExploitSearchWidget />,
    // OFFENSIVE SECURITY ARSENAL
    netrecon: <NetworkRecon />,
    vulnintel: <VulnIntel />,
    webattack: <WebAttack />,
    c2: <C2Orchestration />,
    bas: <BAS />,
    gateway: <OffensiveGateway />
  };

  return (
    <div className={styles.dashboard}>
      {/* Scan Line */}
      <div className={styles.scanLine}></div>

      <CyberHeader
        currentTime={currentTime}
        setCurrentView={setCurrentView}
        activeModule={activeModule}
        setActiveModule={setActiveModule}
      />

      <main className={styles.mainLayout}>
        {/* Sidebar de Alertas */}
        <aside className={styles.sidebar}>
          <CyberAlerts alerts={cyberAlerts} threatData={threatData} />
        </aside>

        {/* Área Principal */}
        <div className={styles.contentArea}>
          <div className={styles.contentInner}>
            {moduleComponents[activeModule]}
          </div>
        </div>
      </main>

      {/* Footer Cyber */}
      <DashboardFooter
        moduleName="CYBER-SECURITY"
        classification="CONFIDENCIAL"
        statusItems={[
          { label: 'CONNECTION', value: 'SECURE', online: true },
          { label: 'THREAT INTEL', value: 'ACTIVE', online: true },
          { label: 'USER', value: 'CYBER_OPS_001', online: true }
        ]}
        metricsItems={[
          { label: 'ALERTS', value: cyberAlerts.length },
          { label: 'THREATS', value: threatData.totalThreats },
          { label: 'SUSPICIOUS IPS', value: threatData.suspiciousIPs }
        ]}
      />
    </div>
  );
};

// Componente Overview
const CyberOverview = ({ threatData }) => {
  return (
    <div className={styles.overviewContainer}>
      <div className={styles.overviewCard}>
        <h2 className={styles.overviewTitle}>
          CENTRO DE OPERAÇÕES CYBER
        </h2>

        {/* Métricas Principais */}
        <div className={styles.metricsGrid}>
          <div className={`${styles.metricCard} ${styles.critical}`}>
            <div className={`${styles.metricValue} ${styles.critical}`}>{threatData.totalThreats}</div>
            <div className={styles.metricLabel}>AMEAÇAS ATIVAS</div>
          </div>
          <div className={`${styles.metricCard} ${styles.warning}`}>
            <div className={`${styles.metricValue} ${styles.warning}`}>{threatData.activeDomains}</div>
            <div className={styles.metricLabel}>DOMÍNIOS SUSPEITOS</div>
          </div>
          <div className={`${styles.metricCard} ${styles.alert}`}>
            <div className={`${styles.metricValue} ${styles.alert}`}>{threatData.suspiciousIPs}</div>
            <div className={styles.metricLabel}>IPS MALICIOSOS</div>
          </div>
          <div className={`${styles.metricCard} ${styles.info}`}>
            <div className={`${styles.metricValue} ${styles.info}`}>{threatData.networkAlerts}</div>
            <div className={styles.metricLabel}>ALERTAS DE REDE</div>
          </div>
        </div>

        {/* Status dos Módulos */}
        <div className={styles.modulesSection}>
          <h3 className={styles.modulesTitle}>STATUS DOS MÓDULOS</h3>
          <div className={styles.modulesGrid}>
            <div className={styles.moduleCard}>
              <div className={styles.moduleHeader}>
                <span className={styles.moduleName}>Domain Analyzer</span>
                <div className={styles.statusDot}></div>
              </div>
              <div className={styles.moduleInfo}>Monitorando 1,247 domínios</div>
            </div>
            <div className={styles.moduleCard}>
              <div className={styles.moduleHeader}>
                <span className={styles.moduleName}>IP Intelligence</span>
                <div className={styles.statusDot}></div>
              </div>
              <div className={styles.moduleInfo}>Analisando 5,832 IPs</div>
            </div>
            <div className={styles.moduleCard}>
              <div className={styles.moduleHeader}>
                <span className={styles.moduleName}>Network Monitor</span>
                <div className={styles.statusDot}></div>
              </div>
              <div className={styles.moduleInfo}>Tempo real ativo</div>
            </div>
            <div className={styles.moduleCard}>
              <div className={styles.moduleHeader}>
                <span className={styles.moduleName}>Nmap Scanner</span>
                <div className={styles.statusDot}></div>
              </div>
              <div className={styles.moduleInfo}>Pronto para varreduras</div>
            </div>
            <div className={styles.moduleCard}>
              <div className={styles.moduleHeader}>
                <span className={styles.moduleName}>Threat Map</span>
                <div className={styles.statusDot}></div>
              </div>
              <div className={styles.moduleInfo}>Visualização global</div>
            </div>
            <div className={`${styles.moduleCard} ${styles.offensive}`}>
              <div className={styles.moduleHeader}>
                <span className={`${styles.moduleName} ${styles.offensive}`}>Vulnerability Scanner ⚠️</span>
                <div className={`${styles.statusDot} ${styles.offensive}`}></div>
              </div>
              <div className={`${styles.moduleInfo} ${styles.offensive}`}>Ferramenta ofensiva ativa</div>
            </div>
            <div className={`${styles.moduleCard} ${styles.offensive}`}>
              <div className={styles.moduleHeader}>
                <span className={`${styles.moduleName} ${styles.offensive}`}>Social Engineering ⚠️</span>
                <div className={`${styles.statusDot} ${styles.offensive}`}></div>
              </div>
              <div className={`${styles.moduleInfo} ${styles.offensive}`}>Campanhas disponíveis</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CyberDashboard;
