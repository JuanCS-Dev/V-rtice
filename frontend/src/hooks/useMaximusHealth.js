/**
 * useMaximusHealth - MAXIMUS AI Health Check Hook
 *
 * Polls MAXIMUS core service health endpoint every 30s
 * Updates AI status (core, oraculo, eureka) based on health response
 *
 * @returns {Object} { aiStatus, setAiStatus } - AI service status object
 */

import { useState, useEffect } from 'react';
import logger from '@/utils/logger';

const MAXIMUS_CORE_URL = 'http://localhost:8099';
const HEALTH_CHECK_INTERVAL = 30000; // 30s

export const useMaximusHealth = () => {
  const [aiStatus, setAiStatus] = useState({
    oraculo: { status: 'idle', lastRun: null, suggestions: 0 },
    eureka: { status: 'idle', lastAnalysis: null, threatsDetected: 0 },
    core: { status: 'online', uptime: '99.9%', reasoning: 'ready' }
  });

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${MAXIMUS_CORE_URL}/health`);
        if (response.ok) {
          const data = await response.json();
          setAiStatus(prev => ({
            ...prev,
            core: {
              status: data.status === 'healthy' ? 'online' : 'degraded',
              uptime: data.uptime_seconds
                ? `${(data.uptime_seconds / 3600).toFixed(1)}h`
                : prev.core.uptime,
              reasoning: data.services?.maximus_core === 'external' ? 'ready' : 'offline'
            }
          }));
        }
      } catch (error) {
        logger.error('MAXIMUS health check failed:', error);
        setAiStatus(prev => ({
          ...prev,
          core: { ...prev.core, status: 'offline' }
        }));
      }
    };

    // Initial check
    checkHealth();

    // Periodic checks
    const interval = setInterval(checkHealth, HEALTH_CHECK_INTERVAL);

    return () => clearInterval(interval);
  }, []);

  return { aiStatus, setAiStatus };
};

export default useMaximusHealth;
