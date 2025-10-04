/**
 * useSystemAlerts - System Alerts Simulation Hook
 *
 * Generates random system alerts for AdminDashboard.
 * In production, this would receive alerts via WebSocket.
 *
 * @param {Function} t - i18n translation function
 * @returns {Array} systemAlerts - Array of system alerts (max 10)
 */

import { useState, useEffect } from 'react';

const ALERT_INTERVAL = 15000; // 15s
const ALERT_PROBABILITY = 0.9; // 90% threshold
const MAX_ALERTS = 10;

export const useSystemAlerts = (t) => {
  const [systemAlerts, setSystemAlerts] = useState([]);

  useEffect(() => {
    const alertTypes = [
      { type: 'INFO', message: t('dashboard.admin.alerts.backup'), severity: 'info' },
      { type: 'WARNING', message: t('dashboard.admin.alerts.cpu'), severity: 'medium' },
      { type: 'ERROR', message: t('dashboard.admin.alerts.apiError'), severity: 'high' },
      { type: 'SECURITY', message: t('dashboard.admin.alerts.security'), severity: 'critical' }
    ];

    const alertTimer = setInterval(() => {
      if (Math.random() > ALERT_PROBABILITY) {
        const randomAlert = alertTypes[Math.floor(Math.random() * alertTypes.length)];
        const newAlert = {
          id: Date.now(),
          ...randomAlert,
          timestamp: new Date().toLocaleTimeString()
        };
        setSystemAlerts(prev => [newAlert, ...prev.slice(0, MAX_ALERTS - 1)]);
      }
    }, ALERT_INTERVAL);

    return () => clearInterval(alertTimer);
  }, [t]);

  return systemAlerts;
};

export default useSystemAlerts;
