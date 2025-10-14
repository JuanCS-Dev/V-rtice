/**
 * useReviewDetails - Hook for fetching detailed APV review context
 *
 * Features:
 * - Fetches complete APV details by ID
 * - Only fetches when APV is selected
 * - React Query cache management
 */

import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_HITL_API_URL || 'http://localhost:8003';

/**
 * Fetch review details from API
 *
 * @param {string} apvId - APV identifier (UUID)
 * @returns {Promise<Object>} ReviewContext with full APV details
 */
const fetchReviewDetails = async (apvId) => {
  const response = await axios.get(`${API_BASE_URL}/hitl/reviews/${apvId}`);
  return response.data;
};

/**
 * Hook for managing review details
 *
 * @param {string} apvId - APV identifier
 * @returns {Object} Query state
 * @returns {Object} review - Review context object
 * @returns {boolean} loading - Loading state
 * @returns {Error} error - Error object if any
 */
export const useReviewDetails = (apvId) => {
  const query = useQuery({
    queryKey: ['hitl-review', apvId],
    queryFn: () => fetchReviewDetails(apvId),
    enabled: !!apvId, // Only fetch when apvId is provided
    staleTime: 60000, // 1 minute
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });

  return {
    review: query.data,
    loading: query.isLoading,
    error: query.error,
  };
};

export default useReviewDetails;
