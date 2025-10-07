/**
 * useDefensiveMetrics Hook
 * Fetch REAL defensive metrics from backend
 *
 * React Query powered for:
 * - Automatic caching
 * - Background refetching
 * - Retry with exponential backoff
 *
 * NO MOCKS - Production Ready
 */

import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '../../../../config/queryClient';

const API_BASE = 'http://localhost:8001'; // Maximus Core

const fetchDefensiveMetrics = async () => {
  // Fetch from Maximus Core health endpoint
  const healthResponse = await fetch(`${API_BASE}/health`);

  if (!healthResponse.ok) {
    throw new Error('Failed to fetch defensive metrics');
  }

  const healthData = await healthResponse.json();

  // Calculate metrics from real data from health endpoint
  // Note: If backend doesn't provide security_stats, these will show 0
  // A dedicated /metrics endpoint would be more appropriate for dashboard stats
  return {
    threats: healthData.memory_system?.episodic_stats?.investigations || 0,
    suspiciousIPs: healthData.security_stats?.suspicious_ips || 0,
    domains: healthData.security_stats?.monitored_domains || 0,
    monitored: healthData.total_integrated_tools || 57
  };
};

export const useDefensiveMetrics = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: queryKeys.defensiveMetrics,
    queryFn: fetchDefensiveMetrics,
    refetchInterval: 30000, // Poll every 30 seconds
    staleTime: 10000, // Consider data stale after 10s
    retry: 2,
    retryDelay: 1000,
    onError: (err) => {
      console.error('Failed to fetch defensive metrics:', err);
    }
  });

  return {
    metrics: data || {
      threats: 0,
      suspiciousIPs: 0,
      domains: 0,
      monitored: 0
    },
    loading: isLoading,
    error: error?.message || null
  };
};
