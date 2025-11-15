/**
 * ActivityItem - Activity Log Item Widget
 *
 * Displays a single activity/log item with timestamp, type, and action.
 * Supports severity-based color coding.
 *
 * Usage:
 * <ActivityItem
 *   timestamp="14:23:45"
 *   type="CORE"
 *   action="Chain-of-thought reasoning initiated"
 *   severity="success"
 * />
 *
 * @param {string} timestamp - Activity timestamp
 * @param {string} type - Activity type/source
 * @param {string} action - Activity description
 * @param {string} severity - Severity level (info, success, warning, critical)
 * @param {string} className - Additional CSS classes
 */

import React from 'react';
import PropTypes from 'prop-types';
import './ActivityItem.css';

export const ActivityItem = ({
  timestamp,
  type,
  action,
  severity = 'info',
  className = ''
}) => {
  const itemClasses = `activity-item activity-item-${severity} ${className}`;

  return (
    <div className={itemClasses}>
      <span className="activity-item-time">{timestamp}</span>
      <span className="activity-item-type">[{type}]</span>
      <span className="activity-item-action">{action}</span>
    </div>
  );
};

ActivityItem.propTypes = {
  timestamp: PropTypes.string.isRequired,
  type: PropTypes.string.isRequired,
  action: PropTypes.string.isRequired,
  severity: PropTypes.oneOf(['info', 'success', 'warning', 'critical']),
  className: PropTypes.string
};

export default ActivityItem;
