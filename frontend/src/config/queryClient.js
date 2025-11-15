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
 *
 * Boris Cherny Standard - GAP #35 FIX: Standardized polling intervals
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
      }
    }
  }
});

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
