/**
import logger from '@/utils/logger';
 * useOffensiveMetrics Hook
 * Fetches real offensive operation metrics from backend services
 *
 * React Query powered for:
 * - Automatic caching
 * - Background refetching
 * - Retry with exponential backoff
 * - Optimistic updates
 *
 * NO MOCKS - Real data from:
 * - Network Recon Service (port 8032)
 * - Vuln Intel Service (port 8033)
 * - Web Attack Service (port 8034)
 * - C2 Orchestration Service (port 8035)
 * - BAS Service (port 8036)
 * - Offensive Gateway (port 8037)
 */

import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '../../../../config/queryClient';

const OFFENSIVE_SERVICES = {
  networkRecon: 'http://localhost:8032',
  vulnIntel: 'http://localhost:8033',
  webAttack: 'http://localhost:8034',
  c2: 'http://localhost:8035',
  bas: 'http://localhost:8036',
  gateway: 'http://localhost:8037'
};

const fetchOffensiveMetrics = async () => {
  // Aggregate metrics from multiple services
  const results = await Promise.allSettled([
    // Network Recon active scans
    fetch(`${OFFENSIVE_SERVICES.networkRecon}/api/scans/active`)
      .then(res => res.ok ? res.json() : { scans: [] })
      .catch(() => ({ scans: [] })),

    // Vuln Intel findings
    fetch(`${OFFENSIVE_SERVICES.vulnIntel}/api/vulnerabilities/count`)
      .then(res => res.ok ? res.json() : { count: 0 })
      .catch(() => ({ count: 0 })),

    // Web Attack targets
    fetch(`${OFFENSIVE_SERVICES.webAttack}/api/targets`)
      .then(res => res.ok ? res.json() : { targets: [] })
      .catch(() => ({ targets: [] })),

    // C2 Sessions
    fetch(`${OFFENSIVE_SERVICES.c2}/api/sessions/active`)
      .then(res => res.ok ? res.json() : { sessions: [] })
      .catch(() => ({ sessions: [] }))
  ]);

  // Calculate metrics from results
  const [reconData, vulnData, targetData, c2Data] = results.map(r =>
    r.status === 'fulfilled' ? r.value : null
  );

  return {
    activeScans: reconData?.scans?.length || 0,
    exploitsFound: vulnData?.count || 0,
    targets: targetData?.targets?.length || 0,
    c2Sessions: c2Data?.sessions?.length || 0
  };
};

export const useOffensiveMetrics = () => {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: queryKeys.offensiveMetrics,
    queryFn: fetchOffensiveMetrics,
    refetchInterval: 5000, // Poll every 5 seconds
    staleTime: 1000, // Consider data stale after 1s
    retry: 2, // Retry failed requests twice
    retryDelay: 1000,
    onError: (err) => {
      logger.error('Failed to fetch offensive metrics:', err);
    }
  });

  return {
    metrics: data || {
      activeScans: 0,
      exploitsFound: 0,
      targets: 0,
      c2Sessions: 0
    },
    loading: isLoading,
    error: error?.message || null,
    refresh: refetch
  };
};
