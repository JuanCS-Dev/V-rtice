/**
 * Defensive Dashboard Sidebar
 * Real-time Alerts & Activity Feed
 */

import React from 'react';

const SEVERITY_COLORS = {
  critical: '#ef4444',
  high: '#f59e0b',
  medium: '#3b82f6',
  low: '#10b981',
  info: '#64748b'
};

const DefensiveSidebar = ({ alerts, metrics }) => {
  return (
    <aside className="dashboard-sidebar">
      {/* Sidebar Header */}
      <div style={{
        padding: '1rem',
        borderBottom: '1px solid rgba(0, 240, 255, 0.3)',
        background: 'rgba(0, 0, 0, 0.5)'
      }}>
        <h3 style={{
          fontSize: '1.125rem',
          fontWeight: 'bold',
          color: '#00f0ff',
          marginBottom: '0.5rem'
        }}>
          🚨 LIVE ALERTS
        </h3>
        <div style={{
          fontSize: '0.75rem',
          opacity: 0.7
        }}>
          {alerts.length} active alerts
        </div>
      </div>

      {/* Alerts List */}
      <div style={{ padding: '0.5rem', overflowY: 'auto', maxHeight: 'calc(100vh - 300px)' }}>
        {alerts.length === 0 ? (
          <div style={{
            padding: '2rem 1rem',
            textAlign: 'center',
            opacity: 0.5,
            fontSize: '0.875rem'
          }}>
            No alerts at this time
          </div>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className={`alert-item alert-${alert.severity}`}
              style={{
                borderLeftColor: SEVERITY_COLORS[alert.severity] || SEVERITY_COLORS.info
              }}
            >
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                marginBottom: '0.25rem'
              }}>
                <span style={{
                  fontWeight: 'bold',
                  fontSize: '0.875rem',
                  color: SEVERITY_COLORS[alert.severity]
                }}>
                  {alert.type}
                </span>
                <span style={{
                  fontSize: '0.75rem',
                  opacity: 0.6
                }}>
                  {alert.severity.toUpperCase()}
                </span>
              </div>

              <div style={{
                fontSize: '0.875rem',
                marginBottom: '0.25rem'
              }}>
                {alert.message}
              </div>

              {alert.source && (
                <div style={{
                  fontSize: '0.75rem',
                  opacity: 0.7,
                  fontFamily: 'monospace'
                }}>
                  Source: {alert.source}
                </div>
              )}

              <div className="alert-timestamp">
                {alert.timestamp}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Quick Stats */}
      <div style={{
        padding: '1rem',
        borderTop: '1px solid rgba(0, 240, 255, 0.3)',
        background: 'rgba(0, 0, 0, 0.5)',
        marginTop: 'auto'
      }}>
        <div style={{ fontSize: '0.75rem', marginBottom: '0.5rem', opacity: 0.7 }}>
          QUICK STATS
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
            <span>Critical Alerts:</span>
            <span style={{ color: '#ef4444', fontWeight: 'bold' }}>
              {alerts.filter(a => a.severity === 'critical').length}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
            <span>High Priority:</span>
            <span style={{ color: '#f59e0b', fontWeight: 'bold' }}>
              {alerts.filter(a => a.severity === 'high').length}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
            <span>Last Hour:</span>
            <span style={{ color: '#00f0ff', fontWeight: 'bold' }}>
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

export default DefensiveSidebar;
