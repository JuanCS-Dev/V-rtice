/**
 * useAnomalies - MVP Anomaly Detection Hook
 *
 * Fetches and monitors detected anomalies in system metrics.
 * Supports filtering by severity and time range.
 *
 * Port: 8153
 * Created: 2025-10-31
 * Governed by: Constituição Vértice v3.0
 *
 * @param {Object} filters - Query filters (severity, time_range)
 * @param {Object} options - Hook options (pollingInterval, enabled)
 * @returns {Object} { anomalies, isLoading, error, timeline, refetch }
 */

import { useState, useEffect, useCallback } from 'react';
import { mvpService } from '../../services/mvp/mvpService';
import logger from '../../utils/logger';

const DEFAULT_POLLING_INTERVAL = 30000; // 30s

export const useAnomalies = (filters = {}, options = {}) => {
  const {
    pollingInterval = DEFAULT_POLLING_INTERVAL,
    enabled = true,
  } = options;

  const [anomalies, setAnomalies] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAnomalies = useCallback(async () => {
    if (!enabled) return;

    try {
      setError(null);
      const response = await mvpService.detectAnomalies(filters);
      setAnomalies(response);
      setIsLoading(false);
      logger.debug(`[useAnomalies] Detected ${response.length} anomalies`);
    } catch (err) {
      logger.error('[useAnomalies] Failed to fetch anomalies:', err);
      setError(err.message);
      setIsLoading(false);
    }
  }, [enabled, JSON.stringify(filters)]);

  // Fetch timeline for heatmap (separate from anomalies list)
  const fetchTimeline = useCallback(async (days = 30) => {
    try {
      const response = await mvpService.getAnomalyTimeline(days);
      setTimeline(response);
      logger.debug('[useAnomalies] Timeline fetched');
    } catch (err) {
      logger.error('[useAnomalies] Failed to fetch timeline:', err);
    }
  }, []);

  useEffect(() => {
    if (!enabled) return;

    // Initial fetch
    fetchAnomalies();
    fetchTimeline();

    // Periodic polling
    const interval = setInterval(fetchAnomalies, pollingInterval);

    return () => clearInterval(interval);
  }, [enabled, pollingInterval, fetchAnomalies, fetchTimeline]);

  // Statistics
  const stats = anomalies.length > 0 ? {
    total: anomalies.length,
    bySeverity: {
      critical: anomalies.filter(a => a.severity === 'critical').length,
      high: anomalies.filter(a => a.severity === 'high').length,
      medium: anomalies.filter(a => a.severity === 'medium').length,
      low: anomalies.filter(a => a.severity === 'low').length,
    },
    recentCount: anomalies.filter(a => {
      const detectedAt = new Date(a.detected_at);
      const hourAgo = new Date(Date.now() - 60 * 60 * 1000);
      return detectedAt > hourAgo;
    }).length,
  } : null;

  return {
    anomalies,
    timeline,
    isLoading,
    error,
    stats,
    refetch: fetchAnomalies,
    refetchTimeline: fetchTimeline,
  };
};

export default useAnomalies;
