/**
 * ═══════════════════════════════════════════════════════════════════════════
 * 📊 DECISION STATS CARDS - KPI Display
 * ═══════════════════════════════════════════════════════════════════════════
 */

import React from "react";
import { Card } from "../../ui/card";

export const DecisionStatsCards = ({ summary }) => {
  if (!summary) return null;

  const autoApprovalRate =
    summary.total_patches > 0
      ? ((summary.auto_approved / summary.total_patches) * 100).toFixed(1)
      : 0;

  const avgDecisionTimeMin = summary.avg_decision_time_seconds
    ? (summary.avg_decision_time_seconds / 60).toFixed(1)
    : 0;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Total Patches */}
      <Card className="p-5 bg-gradient-to-br from-gray-800 to-gray-900 border-2 border-red-500/50 hover:border-red-500 transition-all cursor-pointer group">
        <div className="text-gray-400 text-sm font-semibold mb-2">
          Total Decisions
        </div>
        <div className="text-4xl font-bold text-red-400 mb-1 group-hover:scale-110 transition-transform">
          {summary.total_patches}
        </div>
        <div className="text-xs text-gray-500">All time</div>
      </Card>

      {/* Pending */}
      <Card className="p-5 bg-gradient-to-br from-gray-800 to-gray-900 border-2 border-yellow-500/50 hover:border-yellow-500 transition-all cursor-pointer group">
        <div className="text-gray-400 text-sm font-semibold mb-2">
          Pending Review
        </div>
        <div className="text-4xl font-bold text-yellow-400 mb-1 group-hover:scale-110 transition-transform">
          {summary.pending}
        </div>
        <div className="text-xs text-gray-500">Awaiting human decision</div>
      </Card>

      {/* Auto-Approval Rate */}
      <Card className="p-5 bg-gradient-to-br from-gray-800 to-gray-900 border-2 border-green-500/50 hover:border-green-500 transition-all cursor-pointer group">
        <div className="text-gray-400 text-sm font-semibold mb-2">
          Auto-Approval
        </div>
        <div className="text-4xl font-bold text-green-400 mb-1 group-hover:scale-110 transition-transform">
          {autoApprovalRate}%
        </div>
        <div className="text-xs text-gray-500">
          {summary.auto_approved} patches auto-approved
        </div>
      </Card>

      {/* Avg Decision Time */}
      <Card className="p-5 bg-gradient-to-br from-gray-800 to-gray-900 border-2 border-red-500/50 hover:border-red-500 transition-all cursor-pointer group">
        <div className="text-gray-400 text-sm font-semibold mb-2">
          Avg Decision Time
        </div>
        <div className="text-4xl font-bold text-red-400 mb-1 group-hover:scale-110 transition-transform">
          {avgDecisionTimeMin}m
        </div>
        <div className="text-xs text-gray-500">Time to human decision</div>
      </Card>

      {/* Approved */}
      <Card className="p-5 bg-gradient-to-br from-gray-800 to-gray-900 border border-green-500/30 hover:border-green-500/60 transition-all">
        <div className="text-gray-400 text-xs font-semibold mb-1">Approved</div>
        <div className="text-2xl font-bold text-green-400">
          {summary.approved}
        </div>
      </Card>

      {/* Rejected */}
      <Card className="p-5 bg-gradient-to-br from-gray-800 to-gray-900 border border-red-500/30 hover:border-red-500/60 transition-all">
        <div className="text-gray-400 text-xs font-semibold mb-1">Rejected</div>
        <div className="text-2xl font-bold text-red-400">
          {summary.rejected}
        </div>
      </Card>

      {/* ML Accuracy */}
      {summary.ml_accuracy !== null && (
        <Card className="p-5 bg-gradient-to-br from-gray-800 to-gray-900 border border-orange-500/30 hover:border-orange-500/60 transition-all">
          <div className="text-gray-400 text-xs font-semibold mb-1">
            ML Accuracy
          </div>
          <div className="text-2xl font-bold text-orange-400">
            {(summary.ml_accuracy * 100).toFixed(1)}%
          </div>
        </Card>
      )}
    </div>
  );
};
