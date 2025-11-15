/**
 * ProvenanceModal - Evidence Chain Viewer
 *
 * @version 1.0.0
 */

import React from "react";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import {
  formatDateTime,
  formatDate,
  formatTime,
  getTimestamp,
} from "@/utils/dateHelpers";
import styles from "./ProvenanceModal.module.css";

export const ProvenanceModal = ({ verdict, onClose }) => {
  const { t } = useTranslation();

  if (!verdict) return null;

  return (
    <div
      className={styles.modalOverlay}
      onClick={onClose}
      onKeyDown={(e) => e.key === "Escape" && onClose()}
      role="dialog"
      aria-modal="true"
      tabIndex={-1}
    >
      <div
        className={styles.modalContent}
        onClick={(e) => e.stopPropagation()}
        role="document"
      >
        <div className={styles.modalHeader}>
          <h2>
            <span>📋</span>
            {t("cockpit.provenance.title", "Cadeia de Evidências")}
          </h2>
          <button className={styles.closeButton} onClick={onClose}>
            ✕
          </button>
        </div>

        <div className={styles.modalBody}>
          <div className={styles.verdictSummary}>
            <h3>{verdict.title}</h3>
            <div className={styles.summaryMeta}>
              <span className={styles.severity}>{verdict.severity}</span>
              <span className={styles.category}>{verdict.category}</span>
              <span className={styles.confidence}>
                {(verdict.confidence * 100).toFixed(0)}% confiança
              </span>
            </div>
          </div>

          <div className={styles.evidenceChain}>
            <h4>
              {t("cockpit.provenance.evidence", "Evidências")} (
              {verdict.evidence_chain?.length || 0})
            </h4>
            {verdict.evidence_chain && verdict.evidence_chain.length > 0 ? (
              <div className={styles.evidenceList}>
                {verdict.evidence_chain.map((evidence, index) => (
                  <div key={index} className={styles.evidenceItem}>
                    <div className={styles.evidenceIndex}>{index + 1}</div>
                    <div className={styles.evidenceContent}>
                      <div className={styles.evidenceType}>
                        {evidence.type || "TELEMETRY"}
                      </div>
                      <div className={styles.evidenceText}>
                        {typeof evidence === "string"
                          ? evidence
                          : JSON.stringify(evidence, null, 2)}
                      </div>
                      {evidence.timestamp && (
                        <time className={styles.evidenceTime}>
                          {formatDateTime(evidence.timestamp)}
                        </time>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className={styles.emptyEvidence}>
                {t(
                  "cockpit.provenance.noEvidence",
                  "Nenhuma evidência disponível",
                )}
              </div>
            )}
          </div>
        </div>

        <div className={styles.modalFooter}>
          <button className={styles.closeButtonFooter} onClick={onClose}>
            {t("common.close", "Fechar")}
          </button>
        </div>
      </div>
    </div>
  );
};

ProvenanceModal.propTypes = {
  verdict: PropTypes.shape({
    title: PropTypes.string,
    severity: PropTypes.string,
    category: PropTypes.string,
    confidence: PropTypes.number,
    evidence_chain: PropTypes.array,
  }),
  onClose: PropTypes.func.isRequired,
};
