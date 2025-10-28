# 📊 COVERAGE BOOST PLAN - Path to 100%

**Status:** READY TO EXECUTE  
**Target:** LRR 96% → 100%, MEA 88-96% → 100%  
**Time:** 1-2 horas (amanhã)  

---

## 🎯 CURRENT STATUS

### LRR Coverage: 96.05% (Target: 100%)

| File | Current | Missing | Lines to Cover |
|------|---------|---------|----------------|
| `recursive_reasoner.py` | 96.05% | 10 | 431, 518, 813, 822-823, 930, 932, 970-973, 994 |
| `contradiction_detector.py` | 95.54% | 4 | 260, 264, 266, 315 |
| `meta_monitor.py` | 92.91% | 5 | 79, 82, 125, 149, 199 |
| `introspection_engine.py` | 100% | 0 | ✅ PERFEITO |

**Gap:** 19 linhas = 4% remaining

---

### MEA Coverage: 88-96% (Target: 100%)

| File | Current | Missing | Lines to Cover |
|------|---------|---------|----------------|
| `attention_schema.py` | 88.43% | 8 | 145, 161, 171, 196-197, 213-214, 232 |
| `boundary_detector.py` | 96.67% | 1 | 103 |
| `prediction_validator.py` | 95.65% | 1 | 93 |
| `self_model.py` | 93.65% | 2 | 68, 78 |

**Gap:** 12 linhas = 7-12% remaining

---

## 📋 ACTION PLAN

### Phase 1: MEA Boost (30 min)

#### Task 1: boundary_detector.py (1 linha)
**Missing:** Linha 103 (mean_strength == 0 edge case)

**Test to Add:**
```python
def test_boundary_stability_zero_strength():
    """Test stability when mean strength is zero."""
    detector = BoundaryDetector()
    
    # Feed signals with zero strength
    for _ in range(10):
        signals = BoundarySignals(
            proprioceptive_intensity=0.0,
            exteroceptive_intensity=0.0,
        )
        detector.assess_boundary(signals)
    
    stability = detector._compute_stability()
    assert stability == 0.0  # Covers line 103
```

#### Task 2: prediction_validator.py (1 linha)
**Missing:** Linha 93 (len(predictions) < 2 edge case)

**Test to Add:**
```python
def test_focus_switch_rate_single_prediction():
    """Test switch rate with only one prediction."""
    validator = PredictionValidator()
    
    state = AttentionState(focus_target="test", confidence=0.9, ...)
    validator.validate_prediction(state, "test")
    
    # Simulate metrics computation with 1 prediction
    rate = validator._compute_focus_switch_rate([state])
    assert rate == 0.0  # Covers line 93
```

#### Task 3: self_model.py (2 linhas)
**Missing:** Linhas 68, 78 (RuntimeError raises for uninitialized)

**Tests to Add:**
```python
def test_self_model_current_perspective_uninitialized():
    """Test accessing perspective before initialization."""
    model = SelfModel()
    
    with pytest.raises(RuntimeError, match="not been initialised"):
        _ = model.current_perspective()  # Covers line 68

def test_self_model_current_boundary_uninitialized():
    """Test accessing boundary before initialization."""
    model = SelfModel()
    
    with pytest.raises(RuntimeError, match="not been initialised"):
        _ = model.current_boundary()  # Covers line 78
```

#### Task 4: attention_schema.py (8 linhas)
**Missing:** Linhas 145, 161, 171, 196-197, 213-214, 232

**Tests to Add:**
```python
def test_attention_schema_record_outcome_no_state():
    """Test recording outcome without prior state."""
    model = AttentionSchemaModel()
    
    with pytest.raises(RuntimeError, match="No attention state"):
        model.record_prediction_outcome("target")  # Covers line 145

def test_attention_schema_accuracy_empty():
    """Test accuracy with no traces."""
    model = AttentionSchemaModel()
    
    accuracy = model.prediction_accuracy()
    assert accuracy == 0.0  # Covers line 161

def test_attention_schema_calibration_empty():
    """Test calibration with no traces."""
    model = AttentionSchemaModel()
    
    calibration = model.prediction_calibration()
    assert calibration == 0.0  # Covers line 171

# Add more for remaining lines...
```

---

### Phase 2: LRR Boost (45 min)

#### Task 1: meta_monitor.py (5 linhas)
**Missing:** Linhas 79, 82, 125, 149, 199

**Analysis:** Edge cases em MetaMonitor
- Line 79: Zero levels edge case
- Line 82: Empty history edge case
- Line 125: No bias detection
- Line 149: Zero standard deviation
- Line 199: Empty recommendations

**Tests to Add:**
```python
def test_meta_monitor_zero_levels():
    """Test metrics with zero reasoning levels."""
    monitor = MetaMonitor()
    metrics = monitor.collect_metrics([])  # Empty levels
    # Verify edge case handling - covers line 79

def test_meta_monitor_empty_history():
    """Test with empty history."""
    monitor = MetaMonitor()
    # Test scenario that hits line 82

def test_meta_monitor_no_biases():
    """Test bias detection when no biases present."""
    # Covers line 125

def test_meta_monitor_zero_stdev():
    """Test confidence calibration with zero stdev."""
    # Covers line 149

def test_meta_monitor_no_recommendations():
    """Test recommendation generation with no issues."""
    # Covers line 199
```

#### Task 2: contradiction_detector.py (4 linhas)
**Missing:** Linhas 260, 264, 266, 315

**Analysis:** Edge cases em contradiction detection
- Lines 260-266: Specific contradiction type handling
- Line 315: Edge case in resolution

**Tests to Add:**
```python
def test_contradiction_specific_type_edges():
    """Test edge cases in contradiction type detection."""
    # Covers lines 260, 264, 266

def test_contradiction_resolution_edge():
    """Test resolution edge case."""
    # Covers line 315
```

#### Task 3: recursive_reasoner.py (10 linhas)
**Missing:** Linhas 431, 518, 813, 822-823, 930, 932, 970-973, 994

**Analysis:** Complex edge cases em recursive reasoning
- Line 431: Justification chain edge
- Line 518: Meta-belief generation edge
- Line 813: Coherence calculation edge
- Lines 822-823: Contradiction handling edges
- Lines 930, 932: Meta-level reasoning edges
- Lines 970-973: Integration edges
- Line 994: Final edge case

**Tests to Add:**
```python
def test_recursive_reasoner_justification_edge():
    """Test justification chain edge case."""
    # Covers line 431

def test_recursive_reasoner_meta_belief_edge():
    """Test meta-belief generation edge."""
    # Covers line 518

def test_recursive_reasoner_coherence_edge():
    """Test coherence calculation edge."""
    # Covers line 813

def test_recursive_reasoner_contradiction_edges():
    """Test contradiction handling edges."""
    # Covers lines 822-823

def test_recursive_reasoner_meta_level_edges():
    """Test meta-level reasoning edges."""
    # Covers lines 930, 932

def test_recursive_reasoner_integration_edges():
    """Test integration edge cases."""
    # Covers lines 970-973

def test_recursive_reasoner_final_edge():
    """Test final edge case."""
    # Covers line 994
```

---

## 📊 EXPECTED RESULTS

### After MEA Boost
- `boundary_detector.py`: 96.67% → **100%** (+1 test)
- `prediction_validator.py`: 95.65% → **100%** (+1 test)
- `self_model.py`: 93.65% → **100%** (+2 tests)
- `attention_schema.py`: 88.43% → **100%** (+5-8 tests)

**Total:** +9-12 new tests, MEA coverage: **100%** ✅

### After LRR Boost
- `meta_monitor.py`: 92.91% → **100%** (+5 tests)
- `contradiction_detector.py`: 95.54% → **100%** (+2-3 tests)
- `recursive_reasoner.py`: 96.05% → **100%** (+7-10 tests)

**Total:** +14-18 new tests, LRR coverage: **100%** ✅

---

## 🎯 SUMMARY

**Total Work:**
- New tests to write: ~23-30
- Time estimate: 1-2 hours
- Files to modify: 2 (test_mea.py, test_recursive_reasoner.py)

**Result:**
- MEA: 88-96% → **100%**
- LRR: 96% → **100%**
- Both components: **PERFECT COVERAGE** ✅

---

## ✅ EXECUTION CHECKLIST

- [ ] Phase 1.1: boundary_detector test (+1)
- [ ] Phase 1.2: prediction_validator test (+1)
- [ ] Phase 1.3: self_model tests (+2)
- [ ] Phase 1.4: attention_schema tests (+5-8)
- [ ] Run MEA tests: `pytest consciousness/mea/ --cov=consciousness/mea`
- [ ] Verify MEA 100% ✅
- [ ] Phase 2.1: meta_monitor tests (+5)
- [ ] Phase 2.2: contradiction_detector tests (+2-3)
- [ ] Phase 2.3: recursive_reasoner tests (+7-10)
- [ ] Run LRR tests: `pytest consciousness/lrr/ --cov=consciousness/lrr`
- [ ] Verify LRR 100% ✅
- [ ] Commit: "feat: Coverage 100% LRR + MEA - Perfect Testing"

---

## 🙏 MOTIVATION

> "Foi tão fácil conseguir, mas eu te pergunto: e aí?" - Raul Seixas

Chegamos a 96-88%. Os últimos 4-12% são **detalhes**.  
Mas são **detalhes que fazem a diferença** entre bom e PERFEITO.

**Vamos buscar os 100%!** 🔥

Tomorrow we finish what we started today.  
Tomorrow we achieve **PERFECT COVERAGE**.  
Tomorrow we prove that **excellence is possible**.

**Amém!** 🙏

---

**Created:** 2025-10-10  
**Status:** READY TO EXECUTE (tomorrow)  
**Target:** 100% coverage LRR + MEA  
**Time:** 1-2 hours focused work  

*"Tá boa demais essa negócio, vamo que vamo!"* 🎸
