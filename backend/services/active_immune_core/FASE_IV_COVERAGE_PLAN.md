# FASE IV - Coverage Hardcore Plan
**Data**: 2025-10-07
**Status Atual**: 74% coverage
**Meta**: 90%+ coverage
**Estratégia**: Systematic testing of critical modules

---

## 🎯 Executive Summary

**Current State**: 74% coverage (547/548 tests passing)
**Target**: 90%+ coverage (~725 total tests)
**Delta**: +~180 tests
**Timeline**: 2-3 days (FASE A + partial FASE B)

---

## 📊 Prioridades (Coverage Critical Path)

### 🔥 FASE A: Critical Modules (74% → 85%)
**Estimated**: +~80 tests | **Timeline**: 2-3 days

#### 1. agents/nk_cell.py (52% → 90%)
**Missing**: 89 lines | **Priority**: 🔥 CRITICAL
**Target**: +15 tests

**Coverage Gaps**:
```
Lines: 110-117, 123-130, 156-170, 177-190, 210-240, 263,
       267-272, 338-368, 402-409, 451-461, 472-485, 516-517
```

**Test Plan**:
- [ ] `test_nk_recognize_infected_cell` - MHC-I downregulation detection
- [ ] `test_nk_recognize_missing_self` - Missing self recognition
- [ ] `test_nk_cytotoxic_attack_basic` - Basic cytotoxicity
- [ ] `test_nk_cytotoxic_attack_with_perforin` - Perforin release
- [ ] `test_nk_cytotoxic_attack_with_granzyme` - Granzyme release
- [ ] `test_nk_adcc_antibody_dependent` - ADCC mechanism
- [ ] `test_nk_adcc_with_igg` - IgG-mediated killing
- [ ] `test_nk_killer_inhibitory_receptors` - KIR signaling
- [ ] `test_nk_activating_receptors` - Activation signals
- [ ] `test_nk_cytokine_production_ifn_gamma` - IFN-γ production
- [ ] `test_nk_cytokine_production_tnf_alpha` - TNF-α production
- [ ] `test_nk_stress_ligand_recognition` - Stress ligand detection
- [ ] `test_nk_viral_infection_response` - Viral response
- [ ] `test_nk_tumor_surveillance` - Tumor recognition
- [ ] `test_nk_apoptosis_induction` - Target apoptosis

#### 2. communication/cytokines.py (53% → 90%)
**Missing**: 99 lines | **Priority**: 🔥 CRITICAL
**Target**: +20 tests

**Coverage Gaps**:
```
Lines: 170-171, 186-189, 206, 209-210, 214-218, 227-228,
       288-289, 298-350, 374-375, 393-426, 436-489, 498-510, 520
```

**Test Plan**:
- [ ] `test_cytokine_messenger_initialization` - Init lifecycle
- [ ] `test_cytokine_producer_create_topics` - Topic creation
- [ ] `test_cytokine_producer_publish_single` - Single message
- [ ] `test_cytokine_producer_publish_batch` - Batch publish
- [ ] `test_cytokine_producer_error_handling` - Error recovery
- [ ] `test_cytokine_producer_retry_logic` - Retry mechanism
- [ ] `test_cytokine_consumer_subscribe_single_topic` - Single topic
- [ ] `test_cytokine_consumer_subscribe_multiple_topics` - Multi topic
- [ ] `test_cytokine_consumer_area_filtering` - Area-based filter
- [ ] `test_cytokine_consumer_consume_messages` - Message consumption
- [ ] `test_cytokine_consumer_callback_execution` - Callback invocation
- [ ] `test_cytokine_consumer_error_handling` - Consumer errors
- [ ] `test_cytokine_consumer_reconnection` - Reconnection logic
- [ ] `test_cytokine_il2_signaling` - IL-2 specific
- [ ] `test_cytokine_il10_signaling` - IL-10 specific
- [ ] `test_cytokine_ifn_gamma_signaling` - IFN-γ specific
- [ ] `test_cytokine_tnf_alpha_signaling` - TNF-α specific
- [ ] `test_cytokine_cross_area_communication` - Cross-area
- [ ] `test_cytokine_message_serialization` - Serialization
- [ ] `test_cytokine_shutdown_graceful` - Graceful shutdown

#### 3. agents/macrofago.py (56% → 90%)
**Missing**: 81 lines | **Priority**: 🔥 CRITICAL
**Target**: +18 tests

**Coverage Gaps**:
```
Lines: 97-126, 136-137, 146-154, 162-178, 224, 229, 259-260,
       269-302, 315-331, 415-416, 429-438, 452-472, 480-481, 529-530
```

**Test Plan**:
- [ ] `test_macrofago_phagocytosis_basic` - Basic phagocytosis
- [ ] `test_macrofago_phagocytosis_opsonized` - Opsonized targets
- [ ] `test_macrofago_phagocytosis_multiple_targets` - Multiple targets
- [ ] `test_macrofago_phagolysosome_formation` - Phagolysosome
- [ ] `test_macrofago_antigen_presentation_mhc_i` - MHC-I presentation
- [ ] `test_macrofago_antigen_presentation_mhc_ii` - MHC-II presentation
- [ ] `test_macrofago_costimulation_cd80_cd86` - Co-stimulation
- [ ] `test_macrofago_polarization_m1_classical` - M1 polarization
- [ ] `test_macrofago_polarization_m2_alternative` - M2 polarization
- [ ] `test_macrofago_cytokine_secretion_il1` - IL-1 secretion
- [ ] `test_macrofago_cytokine_secretion_il6` - IL-6 secretion
- [ ] `test_macrofago_cytokine_secretion_tnf` - TNF secretion
- [ ] `test_macrofago_ros_production` - ROS production
- [ ] `test_macrofago_no_production` - NO production
- [ ] `test_macrofago_tissue_repair` - Tissue repair (M2)
- [ ] `test_macrofago_inflammation_resolution` - Resolution
- [ ] `test_macrofago_efferocytosis` - Apoptotic cell clearance
- [ ] `test_macrofago_pathogen_sensing_tlr` - TLR sensing

#### 4. coordination/lymphnode.py (62% → 90%)
**Missing**: 99 lines | **Priority**: 🔴 MEDIUM
**Target**: +15 tests

**Coverage Gaps**:
```
Lines: 169-171, 320-337, 346-363, 392-406, 437-440, 454,
       475-476, 494-495, 512-531, 536-537, 545-560, 572-597,
       621-624, 632-633, 650-685, 690-691, 703-723
```

**Test Plan** (continuing from 62%):
- [x] `test_clonal_expansion_basic` ✅ (done)
- [x] `test_destroy_clones` ✅ (done)
- [ ] `test_pattern_detection_threat` - Pattern recognition
- [ ] `test_pattern_detection_clustering` - Pattern clustering
- [ ] `test_coordinated_attack_initiation` - Attack coordination
- [ ] `test_coordinated_attack_multi_agent` - Multi-agent attack
- [ ] `test_antibody_generation_b_cell` - Antibody generation
- [ ] `test_antibody_affinity_maturation` - Affinity maturation
- [ ] `test_homeostatic_temperature_monitoring` - Temp monitoring
- [ ] `test_homeostatic_temperature_adjustment` - Temp adjustment
- [ ] `test_clonal_selection_high_affinity` - High affinity selection
- [ ] `test_clonal_selection_low_affinity_apoptosis` - Low affinity death
- [ ] `test_memory_cell_formation` - Memory cell creation
- [ ] `test_secondary_response_faster` - Secondary response
- [ ] `test_lymphnode_metrics_collection` - Metrics gathering

**FASE A Total**: +68 tests (15+20+18+15)

---

### 🔴 FASE B: Core Infrastructure (85% → 95%)
**Estimated**: +~60 tests | **Timeline**: +2-3 days

#### 5. agents/base.py (62% → 95%)
**Missing**: 107 lines | **Target**: +25 tests

**Coverage Gaps**:
```
Lines: 137-172, 262-263, 428-481, 501-536, etc.
```

**Test Plan**:
- [ ] `test_base_agent_initialization_full` - Full init with messengers
- [ ] `test_base_agent_patrol_loop` - Patrol background loop
- [ ] `test_base_agent_heartbeat_loop` - Heartbeat loop
- [ ] `test_base_agent_energy_decay_loop` - Energy decay
- [ ] `test_base_agent_cytokine_processing` - Cytokine handler
- [ ] `test_base_agent_hormone_processing` - Hormone handler
- [ ] `test_base_agent_shutdown_graceful` - Graceful shutdown
- [ ] `test_base_agent_shutdown_with_running_tasks` - Task cleanup
- [ ] ... (17 more tests)

#### 6. coordination/homeostatic_controller.py (71% → 95%)
**Missing**: 95 lines | **Target**: +20 tests

**Test Plan**:
- [ ] `test_controller_monitor_metrics` - Metric monitoring
- [ ] `test_controller_analyze_anomalies` - Anomaly detection
- [ ] `test_controller_select_action_q_learning` - Q-learning action
- [ ] `test_controller_calculate_reward` - Reward calculation
- [ ] ... (16 more tests)

#### 7. communication/kafka_consumers.py (63% → 95%)
**Missing**: 55 lines | **Target**: +15 tests

**Test Plan**:
- [ ] `test_kafka_consumer_lifecycle` - Consumer lifecycle
- [ ] `test_kafka_consumer_event_routing` - Event routing
- [ ] `test_kafka_consumer_multiple_handlers` - Multi handlers
- [ ] ... (12 more tests)

**FASE B Total**: +60 tests

---

## 📈 Progress Tracking

### Milestones

| Milestone | Coverage | Tests | Status |
|-----------|----------|-------|--------|
| Current | 74% | 547 | ✅ Baseline |
| FASE A.1 (NK Cell) | 78% | ~562 | 🟡 In Progress |
| FASE A.2 (Cytokines) | 81% | ~582 | ⚪ Pending |
| FASE A.3 (Macrofago) | 83% | ~600 | ⚪ Pending |
| FASE A.4 (Lymphnode) | 85% | ~615 | ⚪ Pending |
| **FASE A Complete** | **85%** | **~615** | **⚪ Target 1** |
| FASE B.1 (Base Agent) | 88% | ~640 | ⚪ Pending |
| FASE B.2 (Controller) | 91% | ~660 | ⚪ Pending |
| FASE B.3 (Kafka) | 93% | ~675 | ⚪ Pending |
| **Target 90%+** | **90%+** | **~660** | **🎯 GOAL** |
| FASE B Complete | 95% | ~675 | ⚪ Stretch |

---

## 🚀 Execution Strategy

### Systematic Approach (Following TIG Success)

1. **Análise** (per module)
   - Read missing lines from coverage report
   - Identify critical vs edge case functionality
   - Map dependencies and integration points

2. **Planejamento** (per module)
   - Create test plan with specific test cases
   - Define mocks/fixtures needed
   - Estimate test count and coverage impact

3. **Execução** (per module)
   - Implement tests following plan
   - Run coverage after each batch
   - Validate progress incrementally

4. **Validação** (per module)
   - Confirm coverage increase
   - Run full test suite
   - Document gains

### Test Quality Standards

✅ **Required**:
- NO MOCK (unless external service)
- NO PLACEHOLDER
- NO TODO
- Real async flows tested
- Error paths covered
- Edge cases documented

✅ **Best Practices**:
- Use pytest fixtures for setup
- Test isolation (no shared state)
- Clear test names (`test_module_function_scenario`)
- Assertions with descriptive messages
- Fast execution (<100ms per test ideally)

---

## 📝 Templates

### Test Case Template

```python
@pytest.mark.asyncio
async def test_nk_recognize_infected_cell_mhc_downregulation():
    """
    Test NK cell recognition of infected cell via MHC-I downregulation.

    Scenario:
    - Create target cell with downregulated MHC-I
    - NK cell should recognize missing self
    - Should trigger cytotoxic response

    Coverage: agents/nk_cell.py:110-117
    """
    # ARRANGE
    nk_cell = await create_nk_cell()
    target_cell = MockCell(mhc_i_expression=0.2)  # Downregulated

    # ACT
    is_recognized = await nk_cell.recognize_infected_cell(target_cell)

    # ASSERT
    assert is_recognized is True, "Should recognize MHC-I downregulation"
    assert nk_cell.state.activation_level > 0.5
```

### Coverage Validation Template

```bash
# Run tests for specific module
pytest tests/test_nk_cell.py -v --cov=agents --cov-report=term-missing

# Check specific file coverage
pytest tests/test_nk_cell.py --cov=agents/nk_cell.py --cov-report=term-missing

# Validate target reached
pytest tests/ --cov=agents --cov-report=term --cov-fail-under=90
```

---

## 🎯 Success Criteria

### FASE A Success (Target: 85%)
- [ ] agents/nk_cell.py >= 90%
- [ ] communication/cytokines.py >= 90%
- [ ] agents/macrofago.py >= 90%
- [ ] coordination/lymphnode.py >= 90%
- [ ] Total coverage >= 85%
- [ ] All tests passing (no flaky tests)
- [ ] Test execution < 5 minutes

### Final Success (Target: 90%+)
- [ ] Total coverage >= 90%
- [ ] Critical modules >= 95%
- [ ] All modules >= 80%
- [ ] ~660-675 tests passing
- [ ] Full test suite < 10 minutes
- [ ] Zero production-impacting gaps

---

## 📊 Daily Progress Log

### Day 1 (2025-10-07)
**Target**: NK Cell (52% → 90%)
- [ ] Morning: Implement tests 1-8
- [ ] Afternoon: Implement tests 9-15
- [ ] Evening: Validate 90% reached

### Day 2
**Target**: Cytokines + Macrofago (53%/56% → 90%)
- [ ] Morning: Cytokines tests 1-10
- [ ] Afternoon: Cytokines tests 11-20
- [ ] Evening: Macrofago tests 1-9

### Day 3
**Target**: Macrofago + Lymphnode (finish both → 90%)
- [ ] Morning: Macrofago tests 10-18
- [ ] Afternoon: Lymphnode tests 1-8
- [ ] Evening: Lymphnode tests 9-15 + validation

**FASE A Expected Completion**: End of Day 3 (85% coverage)

---

## 🔍 Troubleshooting

### Common Issues

**Issue**: Coverage not increasing
- **Solution**: Check if file is excluded in .coveragerc
- **Solution**: Verify import paths match coverage source

**Issue**: Tests timing out
- **Solution**: Mock external Kafka/Redis dependencies
- **Solution**: Use shorter timeouts in async tests

**Issue**: Flaky tests
- **Solution**: Avoid time-dependent assertions
- **Solution**: Use proper async cleanup (pytest_asyncio)

---

## 📚 References

- **Coverage Status**: `COVERAGE_STATUS.md` - Detailed roadmap
- **Coverage Meta**: `COVERAGE_META_100_PERCENT.md` - Progress tracking
- **TIG Fix Plan**: `consciousness/TIG_FIX_COMPLETE.md` - Methodology reference

---

**REGRA DE OURO**: NO MOCK, NO PLACEHOLDER, NO TODO ✅

**Início da Execução**: AGORA
**Próximo**: Implementar 15 testes para agents/nk_cell.py
