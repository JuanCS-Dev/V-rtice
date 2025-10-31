/**
 * useSystemMetrics - MVP System Metrics Hook
 *
 * Fetches and monitors real-time system metrics (CPU, memory, requests, errors).
 * Supports aggregated queries and system pulse visualization.
 *
 * Port: 8153
 * Created: 2025-10-31
 * Governed by: Constituição Vértice v3.0
 *
 * @param {Object} query - Query parameters (time_range_minutes, metric_name)
 * @param {Object} options - Hook options (pollingInterval, enabled)
 * @returns {Object} { metrics, pulse, isLoading, error, refetch }
 */

import { useState, useEffect, useCallback } from 'react';
import { mvpService } from '../../services/mvp/mvpService';
import logger from '../../utils/logger';

const DEFAULT_POLLING_INTERVAL = 15000; // 15s (frequent for real-time pulse)

export const useSystemMetrics = (query = {}, options = {}) => {
  const {
    pollingInterval = DEFAULT_POLLING_INTERVAL,
    enabled = true,
    includePulse = true, // Fetch live pulse data
  } = options;

  const [metrics, setMetrics] = useState(null);
  const [pulse, setPulse] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchMetrics = useCallback(async () => {
    if (!enabled) return;

    try {
      setError(null);

      // Fetch aggregated metrics
      const metricsResponse = await mvpService.queryMetrics({
        time_range_minutes: query.time_range_minutes || 60,
        ...query,
      });
      setMetrics(metricsResponse);

      // Fetch live pulse if enabled
      if (includePulse) {
        const pulseResponse = await mvpService.getSystemPulse();
        setPulse(pulseResponse);
      }

      setIsLoading(false);
      logger.debug('[useSystemMetrics] Metrics updated');
    } catch (err) {
      logger.error('[useSystemMetrics] Failed to fetch metrics:', err);
      setError(err.message);
      setIsLoading(false);
    }
  }, [enabled, includePulse, JSON.stringify(query)]);

  useEffect(() => {
    if (!enabled) return;

    // Initial fetch
    fetchMetrics();

    // Periodic polling
    const interval = setInterval(fetchMetrics, pollingInterval);

    return () => clearInterval(interval);
  }, [enabled, pollingInterval, fetchMetrics]);

  return {
    metrics,
    pulse,
    cpuUsage: metrics?.cpu_usage || null,
    memoryUsage: metrics?.memory_usage || null,
    requestRate: metrics?.request_rate || null,
    errorRate: metrics?.error_rate || null,
    isLoading,
    error,
    refetch: fetchMetrics,
  };
};

export default useSystemMetrics;
