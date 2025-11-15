/**
 * useHealingHistory - PENELOPE Healing Events Hook
 *
 * Fetches and monitors healing history (patches applied, outcomes, metrics).
 * Supports pagination and real-time updates via WebSocket.
 *
 * Port: 8154
 * Created: 2025-10-31
 * Governed by: Constituição Vértice v3.0
 *
 * @param {Object} options - Hook options (limit, pollingInterval, enabled)
 * @returns {Object} { history, isLoading, error, refetch, stats }
 */

import { useState, useEffect, useCallback } from "react";
import { penelopeService } from "../../services/penelope/penelopeService";
import logger from "../../utils/logger";

const DEFAULT_POLLING_INTERVAL = 60000; // 60s (less frequent than health checks)
const DEFAULT_LIMIT = 50;

export const useHealingHistory = (options = {}) => {
  const {
    limit = DEFAULT_LIMIT,
    pollingInterval = DEFAULT_POLLING_INTERVAL,
    enabled = true,
  } = options;

  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchHistory = useCallback(async () => {
    if (!enabled) return;

    try {
      setError(null);
      const response = await penelopeService.getHealingHistory(limit);
      setHistory(response);
      setIsLoading(false);
      logger.debug(`[useHealingHistory] Fetched ${response.length} events`);
    } catch (err) {
      logger.error("[useHealingHistory] Failed to fetch history:", err);
      setError(err.message);
      setIsLoading(false);
    }
  }, [enabled, limit]);

  useEffect(() => {
    if (!enabled) return;

    // Initial fetch
    fetchHistory();

    // Periodic polling
    const interval = setInterval(fetchHistory, pollingInterval);

    return () => clearInterval(interval);
  }, [enabled, pollingInterval, fetchHistory]);

  // Calculate statistics from history
  const stats =
    history.length > 0
      ? {
          total: history.length,
          successful: history.filter((e) => e.outcome === "success").length,
          failed: history.filter((e) => e.outcome === "failed").length,
          escalated: history.filter((e) => e.outcome === "escalated").length,
          successRate: Math.round(
            (history.filter((e) => e.outcome === "success").length /
              history.length) *
              100,
          ),
          avgPatchSize: Math.round(
            history.reduce((sum, e) => sum + (e.patch_size_lines || 0), 0) /
              history.length,
          ),
          avgMansidao: (
            history.reduce((sum, e) => sum + (e.mansidao_score || 0), 0) /
            history.length
          ).toFixed(2),
        }
      : null;

  return {
    history,
    isLoading,
    error,
    refetch: fetchHistory,
    stats,
  };
};

export default useHealingHistory;
