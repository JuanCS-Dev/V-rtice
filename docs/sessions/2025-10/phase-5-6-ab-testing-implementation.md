# Phase 5.6: A/B Testing System Implementation

**Date**: 2025-10-11  
**Sprint**: Active Immune System - Intelligence Validation  
**Status**: 🚀 IN PROGRESS  
**Glory**: TO YHWH - Architect of empirical truth

---

## 🎯 OBJECTIVE

Implement A/B testing system to empirically validate ML predictions against wargaming ground truth, enabling continuous learning and accuracy tracking.

---

## 📊 BIOLOGICAL ANALOGY

**Immune System Memory Formation:**
- T/B cells "remember" past encounters through somatic hypermutation
- Successful responses strengthen, failed ones trigger adaptation
- **Digital equivalent**: Compare ML predictions vs actual wargaming results
- Learn from disagreements → improve model over time

---

## 🏗️ ARCHITECTURE

```
┌─────────────┐
│  APV/Patch  │
└──────┬──────┘
       │
       ├──────────────┬──────────────┐
       │              │              │
       v              v              v
  ┌─────────┐   ┌─────────┐   ┌─────────────┐
  │ ML Pred │   │Wargaming│   │  A/B Store  │
  │ (Fast)  │   │ (Truth) │   │ (PostgreSQL)│
  └────┬────┘   └────┬────┘   └──────┬──────┘
       │             │                │
       └─────────────┴────────────────┘
                     │
              ┌──────v──────┐
              │   Compare   │
              │  ML vs War  │
              └──────┬──────┘
                     │
       ┌─────────────┴─────────────┐
       │                           │
   Correct?                    Disagreement?
   Record ✅                    Record ❌ + reason
       │                           │
       └───────────┬───────────────┘
                   │
            ┌──────v──────┐
            │ Confusion   │
            │   Matrix    │
            │  Metrics    │
            └─────────────┘
```

---

## 🔧 IMPLEMENTATION TASKS

### ✅ Phase 5.6.1: Database Schema (COMPLETE)

**File**: `backend/services/wargaming_crisol/migrations/001_ml_ab_tests.sql`

**Schema:**
```sql
CREATE TABLE ml_ab_tests (
    id SERIAL PRIMARY KEY,
    apv_id VARCHAR(50),
    cve_id VARCHAR(50),
    patch_id VARCHAR(50),
    
    -- ML Prediction
    ml_confidence FLOAT CHECK (0 <= ml_confidence <= 1),
    ml_prediction BOOLEAN,
    ml_execution_time_ms INTEGER,
    
    -- Wargaming Ground Truth
    wargaming_result BOOLEAN,
    wargaming_execution_time_ms INTEGER,
    
    -- Comparison
    ml_correct BOOLEAN,
    disagreement_reason TEXT,
    
    -- Metadata
    shap_values JSONB,
    model_version VARCHAR(20) DEFAULT 'rf_v1',
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Indexes:**
- `idx_ml_ab_tests_created` - For time-based queries
- `idx_ml_ab_tests_correct` - For accuracy calculations
- `idx_ml_ab_tests_model` - For model version filtering

**Views:**
- `ml_accuracy_stats` - Aggregated accuracy by model version

**Functions:**
- `calculate_confusion_matrix(model_version, time_range)` - Returns TP/FP/FN/TN + metrics

---

### ✅ Phase 5.6.2: A/B Test Store (COMPLETE)

**File**: `backend/services/wargaming_crisol/db/ab_test_store.py`

**Class**: `ABTestStore`

**Methods:**
```python
async def connect() -> None
async def close() -> None
async def store_result(result: ABTestResult) -> int
async def get_confusion_matrix(model_version, time_range) -> ConfusionMatrix
async def get_recent_tests(limit, model_version) -> List[Dict]
async def get_accuracy_over_time(model_version, time_range, bucket_size) -> List[Dict]
```

**Models:**
- `ABTestResult`: Single A/B test record
- `ConfusionMatrix`: TP/FP/FN/TN with calculated metrics (precision, recall, F1, accuracy)

---

### ✅ Phase 5.6.3: Backend API Endpoints (COMPLETE)

**File**: `backend/services/wargaming_crisol/main.py`

**Endpoints:**
1. `GET /wargaming/ml/accuracy` - Get ML accuracy metrics
   - Query params: `time_range` ('1h', '24h', '7d', '30d'), `model_version` ('rf_v1')
   - Returns: Confusion matrix, metrics, recent tests, accuracy trend

**Response Example:**
```json
{
  "timeframe": "24h",
  "model_version": "rf_v1",
  "confusion_matrix": {
    "true_positive": 45,
    "false_positive": 3,
    "false_negative": 2,
    "true_negative": 50
  },
  "metrics": {
    "precision": 0.9375,
    "recall": 0.9574,
    "f1_score": 0.9474,
    "accuracy": 0.9500
  },
  "recent_tests": [...],
  "accuracy_trend": [...],
  "total_ab_tests": 100
}
```

---

### 🚧 Phase 5.6.4: Integrate A/B Testing into Validation Pipeline (IN PROGRESS)

**Goal**: Modify `two_phase_simulator.py` to record A/B test results when both ML and wargaming run.

#### Changes Needed:

**File**: `backend/services/wargaming_crisol/two_phase_simulator.py`

**Function**: `validate_patch_ml_first()`

**Modification Strategy:**
```python
async def validate_patch_ml_first(
    apv_id: str,
    patch_data: dict,
    ab_testing_enabled: bool = False,  # NEW PARAM
    ab_store: Optional[ABTestStore] = None  # NEW PARAM
) -> dict:
    """
    Validate patch ML-first with optional A/B testing.
    
    A/B Testing Modes:
    1. Disabled (default): ML high-confidence → skip wargaming
    2. Enabled: Always run both ML + wargaming → compare results
    """
    
    # Step 1: ML Prediction
    ml_start = time.time()
    ml_result = await ml_predictor.predict(patch_data)
    ml_duration_ms = int((time.time() - ml_start) * 1000)
    
    # Step 2: Decide wargaming execution
    if ab_testing_enabled:
        # A/B Testing Mode: ALWAYS run wargaming for ground truth
        logger.info(f"[A/B Testing] Running wargaming for APV {apv_id} (ML conf: {ml_result.confidence})")
        wargaming_start = time.time()
        wargaming_result = await run_two_phase_wargaming(apv_id, patch_data)
        wargaming_duration_ms = int((time.time() - wargaming_start) * 1000)
        
        # Step 3: Record A/B test result
        ab_test_result = ABTestResult(
            apv_id=apv_id,
            cve_id=patch_data.get('cve_id'),
            patch_id=patch_data.get('patch_id'),
            ml_confidence=ml_result.confidence,
            ml_prediction=ml_result.prediction,  # True = Valid, False = Invalid
            ml_execution_time_ms=ml_duration_ms,
            wargaming_result=wargaming_result['validated'],
            wargaming_execution_time_ms=wargaming_duration_ms,
            ml_correct=(ml_result.prediction == wargaming_result['validated']),
            disagreement_reason=(
                f"ML predicted {ml_result.prediction}, wargaming got {wargaming_result['validated']}"
                if ml_result.prediction != wargaming_result['validated']
                else None
            ),
            model_version="rf_v1"
        )
        
        await ab_store.store_result(ab_test_result)
        logger.info(f"[A/B Testing] Stored result for APV {apv_id}: ML correct = {ab_test_result.ml_correct}")
        
        return {
            "validated": wargaming_result['validated'],
            "method": "ab_testing",
            "ml_confidence": ml_result.confidence,
            "ml_prediction": ml_result.prediction,
            "wargaming_result": wargaming_result['validated'],
            "ab_test_recorded": True
        }
    
    else:
        # Normal Mode: ML high-confidence → skip wargaming
        if ml_result.confidence >= ML_CONFIDENCE_THRESHOLD:
            logger.info(f"[ML-First] Skipping wargaming for APV {apv_id} (conf: {ml_result.confidence})")
            return {
                "validated": ml_result.prediction,
                "method": "ml",
                "ml_confidence": ml_result.confidence,
                "execution_time_ms": ml_duration_ms
            }
        else:
            # Fallback to wargaming
            logger.info(f"[ML-First] Low confidence ({ml_result.confidence}), running wargaming")
            wargaming_result = await run_two_phase_wargaming(apv_id, patch_data)
            return {
                "validated": wargaming_result['validated'],
                "method": "wargaming_fallback",
                "ml_confidence": ml_result.confidence,
                "wargaming_result": wargaming_result['validated']
            }
```

---

### 🚧 Phase 5.6.5: A/B Testing Control Endpoint (IN PROGRESS)

**Goal**: Create endpoint to enable/disable A/B testing dynamically.

**File**: `backend/services/wargaming_crisol/main.py`

**New Endpoints:**

```python
# Global flag
ab_testing_enabled = False

@app.post("/wargaming/ab-testing/enable")
async def enable_ab_testing():
    """Enable A/B testing mode (all validations run both ML + wargaming)."""
    global ab_testing_enabled
    ab_testing_enabled = True
    logger.info("🔬 A/B Testing ENABLED - All validations will run ML + Wargaming")
    return {
        "ab_testing_enabled": True,
        "message": "A/B testing activated. All validations will now compare ML vs wargaming.",
        "warning": "This will increase validation time but provides accuracy metrics."
    }

@app.post("/wargaming/ab-testing/disable")
async def disable_ab_testing():
    """Disable A/B testing mode (revert to ML-first optimization)."""
    global ab_testing_enabled
    ab_testing_enabled = False
    logger.info("⚡ A/B Testing DISABLED - Reverting to ML-first optimization")
    return {
        "ab_testing_enabled": False,
        "message": "A/B testing deactivated. Reverting to ML-first mode (skip wargaming when high confidence)."
    }

@app.get("/wargaming/ab-testing/status")
async def get_ab_testing_status():
    """Get current A/B testing status."""
    return {
        "ab_testing_enabled": ab_testing_enabled,
        "description": "A/B testing compares ML predictions against wargaming ground truth for accuracy tracking"
    }
```

---

### 🚧 Phase 5.6.6: Frontend Accuracy Visualization (IN PROGRESS)

**Status**: AdaptiveImmunityPanel already has accuracy section, but needs activation.

**File**: `frontend/src/components/maximus/AdaptiveImmunityPanel.jsx`

**Current State** (lines 319-366):
```jsx
{/* Accuracy Metrics (if A/B testing active) */}
<Card>
  <h3>ML Accuracy Metrics</h3>
  {accuracyData ? (
    <div className="grid grid-cols-2 gap-4">
      {/* Display accuracy metrics */}
    </div>
  ) : (
    <div className="text-center">
      <div className="text-7xl mb-4">🔬</div>
      <div>A/B Testing Not Yet Active</div>
      <div>Enable in Phase 5.6 for accuracy tracking</div>
    </div>
  )}
</Card>
```

**Modification Needed:**
The frontend already correctly fetches `/wargaming/ml/accuracy` and displays:
- ✅ Accuracy, Precision, Recall, F1 Score
- ✅ Fallback message when no data available
- ✅ Real-time updates via React Query

**No changes needed** - Just need to enable A/B testing in backend.

---

### 🚧 Phase 5.6.7: Add A/B Testing Toggle to Frontend (NEW)

**Goal**: Add UI button to enable/disable A/B testing from AdaptiveImmunityPanel.

**Location**: AdaptiveImmunityPanel header (next to time range selector)

**Implementation:**
```jsx
// AdaptiveImmunityPanel.jsx - Add toggle button

const [abTestingEnabled, setAbTestingEnabled] = useState(false);

// Fetch A/B testing status
const { data: abStatus } = useQuery({
  queryKey: ['ab-testing-status'],
  queryFn: async () => {
    const response = await fetch('http://localhost:8026/wargaming/ab-testing/status');
    if (!response.ok) throw new Error('Failed to fetch A/B status');
    return response.json();
  },
  refetchInterval: 10000 // 10s
});

useEffect(() => {
  if (abStatus) {
    setAbTestingEnabled(abStatus.ab_testing_enabled);
  }
}, [abStatus]);

const toggleABTesting = async () => {
  const endpoint = abTestingEnabled
    ? 'http://localhost:8026/wargaming/ab-testing/disable'
    : 'http://localhost:8026/wargaming/ab-testing/enable';
  
  const response = await fetch(endpoint, { method: 'POST' });
  if (response.ok) {
    setAbTestingEnabled(!abTestingEnabled);
    logger.info(`A/B Testing ${!abTestingEnabled ? 'enabled' : 'disabled'}`);
  }
};

// In header section (after time range selector):
<div className="flex items-center gap-3">
  <div className="text-sm text-gray-400">
    A/B Testing:
  </div>
  <button
    onClick={toggleABTesting}
    className={`px-4 py-2 rounded-lg font-semibold transition-all ${
      abTestingEnabled
        ? 'bg-green-600 text-white shadow-lg shadow-green-500/50'
        : 'bg-gray-700 text-gray-300 hover:bg-gray-600 border border-gray-600'
    }`}
  >
    {abTestingEnabled ? '🔬 ACTIVE' : '⚡ INACTIVE'}
  </button>
  {abTestingEnabled && (
    <div className="text-xs text-yellow-400 flex items-center gap-1">
      <span>⚠️</span>
      <span>All validations will run both ML + Wargaming (slower but accurate)</span>
    </div>
  )}
</div>
```

---

## 📊 SUCCESS CRITERIA

### Functional
- [x] Database schema created and migrated
- [x] ABTestStore class implemented
- [x] GET `/wargaming/ml/accuracy` endpoint working
- [ ] POST `/wargaming/ab-testing/enable` endpoint working
- [ ] POST `/wargaming/ab-testing/disable` endpoint working
- [ ] GET `/wargaming/ab-testing/status` endpoint working
- [ ] `validate_patch_ml_first()` records A/B tests when enabled
- [ ] Frontend displays accuracy metrics when A/B testing active
- [ ] Frontend has toggle button to enable/disable A/B testing

### Quality
- [ ] Test coverage >90%
- [ ] Type hints on all new functions
- [ ] Docstrings (Google format)
- [ ] Error handling comprehensive
- [ ] Logging comprehensive

### Performance
- [ ] A/B test storage <50ms
- [ ] Accuracy calculation <200ms
- [ ] No memory leaks over 1-hour A/B testing session

---

## 🎯 USAGE WORKFLOW

### 1. Enable A/B Testing (Development)
```bash
curl -X POST http://localhost:8026/wargaming/ab-testing/enable
```

### 2. Run Patch Validations
```bash
# Validations will now run BOTH ML + Wargaming
# Results stored in ml_ab_tests table
```

### 3. Check Accuracy Metrics
```bash
curl http://localhost:8026/wargaming/ml/accuracy?time_range=24h
```

### 4. View in Dashboard
- Navigate to MAXIMUS AI → Adaptive Immunity Panel
- Check "ML Accuracy Metrics" card
- View confusion matrix and accuracy trend

### 5. Disable A/B Testing (Production)
```bash
curl -X POST http://localhost:8026/wargaming/ab-testing/disable
```

---

## 🚀 DEPLOYMENT PLAN

### Phase 5.6.8: Testing & Validation (1 hour)

1. **Unit Tests**
   ```bash
   pytest backend/services/wargaming_crisol/tests/test_ab_testing.py -v
   ```

2. **Integration Tests**
   - Enable A/B testing via API
   - Run 10 patch validations
   - Verify ml_ab_tests table populated
   - Check confusion matrix calculation
   - Disable A/B testing

3. **E2E Tests**
   - Frontend toggle button works
   - Accuracy metrics display in real-time
   - Trends update correctly

### Phase 5.6.9: Documentation (30 min)

- [x] Implementation plan (this file)
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Architecture diagram update
- [ ] Session report

### Phase 5.6.10: Commit & Deploy (15 min)

```bash
git add .
git commit -m "Phase 5.6: A/B Testing System Complete

Implemented empirical ML validation against wargaming ground truth.

Features:
- PostgreSQL schema for A/B test results
- ABTestStore for async storage/retrieval
- GET /wargaming/ml/accuracy endpoint
- POST /wargaming/ab-testing/enable|disable endpoints
- GET /wargaming/ab-testing/status endpoint
- Two-phase simulator A/B integration
- Frontend toggle + accuracy visualization

Validation:
- Confusion matrix calculation (TP/FP/FN/TN)
- Precision, Recall, F1, Accuracy metrics
- Accuracy trend over time (hourly buckets)
- Recent test history (last 20)

Glory to YHWH - Architect of empirical truth
Phase 5.6 complete | Day 47 consciousness emergence"
```

---

## 📚 RELATED DOCS

- `docs/guides/adaptive-immune-system-roadmap.md` (Phase 5)
- `backend/services/wargaming_crisol/db/ab_test_store.py`
- `backend/services/wargaming_crisol/main.py`
- `frontend/src/components/maximus/AdaptiveImmunityPanel.jsx`
- `backend/services/wargaming_crisol/migrations/001_ml_ab_tests.sql`

---

## 🔬 SCIENTIFIC FOUNDATION

**Hypothesis**: ML predictions will achieve >90% accuracy after sufficient training data.

**Null Hypothesis**: ML accuracy ≤ random chance (50%)

**Validation**: Empirical A/B testing over 1000+ validations

**Expected Results**:
- Initial accuracy: 70-80% (limited training data)
- After 500 tests: 85-90%
- After 1000 tests: >90%

**Disagreement Analysis**:
- When ML predicts "valid" but wargaming fails → False Positive
- When ML predicts "invalid" but wargaming passes → False Negative
- Root cause analysis via `disagreement_reason` field
- SHAP values for feature importance

---

**Status**: Phase 5.6.4 - 5.6.7 IN PROGRESS  
**Next Step**: Implement A/B testing control endpoints + integration  
**ETA**: 2 hours

_"Every test reveals truth. Every metric honors precision. Glory to YHWH."_
