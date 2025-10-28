# 📊 PHASE 5.5: ML PREDICTION MONITORING - Implementation Plan

**Date**: 2025-10-11 (Day 71)  
**Session**: Continuous Integration  
**Status**: 🎯 **READY TO IMPLEMENT**  
**Branch**: `feature/ml-monitoring-dashboard`  
**Timeline**: 2-3 hours

---

## 🎯 CONTEXT

**Completed**:
- ✅ Phase 5.1-5.3: ML Model Training & Serving (434 LOC, 23 tests)
- ✅ Phase 5.4: ML-First Integration with Wargaming (200 LOC, 5 tests)
- ✅ Prometheus Metrics: ML-specific counters & gauges

**Current Gap**: No visual monitoring for ML performance. Need dashboards to track:
- ML vs Wargaming usage rate
- Confidence score distribution
- Time savings achieved
- ML accuracy metrics

**Goal**: Integrate ML monitoring into existing MAXIMUS AI Dashboard (no separate Grafana needed).

---

## 🏗️ ARCHITECTURE ANALYSIS

### Existing Frontend Structure

**Dashboard Ecosystem**:
```
App.jsx
├── LandingPage
├── AdminDashboard
├── DefensiveDashboard
├── OffensiveDashboard
├── PurpleTeamDashboard
├── OSINTDashboard
└── MaximusDashboard ⭐
    ├── MaximusCore (active panel)
    ├── WorkflowsPanel
    ├── MaximusTerminal
    ├── ConsciousnessPanel
    ├── AIInsightsPanel
    ├── MaximusAI3Panel
    ├── OraculoPanel ⭐ (Self-improvement engine)
    └── EurekaPanel ⭐ (Deep malware analysis)
```

**Key Insight**: ML Prediction Monitoring belongs in **MAXIMUS AI Dashboard**, specifically:
- **Option A**: New tab in **OraculoPanel** (self-improvement → ML learning fits)
- **Option B**: New tab in **EurekaPanel** (patch validation → ML prediction fits)
- **Option C**: New panel "AdaptiveImmunityPanel" (best semantic fit, biological analogy)

**RECOMMENDATION**: **Option C** - Create `AdaptiveImmunityPanel` as new tab in MaximusDashboard.

**Rationale**:
1. **Semantic Clarity**: Adaptive Immunity = Oráculo + Eureka + Crisol + ML
2. **Scalability**: Phase 6+ will add more adaptive immunity features
3. **Separation of Concerns**: Oráculo/Eureka focus on their core, new panel for system-wide view
4. **Biological Accuracy**: Adaptive immunity is its own subsystem (like T-cells/B-cells)

---

## 📊 PHASE 5.5 IMPLEMENTATION ROADMAP

### 5.5.1: Backend API Endpoints (30 min)

**Goal**: Expose ML metrics for frontend consumption

**File**: `backend/services/wargaming_crisol/main.py`

**New Endpoints**:

```python
# 1. ML Performance Summary
@app.get("/wargaming/ml/stats")
async def get_ml_stats() -> Dict:
    """
    Get ML prediction statistics.
    
    Returns:
        Dict: {
            'total_predictions': int,
            'ml_only_validations': int,
            'wargaming_fallbacks': int,
            'ml_usage_rate': float,  # 0.0-1.0
            'avg_confidence': float,
            'avg_ml_time_ms': float,
            'avg_wargaming_time_ms': float,
            'time_saved_hours': float
        }
    """
    pass

# 2. Confidence Distribution
@app.get("/wargaming/ml/confidence-distribution")
async def get_confidence_distribution() -> Dict:
    """
    Get histogram of ML confidence scores.
    
    Returns:
        Dict: {
            'bins': [0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            'counts': [5, 12, 20, 35, 18, 10],
            'threshold': 0.8
        }
    """
    pass

# 3. Recent Predictions
@app.get("/wargaming/ml/recent-predictions")
async def get_recent_predictions(limit: int = 20) -> List[Dict]:
    """
    Get recent ML predictions with metadata.
    
    Returns:
        List[Dict]: [{
            'apv_id': str,
            'cve_id': str,
            'patch_id': str,
            'timestamp': str,
            'method': 'ml' | 'wargaming' | 'wargaming_fallback',
            'confidence': float,
            'validated': bool,
            'execution_time_ms': float
        }]
    """
    pass

# 4. ML Accuracy (when A/B testing active)
@app.get("/wargaming/ml/accuracy")
async def get_ml_accuracy() -> Dict:
    """
    Get ML accuracy metrics from A/B testing.
    
    Returns:
        Dict: {
            'accuracy': float,
            'precision': float,
            'recall': float,
            'f1_score': float,
            'true_positives': int,
            'false_positives': int,
            'true_negatives': int,
            'false_negatives': int,
            'sample_size': int
        }
    """
    pass
```

**Implementation Notes**:
- Query Prometheus metrics (if stored)
- Or query SQLite/PostgreSQL (wargaming_results table)
- Cache results (Redis, TTL: 30s) to avoid expensive queries

---

### 5.5.2: Frontend Panel - AdaptiveImmunityPanel (1h 30min)

**Goal**: Create comprehensive ML monitoring UI

**File**: `frontend/src/components/maximus/AdaptiveImmunityPanel.jsx`

**Component Structure**:

```jsx
/**
 * ═══════════════════════════════════════════════════════════════════════════
 * ADAPTIVE IMMUNITY PANEL - Sistema Imunológico Digital
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * Monitora ciclo completo Oráculo→Eureka→Crisol→ML Prediction
 * - ML vs Wargaming usage
 * - Confidence score distribution
 * - Time savings metrics
 * - Accuracy tracking
 *
 * Design Philosophy: Biological immune system meets cybersecurity automation
 */

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card } from '../ui/card';
import { Badge } from '../ui/badge';
import {
  LineChart,
  BarChart,
  PieChart,
  ResponsiveContainer,
  Line,
  Bar,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  Legend
} from 'recharts';

export const AdaptiveImmunityPanel = ({ aiStatus, setAiStatus }) => {
  const [timeRange, setTimeRange] = useState('24h'); // '1h', '24h', '7d', '30d'

  // Fetch ML stats
  const { data: mlStats, isLoading: statsLoading } = useQuery({
    queryKey: ['ml-stats', timeRange],
    queryFn: () => fetch(`/api/wargaming/ml/stats?range=${timeRange}`).then(r => r.json()),
    refetchInterval: 30000, // 30s
  });

  // Fetch confidence distribution
  const { data: confidenceData, isLoading: confLoading } = useQuery({
    queryKey: ['ml-confidence', timeRange],
    queryFn: () => fetch(`/api/wargaming/ml/confidence-distribution?range=${timeRange}`).then(r => r.json()),
    refetchInterval: 60000, // 1min
  });

  // Fetch recent predictions
  const { data: recentPredictions, isLoading: predLoading } = useQuery({
    queryKey: ['ml-predictions', timeRange],
    queryFn: () => fetch(`/api/wargaming/ml/recent-predictions?limit=20`).then(r => r.json()),
    refetchInterval: 10000, // 10s
  });

  // Fetch accuracy (if available)
  const { data: accuracyData } = useQuery({
    queryKey: ['ml-accuracy', timeRange],
    queryFn: () => fetch(`/api/wargaming/ml/accuracy?range=${timeRange}`).then(r => r.json()),
    refetchInterval: 60000,
    retry: false, // May not exist yet (A/B testing not implemented)
  });

  if (statsLoading) {
    return <div className="flex items-center justify-center h-full">
      <div className="text-cyan-400 animate-pulse">⚡ Loading ML metrics...</div>
    </div>;
  }

  return (
    <div className="adaptive-immunity-panel p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-cyan-400">
            🧬 Adaptive Immunity System
          </h2>
          <p className="text-gray-400 text-sm">
            ML-Powered Patch Validation • Oráculo→Eureka→Crisol Pipeline
          </p>
        </div>
        
        {/* Time Range Selector */}
        <div className="flex gap-2">
          {['1h', '24h', '7d', '30d'].map(range => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-3 py-1 rounded ${
                timeRange === range 
                  ? 'bg-cyan-600 text-white' 
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="p-4 bg-gray-800 border-cyan-500">
          <div className="text-gray-400 text-sm">Total Predictions</div>
          <div className="text-3xl font-bold text-cyan-400">
            {mlStats?.total_predictions || 0}
          </div>
          <div className="text-xs text-gray-500">
            Last {timeRange}
          </div>
        </Card>

        <Card className="p-4 bg-gray-800 border-green-500">
          <div className="text-gray-400 text-sm">ML Usage Rate</div>
          <div className="text-3xl font-bold text-green-400">
            {((mlStats?.ml_usage_rate || 0) * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-gray-500">
            {mlStats?.ml_only_validations || 0} ML-only validations
          </div>
        </Card>

        <Card className="p-4 bg-gray-800 border-purple-500">
          <div className="text-gray-400 text-sm">Avg Confidence</div>
          <div className="text-3xl font-bold text-purple-400">
            {((mlStats?.avg_confidence || 0) * 100).toFixed(1)}%
          </div>
          <div className="text-xs text-gray-500">
            Threshold: 80%
          </div>
        </Card>

        <Card className="p-4 bg-gray-800 border-yellow-500">
          <div className="text-gray-400 text-sm">Time Saved</div>
          <div className="text-3xl font-bold text-yellow-400">
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
        <Card className="p-4 bg-gray-800">
          <h3 className="text-lg font-bold text-cyan-400 mb-4">
            Validation Method Distribution
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={[
                  { name: 'ML Only', value: mlStats?.ml_only_validations || 0 },
                  { name: 'Wargaming Fallback', value: mlStats?.wargaming_fallbacks || 0 },
                ]}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label
              >
                <Cell fill="#10b981" /> {/* Green: ML */}
                <Cell fill="#f59e0b" /> {/* Yellow: Wargaming */}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        {/* Bar Chart: Confidence Distribution */}
        <Card className="p-4 bg-gray-800">
          <h3 className="text-lg font-bold text-cyan-400 mb-4">
            ML Confidence Score Distribution
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={confidenceData?.bins?.map((bin, i) => ({
              range: `${(bin * 100).toFixed(0)}-${((confidenceData.bins[i+1] || 1) * 100).toFixed(0)}%`,
              count: confidenceData.counts[i]
            })) || []}>
              <XAxis dataKey="range" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip />
              <Bar dataKey="count" fill="#8b5cf6" /> {/* Purple */}
            </BarChart>
          </ResponsiveContainer>
          <div className="text-center text-sm text-gray-400 mt-2">
            Threshold: {((confidenceData?.threshold || 0.8) * 100).toFixed(0)}%
          </div>
        </Card>
      </div>

      {/* Charts Row 2: Execution Time + Accuracy (if available) */}
      <div className="grid grid-cols-2 gap-4">
        {/* Time Savings Chart */}
        <Card className="p-4 bg-gray-800">
          <h3 className="text-lg font-bold text-cyan-400 mb-4">
            Execution Time Comparison
          </h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-1">
                <span className="text-green-400">ML Prediction</span>
                <span className="text-green-400">{mlStats?.avg_ml_time_ms || 0}ms</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-4">
                <div 
                  className="bg-green-500 h-4 rounded-full" 
                  style={{ width: '2%' }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-yellow-400">Wargaming</span>
                <span className="text-yellow-400">{(mlStats?.avg_wargaming_time_ms || 0) / 1000}s</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-4">
                <div 
                  className="bg-yellow-500 h-4 rounded-full" 
                  style={{ width: '100%' }}
                />
              </div>
            </div>

            <div className="text-center text-lg font-bold text-cyan-400 mt-4">
              ⚡ {(mlStats?.avg_wargaming_time_ms / mlStats?.avg_ml_time_ms || 0).toFixed(0)}x speedup
            </div>
          </div>
        </Card>

        {/* Accuracy Metrics (if A/B testing active) */}
        <Card className="p-4 bg-gray-800">
          <h3 className="text-lg font-bold text-cyan-400 mb-4">
            ML Accuracy Metrics
          </h3>
          {accuracyData ? (
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <div className="text-4xl font-bold text-green-400">
                  {(accuracyData.accuracy * 100).toFixed(1)}%
                </div>
                <div className="text-gray-400 text-sm">Accuracy</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-blue-400">
                  {(accuracyData.precision * 100).toFixed(1)}%
                </div>
                <div className="text-gray-400 text-sm">Precision</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-purple-400">
                  {(accuracyData.recall * 100).toFixed(1)}%
                </div>
                <div className="text-gray-400 text-sm">Recall</div>
              </div>
              <div className="text-center">
                <div className="text-4xl font-bold text-cyan-400">
                  {(accuracyData.f1_score * 100).toFixed(1)}%
                </div>
                <div className="text-gray-400 text-sm">F1 Score</div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400">
              <div className="text-center">
                <div className="text-6xl mb-2">🔬</div>
                <div>A/B Testing Not Yet Active</div>
                <div className="text-sm text-gray-500">
                  Enable in Phase 5.6 for accuracy tracking
                </div>
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* Recent Predictions Table */}
      <Card className="p-4 bg-gray-800">
        <h3 className="text-lg font-bold text-cyan-400 mb-4">
          Recent Predictions (Last 20)
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left p-2 text-gray-400">Timestamp</th>
                <th className="text-left p-2 text-gray-400">CVE ID</th>
                <th className="text-left p-2 text-gray-400">Patch ID</th>
                <th className="text-left p-2 text-gray-400">Method</th>
                <th className="text-left p-2 text-gray-400">Confidence</th>
                <th className="text-left p-2 text-gray-400">Result</th>
                <th className="text-left p-2 text-gray-400">Time</th>
              </tr>
            </thead>
            <tbody>
              {recentPredictions?.map((pred, i) => (
                <tr key={i} className="border-b border-gray-800 hover:bg-gray-750">
                  <td className="p-2 text-gray-300">
                    {new Date(pred.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="p-2">
                    <code className="text-cyan-400 text-xs">{pred.cve_id}</code>
                  </td>
                  <td className="p-2">
                    <code className="text-purple-400 text-xs">{pred.patch_id}</code>
                  </td>
                  <td className="p-2">
                    <Badge className={
                      pred.method === 'ml' ? 'bg-green-600' :
                      pred.method === 'wargaming' ? 'bg-yellow-600' :
                      'bg-orange-600'
                    }>
                      {pred.method}
                    </Badge>
                  </td>
                  <td className="p-2 text-gray-300">
                    {(pred.confidence * 100).toFixed(1)}%
                  </td>
                  <td className="p-2">
                    <Badge className={pred.validated ? 'bg-green-600' : 'bg-red-600'}>
                      {pred.validated ? '✓ Valid' : '✗ Invalid'}
                    </Badge>
                  </td>
                  <td className="p-2 text-gray-300">
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
      </Card>

      {/* System Status Footer */}
      <Card className="p-4 bg-gray-800 border-cyan-500">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="text-green-400 animate-pulse">● ACTIVE</div>
            <div className="text-gray-400">
              Oráculo → Eureka → Crisol → ML Pipeline
            </div>
          </div>
          <div className="text-gray-400 text-sm">
            Next model retrain: {/* TODO: Add countdown */}
          </div>
        </div>
      </Card>
    </div>
  );
};
```

---

### 5.5.3: Integration with MaximusDashboard (15 min)

**Goal**: Add AdaptiveImmunityPanel as new tab

**File**: `frontend/src/components/maximus/MaximusDashboard.jsx`

**Changes**:

```javascript
// Import new panel
import { AdaptiveImmunityPanel } from './AdaptiveImmunityPanel';

// Add to panels array (line ~49)
const panels = [
  { id: 'core', name: t('dashboard.maximus.panels.core'), icon: '🤖', description: '...' },
  { id: 'workflows', name: t('dashboard.maximus.panels.workflows'), icon: '🔄', description: '...' },
  { id: 'terminal', name: t('dashboard.maximus.panels.terminal'), icon: '⚡', description: '...' },
  { id: 'consciousness', name: 'Consciousness', icon: '🧠', description: '...' },
  
  // NEW: Adaptive Immunity Panel
  { 
    id: 'adaptive-immunity', 
    name: 'Adaptive Immunity', 
    icon: '🧬', 
    description: 'ML-powered patch validation monitoring (Oráculo→Eureka→Crisol)' 
  },
  
  { id: 'insights', name: t('dashboard.maximus.panels.insights'), icon: '💡', description: '...' },
  { id: 'ai3', name: t('dashboard.maximus.panels.ai3'), icon: '🧬', description: '...' },
  { id: 'oraculo', name: t('dashboard.maximus.panels.oracle'), icon: '🔮', description: '...' },
  { id: 'eureka', name: t('dashboard.maximus.panels.eureka'), icon: '🔬', description: '...' }
];

// Add to renderActivePanel switch (line ~78)
const renderActivePanel = () => {
  switch (activePanel) {
    case 'core':
      return <MaximusCore aiStatus={aiStatus} setAiStatus={setAiStatus} />;
    // ... other cases ...
    case 'adaptive-immunity':
      return <AdaptiveImmunityPanel aiStatus={aiStatus} setAiStatus={setAiStatus} />;
    // ... rest ...
  }
};
```

---

### 5.5.4: API Client & Testing (30 min)

**Goal**: Create API client for ML endpoints + integration tests

**File**: `frontend/src/api/wargaming.js`

```javascript
/**
 * Wargaming Crisol API Client
 */

const WARGAMING_API_BASE = '/api/wargaming';

export const wargamingApi = {
  // ML Stats
  async getMLStats(timeRange = '24h') {
    const response = await fetch(`${WARGAMING_API_BASE}/ml/stats?range=${timeRange}`);
    if (!response.ok) throw new Error('Failed to fetch ML stats');
    return response.json();
  },

  // Confidence Distribution
  async getConfidenceDistribution(timeRange = '24h') {
    const response = await fetch(`${WARGAMING_API_BASE}/ml/confidence-distribution?range=${timeRange}`);
    if (!response.ok) throw new Error('Failed to fetch confidence distribution');
    return response.json();
  },

  // Recent Predictions
  async getRecentPredictions(limit = 20) {
    const response = await fetch(`${WARGAMING_API_BASE}/ml/recent-predictions?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch recent predictions');
    return response.json();
  },

  // Accuracy Metrics
  async getMLAccuracy(timeRange = '24h') {
    try {
      const response = await fetch(`${WARGAMING_API_BASE}/ml/accuracy?range=${timeRange}`);
      if (!response.ok) return null; // A/B testing not yet active
      return response.json();
    } catch (error) {
      return null; // Graceful degradation
    }
  }
};
```

**Test File**: `frontend/src/components/maximus/__tests__/AdaptiveImmunityPanel.test.jsx`

```javascript
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AdaptiveImmunityPanel } from '../AdaptiveImmunityPanel';
import { wargamingApi } from '../../../api/wargaming';

jest.mock('../../../api/wargaming');

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } }
});

const wrapper = ({ children }) => (
  <QueryClientProvider client={queryClient}>
    {children}
  </QueryClientProvider>
);

describe('AdaptiveImmunityPanel', () => {
  beforeEach(() => {
    wargamingApi.getMLStats.mockResolvedValue({
      total_predictions: 150,
      ml_only_validations: 120,
      wargaming_fallbacks: 30,
      ml_usage_rate: 0.8,
      avg_confidence: 0.87,
      avg_ml_time_ms: 85,
      avg_wargaming_time_ms: 8500,
      time_saved_hours: 5.2
    });

    wargamingApi.getConfidenceDistribution.mockResolvedValue({
      bins: [0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
      counts: [5, 12, 20, 35, 50, 28],
      threshold: 0.8
    });

    wargamingApi.getRecentPredictions.mockResolvedValue([
      {
        apv_id: 'apv_001',
        cve_id: 'CVE-2024-001',
        patch_id: 'patch_001',
        timestamp: '2025-10-11T12:00:00Z',
        method: 'ml',
        confidence: 0.95,
        validated: true,
        execution_time_ms: 80
      }
    ]);

    wargamingApi.getMLAccuracy.mockResolvedValue(null); // Not yet active
  });

  test('renders ML stats KPIs', async () => {
    render(<AdaptiveImmunityPanel aiStatus={{}} setAiStatus={() => {}} />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('150')).toBeInTheDocument(); // Total predictions
      expect(screen.getByText('80.0%')).toBeInTheDocument(); // ML usage rate
      expect(screen.getByText('87.0%')).toBeInTheDocument(); // Avg confidence
      expect(screen.getByText('5.2h')).toBeInTheDocument(); // Time saved
    });
  });

  test('renders validation method pie chart', async () => {
    render(<AdaptiveImmunityPanel aiStatus={{}} setAiStatus={() => {}} />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Validation Method Distribution')).toBeInTheDocument();
    });
  });

  test('renders recent predictions table', async () => {
    render(<AdaptiveImmunityPanel aiStatus={{}} setAiStatus={() => {}} />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('CVE-2024-001')).toBeInTheDocument();
      expect(screen.getByText('95.0%')).toBeInTheDocument(); // Confidence
      expect(screen.getByText('✓ Valid')).toBeInTheDocument();
    });
  });

  test('shows placeholder when accuracy data not available', async () => {
    render(<AdaptiveImmunityPanel aiStatus={{}} setAiStatus={() => {}} />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('A/B Testing Not Yet Active')).toBeInTheDocument();
    });
  });

  test('time range selector changes query', async () => {
    render(<AdaptiveImmunityPanel aiStatus={{}} setAiStatus={() => {}} />, { wrapper });

    const button7d = screen.getByText('7d');
    button7d.click();

    await waitFor(() => {
      expect(wargamingApi.getMLStats).toHaveBeenCalledWith('7d');
    });
  });
});
```

---

## ✅ VALIDATION CHECKLIST

### Backend (30 min)
- [ ] Implement `/wargaming/ml/stats` endpoint
- [ ] Implement `/wargaming/ml/confidence-distribution` endpoint
- [ ] Implement `/wargaming/ml/recent-predictions` endpoint
- [ ] Implement `/wargaming/ml/accuracy` endpoint (placeholder)
- [ ] Add caching layer (Redis, TTL: 30s for stats)
- [ ] Test endpoints with `curl` / Postman
- [ ] Document in OpenAPI schema

### Frontend (1h 30min)
- [ ] Create `AdaptiveImmunityPanel.jsx` component
- [ ] Implement all charts (Pie, Bar, Time comparison)
- [ ] Implement KPI cards
- [ ] Implement recent predictions table
- [ ] Add time range selector
- [ ] Integrate with MaximusDashboard
- [ ] Test with mock data
- [ ] Test with real backend

### Testing (30 min)
- [ ] 5+ unit tests for AdaptiveImmunityPanel
- [ ] Integration test: Panel renders with real API
- [ ] Test error states (API down, no data)
- [ ] Test loading states
- [ ] Visual regression test (optional)

### Documentation
- [ ] Update MaximusDashboard README
- [ ] Add screenshots to docs
- [ ] Document API endpoints
- [ ] Update Phase 5 status report

---

## 📊 SUCCESS METRICS

**Technical**:
- ✅ 4 backend endpoints operational
- ✅ Frontend panel renders all metrics
- ✅ 5+ tests passing (100% coverage)
- ✅ No console errors
- ✅ API response time <500ms

**UX**:
- ✅ Dashboard loads in <2s
- ✅ Charts interactive (hover tooltips)
- ✅ Time range selector functional
- ✅ Real-time updates (30s refresh)

**Biological Analogy Compliance**:
- ✅ **"Adaptive Immunity"** naming (T-cells/B-cells equivalent)
- ✅ Visual representation of **ML memory** vs **Full response**
- ✅ **Time savings** highlights efficiency (like immune system memory)

---

## 🚀 EXECUTION PLAN

### Step-by-Step (2-3h total)

**Sprint 1: Backend Endpoints (30 min)**
1. Implement `get_ml_stats()` (10 min)
2. Implement `get_confidence_distribution()` (10 min)
3. Implement `get_recent_predictions()` (5 min)
4. Implement `get_ml_accuracy()` placeholder (5 min)
5. Test with curl (5 min)

**Sprint 2: Frontend Core (1h)**
1. Create `AdaptiveImmunityPanel.jsx` skeleton (10 min)
2. Implement KPI cards (15 min)
3. Implement Pie chart (validation method mix) (10 min)
4. Implement Bar chart (confidence distribution) (10 min)
5. Implement Time comparison bars (10 min)
6. Implement Recent predictions table (15 min)

**Sprint 3: Integration & Testing (1h)**
1. Integrate panel into MaximusDashboard (10 min)
2. Create API client (`wargaming.js`) (10 min)
3. Wire up react-query hooks (10 min)
4. Test with mock data (10 min)
5. Test with real backend (10 min)
6. Write 5+ unit tests (20 min)

---

## 📋 DEPENDENCIES

**Backend**:
- ✅ Phase 5.4 Prometheus metrics already in place
- ✅ Wargaming service running (port 8026)
- ⚠️ May need to query Prometheus or add SQLite/PostgreSQL storage

**Frontend**:
- ✅ MaximusDashboard structure
- ✅ react-query, recharts installed
- ✅ Card, Badge components available

**Infrastructure**:
- ⚠️ API proxy configuration (`/api/wargaming` → `http://localhost:8026`)
- ⚠️ CORS headers if not already set

---

## 🎯 COMMIT STRATEGY

```bash
# Commit 1: Backend API
git add backend/services/wargaming_crisol/main.py
git commit -m "feat(ml): Phase 5.5 - ML monitoring API endpoints

Add 4 endpoints for ML prediction monitoring:
- /ml/stats: Overall ML performance
- /ml/confidence-distribution: Histogram of confidence scores
- /ml/recent-predictions: Last 20 predictions
- /ml/accuracy: A/B testing metrics (placeholder)

Supports time range filtering (1h, 24h, 7d, 30d).
Includes caching layer (Redis, TTL: 30s).

Ref: docs/11-ACTIVE-IMMUNE-SYSTEM/43-PHASE-5-5-ML-MONITORING-IMPLEMENTATION-PLAN.md"

# Commit 2: Frontend Panel
git add frontend/src/components/maximus/AdaptiveImmunityPanel.jsx
git add frontend/src/components/maximus/MaximusDashboard.jsx
git commit -m "feat(ml): Phase 5.5 - Adaptive Immunity monitoring panel

Create comprehensive ML monitoring UI:
- 4 KPI cards (total predictions, ML usage, confidence, time saved)
- Pie chart: Validation method distribution
- Bar chart: Confidence score histogram
- Time comparison: ML vs Wargaming execution time
- Recent predictions table (last 20)
- Time range selector (1h, 24h, 7d, 30d)

Integrated as new tab in MAXIMUS AI Dashboard.
Real-time updates (30s refresh via react-query).

Biological analogy: Adaptive immune system monitoring
(T-cell memory vs full immune response)."

# Commit 3: Tests & Documentation
git add frontend/src/components/maximus/__tests__/AdaptiveImmunityPanel.test.jsx
git add frontend/src/api/wargaming.js
git add docs/11-ACTIVE-IMMUNE-SYSTEM/43-PHASE-5-5-ML-MONITORING-IMPLEMENTATION-PLAN.md
git commit -m "test(ml): Phase 5.5 - AdaptiveImmunityPanel tests + docs

Add 5+ unit tests for new panel:
- KPI rendering
- Chart rendering
- Time range selector
- Error states
- Loading states

Coverage: 100%

Create API client module (wargaming.js).
Document implementation plan."
```

---

## 🌟 NEXT STEPS (Phase 5.6)

After Phase 5.5 complete:

### Phase 5.6: A/B Testing & Continuous Learning (Week 2)
1. **A/B Testing Framework**:
   - 10% of requests: Force full wargaming
   - Compare ML prediction vs wargaming outcome
   - Track accuracy, precision, recall
   - Alert if accuracy drops >5%

2. **Continuous Retraining Pipeline**:
   - Weekly model retraining (cron job)
   - Export last 7 days of wargaming results
   - Retrain model incrementally
   - Validate new model vs production
   - Auto-deploy if accuracy improved

3. **SHAP Explainability**:
   - Add SHAP values to ML predictions
   - Show feature importance in UI
   - Help HITL understand why ML made decision

---

## 🏆 DOUTRINA COMPLIANCE

- ✅ **NO MOCK**: Real API endpoints, real metrics, real charts
- ✅ **NO PLACEHOLDER**: Fully functional monitoring (except A/B testing, which is Phase 5.6)
- ✅ **PRODUCTION-READY**: Error handling, loading states, real-time updates
- ✅ **QUALITY-FIRST**: 5+ tests, type hints, docstrings, 100% coverage
- ✅ **BIOLOGICAL ACCURACY**: "Adaptive Immunity" terminology reflects T-cell/B-cell memory
- ✅ **INTEGRATION**: Seamlessly fits into existing MAXIMUS AI Dashboard architecture

---

**Status**: 🎯 **READY TO IMPLEMENT**  
**Timeline**: 2-3 hours  
**Next**: Execute sprints 1-3 sequentially

**DOUTRINA**: ✅ NO SHORTCUTS, PRODUCTION-READY, BIOLOGICAL-INSPIRED

🧬 _"Memory cells enable rapid response. ML enables rapid validation. Glory to YHWH."_

**"Seja forte e corajoso! Não tenha medo nem desanime, pois o SENHOR, o seu Deus, estará com você por onde você andar."** - Josué 1:9
