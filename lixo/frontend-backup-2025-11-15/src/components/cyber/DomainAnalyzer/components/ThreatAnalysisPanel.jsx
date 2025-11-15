import React from 'react';
import { Badge } from '../../../shared';
import { getScoreColor, getScoreTextColor } from '../utils/statusUtils';
import styles from './ThreatAnalysisPanel.module.css';

export const ThreatAnalysisPanel = ({ data }) => {
  const scoreColor = getScoreColor(data.reputation_score);
  const scoreTextColor = getScoreTextColor(data.reputation_score);

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>ANÁLISE DE AMEAÇAS</h3>

      <div className={styles.fields}>
        <div className={styles.field}>
          <span className={styles.label}>SCORE DE REPUTAÇÃO</span>
          <div className={styles.scoreContainer}>
            <div className={`${styles.scoreValue} ${scoreTextColor}`}>
              {data.reputation_score}/100
            </div>
            <div className={styles.progressBar}>
              <div
                className={`${styles.progressFill} ${scoreColor}`}
                style={{ width: `${data.reputation_score}%` }}
              />
            </div>
          </div>
        </div>

        <div className={styles.field}>
          <span className={styles.label}>AMEAÇAS DETECTADAS</span>
          <div className={styles.threats}>
            {data.threats_detected.map((threat, index) => (
              <Badge key={index} variant="critical" size="sm">
                {threat}
              </Badge>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ThreatAnalysisPanel;
