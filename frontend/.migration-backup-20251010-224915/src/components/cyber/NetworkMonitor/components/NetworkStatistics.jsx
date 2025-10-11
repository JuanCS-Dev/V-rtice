import React from 'react';
import styles from './NetworkStatistics.module.css';

/**
 * Displays real-time network statistics.
 */
const NetworkStatistics = ({ statistics }) => {
  return (
    <dl className={styles.statsGrid}>
      <div className={styles.statCard}>
        <dt className={styles.statLabel}>CONEXÕES HOJE</dt>
        <dd className={styles.statValue}>{statistics.connectionsToday}</dd>
      </div>
      <div className={`${styles.statCard} ${styles.portScans}`}>
        <dt className={styles.statLabel}>PORT SCANS</dt>
        <dd className={styles.statValue}>{statistics.portScansDetected}</dd>
      </div>
      <div className={`${styles.statCard} ${styles.suspiciousIPs}`}>
        <dt className={styles.statLabel}>IPS SUSPEITOS</dt>
        <dd className={styles.statValue}>{statistics.suspiciousIPs}</dd>
      </div>
      <div className={`${styles.statCard} ${styles.blockedAttempts}`}>
        <dt className={styles.statLabel}>BLOQUEADOS</dt>
        <dd className={styles.statValue}>{statistics.blockedAttempts}</dd>
      </div>
    </dl>
  );
};

export default React.memo(NetworkStatistics);
