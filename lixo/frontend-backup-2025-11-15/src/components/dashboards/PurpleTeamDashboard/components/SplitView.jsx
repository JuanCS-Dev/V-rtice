/**
 * SplitView - Side-by-side Red Team & Blue Team Operations
 * Real-time correlation between attacks and detections
 */

import React from "react";
import styles from "./SplitView.module.css";

export const SplitView = ({
  attackData,
  defenseData,
  correlations,
  loading,
}) => {
  const getCorrelationForAttack = (attackId) => {
    return correlations.find((c) => c.attackId === attackId);
  };

  const getCorrelationForDetection = (detectionId) => {
    return correlations.find((c) => c.detectionId === detectionId);
  };

  return (
    <div className={styles.splitView}>
      {/* Red Team Panel */}
      <div className={styles.panel}>
        <div className={styles.panelHeader}>
          <div className={styles.headerContent}>
            <span className={styles.headerIcon}>⚔️</span>
            <div>
              <h2 className={styles.redTitle}>RED TEAM</h2>
              <p className={styles.panelSubtitle}>Offensive Operations</p>
            </div>
          </div>
          <div className={styles.headerBadge}>
            {attackData.active.length} ACTIVE
          </div>
        </div>

        <div className={styles.panelContent}>
          {loading ? (
            <div className={styles.loading}>
              <div className={styles.spinner}></div>
              <p>Loading attack data...</p>
            </div>
          ) : attackData.active.length === 0 ? (
            <div className={styles.empty}>
              <div className={styles.emptyIcon}>🎯</div>
              <p>No active attacks</p>
              <span>Start an offensive operation to see activity here</span>
            </div>
          ) : (
            <div className={styles.attackList}>
              {attackData.active.map((attack, index) => {
                const correlation = getCorrelationForAttack(attack.id);
                return (
                  <div
                    key={attack.id || index}
                    className={`${styles.attackCard} ${
                      correlation ? styles.correlated : ""
                    }`}
                  >
                    <div className={styles.cardHeader}>
                      <span className={styles.attackType}>{attack.type}</span>
                      <span className={styles.attackStatus}>
                        {attack.status}
                      </span>
                    </div>

                    <div className={styles.cardBody}>
                      <div className={styles.cardField}>
                        <span className={styles.fieldLabel}>Target:</span>
                        <span className={styles.fieldValue}>
                          {attack.target}
                        </span>
                      </div>
                      <div className={styles.cardField}>
                        <span className={styles.fieldLabel}>Technique:</span>
                        <span className={styles.fieldValue}>
                          {attack.technique}
                        </span>
                      </div>
                      {attack.progress !== undefined && (
                        <div className={styles.progress}>
                          <div
                            className={styles.progressBar}
                            style={{ width: `${attack.progress}%` }}
                          />
                        </div>
                      )}
                    </div>

                    {correlation && (
                      <div className={styles.correlationIndicator}>
                        ✓ DETECTED BY BLUE TEAM
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Correlation Connector */}
      <div className={styles.connector}>
        <div className={styles.connectorLine}></div>
        <div className={styles.connectorIcon}>🟣</div>
        <div className={styles.connectorLabel}>
          {correlations.length} CORRELATIONS
        </div>
      </div>

      {/* Blue Team Panel */}
      <div className={styles.panel}>
        <div className={styles.panelHeader}>
          <div className={styles.headerContent}>
            <span className={styles.headerIcon}>🛡️</span>
            <div>
              <h2 className={styles.blueTitle}>BLUE TEAM</h2>
              <p className={styles.panelSubtitle}>Detection & Response</p>
            </div>
          </div>
          <div className={styles.headerBadge}>
            {defenseData.detections.length} DETECTED
          </div>
        </div>

        <div className={styles.panelContent}>
          {loading ? (
            <div className={styles.loading}>
              <div className={styles.spinner}></div>
              <p>Loading detection data...</p>
            </div>
          ) : defenseData.detections.length === 0 ? (
            <div className={styles.empty}>
              <div className={styles.emptyIcon}>🔍</div>
              <p>No detections</p>
              <span>Monitoring for security events...</span>
            </div>
          ) : (
            <div className={styles.detectionList}>
              {defenseData.detections.map((detection, index) => {
                const correlation = getCorrelationForDetection(detection.id);
                return (
                  <div
                    key={detection.id || index}
                    className={`${styles.detectionCard} ${
                      correlation ? styles.correlated : ""
                    }`}
                  >
                    <div className={styles.cardHeader}>
                      <span className={styles.detectionType}>
                        {detection.type}
                      </span>
                      <span
                        className={`${styles.severity} ${styles[detection.severity]}`}
                      >
                        {detection.severity}
                      </span>
                    </div>

                    <div className={styles.cardBody}>
                      <div className={styles.cardField}>
                        <span className={styles.fieldLabel}>Source:</span>
                        <span className={styles.fieldValue}>
                          {detection.source}
                        </span>
                      </div>
                      <div className={styles.cardField}>
                        <span className={styles.fieldLabel}>Rule:</span>
                        <span className={styles.fieldValue}>
                          {detection.rule}
                        </span>
                      </div>
                      <div className={styles.cardField}>
                        <span className={styles.fieldLabel}>Confidence:</span>
                        <span className={styles.fieldValue}>
                          {detection.confidence}%
                        </span>
                      </div>
                    </div>

                    {correlation && (
                      <div className={styles.correlationIndicator}>
                        ✓ LINKED TO RED TEAM ATTACK
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
