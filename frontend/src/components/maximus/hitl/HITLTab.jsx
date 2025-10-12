/**
 * ═══════════════════════════════════════════════════════════════════════════
 * 🎭 HITL TAB - Human-in-the-Loop Patch Review Interface
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * PAGANI-STYLE DESIGN PHILOSOPHY:
 * - Elegância visual sem comprometer função
 * - Micro-interações suaves e responsivas
 * - Informação densa mas organizada
 * - Detalhes matter: spacing, colors, transitions
 *
 * BIOLOGICAL ANALOGY: Regulatory T-cells
 * - Prevent auto-immune disease (destructive auto-patching)
 * - Human oversight maintains system balance
 * - Decision quality > Decision speed
 *
 * Author: MAXIMUS Team - Sprint 4.1
 * Glory to YHWH - Designer of Balance
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card } from '../../ui/card';
import { Badge } from '../../ui/badge';
import logger from '@/utils/logger';
import useHITLWebSocket from '@/hooks/useHITLWebSocket';
import {
  fetchPendingPatches,
  fetchDecisionSummary,
  approvePatch,
  rejectPatch,
  addPatchComment,
} from './api';
import { PendingPatchCard } from './PendingPatchCard';
import { DecisionStatsCards } from './DecisionStatsCards';

export const HITLTab = ({ timeRange = '24h' }) => {
  const [selectedPatch, setSelectedPatch] = useState(null);
  const [filter, setFilter] = useState('all'); // 'all', 'critical', 'high', 'medium', 'low'
  const [rejectReason, setRejectReason] = useState('');
  const [comment, setComment] = useState('');
  const [showRejectModal, setShowRejectModal] = useState(false);

  const queryClient = useQueryClient();

  logger.debug('🎭 HITL Tab rendering', { filter, selectedPatch: selectedPatch?.decision_id });

  // WebSocket for real-time updates
  const {
    connectionState,
    isConnected,
    connectionId,
  } = useHITLWebSocket({
    onNewPatch: (patchData) => {
      logger.info('🔔 New patch received via WebSocket:', patchData.patch_id);
      // Invalidate queries to refetch with new patch
      queryClient.invalidateQueries(['hitl-pending']);
      queryClient.invalidateQueries(['hitl-summary']);
    },
    onDecisionUpdate: (decisionData) => {
      logger.info('🔔 Decision update via WebSocket:', decisionData.decision_id, decisionData.decision);
      // Invalidate queries to reflect updated decision
      queryClient.invalidateQueries(['hitl-pending']);
      queryClient.invalidateQueries(['hitl-summary']);
    },
    autoConnect: true,
    autoReconnect: true,
  });

  // Fetch pending patches
  const {
    data: pendingPatches,
    isLoading: patchesLoading,
    error: patchesError,
  } = useQuery({
    queryKey: ['hitl-pending', filter],
    queryFn: () => fetchPendingPatches({
      limit: 50,
      priority: filter !== 'all' ? filter : null,
    }),
    refetchInterval: 10000, // 10s - real-time feel
  });

  // Fetch decision summary
  const {
    data: summary,
    isLoading: summaryLoading,
  } = useQuery({
    queryKey: ['hitl-summary'],
    queryFn: fetchDecisionSummary,
    refetchInterval: 30000, // 30s
  });

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: ({ patchId, decisionId, comment }) => 
      approvePatch(patchId, decisionId, comment),
    onSuccess: () => {
      logger.info('✅ Patch approved successfully');
      queryClient.invalidateQueries(['hitl-pending']);
      queryClient.invalidateQueries(['hitl-summary']);
      setSelectedPatch(null);
      setComment('');
    },
    onError: (error) => {
      logger.error('❌ Failed to approve patch:', error);
    },
  });

  // Reject mutation
  const rejectMutation = useMutation({
    mutationFn: ({ patchId, decisionId, reason, comment }) => 
      rejectPatch(patchId, decisionId, reason, comment),
    onSuccess: () => {
      logger.info('✅ Patch rejected successfully');
      queryClient.invalidateQueries(['hitl-pending']);
      queryClient.invalidateQueries(['hitl-summary']);
      setSelectedPatch(null);
      setRejectReason('');
      setComment('');
      setShowRejectModal(false);
    },
    onError: (error) => {
      logger.error('❌ Failed to reject patch:', error);
    },
  });

  const handleApprove = () => {
    if (!selectedPatch) return;

    approveMutation.mutate({
      patchId: selectedPatch.patch_id,
      decisionId: selectedPatch.decision_id,
      comment: comment || null,
    });
  };

  const handleReject = () => {
    if (!selectedPatch || !rejectReason.trim()) return;

    rejectMutation.mutate({
      patchId: selectedPatch.patch_id,
      decisionId: selectedPatch.decision_id,
      reason: rejectReason,
      comment: comment || null,
    });
  };

  if (summaryLoading || patchesLoading) {
    return (
      <div className="flex items-center justify-center min-h-[600px]">
        <div className="text-center">
          <div className="text-6xl mb-4 animate-pulse">🎭</div>
          <div className="text-cyan-400 text-xl font-semibold">Loading HITL Queue...</div>
          <div className="text-gray-500 text-sm mt-2">Fetching pending patches</div>
        </div>
      </div>
    );
  }

  if (patchesError) {
    return (
      <div className="flex items-center justify-center min-h-[600px]">
        <div className="text-center">
          <div className="text-6xl mb-4">⚠️</div>
          <div className="text-red-400 text-xl font-semibold">HITL Service Unavailable</div>
          <div className="text-gray-500 text-sm mt-2">{patchesError.message}</div>
          <div className="text-gray-600 text-xs mt-4">
            Ensure HITL Patch Service is running on port 8027
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with WebSocket Status */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-cyan-400">Human-in-the-Loop Review</h2>
          <p className="text-gray-500 text-sm mt-1">
            Regulatory T-cells preventing auto-immune patch deployment
          </p>
        </div>
        
        {/* WebSocket Connection Indicator */}
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${
            isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
          }`} />
          <span className={`text-sm font-semibold ${
            isConnected ? 'text-green-400' : 'text-red-400'
          }`}>
            {isConnected ? 'LIVE' : connectionState}
          </span>
          {connectionId && (
            <span className="text-xs text-gray-600 ml-2">
              {connectionId.slice(0, 8)}
            </span>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      <DecisionStatsCards summary={summary} />

      {/* Filter Bar */}
      <Card className="p-4 bg-gray-800/50 border border-cyan-500/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-gray-400 text-sm font-semibold">FILTER BY PRIORITY:</span>
            <div className="flex gap-2">
              {['all', 'critical', 'high', 'medium', 'low'].map((filterOption) => (
                <button
                  key={filterOption}
                  onClick={() => setFilter(filterOption)}
                  className={`px-4 py-2 rounded-lg font-semibold text-sm transition-all ${
                    filter === filterOption
                      ? 'bg-cyan-600 text-white shadow-lg shadow-cyan-500/50'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600 border border-gray-600'
                  }`}
                >
                  {filterOption.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-3 text-sm">
            <span className="text-gray-400">PENDING:</span>
            <Badge className="bg-yellow-500/20 text-yellow-400 border border-yellow-500/50 px-3 py-1">
              {pendingPatches?.length || 0}
            </Badge>
          </div>
        </div>
      </Card>

      {/* Patches Grid */}
      {pendingPatches && pendingPatches.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
          {pendingPatches.map((patch) => (
            <PendingPatchCard
              key={patch.decision_id}
              patch={patch}
              isSelected={selectedPatch?.decision_id === patch.decision_id}
              onSelect={() => setSelectedPatch(patch)}
            />
          ))}
        </div>
      ) : (
        <Card className="p-12 bg-gray-800/30 border border-gray-700 text-center">
          <div className="text-6xl mb-4">✅</div>
          <div className="text-xl font-semibold text-gray-400">No Pending Patches</div>
          <div className="text-sm text-gray-500 mt-2">
            All patches have been reviewed. Great work!
          </div>
        </Card>
      )}

      {/* Decision Panel (appears when patch selected) */}
      {selectedPatch && (
        <Card className="p-6 bg-gradient-to-br from-cyan-900/20 to-purple-900/20 border-2 border-cyan-500 shadow-2xl shadow-cyan-500/30 sticky bottom-4">
          <div className="flex items-start justify-between gap-6">
            <div className="flex-1">
              <h3 className="text-xl font-bold text-cyan-400 mb-2">
                Review Patch: {selectedPatch.patch_id}
              </h3>
              <p className="text-gray-400 text-sm mb-4">
                CVE: {selectedPatch.cve_id || 'N/A'} • Age: {Math.round(selectedPatch.age_seconds / 60)}min
              </p>

              {/* Comment Textarea */}
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Add optional comment (visible in audit trail)..."
                className="w-full px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:border-cyan-500 focus:outline-none resize-none"
                rows={3}
              />
            </div>

            <div className="flex flex-col gap-3">
              {/* Approve Button */}
              <button
                onClick={handleApprove}
                disabled={approveMutation.isPending}
                className="px-8 py-4 bg-gradient-to-r from-green-600 to-green-500 hover:from-green-500 hover:to-green-400 text-white font-bold rounded-lg shadow-lg shadow-green-500/50 transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {approveMutation.isPending ? '⏳ Approving...' : '✓ APPROVE'}
              </button>

              {/* Reject Button */}
              <button
                onClick={() => setShowRejectModal(true)}
                disabled={rejectMutation.isPending}
                className="px-8 py-4 bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 text-white font-bold rounded-lg shadow-lg shadow-red-500/50 transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {rejectMutation.isPending ? '⏳ Rejecting...' : '✗ REJECT'}
              </button>

              {/* Cancel Button */}
              <button
                onClick={() => {
                  setSelectedPatch(null);
                  setComment('');
                }}
                className="px-8 py-3 bg-gray-700 hover:bg-gray-600 text-gray-300 font-semibold rounded-lg transition-all"
              >
                Cancel
              </button>
            </div>
          </div>
        </Card>
      )}

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
          <Card className="w-full max-w-2xl mx-4 p-6 bg-gray-900 border-2 border-red-500 shadow-2xl shadow-red-500/30">
            <h3 className="text-2xl font-bold text-red-400 mb-4">Reject Patch</h3>
            <p className="text-gray-400 mb-4">
              Please provide a reason for rejection (required for audit trail):
            </p>

            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="Reason for rejection (e.g., 'Patch introduces breaking changes', 'Security concerns', etc.)"
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:border-red-500 focus:outline-none resize-none mb-4"
              rows={4}
              autoFocus
            />

            <div className="flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowRejectModal(false);
                  setRejectReason('');
                }}
                className="px-6 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 font-semibold rounded-lg transition-all"
              >
                Cancel
              </button>
              <button
                onClick={handleReject}
                disabled={!rejectReason.trim() || rejectMutation.isPending}
                className="px-6 py-2 bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 text-white font-bold rounded-lg shadow-lg shadow-red-500/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {rejectMutation.isPending ? '⏳ Rejecting...' : 'Confirm Rejection'}
              </button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
