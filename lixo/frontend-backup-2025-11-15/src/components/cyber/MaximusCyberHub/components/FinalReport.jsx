import React from 'react';
import styles from './FinalReport.module.css';

export const FinalReport = ({ investigation, results }) => {
  if (investigation?.status !== 'completed' || Object.keys(results).length === 0) {
    return null;
  }

  const totalTime = investigation.endTime && investigation.startTime
    ? Math.round((investigation.endTime - investigation.startTime) / 1000)
    : 0;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>Final Report</h3>
        <span className={styles.icon}>📊</span>
      </div>
      <div className={styles.grid}>
        <div className={styles.metric}>
          <div className={styles.metricLabel}>Services Executed</div>
          <div className={styles.metricValue}>{Object.keys(results).length}</div>
        </div>
        <div className={styles.metric}>
          <div className={styles.metricLabel}>Total Time</div>
          <div className={styles.metricValue}>{totalTime}s</div>
        </div>
      </div>
    </div>
  );
};
