import { API_BASE_URL } from "@/config/api";
/**
import logger from '@/utils/logger';
 * useAdminMetrics - Admin Dashboard Metrics Hook
 *
 * Fetches and parses Prometheus metrics from API Gateway.
 * Polls every 5 seconds for real-time updates.
 *
 * @returns {Object} { metrics, loading } - Metrics object and loading state
 */

import { useState, useEffect } from "react";
import { parseMetrics } from "../utils/metricsParser";

const API_GATEWAY_METRICS_URL = `${API_BASE_URL}/metrics`;
const POLLING_INTERVAL = 5000; // 5s

export const useAdminMetrics = () => {
  const [metrics, setMetrics] = useState({
    totalRequests: 0,
    averageLatency: 0,
    errorRate: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch(API_GATEWAY_METRICS_URL);
        if (!response.ok) {
          throw new Error(`Network error: ${response.statusText}`);
        }
        const text = await response.text();
        const parsedData = parseMetrics(text);
        setMetrics(parsedData);
      } catch (error) {
        logger.error("Failed to fetch admin metrics:", error);
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchMetrics();

    // Poll metrics
    const interval = setInterval(fetchMetrics, POLLING_INTERVAL);

    return () => clearInterval(interval);
  }, []);

  return { metrics, loading };
};

export default useAdminMetrics;
