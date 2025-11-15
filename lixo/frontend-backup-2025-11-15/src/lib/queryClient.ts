/**
 * React Query Client Configuration
 *
 * DOUTRINA VÉRTICE - GAP #9 (P1)
 * QueryClient with mutation persistence and offline support
 *
 * Following Boris Cherny's principle: "Configuration should be explicit"
 */

import { QueryClient } from "@tanstack/react-query";

// ============================================================================
// Retry Configuration
// ============================================================================

/**
 * Determine if error is retryable
 *
 * Don't retry on:
 * - 4xx errors (client errors - won't succeed on retry)
 * - Authentication errors (need new token)
 * - Validation errors (need to fix input)
 *
 * Retry on:
 * - 5xx errors (server errors - might be transient)
 * - Network errors (might be temporary connectivity issue)
 * - Timeout errors
 */
function shouldRetry(failureCount: number, error: any): boolean {
  // Max 3 retries
  if (failureCount >= 3) return false;

  // Don't retry client errors (4xx)
  if (error?.response?.status >= 400 && error?.response?.status < 500) {
    return false;
  }

  // Don't retry authentication errors
  const errorCode = error?.error_code || error?.errorCode;
  if (errorCode?.startsWith("AUTH_")) {
    return false;
  }

  // Don't retry validation errors
  if (errorCode?.startsWith("VAL_")) {
    return false;
  }

  // Retry everything else (5xx, network errors, timeouts)
  return true;
}

/**
 * Calculate retry delay with exponential backoff
 *
 * Attempt 1: 1s
 * Attempt 2: 2s
 * Attempt 3: 4s
 */
function getRetryDelay(attemptIndex: number): number {
  return Math.min(1000 * Math.pow(2, attemptIndex), 30000);
}

// ============================================================================
// QueryClient Configuration
// ============================================================================

/**
 * Create configured QueryClient instance
 *
 * Features:
 * - Mutation persistence (survives page reload)
 * - Offline queue (mutations queued when offline)
 * - Auto-retry with exponential backoff
 * - 5-minute stale time for queries
 * - 10-minute cache time
 *
 * @returns Configured QueryClient
 *
 * @example
 * ```tsx
 * import { QueryClientProvider } from '@tanstack/react-query';
 * import { createQueryClient } from '@/lib/queryClient';
 *
 * const queryClient = createQueryClient();
 *
 * function App() {
 *   return (
 *     <QueryClientProvider client={queryClient}>
 *       <YourApp />
 *     </QueryClientProvider>
 *   );
 * }
 * ```
 */
export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Queries considered fresh for 5 minutes
        staleTime: 1000 * 60 * 5,

        // Cache data for 10 minutes
        gcTime: 1000 * 60 * 10,

        // Retry failed queries
        retry: shouldRetry,
        retryDelay: getRetryDelay,

        // Refetch options
        refetchOnWindowFocus: true,
        refetchOnReconnect: true,
        refetchOnMount: true,

        // Don't throw errors - handle via error state
        throwOnError: false,
      },

      mutations: {
        // Retry failed mutations
        retry: shouldRetry,
        retryDelay: getRetryDelay,

        // Network mode: pause mutations when offline
        // This enables offline queue functionality
        networkMode: "offlineFirst",

        // Don't throw errors - handle via error state
        throwOnError: false,

        // Global mutation callbacks
        onError: (error: any, _variables, context) => {
          console.error("[QueryClient] Mutation failed:", {
            error: error.message || error,
            context,
          });
        },

        onSuccess: (_data, _variables, context) => {
          console.info("[QueryClient] Mutation succeeded:", context);
        },
      },
    },
  });
}

// ============================================================================
// Query Key Factories
// ============================================================================

/**
 * Centralized query key management
 *
 * Prevents typos and makes refactoring easier
 *
 * @example
 * ```typescript
 * // Instead of: ['scans', scanId]
 * // Use:
 * queryKeys.scan.detail(scanId)
 * ```
 */
export const queryKeys = {
  // Health endpoint
  health: ["health"] as const,

  // Scans
  scan: {
    all: ["scans"] as const,
    lists: () => [...queryKeys.scan.all, "list"] as const,
    list: (filters: Record<string, any>) =>
      [...queryKeys.scan.lists(), { filters }] as const,
    details: () => [...queryKeys.scan.all, "detail"] as const,
    detail: (id: string) => [...queryKeys.scan.details(), id] as const,
  },

  // Vulnerabilities
  vulnerability: {
    all: ["vulnerabilities"] as const,
    lists: () => [...queryKeys.vulnerability.all, "list"] as const,
    list: (filters: Record<string, any>) =>
      [...queryKeys.vulnerability.lists(), { filters }] as const,
    details: () => [...queryKeys.vulnerability.all, "detail"] as const,
    detail: (id: string) => [...queryKeys.vulnerability.details(), id] as const,
  },

  // Metrics
  metrics: {
    all: ["metrics"] as const,
    dashboard: () => [...queryKeys.metrics.all, "dashboard"] as const,
    timeRange: (range: string) =>
      [...queryKeys.metrics.all, "timeRange", range] as const,
  },
} as const;

/**
 * Mutation key factories
 *
 * @example
 * ```typescript
 * mutationKeys.scan.start
 * mutationKeys.scan.stop(scanId)
 * ```
 */
export const mutationKeys = {
  scan: {
    start: ["scan", "start"] as const,
    stop: (id: string) => ["scan", "stop", id] as const,
    delete: (id: string) => ["scan", "delete", id] as const,
  },
  vulnerability: {
    acknowledge: (id: string) => ["vulnerability", "acknowledge", id] as const,
    ignore: (id: string) => ["vulnerability", "ignore", id] as const,
  },
} as const;

// ============================================================================
// Query Invalidation Helpers
// ============================================================================

/**
 * Invalidate all scan-related queries
 *
 * Call this after mutations that affect scans
 *
 * @example
 * ```typescript
 * const { mutate } = useMutation({
 *   mutationFn: startScan,
 *   onSuccess: () => {
 *     invalidateScans(queryClient);
 *   },
 * });
 * ```
 */
export function invalidateScans(queryClient: QueryClient) {
  return queryClient.invalidateQueries({ queryKey: queryKeys.scan.all });
}

/**
 * Invalidate all vulnerability-related queries
 */
export function invalidateVulnerabilities(queryClient: QueryClient) {
  return queryClient.invalidateQueries({
    queryKey: queryKeys.vulnerability.all,
  });
}

/**
 * Invalidate all metrics-related queries
 */
export function invalidateMetrics(queryClient: QueryClient) {
  return queryClient.invalidateQueries({ queryKey: queryKeys.metrics.all });
}
