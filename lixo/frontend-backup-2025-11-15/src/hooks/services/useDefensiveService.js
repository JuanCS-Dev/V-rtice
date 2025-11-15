/**
 * useDefensiveService Hook
 * =========================
 *
 * React Query hook for Defensive Service operations
 * Follows ADR-002: Component → Hook → Service → API Client
 *
 * Features:
 * - Automatic caching and invalidation
 * - Background refetching
 * - Optimistic updates
 * - Error handling with retry logic
 *
 * Governed by: Constituição Vértice v2.5 - ADR-002
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getDefensiveService } from "@/services/defensive";
import logger from "@/utils/logger";

// Query keys for cache management
export const defensiveQueryKeys = {
  all: ["defensive"],
  metrics: ["defensive", "metrics"],
  health: ["defensive", "health"],
  alerts: ["defensive", "alerts"],
  alert: (id) => ["defensive", "alerts", id],
  behavioral: ["defensive", "behavioral"],
  traffic: ["defensive", "traffic"],
  threatIntel: {
    ip: (ip) => ["defensive", "threat-intel", "ip", ip],
    domain: (domain) => ["defensive", "threat-intel", "domain", domain],
    hash: (hash) => ["defensive", "threat-intel", "hash", hash],
  },
};

// ============================================================================
// METRICS QUERIES
// ============================================================================

/**
 * Hook to fetch defensive metrics
 * @param {Object} options - React Query options
 * @returns {Object} Query result with metrics data
 */
export const useDefensiveMetrics = (options = {}) => {
  const service = getDefensiveService();

  return useQuery({
    queryKey: defensiveQueryKeys.metrics,
    queryFn: () => service.getMetrics(),
    staleTime: 10000, // 10 seconds
    refetchInterval: options.refetchInterval ?? 30000, // 30 seconds
    retry: 2,
    onError: (error) => {
      logger.error("[useDefensiveMetrics] Failed to fetch metrics:", error);
    },
    ...options,
  });
};

/**
 * Hook to check defensive services health
 * @param {Object} options - React Query options
 * @returns {Object} Query result with health status
 */
export const useDefensiveHealth = (options = {}) => {
  const service = getDefensiveService();

  return useQuery({
    queryKey: defensiveQueryKeys.health,
    queryFn: () => service.checkHealth(),
    staleTime: 10000, // 10 seconds
    refetchInterval: options.refetchInterval ?? 60000, // 1 minute
    retry: 1,
    ...options,
  });
};

// ============================================================================
// BEHAVIORAL ANALYZER
// ============================================================================

/**
 * Hook to fetch behavioral metrics
 * @param {Object} options - React Query options
 * @returns {Object} Query result with behavioral metrics
 */
export const useBehavioralMetrics = (options = {}) => {
  const service = getDefensiveService();

  return useQuery({
    queryKey: [...defensiveQueryKeys.behavioral, "metrics"],
    queryFn: () => service.getBehavioralMetrics(),
    staleTime: 10000,
    refetchInterval: options.refetchInterval ?? 30000,
    ...options,
  });
};

/**
 * Hook to analyze behavior event
 * @returns {Object} Mutation object with mutate function
 */
export const useAnalyzeEvent = () => {
  const service = getDefensiveService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (eventData) => service.analyzeEvent(eventData),
    onSuccess: () => {
      // Invalidate metrics after analysis
      queryClient.invalidateQueries({
        queryKey: defensiveQueryKeys.behavioral,
      });
      queryClient.invalidateQueries({ queryKey: defensiveQueryKeys.metrics });
    },
    onError: (error) => {
      logger.error("[useAnalyzeEvent] Analysis failed:", error);
    },
  });
};

/**
 * Hook to analyze batch of events
 * @returns {Object} Mutation object with mutate function
 */
export const useAnalyzeBatchEvents = () => {
  const service = getDefensiveService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (events) => service.analyzeBatchEvents(events),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: defensiveQueryKeys.behavioral,
      });
      queryClient.invalidateQueries({ queryKey: defensiveQueryKeys.metrics });
    },
    onError: (error) => {
      logger.error("[useAnalyzeBatchEvents] Batch analysis failed:", error);
    },
  });
};

/**
 * Hook to train baseline
 * @returns {Object} Mutation object with mutate function
 */
export const useTrainBaseline = () => {
  const service = getDefensiveService();

  return useMutation({
    mutationFn: ({ entityId, trainingEvents }) =>
      service.trainBaseline(entityId, trainingEvents),
    onError: (error) => {
      logger.error("[useTrainBaseline] Training failed:", error);
    },
  });
};

/**
 * Hook to get baseline status
 * @param {string} entityId - Entity identifier
 * @param {Object} options - React Query options
 * @returns {Object} Query result with baseline status
 */
export const useBaselineStatus = (entityId, options = {}) => {
  const service = getDefensiveService();

  return useQuery({
    queryKey: [...defensiveQueryKeys.behavioral, "baseline", entityId],
    queryFn: () => service.getBaselineStatus(entityId),
    enabled: !!entityId, // Only fetch if entityId exists
    staleTime: 30000,
    ...options,
  });
};

// ============================================================================
// ENCRYPTED TRAFFIC ANALYZER
// ============================================================================

/**
 * Hook to fetch traffic metrics
 * @param {Object} options - React Query options
 * @returns {Object} Query result with traffic metrics
 */
export const useTrafficMetrics = (options = {}) => {
  const service = getDefensiveService();

  return useQuery({
    queryKey: [...defensiveQueryKeys.traffic, "metrics"],
    queryFn: () => service.getTrafficMetrics(),
    staleTime: 10000,
    refetchInterval: options.refetchInterval ?? 30000,
    ...options,
  });
};

/**
 * Hook to analyze network flow
 * @returns {Object} Mutation object with mutate function
 */
export const useAnalyzeFlow = () => {
  const service = getDefensiveService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (flowData) => service.analyzeFlow(flowData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: defensiveQueryKeys.traffic });
      queryClient.invalidateQueries({ queryKey: defensiveQueryKeys.metrics });
    },
    onError: (error) => {
      logger.error("[useAnalyzeFlow] Flow analysis failed:", error);
    },
  });
};

/**
 * Hook to analyze batch of flows
 * @returns {Object} Mutation object with mutate function
 */
export const useAnalyzeBatchFlows = () => {
  const service = getDefensiveService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (flows) => service.analyzeBatchFlows(flows),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: defensiveQueryKeys.traffic });
      queryClient.invalidateQueries({ queryKey: defensiveQueryKeys.metrics });
    },
    onError: (error) => {
      logger.error("[useAnalyzeBatchFlows] Batch flow analysis failed:", error);
    },
  });
};

// ============================================================================
// ALERTS
// ============================================================================

/**
 * Hook to fetch alerts
 * @param {Object} filters - Alert filters
 * @param {Object} options - React Query options
 * @returns {Object} Query result with alerts list
 */
export const useAlerts = (filters = {}, options = {}) => {
  const service = getDefensiveService();

  return useQuery({
    queryKey: [...defensiveQueryKeys.alerts, filters],
    queryFn: () => service.getAlerts(filters),
    staleTime: 5000,
    refetchInterval: options.refetchInterval ?? 10000, // Poll every 10s for alerts
    ...options,
  });
};

/**
 * Hook to fetch single alert
 * @param {string} alertId - Alert identifier
 * @param {Object} options - React Query options
 * @returns {Object} Query result with alert details
 */
export const useAlert = (alertId, options = {}) => {
  const service = getDefensiveService();

  return useQuery({
    queryKey: defensiveQueryKeys.alert(alertId),
    queryFn: () => service.getAlert(alertId),
    enabled: !!alertId,
    staleTime: 10000,
    ...options,
  });
};

/**
 * Hook to update alert status
 * Boris Cherny Standard - GAP #33 FIX: Optimistic updates
 * @returns {Object} Mutation object with mutate function
 */
export const useUpdateAlertStatus = () => {
  const service = getDefensiveService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ alertId, status, notes }) =>
      service.updateAlertStatus(alertId, status, notes),
    // Boris Cherny Standard - GAP #33 FIX: Optimistic update
    onMutate: async ({ alertId, status, notes }) => {
      // Cancel any outgoing refetches to prevent overwriting optimistic update
      await queryClient.cancelQueries({ queryKey: defensiveQueryKeys.alerts });
      await queryClient.cancelQueries({
        queryKey: defensiveQueryKeys.alert(alertId),
      });

      // Snapshot previous values
      const previousAlerts = queryClient.getQueryData(
        defensiveQueryKeys.alerts,
      );
      const previousAlert = queryClient.getQueryData(
        defensiveQueryKeys.alert(alertId),
      );

      // Optimistically update alerts list
      if (previousAlerts) {
        queryClient.setQueryData(defensiveQueryKeys.alerts, (old) => {
          if (!old) return old;
          return old.map((alert) =>
            alert.id === alertId
              ? {
                  ...alert,
                  status,
                  notes,
                  updated_at: new Date().toISOString(),
                }
              : alert,
          );
        });
      }

      // Optimistically update specific alert
      if (previousAlert) {
        queryClient.setQueryData(defensiveQueryKeys.alert(alertId), (old) => ({
          ...old,
          status,
          notes,
          updated_at: new Date().toISOString(),
        }));
      }

      // Return context with previous values for rollback
      return { previousAlerts, previousAlert };
    },
    onError: (error, variables, context) => {
      logger.error("[useUpdateAlertStatus] Update failed:", error);
      // Rollback on error
      if (context?.previousAlerts) {
        queryClient.setQueryData(
          defensiveQueryKeys.alerts,
          context.previousAlerts,
        );
      }
      if (context?.previousAlert) {
        queryClient.setQueryData(
          defensiveQueryKeys.alert(variables.alertId),
          context.previousAlert,
        );
      }
    },
    onSettled: (data, error, variables) => {
      // Always refetch after error or success to ensure consistency
      queryClient.invalidateQueries({ queryKey: defensiveQueryKeys.alerts });
      queryClient.invalidateQueries({
        queryKey: defensiveQueryKeys.alert(variables.alertId),
      });
    },
  });
};

// ============================================================================
// THREAT INTELLIGENCE
// ============================================================================

/**
 * Hook to query IP threat intelligence
 * @param {string} ipAddress - IP address
 * @param {Object} options - React Query options
 * @returns {Object} Query result with threat intel
 */
export const useIPThreatIntel = (ipAddress, options = {}) => {
  const service = getDefensiveService();

  return useQuery({
    queryKey: defensiveQueryKeys.threatIntel.ip(ipAddress),
    queryFn: () => service.queryIPThreatIntel(ipAddress),
    enabled: !!ipAddress,
    staleTime: 60000, // 1 minute (threat intel is relatively static)
    ...options,
  });
};

/**
 * Hook to query domain threat intelligence
 * @param {string} domain - Domain name
 * @param {Object} options - React Query options
 * @returns {Object} Query result with threat intel
 */
export const useDomainThreatIntel = (domain, options = {}) => {
  const service = getDefensiveService();

  return useQuery({
    queryKey: defensiveQueryKeys.threatIntel.domain(domain),
    queryFn: () => service.queryDomainThreatIntel(domain),
    enabled: !!domain,
    staleTime: 60000,
    ...options,
  });
};

/**
 * Hook to query hash threat intelligence
 * @param {string} hash - File hash
 * @param {Object} options - React Query options
 * @returns {Object} Query result with threat intel
 */
export const useHashThreatIntel = (hash, options = {}) => {
  const service = getDefensiveService();

  return useQuery({
    queryKey: defensiveQueryKeys.threatIntel.hash(hash),
    queryFn: () => service.queryHashThreatIntel(hash),
    enabled: !!hash && hash.length >= 32,
    staleTime: 60000,
    ...options,
  });
};

/**
 * Hook to search threat intelligence (lazy query)
 * @returns {Object} Mutation object with mutate function
 */
export const useSearchThreatIntel = () => {
  const service = getDefensiveService();

  return useMutation({
    mutationFn: async ({ type, value }) => {
      switch (type) {
        case "ip":
          return await service.queryIPThreatIntel(value);
        case "domain":
          return await service.queryDomainThreatIntel(value);
        case "hash":
          return await service.queryHashThreatIntel(value);
        default:
          throw new Error("Invalid threat intel query type");
      }
    },
    onError: (error) => {
      logger.error("[useSearchThreatIntel] Search failed:", error);
    },
  });
};

// ============================================================================
// UTILITY HOOKS
// ============================================================================

/**
 * Hook to manually invalidate all defensive queries
 * @returns {Function} Invalidation function
 */
export const useInvalidateDefensiveQueries = () => {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: defensiveQueryKeys.all });
  };
};

/**
 * Hook to prefetch defensive metrics
 * @returns {Function} Prefetch function
 */
export const usePrefetchDefensiveMetrics = () => {
  const queryClient = useQueryClient();
  const service = getDefensiveService();

  return () => {
    queryClient.prefetchQuery({
      queryKey: defensiveQueryKeys.metrics,
      queryFn: () => service.getMetrics(),
    });
  };
};

// ============================================================================
// EXPORTS
// ============================================================================

export default {
  // Metrics
  useDefensiveMetrics,
  useDefensiveHealth,

  // Behavioral Analyzer
  useBehavioralMetrics,
  useAnalyzeEvent,
  useAnalyzeBatchEvents,
  useTrainBaseline,
  useBaselineStatus,

  // Traffic Analyzer
  useTrafficMetrics,
  useAnalyzeFlow,
  useAnalyzeBatchFlows,

  // Alerts
  useAlerts,
  useAlert,
  useUpdateAlertStatus,

  // Threat Intelligence
  useIPThreatIntel,
  useDomainThreatIntel,
  useHashThreatIntel,
  useSearchThreatIntel,

  // Utilities
  useInvalidateDefensiveQueries,
  usePrefetchDefensiveMetrics,
};
