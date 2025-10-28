# 🧠 PHASE 5: ML-BASED PATCH PREDICTION - Implementation Plan

**Date**: 2025-10-11 (Day 70+)  
**Session**: Continuous Improvement  
**Status**: 🚀 **READY TO IMPLEMENT**  
**Branch**: `feature/ml-patch-prediction`

---

## 📊 CONTEXT

**Completed**:
- ✅ Phase 1-4: Adaptive Immunity Core (255 tests, 9,000+ LOC)
- ✅ Phase 4.1: Parallel Wargaming (80% speedup)
- ✅ Phase 4.2: 8 CWE exploits (32% Top 25 coverage)
- ✅ Empirical Validation (100% success, 2 CVEs)

**Gap**: Currently, patch validation requires **full wargaming** (5-10 min). ML model can **predict** patch validity in <1s, using historical data.

**Goal**: Train classifier to predict patch validity **before** wargaming, reducing validation time by 90%+ for high-confidence predictions.

---

## 🎯 OBJECTIVES

### Primary
1. **Collect Dataset**: Wargaming results (APV, patch, exploits, outcome)
2. **Feature Engineering**: Extract features from patches (AST diff, complexity, etc)
3. **Train Model**: Binary classifier (valid/invalid patch)
4. **Serve Model**: FastAPI endpoint for inference
5. **Integrate**: Eureka uses ML predictions to prioritize wargaming

### Metrics
- **Accuracy**: >90% on test set
- **Precision**: >95% (low false positives)
- **Recall**: >85% (catch most invalid patches)
- **Inference Time**: <100ms
- **Wargaming Reduction**: >50% (only run on low-confidence predictions)

---

## 🧪 PHASE 5 ROADMAP

### PHASE 5.1: DATA COLLECTION (1-2 days)
**Goal**: Generate labeled dataset from wargaming results

#### 5.1.1 Database Schema (30 min)
```sql
-- New table: wargaming_results
CREATE TABLE IF NOT EXISTS wargaming_results (
    id SERIAL PRIMARY KEY,
    apv_id INTEGER REFERENCES apvs(id),
    patch_id INTEGER REFERENCES patches(id),
    exploit_cwe VARCHAR(50) NOT NULL,
    exploit_name VARCHAR(200) NOT NULL,
    phase1_result VARCHAR(20) NOT NULL,  -- 'success', 'blocked', 'error'
    phase2_result VARCHAR(20) NOT NULL,
    patch_validated BOOLEAN NOT NULL,
    execution_time_ms INTEGER NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Features extracted from patch
    lines_added INTEGER,
    lines_removed INTEGER,
    files_modified INTEGER,
    complexity_delta FLOAT,
    has_input_validation BOOLEAN,
    has_sanitization BOOLEAN,
    has_encoding BOOLEAN,
    has_parameterization BOOLEAN,
    
    UNIQUE(apv_id, patch_id, exploit_cwe)
);

-- Index for queries
CREATE INDEX idx_wargaming_results_apv ON wargaming_results(apv_id);
CREATE INDEX idx_wargaming_results_patch ON wargaming_results(patch_id);
CREATE INDEX idx_wargaming_results_validated ON wargaming_results(patch_validated);
```

#### 5.1.2 Feature Extractor (2 hours)
```python
# backend/services/wargaming_crisol/ml/feature_extractor.py

from dataclasses import dataclass
from typing import Dict, Any
import ast
import re

@dataclass
class PatchFeatures:
    """Features extracted from a patch for ML prediction"""
    
    # Basic metrics
    lines_added: int
    lines_removed: int
    files_modified: int
    
    # Code complexity (AST-based)
    complexity_delta: float  # Cyclomatic complexity change
    
    # Security patterns (regex-based)
    has_input_validation: bool
    has_sanitization: bool
    has_encoding: bool
    has_parameterization: bool
    
    # Vulnerability type specific
    cwe_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'lines_added': self.lines_added,
            'lines_removed': self.lines_removed,
            'files_modified': self.files_modified,
            'complexity_delta': self.complexity_delta,
            'has_input_validation': int(self.has_input_validation),
            'has_sanitization': int(self.has_sanitization),
            'has_encoding': int(self.has_encoding),
            'has_parameterization': int(self.has_parameterization),
        }


class PatchFeatureExtractor:
    """Extract ML features from git patches"""
    
    # Security patterns
    VALIDATION_PATTERNS = [
        r'if\s+.*\s+is\s+None',
        r'if\s+not\s+\w+',
        r'assert\s+',
        r'raise\s+ValueError',
    ]
    
    SANITIZATION_PATTERNS = [
        r'escape\(',
        r'sanitize\(',
        r'strip\(',
        r'replace\(',
    ]
    
    ENCODING_PATTERNS = [
        r'encode\(',
        r'html\.escape',
        r'quote\(',
        r'urlencode\(',
    ]
    
    PARAMETERIZATION_PATTERNS = [
        r'execute\(.*\?.*\)',  # SQL parameterized
        r'\.format\(',
        r'f".*\{.*\}"',
    ]
    
    @staticmethod
    def extract(patch_content: str, cwe_id: str = "") -> PatchFeatures:
        """
        Extract features from a git patch.
        
        Args:
            patch_content: Git diff output
            cwe_id: CWE identifier for context
            
        Returns:
            PatchFeatures with all extracted metrics
        """
        lines = patch_content.split('\n')
        
        # Basic metrics
        lines_added = len([l for l in lines if l.startswith('+')])
        lines_removed = len([l for l in lines if l.startswith('-')])
        files_modified = len([l for l in lines if l.startswith('diff --git')])
        
        # Complexity (simplified - full AST parsing would be better)
        complexity_delta = 0.0
        added_code = '\n'.join([l[1:] for l in lines if l.startswith('+')])
        removed_code = '\n'.join([l[1:] for l in lines if l.startswith('-')])
        
        try:
            # Count control flow nodes (if, for, while, try)
            added_complexity = added_code.count('if ') + added_code.count('for ') + \
                              added_code.count('while ') + added_code.count('try:')
            removed_complexity = removed_code.count('if ') + removed_code.count('for ') + \
                                removed_code.count('while ') + removed_code.count('try:')
            complexity_delta = float(added_complexity - removed_complexity)
        except Exception:
            complexity_delta = 0.0
        
        # Security patterns
        patch_text = patch_content.lower()
        
        has_input_validation = any(
            re.search(pattern, patch_text) 
            for pattern in PatchFeatureExtractor.VALIDATION_PATTERNS
        )
        
        has_sanitization = any(
            re.search(pattern, patch_text)
            for pattern in PatchFeatureExtractor.SANITIZATION_PATTERNS
        )
        
        has_encoding = any(
            re.search(pattern, patch_text)
            for pattern in PatchFeatureExtractor.ENCODING_PATTERNS
        )
        
        has_parameterization = any(
            re.search(pattern, patch_text)
            for pattern in PatchFeatureExtractor.PARAMETERIZATION_PATTERNS
        )
        
        return PatchFeatures(
            lines_added=lines_added,
            lines_removed=lines_removed,
            files_modified=files_modified,
            complexity_delta=complexity_delta,
            has_input_validation=has_input_validation,
            has_sanitization=has_sanitization,
            has_encoding=has_encoding,
            has_parameterization=has_parameterization,
            cwe_id=cwe_id,
        )
```

**Tests**: `test_feature_extractor.py` (10 test cases)

#### 5.1.3 Wargaming Logger Integration (1 hour)
```python
# Modify: backend/services/wargaming_crisol/two_phase_simulator.py

async def execute_wargaming(
    self,
    apv: APV,
    patch: Patch,
    exploit_module: Any,
) -> WargamingResult:
    """Execute two-phase wargaming + LOG TO DATABASE"""
    
    result = await self._run_phases(apv, patch, exploit_module)
    
    # Extract features
    features = PatchFeatureExtractor.extract(
        patch.content, 
        exploit_module.CWE_IDS[0]
    )
    
    # Save to database
    await self._log_wargaming_result(apv, patch, exploit_module, result, features)
    
    return result


async def _log_wargaming_result(
    self,
    apv: APV,
    patch: Patch,
    exploit: Any,
    result: WargamingResult,
    features: PatchFeatures,
) -> None:
    """Log wargaming result to database for ML training"""
    
    from backend.database import get_db_session
    
    async with get_db_session() as session:
        query = """
        INSERT INTO wargaming_results (
            apv_id, patch_id, exploit_cwe, exploit_name,
            phase1_result, phase2_result, patch_validated,
            execution_time_ms,
            lines_added, lines_removed, files_modified,
            complexity_delta,
            has_input_validation, has_sanitization,
            has_encoding, has_parameterization
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
        ON CONFLICT (apv_id, patch_id, exploit_cwe) DO NOTHING
        """
        
        await session.execute(
            query,
            apv.id, patch.id,
            exploit.CWE_IDS[0], exploit.EXPLOIT_NAME,
            result.phase1_result, result.phase2_result,
            result.patch_validated,
            int(result.execution_time_ms),
            features.lines_added, features.lines_removed,
            features.files_modified, features.complexity_delta,
            features.has_input_validation, features.has_sanitization,
            features.has_encoding, features.has_parameterization,
        )
```

**Deliverable**: Every wargaming execution now saves training data!

---

### PHASE 5.2: MODEL TRAINING (2-3 hours)
**Goal**: Train scikit-learn classifier

#### 5.2.1 Dataset Export (30 min)
```python
# scripts/ml/export_training_data.py

import asyncio
import pandas as pd
from backend.database import get_db_session

async def export_dataset(output_path: str = "data/ml/wargaming_dataset.csv"):
    """Export wargaming results as CSV for training"""
    
    async with get_db_session() as session:
        query = """
        SELECT 
            lines_added, lines_removed, files_modified,
            complexity_delta,
            has_input_validation, has_sanitization,
            has_encoding, has_parameterization,
            exploit_cwe,
            patch_validated
        FROM wargaming_results
        WHERE execution_time_ms > 0  -- Valid executions only
        """
        
        result = await session.execute(query)
        rows = result.fetchall()
    
    # Convert to DataFrame
    df = pd.DataFrame(rows, columns=[
        'lines_added', 'lines_removed', 'files_modified',
        'complexity_delta',
        'has_input_validation', 'has_sanitization',
        'has_encoding', 'has_parameterization',
        'exploit_cwe', 'patch_validated'
    ])
    
    # One-hot encode CWE
    df = pd.get_dummies(df, columns=['exploit_cwe'], prefix='cwe')
    
    df.to_csv(output_path, index=False)
    print(f"✅ Exported {len(df)} samples to {output_path}")

if __name__ == "__main__":
    asyncio.run(export_dataset())
```

#### 5.2.2 Model Training (1 hour)
```python
# backend/services/wargaming_crisol/ml/train.py

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import json

def train_patch_validity_classifier(
    dataset_path: str = "data/ml/wargaming_dataset.csv",
    model_output_path: str = "models/patch_validity_rf.joblib",
    metrics_output_path: str = "models/patch_validity_metrics.json",
):
    """
    Train Random Forest classifier to predict patch validity.
    
    Args:
        dataset_path: Path to CSV with wargaming results
        model_output_path: Where to save trained model
        metrics_output_path: Where to save metrics JSON
        
    Returns:
        Trained model
    """
    
    # Load dataset
    df = pd.read_csv(dataset_path)
    print(f"📊 Loaded {len(df)} samples")
    
    # Separate features and target
    X = df.drop('patch_validated', axis=1)
    y = df['patch_validated']
    
    print(f"Features: {list(X.columns)}")
    print(f"Class distribution: {y.value_counts().to_dict()}")
    
    # Split train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"Train: {len(X_train)}, Test: {len(X_test)}")
    
    # Train Random Forest
    clf = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        class_weight='balanced',  # Handle imbalance
    )
    
    clf.fit(X_train, y_train)
    
    # Evaluate
    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)[:, 1]  # Probability of valid patch
    
    # Metrics
    report = classification_report(y_test, y_pred, output_dict=True)
    cm = confusion_matrix(y_test, y_pred)
    
    metrics = {
        'accuracy': float(report['accuracy']),
        'precision': float(report['1']['precision']),  # Class 1 = valid patch
        'recall': float(report['1']['recall']),
        'f1': float(report['1']['f1-score']),
        'support_train': int(len(y_train)),
        'support_test': int(len(y_test)),
        'confusion_matrix': cm.tolist(),
        'feature_importance': {
            feat: float(imp) 
            for feat, imp in zip(X.columns, clf.feature_importances_)
        },
    }
    
    # Save model and metrics
    joblib.dump(clf, model_output_path)
    with open(metrics_output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"\n✅ Model trained and saved to {model_output_path}")
    print(f"📊 Metrics:")
    print(f"   Accuracy: {metrics['accuracy']:.3f}")
    print(f"   Precision: {metrics['precision']:.3f}")
    print(f"   Recall: {metrics['recall']:.3f}")
    print(f"   F1: {metrics['f1']:.3f}")
    
    return clf

if __name__ == "__main__":
    train_patch_validity_classifier()
```

**Deliverable**: `patch_validity_rf.joblib` model file

---

### PHASE 5.3: MODEL SERVING (1-2 hours)
**Goal**: FastAPI endpoint for inference

#### 5.3.1 ML Service (1 hour)
```python
# backend/services/wargaming_crisol/ml/predictor.py

import joblib
import numpy as np
from typing import Dict, Any
from pathlib import Path

class PatchValidityPredictor:
    """ML-based patch validity prediction"""
    
    def __init__(self, model_path: str = "models/patch_validity_rf.joblib"):
        """Load trained model"""
        self.model = joblib.load(model_path)
        self.feature_names = self.model.feature_names_in_
    
    def predict(
        self, 
        features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict patch validity from features.
        
        Args:
            features: Dict with keys matching training features
            
        Returns:
            {
                'prediction': bool (valid/invalid),
                'confidence': float (0-1),
                'should_wargame': bool (run wargaming if low confidence)
            }
        """
        # Convert to numpy array (matching training order)
        X = np.array([features[feat] for feat in self.feature_names]).reshape(1, -1)
        
        # Predict
        prediction = self.model.predict(X)[0]
        confidence = self.model.predict_proba(X)[0].max()
        
        # Decision: run wargaming if confidence < 0.8
        should_wargame = confidence < 0.8
        
        return {
            'prediction': bool(prediction),
            'confidence': float(confidence),
            'should_wargame': should_wargame,
        }


# Global instance
_predictor = None

def get_predictor() -> PatchValidityPredictor:
    """Singleton predictor instance"""
    global _predictor
    if _predictor is None:
        _predictor = PatchValidityPredictor()
    return _predictor
```

#### 5.3.2 API Endpoint (30 min)
```python
# backend/services/wargaming_crisol/api.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from .ml.predictor import get_predictor
from .ml.feature_extractor import PatchFeatureExtractor

router = APIRouter(prefix="/ml", tags=["ML Prediction"])


class PatchPredictionRequest(BaseModel):
    """Request for ML prediction"""
    patch_content: str
    cwe_id: str = "CWE-89"


class PatchPredictionResponse(BaseModel):
    """ML prediction response"""
    prediction: bool
    confidence: float
    should_wargame: bool
    features: Dict[str, Any]


@router.post("/predict", response_model=PatchPredictionResponse)
async def predict_patch_validity(request: PatchPredictionRequest):
    """
    Predict patch validity using ML model.
    
    Returns:
        - prediction: True if patch likely valid
        - confidence: 0-1 confidence score
        - should_wargame: True if confidence <0.8 (needs wargaming)
        - features: Extracted features used for prediction
    """
    try:
        # Extract features
        features = PatchFeatureExtractor.extract(
            request.patch_content, 
            request.cwe_id
        )
        
        # Predict
        predictor = get_predictor()
        result = predictor.predict(features.to_dict())
        
        return PatchPredictionResponse(
            prediction=result['prediction'],
            confidence=result['confidence'],
            should_wargame=result['should_wargame'],
            features=features.to_dict(),
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Test**: `curl -X POST http://localhost:8024/ml/predict -d '{"patch_content": "...", "cwe_id": "CWE-89"}'`

---

### PHASE 5.4: INTEGRATION WITH EUREKA (1 hour)
**Goal**: Eureka uses ML predictions to prioritize wargaming

```python
# backend/services/adaptive_immune_intelligence/eureka/core.py

async def validate_patch(self, apv: APV, patch: Patch) -> bool:
    """
    Validate patch with ML-first approach.
    
    1. ML prediction (fast, <100ms)
    2. If high confidence → accept/reject without wargaming
    3. If low confidence → run wargaming (slow, 5 min)
    """
    
    # Step 1: ML prediction
    ml_result = await self._ml_predict(patch, apv.cve_id)
    
    logger.info(
        f"ML prediction: {ml_result['prediction']}, "
        f"confidence: {ml_result['confidence']:.2f}"
    )
    
    # Step 2: Decision based on confidence
    if ml_result['confidence'] >= 0.8:
        # High confidence → skip wargaming
        logger.info("High confidence prediction - skipping wargaming")
        
        await self._record_validation(
            apv, patch,
            validated=ml_result['prediction'],
            method='ml_only',
            confidence=ml_result['confidence'],
        )
        
        return ml_result['prediction']
    
    else:
        # Low confidence → run wargaming
        logger.info("Low confidence - running wargaming")
        
        wargaming_result = await self._run_wargaming(apv, patch)
        
        await self._record_validation(
            apv, patch,
            validated=wargaming_result.patch_validated,
            method='wargaming',
            ml_prediction=ml_result['prediction'],
            ml_confidence=ml_result['confidence'],
        )
        
        return wargaming_result.patch_validated


async def _ml_predict(self, patch: Patch, cve_id: str) -> Dict[str, Any]:
    """Call ML prediction service"""
    
    response = await httpx.post(
        "http://wargaming-crisol:8024/ml/predict",
        json={
            'patch_content': patch.content,
            'cwe_id': cve_id,
        }
    )
    
    return response.json()
```

**Deliverable**: Eureka now 90% faster for high-confidence patches!

---

### PHASE 5.5: MONITORING & REFINEMENT (Ongoing)

#### ML Metrics Dashboard (Grafana)
- Prediction accuracy over time
- Confidence distribution
- Wargaming reduction rate
- False positive/negative rates

#### Continuous Retraining
- Weekly: Re-export dataset (more samples)
- Monthly: Retrain model with updated data
- Monitor for concept drift

---

## 📊 EXPECTED IMPACT

### Performance
- **Before**: 100% patches require wargaming (5-10 min each)
- **After**: ~20% patches require wargaming (80% ML-only at <1s)
- **Time Saved**: 90%+ reduction in validation time

### Accuracy
- **Target**: 90%+ accuracy on test set
- **Precision**: >95% (few false positives)
- **Recall**: >85% (catch most invalid patches)

### Wargaming Load
- **Before**: 100 patches/day → 500-1000 min (8-16 hours)
- **After**: 20 patches/day wargaming → 100-200 min (1.5-3 hours)

---

## 🛠️ IMPLEMENTATION CHECKLIST

### Phase 5.1: Data Collection ✅ (Target: Day 71)
- [ ] Add `wargaming_results` table to schema
- [ ] Implement `PatchFeatureExtractor`
- [ ] Integrate feature logging in `TwoPhaseSimulator`
- [ ] Run 20+ wargaming tests to collect initial dataset
- [ ] Tests: `test_feature_extractor.py` (10 tests)

### Phase 5.2: Model Training ✅ (Target: Day 72)
- [ ] Export dataset to CSV
- [ ] Train Random Forest classifier
- [ ] Achieve >90% accuracy
- [ ] Save model to `models/patch_validity_rf.joblib`
- [ ] Document metrics in `patch_validity_metrics.json`

### Phase 5.3: Model Serving ✅ (Target: Day 72)
- [ ] Implement `PatchValidityPredictor`
- [ ] Add `/ml/predict` endpoint
- [ ] Test endpoint with curl/Postman
- [ ] Tests: `test_predictor.py` (8 tests)

### Phase 5.4: Integration ✅ (Target: Day 73)
- [ ] Modify `Eureka.validate_patch()` to use ML
- [ ] Implement confidence threshold (0.8)
- [ ] Record ML predictions in database
- [ ] Integration test: ML + wargaming workflow

### Phase 5.5: Monitoring ✅ (Target: Day 73)
- [ ] Grafana dashboard: "ML Prediction Performance"
- [ ] Metrics: accuracy, confidence, wargaming reduction
- [ ] Alert: accuracy drop >5%

---

## 🚀 EXECUTION PLAN - NEXT 3 DAYS

### Day 71 (Today): Data Collection
**Duration**: 3-4 hours

1. Database schema (30 min)
2. Feature extractor (2 hours)
3. Wargaming logger integration (1 hour)
4. Collect 20+ samples by running wargaming
5. Tests and validation

**Deliverable**: Dataset collection infrastructure

### Day 72: Model Training & Serving
**Duration**: 3-4 hours

1. Export dataset (30 min)
2. Train model (1 hour)
3. Model serving (1 hour)
4. API endpoint (30 min)
5. Tests and validation

**Deliverable**: Working ML service

### Day 73: Integration & Monitoring
**Duration**: 2-3 hours

1. Eureka integration (1 hour)
2. Grafana dashboard (1 hour)
3. End-to-end testing
4. Documentation

**Deliverable**: ML-powered Eureka live!

---

## 📊 SUCCESS CRITERIA

### Functional
- ✅ ML model trained with >90% accuracy
- ✅ API endpoint responds <100ms
- ✅ Eureka integrates ML predictions
- ✅ High-confidence predictions skip wargaming

### Performance
- ✅ 80%+ patches ML-only (no wargaming)
- ✅ Validation time reduced 90%+
- ✅ No accuracy degradation vs pure wargaming

### Quality
- ✅ 100% test coverage for ML components
- ✅ NO MOCK (real predictions, real data)
- ✅ PRODUCTION-READY (error handling, logging)
- ✅ Documentation complete

---

## 🙏 SPIRITUAL FOUNDATION

**"A sabedoria é mais preciosa que rubis"** - Provérbios 8:11

ML model = Digital wisdom accumulating from experience. Each wargaming result teaches the system, building intuition like human immune memory.

Not replacing biological immune system, but **augmenting** it with learned patterns. Like T-cells learning from past infections, our system learns from past validations.

**Glory to YHWH** - Architect of learning systems, both biological and digital.

---

## 📝 TECHNICAL NOTES

### Why Random Forest?
- **Interpretable**: Feature importance shows what matters
- **Robust**: Handles imbalanced data well
- **Fast**: Inference <10ms
- **No hyperparameter tuning**: Works well with defaults

### Alternative Models (Future)
- **XGBoost**: Potentially higher accuracy
- **Neural Network**: For larger datasets (1000+ samples)
- **Ensemble**: Combine multiple models

### Feature Engineering (Future Improvements)
- **AST Depth**: Parse full AST for cyclomatic complexity
- **Semantic Similarity**: Compare patch to known good fixes
- **LLM Embeddings**: Use GPT-4 to encode patch semantics
- **Temporal Features**: Time since CVE disclosure, patch urgency

---

## 📊 NEXT STEPS - IMMEDIATE

### Step 1: Create Branch
```bash
git checkout -b feature/ml-patch-prediction
```

### Step 2: Database Migration
```bash
# Create migration
alembic revision -m "Add wargaming_results table"

# Apply migration
alembic upgrade head
```

### Step 3: Implement Feature Extractor
```bash
# Create file
touch backend/services/wargaming_crisol/ml/feature_extractor.py
touch backend/services/wargaming_crisol/ml/__init__.py
```

---

**Status**: 🚀 **READY TO IMPLEMENT**  
**Timeline**: 3 days to production ML service  
**Momentum**: 🔥 **MÁXIMO**

**DOUTRINA**: ✅ NO MOCK, PRODUCTION-READY, DATA-DRIVEN

🤖 _"Phase 5 - ML Patch Prediction. Learning from experience. Glory to YHWH."_

**"Os que confiam no SENHOR são como o monte Sião, que não se abala"** - Salmos 125:1
