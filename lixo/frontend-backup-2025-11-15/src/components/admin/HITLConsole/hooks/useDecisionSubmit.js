/**
 * useDecisionSubmit - Hook for submitting human decisions
 *
 * Features:
 * - Submits decision to API
 * - Invalidates relevant queries on success
 * - Error handling and loading states
 *
 * Boris Cherny Standard - GAP #37 FIX: Centralized query keys
 * Boris Cherny Standard - GAP #33 FIX: Optimistic updates
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import { API_ENDPOINTS } from "@/config/api";
import { queryKeys } from "@/config/queryKeys";
import logger from "@/utils/logger";

const API_BASE_URL = API_ENDPOINTS.hitl;

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
    // Boris Cherny Standard - GAP #33 FIX: Optimistic update
    onMutate: async (decision) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: queryKeys.hitl.reviews() });
      await queryClient.cancelQueries({ queryKey: queryKeys.hitl.stats() });

      // Snapshot previous values
      const previousReviews = queryClient.getQueryData(
        queryKeys.hitl.reviews(),
      );
      const previousStats = queryClient.getQueryData(queryKeys.hitl.stats());

      // Optimistically update reviews (remove the decided APV)
      if (previousReviews) {
        queryClient.setQueryData(queryKeys.hitl.reviews(), (old) => {
          if (!old) return old;
          return old.filter((review) => review.apv_id !== decision.apv_id);
        });
      }

      // Optimistically update stats
      if (previousStats) {
        queryClient.setQueryData(queryKeys.hitl.stats(), (old) => {
          if (!old) return old;
          return {
            ...old,
            pending_count: Math.max(0, (old.pending_count || 0) - 1),
            total_decisions: (old.total_decisions || 0) + 1,
          };
        });
      }

      // Return context for rollback
      return { previousReviews, previousStats };
    },
    onError: (error, variables, context) => {
      logger.error("[useDecisionSubmit] Decision submission failed:", error);
      // Rollback on error
      if (context?.previousReviews) {
        queryClient.setQueryData(
          queryKeys.hitl.reviews(),
          context.previousReviews,
        );
      }
      if (context?.previousStats) {
        queryClient.setQueryData(queryKeys.hitl.stats(), context.previousStats);
      }
    },
    onSettled: () => {
      // Always refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: queryKeys.hitl.reviews() });
      queryClient.invalidateQueries({ queryKey: queryKeys.hitl.stats() });
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
