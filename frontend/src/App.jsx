// /home/juan/vertice-dev/frontend/src/App.jsx

import React, { useState, useEffect, Suspense } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
// Boris Cherny Standard - GAP #103 FIX: Add React Query DevTools for staging
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import ErrorBoundary from "./components/ErrorBoundary";
import { LandingPage } from "./components/LandingPage";
import { queryClient } from "./config/queryClient";
import { SkipLink } from "./components/shared/SkipLink";
import { useModuleNavigation } from "./hooks/useModuleNavigation";
import { ToastProvider } from "./components/shared/Toast";
import { DashboardLoader } from "./components/shared/LoadingStates";
import { register as registerServiceWorker } from "./utils/serviceWorkerRegistration";
import { ServiceWorkerUpdateNotification } from "./components/shared/ServiceWorkerUpdateNotification";
import "./i18n/config"; // Initialize i18n

// Import new animation & micro-interaction styles
import "./styles/tokens/transitions.css";
import "./styles/micro-interactions.css";

// Lazy load all dashboards for optimal performance (code splitting)
const AdminDashboard = React.lazy(() => import("./components/AdminDashboard"));
const DefensiveDashboard = React.lazy(
  () => import("./components/dashboards/DefensiveDashboard/DefensiveDashboard"),
);
const OffensiveDashboard = React.lazy(
  () => import("./components/dashboards/OffensiveDashboard/OffensiveDashboard"),
);
const PurpleTeamDashboard = React.lazy(
  () =>
    import("./components/dashboards/PurpleTeamDashboard/PurpleTeamDashboard"),
);
const CockpitSoberano = React.lazy(
  () => import("./components/dashboards/CockpitSoberano/CockpitSoberano"),
);
const OSINTDashboard = React.lazy(() => import("./components/OSINTDashboard"));
const MaximusDashboard = React.lazy(
  () => import("./components/maximus/MaximusDashboard"),
);
const ReactiveFabricDashboard = React.lazy(
  () => import("./components/reactive-fabric/ReactiveFabricDashboard"),
);
const HITLDecisionConsole = React.lazy(
  () => import("./components/reactive-fabric/HITLDecisionConsole"),
);
const ToMEngineDashboard = React.lazy(
  () => import("./components/tom-engine/ToMEngineDashboard"),
);
const ImmuneSystemDashboard = React.lazy(
  () => import("./components/immune-system/ImmuneSystemDashboard"),
);
const MonitoringDashboard = React.lazy(
  () => import("./components/monitoring/MonitoringDashboard"),
);
const PenelopeDashboard = React.lazy(
  () => import("./components/penelope/PenelopeDashboard"),
);
const MABADashboard = React.lazy(
  () => import("./components/maba/MABADashboard"),
);
const MVPDashboard = React.lazy(() => import("./components/mvp/MVPDashboard"));

function App() {
  // 'main', 'admin', 'defensive', 'offensive', 'purple', 'cockpit', 'osint', 'maximus', 'reactive-fabric', 'hitl-console'
  const [currentView, setCurrentView] = useState("main");

  // Enable keyboard navigation
  useModuleNavigation(setCurrentView);

  // Register Service Worker for PWA (offline-first, caching)
  useEffect(() => {
    registerServiceWorker({
      onSuccess: () =>
        console.log("[SW] Service Worker registered successfully"),
      onUpdate: () =>
        console.log("[SW] New content available, reload to update"),
      onOffline: () => console.log("[SW] App is offline"),
      onOnline: () => console.log("[SW] App is back online"),
    });
  }, []);

  const views = {
    admin: (
      <ErrorBoundary context="admin-dashboard" title="Admin Dashboard Error">
        <AdminDashboard setCurrentView={setCurrentView} />
      </ErrorBoundary>
    ),
    defensive: (
      <ErrorBoundary
        context="defensive-dashboard"
        title="Defensive Dashboard Error"
      >
        <DefensiveDashboard setCurrentView={setCurrentView} />
      </ErrorBoundary>
    ),
    offensive: (
      <ErrorBoundary
        context="offensive-dashboard"
        title="Offensive Dashboard Error"
      >
        <OffensiveDashboard setCurrentView={setCurrentView} />
      </ErrorBoundary>
    ),
    purple: (
      <ErrorBoundary
        context="purple-team-dashboard"
        title="Purple Team Dashboard Error"
      >
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
      <ErrorBoundary
        context="maximus-dashboard"
        title="MAXIMUS AI Dashboard Error"
      >
        <MaximusDashboard setCurrentView={setCurrentView} />
      </ErrorBoundary>
    ),
    "reactive-fabric": (
      <ErrorBoundary
        context="reactive-fabric-dashboard"
        title="Reactive Fabric Dashboard Error"
      >
        <ReactiveFabricDashboard setCurrentView={setCurrentView} />
      </ErrorBoundary>
    ),
    "hitl-console": (
      <ErrorBoundary context="hitl-console" title="HITL Console Error">
        <HITLDecisionConsole setCurrentView={setCurrentView} />
      </ErrorBoundary>
    ),
    "tom-engine": (
      <ErrorBoundary context="tom-engine" title="ToM Engine Error">
        <ToMEngineDashboard setCurrentView={setCurrentView} />
      </ErrorBoundary>
    ),
    "immune-system": (
      <ErrorBoundary context="immune-system" title="Immune System Error">
        <ImmuneSystemDashboard setCurrentView={setCurrentView} />
      </ErrorBoundary>
    ),
    monitoring: (
      <ErrorBoundary context="monitoring" title="Monitoring Error">
        <MonitoringDashboard setCurrentView={setCurrentView} />
      </ErrorBoundary>
    ),
    penelope: (
      <ErrorBoundary context="penelope" title="PENELOPE Dashboard Error">
        <PenelopeDashboard setCurrentView={setCurrentView} />
      </ErrorBoundary>
    ),
    maba: (
      <ErrorBoundary context="maba" title="MABA Dashboard Error">
        <MABADashboard setCurrentView={setCurrentView} />
      </ErrorBoundary>
    ),
    mvp: (
      <ErrorBoundary context="mvp" title="MVP Dashboard Error">
        <MVPDashboard setCurrentView={setCurrentView} />
      </ErrorBoundary>
    ),
  };

  return (
    <QueryClientProvider client={queryClient}>
      {/* Boris Cherny Standard - GAP #103 FIX: React Query DevTools for staging/development */}
      {(import.meta.env.DEV || import.meta.env.MODE === 'staging') && (
        <ReactQueryDevtools initialIsOpen={false} position="bottom-right" />
      )}
      <ToastProvider>
        <ErrorBoundary context="app-root" title="Application Error">
          <SkipLink href="#main-content" />

          {/* PWA Update Notification */}
          <ServiceWorkerUpdateNotification />

          <main id="main-content" role="main" className="page-enter">
            {currentView === "main" ? (
              <LandingPage setCurrentView={setCurrentView} />
            ) : (
              <Suspense fallback={<DashboardLoader />}>
                {views[currentView] || (
                  <ErrorBoundary
                    context="unknown-view"
                    title="Unknown View Error"
                  >
                    <div>View not found: {currentView}</div>
                  </ErrorBoundary>
                )}
              </Suspense>
            )}
          </main>
        </ErrorBoundary>
      </ToastProvider>
    </QueryClientProvider>
  );
}

export default App;
