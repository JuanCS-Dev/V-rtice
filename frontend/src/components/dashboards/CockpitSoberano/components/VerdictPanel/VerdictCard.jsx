/**
 * VerdictCard - Individual Verdict Display Component
 *
 * @version 1.0.0
 */

import React from "react";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import styles from "./VerdictCard.module.css";
import { formatDateTime } from "@/utils/dateHelpers";

export const VerdictCard = ({ verdict, onViewEvidence, onDismiss }) => {
  const { t } = useTranslation();

  const getSeverityColor = () => {
    switch (verdict.severity) {
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

  const getSeverityIcon = () => {
    switch (verdict.severity) {
      case "CRITICAL":
        return "🚨";
      case "HIGH":
        return "⚠️";
      case "MEDIUM":
        return "⚡";
      case "LOW":
        return "ℹ️";
      default:
        return "•";
    }
  };

  const getCategoryIcon = () => {
    switch (verdict.category) {
      case "ALLIANCE":
        return "🤝";
      case "DECEPTION":
        return "🎭";
      case "INCONSISTENCY":
        return "❌";
      case "ANOMALY":
        return "⚠️";
      default:
        return "•";
    }
  };

  const formatTimestamp = (timestamp) => {
    return formatDateTime(timestamp, "N/A");
  };

  const confidencePercent = (verdict.confidence * 100).toFixed(0);

  return (
    <div
      className={styles.verdictCard}
      style={{ "--severity-color": getSeverityColor() }}
    >
      <div className={styles.cardHeader}>
        <div className={styles.severityBadge}>
          <span className={styles.severityIcon}>{getSeverityIcon()}</span>
          <span className={styles.severityText}>{verdict.severity}</span>
        </div>
        <div className={styles.categoryBadge}>
          <span className={styles.categoryIcon}>{getCategoryIcon()}</span>
          <span className={styles.categoryText}>{verdict.category}</span>
        </div>
        <time className={styles.timestamp}>
          {formatTimestamp(verdict.timestamp)}
        </time>
      </div>

      <div className={styles.cardBody}>
        <h3 className={styles.verdictTitle}>{verdict.title}</h3>

        {verdict.agents_involved && verdict.agents_involved.length > 0 && (
          <div className={styles.agentsSection}>
            <span className={styles.agentsLabel}>
              {t("cockpit.verdict.agents", "Agentes")}:
            </span>
            <div className={styles.agentsList}>
              {verdict.agents_involved.map((agent) => (
                <span key={agent} className={styles.agentTag}>
                  {agent}
                </span>
              ))}
            </div>
          </div>
        )}

        {verdict.target && (
          <div className={styles.targetSection}>
            <span className={styles.targetLabel}>
              {t("cockpit.verdict.target", "Alvo")}:
            </span>
            <span className={styles.targetValue}>{verdict.target}</span>
          </div>
        )}

        <div className={styles.confidenceSection}>
          <div className={styles.confidenceHeader}>
            <span className={styles.confidenceLabel}>
              {t("cockpit.verdict.confidence", "Confiança")}
            </span>
            <span className={styles.confidenceValue}>{confidencePercent}%</span>
          </div>
          <div className={styles.confidenceBar}>
            <div
              className={styles.confidenceFill}
              style={{ width: `${confidencePercent}%` }}
            />
          </div>
        </div>

        {verdict.recommended_action && (
          <div className={styles.actionSection}>
            <span className={styles.actionLabel}>
              {t("cockpit.verdict.action", "Ação Recomendada")}:
            </span>
            <span className={styles.actionValue}>
              {verdict.recommended_action}
            </span>
          </div>
        )}
      </div>

      <div className={styles.cardFooter}>
        <button
          className={styles.evidenceButton}
          onClick={onViewEvidence}
          disabled={
            !verdict.evidence_chain || verdict.evidence_chain.length === 0
          }
        >
          <span>📋</span>
          {t("cockpit.verdict.viewEvidence", "Ver Evidências")}
          {verdict.evidence_chain && (
            <span className={styles.evidenceCount}>
              ({verdict.evidence_chain.length})
            </span>
          )}
        </button>

        <button
          className={styles.dismissButton}
          onClick={onDismiss}
          aria-label={t("common.dismiss", "Dispensar")}
        >
          ✕
        </button>
      </div>
    </div>
  );
};

VerdictCard.propTypes = {
  verdict: PropTypes.shape({
    id: PropTypes.string.isRequired,
    severity: PropTypes.string.isRequired,
    category: PropTypes.string.isRequired,
    title: PropTypes.string.isRequired,
    timestamp: PropTypes.string.isRequired,
    agents_involved: PropTypes.arrayOf(PropTypes.string),
    target: PropTypes.string,
    confidence: PropTypes.number.isRequired,
    recommended_action: PropTypes.string,
    evidence_chain: PropTypes.array,
  }).isRequired,
  onViewEvidence: PropTypes.func.isRequired,
  onDismiss: PropTypes.func.isRequired,
};
