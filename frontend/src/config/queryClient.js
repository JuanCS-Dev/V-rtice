/**
 * React Query Configuration
 *
 * Centralized configuration for API caching and data fetching
 *
 * Features:
 * - Automatic retry with exponential backoff
 * - Stale-while-revalidate caching
 * - Optimistic updates support
 * - Background refetching
 * - Error handling
 * - Mutation persistence for offline support (GAP #71 FIX)
 * - Prefetching support (GAP #72 FIX)
 *
 * Boris Cherny Standard - GAP #35, #71, #72 FIXES
 */

import { QueryClient } from '@tanstack/react-query';
import logger from '@/utils/logger';

// ============================================================================
// POLLING INTERVALS - Boris Cherny Standard (GAP #35 FIX)
// ============================================================================
/**
 * Standardized polling intervals for consistent data freshness
 * Use these constants instead of hardcoded values
 */
export const POLLING_INTERVALS = {
  REAL_TIME: 1000,      // 1s - Critical real-time data (active scans, live metrics)
  FREQUENT: 5000,       // 5s - Frequently changing data (alerts, scan status)
  NORMAL: 30000,        // 30s - Normal updates (metrics, health checks)
  INFREQUENT: 60000,    // 60s - Slow changing data (HITL reviews, static configs)
  MANUAL: false,        // No automatic polling - manual refresh only
};

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Caching strategy
      staleTime: 5 * 60 * 1000, // 5 minutes - data considered fresh
      cacheTime: 10 * 60 * 1000, // 10 minutes - cache retention

      // Refetching strategy
      refetchOnWindowFocus: true, // Refetch when user returns to tab
      refetchOnReconnect: true, // Refetch when connection restored
      refetchInterval: false, // No automatic polling by default

      // Retry strategy (exponential backoff)
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),

      // Error handling
      onError: (error) => {
        if (process.env.NODE_ENV === 'development') {
          logger.error('[React Query] Error:', error);
        }
      },

      // Suspense support
      suspense: false,

      // Keep previous data while fetching new data
      keepPreviousData: true
    },

    mutations: {
      // Retry strategy for mutations
      retry: 1,
      retryDelay: 1000,

      // Error handling
      onError: (error) => {
        if (process.env.NODE_ENV === 'development') {
          logger.error('[React Query] Mutation Error:', error);
        }
      },

      // GAP #71 FIX: Enable mutation persistence for offline support
      // Mutations will be persisted and retried when connection is restored
      // Note: Requires persistence configuration in App setup (see below)
      gcTime: 1000 * 60 * 60 * 24, // 24 hours - keep failed mutations for retry
      networkMode: 'offlineFirst' // Queue mutations when offline
    }
  }
});

// ============================================================================
// PREFETCHING UTILITIES - Boris Cherny Standard (GAP #72 FIX)
// ============================================================================
/**
 * Prefetch data on route/tab hover for instant navigation
 *
 * Usage:
 * <Link
 *   to="/dashboard"
 *   onMouseEnter={() => prefetchQuery(['dashboard', 'metrics'], fetchMetrics)}
 * >
 *   Dashboard
 * </Link>
 */
export const prefetchQuery = async (queryKey, queryFn, options = {}) => {
  try {
    await queryClient.prefetchQuery({
      queryKey,
      queryFn,
      staleTime: 5 * 60 * 1000, // 5 minutes
      ...options
    });
    logger.debug('[React Query] Prefetched:', queryKey);
  } catch (error) {
    logger.error('[React Query] Prefetch failed:', queryKey, error);
  }
};

/**
 * Prefetch multiple queries at once
 *
 * Usage:
 * onMouseEnter={() => prefetchQueries([
 *   { key: ['metrics'], fn: fetchMetrics },
 *   { key: ['alerts'], fn: fetchAlerts }
 * ])}
 */
export const prefetchQueries = async (queries) => {
  await Promise.all(
    queries.map(({ key, fn, options }) =>
      prefetchQuery(key, fn, options)
    )
  );
};

/**
 * Invalidate and refetch specific queries
 * Useful after mutations or WebSocket updates
 */
export const invalidateQueries = async (queryKey) => {
  await queryClient.invalidateQueries({ queryKey });
  logger.debug('[React Query] Invalidated:', queryKey);
};

// ============================================================================
// QUERY KEYS - Boris Cherny Standard (GAP #34 FIX)
// ============================================================================
/**
 * DEPRECATED: Use centralized queryKeys from '@/config/queryKeys' instead
 * This export is kept for backward compatibility only
 *
 * @deprecated Import from '@/config/queryKeys' instead
 */
export const queryKeys = {
  // Defensive
  defensiveMetrics: ['defensive', 'metrics'],
  defensiveAlerts: ['defensive', 'alerts'],
  defensiveHealth: ['defensive', 'health'],

  // Offensive
  offensiveMetrics: ['offensive', 'metrics'],
  offensiveExecutions: ['offensive', 'executions'],
  offensiveScans: (status) => ['offensive', 'scans', status],

  // Purple Team
  purpleCorrelations: ['purple', 'correlations'],
  purpleGaps: ['purple', 'gaps'],

  // Maximus AI
  maximusHealth: ['maximus', 'health'],
  maximusChat: (sessionId) => ['maximus', 'chat', sessionId],
  maximusTools: ['maximus', 'tools'],

  // OSINT
  osintDomain: (domain) => ['osint', 'domain', domain],
  osintIP: (ip) => ['osint', 'ip', ip],

  // Services
  serviceHealth: (serviceId) => ['service', 'health', serviceId],
  serviceMetrics: (serviceId) => ['service', 'metrics', serviceId]
};

// Export centralized query keys (GAP #34 FIX)
export { queryKeys as centralizedQueryKeys } from './queryKeys';
