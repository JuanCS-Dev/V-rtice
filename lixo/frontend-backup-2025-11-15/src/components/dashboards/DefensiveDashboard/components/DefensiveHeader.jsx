/**
 * DEFENSIVE HEADER - Blue Team Operations Header
 *
 * Semantic header with:
 * - Real-time defensive metrics
 * - Module navigation
 * - Control buttons
 * - Current timestamp display
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <header role="banner"> with data-maximus-section="header"
 * - Metrics as semantic region with data-maximus-metrics="defensive"
 * - <nav> with proper ARIA for module navigation
 * - All interactive elements keyboard accessible
 *
 * Maximus can:
 * - Identify header via data-maximus-section="header"
 * - Access metrics via data-maximus-metrics="defensive"
 * - Navigate modules via data-maximus-nav="modules"
 *
 * Performance: React.memo optimization
 * Design: Purple + Cyan color scheme (SOURCE OF TRUTH)
 * i18n: react-i18next (pt-BR, en-US)
 *
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 * @version 2.0.0 (Maximus Vision)
 */

import React, { useCallback } from "react";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import { MemoizedMetricCard } from "../../../optimized/MemoizedMetricCard";
import { formatTime } from "../../../../utils/dateHelpers";
import styles from "./DefensiveHeader.module.css";

const DefensiveHeader = React.memo(
  ({
    currentTime,
    setCurrentView,
    activeModule,
    setActiveModule,
    modules,
    metrics,
    metricsLoading,
    metricsRefetching, // Boris Cherny Standard - GAP #38 FIX
    metricsUpdatedAt, // Boris Cherny Standard - GAP #38 FIX
  }) => {
    const { t } = useTranslation();

    // Boris Cherny Standard - GAP #88 FIX: Extract inline functions to useCallback
    const handleBackToMain = useCallback(() => {
      setCurrentView("main");
    }, [setCurrentView]);

    const handleModuleClick = useCallback(
      (moduleId) => {
        setActiveModule(moduleId);
      },
      [setActiveModule],
    );

    // Boris Cherny Standard - GAP #38 FIX: Format last update time
    const formatLastUpdate = (timestamp) => {
      if (!timestamp) return null;
      const secondsAgo = Math.floor((Date.now() - timestamp) / 1000);
      if (secondsAgo < 60) return `${secondsAgo}s ago`;
      const minutesAgo = Math.floor(secondsAgo / 60);
      if (minutesAgo < 60) return `${minutesAgo}m ago`;
      const hoursAgo = Math.floor(minutesAgo / 60);
      return `${hoursAgo}h ago`;
    };

    return (
      <header
        className={styles.header}
        role="banner"
        data-maximus-section="header"
        data-maximus-category="defensive"
      >
        <div className={styles.topBar}>
          <div className={styles.titleSection}>
            <button
              onClick={handleBackToMain}
              className={styles.backButton}
              aria-label={t("navigation.back_to_hub")}
              data-maximus-action="back"
            >
              ← {t("common.back", "BACK").toUpperCase()}
            </button>

            <div className={styles.title}>
              <span className={styles.icon} aria-hidden="true">
                🛡️
              </span>
              <div>
                <h1 id="defensive-dashboard-title">
                  {t("dashboard.defensive.title", "DEFENSIVE OPERATIONS")}
                </h1>
                <p className={styles.subtitle}>
                  {t(
                    "dashboard.defensive.subtitle",
                    "Blue Team - Threat Detection & Monitoring",
                  )}{" "}
                  |{" "}
                  <time dateTime={currentTime.toISOString()}>
                    {formatTime(currentTime, "--:--:--")}
                  </time>
                </p>
              </div>
            </div>
          </div>

          <section
            className={styles.metrics}
            aria-label={t(
              "dashboard.defensive.metrics.title",
              "Defensive metrics",
            )}
            data-maximus-section="metrics"
            data-maximus-metrics="defensive"
          >
            {/* Boris Cherny Standard - GAP #38 FIX: Stale data indicator */}
            {metricsRefetching && (
              <div
                className={styles.staleIndicator}
                role="status"
                aria-live="polite"
                data-maximus-status="updating"
              >
                <span className={styles.spinner} aria-hidden="true">
                  ⟳
                </span>
                <span>{t("common.updating", "Updating")}...</span>
              </div>
            )}
            {!metricsRefetching && metricsUpdatedAt && (
              <div
                className={styles.lastUpdate}
                title={new Date(metricsUpdatedAt).toLocaleString()}
                data-maximus-timestamp={metricsUpdatedAt}
              >
                <span aria-label={t("common.last_updated", "Last updated")}>
                  📊 {formatLastUpdate(metricsUpdatedAt)}
                </span>
              </div>
            )}
            <MemoizedMetricCard
              label={t("dashboard.defensive.metrics.threats", "THREATS")}
              value={metrics.threats || 0}
              icon="🚨"
              loading={metricsLoading}
            />
            <MemoizedMetricCard
              label={t(
                "dashboard.defensive.metrics.suspiciousIPs",
                "SUSPICIOUS IPs",
              )}
              value={metrics.suspiciousIPs || 0}
              icon="🎯"
              loading={metricsLoading}
            />
            <MemoizedMetricCard
              label={t("dashboard.defensive.metrics.domains", "DOMAINS")}
              value={metrics.domains || 0}
              icon="🌐"
              loading={metricsLoading}
            />
            <MemoizedMetricCard
              label={t("dashboard.defensive.metrics.monitored", "MONITORED")}
              value={metrics.monitored || 0}
              icon="🛡️"
              loading={metricsLoading}
            />
          </section>
        </div>

        <nav
          className={styles.moduleNav}
          role="navigation"
          aria-label={t(
            "dashboard.defensive.navigation",
            "Defensive tools navigation",
          )}
          data-maximus-section="navigation"
          data-maximus-nav="modules"
        >
          {modules.map((module) => (
            <button
              key={module.id}
              onClick={() => handleModuleClick(module.id)}
              className={`${styles.moduleButton} ${activeModule === module.id ? styles.active : ""}`}
              aria-label={`${t("navigation.access_module", "Access module")}: ${module.name}`}
              aria-current={activeModule === module.id ? "page" : undefined}
              data-maximus-item={module.id}
              data-maximus-active={
                activeModule === module.id ? "true" : "false"
              }
            >
              <span className={styles.moduleIcon} aria-hidden="true">
                {module.icon}
              </span>
              <span>{module.name}</span>
            </button>
          ))}
        </nav>
      </header>
    );
  },
);

DefensiveHeader.displayName = "DefensiveHeader";

DefensiveHeader.propTypes = {
  currentTime: PropTypes.instanceOf(Date).isRequired,
  setCurrentView: PropTypes.func.isRequired,
  activeModule: PropTypes.string.isRequired,
  setActiveModule: PropTypes.func.isRequired,
  modules: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
      icon: PropTypes.string.isRequired,
    }),
  ).isRequired,
  metrics: PropTypes.shape({
    threats: PropTypes.number,
    suspiciousIPs: PropTypes.number,
    domains: PropTypes.number,
    monitored: PropTypes.number,
  }).isRequired,
  metricsLoading: PropTypes.bool.isRequired,
  metricsRefetching: PropTypes.bool, // Boris Cherny Standard - GAP #38 FIX
  metricsUpdatedAt: PropTypes.number, // Boris Cherny Standard - GAP #38 FIX
};

export default DefensiveHeader;
