/**
 * useCockpitMetrics - Real-time Cockpit Metrics Hook
 * 
 * Fetches aggregated metrics from Narrative Filter + Verdict Engine
 * NO MOCKS - Real API calls
 * 
 * @version 1.0.0
 */

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const NARRATIVE_FILTER_API = import.meta.env.VITE_NARRATIVE_FILTER_API || 'http://localhost:8090';
const VERDICT_ENGINE_API = import.meta.env.VITE_VERDICT_ENGINE_API || 'http://localhost:8091';
const POLL_INTERVAL = 5000; // 5 seconds

export const useCockpitMetrics = () => {
  const [metrics, setMetrics] = useState({
    totalAgents: 0,
    activeAgents: 0,
    totalVerdicts: 0,
    criticalVerdicts: 0,
    alliancesDetected: 0,
    deceptionMarkers: 0,
    avgProcessingLatency: 0,
    systemHealth: 'UNKNOWN'
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchMetrics = useCallback(async () => {
    try {
      const [narrativeStats, verdictStats] = await Promise.all([
        axios.get(`${NARRATIVE_FILTER_API}/stats`, { timeout: 5000 }),
        axios.get(`${VERDICT_ENGINE_API}/stats`, { timeout: 5000 })
      ]);

      setMetrics({
        totalAgents: narrativeStats.data.total_agents || 0,
        activeAgents: narrativeStats.data.active_agents || 0,
        totalVerdicts: verdictStats.data.total_verdicts || 0,
        criticalVerdicts: verdictStats.data.critical_count || 0,
        alliancesDetected: narrativeStats.data.alliances_count || 0,
        deceptionMarkers: narrativeStats.data.deception_count || 0,
        avgProcessingLatency: narrativeStats.data.avg_latency_ms || 0,
        systemHealth: verdictStats.data.health_status || 'OPERATIONAL'
      });

      setError(null);
    } catch (err) {
      console.error('[CockpitMetrics] Failed to fetch:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();

    const interval = setInterval(fetchMetrics, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchMetrics]);

  return { metrics, loading, error, refresh: fetchMetrics };
};
