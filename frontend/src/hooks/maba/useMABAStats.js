/**
 * useMABAStats - MABA Statistics Hook
 *
 * Fetches MABA service statistics:
 * - Cognitive map metrics (pages learned, elements, domains)
 * - Browser session metrics (active sessions, navigations)
 * - Service uptime
 *
 * Port: 8155
 * Created: 2025-10-31
 * Governed by: Constituição Vértice v3.0
 *
 * @param {Object} options - Hook options (pollingInterval, enabled)
 * @returns {Object} { stats, isLoading, error, refetch }
 */

import { useState, useEffect, useCallback } from 'react';
import { mabaService } from '../../services/maba/mabaService';
import logger from '../../utils/logger';

const DEFAULT_POLLING_INTERVAL = 30000; // 30s

export const useMABAStats = (options = {}) => {
  const {
    pollingInterval = DEFAULT_POLLING_INTERVAL,
    enabled = true,
  } = options;

  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStats = useCallback(async () => {
    if (!enabled) return;

    try {
      setError(null);
      const response = await mabaService.getStats();
      setStats(response);
      setIsLoading(false);
      logger.debug('[useMABAStats] Stats updated:', response);
    } catch (err) {
      logger.error('[useMABAStats] Failed to fetch stats:', err);
      setError(err.message);
      setIsLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    if (!enabled) return;

    // Initial fetch
    fetchStats();

    // Periodic polling
    const interval = setInterval(fetchStats, pollingInterval);

    return () => clearInterval(interval);
  }, [enabled, pollingInterval, fetchStats]);

  return {
    stats,
    cognitiveMap: stats?.cognitive_map || null,
    browser: stats?.browser || null,
    uptime: stats?.uptime_seconds || 0,
    isLoading,
    error,
    refetch: fetchStats,
  };
};

export default useMABAStats;
