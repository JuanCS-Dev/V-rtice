/**
 * OffensiveSidebar - Real-time Execution Monitor
 * Displays active scans, exploits, and C2 sessions
 * Now with Virtual Scrolling for 100x performance on large lists
 */

import React from 'react';
import PropTypes from 'prop-types';
import { VirtualizedExecutionsList } from './VirtualizedExecutionsList';
import styles from './OffensiveSidebar.module.css';

export const OffensiveSidebar = ({ executions, ariaLabel }) => {
  return (
    <aside className={styles.sidebar} role="complementary" aria-label={ariaLabel || 'Live Executions'}>
      <div className={styles.sidebarHeader}>
        <h3 className={styles.sidebarTitle}>
          <span className={styles.sidebarIcon} aria-hidden="true">⚡</span>
          LIVE EXECUTIONS
        </h3>
        <div className={styles.badge} aria-label={`${executions.length} active executions`}>{executions.length}</div>
      </div>

      {/* Virtualized List for 100x performance */}
      <VirtualizedExecutionsList
        executions={executions}
        ariaLabel="Live execution feed"
      />
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
