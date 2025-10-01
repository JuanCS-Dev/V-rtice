import React from 'react';
import { Badge } from '../../../shared';
import styles from './StatisticsPanel.module.css';

const STATS = [
  { key: 'connectionsToday', label: 'Conexões Hoje', icon: 'fas fa-network-wired', variant: 'cyber' },
  { key: 'portScansDetected', label: 'Port Scans', icon: 'fas fa-radar', variant: 'high' },
  { key: 'suspiciousIPs', label: 'IPs Suspeitos', icon: 'fas fa-exclamation-triangle', variant: 'warning' },
  { key: 'blockedAttempts', label: 'Bloqueios', icon: 'fas fa-shield-alt', variant: 'success' }
];

export const StatisticsPanel = ({ statistics }) => {
  return (
    <div className={styles.container}>
      {STATS.map(stat => (
        <div key={stat.key} className={styles.statCard}>
          <div className={styles.statIcon}>
            <i className={stat.icon}></i>
          </div>
          <div className={styles.statContent}>
            <span className={styles.statLabel}>{stat.label}</span>
            <span className={styles.statValue}>{statistics[stat.key]}</span>
          </div>
        </div>
      ))}
    </div>
  );
};

export default StatisticsPanel;
