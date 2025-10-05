/**
 * Defensive Dashboard Footer
 * System Status & Information
 */

import React from 'react';

const DefensiveFooter = ({ alertsCount, metrics }) => {
  return (
    <footer className="dashboard-footer">
      <div className="footer-status">
        <div className="footer-status-item">
          <span className="status-dot"></span>
          CONNECTION: SECURE
        </div>
        <div className="footer-status-item">
          <span className="status-dot"></span>
          THREAT INTEL: ACTIVE
        </div>
        <div className="footer-status-item">
          <span className="status-dot"></span>
          SIEM: ONLINE
        </div>
        <div className="footer-status-item">
          ALERTS: {alertsCount}
        </div>
        <div className="footer-status-item">
          MONITORED: {metrics?.monitored || 0}
        </div>
      </div>

      <div style={{ opacity: 0.7 }}>
        DEFENSIVE OPERATIONS | PROJETO VÉRTICE v2.0 | CLASSIFICAÇÃO: CONFIDENCIAL
      </div>
    </footer>
  );
};

export default DefensiveFooter;
