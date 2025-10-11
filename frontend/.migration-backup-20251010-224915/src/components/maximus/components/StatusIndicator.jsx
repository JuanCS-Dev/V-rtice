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
    <div
      className="status-indicator"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        padding: '0.5rem 1rem',
        background: 'rgba(139, 92, 246, 0.1)',
        border: '1px solid rgba(139, 92, 246, 0.3)',
        borderRadius: '8px'
      }}
    >
      <span
        className={`status-dot ${getDotClass()}`}
        style={{
          width: '12px',
          height: '12px',
          borderRadius: '50%',
          position: 'relative',
          background: status === 'online' ? '#10B981' :
                     status === 'running' ? '#8B5CF6' :
                     status === 'idle' ? '#06B6D4' :
                     status === 'degraded' ? '#F59E0B' : '#64748B',
          boxShadow: status === 'online' ? '0 0 10px #10B981' :
                     status === 'running' ? '0 0 10px #8B5CF6' :
                     status === 'idle' ? '0 0 10px #06B6D4' : 'none'
        }}
      ></span>
      <div
        className="status-info"
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '0.125rem'
        }}
      >
        <span
          className="status-label"
          style={{
            fontSize: '0.6rem',
            color: '#94A3B8',
            textTransform: 'uppercase',
            letterSpacing: '1px'
          }}
        >
          {label}
        </span>
        <span
          className={`status-value ${getStatusColor(status)}`}
          style={{
            fontSize: '0.875rem',
            fontWeight: 'bold'
          }}
        >
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
