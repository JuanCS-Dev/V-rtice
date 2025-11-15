/**
 * OFFENSIVE HEADER - Red Team Operations Header
 *
 * Semantic header with:
 * - Real-time offensive metrics
 * - Module navigation
 * - Control buttons
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <header> with data-maximus-section="header"
 * - Metrics as semantic description list (<dl>, <dt>, <dd>)
 * - <nav> with proper ARIA for keyboard navigation
 * - All interactive elements keyboard accessible
 *
 * Maximus can:
 * - Identify header via data-maximus-section="header"
 * - Access metrics via data-maximus-metrics="offensive"
 * - Navigate modules via data-maximus-nav="modules"
 *
 * Performance: React.memo optimization
 * i18n: react-i18next (pt-BR, en-US)
 *
 * @see MAXIMUS_VISION_PROTOCOL_HTML_BLUEPRINT.md
 * @version 2.0.0 (Maximus Vision)
 */

import React from "react";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import useKeyboardNavigation from "../../../../hooks/useKeyboardNavigation";
import { MemoizedMetricCard } from "../../../optimized/MemoizedMetricCard";
import styles from "./OffensiveHeader.module.css";

export const OffensiveHeader = React.memo(
  ({
    metrics,
    loading,
    metricsRefetching, // Boris Cherny Standard - GAP #38 FIX
    metricsUpdatedAt, // Boris Cherny Standard - GAP #38 FIX
    onBack,
    activeModule,
    modules,
    onModuleChange,
  }) => {
    const { t } = useTranslation();

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

    const { getItemProps } = useKeyboardNavigation({
      itemCount: modules.length,
      onSelect: (index) => onModuleChange(modules[index].id),
      orientation: "horizontal",
      loop: true,
    });

    return (
      <header
        className={styles.header}
        role="banner"
        data-maximus-section="header"
        data-maximus-category="offensive"
      >
        <div className={styles.topBar}>
          <div className={styles.titleSection}>
            <button
              onClick={onBack}
              className={styles.backButton}
              aria-label={t("navigation.back_to_hub")}
              data-maximus-action="back"
            >
              ← {t("common.back").toUpperCase()}
            </button>

            <div className={styles.title}>
              <span className={styles.icon} aria-hidden="true">
                ⚔️
              </span>
              <div>
                <h1 id="offensive-dashboard-title">
                  {t("dashboard.offensive.title")}
                </h1>
                <p className={styles.subtitle}>
                  {t("dashboard.offensive.subtitle")}
                </p>
              </div>
            </div>
          </div>

          <section
            className={styles.metrics}
            aria-label={t(
              "dashboard.offensive.metrics.title",
              "Offensive metrics",
            )}
            data-maximus-section="metrics"
            data-maximus-metrics="offensive"
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
                  ⚔️ {formatLastUpdate(metricsUpdatedAt)}
                </span>
              </div>
            )}

            <MemoizedMetricCard
              label={t("dashboard.offensive.metrics.activeScans")}
              value={metrics.activeScans || 0}
              icon="📡"
              loading={loading}
            />
            <MemoizedMetricCard
              label={t("dashboard.offensive.metrics.exploitsFound")}
              value={metrics.exploitsFound || 0}
              icon="🎯"
              loading={loading}
            />
            <MemoizedMetricCard
              label={t("dashboard.offensive.metrics.targets")}
              value={metrics.targets || 0}
              icon="🔍"
              loading={loading}
            />
            <MemoizedMetricCard
              label={t("dashboard.offensive.metrics.sessions")}
              value={metrics.c2Sessions || 0}
              icon="⚡"
              loading={loading}
            />
          </section>
        </div>

        <nav
          className={styles.moduleNav}
          role="navigation"
          aria-label={t(
            "dashboard.offensive.navigation",
            "Offensive tools navigation",
          )}
          data-maximus-section="navigation"
          data-maximus-nav="modules"
        >
          {modules.map((module, index) => (
            <button
              key={module.id}
              {...getItemProps(index, {
                onClick: () => onModuleChange(module.id),
                className: `${styles.moduleButton} ${activeModule === module.id ? styles.active : ""}`,
                "aria-label": `${t("navigation.access_module")}: ${module.name}`,
                "aria-current": activeModule === module.id ? "page" : undefined,
                "data-maximus-item": module.id,
                "data-maximus-active":
                  activeModule === module.id ? "true" : "false",
              })}
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

OffensiveHeader.displayName = "OffensiveHeader";

OffensiveHeader.propTypes = {
  metrics: PropTypes.shape({
    activeScans: PropTypes.number,
    exploitsFound: PropTypes.number,
    targets: PropTypes.number,
    c2Sessions: PropTypes.number,
  }),
  loading: PropTypes.bool,
  metricsRefetching: PropTypes.bool, // Boris Cherny Standard - GAP #38 FIX
  metricsUpdatedAt: PropTypes.number, // Boris Cherny Standard - GAP #38 FIX
  onBack: PropTypes.func.isRequired,
  activeModule: PropTypes.string.isRequired,
  modules: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired,
      icon: PropTypes.string.isRequired,
    }),
  ).isRequired,
  onModuleChange: PropTypes.func.isRequired,
};
