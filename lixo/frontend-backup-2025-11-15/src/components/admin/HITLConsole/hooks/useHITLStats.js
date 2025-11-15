/**
 * useHITLStats - Hook for fetching HITL statistics
 *
 * Features:
 * - Fetches dashboard statistics
 * - Auto-refetch every 60 seconds
 * - React Query cache management
 *
 * Boris Cherny Standard - GAP #37 FIX: Centralized query keys
 * Boris Cherny Standard - GAP #35 FIX: Standardized polling intervals
 */

import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { API_ENDPOINTS } from '@/config/api';
import { queryKeys } from '@/config/queryKeys';
import { POLLING_INTERVALS } from '@/config/queryClient';

const API_BASE_URL = API_ENDPOINTS.hitl;

/**
 * Fetch HITL stats from API
 *
 * @returns {Promise<Object>} ReviewStats with all metrics
 */
const fetchHITLStats = async () => {
  const response = await axios.get(`${API_BASE_URL}/hitl/reviews/stats`);
  return response.data;
};

/**
 * Hook for managing HITL statistics
 *
 * @returns {Object} Query state
 * @returns {Object} stats - Statistics object
 * @returns {boolean} loading - Loading state
 * @returns {Error} error - Error object if any
 */
export const useHITLStats = () => {
  const query = useQuery({
    // Boris Cherny Standard - GAP #37 FIX: Use centralized query key factory
    queryKey: queryKeys.hitl.stats(),
    queryFn: fetchHITLStats,
    staleTime: 30000, // 30 seconds
    // Boris Cherny Standard - GAP #35 FIX: Use standardized polling interval
    refetchInterval: POLLING_INTERVALS.INFREQUENT, // 60s - slow changing data
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });

  return {
    stats: query.data,
    loading: query.isLoading,
    error: query.error,
  };
};

export default useHITLStats;
