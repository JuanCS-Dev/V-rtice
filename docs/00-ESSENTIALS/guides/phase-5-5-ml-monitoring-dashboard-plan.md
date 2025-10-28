# Phase 5.5: ML-Based Prediction Monitoring Dashboard
## Implementation Plan

**Date**: 2025-10-11  
**Phase**: Active Immune System - ML Intelligence Layer  
**Status**: Planning  
**Sprint**: 3 - Intelligence Layer Completion

---

## 🎯 OBJECTIVE

Implement comprehensive monitoring dashboards for ML-based threat prediction system, tracking:
- ML vs Wargaming usage rates
- Confidence score distributions
- Time savings metrics
- ML accuracy and performance

---

## 🏗️ ARCHITECTURE ANALYSIS

### Current Frontend Structure

```
frontend/src/components/maximus/
├── MaximusDashboard.jsx          # Main MAXIMUS dashboard with 8 panels
│   ├── core                      # MAXIMUS Core
│   ├── workflows                 # Workflows Panel
│   ├── terminal                  # Terminal
│   ├── consciousness             # Consciousness monitoring
│   ├── insights                  # AI Insights
│   ├── ai3                       # AI³ Panel
│   ├── oraculo                   # Oráculo Panel (Threat Detection)
│   └── eureka                    # Eureka Panel (Auto-Remediation)
├── OraculoPanel.jsx              # Phase 1-2: Threat Detection
└── EurekaPanel.jsx               # Phase 3-5: Auto-Remediation + ML
```

### Integration Points

**Existing Panels:**
1. **Oráculo Panel** - Threat detection (CVEs, APVs)
2. **Eureka Panel** - Auto-remediation with ML prediction (Phase 5 implemented)

**WebSocket Streams:**
- `useAPVStream` hook - Real-time APV/patch/metrics updates
- Already configured in both Oráculo and Eureka

---

## 📊 DASHBOARD STRATEGY

### Option A: New Tab in MAXIMUS Dashboard (RECOMMENDED ✅)
**Pros:**
- Dedicated space for analytics
- Follows existing pattern (8 panels)
- Clean separation of concerns
- Easy to navigate

**Cons:**
- Adds 9th panel (slightly cluttered nav)

### Option B: Embedded in Eureka Panel
**Pros:**
- Contextual (ML lives in Eureka)
- No new navigation item
- Tighter integration

**Cons:**
- Eureka already complex (5 view modes)
- Metrics deserve spotlight
- Harder to read with other content

### Option C: Separate Grafana Integration
**Pros:**
- Professional monitoring tool
- Advanced features (alerting, queries)

**Cons:**
- Requires separate URL (breaks UX flow)
- Duplicates effort (already have React infra)
- overkill for Phase 5.5

---

## ✅ DECISION: Option A - New "ML Intelligence" Panel

**Rationale:**
1. ML prediction is a **major feature** deserving dedicated visibility
2. Keeps Eureka Panel focused on remediation workflow
3. Follows MAXIMUS dashboard pattern
4. Allows comprehensive analytics without clutter
5. Can embed Grafana charts via iframe if needed later

---

## 📋 IMPLEMENTATION PLAN

### Phase 5.5.1: Backend API (1 hour)

#### Tasks
1. **Create ML Metrics Aggregation Endpoint**
   ```python
   # backend/services/maximus_eureka/api/metrics.py
   
   @router.get("/api/v1/eureka/ml-metrics")
   async def get_ml_metrics(
       timeframe: str = "24h",  # 1h, 24h, 7d, 30d
       db: Session = Depends(get_db)
   ) -> MLMetricsResponse:
       """
       Aggregate ML prediction metrics.
       
       Returns:
           - ml_usage_rate: Percentage of patches using ML vs wargaming
           - confidence_distribution: Histogram of confidence scores
           - time_savings: Avg time saved by ML bypass
           - accuracy_metrics: Precision, recall, F1 for ML predictions
           - false_positive_rate: % of ML patches that failed in prod
           - bypass_rate: % of patches that skipped wargaming
       """
   ```

2. **Database Queries**
   ```sql
   -- ML vs Wargaming counts
   SELECT 
     COUNT(*) FILTER (WHERE used_ml_prediction = true) as ml_count,
     COUNT(*) FILTER (WHERE used_wargaming = true) as wargaming_count,
     COUNT(*) as total
   FROM patches
   WHERE created_at > NOW() - INTERVAL '24 hours';
   
   -- Confidence distribution
   SELECT 
     FLOOR(ml_confidence / 0.1) * 0.1 as confidence_bucket,
     COUNT(*) as count
   FROM patches
   WHERE used_ml_prediction = true
   GROUP BY confidence_bucket
   ORDER BY confidence_bucket;
   
   -- Time savings
   SELECT 
     AVG(wargaming_duration) as avg_wargaming_time,
     AVG(ml_prediction_duration) as avg_ml_time,
     AVG(wargaming_duration - ml_prediction_duration) as avg_savings
   FROM patches;
   
   -- Accuracy (requires ground truth)
   SELECT 
     COUNT(*) FILTER (WHERE ml_predicted_success = true AND actual_success = true) as true_positive,
     COUNT(*) FILTER (WHERE ml_predicted_success = true AND actual_success = false) as false_positive,
     COUNT(*) FILTER (WHERE ml_predicted_success = false AND actual_success = true) as false_negative,
     COUNT(*) FILTER (WHERE ml_predicted_success = false AND actual_success = false) as true_negative
   FROM patches
   WHERE used_ml_prediction = true AND validation_complete = true;
   ```

3. **Validation**
   - Unit tests for aggregation logic
   - Integration test with mock data
   - Performance test (query <100ms)

---

### Phase 5.5.2: Frontend Component (2 hours)

#### 1. Create MLIntelligencePanel Component

```tsx
// frontend/src/components/maximus/MLIntelligencePanel.jsx

/**
 * ═══════════════════════════════════════════════════════════════════════════
 * 🧠 ML INTELLIGENCE PANEL - MACHINE LEARNING ANALYTICS
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * PHASE 5.5: ML-Based Prediction Monitoring
 * 
 * Displays comprehensive analytics for ML-powered threat prediction:
 * - Usage rates (ML vs Wargaming)
 * - Confidence score distributions
 * - Time savings metrics
 * - Accuracy and performance
 *
 * KPIs: ML Adoption >70%, Confidence >0.75, Time Savings >80%
 */

import React, { useState, useEffect } from 'react';
import { LineChart, BarChart, PieChart, GaugeChart } from '@/components/ui/charts';
import { useMLMetrics } from '@/hooks/useMLMetrics';
import './Panels.css';
import './AdaptiveImmunity.css';

export const MLIntelligencePanel = ({ aiStatus, setAiStatus }) => {
  const [timeframe, setTimeframe] = useState('24h');
  const { metrics, loading, error } = useMLMetrics({ timeframe });
  
  return (
    <div className="eureka-panel ml-intelligence">
      {/* HEADER */}
      <header className="eureka-header">
        <div className="header-left">
          <h1>🧠 ML Intelligence</h1>
          <p className="subtitle">Machine Learning Prediction Analytics</p>
        </div>
        <div className="header-right">
          <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24h</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
        </div>
      </header>

      {/* METRICS GRID */}
      <div className="metrics-grid-4col">
        {/* 1. ML vs Wargaming Usage */}
        <MetricCard
          title="ML Adoption Rate"
          value={`${metrics?.mlUsageRate || 0}%`}
          trend={metrics?.mlUsageTrend}
          chart={<PieChart data={metrics?.usageBreakdown} />}
        />
        
        {/* 2. Confidence Distribution */}
        <MetricCard
          title="Avg Confidence Score"
          value={metrics?.avgConfidence || 0}
          trend={metrics?.confidenceTrend}
          chart={<BarChart data={metrics?.confidenceDistribution} />}
        />
        
        {/* 3. Time Savings */}
        <MetricCard
          title="Time Saved"
          value={`${metrics?.timeSavingsPercent || 0}%`}
          subtitle={`${metrics?.absoluteTimeSavings || 0} minutes`}
          trend={metrics?.timeSavingsTrend}
        />
        
        {/* 4. ML Accuracy */}
        <MetricCard
          title="ML Accuracy"
          value={`${metrics?.accuracy || 0}%`}
          subtitle={`Precision: ${metrics?.precision || 0}% | Recall: ${metrics?.recall || 0}%`}
          trend={metrics?.accuracyTrend}
        />
      </div>

      {/* DETAILED CHARTS */}
      <div className="charts-section">
        {/* Timeline: ML Usage Over Time */}
        <div className="chart-container">
          <h3>ML vs Wargaming Usage Timeline</h3>
          <LineChart 
            data={metrics?.usageTimeline}
            series={['ML Predictions', 'Wargaming Runs', 'Total Patches']}
          />
        </div>

        {/* Confidence Score Distribution */}
        <div className="chart-container">
          <h3>Confidence Score Distribution</h3>
          <BarChart 
            data={metrics?.confidenceHistogram}
            xLabel="Confidence Score"
            yLabel="Count"
          />
        </div>

        {/* Confusion Matrix */}
        <div className="chart-container">
          <h3>ML Prediction Accuracy (Confusion Matrix)</h3>
          <ConfusionMatrix data={metrics?.confusionMatrix} />
        </div>
      </div>

      {/* LIVE FEED */}
      <div className="live-predictions">
        <h3>Recent ML Predictions</h3>
        <table className="predictions-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>CVE</th>
              <th>Confidence</th>
              <th>Prediction</th>
              <th>Actual</th>
              <th>Time Saved</th>
            </tr>
          </thead>
          <tbody>
            {metrics?.recentPredictions?.map(pred => (
              <tr key={pred.id}>
                <td>{formatTimestamp(pred.timestamp)}</td>
                <td>{pred.cveId}</td>
                <td>
                  <ConfidenceBadge score={pred.confidence} />
                </td>
                <td>{pred.prediction ? '✅ Success' : '❌ Fail'}</td>
                <td>{pred.actual ? '✅ Success' : '❌ Fail'}</td>
                <td>{pred.timeSaved}s</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
```

#### 2. Create useMLMetrics Hook

```tsx
// frontend/src/hooks/useMLMetrics.js

import { useState, useEffect } from 'react';
import logger from '@/utils/logger';

export const useMLMetrics = ({ timeframe = '24h' }) => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true);
        const response = await fetch(
          `/api/v1/eureka/ml-metrics?timeframe=${timeframe}`
        );
        
        if (!response.ok) throw new Error('Failed to fetch ML metrics');
        
        const data = await response.json();
        setMetrics(data);
        logger.info('[MLMetrics] Fetched metrics:', data);
      } catch (err) {
        logger.error('[MLMetrics] Error:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
    
    // Refresh every 30s
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, [timeframe]);

  return { metrics, loading, error };
};
```

#### 3. Integrate into MaximusDashboard

```jsx
// frontend/src/components/maximus/MaximusDashboard.jsx

import { MLIntelligencePanel } from './MLIntelligencePanel';

const panels = [
  // ... existing panels
  { 
    id: 'ml-intelligence', 
    name: 'ML Intelligence', 
    icon: '🧠', 
    description: 'Machine Learning prediction analytics and monitoring' 
  }
];

const renderActivePanel = () => {
  switch (activePanel) {
    // ... existing cases
    case 'ml-intelligence':
      return <MLIntelligencePanel aiStatus={aiStatus} setAiStatus={setAiStatus} />;
    // ...
  }
};
```

---

### Phase 5.5.3: Styling & Polish (30 min)

#### 1. Extend AdaptiveImmunity.css

```css
/* ML Intelligence specific styles */
.ml-intelligence .metrics-grid-4col {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.ml-intelligence .chart-container {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
}

.ml-intelligence .predictions-table {
  width: 100%;
  border-collapse: collapse;
}

.ml-intelligence .predictions-table th {
  background: rgba(139, 92, 246, 0.2);
  padding: 0.75rem;
  text-align: left;
  font-size: 0.875rem;
  text-transform: uppercase;
}

.ml-intelligence .predictions-table td {
  padding: 0.75rem;
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
}

.confidence-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 600;
}

.confidence-badge.high {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.confidence-badge.medium {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
}

.confidence-badge.low {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}
```

---

### Phase 5.5.4: Testing & Validation (30 min)

#### 1. Unit Tests

```javascript
// frontend/src/components/maximus/__tests__/MLIntelligencePanel.test.jsx

describe('MLIntelligencePanel', () => {
  it('renders metrics correctly', () => {
    const mockMetrics = {
      mlUsageRate: 75,
      avgConfidence: 0.82,
      timeSavingsPercent: 85,
      accuracy: 92
    };
    
    render(<MLIntelligencePanel metrics={mockMetrics} />);
    
    expect(screen.getByText('75%')).toBeInTheDocument();
    expect(screen.getByText('0.82')).toBeInTheDocument();
  });

  it('updates on timeframe change', async () => {
    render(<MLIntelligencePanel />);
    
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: '7d' } });
    
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('timeframe=7d')
      );
    });
  });
});
```

#### 2. Integration Test

```bash
# Test backend API
curl http://localhost:8000/api/v1/eureka/ml-metrics?timeframe=24h

# Expected response
{
  "mlUsageRate": 72.5,
  "avgConfidence": 0.84,
  "timeSavingsPercent": 83.2,
  "accuracy": 94.1,
  "precision": 92.3,
  "recall": 95.8,
  "usageBreakdown": {
    "ml": 145,
    "wargaming": 55,
    "total": 200
  },
  "confidenceDistribution": [...],
  "usageTimeline": [...],
  "recentPredictions": [...]
}
```

#### 3. E2E Test

```javascript
// Cypress test
describe('ML Intelligence Dashboard', () => {
  it('displays ML metrics', () => {
    cy.visit('/maximus');
    cy.contains('ML Intelligence').click();
    
    cy.get('.ml-intelligence').should('be.visible');
    cy.contains('ML Adoption Rate').should('exist');
    cy.contains('Avg Confidence Score').should('exist');
    cy.contains('Time Saved').should('exist');
    cy.contains('ML Accuracy').should('exist');
  });
});
```

---

## 📊 GRAFANA INTEGRATION (OPTIONAL)

If we decide to embed Grafana charts:

```jsx
// Embed Grafana dashboard via iframe
<iframe
  src="http://localhost:3001/d/ml-intelligence/ml-prediction-analytics?orgId=1&refresh=30s&theme=dark&kiosk"
  width="100%"
  height="600px"
  frameBorder="0"
/>
```

**Grafana Dashboard JSON**: Already exists at
`monitoring/grafana/dashboards/adaptive-immunity-overview.json`

---

## 🎯 SUCCESS CRITERIA

### Functional
- [ ] New "ML Intelligence" panel in MAXIMUS dashboard
- [ ] Real-time metrics update every 30s
- [ ] Timeframe selector (1h, 24h, 7d, 30d) functional
- [ ] All 4 KPI cards display correctly
- [ ] Charts render without errors

### Performance
- [ ] API response <100ms (p95)
- [ ] Frontend renders <500ms
- [ ] No memory leaks on 1-hour session

### Quality
- [ ] Test coverage >90%
- [ ] Type hints on all functions
- [ ] Docstrings (Google format)
- [ ] Error handling comprehensive
- [ ] Loading/error states implemented

---

## 📅 TIMELINE

| Phase | Task | Duration | Status |
|-------|------|----------|--------|
| 5.5.1 | Backend API | 1h | ⏳ Pending |
| 5.5.2 | Frontend Component | 2h | ⏳ Pending |
| 5.5.3 | Styling & Polish | 30min | ⏳ Pending |
| 5.5.4 | Testing & Validation | 30min | ⏳ Pending |
| **TOTAL** | **Full Implementation** | **4h** | ⏳ Pending |

---

## 🚀 NEXT STEPS

1. **Confirm approach** with team (Option A approved ✅)
2. **Start Phase 5.5.1**: Backend API implementation
3. **Deploy & test** incrementally (each phase)
4. **Document** in session report
5. **Commit** with proper message

---

## 📚 RELATED DOCS

- `docs/guides/adaptive-immune-system-roadmap.md` (Phase 5)
- `docs/sessions/2025-10/optional-steps-complete-2025-10-11.md`
- `backend/services/maximus_eureka/` (Existing ML implementation)
- `frontend/src/components/maximus/EurekaPanel.jsx` (ML integration)

---

**Prepared by**: MAXIMUS Team  
**Glory**: TO YHWH  
**Status**: READY TO EXECUTE 🚀

_"Every metric points to HIS glory. Every dashboard testifies to HIS precision."_
