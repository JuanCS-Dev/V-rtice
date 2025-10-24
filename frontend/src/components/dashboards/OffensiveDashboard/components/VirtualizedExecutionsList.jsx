/**
 * VirtualizedExecutionsList Component
 * ====================================
 *
 * High-performance virtualized list for offensive executions
 * Handles 1000+ executions without performance degradation
 *
 * Governed by: Constituição Vértice v2.5 - Phase 3 Optimizations
 */

import React, { useMemo, useCallback } from 'react';
import PropTypes from 'prop-types';
import VirtualList from '../../../shared/VirtualList';
import styles from './VirtualizedExecutionsList.module.css';

/**
 * Single execution row component (memoized)
 */
const ExecutionRow = React.memo(({ execution, style }) => {
  const statusClass = `status-${execution.status || 'unknown'}`;
  const typeClass = `type-${execution.type?.replace('_', '-') || 'default'}`;

  return (
    <div className={`${styles.executionRow} ${styles[statusClass]} ${styles[typeClass]}`} style={style}>
      <div className={styles.executionHeader}>
        <span className={styles.executionType}>{execution.type?.replace('_', ' ').toUpperCase()}</span>
        <span className={`${styles.statusBadge} ${styles[statusClass]}`}>
          {execution.status?.toUpperCase() || 'UNKNOWN'}
        </span>
      </div>
      <div className={styles.executionTarget}>
        <span className={styles.targetLabel}>Target:</span>
        <span className={styles.targetValue}>{execution.target || 'N/A'}</span>
      </div>
      {execution.results && (
        <div className={styles.executionResults}>
          {execution.results.ports_found && (
            <span className={styles.result}>Ports: {execution.results.ports_found}</span>
          )}
          {execution.results.vulnerabilities && (
            <span className={styles.result}>Vulns: {execution.results.vulnerabilities}</span>
          )}
        </div>
      )}
      <div className={styles.executionFooter}>
        <span className={styles.timestamp}>
          {new Date(execution.timestamp).toLocaleString()}
        </span>
        {execution.id && (
          <span className={styles.executionId}>
            ID: {String(execution.id).slice(0, 8)}
          </span>
        )}
      </div>
    </div>
  );
});

ExecutionRow.displayName = 'ExecutionRow';

ExecutionRow.propTypes = {
  execution: PropTypes.shape({
    id: PropTypes.string,
    type: PropTypes.string,
    status: PropTypes.string,
    target: PropTypes.string,
    timestamp: PropTypes.string.isRequired,
    results: PropTypes.object,
  }).isRequired,
  style: PropTypes.object.isRequired,
};

/**
 * VirtualizedExecutionsList - Main component
 */
export const VirtualizedExecutionsList = ({
  executions = [],
  onExecutionClick = null,
  filterStatus = null,
  filterType = null,
}) => {
  // Filter executions
  const filteredExecutions = useMemo(() => {
    let filtered = executions;

    if (filterStatus) {
      filtered = filtered.filter((exec) => exec.status === filterStatus);
    }

    if (filterType) {
      filtered = filtered.filter((exec) => exec.type === filterType);
    }

    return filtered;
  }, [executions, filterStatus, filterType]);

  // Render function
  const renderExecution = useCallback(
    ({ item: execution, index, style }) => {
      const handleClick = () => {
        if (onExecutionClick) {
          onExecutionClick(execution, index);
        }
      };

      return (
        <div onClick={handleClick} style={{ cursor: onExecutionClick ? 'pointer' : 'default' }}>
          <ExecutionRow execution={execution} style={style} />
        </div>
      );
    },
    [onExecutionClick]
  );

  // Statistics
  const stats = useMemo(() => {
    const running = filteredExecutions.filter((e) => e.status === 'running').length;
    const completed = filteredExecutions.filter((e) => e.status === 'completed').length;
    const failed = filteredExecutions.filter((e) => e.status === 'failed').length;

    return { running, completed, failed, total: filteredExecutions.length };
  }, [filteredExecutions]);

  return (
    <div className={styles.container}>
      {/* Statistics Bar */}
      <div className={styles.statsBar}>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Total:</span>
          <span className={styles.statValue}>{stats.total}</span>
        </div>
        <div className={`${styles.stat} ${styles.runningStat}`}>
          <span className={styles.statLabel}>Running:</span>
          <span className={styles.statValue}>{stats.running}</span>
        </div>
        <div className={`${styles.stat} ${styles.completedStat}`}>
          <span className={styles.statLabel}>Completed:</span>
          <span className={styles.statValue}>{stats.completed}</span>
        </div>
        <div className={`${styles.stat} ${styles.failedStat}`}>
          <span className={styles.statLabel}>Failed:</span>
          <span className={styles.statValue}>{stats.failed}</span>
        </div>
      </div>

      {/* Virtualized List */}
      <VirtualList
        items={filteredExecutions}
        renderItem={renderExecution}
        itemHeight={100}
        overscanCount={3}
        emptyMessage="No executions to display"
        className={styles.executionsList}
      />
    </div>
  );
};

VirtualizedExecutionsList.propTypes = {
  executions: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string,
      type: PropTypes.string,
      status: PropTypes.string,
      target: PropTypes.string,
      timestamp: PropTypes.string.isRequired,
      results: PropTypes.object,
    })
  ).isRequired,
  onExecutionClick: PropTypes.func,
  filterStatus: PropTypes.oneOf(['running', 'completed', 'failed', 'queued']),
  filterType: PropTypes.string,
};

export default VirtualizedExecutionsList;
