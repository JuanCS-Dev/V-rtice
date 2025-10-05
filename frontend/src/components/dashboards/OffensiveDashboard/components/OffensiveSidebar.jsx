/**
 * OffensiveSidebar - Real-time Execution Monitor
 * Displays active scans, exploits, and C2 sessions
 */

import React from 'react';
import PropTypes from 'prop-types';
import styles from './OffensiveSidebar.module.css';

export const OffensiveSidebar = ({ executions, ariaLabel }) => {
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

  const getStatusClass = (status) => {
    const statusMap = {
      running: styles.running,
      completed: styles.completed,
      failed: styles.failed,
      pending: styles.pending
    };
    return statusMap[status] || styles.pending;
  };

  return (
    <aside className={styles.sidebar} aria-label={ariaLabel || 'Live Executions'}>
      <div className={styles.sidebarHeader}>
        <h3 className={styles.sidebarTitle}>
          <span className={styles.sidebarIcon} aria-hidden="true">⚡</span>
          LIVE EXECUTIONS
        </h3>
        <div className={styles.badge} aria-label={`${executions.length} active executions`}>{executions.length}</div>
      </div>

      <div className={styles.executionList} aria-live="polite" aria-atomic="false">
        {executions.length === 0 ? (
          <div className={styles.noExecutions}>
            <div className={styles.emptyIcon}>🎯</div>
            <p>No active executions</p>
            <span>Start a scan or attack to see activity here</span>
          </div>
        ) : (
          executions.map((execution, index) => (
            <div
              key={execution.id || index}
              className={`${styles.executionCard} ${getStatusClass(execution.status)}`}
            >
              <div className={styles.executionHeader}>
                <span className={styles.executionType}>{execution.type || 'SCAN'}</span>
                <span className={`${styles.executionStatus} ${getStatusClass(execution.status)}`}>
                  {execution.status?.toUpperCase() || 'PENDING'}
                </span>
              </div>

              <div className={styles.executionTarget}>
                <span className={styles.targetIcon}>🎯</span>
                <span className={styles.targetValue}>{execution.target || 'Unknown'}</span>
              </div>

              {execution.progress !== undefined && (
                <div className={styles.progressBar}>
                  <div
                    className={styles.progressFill}
                    style={{ width: `${execution.progress}%` }}
                  />
                  <span className={styles.progressText}>{execution.progress}%</span>
                </div>
              )}

              {execution.findings && execution.findings.length > 0 && (
                <div className={styles.findings}>
                  <div className={styles.findingsLabel}>Findings:</div>
                  {execution.findings.slice(0, 2).map((finding, idx) => (
                    <div
                      key={idx}
                      className={`${styles.finding} ${getSeverityClass(finding.severity)}`}
                    >
                      <span className={styles.findingSeverity}>
                        {finding.severity?.toUpperCase() || 'INFO'}
                      </span>
                      <span className={styles.findingText}>{finding.description}</span>
                    </div>
                  ))}
                  {execution.findings.length > 2 && (
                    <div className={styles.morefindings}>
                      +{execution.findings.length - 2} more
                    </div>
                  )}
                </div>
              )}

              <div className={styles.executionTime}>
                {execution.timestamp
                  ? new Date(execution.timestamp).toLocaleTimeString()
                  : 'Just now'}
              </div>
            </div>
          ))
        )}
      </div>
    </aside>
  );
};

OffensiveSidebar.propTypes = {
  executions: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
      type: PropTypes.string,
      status: PropTypes.string,
      target: PropTypes.string,
      progress: PropTypes.number,
      findings: PropTypes.array,
      timestamp: PropTypes.oneOfType([PropTypes.string, PropTypes.instanceOf(Date)])
    })
  ).isRequired,
  ariaLabel: PropTypes.string
};
