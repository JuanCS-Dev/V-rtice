# FASE 5: Testing with Real Projects - Test Plan

**Status**: 🔄 In Progress
**Date**: 2025-10-23
**Objective**: Validate Anthropic patterns (Planning, Self-Healing, Reflection) with real-world projects

---

## 🎯 Test Objectives

1. **Validate Planning Phase**
   - Measure plan quality scores
   - Verify complexity estimation accuracy
   - Confirm risk identification works
   - Test skip-planning fast mode

2. **Validate Self-Healing Loop**
   - Measure retry success rate (target: 83% from Meta research)
   - Test all backoff strategies (none, linear, exponential)
   - Verify reflection provides useful insights
   - Measure recovery time

3. **Validate Reflection Pattern**
   - Measure code quality score accuracy
   - Verify issue detection (error handling, TODOs, security)
   - Test compilation error analysis
   - Test test failure diagnosis

4. **Measure Performance Impact**
   - Code quality improvement (target: 25%)
   - Wasted code reduction (target: 40%)
   - Overall development speed (target: 50-70% faster)

---

## 🧪 Test Scenarios

### Scenario 1: Simple Go Function (Baseline)
**Task**: "Add a fibonacci function that calculates the nth fibonacci number"

**Target**: `internal/agents/utils/math.go` (new file)

**Expected Results**:
- Planning: Complexity 2-3/10, no risks
- Code Quality: 70-80/100 (simple function)
- Compilation: Success on first attempt
- Tests: Should suggest unit tests

**Flags**: Default (planning enabled, retry disabled)

---

### Scenario 2: Go Function with Error Handling
**Task**: "Add a file reader function that safely reads a JSON config file with error handling"

**Target**: `internal/agents/utils/config.go` (new file)

**Expected Results**:
- Planning: Complexity 4-5/10, file I/O risks identified
- Code Quality: 60-70/100 initially (may lack complete error handling)
- Reflection: Should detect if error handling incomplete
- Tests: Should recommend error case tests

**Flags**: Default

---

### Scenario 3: Intentional Compilation Error (Self-Healing Test)
**Task**: "Add a function that uses an undefined type 'CustomError' without importing it"

**Target**: `internal/agents/utils/errors.go` (new file)

**Expected Results**:
- Compilation: FAIL on attempt 1
- Self-Healing: Retry with reflection
- Reflection: "undefined_symbol" error detected
- Recovery: Depends on codegen capability (may fail all attempts)

**Flags**: `--enable-retry --max-retries 3 --enable-reflection`

**Success Metric**: Reflection provides actionable feedback

---

### Scenario 4: Complex Feature (Full Patterns)
**Task**: "Add a caching layer with Redis for agent results, including connection pooling and error handling"

**Target**: `internal/agents/cache/` (new directory)

**Expected Results**:
- Planning: Complexity 7-8/10, multiple risks (network, concurrency)
- Files: Multiple files needed (cache.go, redis.go, types.go)
- Dependencies: Should identify need for Redis client library
- Risks: Network failures, connection limits, data serialization
- Tests: Integration tests recommended

**Flags**: All features enabled

---

### Scenario 5: Python Project Test
**Task**: "Add a new FastAPI endpoint for health check with database ping"

**Target**: `backend/services/maximus_core_service/api.py` (if exists) or new service

**Expected Results**:
- Planning: Complexity 3-4/10
- Language Detection: Python (100% confidence)
- Code Quality: Check for async/await, error handling
- Tests: pytest tests recommended

**Flags**: Default

---

### Scenario 6: Fast Mode (Skip Planning)
**Task**: "Add a simple hello world endpoint"

**Target**: `cmd/hello.go` (new file)

**Expected Results**:
- Planning: SKIPPED (Step 0.5 should not run)
- Code Generation: Immediate
- Time Saved: ~2-5 seconds vs with planning

**Flags**: `--skip-planning --hitl=false`

---

## 📊 Metrics to Collect

### Planning Phase Metrics
| Metric | How to Measure | Target |
|--------|----------------|--------|
| Plan Generation Time | Log timestamps | <3 seconds |
| Complexity Accuracy | Manual review vs actual | ±1 point |
| Risk Detection Rate | Count identified vs actual | >70% |
| Plan Quality Score | Average across tests | >80/100 |

### Self-Healing Metrics
| Metric | How to Measure | Target |
|--------|----------------|--------|
| Retry Success Rate | Successful recovery / Total failures | 50-83% |
| Average Attempts | Mean attempts across tests | 1.5-2.5 |
| Backoff Effectiveness | Time to recovery | Exponential < Linear |
| Reflection Usefulness | Qualitative assessment | Actionable insights |

### Reflection Metrics
| Metric | How to Measure | Target |
|--------|----------------|--------|
| Code Quality Score Accuracy | Compare to manual review | ±10 points |
| Issue Detection Rate | True positives / Total issues | >80% |
| False Positive Rate | False alarms / Total flags | <20% |
| Suggestion Quality | Qualitative assessment | Helpful |

### Overall Performance
| Metric | How to Measure | Target |
|--------|----------------|--------|
| Time to Working Code | End-to-end duration | Baseline for comparison |
| Iterations Required | Attempts until passing | <3 with retry, 1 ideal |
| Code Quality Improvement | With reflection vs without | +25% |
| Developer Productivity | Qualitative assessment | 50-70% faster |

---

## 🔧 Test Execution Plan

### Phase 1: Baseline Tests (No Advanced Features)
1. ✅ Test Scenario 1 (Simple Function) - Flags: default, no retry
2. Test Scenario 2 (Error Handling) - Flags: default, no retry

**Goal**: Establish baseline performance without self-healing

### Phase 2: Planning Phase Tests
3. Re-run Scenario 2 with planning enabled
4. Test Scenario 4 (Complex Feature) - Observe plan quality
5. Test Scenario 6 (Fast Mode) - Compare time with/without planning

**Goal**: Validate planning reduces complexity and identifies risks

### Phase 3: Self-Healing Tests
6. Test Scenario 3 (Intentional Error) - Enable retry
7. Re-run failed tests from Phase 1 with retry enabled

**Goal**: Measure retry success rate and reflection quality

### Phase 4: Full Integration Tests
8. Test Scenario 4 (Complex Feature) - All features enabled
9. Test Scenario 5 (Python Project) - All features enabled

**Goal**: Validate all patterns work together

### Phase 5: Performance Analysis
10. Compare metrics across all scenarios
11. Calculate improvement percentages
12. Document findings

---

## ✅ Success Criteria

**Minimum Acceptable**:
- Planning generates valid plans with >60/100 quality score
- Self-healing recovers from >30% of failures
- Reflection provides actionable feedback in >70% of cases
- No regressions in base functionality

**Target Performance**:
- Planning quality score >80/100
- Self-healing success rate >50%
- Code quality improvement +15-25%
- Overall development speed +30-50%

**Stretch Goals** (Research Targets):
- Self-healing success rate >83% (Meta research)
- Wasted code reduction >40%
- Code quality improvement +25%
- Development speed +50-70%

---

## 📝 Test Log Template

For each scenario, document:

```markdown
### Test: [Scenario Name]
**Date**: [timestamp]
**Command**: [exact CLI command]
**Flags**: [flags used]

**Planning Phase**:
- Plan ID: [id]
- Complexity: [score/10]
- Risks Identified: [count] - [list]
- Quality Score: [score/100]
- Time: [seconds]

**Code Generation**:
- Files Created: [count] - [list]
- Files Modified: [count] - [list]
- Generation Time: [seconds]

**Code Quality Reflection**:
- Quality Score: [score/100]
- Issues Found: [count] - [list]
- Suggestions: [list]

**Compilation**:
- Result: [SUCCESS/FAIL]
- Attempts: [number]
- Errors: [list if failed]

**Self-Healing** (if enabled):
- Total Attempts: [number]
- Success: [yes/no]
- Recovery Time: [seconds]
- Reflection Insights: [summary]

**Tests**:
- Executed: [count]
- Passed: [count]
- Failed: [count]

**Overall**:
- Status: [SUCCESS/PARTIAL/FAIL]
- Duration: [total seconds]
- Notes: [observations]
```

---

## 🚀 Next Actions

1. Execute Phase 1 tests (Baseline)
2. Collect metrics
3. Execute Phase 2-4 tests
4. Analyze results
5. Document findings in FASE-5-RESULTS.md

---

**Última atualização**: 2025-10-23 10:45 UTC
**Responsável**: Claude Code (Sonnet 4.5) + Juan Carlos
**Status**: Test Plan Ready - Starting Execution 🚀
