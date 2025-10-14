/**
 * Defensive Dashboard Sidebar
 * Real-time Alerts & Activity Feed
 *
 * 🎯 ZERO INLINE STYLES - 100% CSS Module
 * ✅ Theme-agnostic (Matrix + Enterprise)
 * ✅ Matches OffensiveSidebar design pattern
 */

import React from 'react';
import PropTypes from 'prop-types';
import styles from './DefensiveSidebar.module.css';

const DefensiveSidebar = ({ alerts }) => {
  const getSeverityClass = (severity) => {
    const severityMap = {
      critical: styles.critical,
      high: styles.high,
      medium: styles.medium,
      low: styles.low,
      info: styles.info
    };
    return severityMap[severity] || styles.info;
  };

  return (
    <aside className={styles.sidebar} aria-label="Live Alerts">
      {/* Sidebar Header */}
      <div className={styles.header}>
        <h3 className={styles.title}>
          🚨 LIVE ALERTS
        </h3>
        <div className={styles.count} aria-label={`${alerts.length} active alerts`}>
          {alerts.length} active alerts
        </div>
      </div>

      {/* Alerts List */}
      <div className={styles.alertsList} aria-live="polite" aria-atomic="false">
        {alerts.length === 0 ? (
          <div className={styles.emptyState}>
            No alerts at this time
          </div>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className={`${styles.alertItem} ${getSeverityClass(alert.severity)}`}
            >
              <div className={styles.alertHeader}>
                <span className={styles.alertType}>
                  {alert.type}
                </span>
                <span className={styles.alertSeverityBadge}>
                  {alert.severity.toUpperCase()}
                </span>
              </div>

              <div className={styles.alertMessage}>
                {alert.message}
              </div>

              {alert.source && (
                <div className={styles.alertSource}>
                  Source: {alert.source}
                </div>
              )}

              <div className={styles.alertTimestamp}>
                {alert.timestamp}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Quick Stats */}
      <div className={styles.stats}>
        <div className={styles.statsHeader}>
          QUICK STATS
        </div>
        <div className={styles.statsGrid}>
          <div className={styles.statRow}>
            <span className={styles.statLabel}>Critical Alerts:</span>
            <span className={`${styles.statValue} ${styles.critical}`}>
              {alerts.filter(a => a.severity === 'critical').length}
            </span>
          </div>
          <div className={styles.statRow}>
            <span className={styles.statLabel}>High Priority:</span>
            <span className={`${styles.statValue} ${styles.high}`}>
              {alerts.filter(a => a.severity === 'high').length}
            </span>
          </div>
          <div className={styles.statRow}>
            <span className={styles.statLabel}>Last Hour:</span>
            <span className={`${styles.statValue} ${styles.info}`}>
              {alerts.filter(a => {
                const alertTime = new Date(a.timestamp);
                const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000);
                return alertTime > oneHourAgo;
              }).length}
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
};

DefensiveSidebar.propTypes = {
  alerts: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
      type: PropTypes.string,
      severity: PropTypes.string,
      message: PropTypes.string,
      source: PropTypes.string,
      timestamp: PropTypes.oneOfType([PropTypes.string, PropTypes.instanceOf(Date)])
    })
  ).isRequired
};

export default DefensiveSidebar;
