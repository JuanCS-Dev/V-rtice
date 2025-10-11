/**
 * useOSINTAlerts - OSINT Alert Stream Hook
 *
 * Simulates real-time OSINT alerts (leaks, breaches, social activity).
 * In production, this would be replaced with real-time WebSocket.
 *
 * @param {Function} t - i18n translation function
 * @returns {Array} osintAlerts - Array of OSINT alerts (max 30)
 */

import { useState, useEffect } from 'react';

const ALERT_INTERVAL = 4000; // 4s
const ALERT_PROBABILITY = 0.85; // 85% threshold
const MAX_ALERTS = 30;

export const useOSINTAlerts = (t) => {
  const [osintAlerts, setOsintAlerts] = useState([]);

  useEffect(() => {
    const alertTypes = [
      {
        type: 'LEAK',
        message: t('dashboard.osint.alerts.leak'),
        severity: 'critical',
        source: 'Dark Web Monitor'
      },
      {
        type: 'SOCIAL',
        message: t('dashboard.osint.alerts.social'),
        severity: 'high',
        source: 'Social Scraper'
      },
      {
        type: 'BREACH',
        message: t('dashboard.osint.alerts.breach'),
        severity: 'critical',
        source: 'Breach Analyzer'
      },
      {
        type: 'PATTERN',
        message: t('dashboard.osint.alerts.pattern'),
        severity: 'medium',
        source: 'Maximus AI'
      },
      {
        type: 'IDENTITY',
        message: t('dashboard.osint.alerts.identity'),
        severity: 'info',
        source: 'Username Hunter'
      }
    ];

    const alertTimer = setInterval(() => {
      if (Math.random() > ALERT_PROBABILITY) {
        const randomAlert = alertTypes[Math.floor(Math.random() * alertTypes.length)];
        const newAlert = {
          id: Date.now(),
          ...randomAlert,
          timestamp: new Date().toLocaleTimeString('pt-BR'),
          target: `Target_${Math.floor(Math.random() * 999)}`
        };
        setOsintAlerts(prev => [newAlert, ...prev.slice(0, MAX_ALERTS - 1)]);
      }
    }, ALERT_INTERVAL);

    return () => clearInterval(alertTimer);
  }, [t]);

  return osintAlerts;
};

export default useOSINTAlerts;
