/**
 * ═══════════════════════════════════════════════════════════════════════════
 * UNIVERSAL DASHBOARD FOOTER - VÉRTICE CORE THEME
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Componente universal para footers de todas as dashboards.
 * Padrão único: Preto + Vermelho
 *
 * @implements {DOUTRINA_VERTICE} Artigo II - Padrão Pagani
 * @version 2.0.0
 */

import React from "react";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import styles from "./DashboardFooter.module.css";
import { formatTime } from "../../utils/dateHelpers";

export const DashboardFooter = ({
  moduleName = "VÉRTICE",
  classification = "CONFIDENCIAL",
  statusItems = [],
  metricsItems = [],
  showTimestamp = false,
}) => {
  const { t } = useTranslation();

  // Default status items se não fornecido
  const defaultStatusItems = [
    { label: "CONNECTION", value: "SECURE", online: true },
    { label: "SYSTEM", value: "ONLINE", online: true },
  ];

  const effectiveStatusItems =
    statusItems.length > 0 ? statusItems : defaultStatusItems;

  const currentTime = formatTime(new Date(), "--:--:--");

  return (
    <footer
      className={styles.footer}
      role="contentinfo"
      aria-label={t("accessibility.dashboardFooter", "Dashboard footer")}
    >
      {/* Left Section - Status Indicators */}
      <div className={styles.statusContainer}>
        {effectiveStatusItems.map((item, index) => (
          <div key={index} className={styles.statusItem}>
            <span
              className={`${styles.statusDot} ${item.online === false ? styles.offline : ""}`}
              aria-label={item.online === false ? "Offline" : "Online"}
            />
            <span className={styles.label}>{item.label}:</span>
            <span className={styles.value}>{item.value}</span>
          </div>
        ))}
      </div>

      {/* Center Section - Brand */}
      <div className={styles.brand}>
        {moduleName} | PROJETO VÉRTICE v2.0 | CLASSIFICAÇÃO: {classification}
      </div>

      {/* Right Section - Metrics */}
      <div className={styles.metrics}>
        {showTimestamp && (
          <div className={styles.metric}>
            <span className={styles.metricLabel}>TIME</span>
            <span className={styles.metricValue}>{currentTime}</span>
          </div>
        )}
        {metricsItems.map((metric, index) => (
          <div key={index} className={styles.metric}>
            <span className={styles.metricLabel}>{metric.label}</span>
            <span className={styles.metricValue}>{metric.value}</span>
          </div>
        ))}
      </div>
    </footer>
  );
};

DashboardFooter.propTypes = {
  moduleName: PropTypes.string,
  classification: PropTypes.string,
  statusItems: PropTypes.arrayOf(
    PropTypes.shape({
      label: PropTypes.string.isRequired,
      value: PropTypes.string.isRequired,
      online: PropTypes.bool,
    }),
  ),
  metricsItems: PropTypes.arrayOf(
    PropTypes.shape({
      label: PropTypes.string.isRequired,
      value: PropTypes.oneOfType([PropTypes.string, PropTypes.number])
        .isRequired,
    }),
  ),
  showTimestamp: PropTypes.bool,
};

export default DashboardFooter;
