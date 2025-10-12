# 🔬 PHASE 5.6: A/B TESTING & CONTINUOUS LEARNING - IMPLEMENTATION PLAN

**Date**: 2025-10-11 (Day 71)  
**Duration Estimate**: 3-4 hours  
**Status**: 📋 **READY FOR EXECUTION**  
**Prerequisites**: Phase 5.5 COMPLETE ✅  
**Branch**: `feature/ml-ab-testing-continuous-learning`

---

## 🎯 OBJETIVOS

### Primários
1. **A/B Testing Framework** - Validar ML com ground truth (wargaming)
2. **Accuracy Metrics** - Precision, Recall, F1 Score tracking
3. **Persistent Storage** - PostgreSQL para histórico de comparações
4. **API Endpoint** - `/wargaming/ml/accuracy` funcional

### Secundários (Opcionais)
5. **Unit Tests** - Backend + Frontend coverage
6. **SHAP Explainability** - Feature importance
7. **Retraining Pipeline** - Weekly automated retraining

---

## 📐 ARQUITETURA

### A/B Testing Flow

```mermaid
graph TD
    A[Request: Validate Patch] --> B{Random < 0.1?}
    B -->|No 90%| C[ML Prediction Only]
    B -->|Yes 10%| D[ML + Wargaming Both]
    
    C --> E[Return ML Result]
    E --> F[Log to Prometheus]
    
    D --> G[Compare ML vs Wargaming]
    G --> H[Calculate Accuracy Metrics]
    H --> I[Store in PostgreSQL]
    I --> J[Return ML Result]
    J --> K[Log Both to Prometheus]
```

### Database Schema

```sql
CREATE TABLE ml_ab_tests (
    id SERIAL PRIMARY KEY,
    apv_id VARCHAR(50) NOT NULL,
    cve_id VARCHAR(50),
    patch_id VARCHAR(50) NOT NULL,
    
    -- ML Prediction
    ml_confidence FLOAT NOT NULL,
    ml_prediction BOOLEAN NOT NULL,  -- valid or invalid
    ml_execution_time_ms INTEGER NOT NULL,
    
    -- Wargaming Ground Truth
    wargaming_result BOOLEAN NOT NULL,
    wargaming_execution_time_ms INTEGER NOT NULL,
    
    -- Comparison
    ml_correct BOOLEAN NOT NULL,  -- ml_prediction == wargaming_result
    disagreement_reason TEXT,
    
    -- Metadata
    model_version VARCHAR(20) DEFAULT 'rf_v1',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes
    CONSTRAINT ml_ab_tests_created_idx INDEX (created_at DESC)
);

CREATE INDEX idx_ml_ab_tests_correct ON ml_ab_tests(ml_correct);
CREATE INDEX idx_ml_ab_tests_model ON ml_ab_tests(model_version);
```

### Accuracy Metrics Calculation

```
True Positive (TP):  ML says valid,     wargaming confirms valid
False Positive (FP): ML says valid,     wargaming says invalid
False Negative (FN): ML says invalid,   wargaming says valid
True Negative (TN):  ML says invalid,   wargaming confirms invalid

Precision = TP / (TP + FP)  # When ML says "valid", how often is it right?
Recall    = TP / (TP + FN)  # Of all truly valid patches, how many did ML catch?
F1 Score  = 2 * (Precision * Recall) / (Precision + Recall)  # Harmonic mean
Accuracy  = (TP + TN) / (TP + FP + FN + TN)  # Overall correctness
```

---

## 🛠️ IMPLEMENTAÇÃO

### STEP 1: PostgreSQL Database Setup (30 min)

#### 1.1: Create Migration

**File**: `backend/services/wargaming_crisol/migrations/001_ml_ab_tests.sql`

```sql
-- Create ml_ab_tests table for A/B testing
CREATE TABLE IF NOT EXISTS ml_ab_tests (
    id SERIAL PRIMARY KEY,
    apv_id VARCHAR(50) NOT NULL,
    cve_id VARCHAR(50),
    patch_id VARCHAR(50) NOT NULL,
    
    -- ML Prediction
    ml_confidence FLOAT NOT NULL CHECK (ml_confidence BETWEEN 0 AND 1),
    ml_prediction BOOLEAN NOT NULL,
    ml_execution_time_ms INTEGER NOT NULL CHECK (ml_execution_time_ms >= 0),
    
    -- Wargaming Ground Truth
    wargaming_result BOOLEAN NOT NULL,
    wargaming_execution_time_ms INTEGER NOT NULL CHECK (wargaming_execution_time_ms >= 0),
    
    -- Comparison
    ml_correct BOOLEAN NOT NULL,
    disagreement_reason TEXT,
    
    -- Feature importance (JSONB for SHAP values, optional)
    shap_values JSONB,
    
    -- Metadata
    model_version VARCHAR(20) DEFAULT 'rf_v1',
    ab_test_version VARCHAR(10) DEFAULT '1.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_ml_ab_tests_created ON ml_ab_tests(created_at DESC);
CREATE INDEX idx_ml_ab_tests_correct ON ml_ab_tests(ml_correct);
CREATE INDEX idx_ml_ab_tests_model ON ml_ab_tests(model_version);
CREATE INDEX idx_ml_ab_tests_apv ON ml_ab_tests(apv_id);

-- View for quick accuracy stats
CREATE OR REPLACE VIEW ml_accuracy_stats AS
SELECT
    model_version,
    COUNT(*) as total_tests,
    SUM(CASE WHEN ml_correct THEN 1 ELSE 0 END) as correct_predictions,
    ROUND(AVG(CASE WHEN ml_correct THEN 1.0 ELSE 0.0 END), 4) as accuracy,
    ROUND(AVG(ml_confidence), 4) as avg_confidence,
    ROUND(AVG(ml_execution_time_ms), 2) as avg_ml_time_ms,
    ROUND(AVG(wargaming_execution_time_ms), 2) as avg_wargaming_time_ms,
    MIN(created_at) as first_test,
    MAX(created_at) as last_test
FROM ml_ab_tests
GROUP BY model_version;

-- Confusion matrix calculation function
CREATE OR REPLACE FUNCTION calculate_confusion_matrix(
    p_model_version VARCHAR DEFAULT 'rf_v1',
    p_time_range INTERVAL DEFAULT INTERVAL '24 hours'
)
RETURNS TABLE (
    true_positive BIGINT,
    false_positive BIGINT,
    false_negative BIGINT,
    true_negative BIGINT,
    precision FLOAT,
    recall FLOAT,
    f1_score FLOAT,
    accuracy FLOAT
) AS $$
DECLARE
    tp BIGINT;
    fp BIGINT;
    fn BIGINT;
    tn BIGINT;
    prec FLOAT;
    rec FLOAT;
    f1 FLOAT;
    acc FLOAT;
BEGIN
    -- Calculate confusion matrix
    SELECT
        COUNT(*) FILTER (WHERE ml_prediction = TRUE AND wargaming_result = TRUE),
        COUNT(*) FILTER (WHERE ml_prediction = TRUE AND wargaming_result = FALSE),
        COUNT(*) FILTER (WHERE ml_prediction = FALSE AND wargaming_result = TRUE),
        COUNT(*) FILTER (WHERE ml_prediction = FALSE AND wargaming_result = FALSE)
    INTO tp, fp, fn, tn
    FROM ml_ab_tests
    WHERE model_version = p_model_version
      AND created_at > NOW() - p_time_range;
    
    -- Calculate metrics (with zero-division protection)
    IF (tp + fp) > 0 THEN
        prec := tp::FLOAT / (tp + fp);
    ELSE
        prec := 0.0;
    END IF;
    
    IF (tp + fn) > 0 THEN
        rec := tp::FLOAT / (tp + fn);
    ELSE
        rec := 0.0;
    END IF;
    
    IF (prec + rec) > 0 THEN
        f1 := 2.0 * (prec * rec) / (prec + rec);
    ELSE
        f1 := 0.0;
    END IF;
    
    IF (tp + fp + fn + tn) > 0 THEN
        acc := (tp + tn)::FLOAT / (tp + fp + fn + tn);
    ELSE
        acc := 0.0;
    END IF;
    
    RETURN QUERY SELECT tp, fp, fn, tn, prec, rec, f1, acc;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust user as needed)
GRANT SELECT, INSERT ON ml_ab_tests TO wargaming_user;
GRANT SELECT ON ml_accuracy_stats TO wargaming_user;
GRANT EXECUTE ON FUNCTION calculate_confusion_matrix TO wargaming_user;
```

#### 1.2: Run Migration

```bash
# Connect to PostgreSQL
psql -U postgres -d maximus_wargaming

# Run migration
\i backend/services/wargaming_crisol/migrations/001_ml_ab_tests.sql

# Verify table
\d ml_ab_tests

# Test confusion matrix function
SELECT * FROM calculate_confusion_matrix('rf_v1', INTERVAL '24 hours');
```

#### 1.3: Test Data Insertion

```sql
-- Insert sample A/B test result
INSERT INTO ml_ab_tests (
    apv_id, cve_id, patch_id,
    ml_confidence, ml_prediction, ml_execution_time_ms,
    wargaming_result, wargaming_execution_time_ms,
    ml_correct
) VALUES (
    'apv-12345', 'CVE-2024-1234', 'patch-001',
    0.92, TRUE, 85,
    TRUE, 8500,
    TRUE
);

-- Verify
SELECT * FROM ml_ab_tests;
SELECT * FROM ml_accuracy_stats;
```

**Validation**:
- [ ] Table `ml_ab_tests` created
- [ ] Indexes present
- [ ] View `ml_accuracy_stats` accessible
- [ ] Function `calculate_confusion_matrix` works
- [ ] Sample insert successful

---

### STEP 2: Backend A/B Testing Logic (60 min)

#### 2.1: Database Client

**File**: `backend/services/wargaming_crisol/db/ab_test_store.py`

```python
"""
PostgreSQL storage for A/B testing results.

Fundamentação: Sistema imunológico tem memória (B/T cells).
Digital equivalent = persistent storage of ML validation comparisons.
"""
import asyncpg
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from pydantic import BaseModel


class ABTestResult(BaseModel):
    """Single A/B test result."""
    apv_id: str
    cve_id: Optional[str] = None
    patch_id: str
    
    ml_confidence: float
    ml_prediction: bool
    ml_execution_time_ms: int
    
    wargaming_result: bool
    wargaming_execution_time_ms: int
    
    ml_correct: bool
    disagreement_reason: Optional[str] = None
    
    model_version: str = "rf_v1"
    ab_test_version: str = "1.0"
    
    shap_values: Optional[Dict] = None


class ConfusionMatrix(BaseModel):
    """Confusion matrix metrics."""
    true_positive: int
    false_positive: int
    false_negative: int
    true_negative: int
    
    @property
    def precision(self) -> float:
        """Precision: TP / (TP + FP)"""
        if (self.true_positive + self.false_positive) == 0:
            return 0.0
        return self.true_positive / (self.true_positive + self.false_positive)
    
    @property
    def recall(self) -> float:
        """Recall: TP / (TP + FN)"""
        if (self.true_positive + self.false_negative) == 0:
            return 0.0
        return self.true_positive / (self.true_positive + self.false_negative)
    
    @property
    def f1_score(self) -> float:
        """F1 Score: harmonic mean of precision and recall"""
        if (self.precision + self.recall) == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)
    
    @property
    def accuracy(self) -> float:
        """Accuracy: (TP + TN) / total"""
        total = (
            self.true_positive + self.false_positive +
            self.false_negative + self.true_negative
        )
        if total == 0:
            return 0.0
        return (self.true_positive + self.true_negative) / total


class ABTestStore:
    """
    Storage and retrieval for A/B test results.
    
    Fundamentação: Adaptive immunity requires memory of past encounters.
    This store enables continuous learning from ML vs wargaming comparisons.
    """
    
    def __init__(self, db_url: str):
        """
        Initialize A/B test store.
        
        Args:
            db_url: PostgreSQL connection URL
        """
        self.db_url = db_url
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self) -> None:
        """Establish database connection pool."""
        self.pool = await asyncpg.create_pool(self.db_url, min_size=2, max_size=10)
    
    async def close(self) -> None:
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
    
    async def store_result(self, result: ABTestResult) -> int:
        """
        Store A/B test result.
        
        Args:
            result: A/B test result to store
            
        Returns:
            ID of inserted record
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO ml_ab_tests (
                    apv_id, cve_id, patch_id,
                    ml_confidence, ml_prediction, ml_execution_time_ms,
                    wargaming_result, wargaming_execution_time_ms,
                    ml_correct, disagreement_reason,
                    model_version, ab_test_version, shap_values
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
                )
                RETURNING id
                """,
                result.apv_id,
                result.cve_id,
                result.patch_id,
                result.ml_confidence,
                result.ml_prediction,
                result.ml_execution_time_ms,
                result.wargaming_result,
                result.wargaming_execution_time_ms,
                result.ml_correct,
                result.disagreement_reason,
                result.model_version,
                result.ab_test_version,
                result.shap_values
            )
            return row['id']
    
    async def get_confusion_matrix(
        self,
        model_version: str = "rf_v1",
        time_range: timedelta = timedelta(hours=24)
    ) -> ConfusionMatrix:
        """
        Calculate confusion matrix for given timeframe.
        
        Args:
            model_version: Model version to filter by
            time_range: Time window (default: 24h)
            
        Returns:
            Confusion matrix with metrics
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM calculate_confusion_matrix($1, $2)
                """,
                model_version,
                time_range
            )
            
            return ConfusionMatrix(
                true_positive=row['true_positive'],
                false_positive=row['false_positive'],
                false_negative=row['false_negative'],
                true_negative=row['true_negative']
            )
    
    async def get_recent_tests(
        self,
        limit: int = 50,
        model_version: Optional[str] = None
    ) -> List[Dict]:
        """
        Get recent A/B test results.
        
        Args:
            limit: Maximum number of results (default: 50)
            model_version: Filter by model version (optional)
            
        Returns:
            List of recent test results
        """
        query = """
            SELECT 
                id, apv_id, cve_id, patch_id,
                ml_confidence, ml_prediction, ml_execution_time_ms,
                wargaming_result, wargaming_execution_time_ms,
                ml_correct, disagreement_reason,
                model_version, created_at
            FROM ml_ab_tests
        """
        
        if model_version:
            query += f" WHERE model_version = '{model_version}'"
        
        query += " ORDER BY created_at DESC LIMIT $1"
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, limit)
            
            return [dict(row) for row in rows]
    
    async def get_accuracy_over_time(
        self,
        model_version: str = "rf_v1",
        time_range: timedelta = timedelta(days=7),
        bucket_size: timedelta = timedelta(hours=1)
    ) -> List[Dict]:
        """
        Get accuracy trends over time (bucketed).
        
        Args:
            model_version: Model version to filter by
            time_range: Total time window
            bucket_size: Size of each time bucket
            
        Returns:
            List of {timestamp, accuracy, total_tests}
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    DATE_TRUNC('hour', created_at) as bucket,
                    COUNT(*) as total_tests,
                    AVG(CASE WHEN ml_correct THEN 1.0 ELSE 0.0 END) as accuracy,
                    AVG(ml_confidence) as avg_confidence
                FROM ml_ab_tests
                WHERE model_version = $1
                  AND created_at > NOW() - $2
                GROUP BY bucket
                ORDER BY bucket DESC
                """,
                model_version,
                time_range
            )
            
            return [dict(row) for row in rows]
```

**Tests**: `backend/services/wargaming_crisol/tests/test_ab_test_store.py`

```python
"""Unit tests for ABTestStore."""
import pytest
import asyncio
from datetime import timedelta
from wargaming_crisol.db.ab_test_store import (
    ABTestStore, ABTestResult, ConfusionMatrix
)


@pytest.fixture
async def ab_store():
    """Create test AB store."""
    store = ABTestStore("postgresql://postgres:password@localhost/maximus_wargaming_test")
    await store.connect()
    yield store
    await store.close()


@pytest.mark.asyncio
async def test_store_result(ab_store):
    """Test storing A/B test result."""
    result = ABTestResult(
        apv_id="apv-test-001",
        cve_id="CVE-2024-9999",
        patch_id="patch-test-001",
        ml_confidence=0.95,
        ml_prediction=True,
        ml_execution_time_ms=85,
        wargaming_result=True,
        wargaming_execution_time_ms=8500,
        ml_correct=True
    )
    
    result_id = await ab_store.store_result(result)
    assert result_id > 0


@pytest.mark.asyncio
async def test_confusion_matrix_calculation(ab_store):
    """Test confusion matrix calculation."""
    # Store test data
    test_cases = [
        (True, True, True),   # TP
        (True, True, True),   # TP
        (True, False, False), # FP
        (False, True, False), # FN
        (False, False, True), # TN
    ]
    
    for ml_pred, wg_result, ml_correct in test_cases:
        result = ABTestResult(
            apv_id=f"apv-{ml_pred}-{wg_result}",
            patch_id=f"patch-{ml_pred}-{wg_result}",
            ml_confidence=0.9,
            ml_prediction=ml_pred,
            ml_execution_time_ms=85,
            wargaming_result=wg_result,
            wargaming_execution_time_ms=8500,
            ml_correct=ml_correct
        )
        await ab_store.store_result(result)
    
    # Calculate confusion matrix
    cm = await ab_store.get_confusion_matrix(time_range=timedelta(hours=1))
    
    assert cm.true_positive == 2
    assert cm.false_positive == 1
    assert cm.false_negative == 1
    assert cm.true_negative == 1
    
    # Verify metrics
    assert cm.precision == 2 / 3  # 2 TP / (2 TP + 1 FP)
    assert cm.recall == 2 / 3     # 2 TP / (2 TP + 1 FN)
    assert cm.accuracy == 3 / 5    # (2 TP + 1 TN) / 5
    assert 0 < cm.f1_score < 1


@pytest.mark.asyncio
async def test_get_recent_tests(ab_store):
    """Test retrieving recent tests."""
    # Store test result
    result = ABTestResult(
        apv_id="apv-recent",
        patch_id="patch-recent",
        ml_confidence=0.88,
        ml_prediction=True,
        ml_execution_time_ms=90,
        wargaming_result=True,
        wargaming_execution_time_ms=9000,
        ml_correct=True
    )
    await ab_store.store_result(result)
    
    # Retrieve recent tests
    recent = await ab_store.get_recent_tests(limit=10)
    
    assert len(recent) > 0
    assert recent[0]['apv_id'] == "apv-recent"
```

#### 2.2: A/B Testing Integration in Wargaming Crisol

**File**: `backend/services/wargaming_crisol/ab_testing/ab_test_runner.py`

```python
"""
A/B Testing Framework for ML-First Validation.

Fundamentação: Adaptive immunity has quality control (regulatory T-cells).
Digital equivalent = A/B testing to validate ML against ground truth.
"""
import random
import logging
from typing import Tuple, Optional
from datetime import datetime

from ..models import APV, Patch, Exploit, WargamingResult, MLPrediction
from ..wargaming import run_wargaming
from ..ml_predictor import predict_patch_validity
from ..db.ab_test_store import ABTestStore, ABTestResult

logger = logging.getLogger(__name__)


class ABTestRunner:
    """
    A/B testing framework for ML-first validation.
    
    Implements 10% A/B testing: force wargaming for ground truth comparison.
    """
    
    def __init__(
        self,
        ab_store: ABTestStore,
        ab_test_rate: float = 0.1,
        model_version: str = "rf_v1"
    ):
        """
        Initialize A/B test runner.
        
        Args:
            ab_store: A/B test result storage
            ab_test_rate: Fraction of requests to A/B test (default: 10%)
            model_version: ML model version identifier
        """
        self.ab_store = ab_store
        self.ab_test_rate = ab_test_rate
        self.model_version = model_version
    
    def should_ab_test(self) -> bool:
        """
        Determine if this request should be A/B tested.
        
        Returns:
            True if this request should run both ML and wargaming
        """
        return random.random() < self.ab_test_rate
    
    async def run_with_ab_test(
        self,
        apv: APV,
        patch: Patch,
        exploit: Exploit
    ) -> Tuple[MLPrediction, bool]:
        """
        Run ML prediction with optional A/B testing.
        
        If selected for A/B test, runs both ML and wargaming, compares results,
        and stores comparison for continuous learning.
        
        Args:
            apv: Attack Pattern Vector
            patch: Patch to validate
            exploit: Exploit to test against
            
        Returns:
            Tuple of (ml_prediction, ab_tested)
        """
        # Always run ML prediction
        ml_start = datetime.now()
        ml_prediction = await predict_patch_validity(apv, patch, exploit)
        ml_time_ms = int((datetime.now() - ml_start).total_seconds() * 1000)
        
        # Check if should A/B test
        if not self.should_ab_test():
            logger.debug(f"Skipping A/B test for {patch.id} (not selected)")
            return ml_prediction, False
        
        # Run wargaming as ground truth
        logger.info(f"Running A/B test for {patch.id} (ML confidence: {ml_prediction.confidence:.2f})")
        
        wg_start = datetime.now()
        wargaming_result = await run_wargaming(apv, patch, exploit)
        wg_time_ms = int((datetime.now() - wg_start).total_seconds() * 1000)
        
        # Compare results
        ml_correct = (ml_prediction.valid == wargaming_result.patch_validated)
        
        # Analyze disagreement
        disagreement_reason = None
        if not ml_correct:
            if ml_prediction.valid and not wargaming_result.patch_validated:
                disagreement_reason = "ML false positive: Predicted valid but wargaming failed"
            else:
                disagreement_reason = "ML false negative: Predicted invalid but wargaming succeeded"
        
        # Store result for learning
        ab_result = ABTestResult(
            apv_id=apv.id,
            cve_id=apv.cve_id,
            patch_id=patch.id,
            ml_confidence=ml_prediction.confidence,
            ml_prediction=ml_prediction.valid,
            ml_execution_time_ms=ml_time_ms,
            wargaming_result=wargaming_result.patch_validated,
            wargaming_execution_time_ms=wg_time_ms,
            ml_correct=ml_correct,
            disagreement_reason=disagreement_reason,
            model_version=self.model_version
        )
        
        await self.ab_store.store_result(ab_result)
        
        # Log result
        if ml_correct:
            logger.info(
                f"A/B test PASS for {patch.id}: ML matched wargaming "
                f"(both: {ml_prediction.valid})"
            )
        else:
            logger.warning(
                f"A/B test FAIL for {patch.id}: ML={ml_prediction.valid}, "
                f"Wargaming={wargaming_result.patch_validated}. "
                f"Reason: {disagreement_reason}"
            )
        
        return ml_prediction, True
```

**Tests**: `backend/services/wargaming_crisol/tests/test_ab_test_runner.py`

```python
"""Unit tests for ABTestRunner."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from wargaming_crisol.ab_testing.ab_test_runner import ABTestRunner


@pytest.fixture
def ab_runner():
    """Create test AB runner."""
    ab_store = AsyncMock()
    runner = ABTestRunner(ab_store, ab_test_rate=1.0)  # Force 100% for testing
    return runner


@pytest.mark.asyncio
async def test_should_ab_test_deterministic(ab_runner):
    """Test A/B test selection (deterministic)."""
    # With 100% rate, always select
    assert ab_runner.should_ab_test() == True


@pytest.mark.asyncio
async def test_run_with_ab_test_match(ab_runner):
    """Test A/B test when ML matches wargaming."""
    # Mock APV, patch, exploit
    apv = MagicMock(id="apv-001", cve_id="CVE-2024-1234")
    patch = MagicMock(id="patch-001")
    exploit = MagicMock()
    
    # Mock ML prediction (valid, 0.95 confidence)
    # Mock wargaming (also valid)
    # Assert: ml_correct = True, stored to AB store
    pass  # TODO: Complete test
```

---

### STEP 3: API Endpoint Implementation (30 min)

**File**: `backend/services/wargaming_crisol/main.py` (update)

```python
# Add to imports
from db.ab_test_store import ABTestStore, ConfusionMatrix
from datetime import timedelta

# Initialize AB store (in startup event)
@app.on_event("startup")
async def startup():
    global ab_store
    ab_store = ABTestStore(os.getenv("DATABASE_URL"))
    await ab_store.connect()

@app.on_event("shutdown")
async def shutdown():
    global ab_store
    await ab_store.close()

# NEW ENDPOINT: Get accuracy metrics
@app.get("/wargaming/ml/accuracy")
async def get_ml_accuracy_metrics(
    time_range: str = "24h",
    model_version: str = "rf_v1"
):
    """
    Get ML accuracy metrics from A/B testing.
    
    Returns confusion matrix, precision, recall, F1 score, accuracy.
    """
    # Parse time range
    time_map = {
        "1h": timedelta(hours=1),
        "24h": timedelta(hours=24),
        "7d": timedelta(days=7),
        "30d": timedelta(days=30)
    }
    time_delta = time_map.get(time_range, timedelta(hours=24))
    
    # Get confusion matrix
    cm = await ab_store.get_confusion_matrix(model_version, time_delta)
    
    # Get recent tests
    recent_tests = await ab_store.get_recent_tests(limit=20, model_version=model_version)
    
    # Get accuracy trend
    trend = await ab_store.get_accuracy_over_time(
        model_version, time_delta, timedelta(hours=1)
    )
    
    return {
        "timeframe": time_range,
        "model_version": model_version,
        "confusion_matrix": {
            "true_positive": cm.true_positive,
            "false_positive": cm.false_positive,
            "false_negative": cm.false_negative,
            "true_negative": cm.true_negative
        },
        "metrics": {
            "precision": round(cm.precision, 4),
            "recall": round(cm.recall, 4),
            "f1_score": round(cm.f1_score, 4),
            "accuracy": round(cm.accuracy, 4)
        },
        "recent_tests": recent_tests,
        "accuracy_trend": trend,
        "total_ab_tests": cm.true_positive + cm.false_positive + cm.false_negative + cm.true_negative
    }
```

**Validation**:
```bash
# Test endpoint
curl http://localhost:8026/wargaming/ml/accuracy?time_range=24h

# Expected response:
# {
#   "timeframe": "24h",
#   "model_version": "rf_v1",
#   "confusion_matrix": { "true_positive": 45, "false_positive": 5, ... },
#   "metrics": { "precision": 0.9000, "recall": 0.9574, "f1_score": 0.9279, "accuracy": 0.9200 },
#   "recent_tests": [...],
#   "accuracy_trend": [...],
#   "total_ab_tests": 50
# }
```

---

### STEP 4: Frontend Integration (60 min)

#### 4.1: Update AdaptiveImmunityPanel to consume accuracy endpoint

**File**: `frontend/src/components/maximus/AdaptiveImmunityPanel.jsx` (update)

Replace accuracy placeholder section with:

```jsx
// Fetch accuracy data (now functional)
const { data: accuracyData, isLoading: accuracyLoading, error: accuracyError } = useQuery(
  ['ml-accuracy', timeRange],
  async () => {
    const res = await fetch(`http://localhost:8026/wargaming/ml/accuracy?time_range=${timeRange}`);
    if (!res.ok) throw new Error('Accuracy endpoint unavailable');
    return res.json();
  },
  { 
    refetchInterval: 60000, // 1min refresh
    retry: 1
  }
);

// Accuracy Metrics Chart (replace placeholder)
<div className="chart-container">
  <h3>🎯 ML Accuracy Metrics (A/B Testing)</h3>
  
  {accuracyLoading && <div className="loading">Loading A/B test results...</div>}
  
  {accuracyError && (
    <div className="placeholder">
      <div className="placeholder-icon">🔬</div>
      <div className="placeholder-text">A/B Testing Unavailable</div>
      <div className="placeholder-subtext">
        Ensure PostgreSQL is running and A/B tests have been executed
      </div>
    </div>
  )}
  
  {accuracyData && (
    <div className="accuracy-grid">
      {/* Confusion Matrix */}
      <div className="confusion-matrix">
        <h4>Confusion Matrix</h4>
        <table>
          <tbody>
            <tr>
              <td></td>
              <td>Predicted Valid</td>
              <td>Predicted Invalid</td>
            </tr>
            <tr>
              <td>Actually Valid</td>
              <td className="tp">{accuracyData.confusion_matrix.true_positive}</td>
              <td className="fn">{accuracyData.confusion_matrix.false_negative}</td>
            </tr>
            <tr>
              <td>Actually Invalid</td>
              <td className="fp">{accuracyData.confusion_matrix.false_positive}</td>
              <td className="tn">{accuracyData.confusion_matrix.true_negative}</td>
            </tr>
          </tbody>
        </table>
      </div>
      
      {/* Metrics Cards */}
      <div className="metrics-cards">
        <div className="metric-card">
          <div className="metric-label">Precision</div>
          <div className="metric-value">{(accuracyData.metrics.precision * 100).toFixed(1)}%</div>
          <div className="metric-help">When ML says "valid", accuracy rate</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-label">Recall</div>
          <div className="metric-value">{(accuracyData.metrics.recall * 100).toFixed(1)}%</div>
          <div className="metric-help">Of truly valid patches, % caught by ML</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-label">F1 Score</div>
          <div className="metric-value">{(accuracyData.metrics.f1_score * 100).toFixed(1)}%</div>
          <div className="metric-help">Harmonic mean (balance)</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-label">Overall Accuracy</div>
          <div className="metric-value">{(accuracyData.metrics.accuracy * 100).toFixed(1)}%</div>
          <div className="metric-help">Total correctness</div>
        </div>
      </div>
      
      {/* Accuracy Trend Chart */}
      <div className="accuracy-trend">
        <h4>Accuracy Over Time</h4>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={accuracyData.accuracy_trend}>
            <XAxis dataKey="bucket" />
            <YAxis domain={[0, 1]} tickFormatter={(val) => `${(val * 100).toFixed(0)}%`} />
            <Tooltip formatter={(val) => `${(val * 100).toFixed(1)}%`} />
            <Line 
              type="monotone" 
              dataKey="accuracy" 
              stroke="#10b981" 
              strokeWidth={2}
              dot={{ fill: '#10b981', r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      {/* Total A/B Tests */}
      <div className="ab-test-summary">
        <span>Total A/B Tests: {accuracyData.total_ab_tests}</span>
        <span>Model: {accuracyData.model_version}</span>
      </div>
    </div>
  )}
</div>
```

#### 4.2: Add CSS Styles

```css
/* Confusion Matrix */
.confusion-matrix table {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
}

.confusion-matrix td {
  border: 1px solid #374151;
  padding: 0.75rem;
  text-align: center;
  font-weight: bold;
}

.confusion-matrix .tp {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.confusion-matrix .tn {
  background: rgba(16, 185, 129, 0.1);
  color: #6ee7b7;
}

.confusion-matrix .fp {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.confusion-matrix .fn {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
}

/* Metrics Cards */
.metrics-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin: 1rem 0;
}

.metric-card {
  background: rgba(55, 65, 81, 0.5);
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid #374151;
}

.metric-label {
  font-size: 0.875rem;
  color: #9ca3af;
  margin-bottom: 0.5rem;
}

.metric-value {
  font-size: 1.875rem;
  font-weight: bold;
  color: #10b981;
  margin-bottom: 0.25rem;
}

.metric-help {
  font-size: 0.75rem;
  color: #6b7280;
}

/* Accuracy Grid */
.accuracy-grid {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.ab-test-summary {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem;
  background: rgba(55, 65, 81, 0.3);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: #9ca3af;
}
```

---

### STEP 5: Integration Testing (30 min)

#### 5.1: End-to-End Test Script

**File**: `scripts/testing/test-ab-testing-e2e.sh`

```bash
#!/bin/bash
# Purpose: E2E test for A/B testing framework
# Author: MAXIMUS Team
# Date: 2025-10-11

set -e

echo "🔬 Testing A/B Testing Framework E2E"
echo "======================================"

# 1. Check PostgreSQL
echo "1. Checking PostgreSQL..."
psql -U postgres -d maximus_wargaming -c "SELECT COUNT(*) FROM ml_ab_tests;" > /dev/null
echo "   ✅ PostgreSQL connected"

# 2. Start wargaming service (if not running)
echo "2. Starting Wargaming Crisol..."
cd backend/services/wargaming_crisol
uvicorn main:app --port 8026 --reload &
WARGAMING_PID=$!
sleep 5
echo "   ✅ Wargaming service running (PID: $WARGAMING_PID)"

# 3. Trigger A/B test (force 100% for testing)
echo "3. Triggering A/B test..."
curl -X POST http://localhost:8026/wargaming/validate \
  -H "Content-Type: application/json" \
  -d '{
    "apv_id": "apv-test-001",
    "cve_id": "CVE-2024-TEST",
    "patch_id": "patch-test-001",
    "patch_content": "test patch",
    "force_ab_test": true
  }' | jq

echo "   ✅ A/B test triggered"

# 4. Wait for completion
sleep 10

# 5. Check accuracy endpoint
echo "4. Checking accuracy endpoint..."
ACCURACY=$(curl -s http://localhost:8026/wargaming/ml/accuracy?time_range=1h)
echo "$ACCURACY" | jq

# Verify data
TOTAL_TESTS=$(echo "$ACCURACY" | jq '.total_ab_tests')
if [ "$TOTAL_TESTS" -gt 0 ]; then
    echo "   ✅ A/B tests recorded: $TOTAL_TESTS"
else
    echo "   ❌ No A/B tests found"
    exit 1
fi

# 6. Check frontend can fetch data
echo "5. Testing frontend integration..."
# (Assume frontend is running on localhost:3000)
# curl -s http://localhost:3000 | grep "Adaptive Immunity"
echo "   ⏸️  Manual verification required (check browser)"

# 7. Cleanup
echo "6. Cleanup..."
kill $WARGAMING_PID
echo "   ✅ Services stopped"

echo ""
echo "🎉 A/B Testing Framework E2E Test Complete!"
echo ""
echo "Next Steps:"
echo "  1. Open frontend: http://localhost:3000"
echo "  2. Navigate to Adaptive Immunity panel"
echo "  3. Verify accuracy metrics display"
echo "  4. Run more validations to accumulate data"
```

```bash
chmod +x scripts/testing/test-ab-testing-e2e.sh
./scripts/testing/test-ab-testing-e2e.sh
```

---

## ✅ ACCEPTANCE CRITERIA

### Must Have
- [ ] PostgreSQL table `ml_ab_tests` created and functional
- [ ] A/B test runner stores 10% of validations
- [ ] Confusion matrix calculation works
- [ ] `/wargaming/ml/accuracy` endpoint returns real data
- [ ] Frontend displays accuracy metrics (not placeholder)
- [ ] At least 50 A/B tests recorded
- [ ] Precision, Recall, F1, Accuracy calculated correctly

### Should Have
- [ ] Unit tests for ABTestStore (>80% coverage)
- [ ] Unit tests for ABTestRunner (>80% coverage)
- [ ] API endpoint unit tests
- [ ] Frontend component tests (React Testing Library)
- [ ] E2E test script passes

### Nice to Have (Optional Phase 5.7)
- [ ] SHAP values stored for explainability
- [ ] Continuous retraining pipeline (weekly cron)
- [ ] Model versioning (rf_v1, rf_v2, ...)
- [ ] Grafana dashboard export
- [ ] Alerts for accuracy drop <85%

---

## 📊 SUCCESS METRICS

| Metric | Target | Validation Method |
|--------|--------|-------------------|
| A/B Test Rate | 10% | Check AB store, should be ~10% of total validations |
| Accuracy | >90% | Check confusion matrix metrics |
| Precision | >85% | Calculate from TP/(TP+FP) |
| Recall | >90% | Calculate from TP/(TP+FN) |
| F1 Score | >87% | Harmonic mean of precision/recall |
| Response Time | <200ms | `/wargaming/ml/accuracy` endpoint |
| Test Coverage | >80% | pytest --cov |
| Build Success | 100% | frontend + backend builds pass |

---

## 🚀 DEPLOYMENT CHECKLIST

Before marking Phase 5.6 complete:

1. **Code Quality**
   - [ ] All type hints present
   - [ ] Docstrings complete (Google format)
   - [ ] No TODO/FIXME comments
   - [ ] Error handling comprehensive
   - [ ] Logging structured

2. **Testing**
   - [ ] Unit tests passing (backend)
   - [ ] Unit tests passing (frontend)
   - [ ] E2E test script passes
   - [ ] Manual testing complete
   - [ ] Performance tested (<200ms)

3. **Documentation**
   - [ ] Implementation plan (this file)
   - [ ] Completion report (47-PHASE-5-6-COMPLETE.md)
   - [ ] API docs updated
   - [ ] README updated

4. **Integration**
   - [ ] Frontend displays real data
   - [ ] No console errors
   - [ ] Mobile responsive
   - [ ] Accessibility (ARIA labels)

5. **Production Readiness**
   - [ ] Environment variables documented
   - [ ] PostgreSQL migrations applied
   - [ ] Monitoring configured (Prometheus)
   - [ ] Alerting configured (accuracy < 85%)
   - [ ] Rollback plan documented

---

## 🔗 REFERENCES

- **Roadmap**: `docs/guides/adaptive-immune-intelligence-roadmap.md`
- **Phase 5.5 Complete**: `docs/11-ACTIVE-IMMUNE-SYSTEM/44-PHASE-5-5-COMPLETE-ML-MONITORING.md`
- **Blueprint**: `docs/architecture/security/adaptive-immune-intelligence-blueprint.md`
- **Doutrina**: `.github/copilot-instructions.md`

---

## 🙏 FUNDAMENTAÇÃO ESPIRITUAL

**"Examinai tudo. Retende o bem."** - 1 Tessalonicenses 5:21

Phase 5.6 implementa exame crítico do sistema ML. Assim como o apóstolo Paulo nos instrui a examinar tudo, o A/B testing valida cada predição contra a verdade (wargaming ground truth).

Não confiamos cegamente na máquina. Validamos. Aprendemos. Melhoramos. **Glory to YHWH**, que nos dá discernimento para construir sistemas resilientes e verificáveis.

---

**Status**: 📋 **READY FOR EXECUTION**  
**Estimated Duration**: 3-4 hours  
**Next**: Execute STEP 1 (PostgreSQL Setup)

🧬 _"Test all things. Hold fast to what is good. Continuous learning through validation. Glory to YHWH."_
