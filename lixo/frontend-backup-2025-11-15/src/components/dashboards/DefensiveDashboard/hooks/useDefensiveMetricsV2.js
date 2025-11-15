/**
 * useDefensiveMetricsV2 Hook
 *
 * VERSÃO 2 - Integração Zustand + React Query
 *
 * Combines:
 * - React Query for API caching and fetching
 * - Zustand for global state management
 *
 * Benefits:
 * - No props drilling
 * - Automatic caching
 * - Background refetching
 * - Centralized state
 * - Optimized re-renders
 */

import { useEffect } from "react";
import { useDefensiveMetricsQuery } from "../../../../hooks/queries/useDefensiveMetricsQuery";
import { useDefensiveStore } from "../../../../stores/defensiveStore";

/**
 * Hook that combines React Query + Zustand
 *
 * Fetches data with React Query and syncs to Zustand store
 *
 * @param {Object} options - Options for React Query
 * @returns {Object} Combined state and actions
 */
export const useDefensiveMetricsV2 = (options = {}) => {
  // Zustand store
  const metrics = useDefensiveStore((state) => state.metrics);
  const setMetrics = useDefensiveStore((state) => state.setMetrics);
  const setLoading = useDefensiveStore((state) => state.setLoading);
  const setError = useDefensiveStore((state) => state.setError);

  // React Query
  const { data, isLoading, error, refetch, isRefetching, dataUpdatedAt } =
    useDefensiveMetricsQuery({
      ...options,
      onSuccess: (data) => {
        // Sync to Zustand store on successful fetch
        setMetrics(data);

        // Call custom callback if provided
        if (options.onSuccess) {
          options.onSuccess(data);
        }
      },
      onError: (err) => {
        // Sync error to Zustand store
        setError(err.message);

        // Call custom callback if provided
        if (options.onError) {
          options.onError(err);
        }
      },
    });

  // Sync loading state to Zustand
  useEffect(() => {
    setLoading("metrics", isLoading || isRefetching);
  }, [isLoading, isRefetching, setLoading]);

  return {
    // Data (prioritize React Query cache, fallback to Zustand)
    metrics: data || metrics,

    // Loading state
    loading: isLoading || isRefetching,
    isLoading,
    isRefetching,

    // Error state
    error,

    // Actions
    refetch,

    // Metadata
    lastUpdate: dataUpdatedAt ? new Date(dataUpdatedAt).toISOString() : null,
  };
};

/**
 * Example usage:
 *
 * // In component:
 * const { metrics, loading, refetch } = useDefensiveMetricsV2();
 *
 * // Metrics are automatically cached by React Query
 * // State is automatically synced to Zustand
 * // Any component can access the same data without re-fetching
 */
