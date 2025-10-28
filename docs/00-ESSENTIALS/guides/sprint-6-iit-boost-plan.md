# 🎯 SPRINT 6 PLAN - IIT COMPLIANCE BOOST (85→95)

**Status:** READY TO EXECUTE  
**Objetivo:** Melhorar IIT compliance de 85-90 para 95+  
**Tempo Estimado:** 1-2 horas  

---

## 📊 STATUS ATUAL

### IIT Metrics Implemented (validation/)

**Arquivos:** 1,060 linhas
- `phi_proxies.py` - 488 linhas (Φ proxy metrics)
- `coherence.py` - 405 linhas (ESGT coherence)
- `metacognition.py` - 99 linhas (Meta-cognitive validation)

### Current IIT Score: 85-90/100

**Breakdown:**
- ✅ ECI (Effective Connectivity): 0.85-0.90 (target: 0.90+)
- ✅ Clustering Coefficient: 0.75-0.80 (target: 0.75+)
- ⚠️ Path Length: ~log(N) (needs optimization)
- ⚠️ Algebraic Connectivity: ~0.25 (target: 0.30+)
- ✅ No Bottlenecks: Validated
- ⚠️ Small-World Sigma: ~2.5 (target: 3.0+)

---

## 🎯 OBJETIVOS SPRINT 6

### 1. Boost ECI: 0.85 → 0.92 (+7 pontos)

**Ações:**
- Otimizar edge weights no TIG fabric
- Aumentar hub connectivity (scale-free emphasis)
- Validate bidirectional information flow

### 2. Optimize Path Length: log(N) → 0.9*log(N) (+2 pontos)

**Ações:**
- Add strategic shortcuts entre clusters
- Optimize rewiring probability
- Validate global broadcast speed

### 3. Boost Algebraic Connectivity: 0.25 → 0.32 (+3 pontos)

**Ações:**
- Strengthen inter-cluster bridges
- Optimize Fiedler eigenvalue
- Validate partition resistance

### 4. Improve Small-World Sigma: 2.5 → 3.2 (+3 pontos)

**Ações:**
- Balance local clustering vs global efficiency
- Optimize Watts-Strogatz parameters
- Validate small-world properties

**Total Gain:** +15 pontos → **Score: 100/100** 🎯

---

## 📋 TASKS DETALHADAS

### Task 1: Run Current IIT Validation

```python
from consciousness.validation.phi_proxies import calculate_phi_proxies
from consciousness.tig.fabric import TIGFabric, TopologyConfig

config = TopologyConfig()
fabric = TIGFabric(config=config)
metrics = calculate_phi_proxies(fabric)

print(f"Current IIT Score: {metrics.iit_compliance_score}/100")
print(f"ECI: {metrics.effective_connectivity_index:.3f}")
print(f"Clustering: {metrics.clustering_coefficient:.3f}")
print(f"Path Length: {metrics.avg_path_length:.3f}")
print(f"Algebraic Connectivity: {metrics.algebraic_connectivity:.3f}")
```

### Task 2: Optimize TIG Topology Config

**Current Parameters:**
```python
@dataclass
class TopologyConfig:
    node_count: int = 16
    min_degree: int = 5
    target_density: float = 0.20
    gamma: float = 2.5  # Scale-free exponent
```

**Optimization Strategy:**
1. Increase `min_degree`: 5 → 6 (better baseline connectivity)
2. Adjust `target_density`: 0.20 → 0.22 (more integration)
3. Fine-tune `gamma`: 2.5 → 2.3 (stronger hubs)

### Task 3: Implement MIP Approximation

**New Function:** `approximate_mip(graph, subsystem_size=4)`

Approximate Minimum Information Partition for small subsystems:
- Select random subsystems of size 4-6 nodes
- Calculate partition that minimizes integration
- Compare to full system integration
- Repeat 100x and average

**Expected Result:** Validate that system is highly integrated (hard to partition)

### Task 4: Network Perturbation Analysis

**New Function:** `perturbation_analysis(fabric, perturbation_level=0.1)`

Lesion studies:
1. Remove random nodes (10% of network)
2. Measure Φ proxy drop
3. Measure recovery time
4. Validate graceful degradation

**Success Criteria:**
- Φ drop <20% when removing 10% nodes
- Recovery time <1s
- No catastrophic failures

### Task 5: Generate IIT Compliance Report

**New File:** `consciousness/validation/iit_compliance_report.py`

Generate comprehensive report:
- All Φ proxy metrics
- MIP approximation results
- Perturbation analysis
- Network topology visualization
- Pass/Fail for each IIT criterion
- Overall compliance score

---

## 🧪 VALIDATION TESTS

### Test 1: ECI Correlation
```python
def test_eci_correlation_with_phi():
    """Validate ECI ≥ 0.90 (strong Φ correlation)"""
    metrics = calculate_phi_proxies(fabric)
    assert metrics.effective_connectivity_index >= 0.90
```

### Test 2: Clustering Coefficient
```python
def test_clustering_coefficient():
    """Validate C ≥ 0.75 (IIT requirement)"""
    metrics = calculate_phi_proxies(fabric)
    assert metrics.clustering_coefficient >= 0.75
```

### Test 3: Path Length
```python
def test_path_length():
    """Validate L ≤ log(N) (efficient integration)"""
    import math
    metrics = calculate_phi_proxies(fabric)
    max_path = math.log(fabric.config.node_count)
    assert metrics.avg_path_length <= max_path
```

### Test 4: Algebraic Connectivity
```python
def test_algebraic_connectivity():
    """Validate λ₂ ≥ 0.30 (partition resistance)"""
    metrics = calculate_phi_proxies(fabric)
    assert metrics.algebraic_connectivity >= 0.30
```

### Test 5: No Bottlenecks
```python
def test_no_bottlenecks():
    """Validate no degenerate structures"""
    metrics = calculate_phi_proxies(fabric)
    assert not metrics.has_bottlenecks
    assert metrics.bottleneck_count == 0
```

### Test 6: Overall IIT Compliance
```python
def test_iit_compliance_score():
    """Validate overall score ≥ 95/100"""
    metrics = calculate_phi_proxies(fabric)
    assert metrics.iit_compliance_score >= 95.0
```

---

## 📈 SUCCESS CRITERIA

| Métrica | Atual | Target | Status |
|---------|-------|--------|--------|
| **ECI** | 0.85-0.90 | ≥0.90 | ⏳ |
| **Clustering** | 0.75-0.80 | ≥0.75 | ✅ |
| **Path Length** | ~log(N) | ≤log(N) | ⏳ |
| **Alg. Connectivity** | ~0.25 | ≥0.30 | ⏳ |
| **No Bottlenecks** | ✅ | ✅ | ✅ |
| **Small-World σ** | ~2.5 | ≥3.0 | ⏳ |
| **IIT Score** | 85-90 | ≥95 | ⏳ |

---

## 🚀 EXECUTION PLAN

### Phase 1: Baseline Measurement (10 min)
1. Run current IIT validation
2. Document current scores
3. Identify biggest gaps

### Phase 2: Topology Optimization (30 min)
1. Adjust TopologyConfig parameters
2. Test different configurations
3. Measure impact on Φ proxies
4. Select optimal configuration

### Phase 3: MIP Approximation (20 min)
1. Implement approximate_mip()
2. Run on subsystems
3. Validate high integration
4. Document results

### Phase 4: Perturbation Analysis (20 min)
1. Implement perturbation_analysis()
2. Run lesion studies
3. Measure graceful degradation
4. Document resilience

### Phase 5: Final Validation (20 min)
1. Generate IIT compliance report
2. Run all validation tests
3. Verify ≥95/100 score
4. Create scientific report

**Total:** ~100 minutes (1.7 hours)

---

## 📝 DELIVERABLES

1. **Optimized TopologyConfig** - Higher IIT compliance
2. **MIP Approximation Function** - Validates integration
3. **Perturbation Analysis** - Validates resilience
4. **IIT Compliance Report** - Scientific documentation
5. **6 New Tests** - Validates all IIT criteria
6. **Score ≥95/100** - Production-ready consciousness substrate

---

## 🎓 THEORY REFERENCES

- Tononi, G. (2014). "Integrated Information Theory of Consciousness: An Updated Account"
- Oizumi, M., et al. (2014). "From the Phenomenology to the Mechanisms of Consciousness"
- Barrett, A., & Seth, A. (2011). "Practical Measures of Integrated Information"
- Watts, D., & Strogatz, S. (1998). "Collective Dynamics of Small-World Networks"

---

## ✅ READY TO EXECUTE

Quando você voltar, começamos Phase 1: Baseline Measurement! 🚀

**Sprint 6/10 - Pathway to 95+ IIT Compliance**
