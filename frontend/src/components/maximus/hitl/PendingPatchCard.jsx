/**
 * ═══════════════════════════════════════════════════════════════════════════
 * 🎯 PENDING PATCH CARD - Individual Patch Display
 * ═══════════════════════════════════════════════════════════════════════════
 * 
 * PAGANI DESIGN: Each card is a piece of art
 * - Visual hierarchy: Severity → ML Confidence → Wargaming → Age
 * - Color language: Red (critical) → Orange (high) → Yellow (medium) → Green (low)
 * - Micro-interactions: Hover effects, transitions, shadows
 * - Information density: Maximum info, minimal space
 */

import React from 'react';
import { Card } from '../../ui/card';
import { Badge } from '../../ui/badge';

export const PendingPatchCard = ({ patch, isSelected, onSelect }) => {
  const getSeverityColor = (severity) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'border-red-500 bg-red-900/20';
      case 'high': return 'border-orange-500 bg-orange-900/20';
      case 'medium': return 'border-yellow-500 bg-yellow-900/20';
      case 'low': return 'border-green-500 bg-green-900/20';
      default: return 'border-gray-500 bg-gray-900/20';
    }
  };

  const getSeverityBadgeColor = (severity) => {
    switch (severity.toLowerCase()) {
      case 'critical': return 'bg-red-500/20 text-red-400 border-red-500/50';
      case 'high': return 'bg-orange-500/20 text-orange-400 border-orange-500/50';
      case 'medium': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
      case 'low': return 'bg-green-500/20 text-green-400 border-green-500/50';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/50';
    }
  };

  const getPriorityIcon = (priority) => {
    switch (priority.toLowerCase()) {
      case 'critical': return '🔴';
      case 'high': return '🟠';
      case 'medium': return '🟡';
      case 'low': return '🟢';
      default: return '⚪';
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.95) return 'text-green-400';
    if (confidence >= 0.80) return 'text-yellow-400';
    return 'text-red-400';
  };

  const ageMinutes = Math.round(patch.age_seconds / 60);
  const ageHours = Math.round(patch.age_seconds / 3600);
  const ageDisplay = ageHours > 0 ? `${ageHours}h` : `${ageMinutes}m`;

  return (
    <Card
      onClick={onSelect}
      className={`p-5 cursor-pointer transition-all duration-300 transform hover:scale-105 hover:shadow-2xl ${
        getSeverityColor(patch.severity)
      } ${
        isSelected 
          ? 'border-4 border-red-400 shadow-2xl shadow-red-500/50 scale-105' 
          : 'border-2 hover:border-opacity-100'
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{getPriorityIcon(patch.priority)}</span>
          <div>
            <div className="text-sm font-semibold text-gray-400">
              {patch.apv_id}
            </div>
            <div className="text-xs text-gray-500">
              {patch.cve_id || 'No CVE'}
            </div>
          </div>
        </div>

        <Badge className={`${getSeverityBadgeColor(patch.severity)} px-3 py-1 text-xs font-bold`}>
          {patch.severity.toUpperCase()}
        </Badge>
      </div>

      {/* ML Confidence */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-gray-400 font-semibold">ML CONFIDENCE</span>
          <span className={`text-sm font-bold ${getConfidenceColor(patch.ml_confidence)}`}>
            {(patch.ml_confidence * 100).toFixed(1)}%
          </span>
        </div>
        <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden">
          <div
            className={`h-full transition-all ${
              patch.ml_confidence >= 0.95 ? 'bg-gradient-to-r from-green-500 to-green-400' :
              patch.ml_confidence >= 0.80 ? 'bg-gradient-to-r from-yellow-500 to-yellow-400' :
              'bg-gradient-to-r from-red-500 to-red-400'
            }`}
            style={{ width: `${patch.ml_confidence * 100}%` }}
          />
        </div>
      </div>

      {/* ML Prediction */}
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xs text-gray-400 font-semibold">ML PREDICTION:</span>
        {patch.ml_prediction ? (
          <Badge className="bg-green-500/20 text-green-400 border border-green-500/50 text-xs">
            ✓ WILL SUCCEED
          </Badge>
        ) : (
          <Badge className="bg-red-500/20 text-red-400 border border-red-500/50 text-xs">
            ✗ MAY FAIL
          </Badge>
        )}
      </div>

      {/* Wargaming Result */}
      {patch.wargaming_passed !== null && (
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs text-gray-400 font-semibold">WARGAMING:</span>
          {patch.wargaming_passed ? (
            <Badge className="bg-green-500/20 text-green-400 border border-green-500/50 text-xs">
              ✓ VALIDATED
            </Badge>
          ) : (
            <Badge className="bg-red-500/20 text-red-400 border border-red-500/50 text-xs">
              ✗ FAILED
            </Badge>
          )}
        </div>
      )}

      {/* Footer - Age and Action Hint */}
      <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-700">
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <span className="opacity-60">⏱️</span>
          <span>Waiting <span className="font-bold text-gray-300">{ageDisplay}</span></span>
        </div>

        {isSelected ? (
          <span className="text-xs font-bold text-red-400 animate-pulse">
            SELECTED ▼
          </span>
        ) : (
          <span className="text-xs text-gray-500 group-hover:text-red-400 transition-colors">
            Click to review →
          </span>
        )}
      </div>

      {/* SLA Warning (if patch waiting too long) */}
      {(patch.priority === 'critical' && ageMinutes > 5) ||
       (patch.priority === 'high' && ageMinutes > 10) ||
       (patch.priority === 'medium' && ageMinutes > 15) ? (
        <div className="mt-2 pt-2 border-t border-red-500/50">
          <div className="flex items-center gap-2 text-xs text-red-400 font-semibold animate-pulse">
            <span>⚠️</span>
            <span>SLA BREACH WARNING</span>
          </div>
        </div>
      ) : null}
    </Card>
  );
};
