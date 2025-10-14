import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import OSINTHeader from './osint/OSINTHeader';
import OSINTAlerts from './osint/OSINTAlerts';
import MaximusAIModule from './osint/MaximusAIModule';
import UsernameModule from './osint/UsernameModule';
import EmailModule from './osint/EmailModule';
import PhoneModule from './osint/PhoneModule';
import SocialModule from './osint/SocialModule';
import GoogleModule from './osint/GoogleModule';
import DarkWebModule from './osint/DarkWebModule';
import ReportsModule from './osint/ReportsModule';
import SocialMediaWidget from './osint/SocialMediaWidget';
import BreachDataWidget from './osint/BreachDataWidget';
import { OverviewModule } from './osint/OverviewModule';
import { DashboardFooter } from './shared/DashboardFooter';
import { AIProcessingOverlay } from './osint/AIProcessingOverlay';
import SkipLink from './shared/SkipLink';
import { Breadcrumb } from './shared/Breadcrumb';
import { useClock } from '../hooks/useClock';
import { useOSINTAlerts } from '../hooks/useOSINTAlerts';
import styles from './OSINTDashboard.module.css';

const OSINTDashboard = ({ setCurrentView }) => {
  const { t } = useTranslation();
  const [activeModule, setActiveModule] = useState('aurora');
  const [isAIProcessing, setIsAIProcessing] = useState(false);
  const [investigationResults, setInvestigationResults] = useState(null);
  const [systemStats] = useState({
    totalInvestigations: 0,
    activeTargets: 0,
    threatsDetected: 0,
    dataPoints: 0,
    aiAccuracy: 95.7
  });

  // Custom hooks
  const currentTime = useClock();
  const osintAlerts = useOSINTAlerts(t);

  const moduleComponents = {
    overview: <OverviewModule stats={systemStats} />,
    aurora: <MaximusAIModule setIsAIProcessing={setIsAIProcessing} setResults={setInvestigationResults} />,
    socialmedia: <SocialMediaWidget />,
    breachdata: <BreachDataWidget />,
    username: <UsernameModule />,
    email: <EmailModule />,
    phone: <PhoneModule />,
    social: <SocialModule />,
    google: <GoogleModule />,
    darkweb: <DarkWebModule />,
    reports: <ReportsModule results={investigationResults} />
  };

  return (
    <div className={styles.dashboard}>
      <SkipLink href="#main-content">{t('accessibility.skipToMain')}</SkipLink>

      {/* Scan Line */}
      <div className={styles.scanLine}></div>

      <OSINTHeader
        currentTime={currentTime}
        setCurrentView={setCurrentView}
        activeModule={activeModule}
        setActiveModule={setActiveModule}
      />

      <main className={styles.mainLayout} role="main">
        {/* Sidebar de Alertas OSINT */}
        <aside
          className={styles.sidebar}
          aria-label={t('accessibility.alertsSidebar')}
        >
          <OSINTAlerts alerts={osintAlerts} systemStats={systemStats} />
        </aside>

        {/* Área Principal */}
        <div id="main-content" className={styles.contentArea}>
          {/* AI Processing Overlay */}
          <AIProcessingOverlay isVisible={isAIProcessing} />

          {moduleComponents[activeModule]}
        </div>
      </main>

      {/* Footer OSINT */}
      <DashboardFooter
        moduleName="OSINT INTELLIGENCE"
        classification="CONFIDENCIAL"
        statusItems={[
          { label: 'CONNECTION', value: 'SECURE', online: true },
          { label: 'AURORA AI', value: 'ACTIVE', online: true },
          { label: 'OPERATOR', value: 'OSINT_OPS_001', online: true }
        ]}
        metricsItems={[
          { label: 'INVESTIGATIONS', value: systemStats.totalInvestigations },
          { label: 'THREATS', value: systemStats.threatsDetected },
          { label: 'AI ACCURACY', value: `${systemStats.aiAccuracy}%` }
        ]}
      />
    </div>
  );
};

export default OSINTDashboard;
