/**
 * useReviewQueue - Hook for fetching APV review queue
 *
 * Features:
 * - Fetches pending APVs from API
 * - Supports filtering by severity, strategy, verdict
 * - Auto-refetch every 60 seconds
 * - React Query cache management
 */

import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_HITL_API_URL || 'http://localhost:8003';

/**
 * Fetch review queue from API
 *
 * @param {Object} filters - Filter parameters
 * @param {string} filters.severity - Filter by severity (critical/high/medium/low)
 * @param {string} filters.patch_strategy - Filter by patch strategy
 * @param {string} filters.wargame_verdict - Filter by wargame verdict
 * @returns {Promise<Array>} List of ReviewListItem
 */
const fetchReviewQueue = async (filters = {}) => {
  const params = new URLSearchParams();

  if (filters.severity) {
    params.append('severity', filters.severity);
  }
  if (filters.patch_strategy) {
    params.append('patch_strategy', filters.patch_strategy);
  }
  if (filters.wargame_verdict) {
    params.append('wargame_verdict', filters.wargame_verdict);
  }

  params.append('limit', '50');
  params.append('offset', '0');

  const response = await axios.get(`${API_BASE_URL}/hitl/reviews?${params.toString()}`);
  // API returns {reviews: [...], total: N}
  return response.data.reviews || [];
};

/**
 * Hook for managing review queue
 *
 * @param {Object} filters - Filter parameters
 * @returns {Object} Query state
 * @returns {Array} reviews - List of reviews
 * @returns {boolean} loading - Loading state
 * @returns {Error} error - Error object if any
 * @returns {Function} refetch - Function to manually refetch
 */
export const useReviewQueue = (filters = {}) => {
  const query = useQuery({
    queryKey: ['hitl-reviews', filters],
    queryFn: () => fetchReviewQueue(filters),
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Refetch every 60 seconds
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });

  return {
    reviews: query.data || [],
    loading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
    isRefetching: query.isRefetching,
  };
};

export default useReviewQueue;
