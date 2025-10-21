// /home/juan/vertice-dev/frontend/src/App.jsx

import React, { useState, lazy, Suspense } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import ErrorBoundary from './components/ErrorBoundary';
import { LandingPage } from './components/LandingPage';
import { queryClient } from './config/queryClient';
import { SkipLink } from './components/shared/SkipLink';
import { useModuleNavigation } from './hooks/useModuleNavigation';
import { ToastProvider } from './components/shared/Toast';
import { DashboardLoader } from './components/shared/LoadingStates';
import './i18n/config'; // Initialize i18n

// Import new animation & micro-interaction styles
import './styles/tokens/transitions.css';
import './styles/micro-interactions.css';

// Lazy load dashboards for code splitting
const AdminDashboard = lazy(() => import('./components/AdminDashboard'));
const DefensiveDashboard = lazy(() => import('./components/dashboards/DefensiveDashboard/DefensiveDashboard'));
const OffensiveDashboard = lazy(() => import('./components/dashboards/OffensiveDashboard/OffensiveDashboard'));
const PurpleTeamDashboard = lazy(() => import('./components/dashboards/PurpleTeamDashboard/PurpleTeamDashboard'));
const CockpitSoberano = lazy(() => import('./components/dashboards/CockpitSoberano/CockpitSoberano'));
const OSINTDashboard = lazy(() => import('./components/OSINTDashboard'));
const MaximusDashboard = lazy(() => import('./components/maximus/MaximusDashboard'));
const ReactiveFabricDashboard = lazy(() => import('./components/reactive-fabric/ReactiveFabricDashboard'));
const HITLDecisionConsole = lazy(() => import('./components/reactive-fabric/HITLDecisionConsole'));

function App() {
  // 'main', 'admin', 'defensive', 'offensive', 'purple', 'cockpit', 'osint', 'maximus', 'reactive-fabric', 'hitl-console'
  const [currentView, setCurrentView] = useState('main');

  // Enable keyboard navigation
  useModuleNavigation(setCurrentView);

  const views = {
    admin: (
      <ErrorBoundary context="admin-dashboard" title="Admin Dashboard Error">
        <AdminDashboard setCurrentView={setCurrentView} />
      </ErrorBoundary>
    ),
    defensive: (
      <ErrorBoundary context="defensive-dashboard" title="Defensive Dashboard Error">
        <DefensiveDashboard setCurrentView={setCurrentView} />
      </ErrorBoundary>
    ),
    offensive: (
      <ErrorBoundary context="offensive-dashboard" title="Offensive Dashboard Error">
        <OffensiveDashboard setCurrentView={setCurrentView} />
      </ErrorBoundary>
    ),
    purple: (
      <ErrorBoundary context="purple-team-dashboard" title="Purple Team Dashboard Error">
        <PurpleTeamDashboard setCurrentView={setCurrentView} />
      </ErrorBoundary>
    ),
    cockpit: (
      <ErrorBoundary context="cockpit-soberano" title="Cockpit Soberano Error">
        <CockpitSoberano setCurrentView={setCurrentView} />
      </ErrorBoundary>
    ),
    osint: (
      <ErrorBoundary context="osint-dashboard" title="OSINT Dashboard Error">
        <OSINTDashboard setCurrentView={setCurrentView} />
      </ErrorBoundary>
    ),
    maximus: (
      <ErrorBoundary context="maximus-dashboard" title="MAXIMUS AI Dashboard Error">
        <MaximusDashboard setCurrentView={setCurrentView} />
      </ErrorBoundary>
    ),
    'reactive-fabric': (
      <ErrorBoundary context="reactive-fabric-dashboard" title="Reactive Fabric Dashboard Error">
        <ReactiveFabricDashboard setCurrentView={setCurrentView} />
      </ErrorBoundary>
    ),
    'hitl-console': (
      <ErrorBoundary context="hitl-console" title="HITL Console Error">
        <HITLDecisionConsole setCurrentView={setCurrentView} />
      </ErrorBoundary>
    ),
  };

  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <ErrorBoundary context="app-root" title="Application Error">
          <SkipLink href="#main-content" />
          <main id="main-content" role="main" className="page-enter">
            {currentView === 'main' ? (
              <LandingPage setCurrentView={setCurrentView} />
            ) : (
              <Suspense fallback={<DashboardLoader />}>
                {views[currentView]}
              </Suspense>
            )}
          </main>
        </ErrorBoundary>
      </ToastProvider>
    </QueryClientProvider>
  );
}

export default App;
