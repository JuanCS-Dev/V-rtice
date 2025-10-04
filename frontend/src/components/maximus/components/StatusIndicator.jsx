/**
 * StatusIndicator - Reusable Status Display Component
 *
 * Displays a status dot + label + value for AI services.
 * Used by: MaximusStatusIndicators
 *
 * @param {string} label - Status label (e.g., "CORE", "ORACLE")
 * @param {string} status - Status value (online, idle, running, degraded, offline)
 * @param {Function} getStatusColor - Function to get color class based on status
 * @param {Function} t - i18n translation function
 */

import React from 'react';
import PropTypes from 'prop-types';

export const StatusIndicator = ({ label, status, getStatusColor, t }) => {
  const getDotClass = () => {
    if (status === 'online') return 'status-online';
    if (status === 'running') return 'status-running';
    if (status === 'idle') return 'status-idle';
    if (status === 'degraded') return 'status-degraded';
    return 'status-offline';
  };

  return (
    <div className="status-indicator">
      <span className={`status-dot ${getDotClass()}`}></span>
      <div className="status-info">
        <span className="status-label">{label}</span>
        <span className={`status-value ${getStatusColor(status)}`}>
          {t(`dashboard.maximus.status.${status}`)}
        </span>
      </div>
    </div>
  );
};

StatusIndicator.propTypes = {
  label: PropTypes.string.isRequired,
  status: PropTypes.oneOf(['online', 'idle', 'running', 'degraded', 'offline']).isRequired,
  getStatusColor: PropTypes.func.isRequired,
  t: PropTypes.func.isRequired
};

export default StatusIndicator;
