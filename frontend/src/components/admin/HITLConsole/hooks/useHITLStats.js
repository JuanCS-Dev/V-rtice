/**
 * useHITLStats - Hook for fetching HITL statistics
 *
 * Features:
 * - Fetches dashboard statistics
 * - Auto-refetch every 60 seconds
 * - React Query cache management
 */

import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { API_ENDPOINTS } from '@/config/api';

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
    queryKey: ['hitl-stats'],
    queryFn: fetchHITLStats,
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Refetch every 60 seconds
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
