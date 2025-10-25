/**
 * useOffensiveMetrics Hook
 * Fetches real offensive operation metrics from backend services
 *
 * React Query powered for:
 * - Automatic caching
 * - Background refetching
 * - Retry with exponential backoff
 * - Optimistic updates
 *
 * INTEGRATION: Uses ServiceEndpoints for environment-aware configuration
 *
 * TODO: Offensive services not yet exposed publicly
 * Currently returns mock data until services are deployed with proper ports
 *
 * When ready, uncomment sections below and configure in .env:
 * - Network Recon Service (VITE_OFFENSIVE_NETWORK_RECON_URL)
 * - Vuln Intel Service (VITE_OFFENSIVE_VULN_INTEL_URL)
 * - Web Attack Service (VITE_OFFENSIVE_WEB_ATTACK_URL)
 * - C2 Orchestration Service (VITE_OFFENSIVE_C2_URL)
 * - BAS Service (VITE_OFFENSIVE_BAS_URL)
 * - Offensive Gateway (VITE_OFFENSIVE_GATEWAY_URL)
 */

import { useQuery } from '@tanstack/react-query';
import { ServiceEndpoints } from '@/config/endpoints';
import { queryKeys } from '../../../../config/queryClient';
import logger from '@/utils/logger';

const fetchOffensiveMetrics = async () => {
  // TODO: Uncomment when offensive services are exposed
  /*
  const results = await Promise.allSettled([
    // Network Recon active scans
    fetch(`${ServiceEndpoints.offensive.networkRecon}/api/scans/active`)
      .then(res => res.ok ? res.json() : { scans: [] })
      .catch(() => ({ scans: [] })),

    // Vuln Intel findings
    fetch(`${ServiceEndpoints.offensive.vulnIntel}/api/vulnerabilities/count`)
      .then(res => res.ok ? res.json() : { count: 0 })
      .catch(() => ({ count: 0 })),

    // Web Attack targets
    fetch(`${ServiceEndpoints.offensive.webAttack}/api/targets`)
      .then(res => res.ok ? res.json() : { targets: [] })
      .catch(() => ({ targets: [] })),

    // C2 Sessions
    fetch(`${ServiceEndpoints.offensive.c2Orchestration}/api/sessions/active`)
      .then(res => res.ok ? res.json() : { sessions: [] })
      .catch(() => ({ sessions: [] }))
  ]);

  const [reconData, vulnData, targetData, c2Data] = results.map(r =>
    r.status === 'fulfilled' ? r.value : null
  );

  return {
    activeScans: reconData?.scans?.length || 0,
    exploitsFound: vulnData?.count || 0,
    targets: targetData?.targets?.length || 0,
    c2Sessions: c2Data?.sessions?.length || 0
  };
  */

  // Temporary: Return zero metrics until services are exposed
  logger.warn('Offensive services not yet exposed - returning zero metrics');
  return {
    activeScans: 0,
    exploitsFound: 0,
    targets: 0,
    c2Sessions: 0
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
