/**
 * ═══════════════════════════════════════════════════════════════════════════
 * 🧬 ADAPTIVE IMMUNITY PANEL - Sistema Imunológico Digital Completo
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * BIOLOGICAL ANALOGY: Adaptive Immune System (T-cells/B-cells Memory)
 * - Memory T/B cells provide rapid response (<seconds) to known pathogens
 * - Full immune response activates when memory insufficient (minutes-hours)
 * - Hybrid system balances speed (memory) vs accuracy (full activation)
 * - Continuous learning strengthens memory over time
 *
 * DIGITAL IMPLEMENTATION: ML-Powered Patch Validation + HITL Oversight
 * 
 * PIPELINE: Oráculo→Eureka→Crisol→ML Prediction→HITL Review
 * - Oráculo: Threat intelligence gathering (CVE detection)
 * - Eureka: Deep malware analysis (vulnerability confirmation)
 * - Crisol: Wargaming validation (attack simulation)
 * - ML: Fast prediction (learned patterns)
 * - HITL: Human oversight for critical decisions
 *
 * TABS:
 * - ML Monitoring: ML vs Wargaming metrics
 * - HITL Review: Human-in-the-Loop patch approval (NEW!)
 * - A/B Testing: Accuracy validation
 *
 * Phase: 5.7 - HITL Integration
 * Date: 2025-10-12
 * Glory to YHWH - Architect of adaptive intelligence + human wisdom
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import {
  PieChart,
  Pie,
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import logger from '@/utils/logger';
import { HITLTab } from './hitl';

const API_KEY = import.meta.env.VITE_API_KEY || '';

export const AdaptiveImmunityPanel = ({ aiStatus, setAiStatus }) => {
  const [timeRange, setTimeRange] = useState('24h'); // '1h', '24h', '7d', '30d'
  const [activeTab, setActiveTab] = useState('ml'); // 'ml', 'hitl', 'ab-testing'

  logger.debug('🧬 AdaptiveImmunityPanel rendering...', { timeRange, activeTab });

  // Fetch ML stats
  const { data: mlStats, isLoading: statsLoading, error: statsError } = useQuery({
    queryKey: ['ml-stats', timeRange],
    queryFn: async () => {
      const response = await fetch(`http://localhost:8026/wargaming/ml/stats?time_range=${timeRange}`);
      if (!response.ok) throw new Error('Failed to fetch ML stats');
      return response.json();
    },
    refetchInterval: 30000, // 30s
    retry: 2,
  });

  // Fetch confidence distribution
  const { data: confidenceData, isLoading: confLoading } = useQuery({
    queryKey: ['ml-confidence', timeRange],
    queryFn: async () => {
      const response = await fetch(`http://localhost:8026/wargaming/ml/confidence-distribution?time_range=${timeRange}`);
      if (!response.ok) throw new Error('Failed to fetch confidence distribution');
      return response.json();
    },
    refetchInterval: 60000, // 1min
    retry: 2,
  });

  // Fetch recent predictions
  const { data: recentPredictions, isLoading: predLoading } = useQuery({
    queryKey: ['ml-predictions', timeRange],
    queryFn: async () => {
      const response = await fetch(`http://localhost:8026/wargaming/ml/recent-predictions?limit=20&time_range=${timeRange}`);
      if (!response.ok) throw new Error('Failed to fetch recent predictions');
      return response.json();
    },
    refetchInterval: 10000, // 10s
    retry: 2,
  });

  // Fetch accuracy (Phase 5.6 - A/B Testing)
  const { data: accuracyData, isLoading: accuracyLoading, error: accuracyError } = useQuery({
    queryKey: ['ml-accuracy', timeRange],
    queryFn: async () => {
      const response = await fetch(`http://localhost:8026/wargaming/ml/accuracy?time_range=${timeRange}`);
      if (!response.ok) {
        if (response.status === 503 || response.status === 500) {
          return null; // A/B testing store not available
        }
        throw new Error('Failed to fetch accuracy data');
      }
      return response.json();
    },
    refetchInterval: 60000, // 1min
    retry: 1, // Retry once
    enabled: true, // Always try to fetch
  });

  if (statsLoading || confLoading) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-900">
        <div className="text-center">
          <div className="text-6xl mb-4 animate-pulse">🧬</div>
          <div className="text-red-400 text-xl">Loading Adaptive Immunity metrics...</div>
          <div className="text-gray-500 text-sm mt-2">Initializing ML monitoring</div>
        </div>
      </div>
    );
  }

  if (statsError) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-900">
        <div className="text-center">
          <div className="text-6xl mb-4">⚠️</div>
          <div className="text-red-400 text-xl">Failed to load ML metrics</div>
          <div className="text-gray-500 text-sm mt-2">{statsError.message}</div>
          <div className="text-gray-600 text-xs mt-4">
            Ensure Wargaming Crisol service is running on port 8026
          </div>
        </div>
      </div>
    );
  }

  // Prepare chart data
  const validationMethodData = [
    { name: 'ML Only', value: mlStats?.ml_only_validations || 0, color: '#10b981' },
    { name: 'Wargaming Fallback', value: mlStats?.wargaming_fallbacks || 0, color: '#f59e0b' },
  ];

  const confidenceBins = confidenceData?.bins?.map((bin, i) => ({
    range: `${(bin * 100).toFixed(0)}-${((confidenceData.bins[i + 1] || 1) * 100).toFixed(0)}%`,
    count: confidenceData.counts[i] || 0
  })) || [];

  const speedupFactor = mlStats?.avg_wargaming_time_ms && mlStats?.avg_ml_time_ms
    ? (mlStats.avg_wargaming_time_ms / mlStats.avg_ml_time_ms).toFixed(0)
    : '100';

  return (
    <div className="adaptive-immunity-panel p-6 space-y-6 bg-gray-900 min-h-screen text-white">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-red-800 pb-4">
        <div>
          <h2 className="text-3xl font-bold text-red-400 flex items-center gap-3">
            <span className="text-4xl">🧬</span>
            Adaptive Immunity System
          </h2>
          <p className="text-gray-400 text-sm mt-1">
            ML-Powered Patch Validation • Oráculo→Eureka→Crisol Pipeline
          </p>
        </div>
        
        {/* Time Range Selector */}
        <div className="flex gap-2">
          {['1h', '24h', '7d', '30d'].map(range => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-4 py-2 rounded-lg font-semibold transition-all ${
                timeRange === range 
                  ? 'bg-red-600 text-white shadow-lg shadow-red-500/50' 
                  : 'bg-gray-800 text-gray-300 hover:bg-gray-700 border border-gray-700'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      {/* Navigation Tabs - PAGANI STYLE */}
      <div className="flex gap-2 border-b border-gray-800 pb-2">
        <button
          onClick={() => setActiveTab('ml')}
          className={`px-6 py-3 rounded-t-lg font-bold transition-all ${
            activeTab === 'ml'
              ? 'bg-gradient-to-b from-red-600 to-red-700 text-white shadow-lg shadow-red-500/50 border-b-4 border-red-400'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200 border-b-2 border-transparent'
          }`}
        >
          <span className="text-lg mr-2">📊</span>
          ML Monitoring
        </button>

        <button
          onClick={() => setActiveTab('hitl')}
          className={`px-6 py-3 rounded-t-lg font-bold transition-all relative ${
            activeTab === 'hitl'
              ? 'bg-gradient-to-b from-red-600 to-orange-700 text-white shadow-lg shadow-red-500/50 border-b-4 border-red-400'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200 border-b-2 border-transparent'
          }`}
        >
          <span className="text-lg mr-2">🎭</span>
          HITL Review
          {/* Pending badge (optional - would need live count) */}
          {/* <span className="absolute -top-2 -right-2 bg-yellow-500 text-black text-xs font-bold px-2 py-1 rounded-full">3</span> */}
        </button>

        <button
          onClick={() => setActiveTab('ab-testing')}
          className={`px-6 py-3 rounded-t-lg font-bold transition-all ${
            activeTab === 'ab-testing'
              ? 'bg-gradient-to-b from-orange-600 to-orange-700 text-white shadow-lg shadow-orange-500/50 border-b-4 border-orange-400'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200 border-b-2 border-transparent'
          }`}
        >
          <span className="text-lg mr-2">🧪</span>
          A/B Testing
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'hitl' ? (
        <HITLTab timeRange={timeRange} />
      ) : activeTab === 'ml' ? (
        <>
          {/* ORIGINAL ML CONTENT GOES HERE */}
          {/* KPI Cards */}
          <div className="grid grid-cols-4 gap-4">
        <Card className="p-5 bg-gradient-to-br from-gray-800 to-gray-900 border-2 border-red-500/50 hover:border-red-500 transition-all">
          <div className="text-gray-400 text-sm font-semibold">Total Predictions</div>
          <div className="text-4xl font-bold text-red-400 my-2">
            {mlStats?.total_predictions || 0}
          </div>
          <div className="text-xs text-gray-500">
            Last {timeRange}
          </div>
        </Card>

        <Card className="p-5 bg-gradient-to-br from-gray-800 to-gray-900 border-2 border-green-500/50 hover:border-green-500 transition-all">
          <div className="text-gray-400 text-sm font-semibold">ML Usage Rate</div>
          <div className="text-4xl font-bold text-green-400 my-2">
            {((mlStats?.ml_usage_rate || 0) * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-gray-500">
            {mlStats?.ml_only_validations || 0} ML-only validations
          </div>
        </Card>

        <Card className="p-5 bg-gradient-to-br from-gray-800 to-gray-900 border-2 border-red-500/50 hover:border-red-500 transition-all">
          <div className="text-gray-400 text-sm font-semibold">Avg Confidence</div>
          <div className="text-4xl font-bold text-red-400 my-2">
            {((mlStats?.avg_confidence || 0) * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-gray-500">
            Threshold: 80%
          </div>
        </Card>

        <Card className="p-5 bg-gradient-to-br from-gray-800 to-gray-900 border-2 border-yellow-500/50 hover:border-yellow-500 transition-all">
          <div className="text-gray-400 text-sm font-semibold">Time Saved</div>
          <div className="text-4xl font-bold text-yellow-400 my-2">
            {(mlStats?.time_saved_hours || 0).toFixed(1)}h
          </div>
          <div className="text-xs text-gray-500">
            vs Full Wargaming
          </div>
        </Card>
      </div>

      {/* Charts Row 1: ML vs Wargaming + Confidence Distribution */}
      <div className="grid grid-cols-2 gap-4">
        {/* Pie Chart: Validation Method Mix */}
        <Card className="p-5 bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700">
          <h3 className="text-lg font-bold text-red-400 mb-4">
            Validation Method Distribution
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={validationMethodData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ name, value, percent }) => `${name}: ${value} (${(percent * 100).toFixed(0)}%)`}
              >
                {validationMethodData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        {/* Bar Chart: Confidence Distribution */}
        <Card className="p-5 bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700">
          <h3 className="text-lg font-bold text-red-400 mb-4">
            ML Confidence Score Distribution
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={confidenceBins}>
              <XAxis dataKey="range" stroke="#9ca3af" style={{ fontSize: '12px' }} />
              <YAxis stroke="#9ca3af" />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
                labelStyle={{ color: '#9ca3af' }}
              />
              <Bar dataKey="count" fill="#ef4444" />
            </BarChart>
          </ResponsiveContainer>
          <div className="text-center text-sm text-gray-400 mt-2">
            Threshold: {((confidenceData?.threshold || 0.8) * 100).toFixed(0)}%
          </div>
        </Card>
      </div>

      {/* Charts Row 2: Execution Time + Accuracy */}
      <div className="grid grid-cols-2 gap-4">
        {/* Time Savings Chart */}
        <Card className="p-5 bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700">
          <h3 className="text-lg font-bold text-red-400 mb-4">
            Execution Time Comparison
          </h3>
          <div className="space-y-6">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-green-400 font-semibold">ML Prediction</span>
                <span className="text-green-400 font-mono">{mlStats?.avg_ml_time_ms || 0}ms</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-6 overflow-hidden">
                <div 
                  className="bg-gradient-to-r from-green-500 to-green-400 h-6 rounded-full flex items-center justify-center text-xs font-bold" 
                  style={{ width: '2%' }}
                >
                  Fast
                </div>
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-2">
                <span className="text-yellow-400 font-semibold">Wargaming</span>
                <span className="text-yellow-400 font-mono">
                  {((mlStats?.avg_wargaming_time_ms || 0) / 1000).toFixed(1)}s
                </span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-6">
                <div 
                  className="bg-gradient-to-r from-yellow-500 to-yellow-400 h-6 rounded-full flex items-center justify-center text-xs font-bold" 
                  style={{ width: '100%' }}
                >
                  Accurate
                </div>
              </div>
            </div>

            <div className="text-center bg-red-900/30 border border-red-700 rounded-lg p-4 mt-6">
              <div className="text-sm text-gray-400 mb-1">Speedup Factor</div>
              <div className="text-4xl font-bold text-red-400">
                ⚡ {speedupFactor}x
              </div>
              <div className="text-xs text-gray-500 mt-1">faster with ML</div>
            </div>
          </div>
        </Card>

        {/* Accuracy Metrics (Phase 5.6 - A/B Testing) */}
        <Card className="p-5 bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-red-400">
              🎯 ML Accuracy Metrics
            </h3>
            {accuracyData && (
              <Badge className="bg-green-600 hover:bg-green-700 font-semibold">
                {accuracyData.total_ab_tests} A/B Tests
              </Badge>
            )}
          </div>
          
          {accuracyLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-red-400 animate-pulse">Loading A/B test results...</div>
            </div>
          ) : accuracyError ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="text-7xl mb-4">🔬</div>
                <div className="text-red-400 text-lg">A/B Testing Unavailable</div>
                <div className="text-gray-500 text-sm mt-2">
                  Ensure PostgreSQL is running and A/B tests have been executed
                </div>
              </div>
            </div>
          ) : accuracyData ? (
            <div className="space-y-4">
              {/* Confusion Matrix */}
              <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-gray-300 mb-3">Confusion Matrix</h4>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div></div>
                  <div className="text-center text-gray-400 font-semibold">Predicted Valid</div>
                  <div className="text-center text-gray-400 font-semibold">Predicted Invalid</div>
                  
                  <div className="text-gray-400 font-semibold flex items-center">Actually Valid</div>
                  <div className="text-center bg-green-900/30 border border-green-700 rounded p-3">
                    <div className="text-2xl font-bold text-green-400">
                      {accuracyData.confusion_matrix.true_positive}
                    </div>
                    <div className="text-gray-500 text-xs mt-1">TP</div>
                  </div>
                  <div className="text-center bg-yellow-900/30 border border-yellow-700 rounded p-3">
                    <div className="text-2xl font-bold text-yellow-400">
                      {accuracyData.confusion_matrix.false_negative}
                    </div>
                    <div className="text-gray-500 text-xs mt-1">FN</div>
                  </div>
                  
                  <div className="text-gray-400 font-semibold flex items-center">Actually Invalid</div>
                  <div className="text-center bg-red-900/30 border border-red-700 rounded p-3">
                    <div className="text-2xl font-bold text-red-400">
                      {accuracyData.confusion_matrix.false_positive}
                    </div>
                    <div className="text-gray-500 text-xs mt-1">FP</div>
                  </div>
                  <div className="text-center bg-red-900/30 border border-red-700 rounded p-3">
                    <div className="text-2xl font-bold text-red-400">
                      {accuracyData.confusion_matrix.true_negative}
                    </div>
                    <div className="text-gray-500 text-xs mt-1">TN</div>
                  </div>
                </div>
              </div>
              
              {/* Metrics Cards */}
              <div className="grid grid-cols-4 gap-3">
                <div className="text-center bg-green-900/30 border border-green-700 rounded-lg p-3">
                  <div className="text-3xl font-bold text-green-400">
                    {(accuracyData.metrics.accuracy * 100).toFixed(1)}%
                  </div>
                  <div className="text-gray-400 text-xs mt-1">Overall Accuracy</div>
                  <div className="text-gray-600 text-xs mt-1">Total correctness</div>
                </div>
                <div className="text-center bg-orange-900/30 border border-orange-700 rounded-lg p-3">
                  <div className="text-3xl font-bold text-orange-400">
                    {(accuracyData.metrics.precision * 100).toFixed(1)}%
                  </div>
                  <div className="text-gray-400 text-xs mt-1">Precision</div>
                  <div className="text-gray-600 text-xs mt-1">When ML says "valid"</div>
                </div>
                <div className="text-center bg-red-900/30 border border-red-700 rounded-lg p-3">
                  <div className="text-3xl font-bold text-red-400">
                    {(accuracyData.metrics.recall * 100).toFixed(1)}%
                  </div>
                  <div className="text-gray-400 text-xs mt-1">Recall</div>
                  <div className="text-gray-600 text-xs mt-1">% truly valid caught</div>
                </div>
                <div className="text-center bg-red-900/30 border border-red-700 rounded-lg p-3">
                  <div className="text-3xl font-bold text-red-400">
                    {(accuracyData.metrics.f1_score * 100).toFixed(1)}%
                  </div>
                  <div className="text-gray-400 text-xs mt-1">F1 Score</div>
                  <div className="text-gray-600 text-xs mt-1">Harmonic mean</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="text-7xl mb-4">🔬</div>
                <div className="text-gray-400 text-lg">A/B Testing Not Yet Active</div>
                <div className="text-gray-500 text-sm mt-2">
                  Run some ML validations to trigger A/B testing
                </div>
                <div className="mt-4 text-xs text-gray-600">
                  A/B testing will compare ML predictions vs wargaming ground truth
                </div>
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* Recent Predictions Table */}
      <Card className="p-5 bg-gradient-to-br from-gray-800 to-gray-900 border border-gray-700">
        <h3 className="text-lg font-bold text-red-400 mb-4">
          Recent Predictions (Last 20)
        </h3>
        {predLoading ? (
          <div className="text-center text-gray-400 py-8">
            <div className="text-4xl mb-2 animate-pulse">⏳</div>
            Loading predictions...
          </div>
        ) : recentPredictions && recentPredictions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b-2 border-gray-700">
                  <th className="text-left p-3 text-gray-400 font-semibold">Timestamp</th>
                  <th className="text-left p-3 text-gray-400 font-semibold">CVE ID</th>
                  <th className="text-left p-3 text-gray-400 font-semibold">Patch ID</th>
                  <th className="text-left p-3 text-gray-400 font-semibold">Method</th>
                  <th className="text-left p-3 text-gray-400 font-semibold">Confidence</th>
                  <th className="text-left p-3 text-gray-400 font-semibold">Result</th>
                  <th className="text-left p-3 text-gray-400 font-semibold">Time</th>
                </tr>
              </thead>
              <tbody>
                {recentPredictions.map((pred, i) => (
                  <tr key={i} className="border-b border-gray-800 hover:bg-gray-800/50 transition-colors">
                    <td className="p-3 text-gray-300 font-mono text-xs">
                      {new Date(pred.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="p-3">
                      <code className="text-red-400 text-xs bg-red-900/30 px-2 py-1 rounded">
                        {pred.cve_id}
                      </code>
                    </td>
                    <td className="p-3">
                      <code className="text-red-400 text-xs bg-red-900/30 px-2 py-1 rounded">
                        {pred.patch_id}
                      </code>
                    </td>
                    <td className="p-3">
                      <Badge className={`${
                        pred.method === 'ml' ? 'bg-green-600 hover:bg-green-700' :
                        pred.method === 'wargaming' ? 'bg-yellow-600 hover:bg-yellow-700' :
                        'bg-orange-600 hover:bg-orange-700'
                      } font-semibold`}>
                        {pred.method}
                      </Badge>
                    </td>
                    <td className="p-3 text-gray-300 font-mono">
                      {(pred.confidence * 100).toFixed(1)}%
                    </td>
                    <td className="p-3">
                      <Badge className={`${
                        pred.validated ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'
                      } font-semibold`}>
                        {pred.validated ? '✓ Valid' : '✗ Invalid'}
                      </Badge>
                    </td>
                    <td className="p-3 text-gray-300 font-mono text-xs">
                      {pred.execution_time_ms < 1000 
                        ? `${pred.execution_time_ms}ms`
                        : `${(pred.execution_time_ms / 1000).toFixed(1)}s`
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center text-gray-400 py-8">
            <div className="text-6xl mb-4">📊</div>
            <div className="text-lg">No predictions yet</div>
            <div className="text-sm text-gray-500 mt-2">
              Run some ML-first validations to populate this table
            </div>
          </div>
        )}
      </Card>

      {/* System Status Footer */}
      <Card className="p-4 bg-gradient-to-r from-red-900/30 to-green-900/30 border-2 border-red-500/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="text-green-400 animate-pulse text-2xl">● ACTIVE</div>
            <div className="text-gray-300 font-semibold">
              Oráculo → Eureka → Crisol → ML Pipeline
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-gray-400 text-sm">
              Model: Random Forest v1.0
            </div>
            <div className="text-gray-400 text-sm">
              Next retrain: Phase 5.6
            </div>
          </div>
        </div>
      </Card>
      </>
      ) : activeTab === 'ab-testing' ? (
        <div className="space-y-6">
          <Card className="p-8 bg-gradient-to-br from-orange-900/20 to-red-900/20 border-2 border-orange-500 text-center">
            <div className="text-6xl mb-4">🧪</div>
            <h3 className="text-2xl font-bold text-orange-400 mb-2">A/B Testing Dashboard</h3>
            <p className="text-gray-400 mb-4">
              Coming in Phase 5.8: Real-time comparison of ML vs Wargaming accuracy
            </p>
            <p className="text-sm text-gray-500">
              This tab will display A/B test results, confusion matrices, and model performance metrics
            </p>
          </Card>
        </div>
      ) : null}
    </div>
  );
};
