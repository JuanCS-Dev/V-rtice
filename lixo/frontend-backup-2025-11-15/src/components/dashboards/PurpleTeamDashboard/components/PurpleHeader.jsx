/**
 * PURPLE HEADER - Purple Team Operations Header
 *
 * Semantic header with:
 * - Combined offensive + defensive metrics
 * - View navigation (Split, Timeline, Analysis)
 * - Coverage and correlation stats
 *
 * AI-FIRST DESIGN (Maximus Vision Protocol):
 * - <header role="banner"> with data-maximus-section="header"
 * - Metrics as semantic region with data-maximus-metrics="purple"
 * - View navigation with data-maximus-nav="views"
 * - Keyboard navigation via useKeyboardNavigation hook
 *
 * Maximus can:
 * - Identify header via data-maximus-section="header"
 * - Access metrics via data-maximus-metrics="purple"
 * - Navigate views via data-maximus-nav="views"
 * - Track active view via data-maximus-active
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
import styles from "./PurpleHeader.module.css";

export const PurpleHeader = React.memo(
  ({ onBack, activeView, onViewChange, stats }) => {
    const { t } = useTranslation();

    const views = ["split", "timeline", "analysis"];
    const { getItemProps } = useKeyboardNavigation({
      itemCount: views.length,
      onSelect: (index) => onViewChange(views[index]),
      orientation: "horizontal",
      loop: true,
    });

    return (
      <header
        className={styles.header}
        role="banner"
        data-maximus-section="header"
        data-maximus-category="purple-team"
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
                🟣
              </span>
              <div>
                <h1 id="purple-team-dashboard-title">
                  {t("dashboard.purple.title")}
                </h1>
                <p className={styles.subtitle}>
                  {t("dashboard.purple.subtitle")}
                </p>
              </div>
            </div>
          </div>

          <section
            className={styles.metrics}
            aria-label={t(
              "dashboard.purple.metrics.title",
              "Purple team metrics",
            )}
            data-maximus-section="metrics"
            data-maximus-metrics="purple"
          >
            <div
              className={`${styles.metric} ${styles.redMetric}`}
              data-metric-type="offensive"
            >
              <span className={styles.metricLabel}>
                {t("dashboard.purple.metrics.activeAttacks")}
              </span>
              <span className={styles.metricValue}>
                {stats.activeAttacks || 0}
              </span>
            </div>
            <div
              className={`${styles.metric} ${styles.blueMetric}`}
              data-metric-type="defensive"
            >
              <span className={styles.metricLabel}>
                {t("dashboard.purple.metrics.detections")}
              </span>
              <span className={styles.metricValue}>
                {stats.detections || 0}
              </span>
            </div>
            <div
              className={`${styles.metric} ${styles.purpleMetric}`}
              data-metric-type="coverage"
            >
              <span className={styles.metricLabel}>
                {t("dashboard.purple.metrics.coverage")}
              </span>
              <span className={styles.metricValue}>{stats.coverage || 0}%</span>
            </div>
            <div
              className={`${styles.metric} ${styles.greenMetric}`}
              data-metric-type="correlation"
            >
              <span className={styles.metricLabel}>
                {t("dashboard.purple.metrics.correlations")}
              </span>
              <span className={styles.metricValue}>
                {stats.correlations || 0}
              </span>
            </div>
          </section>
        </div>

        <nav
          className={styles.viewNav}
          role="navigation"
          aria-label={t(
            "dashboard.purple.navigation",
            "Purple team views navigation",
          )}
          data-maximus-section="navigation"
          data-maximus-nav="views"
        >
          <button
            {...getItemProps(0, {
              onClick: () => onViewChange("split"),
              className: `${styles.viewButton} ${activeView === "split" ? styles.active : ""}`,
              "aria-label": `${t("navigation.access_view")}: ${t("dashboard.purple.views.split")}`,
              "aria-current": activeView === "split" ? "page" : undefined,
              "data-maximus-view": "split",
              "data-maximus-active": activeView === "split" ? "true" : "false",
            })}
          >
            <span className={styles.viewIcon} aria-hidden="true">
              ⚔️
            </span>
            <span>{t("dashboard.purple.views.split")}</span>
          </button>
          <button
            {...getItemProps(1, {
              onClick: () => onViewChange("timeline"),
              className: `${styles.viewButton} ${activeView === "timeline" ? styles.active : ""}`,
              "aria-label": `${t("navigation.access_view")}: ${t("dashboard.purple.views.timeline")}`,
              "aria-current": activeView === "timeline" ? "page" : undefined,
              "data-maximus-view": "timeline",
              "data-maximus-active":
                activeView === "timeline" ? "true" : "false",
            })}
          >
            <span className={styles.viewIcon} aria-hidden="true">
              ⏱️
            </span>
            <span>{t("dashboard.purple.views.timeline")}</span>
          </button>
          <button
            {...getItemProps(2, {
              onClick: () => onViewChange("analysis"),
              className: `${styles.viewButton} ${activeView === "analysis" ? styles.active : ""}`,
              "aria-label": `${t("navigation.access_view")}: ${t("dashboard.purple.views.analysis")}`,
              "aria-current": activeView === "analysis" ? "page" : undefined,
              "data-maximus-view": "analysis",
              "data-maximus-active":
                activeView === "analysis" ? "true" : "false",
            })}
          >
            <span className={styles.viewIcon} aria-hidden="true">
              📊
            </span>
            <span>{t("dashboard.purple.views.analysis")}</span>
          </button>
        </nav>
      </header>
    );
  },
);

PurpleHeader.displayName = "PurpleHeader";

PurpleHeader.propTypes = {
  onBack: PropTypes.func.isRequired,
  activeView: PropTypes.string.isRequired,
  onViewChange: PropTypes.func.isRequired,
  stats: PropTypes.shape({
    activeAttacks: PropTypes.number,
    detections: PropTypes.number,
    coverage: PropTypes.number,
    correlations: PropTypes.number,
  }),
};
