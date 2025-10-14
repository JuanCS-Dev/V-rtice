/**
 * useDecisionSubmit - Hook for submitting human decisions
 *
 * Features:
 * - Submits decision to API
 * - Invalidates relevant queries on success
 * - Error handling and loading states
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_HITL_API_URL || 'http://localhost:8003';

/**
 * Submit decision to API
 *
 * @param {Object} decision - DecisionRequest object
 * @param {string} decision.apv_id - APV identifier
 * @param {string} decision.decision - Decision type (approve/reject/modify/escalate)
 * @param {string} decision.justification - Justification text (min 10 chars)
 * @param {number} decision.confidence - Confidence (0.0 - 1.0)
 * @param {Object} decision.modifications - Modifications for "modify" decision
 * @param {string} decision.reviewer_name - Reviewer name
 * @param {string} decision.reviewer_email - Reviewer email
 * @returns {Promise<Object>} DecisionRecord
 */
const submitDecision = async (decision) => {
  const response = await axios.post(`${API_BASE_URL}/hitl/decisions`, decision);
  return response.data;
};

/**
 * Hook for submitting decisions
 *
 * @returns {Object} Mutation state
 * @returns {Function} submit - Function to submit decision
 * @returns {boolean} loading - Loading state
 * @returns {Error} error - Error object if any
 * @returns {boolean} success - Success state
 * @returns {Function} reset - Reset mutation state
 */
export const useDecisionSubmit = () => {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: submitDecision,
    onSuccess: () => {
      // Invalidate queries to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['hitl-reviews'] });
      queryClient.invalidateQueries({ queryKey: ['hitl-stats'] });
    },
    retry: 1,
    retryDelay: 1000,
  });

  return {
    submit: mutation.mutate,
    submitAsync: mutation.mutateAsync,
    loading: mutation.isPending,
    error: mutation.error,
    success: mutation.isSuccess,
    reset: mutation.reset,
  };
};

export default useDecisionSubmit;
