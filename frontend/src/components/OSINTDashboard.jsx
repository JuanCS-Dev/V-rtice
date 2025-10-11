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
import { OSINTFooter } from './osint/OSINTFooter';
import { AIProcessingOverlay } from './osint/AIProcessingOverlay';
import SkipLink from './shared/SkipLink';
import { Breadcrumb } from './shared/Breadcrumb';
import { useClock } from '../hooks/useClock';
import { useOSINTAlerts } from '../hooks/useOSINTAlerts';

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
    <div className="h-screen w-screen bg-gradient-to-br from-gray-900 via-black to-purple-900 text-purple-400 font-mono overflow-hidden flex flex-col">
      <SkipLink href="#main-content">{t('accessibility.skipToMain')}</SkipLink>

      {/* Scan Line */}
      <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-purple-400 to-transparent animate-pulse z-20"></div>

      <OSINTHeader
        currentTime={currentTime}
        setCurrentView={setCurrentView}
        activeModule={activeModule}
        setActiveModule={setActiveModule}
      />

      <main className="flex-1 flex min-h-0" role="main">
        {/* Sidebar de Alertas OSINT */}
        <aside
          className="w-80 border-r border-purple-400/30 bg-black/30 backdrop-blur-sm"
          aria-label={t('accessibility.alertsSidebar')}
        >
          <OSINTAlerts alerts={osintAlerts} systemStats={systemStats} />
        </aside>

        {/* Área Principal */}
        <div id="main-content" className="flex-1 p-4 overflow-hidden relative">
          {/* AI Processing Overlay */}
          <AIProcessingOverlay isVisible={isAIProcessing} />

          {moduleComponents[activeModule]}
        </div>
      </main>

      {/* Footer OSINT */}
      <OSINTFooter systemStats={systemStats} />
    </div>
  );
};

export default OSINTDashboard;
