/**
 * useOffensiveService Hook
 * =========================
 *
 * React Query hook for Offensive Service operations
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

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getOffensiveService } from '@/services/offensive';
import logger from '@/utils/logger';

// Query keys for cache management
export const offensiveQueryKeys = {
  all: ['offensive'],
  metrics: ['offensive', 'metrics'],
  health: ['offensive', 'health'],
  scans: ['offensive', 'scans'],
  scan: (id) => ['offensive', 'scans', id],
  workflows: ['offensive', 'workflows'],
  workflow: (id) => ['offensive', 'workflows', id],
  c2Sessions: ['offensive', 'c2', 'sessions'],
  techniques: ['offensive', 'bas', 'techniques'],
};

// ============================================================================
// METRICS QUERIES
// ============================================================================

/**
 * Hook to fetch offensive metrics
 * @param {Object} options - React Query options
 * @returns {Object} Query result with metrics data
 */
export const useOffensiveMetrics = (options = {}) => {
  const service = getOffensiveService();

  return useQuery({
    queryKey: offensiveQueryKeys.metrics,
    queryFn: () => service.getMetrics(),
    staleTime: 5000, // 5 seconds
    refetchInterval: options.refetchInterval ?? 30000, // 30 seconds
    retry: 2,
    onError: (error) => {
      logger.error('[useOffensiveMetrics] Failed to fetch metrics:', error);
    },
    ...options,
  });
};

/**
 * Hook to check offensive services health
 * @param {Object} options - React Query options
 * @returns {Object} Query result with health status
 */
export const useOffensiveHealth = (options = {}) => {
  const service = getOffensiveService();

  return useQuery({
    queryKey: offensiveQueryKeys.health,
    queryFn: () => service.checkHealth(),
    staleTime: 10000, // 10 seconds
    refetchInterval: options.refetchInterval ?? 60000, // 1 minute
    retry: 1,
    ...options,
  });
};

// ============================================================================
// NETWORK RECONNAISSANCE
// ============================================================================

/**
 * Hook to list network scans
 * @param {number} limit - Maximum scans to return
 * @param {Object} options - React Query options
 * @returns {Object} Query result with scans list
 */
export const useScans = (limit = 50, options = {}) => {
  const service = getOffensiveService();

  return useQuery({
    queryKey: [...offensiveQueryKeys.scans, limit],
    queryFn: () => service.listScans(limit),
    staleTime: 10000,
    ...options,
  });
};

/**
 * Hook to get scan status
 * @param {string} scanId - Scan identifier
 * @param {Object} options - React Query options
 * @returns {Object} Query result with scan status
 */
export const useScanStatus = (scanId, options = {}) => {
  const service = getOffensiveService();

  return useQuery({
    queryKey: offensiveQueryKeys.scan(scanId),
    queryFn: () => service.getScanStatus(scanId),
    enabled: !!scanId, // Only fetch if scanId exists
    refetchInterval: options.refetchInterval ?? 5000, // Poll every 5s
    staleTime: 1000,
    ...options,
  });
};

/**
 * Hook to execute network scan
 * Boris Cherny Standard - GAP #33 FIX: Optimistic updates
 * @returns {Object} Mutation object with mutate function
 */
export const useScanNetwork = () => {
  const service = getOffensiveService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ target, scanType, ports }) =>
      service.scanNetwork(target, scanType, ports),
    // Boris Cherny Standard - GAP #33 FIX: Optimistic update
    onMutate: async ({ target, scanType, ports }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: offensiveQueryKeys.scans });
      await queryClient.cancelQueries({ queryKey: offensiveQueryKeys.metrics });

      // Snapshot previous values
      const previousScans = queryClient.getQueryData(offensiveQueryKeys.scans);
      const previousMetrics = queryClient.getQueryData(offensiveQueryKeys.metrics);

      // Create optimistic scan entry
      const optimisticScan = {
        id: `scan-${Date.now()}-optimistic`,
        target,
        scan_type: scanType,
        ports,
        status: 'running',
        created_at: new Date().toISOString(),
        _optimistic: true, // Flag to identify optimistic updates
      };

      // Optimistically add scan to list
      if (previousScans) {
        queryClient.setQueryData(offensiveQueryKeys.scans, (old) => {
          if (!old) return [optimisticScan];
          return [optimisticScan, ...old];
        });
      }

      // Optimistically update metrics
      if (previousMetrics) {
        queryClient.setQueryData(offensiveQueryKeys.metrics, (old) => ({
          ...old,
          activeScans: (old?.activeScans || 0) + 1,
          networkScans: (old?.networkScans || 0) + 1,
        }));
      }

      // Return context for rollback
      return { previousScans, previousMetrics, optimisticScan };
    },
    onError: (error, variables, context) => {
      logger.error('[useScanNetwork] Scan failed:', error);
      // Rollback on error
      if (context?.previousScans) {
        queryClient.setQueryData(offensiveQueryKeys.scans, context.previousScans);
      }
      if (context?.previousMetrics) {
        queryClient.setQueryData(offensiveQueryKeys.metrics, context.previousMetrics);
      }
    },
    onSuccess: (data, variables, context) => {
      // Replace optimistic scan with real data
      if (context?.optimisticScan && data) {
        queryClient.setQueryData(offensiveQueryKeys.scans, (old) => {
          if (!old) return [data];
          // Replace optimistic entry with real data
          return old.map((scan) =>
            scan.id === context.optimisticScan.id ? data : scan
          );
        });
      }
    },
    onSettled: () => {
      // Always refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: offensiveQueryKeys.scans });
      queryClient.invalidateQueries({ queryKey: offensiveQueryKeys.metrics });
    },
  });
};

/**
 * Hook to discover hosts
 * @returns {Object} Mutation object with mutate function
 */
export const useDiscoverHosts = () => {
  const service = getOffensiveService();

  return useMutation({
    mutationFn: ({ network }) => service.discoverHosts(network),
    onError: (error) => {
      logger.error('[useDiscoverHosts] Discovery failed:', error);
    },
  });
};

// ============================================================================
// VULNERABILITY INTELLIGENCE
// ============================================================================

/**
 * Hook to search CVE
 * @returns {Object} Mutation object with mutate function
 */
export const useSearchCVE = () => {
  const service = getOffensiveService();

  return useMutation({
    mutationFn: ({ cveId }) => service.searchCVE(cveId),
    onError: (error) => {
      logger.error('[useSearchCVE] Search failed:', error);
    },
  });
};

/**
 * Hook to search vulnerabilities
 * @returns {Object} Mutation object with mutate function
 */
export const useSearchVulnerabilities = () => {
  const service = getOffensiveService();

  return useMutation({
    mutationFn: ({ query, filters }) => service.searchVulnerabilities(query, filters),
    onError: (error) => {
      logger.error('[useSearchVulnerabilities] Search failed:', error);
    },
  });
};

/**
 * Hook to get exploits for CVE
 * @returns {Object} Mutation object with mutate function
 */
export const useGetExploits = () => {
  const service = getOffensiveService();

  return useMutation({
    mutationFn: ({ cveId }) => service.getExploits(cveId),
    onError: (error) => {
      logger.error('[useGetExploits] Failed to get exploits:', error);
    },
  });
};

// ============================================================================
// WEB ATTACK SURFACE
// ============================================================================

/**
 * Hook to scan web target
 * @returns {Object} Mutation object with mutate function
 */
export const useScanWebTarget = () => {
  const service = getOffensiveService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ url, scanProfile, authConfig }) =>
      service.scanWebTarget(url, scanProfile, authConfig),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: offensiveQueryKeys.metrics });
    },
    onError: (error) => {
      logger.error('[useScanWebTarget] Web scan failed:', error);
    },
  });
};

/**
 * Hook to run web test
 * @returns {Object} Mutation object with mutate function
 */
export const useRunWebTest = () => {
  const service = getOffensiveService();

  return useMutation({
    mutationFn: ({ url, testType, params }) =>
      service.runWebTest(url, testType, params),
    onError: (error) => {
      logger.error('[useRunWebTest] Test failed:', error);
    },
  });
};

// ============================================================================
// C2 ORCHESTRATION
// ============================================================================

/**
 * Hook to list C2 sessions
 * @param {string} framework - Optional framework filter
 * @param {Object} options - React Query options
 * @returns {Object} Query result with sessions
 */
export const useC2Sessions = (framework = null, options = {}) => {
  const service = getOffensiveService();

  return useQuery({
    queryKey: [...offensiveQueryKeys.c2Sessions, framework],
    queryFn: () => service.listC2Sessions(framework),
    staleTime: 5000,
    refetchInterval: options.refetchInterval ?? 10000, // Poll every 10s
    ...options,
  });
};

/**
 * Hook to create C2 session
 * @returns {Object} Mutation object with mutate function
 */
export const useCreateC2Session = () => {
  const service = getOffensiveService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ framework, targetHost, payload, config }) =>
      service.createC2Session(framework, targetHost, payload, config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: offensiveQueryKeys.c2Sessions });
      queryClient.invalidateQueries({ queryKey: offensiveQueryKeys.metrics });
    },
    onError: (error) => {
      logger.error('[useCreateC2Session] Session creation failed:', error);
    },
  });
};

/**
 * Hook to execute C2 command
 * @returns {Object} Mutation object with mutate function
 */
export const useExecuteC2Command = () => {
  const service = getOffensiveService();

  return useMutation({
    mutationFn: ({ sessionId, command, args }) =>
      service.executeC2Command(sessionId, command, args),
    onError: (error) => {
      logger.error('[useExecuteC2Command] Command execution failed:', error);
    },
  });
};

// ============================================================================
// BREACH & ATTACK SIMULATION
// ============================================================================

/**
 * Hook to list MITRE ATT&CK techniques
 * @param {string} tactic - Optional tactic filter
 * @param {string} platform - Optional platform filter
 * @param {Object} options - React Query options
 * @returns {Object} Query result with techniques
 */
export const useAttackTechniques = (tactic = null, platform = null, options = {}) => {
  const service = getOffensiveService();

  return useQuery({
    queryKey: [...offensiveQueryKeys.techniques, tactic, platform],
    queryFn: () => service.listAttackTechniques(tactic, platform),
    staleTime: 60000, // 1 minute (static data)
    ...options,
  });
};

/**
 * Hook to run attack simulation
 * @returns {Object} Mutation object with mutate function
 */
export const useRunAttackSimulation = () => {
  const service = getOffensiveService();

  return useMutation({
    mutationFn: ({ techniqueId, targetHost, platform, params }) =>
      service.runAttackSimulation(techniqueId, targetHost, platform, params),
    onError: (error) => {
      logger.error('[useRunAttackSimulation] Simulation failed:', error);
    },
  });
};

/**
 * Hook to get ATT&CK coverage
 * @param {string} organizationId - Optional organization filter
 * @param {Object} options - React Query options
 * @returns {Object} Query result with coverage data
 */
export const useAttackCoverage = (organizationId = null, options = {}) => {
  const service = getOffensiveService();

  return useQuery({
    queryKey: ['offensive', 'bas', 'coverage', organizationId],
    queryFn: () => service.getAttackCoverage(organizationId),
    staleTime: 30000,
    ...options,
  });
};

// ============================================================================
// WORKFLOWS
// ============================================================================

/**
 * Hook to list workflows
 * @param {Object} options - React Query options
 * @returns {Object} Query result with workflows
 */
export const useWorkflows = (options = {}) => {
  const service = getOffensiveService();

  return useQuery({
    queryKey: offensiveQueryKeys.workflows,
    queryFn: () => service.listWorkflows(),
    staleTime: 30000,
    ...options,
  });
};

/**
 * Hook to create workflow
 * @returns {Object} Mutation object with mutate function
 */
export const useCreateWorkflow = () => {
  const service = getOffensiveService();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (workflowConfig) => service.createWorkflow(workflowConfig),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: offensiveQueryKeys.workflows });
    },
    onError: (error) => {
      logger.error('[useCreateWorkflow] Workflow creation failed:', error);
    },
  });
};

/**
 * Hook to execute workflow
 * @returns {Object} Mutation object with mutate function
 */
export const useExecuteWorkflow = () => {
  const service = getOffensiveService();

  return useMutation({
    mutationFn: ({ workflowId, context }) =>
      service.executeWorkflow(workflowId, context),
    onError: (error) => {
      logger.error('[useExecuteWorkflow] Workflow execution failed:', error);
    },
  });
};

/**
 * Hook to get workflow status
 * @param {string} executionId - Execution identifier
 * @param {Object} options - React Query options
 * @returns {Object} Query result with workflow status
 */
export const useWorkflowStatus = (executionId, options = {}) => {
  const service = getOffensiveService();

  return useQuery({
    queryKey: offensiveQueryKeys.workflow(executionId),
    queryFn: () => service.getWorkflowStatus(executionId),
    enabled: !!executionId,
    refetchInterval: options.refetchInterval ?? 5000, // Poll every 5s
    staleTime: 1000,
    ...options,
  });
};

// ============================================================================
// UTILITY HOOKS
// ============================================================================

/**
 * Hook to manually invalidate all offensive queries
 * @returns {Function} Invalidation function
 */
export const useInvalidateOffensiveQueries = () => {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: offensiveQueryKeys.all });
  };
};

/**
 * Hook to prefetch offensive metrics
 * @returns {Function} Prefetch function
 */
export const usePrefetchOffensiveMetrics = () => {
  const queryClient = useQueryClient();
  const service = getOffensiveService();

  return () => {
    queryClient.prefetchQuery({
      queryKey: offensiveQueryKeys.metrics,
      queryFn: () => service.getMetrics(),
    });
  };
};

// ============================================================================
// EXPORTS
// ============================================================================

export default {
  // Metrics
  useOffensiveMetrics,
  useOffensiveHealth,

  // Network Reconnaissance
  useScans,
  useScanStatus,
  useScanNetwork,
  useDiscoverHosts,

  // Vulnerability Intelligence
  useSearchCVE,
  useSearchVulnerabilities,
  useGetExploits,

  // Web Attack Surface
  useScanWebTarget,
  useRunWebTest,

  // C2 Orchestration
  useC2Sessions,
  useCreateC2Session,
  useExecuteC2Command,

  // BAS
  useAttackTechniques,
  useRunAttackSimulation,
  useAttackCoverage,

  // Workflows
  useWorkflows,
  useCreateWorkflow,
  useExecuteWorkflow,
  useWorkflowStatus,

  // Utilities
  useInvalidateOffensiveQueries,
  usePrefetchOffensiveMetrics,
};
