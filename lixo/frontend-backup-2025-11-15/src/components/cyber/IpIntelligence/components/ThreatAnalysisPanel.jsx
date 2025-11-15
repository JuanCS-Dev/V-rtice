import React from "react";
import { Badge } from "../../../shared";
import {
  getThreatBadgeVariant,
  getScoreColor,
  getThreatCategoryVariant,
} from "../utils/threatUtils";
import styles from "./ThreatAnalysisPanel.module.css";

export const ThreatAnalysisPanel = ({ data }) => {
  const scoreColor = getScoreColor(data.reputation.score);
  const threatVariant = getThreatBadgeVariant(data.threat_level);

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>ANÁLISE DE AMEAÇAS</h3>

      <div className={styles.fields}>
        {/* Threat Level */}
        <div className={styles.field}>
          <span className={styles.label}>NÍVEL DE AMEAÇA</span>
          <Badge variant={threatVariant} size="md">
            {data.threat_level.toUpperCase()}
          </Badge>
        </div>

        {/* Reputation Score */}
        <div className={styles.field}>
          <span className={styles.label}>SCORE DE REPUTAÇÃO</span>
          <div className={styles.scoreContainer}>
            <div className={styles.scoreValue}>
              <span
                className={
                  scoreColor === "bg-red-400"
                    ? styles.scoreLow
                    : scoreColor === "bg-orange-400"
                      ? styles.scoreMedium
                      : styles.scoreHigh
                }
              >
                {data.reputation.score}
              </span>
              <span className={styles.scoreTotal}>/100</span>
            </div>
            <div className={styles.progressBar}>
              <div
                className={`${styles.progressFill} ${scoreColor}`}
                style={{ width: `${data.reputation.score}%` }}
              />
            </div>
          </div>
        </div>

        {/* Threat Categories */}
        <div className={styles.field}>
          <span className={styles.label}>CATEGORIAS DE AMEAÇA</span>
          <div className={styles.categories}>
            {data.reputation.categories.map((category, index) => (
              <Badge
                key={index}
                variant={getThreatCategoryVariant(category)}
                size="sm"
              >
                {category.toUpperCase()}
              </Badge>
            ))}
          </div>
        </div>

        {/* Last Activity */}
        <div className={styles.field}>
          <span className={styles.label}>ÚLTIMA ATIVIDADE</span>
          <span className={styles.value}>{data.reputation.last_seen}</span>
        </div>
      </div>
    </div>
  );
};

export default ThreatAnalysisPanel;
