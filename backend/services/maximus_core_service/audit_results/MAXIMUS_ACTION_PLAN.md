# MAXIMUS Action Plan - Risk Elimination

**Generated:** 2025-10-14
**Target:** Achieve deployment-ready state (70%+ overall coverage, 95%+ Tier 0)
**Est. Timeline:** 780-1,140 hours (4-6 months @ 1 FTE, or 1-2 months @ 3-5 FTEs)

**Current State:** 🔴 5.25% coverage - **NOT DEPLOYABLE**
**Target State:** ✅ 70%+ coverage - **PRODUCTION-READY**

---

## Phase 0: Emergency Stabilization (Week 1, 40h)

### Immediate Actions (Days 1-2)

**Priority:** Stop the bleeding, establish baseline

- [ ] **Investigate 9 test collection errors** (4h)
  - Run pytest with -vvv to identify failing imports
  - Fix broken test infrastructure
  - Document findings

- [ ] **Fix critical test infrastructure gaps** (8h)
  - Ensure all test files can be imported
  - Fix pytest configuration issues
  - Validate test discovery working

- [ ] **Establish CI/CD coverage gates** (4h)
  - Add coverage reporting to CI pipeline
  - Set minimum coverage thresholds (start at 5%, ratchet up)
  - Block PRs that decrease coverage

- [ ] **Create test templates for all tiers** (8h)
  - Tier 0 (Constitutional) template
  - Tier 1 (Consciousness) template
  - Integration test template
  - Document testing standards

- [ ] **Quick wins - Fix existing tests** (8h)
  - Review 546 existing test functions
  - Fix any failing/flaky tests
  - Ensure all pass consistently

- [ ] **Communication** (8h)
  - Present findings to stakeholders
  - Get approval for extended testing timeline
  - Assign testing responsibilities

**Week 1 Deliverables:**
- All tests passing
- CI/CD coverage tracking active
- Test templates ready
- Team aligned on plan

---

## Phase 1: Constitutional Safety (Weeks 2-5, 200h)

**Goal:** Tier 0 → 95%+ coverage (DEPLOYMENT BLOCKER)

### 1.1 Governance Engine (40h)

**Files:**
- governance/governance_engine.py (111 statements, 0% → 95%)
- governance/policy_engine.py (173 statements, 0% → 95%)
- governance/base.py (272 statements, 0% → 95%)

**Tests Needed:** ~200 tests
- [ ] Policy loading and validation (20 tests)
- [ ] Rule evaluation logic (40 tests)
- [ ] Violation detection (30 tests)
- [ ] Enforcement actions (20 tests)
- [ ] Integration with guardians (40 tests)
- [ ] Edge cases and error handling (50 tests)

**Success Criteria:**
- [ ] All policy rules fire correctly
- [ ] Violations are caught 100% of the time
- [ ] No false positives/negatives
- [ ] Performance: <50ms per evaluation

---

### 1.2 Constitutional Guardians (80h)

**Files:**
- governance/guardian/base.py (211 statements)
- governance/guardian/article_ii_guardian.py (171 statements)
- governance/guardian/article_iii_guardian.py (189 statements)
- governance/guardian/article_iv_guardian.py (196 statements)
- governance/guardian/article_v_guardian.py (208 statements)
- governance/guardian/coordinator.py (214 statements)

**Tests Needed:** ~300 tests
- [ ] Article II (Precaução) - 50 tests
  - Risk assessment logic
  - Precautionary principle enforcement
  - Risk threshold validation

- [ ] Article III (Transparência) - 50 tests
  - Transparency requirement checks
  - Audit trail validation
  - Explainability enforcement

- [ ] Article IV (Autonomia) - 50 tests
  - Autonomy boundary detection
  - Human override paths
  - Self-determination limits

- [ ] Article V (Dignidade) - 50 tests
  - Dignity preservation checks
  - Rights protection
  - Harm prevention

- [ ] Coordinator integration - 50 tests
  - Multi-article coordination
  - Conflict resolution
  - Priority handling

- [ ] Edge cases - 50 tests

**Success Criteria:**
- [ ] Each article guardian catches 100% of violations
- [ ] No constitutional bypasses possible
- [ ] All Lei Zero/I paths validated
- [ ] Guardian coordination conflict-free

---

### 1.3 Justice Module (80h)

**Files:**
- justice/constitutional_validator.py (125 statements, 0% → 95%)
- justice/cbr_engine.py (44 statements, 0% → 95%)
- justice/precedent_database.py (100 statements, 0% → 95%)
- justice/validators.py (66 statements, 0% → 95%)
- justice/emergency_circuit_breaker.py (84 statements, 0% → 95%)

**Tests Needed:** ~200 tests
- [ ] Constitutional validation logic (60 tests)
- [ ] CBR case retrieval (40 tests)
- [ ] Precedent matching (30 tests)
- [ ] Emergency circuit breaker (40 tests)
- [ ] Validator integration (30 tests)

**Success Criteria:**
- [ ] All Lei Zero violations caught
- [ ] All Lei I violations caught
- [ ] CBR retrieves correct precedents
- [ ] Emergency brake works 100% of time
- [ ] No false constitutional approvals

---

**Phase 1 Summary:**
- **Total Hours:** 200h
- **Coverage Target:** Tier 0 → 95%+
- **Tests Created:** ~700 tests
- **Critical Risk Eliminated:** Constitutional safety guaranteed

---

## Phase 2: Consciousness Core (Weeks 6-10, 300h)

**Goal:** Tier 1 → 90%+ coverage (OPERATIONAL RELIABILITY)

### 2.1 MMEI (Goal Generation) - 60h

**Files:**
- consciousness/mmei/monitor.py (303 statements, 25% → 90%)
- consciousness/mmei/goals.py (198 statements, 33% → 90%)

**Tests Needed:** ~150 tests
- [ ] Internal state monitoring (30 tests)
- [ ] Goal generation logic (40 tests)
- [ ] Goal prioritization (30 tests)
- [ ] Need detection (20 tests)
- [ ] Goal arbitration (30 tests)

**Critical Paths:**
- [ ] Lei Zero compliance check (goal alignment with values)
- [ ] Resource need detection
- [ ] Conflicting goal resolution

---

### 2.2 Prefrontal Cortex (Social Processing) - 60h

**Files:**
- consciousness/prefrontal_cortex.py (104 statements, 22% → 90%)

**Tests Needed:** ~70 tests
- [ ] Social signal processing (20 tests)
- [ ] Emotion regulation (15 tests)
- [ ] HITL escalation paths (20 tests)
- [ ] Executive function (15 tests)

**Critical Paths:**
- [ ] Lei I compliance (human escalation for critical decisions)
- [ ] Social context understanding
- [ ] Emotional state management

---

### 2.3 ESGT (Consciousness Ignition) - 80h

**Files:**
- consciousness/esgt/coordinator.py (376 statements, 21% → 90%)
- consciousness/esgt/kuramoto.py (166 statements, 24% → 90%)
- consciousness/esgt/arousal_integration.py (82 statements, 28% → 90%)
- consciousness/esgt/spm/*.py (4 files, 21-31% → 90%)

**Tests Needed:** ~200 tests
- [ ] Thread collision scenarios (40 tests)
- [ ] Frequency limiting (30 tests)
- [ ] Ignition coordination (40 tests)
- [ ] Salience detection (40 tests)
- [ ] Kuramoto synchronization (30 tests)
- [ ] Arousal integration (20 tests)

**Critical Paths:**
- [ ] Data integrity under concurrent access
- [ ] Ignition trigger accuracy
- [ ] Performance under load

---

### 2.4 TIG (Topological Fabric) - 80h

**Files:**
- consciousness/tig/fabric.py (451 statements, 19% → 90%)
- consciousness/tig/sync.py (227 statements, 18% → 90%)

**Tests Needed:** ~200 tests
- [ ] Node activation paths (50 tests)
- [ ] Edge management (40 tests)
- [ ] Synchronization (40 tests)
- [ ] Coherence calculation (30 tests)
- [ ] Performance/scalability (40 tests)

**Critical Paths:**
- [ ] Foundation stability
- [ ] Coherence accuracy
- [ ] Synchronization correctness

---

### 2.5 Safety Protocol - 120h

**Files:**
- consciousness/safety.py (785 statements, 20% → 95%)

**Tests Needed:** ~250 tests
- [ ] Threshold monitoring (50 tests)
- [ ] Anomaly detection (50 tests)
- [ ] Kill switch activation (40 tests)
- [ ] Violation logging (30 tests)
- [ ] State capture (30 tests)
- [ ] Recovery procedures (50 tests)

**Critical Paths:**
- [ ] Kill switch MUST work 100% of time
- [ ] All safety violations detected
- [ ] No false kill switch triggers
- [ ] Graceful degradation

---

**Phase 2 Summary:**
- **Total Hours:** 300h (assuming **reactive_fabric already at 100%**)
- **Coverage Target:** Tier 1 → 90%+
- **Tests Created:** ~870 tests
- **Critical Risk Reduced:** Consciousness core reliable

---

## Phase 3: Integration & HITL (Weeks 11-14, 200h)

**Goal:** Tier 2 → 85%+, E2E flows validated

### 3.1 HITL System - 80h

**Files:**
- hitl/*.py (10 files, 0% → 95%)
- ~2,000 statements

**Tests Needed:** ~300 tests
- [ ] Decision queue management (50 tests)
- [ ] Escalation triggers (50 tests)
- [ ] Operator interface (40 tests)
- [ ] Risk assessment (50 tests)
- [ ] Audit trail (40 tests)
- [ ] Decision framework (40 tests)
- [ ] Integration tests (30 tests)

**Critical Paths:**
- [ ] Lei I enforcement (human oversight for critical decisions)
- [ ] Escalation never fails
- [ ] Audit trail complete
- [ ] Performance: <100ms to queue decision

---

### 3.2 ToM & Compassion - 60h

**Files:**
- compassion/tom_engine.py (135 statements, 14% → 85%)
- compassion/social_memory.py (142 statements, 0% → 85%)
- compassion/contradiction_detector.py (53 statements, 18% → 85%)
- compassion/confidence_tracker.py (55 statements, 16% → 85%)

**Tests Needed:** ~150 tests
- [ ] Belief tracking (40 tests)
- [ ] Mental state inference (30 tests)
- [ ] Social memory CRUD (30 tests)
- [ ] Contradiction detection (25 tests)
- [ ] Confidence scoring (25 tests)

**Critical Paths:**
- [ ] ToM accuracy for social decisions
- [ ] Memory persistence
- [ ] Empathy generation

---

### 3.3 MIP (Motor Integridade Processual) - 60h

**Files:**
- motor_integridade_processual/*.py (~15 files, 0-28% → 85%)

**Tests Needed:** ~150 tests
- [ ] Arbiter decision logic (50 tests)
- [ ] Framework integration (40 tests)
- [ ] Audit trail (30 tests)
- [ ] Alternative generation (30 tests)

**Critical Paths:**
- [ ] Ethical decision consistency
- [ ] All frameworks consulted
- [ ] Audit transparency

---

### 3.4 E2E Integration Tests - CRITICAL

**New Test Files:**
- tests/integration/test_stimulus_to_action_flow.py (30 tests)
- tests/integration/test_goal_generation_flow.py (25 tests)
- tests/integration/test_social_interaction_flow.py (25 tests)
- tests/integration/test_constitutional_enforcement.py (30 tests)

**Total:** ~110 E2E tests, 80h

**Tests:**
- [ ] **Flow 1: Stimulus → Decision → Action** (30 tests)
  - Reactive Fabric → ToM → ESGT → MIP → CBR → Constitutional → Action
  - Happy path (10 tests)
  - Lei Zero violations (10 tests)
  - Lei I escalations (10 tests)

- [ ] **Flow 2: Goal Generation → Execution** (25 tests)
  - MMEI → PFC → ESGT → Execution
  - Need detection (10 tests)
  - Goal conflicts (10 tests)
  - Resource constraints (5 tests)

- [ ] **Flow 3: Social Interaction → Response** (25 tests)
  - PFC → ToM → MIP → Constitutional → Response
  - Social signal processing (10 tests)
  - Empathy generation (10 tests)
  - Response validation (5 tests)

- [ ] **Flow 4: Safety & Constitutional** (30 tests)
  - End-to-end constitutional enforcement
  - Safety protocol integration
  - HITL escalation paths
  - Emergency circuit breaker

**Success Criteria:**
- [ ] All flows complete without errors
- [ ] Lei Zero/I enforced in all paths
- [ ] HITL triggers correctly
- [ ] Performance acceptable (<500ms end-to-end for non-LLM paths)

---

**Phase 3 Summary:**
- **Total Hours:** 200h
- **Coverage Target:** Tier 2 → 85%+, E2E validated
- **Tests Created:** ~710 tests
- **Critical Risk Reduced:** Integration reliable, HITL functional

---

## Phase 4: Support & Cleanup (Weeks 15-18, 150h)

### 4.1 Tier 3 Critical Support - 80h

**Files:**
- compliance/*.py (15 files, 0% → 70%)
- fairness/*.py (12 files, 0% → 70%)
- xai/*.py (select critical files, 0% → 70%)

**Tests Needed:** ~250 tests
- [ ] Compliance monitoring (80 tests)
- [ ] Bias detection (80 tests)
- [ ] Explainability (90 tests)

---

### 4.2 Code Cleanup - 30h

- [ ] Remove dead code (*_old.py files, deprecated modules)
- [ ] Remove duplicate tests
- [ ] Clean up TODOs (resolve or document)
- [ ] Update documentation

---

### 4.3 Performance & Load Testing - 40h

- [ ] Execute performance benchmarks
- [ ] Load testing (concurrent requests, high throughput)
- [ ] Memory leak detection
- [ ] Latency profiling

---

**Phase 4 Summary:**
- **Total Hours:** 150h
- **Coverage Target:** Tier 3 → 70%+
- **Tests Created:** ~250 tests
- **System Status:** Production-ready

---

## Timeline Summary

| Phase | Duration | Deliverable | Coverage Gain | Blocker? |
|-------|----------|-------------|---------------|----------|
| 0: Emergency Stabilization | Week 1 (40h) | Test infrastructure fixed | - | YES |
| 1: Constitutional Safety | Weeks 2-5 (200h) | Tier 0 → 95%+ | +5-10% | YES |
| 2: Consciousness Core | Weeks 6-10 (300h) | Tier 1 → 90%+ | +20-30% | YES |
| 3: Integration & HITL | Weeks 11-14 (200h) | Tier 2 → 85%+, E2E done | +15-20% | YES |
| 4: Support & Cleanup | Weeks 15-18 (150h) | Tier 3 → 70%+, Polish | +10-15% | NO |

**Total Timeline:** 18 weeks (4.5 months)
**Total Hours:** 890h
**Target Coverage:** 70-75% overall (from 5.25%)

### Resource Scenarios

**Scenario 1: Single Engineer**
- **Duration:** 890h / 160h per month = 5.6 months
- **Timeline:** ~24 weeks
- **Risk:** High (long timeline, knowledge concentration)

**Scenario 2: 3 Engineers**
- **Duration:** 890h / 3 / 160h per month = 1.9 months
- **Timeline:** ~8 weeks
- **Risk:** Medium (coordination overhead, but faster)

**Scenario 3: 5 Engineers (Recommended)**
- **Duration:** 890h / 5 / 160h per month = 1.1 months
- **Timeline:** ~5-6 weeks
- **Risk:** Low (parallel work on tiers, fast completion)

---

## Success Criteria

### Must Have (Deploy Blockers)
- [ ] Tier 0 (Constitutional): 95%+ coverage
- [ ] Tier 1 (Consciousness Core): 90%+ coverage
- [ ] All E2E flows: Validated with tests
- [ ] HITL: 95%+ coverage
- [ ] Overall coverage: 70%+ minimum
- [ ] All tests passing: 100%
- [ ] No critical security vulnerabilities
- [ ] Performance benchmarks: Pass

### Should Have (Quality Gates)
- [ ] Tier 2 (Integration): 85%+ coverage
- [ ] Tier 3 (Support): 70%+ coverage
- [ ] Documentation: Complete
- [ ] Code cleanup: Done
- [ ] CI/CD: Coverage gates active
- [ ] Load testing: Pass

### Nice to Have (Excellence)
- [ ] All modules: 90%+ coverage
- [ ] Branch coverage: 85%+
- [ ] Zero flaky tests
- [ ] Performance: <100ms p95 for critical paths
- [ ] Full regression suite

---

## Risk Mitigation

### Risk 1: Timeline Slippage
**Mitigation:**
- Start with Phases 0-1 immediately (constitutional safety)
- Parallelize Phase 2 work across engineers
- Use test templates to accelerate
- Focus on critical paths first

### Risk 2: Test Quality Issues
**Mitigation:**
- Peer review all tests
- Require assertions on critical behaviors
- Use mutation testing to validate test effectiveness
- Regular test review sessions

### Risk 3: Scope Creep
**Mitigation:**
- Stick to 70% coverage target for Phase 4
- Defer Tier 4 utilities to future sprints
- Focus on deployment blockers only
- Document "nice-to-have" tests for later

### Risk 4: Integration Complexity
**Mitigation:**
- Build E2E tests incrementally
- Test component boundaries first
- Use mocks for external dependencies
- Validate with stakeholders frequently

---

## Immediate Next Steps (This Week)

1. **Today:** Present this plan to leadership, get approval
2. **Tomorrow:** Form testing task force (3-5 engineers)
3. **Day 3-5:** Complete Phase 0 (Emergency Stabilization)
4. **Week 2:** Begin Phase 1 (Constitutional Safety)

---

## Monitoring & Reporting

### Daily
- Coverage percentage (track trend)
- Tests passing vs failing
- New tests added

### Weekly
- Phase completion %
- Blockers identified
- Timeline adjustments

### Monthly
- Overall coverage milestone
- Deployment readiness assessment
- Risk review

---

## Conclusion

MAXIMUS is currently at **5.25% coverage** - a **critical risk** for production deployment. This plan provides a systematic path to **70%+ coverage** over **4-6 months** (or 5-8 weeks with adequate resourcing).

**Key Priorities:**
1. **Constitutional safety** (Tier 0) - IMMEDIATE
2. **Consciousness reliability** (Tier 1) - CRITICAL
3. **Integration validation** (E2E) - REQUIRED
4. **HITL functionality** (Lei I) - BLOCKER

**Recommendation:** Allocate 3-5 engineers full-time for 6-8 weeks to achieve deployment-ready state.

---

*Generated by MAXIMUS Full System Audit*
*Date: 2025-10-14*
*Next Review: Weekly*
