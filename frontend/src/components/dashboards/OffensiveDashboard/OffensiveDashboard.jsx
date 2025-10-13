/**
 * OffensiveDashboard - Red Team Operations Center
 *
 * Dashboard completa de operações ofensivas com:
 * - Network Reconnaissance
 * - Vulnerability Intelligence
 * - Web Attack Tools
 * - C2 Orchestration
 * - BAS (Breach & Attack Simulation)
 * - Offensive Gateway (Workflows)
 * - Real-time attack metrics
 * - Live execution monitoring
 *
 * i18n: Fully internationalized with pt-BR and en-US support
 * @version 1.0.0
 */

import React, { lazy, Suspense } from 'react';
import { useTranslation } from 'react-i18next';
import { OffensiveHeader } from './components/OffensiveHeader';
import { OffensiveSidebar } from './components/OffensiveSidebar';
import { OffensiveFooter } from './components/OffensiveFooter';
import { ModuleContainer } from './components/ModuleContainer';
import { useOffensiveMetrics } from './hooks/useOffensiveMetrics';
import { useRealTimeExecutions } from './hooks/useRealTimeExecutions';
import SkipLink from '../../shared/SkipLink';
import QueryErrorBoundary from '../../shared/QueryErrorBoundary';
import WidgetErrorBoundary from '../../shared/WidgetErrorBoundary';
import styles from './OffensiveDashboard.module.css';

// Lazy load offensive modules
const NetworkRecon = lazy(() => import('../../cyber/NetworkRecon/NetworkRecon'));
const VulnIntel = lazy(() => import('../../cyber/VulnIntel/VulnIntel'));
const WebAttack = lazy(() => import('../../cyber/WebAttack/WebAttack'));
const C2Orchestration = lazy(() => import('../../cyber/C2Orchestration/C2Orchestration'));
const BAS = lazy(() => import('../../cyber/BAS/BAS'));
const OffensiveGateway = lazy(() => import('../../cyber/OffensiveGateway/OffensiveGateway'));

// NEW: Offensive Arsenal Tools
const NetworkScanner = lazy(() => import('../../cyber/NetworkScanner/NetworkScanner'));

const LoadingFallback = () => {
  const { t } = useTranslation();
  return (
    <div className={styles.loadingModule}>
      <div className={styles.spinner} aria-label={t('common.loading')}></div>
      <p>{t('common.loading')}...</p>
    </div>
  );
};

export const OffensiveDashboard = ({ setCurrentView }) => {
  const { t } = useTranslation();
  const { metrics, loading: metricsLoading } = useOffensiveMetrics();
  const { executions } = useRealTimeExecutions();
  const [activeModule, setActiveModule] = React.useState('network-recon');

  const handleBack = () => {
    if (setCurrentView) {
      setCurrentView('main');
    }
  };

  const modules = [
    { id: 'network-scanner', name: t('dashboard.offensive.modules.networkScanner', 'NETWORK SCANNER'), icon: '🔍', component: NetworkScanner },
    { id: 'network-recon', name: t('dashboard.offensive.modules.networkRecon'), icon: '📡', component: NetworkRecon },
    { id: 'vuln-intel', name: t('dashboard.offensive.modules.vulnIntel'), icon: '🎯', component: VulnIntel },
    { id: 'web-attack', name: t('dashboard.offensive.modules.webAttack'), icon: '🌐', component: WebAttack },
    { id: 'c2-orchestration', name: t('dashboard.offensive.modules.c2Control'), icon: '⚡', component: C2Orchestration },
    { id: 'bas', name: t('dashboard.offensive.modules.bas'), icon: '💥', component: BAS },
    { id: 'offensive-gateway', name: t('dashboard.offensive.modules.gateway'), icon: '⚔️', component: OffensiveGateway }
  ];

  const currentModule = modules.find(m => m.id === activeModule);
  const ModuleComponent = currentModule?.component;

  return (
    <div className={styles.offensiveDashboard}>
      <SkipLink href="#main-content">{t('accessibility.skipToMain')}</SkipLink>

      <QueryErrorBoundary>
        <OffensiveHeader
          metrics={metrics}
          loading={metricsLoading}
          onBack={handleBack}
          activeModule={activeModule}
          modules={modules}
          onModuleChange={setActiveModule}
        />
      </QueryErrorBoundary>

      <div className={styles.mainContent}>
        <div id="main-content" className={styles.moduleArea} role="main">
          <Suspense fallback={<LoadingFallback />}>
            {ModuleComponent && (
              <WidgetErrorBoundary widgetName={currentModule.name}>
                <ModuleContainer moduleName={currentModule.name}>
                  <ModuleComponent />
                </ModuleContainer>
              </WidgetErrorBoundary>
            )}
          </Suspense>
        </div>

        <WidgetErrorBoundary widgetName="Live Executions">
          <OffensiveSidebar executions={executions} ariaLabel={t('accessibility.executionsSidebar')} />
        </WidgetErrorBoundary>
      </div>

      <OffensiveFooter />
    </div>
  );
};

export default OffensiveDashboard;
