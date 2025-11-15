/**
 * VerdictPanel - Real-time Verdict Display
 *
 * Displays verdict cards in timeline format with real-time updates
 * NO MOCKS - WebSocket-driven
 *
 * @version 1.0.0
 */

import React, { useState } from "react";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import { VerdictCard } from "./VerdictCard";
import { ProvenanceModal } from "../ProvenanceViewer/ProvenanceModal";
import styles from "./VerdictPanel.module.css";

export const VerdictPanel = ({
  verdicts = [],
  onDismiss,
  isConnected = false,
}) => {
  const { t } = useTranslation();
  const [selectedVerdict, setSelectedVerdict] = useState(null);
  const [filter, setFilter] = useState("ALL");

  const filteredVerdicts = verdicts.filter((v) => {
    if (filter === "ALL") return true;
    return v.severity === filter;
  });

  const severityCounts = verdicts.reduce((acc, v) => {
    acc[v.severity] = (acc[v.severity] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className={styles.verdictPanel}>
      <div className={styles.panelHeader}>
        <div className={styles.headerTitle}>
          <h2>{t("cockpit.verdicts.title", "Veredictos")}</h2>
          <div className={styles.connectionStatus}>
            <span
              className={`${styles.statusDot} ${isConnected ? styles.connected : styles.disconnected}`}
            ></span>
            <span className={styles.statusText}>
              {isConnected
                ? t("cockpit.verdicts.connected", "CONECTADO")
                : t("cockpit.verdicts.disconnected", "DESCONECTADO")}
            </span>
          </div>
        </div>

        <div className={styles.filterBar}>
          <FilterButton
            label={t("common.all", "TODOS")}
            count={verdicts.length}
            active={filter === "ALL"}
            onClick={() => setFilter("ALL")}
          />
          <FilterButton
            label="CRITICAL"
            count={severityCounts.CRITICAL || 0}
            active={filter === "CRITICAL"}
            onClick={() => setFilter("CRITICAL")}
            severity="CRITICAL"
          />
          <FilterButton
            label="HIGH"
            count={severityCounts.HIGH || 0}
            active={filter === "HIGH"}
            onClick={() => setFilter("HIGH")}
            severity="HIGH"
          />
          <FilterButton
            label="MEDIUM"
            count={severityCounts.MEDIUM || 0}
            active={filter === "MEDIUM"}
            onClick={() => setFilter("MEDIUM")}
            severity="MEDIUM"
          />
          <FilterButton
            label="LOW"
            count={severityCounts.LOW || 0}
            active={filter === "LOW"}
            onClick={() => setFilter("LOW")}
            severity="LOW"
          />
        </div>
      </div>

      <div className={styles.verdictTimeline}>
        {filteredVerdicts.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyIcon}>⚖️</div>
            <p>{t("cockpit.verdicts.empty", "Nenhum veredicto no momento")}</p>
            <small>
              {t(
                "cockpit.verdicts.emptyHint",
                "Aguardando análise de telemetria...",
              )}
            </small>
          </div>
        ) : (
          filteredVerdicts.map((verdict) => (
            <VerdictCard
              key={verdict.id}
              verdict={verdict}
              onViewEvidence={() => setSelectedVerdict(verdict)}
              onDismiss={() => onDismiss(verdict.id)}
            />
          ))
        )}
      </div>

      {selectedVerdict && (
        <ProvenanceModal
          verdict={selectedVerdict}
          onClose={() => setSelectedVerdict(null)}
        />
      )}
    </div>
  );
};

const FilterButton = ({ label, count, active, onClick, severity }) => {
  const getSeverityColor = (sev) => {
    switch (sev) {
      case "CRITICAL":
        return "#ef4444";
      case "HIGH":
        return "#f97316";
      case "MEDIUM":
        return "#f59e0b";
      case "LOW":
        return "#3b82f6";
      default:
        return "#6b7280";
    }
  };

  return (
    <button
      className={`${styles.filterButton} ${active ? styles.filterActive : ""}`}
      onClick={onClick}
      style={{
        "--filter-color": severity ? getSeverityColor(severity) : "#6b7280",
      }}
    >
      <span className={styles.filterLabel}>{label}</span>
      <span className={styles.filterCount}>{count}</span>
    </button>
  );
};

FilterButton.propTypes = {
  label: PropTypes.string.isRequired,
  count: PropTypes.number.isRequired,
  active: PropTypes.bool,
  onClick: PropTypes.func.isRequired,
  severity: PropTypes.string,
};

VerdictPanel.propTypes = {
  verdicts: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      severity: PropTypes.string.isRequired,
      title: PropTypes.string.isRequired,
      timestamp: PropTypes.string.isRequired,
      agents_involved: PropTypes.arrayOf(PropTypes.string),
      confidence: PropTypes.number,
      evidence_chain: PropTypes.array,
    }),
  ),
  onDismiss: PropTypes.func.isRequired,
  isConnected: PropTypes.bool,
};

// defaultProps migrated to default parameters (React 18 compatible)
