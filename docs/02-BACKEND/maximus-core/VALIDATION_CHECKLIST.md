# 🏛️ Governance Workspace - Manual Validation Checklist

**Version:** 1.0
**Date:** 2025-10-06
**Validator:** _________________
**Environment:** Production Server (port 8002)

---

## Pre-requisites

**Before starting, ensure:**

- [ ] Servidor rodando em porta 8002
```bash
# Verify server is running
curl -s http://localhost:8002/health | python -m json.tool
```

- [ ] Terminal supports colors and Unicode
- [ ] Python 3.11+ installed
- [ ] `httpx` and `textual` packages available

---

## Section 1: Startup Validation (5 minutes)

### 1.1 Server Health Check

**Objective:** Verify backend server is operational

- [ ] Check root health endpoint
```bash
curl -s http://localhost:8002/health | python -m json.tool
# Expected: status="healthy", all components=true
```

- [ ] Check Governance API health
```bash
curl -s http://localhost:8002/api/v1/governance/health | python -m json.tool
# Expected: status="healthy", queue_size visible
```

- [ ] Check API documentation
```bash
# Open in browser
open http://localhost:8002/docs
# Or: curl http://localhost:8002/docs
```

**✅ Pass Criteria:** All endpoints return 200 OK, status="healthy"

---

### 1.2 TUI Launch

**Objective:** Verify TUI starts without errors

- [ ] Launch TUI from vertice-terminal directory
```bash
cd /home/juan/vertice-dev/vertice-terminal
python -m vertice.cli governance start --backend-url http://localhost:8002
```

- [ ] Verify TUI displays without crashes
- [ ] Look for error messages in terminal output
- [ ] Confirm SSE connection message appears

**Expected Output:**
```
🚀 Governance Workspace
Connecting to: http://localhost:8002
✅ SSE connection established
```

**✅ Pass Criteria:** TUI opens, no Python exceptions, SSE connected

---

## Section 2: UI/UX Validation (10 minutes)

### 2.1 Layout Verification

**Objective:** Verify visual layout renders correctly

Visual Checklist:

- [ ] **Header** displays "Governance Workspace" title
- [ ] **Three panels** visible:
  - Left: Pending Decisions
  - Center: Active Decision
  - Right: History/Stats
- [ ] **Footer** shows keybindings (q, r, c, etc.)
- [ ] **Colors** render correctly (no escape codes visible)
- [ ] **Borders** are clean (no broken lines)

**Expected Layout:**
```
┌─ Governance Workspace ───────────────────────────────────────┐
│                                                               │
│ ┌─ Pending ──┐ ┌─ Active ────┐ ┌─ History ──┐               │
│ │            │ │              │ │            │               │
│ │            │ │              │ │            │               │
│ │            │ │              │ │            │               │
│ └────────────┘ └──────────────┘ └────────────┘               │
│                                                               │
│ q: Quit  r: Refresh  c: Clear  ?: Help                       │
└───────────────────────────────────────────────────────────────┘
```

**✅ Pass Criteria:** Layout matches expected design, all text readable

---

### 2.2 Keyboard Navigation

**Objective:** Verify keyboard controls work

Test each key:

- [ ] Press `Tab` → Focus moves between panels
- [ ] Press `Shift+Tab` → Focus moves backwards
- [ ] Press `r` → Stats refresh
- [ ] Press `c` → History clears (if applicable)
- [ ] Press `?` → Help screen appears
- [ ] Press `Escape` → Returns from help
- [ ] Press `q` → Confirm prompt appears

**✅ Pass Criteria:** All keys respond correctly, no lag

---

## Section 3: Functional Validation (15 minutes)

### 3.1 Decision Processing Flow

**Objective:** Test complete decision approval workflow

**Step 1: Enqueue Test Decision**

In separate terminal:

```bash
curl -X POST http://localhost:8002/api/v1/governance/test/enqueue \
  -H "Content-Type: application/json" \
  -d '{
    "decision_id": "manual_test_001",
    "risk_level": "high",
    "action_type": "block_ip",
    "target": "192.168.1.100",
    "confidence": 0.95,
    "ai_reasoning": "Manual validation test - suspicious C2 communication",
    "threat_score": 9.5,
    "threat_type": "command_and_control",
    "metadata": {
      "source": "manual_validation",
      "timestamp": "2025-10-06T21:00:00Z"
    }
  }'
```

- [ ] Decision appears in TUI within 2 seconds
- [ ] Decision shows correct risk level (HIGH)
- [ ] Target IP displayed correctly (192.168.1.100)
- [ ] Confidence shown (95%)

**Step 2: Review Decision Details**

- [ ] Select decision in Pending panel
- [ ] Decision details appear in Active panel
- [ ] AI reasoning text visible
- [ ] Threat score displayed (9.5)

**Step 3: Approve Decision**

- [ ] Press `a` key (or designated approve key)
- [ ] Confirmation prompt appears
- [ ] Confirm approval
- [ ] Decision moves to History panel
- [ ] Stats increment (+1 reviewed, +1 approved)

**✅ Pass Criteria:** Complete flow works, stats update correctly

---

### 3.2 Multiple Decisions Processing

**Objective:** Test handling multiple decisions

**Enqueue 5 decisions:**

```bash
for i in {1..5}; do
  curl -X POST http://localhost:8002/api/v1/governance/test/enqueue \
    -H "Content-Type: application/json" \
    -d "{
      \"decision_id\": \"multi_test_$i\",
      \"risk_level\": \"medium\",
      \"action_type\": \"block_ip\",
      \"target\": \"10.0.0.$i\",
      \"confidence\": 0.85,
      \"ai_reasoning\": \"Multiple decision test #$i\",
      \"threat_score\": 7.0,
      \"threat_type\": \"test\",
      \"metadata\": {}
    }" &
done
wait
echo "✅ 5 decisions enqueued"
```

- [ ] All 5 decisions appear in Pending panel
- [ ] Decisions sorted by risk/SLA (verify order)
- [ ] Can scroll through list (if needed)

**Process decisions:**

- [ ] Approve 2 decisions (press `a` twice)
- [ ] Reject 2 decisions (press `r` twice)
- [ ] Escalate 1 decision (press `e` once)

**Verify stats:**

- [ ] Total reviewed: 5
- [ ] Approved: 2
- [ ] Rejected: 2
- [ ] Escalated: 1
- [ ] Approval rate: 40%
- [ ] Rejection rate: 40%
- [ ] Escalation rate: 20%

**✅ Pass Criteria:** All actions work, stats accurate

---

## Section 4: Real-time Updates (5 minutes)

### 4.1 SSE Streaming

**Objective:** Verify real-time updates via SSE

With TUI open:

```bash
# In another terminal, enqueue decision
curl -X POST http://localhost:8002/api/v1/governance/test/enqueue \
  -H "Content-Type: application/json" \
  -d '{
    "decision_id": "sse_test_realtime",
    "risk_level": "critical",
    "action_type": "isolate_host",
    "target": "server-prod-db-01",
    "confidence": 0.99,
    "ai_reasoning": "Critical threat detected - immediate action required",
    "threat_score": 9.9,
    "threat_type": "ransomware",
    "metadata": {"urgency": "immediate"}
  }'
```

- [ ] Decision appears in TUI **within 2 seconds**
- [ ] No manual refresh needed (automatic via SSE)
- [ ] CRITICAL risk level highlighted (red/urgent color)
- [ ] High threat score visible

**✅ Pass Criteria:** Real-time update < 2s, no manual refresh

---

### 4.2 Heartbeat Monitoring

**Objective:** Verify SSE connection stays alive

- [ ] Keep TUI open for 60 seconds without interaction
- [ ] Observe console/logs for heartbeat messages
- [ ] TUI remains responsive (not frozen)
- [ ] No disconnection warnings

**Expected:** Heartbeat every ~30 seconds

**✅ Pass Criteria:** Connection stable, no disconnects

---

## Section 5: Performance Validation (5 minutes)

### 5.1 Load Testing

**Objective:** Verify TUI handles moderate load

**Enqueue 20 decisions rapidly:**

```bash
for i in {1..20}; do
  curl -s -X POST http://localhost:8002/api/v1/governance/test/enqueue \
    -H "Content-Type: application/json" \
    -d "{
      \"decision_id\": \"perf_test_$i\",
      \"risk_level\": \"low\",
      \"action_type\": \"block_ip\",
      \"target\": \"192.168.100.$i\",
      \"confidence\": 0.75,
      \"ai_reasoning\": \"Performance test decision #$i\",
      \"threat_score\": 5.0,
      \"threat_type\": \"test\",
      \"metadata\": {}
    }" > /dev/null &
done
wait
echo "✅ 20 decisions enqueued"
```

- [ ] All 20 decisions load in TUI
- [ ] Load time < 5 seconds
- [ ] TUI remains responsive (can scroll, select)
- [ ] No lag or freezing
- [ ] CPU usage reasonable (< 50%)

**Process all decisions:**

- [ ] Bulk approve/reject works smoothly
- [ ] No crashes or hangs
- [ ] Stats update correctly

**✅ Pass Criteria:** No lag, all decisions processed successfully

---

## Section 6: Error Handling (5 minutes)

### 6.1 Network Interruption

**Objective:** Test recovery from connection loss

**Simulate server failure:**

```bash
# In server terminal, stop server (Ctrl+C)
# Or kill server process:
pkill -f "governance_production_server"
```

- [ ] TUI shows connection error/warning
- [ ] Error message clear and actionable
- [ ] TUI doesn't crash (remains open)

**Restart server:**

```bash
cd /home/juan/vertice-dev/backend/services/maximus_core_service
uvicorn governance_production_server:app --host 0.0.0.0 --port 8002 &
sleep 3
```

- [ ] TUI reconnects automatically OR shows reconnect option
- [ ] SSE stream re-establishes
- [ ] Can continue working normally

**✅ Pass Criteria:** Graceful error handling, successful reconnection

---

### 6.2 Invalid Input Handling

**Objective:** Verify error validation

- [ ] Try to approve already-approved decision
  - Expected: Error message or prevention

- [ ] Try to access decision that doesn't exist
  - Expected: Graceful error, no crash

**✅ Pass Criteria:** All errors handled gracefully, no crashes

---

## Section 7: Final Validation (2 minutes)

### 7.1 Session Stats Accuracy

**Verify stats via API match TUI display:**

```bash
# Replace with your operator ID from TUI
OPERATOR_ID="your_operator@test"

curl -s http://localhost:8002/api/v1/governance/session/$OPERATOR_ID/stats | python -m json.tool
```

- [ ] Total reviewed matches TUI
- [ ] Approved count matches
- [ ] Rejected count matches
- [ ] Escalated count matches
- [ ] Rates calculated correctly

**✅ Pass Criteria:** API stats == TUI stats (100% accuracy)

---

### 7.2 Clean Exit

- [ ] Press `q` to quit
- [ ] Confirmation prompt appears
- [ ] Confirm exit
- [ ] TUI closes cleanly (no errors)
- [ ] Terminal restored to normal state

**✅ Pass Criteria:** Clean exit, no lingering processes

---

## Final Sign-Off

### Summary

| Category | Status | Notes |
|----------|--------|-------|
| 1. Startup | ☐ Pass ☐ Fail | |
| 2. UI/UX | ☐ Pass ☐ Fail | |
| 3. Functional | ☐ Pass ☐ Fail | |
| 4. Real-time | ☐ Pass ☐ Fail | |
| 5. Performance | ☐ Pass ☐ Fail | |
| 6. Error Handling | ☐ Pass ☐ Fail | |
| 7. Final Validation | ☐ Pass ☐ Fail | |

### Overall Assessment

- [ ] **ALL SECTIONS PASSED** → ✅ **APPROVED FOR PRODUCTION**
- [ ] **MINOR ISSUES** → ⚠️ **NEEDS REVIEW** (document issues below)
- [ ] **CRITICAL FAILURES** → ❌ **REJECTED** (must fix before deploy)

### Issues Found

```
[Document any issues, bugs, or unexpected behavior here]




```

### Recommendations

```
[Optional improvements or suggestions]




```

---

**Validator Name:** _______________________

**Date:** _______________________

**Time Spent:** _______ minutes

**Final Decision:** ☐ APPROVED  ☐ NEEDS REVIEW  ☐ REJECTED

**Signature:** _______________________

---

## Quick Reference Commands

### Start TUI
```bash
cd /home/juan/vertice-dev/vertice-terminal
python -m vertice.cli governance start --backend-url http://localhost:8002
```

### Enqueue Single Decision
```bash
curl -X POST http://localhost:8002/api/v1/governance/test/enqueue \
  -H "Content-Type: application/json" \
  -d '{
    "decision_id": "test_001",
    "risk_level": "high",
    "action_type": "block_ip",
    "target": "192.168.1.1",
    "confidence": 0.95,
    "ai_reasoning": "Test decision",
    "threat_score": 9.0,
    "threat_type": "test",
    "metadata": {}
  }'
```

### Check Health
```bash
curl http://localhost:8002/api/v1/governance/health | python -m json.tool
```

### View Operator Stats
```bash
curl http://localhost:8002/api/v1/governance/session/<operator_id>/stats | python -m json.tool
```

---

**End of Checklist**
