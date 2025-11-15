/**
 * FruitCard - Card individual de um Fruto do Espírito
 * ===================================================
 *
 * Visualiza métricas de um fruto específico com score e ícone.
 */

import React from "react";
import styles from "./FruitCard.module.css";

export const FruitCard = ({ fruit, icon, data, color = "#00ff88" }) => {
  if (!data) {
    return (
      <div className={styles.fruitCard} style={{ borderColor: color }}>
        <div className={styles.icon}>{icon}</div>
        <div className={styles.name}>{fruit}</div>
        <div className={styles.loading}>Carregando...</div>
      </div>
    );
  }

  const score = data.score || 0;
  const greek = data.greek || "";

  // Determine color based on score
  const getScoreColor = (score) => {
    if (score >= 80) return "#00ff88"; // Green
    if (score >= 60) return "#ffd700"; // Gold
    if (score >= 40) return "#ffaa00"; // Orange
    return "#ff6b6b"; // Red
  };

  const scoreColor = getScoreColor(score);

  return (
    <div className={styles.fruitCard} style={{ borderColor: color }}>
      <div className={styles.icon}>{icon}</div>
      <div className={styles.name}>{fruit}</div>
      <div className={styles.greek}>{greek}</div>

      <div className={styles.scoreContainer}>
        <div className={styles.scoreValue} style={{ color: scoreColor }}>
          {score}
        </div>
        <div className={styles.scoreLabel}>/100</div>
      </div>

      {/* Progress bar */}
      <div className={styles.progressBar}>
        <div
          className={styles.progressFill}
          style={{
            width: `${score}%`,
            background: `linear-gradient(90deg, ${color}, ${scoreColor})`,
          }}
        ></div>
      </div>

      {/* Optional: Show specific metrics */}
      {data.interventions_compassionate !== undefined && (
        <div className={styles.metrics}>
          <div className={styles.metricRow}>
            <span className={styles.metricLabel}>Intervenções:</span>
            <span className={styles.metricValue}>
              {data.interventions_compassionate}
            </span>
          </div>
        </div>
      )}

      {data.successes_celebrated !== undefined && (
        <div className={styles.metrics}>
          <div className={styles.metricRow}>
            <span className={styles.metricLabel}>Celebrações:</span>
            <span className={styles.metricValue}>
              {data.successes_celebrated}
            </span>
          </div>
        </div>
      )}

      {data.patches_within_limits !== undefined && (
        <div className={styles.metrics}>
          <div className={styles.metricRow}>
            <span className={styles.metricLabel}>Patches nos limites:</span>
            <span className={styles.metricValue}>
              {data.patches_within_limits}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default FruitCard;
