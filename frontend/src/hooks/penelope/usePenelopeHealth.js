/**
 * usePenelopeHealth - PENELOPE Health Check Hook
 *
 * Polls PENELOPE service health endpoint every 30s.
 * Monitors Sabbath mode status (Sunday read-only mode).
 *
 * Port: 8154
 * Created: 2025-10-31
 * Governed by: Constituição Vértice v3.0
 *
 * @returns {Object} { health, isLoading, error, isSabbath }
 */

import { useState, useEffect } from 'react';
import { penelopeService } from '../../services/penelope/penelopeService';
import logger from '../../utils/logger';

const HEALTH_CHECK_INTERVAL = 30000; // 30s

export const usePenelopeHealth = () => {
  const [health, setHealth] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        setError(null);
        const response = await penelopeService.getHealth();
        setHealth(response);
        setIsLoading(false);
        logger.debug('[usePenelopeHealth] Health check successful:', response);
      } catch (err) {
        logger.error('[usePenelopeHealth] Health check failed:', err);
        setError(err.message);
        setHealth(null);
        setIsLoading(false);
      }
    };

    // Initial check
    checkHealth();

    // Periodic checks
    const interval = setInterval(checkHealth, HEALTH_CHECK_INTERVAL);

    return () => clearInterval(interval);
  }, []);

  // Sabbath mode (Sunday = read-only)
  const isSabbath = health?.sabbath_mode || new Date().getDay() === 0;

  return {
    health,
    isLoading,
    error,
    isSabbath,
    isHealthy: health?.status === 'healthy',
    uptime: health?.uptime_seconds || 0,
  };
};

export default usePenelopeHealth;
