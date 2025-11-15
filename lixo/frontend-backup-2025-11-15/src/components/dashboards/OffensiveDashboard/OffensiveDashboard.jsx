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
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - Fully navigable by Maximus AI via data-maximus-* attributes
 * - WCAG 2.1 AAA compliant
 * - Semantic HTML5 structure (article, section, aside)
 * - ARIA 1.2 patterns for landmarks and live regions
 *
 * Maximus can:
 * - Identify dashboard via data-maximus-module="offensive-dashboard"
 * - Navigate between tools via data-maximus-tool attributes
 * - Monitor executions via data-maximus-live="true"
 * - Access all interactive elements via aria-labels
 *
 * i18n: Fully internationalized with pt-BR and en-US support
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 * @version 2.0.0 (Maximus Vision)
 */

import React, { lazy, Suspense } from "react";
import { useTranslation } from "react-i18next";
import { OffensiveHeader } from "./components/OffensiveHeader";
import { OffensiveSidebar } from "./components/OffensiveSidebar";
import { DashboardFooter } from "../../shared/DashboardFooter";
import { ModuleContainer } from "./components/ModuleContainer";
import { useOffensiveMetrics } from "@/hooks/services/useOffensiveService";
import { useRealTimeExecutions } from "./hooks/useRealTimeExecutions";
import SkipLink from "../../shared/SkipLink";
import QueryErrorBoundary from "../../shared/QueryErrorBoundary";
import WidgetErrorBoundary from "../../shared/WidgetErrorBoundary";
import styles from "./OffensiveDashboard.module.css";

// Lazy load offensive modules
const NetworkRecon = lazy(
  () => import("../../cyber/NetworkRecon/NetworkRecon"),
);
const VulnIntel = lazy(() => import("../../cyber/VulnIntel/VulnIntel"));
const WebAttack = lazy(() => import("../../cyber/WebAttack/WebAttack"));
const C2Orchestration = lazy(
  () => import("../../cyber/C2Orchestration/C2Orchestration"),
);
const BAS = lazy(() => import("../../cyber/BAS/BAS"));
const OffensiveGateway = lazy(
  () => import("../../cyber/OffensiveGateway/OffensiveGateway"),
);

// NEW: Offensive Arsenal Tools
const NetworkScanner = lazy(
  () => import("../../cyber/NetworkScanner/NetworkScanner"),
);

// NEW: Defensive Arsenal Tools (Active Immune System)
const BehavioralAnalyzer = lazy(
  () => import("../../cyber/BehavioralAnalyzer/BehavioralAnalyzer"),
);
const TrafficAnalyzer = lazy(
  () => import("../../cyber/EncryptedTrafficAnalyzer/EncryptedTrafficAnalyzer"),
);

const LoadingFallback = () => {
  const { t } = useTranslation();
  return (
    <div className={styles.loadingModule}>
      <div className={styles.spinner} aria-label={t("common.loading")}></div>
      <p>{t("common.loading")}...</p>
    </div>
  );
};

export const OffensiveDashboard = ({ setCurrentView }) => {
  const { t } = useTranslation();
  // Boris Cherny Standard - GAP #38 FIX: Expose isRefetching and dataUpdatedAt
  const {
    data: metricsData,
    isLoading: metricsLoading,
    isRefetching: metricsRefetching,
    dataUpdatedAt: metricsUpdatedAt,
  } = useOffensiveMetrics();
  const { executions } = useRealTimeExecutions();
  const [activeModule, setActiveModule] = React.useState("network-recon");

  // Provide default metrics if loading or undefined
  const metrics = metricsData || {
    activeScans: 0,
    exploitsFound: 0,
    targets: 0,
    c2Sessions: 0,
  };

  const handleBack = () => {
    if (setCurrentView) {
      setCurrentView("main");
    }
  };

  const modules = [
    {
      id: "network-scanner",
      name: t("dashboard.offensive.modules.networkScanner", "NETWORK SCANNER"),
      icon: "🔍",
      component: NetworkScanner,
    },
    {
      id: "network-recon",
      name: t("dashboard.offensive.modules.networkRecon"),
      icon: "📡",
      component: NetworkRecon,
    },
    {
      id: "vuln-intel",
      name: t("dashboard.offensive.modules.vulnIntel"),
      icon: "🎯",
      component: VulnIntel,
    },
    {
      id: "web-attack",
      name: t("dashboard.offensive.modules.webAttack"),
      icon: "🌐",
      component: WebAttack,
    },
    {
      id: "c2-orchestration",
      name: t("dashboard.offensive.modules.c2Control"),
      icon: "⚡",
      component: C2Orchestration,
    },
    {
      id: "bas",
      name: t("dashboard.offensive.modules.bas"),
      icon: "💥",
      component: BAS,
    },
    {
      id: "offensive-gateway",
      name: t("dashboard.offensive.modules.gateway"),
      icon: "⚔️",
      component: OffensiveGateway,
    },
    {
      id: "behavioral-analyzer",
      name: t("dashboard.defensive.modules.behavioral", "BEHAVIORAL ANALYZER"),
      icon: "🧠",
      component: BehavioralAnalyzer,
    },
    {
      id: "traffic-analyzer",
      name: t("dashboard.defensive.modules.traffic", "TRAFFIC ANALYZER"),
      icon: "🔒",
      component: TrafficAnalyzer,
    },
  ];

  const currentModule = modules.find((m) => m.id === activeModule);
  const ModuleComponent = currentModule?.component;

  return (
    <article
      className={styles.offensiveDashboard}
      aria-labelledby="offensive-dashboard-title"
      data-maximus-module="offensive-dashboard"
      data-maximus-navigable="true"
      data-maximus-version="2.0"
      data-maximus-category="red-team"
    >
      <SkipLink href="#offensive-tool-content">
        {t("accessibility.skipToMain")}
      </SkipLink>

      <QueryErrorBoundary>
        <OffensiveHeader
          metrics={metrics}
          loading={metricsLoading}
          metricsRefetching={metricsRefetching}
          metricsUpdatedAt={metricsUpdatedAt}
          onBack={handleBack}
          activeModule={activeModule}
          modules={modules}
          onModuleChange={setActiveModule}
        />
      </QueryErrorBoundary>

      <section
        className={styles.mainContent}
        aria-label={t(
          "dashboard.offensive.workspace",
          "Offensive operations workspace",
        )}
        data-maximus-section="workspace"
      >
        <section
          id="offensive-tool-content"
          className={styles.moduleArea}
          aria-label={t(
            "dashboard.offensive.activeTool",
            "Active offensive tool",
          )}
          aria-live="polite"
          aria-atomic="false"
          data-maximus-section="active-tool"
          data-maximus-tool={activeModule}
          data-maximus-interactive="true"
        >
          <Suspense fallback={<LoadingFallback />}>
            {ModuleComponent && (
              <WidgetErrorBoundary widgetName={currentModule.name}>
                <ModuleContainer moduleName={currentModule.name}>
                  <ModuleComponent />
                </ModuleContainer>
              </WidgetErrorBoundary>
            )}
          </Suspense>
        </section>

        <aside
          aria-label={t(
            "accessibility.executionsSidebar",
            "Live executions sidebar",
          )}
          data-maximus-section="sidebar"
          data-maximus-live="true"
          data-maximus-monitor="executions"
        >
          <WidgetErrorBoundary widgetName="Live Executions">
            <OffensiveSidebar
              executions={executions}
              ariaLabel={t("accessibility.executionsSidebar")}
            />
          </WidgetErrorBoundary>
        </aside>
      </section>

      <DashboardFooter
        moduleName="OFFENSIVE OPERATIONS"
        classification="TOP SECRET"
        statusItems={[
          { label: "SYSTEM", value: "ONLINE", online: true },
          { label: "MODE", value: "RED TEAM", online: true },
          { label: "OPSEC", value: "ENABLED", online: true },
        ]}
        metricsItems={[
          { label: "EXECUTIONS", value: executions.length },
          { label: "ACTIVE", value: currentModule?.name || "N/A" },
        ]}
        showTimestamp={true}
      />
    </article>
  );
};

export default OffensiveDashboard;
