// /home/juan/vertice-dev/frontend/src/App.jsx

import React, { useState, lazy, Suspense } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useTranslation } from 'react-i18next';
import ErrorBoundary from './components/ErrorBoundary';
import { LandingPage } from './components/LandingPage';
import { queryClient } from './config/queryClient';
import { LanguageSwitcher } from './components/shared/LanguageSwitcher';
import { SkipLink } from './components/shared/SkipLink';
import './i18n/config'; // Initialize i18n

// Lazy load dashboards for code splitting
const AdminDashboard = lazy(() => import('./components/AdminDashboard'));
const DefensiveDashboard = lazy(() => import('./components/dashboards/DefensiveDashboard/DefensiveDashboard'));
const OffensiveDashboard = lazy(() => import('./components/dashboards/OffensiveDashboard/OffensiveDashboard'));
const PurpleTeamDashboard = lazy(() => import('./components/dashboards/PurpleTeamDashboard/PurpleTeamDashboard'));
const OSINTDashboard = lazy(() => import('./components/OSINTDashboard'));
const MaximusDashboard = lazy(() => import('./components/maximus/MaximusDashboard'));

// Loading component
const DashboardLoader = () => {
  const { t } = useTranslation();
  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #0a1929 0%, #001e3c 100%)',
      color: '#00f0ff',
      fontFamily: 'Courier New, monospace',
      fontSize: '1.5rem'
    }}>
      <div>
        <div className="loading-spinner" style={{
          border: '4px solid rgba(0, 240, 255, 0.1)',
          borderTop: '4px solid #00f0ff',
          borderRadius: '50%',
          width: '3rem',
          height: '3rem',
          animation: 'spin 1s linear infinite',
          margin: '0 auto 1rem'
        }}></div>
        {t('common.loading').toUpperCase()}...
      </div>
    </div>
  );
};

function App() {
  // 'main', 'admin', 'defensive', 'offensive', 'purple', 'osint', 'maximus'
  const [currentView, setCurrentView] = useState('main');

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
  };

  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary context="app-root" title="Application Error">
        <SkipLink href="#main-content" />
        <LanguageSwitcher position="top-right" />
        <main id="main-content" role="main">
          {currentView === 'main' ? (
            <LandingPage setCurrentView={setCurrentView} />
          ) : (
            <Suspense fallback={<DashboardLoader />}>
              {views[currentView]}
            </Suspense>
          )}
        </main>
      </ErrorBoundary>
      {process.env.NODE_ENV === 'development' && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  );
}

export default App;
