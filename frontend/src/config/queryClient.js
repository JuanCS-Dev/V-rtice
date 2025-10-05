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
 */

import { QueryClient } from '@tanstack/react-query';

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
          console.error('[React Query] Error:', error);
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
          console.error('[React Query] Mutation Error:', error);
        }
      }
    }
  }
});

// Query keys factory (for consistency)
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
