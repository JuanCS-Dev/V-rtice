# 🎨 HITL Console - Manual UI Testing Guide

## 📋 Pre-Requisites

**Before starting manual testing, ensure:**

1. ✅ Mock API is running on `:8003`
   ```bash
   # Check health
   curl http://localhost:8003/hitl/health
   # Expected: {"status":"healthy","mode":"MOCK"}
   ```

2. ✅ Frontend environment is configured
   ```bash
   cd /home/juan/vertice-dev/frontend
   cat .env | grep VITE_HITL_API_URL
   # Expected: VITE_HITL_API_URL=http://localhost:8003
   ```

3. ✅ All automated tests passed
   ```bash
   cd /home/juan/vertice-dev/backend/services/adaptive_immune_system
   ./test_frontend_integration.sh
   # Expected: 33/33 tests passed (100%)
   ```

---

## 🚀 Starting the Frontend

### Terminal 1: Mock API (already running)
```bash
cd /home/juan/vertice-dev/backend/services/adaptive_immune_system
PYTHONPATH=. python3 -m hitl.test_mock_api

# You should see:
# 🚀 Starting HITL Mock API Server...
# 📍 http://localhost:8003
# ✅ Initialized 15 mock APVs
```

### Terminal 2: Frontend Dev Server
```bash
cd /home/juan/vertice-dev/frontend
npm run dev

# You should see:
#   VITE v5.4.x ready in xxx ms
#   ➜  Local:   http://localhost:5173/
#   ➜  Network: use --host to expose
```

### Browser
1. Open: http://localhost:5173
2. Navigate to: **Admin Dashboard**
3. Click on tab: **"HITL"** (🛡️ icon)

---

## ✅ Manual Testing Checklist

### 1. Initial Load ✓

**What to check:**
- [ ] HITLConsole loads without errors
- [ ] 3-column layout appears correctly
- [ ] Header shows "HITL Console" title
- [ ] Scan line animation appears
- [ ] Quick stats show in header (pending/today counts)

**Expected behavior:**
- Page loads within 1-2 seconds
- 15 APVs appear in ReviewQueue (left column)
- "No APV selected" message in ReviewDetails (center column)
- Decision panel disabled in DecisionPanel (right column)
- Stats cards show at bottom

**Screenshot location:** `/tmp/hitl_screenshots/01_initial_load.png`

---

### 2. ReviewQueue (Left Column) ✓

#### Test 2.1: APV List Display
**What to check:**
- [ ] 15 APVs listed (or more if pagination)
- [ ] Each APV card shows:
  - APV Code (e.g., "APV-TEST-001")
  - CVE ID (e.g., "CVE-2024-12345")
  - Severity badge (🔴 Critical, 🟠 High, 🟡 Medium, 🟢 Low)
  - Package name (e.g., "requests")
  - Patch strategy (e.g., "version_bump")
  - Wargame verdict (e.g., "PATCH_EFFECTIVE")
  - Waiting time (e.g., "2.5 hours ago")

**Expected colors:**
- Critical: Red background (#dc2626)
- High: Orange background (#ea580c)
- Medium: Yellow background (#d97706)
- Low: Green background (#16a34a)

#### Test 2.2: Severity Filter
**Steps:**
1. Click severity dropdown
2. Select "Critical"
3. Verify only critical APVs shown (should be 3-5 APVs)
4. Select "All" to reset

**Expected:**
- Filter updates immediately
- APV count updates
- Correct APVs shown

#### Test 2.3: Wargame Verdict Filter
**Steps:**
1. Click wargame verdict dropdown
2. Select "PATCH_EFFECTIVE"
3. Verify only effective patches shown (should be ~5 APVs)
4. Select "All" to reset

**Expected:**
- Filter updates immediately
- Green verdict badges shown
- Correct APVs filtered

#### Test 2.4: Combined Filters
**Steps:**
1. Set severity: "Critical"
2. Set verdict: "PATCH_EFFECTIVE"
3. Verify ~1-2 APVs shown

**Expected:**
- Both filters applied
- Correct intersection of criteria

#### Test 2.5: APV Selection
**Steps:**
1. Click on first APV in list
2. Verify APV highlighted (yellow border)
3. Click on different APV
4. Verify new APV highlighted

**Expected:**
- Selected APV has yellow border (#fbbf24)
- Previous selection removed
- ReviewDetails updates (center column)

**Screenshot location:** `/tmp/hitl_screenshots/02_review_queue.png`

---

### 3. ReviewDetails (Center Column) ✓

#### Test 3.1: Tab Navigation
**Steps:**
1. Select an APV from ReviewQueue
2. Verify 4 tabs appear:
   - CVE
   - Patch
   - Wargame
   - Validation
3. Click each tab

**Expected:**
- Active tab has yellow underline (#fbbf24)
- Tab content updates smoothly
- No errors in console

#### Test 3.2: CVE Tab
**What to check:**
- [ ] CVE ID displayed (e.g., "CVE-2024-12345")
- [ ] CVSS Score (e.g., "9.8 / 10.0")
- [ ] Severity badge matches ReviewQueue
- [ ] CWE information (e.g., "CWE-502: Deserialization")
- [ ] Description paragraph (3-5 sentences)
- [ ] Published date

**Expected formatting:**
- Clean card layout
- Readable fonts
- Yellow accents (#fbbf24)

#### Test 3.3: Patch Tab
**What to check:**
- [ ] Patch strategy label (e.g., "Version Bump")
- [ ] Old version (e.g., "1.2.3")
- [ ] New version (e.g., "1.2.4")
- [ ] Diff viewer with syntax highlighting
- [ ] Lines added/removed highlighted

**Expected diff colors:**
- Added lines: Green background
- Removed lines: Red background
- Line numbers shown

**Example diff:**
```diff
- requests==1.2.3
+ requests==1.2.4
```

#### Test 3.4: Wargame Tab
**What to check:**
- [ ] Verdict badge (PATCH_EFFECTIVE/INCONCLUSIVE/PATCH_INSUFFICIENT)
- [ ] "Before Patch" section:
  - Exit code (e.g., 1 = exploit success)
  - Duration (e.g., "2.34s")
  - Status badge (red if vulnerable)
- [ ] "After Patch" section:
  - Exit code (e.g., 0 = exploit blocked)
  - Duration (e.g., "0.12s")
  - Status badge (green if protected)
- [ ] Evidence summary

**Expected:**
- Clear before/after comparison
- Visual distinction (red vs green)
- Verdict explanation

#### Test 3.5: Validation Tab
**What to check:**
- [ ] 5 validation checks:
  1. ✅ Syntax Valid
  2. ✅ Tests Pass
  3. ✅ Builds Successfully
  4. ✅ Security Scan Clean
  5. ✅ Performance Acceptable
- [ ] Each check has icon (✅ or ❌)
- [ ] Confirmation confidence score (e.g., "0.95")
- [ ] Confidence bar visualization

**Expected:**
- All checks should have green checkmarks for mock data
- Confidence bar filled proportionally
- Clean layout

**Screenshot location:** `/tmp/hitl_screenshots/03_review_details.png`

---

### 4. DecisionPanel (Right Column) ✓

#### Test 4.1: Panel Initial State
**Before selecting APV:**
- [ ] All 4 buttons disabled
- [ ] Justification textarea disabled
- [ ] Confidence slider disabled
- [ ] Message: "Select an APV to review"

**After selecting APV:**
- [ ] All controls enabled
- [ ] Form is empty/reset

#### Test 4.2: Approve Decision
**Steps:**
1. Select an APV with "PATCH_EFFECTIVE" verdict
2. Click "Approve" button (green)
3. Enter justification: "Patch is effective and wargaming confirms protection. No issues detected."
4. Set confidence: 95%
5. Click "Submit Decision"

**Expected:**
- Form validates (min 10 chars justification)
- Loading spinner appears
- Success message shown
- APV removed from pending list (in real implementation)
- Stats update (approved count +1)

**Console logs to check:**
- API POST to `/hitl/decisions`
- Response: `decision_id` returned
- No errors

#### Test 4.3: Reject Decision
**Steps:**
1. Select different APV
2. Click "Reject" button (red)
3. Enter justification: "Patch introduces breaking changes and fails integration tests."
4. Set confidence: 80%
5. Submit

**Expected:**
- Same flow as approve
- Reject count +1 in stats

#### Test 4.4: Modify Decision
**Steps:**
1. Select APV
2. Click "Modify" button (yellow)
3. Enter justification: "Patch is good but needs minor adjustments to dependency versions."
4. Enter modifications: "Change requests==1.2.4 to requests==1.2.5"
5. Set confidence: 75%
6. Submit

**Expected:**
- Modifications field appears (only for "Modify")
- Submission succeeds
- Modify count +1

#### Test 4.5: Escalate Decision
**Steps:**
1. Select APV with "INCONCLUSIVE" verdict
2. Click "Escalate" button (orange)
3. Enter justification: "Wargaming results are inconclusive. Requires senior security review."
4. Set confidence: 60%
5. Submit

**Expected:**
- Escalate count +1
- Decision recorded

#### Test 4.6: Form Validation
**Steps:**
1. Select APV
2. Click "Approve"
3. Leave justification empty
4. Try to submit

**Expected:**
- Error message: "Justification must be at least 10 characters"
- Submit button disabled or validation error shown
- No API call made

**Screenshot location:** `/tmp/hitl_screenshots/04_decision_panel.png`

---

### 5. HITLStats (Bottom Bar) ✓

#### Test 5.1: Stats Display
**What to check:**
- [ ] 6 stat cards displayed:
  1. Pending Reviews (e.g., "15")
  2. Decisions Today (e.g., "4")
  3. Approved (e.g., "1")
  4. Rejected (e.g., "1")
  5. Modified (e.g., "1")
  6. Escalated (e.g., "1")
- [ ] Each card has:
  - Icon/emoji
  - Label
  - Count number
  - Yellow accent border

#### Test 5.2: Stats Update After Decision
**Steps:**
1. Note current stats counts
2. Submit a decision (any type)
3. Wait 5 seconds (auto-refresh)
4. Verify stats updated

**Expected:**
- Pending reviews decreases by 1 (in real impl)
- Decision type count increases by 1
- Decisions today increases by 1
- Update happens automatically (React Query refetch)

**Screenshot location:** `/tmp/hitl_screenshots/05_hitl_stats.png`

---

### 6. Auto-Refresh Behavior ✓

#### Test 6.1: ReviewQueue Auto-Refresh
**Steps:**
1. Open DevTools → Network tab
2. Wait 60 seconds
3. Observe network requests

**Expected:**
- GET `/hitl/reviews` called every 60s
- No page reload
- Smooth update (no flicker)

#### Test 6.2: Stats Auto-Refresh
**Steps:**
1. Observe stats at bottom
2. Wait 60 seconds
3. Check network tab

**Expected:**
- GET `/hitl/reviews/stats` called every 60s
- Stats update automatically

---

### 7. Loading States ✓

#### Test 7.1: Initial Load
**What to check:**
- [ ] ReviewQueue shows "Loading..." or skeleton
- [ ] ReviewDetails shows placeholder
- [ ] Stats show "Loading..."

#### Test 7.2: Filter Change
**Steps:**
1. Change severity filter
2. Observe ReviewQueue

**Expected:**
- Brief loading indicator
- Smooth transition to new data

#### Test 7.3: Decision Submit
**Steps:**
1. Submit decision
2. Observe DecisionPanel

**Expected:**
- Submit button shows spinner
- Button disabled during submission
- Success message after ~500ms

---

### 8. Error Handling ✓

#### Test 8.1: Mock API Down (Simulated)
**Steps:**
1. Stop Mock API (Ctrl+C in terminal)
2. Try to load ReviewQueue
3. Try to submit decision

**Expected:**
- Error message: "Failed to load reviews"
- Retry button appears
- No crashes
- Graceful degradation

#### Test 8.2: Network Error
**Steps:**
1. Open DevTools → Network tab
2. Set throttling to "Offline"
3. Try actions

**Expected:**
- Error messages shown
- User not stuck
- Can retry

---

### 9. Responsive Design ✓

#### Test 9.1: Desktop (1920x1080)
**Expected:**
- 3-column layout
- All content visible
- No horizontal scrolling

#### Test 9.2: Laptop (1366x768)
**Expected:**
- Layout adapts
- Still usable
- May have vertical scrolling

#### Test 9.3: Tablet (768px width)
**Expected:**
- Columns stack vertically
- Touch-friendly buttons
- Readable text

---

### 10. Performance ✓

#### Test 10.1: Load Time
**Steps:**
1. Hard refresh (Ctrl+Shift+R)
2. Measure time to interactive

**Expected:**
- First paint: < 1s
- Interactive: < 2s
- No blocking resources

#### Test 10.2: Filter Performance
**Steps:**
1. Rapidly change filters 10x
2. Observe UI responsiveness

**Expected:**
- No lag
- Smooth updates
- No memory leaks

#### Test 10.3: Long Session
**Steps:**
1. Keep browser open for 30+ minutes
2. Monitor memory usage (DevTools → Performance)

**Expected:**
- Memory stable
- No leaks
- Auto-refresh continues working

---

## 📊 Test Results Template

Copy this and fill out after testing:

```markdown
## Manual UI Testing - Results

**Date:** 2025-10-13
**Tester:** [Your Name]
**Browser:** Chrome/Firefox/Safari [Version]
**Screen Resolution:** 1920x1080

### Test Categories

| Category | Tests Passed | Tests Failed | Notes |
|----------|--------------|--------------|-------|
| 1. Initial Load | _/1 | _/1 | |
| 2. ReviewQueue | _/5 | _/5 | |
| 3. ReviewDetails | _/5 | _/5 | |
| 4. DecisionPanel | _/6 | _/6 | |
| 5. HITLStats | _/2 | _/2 | |
| 6. Auto-Refresh | _/2 | _/2 | |
| 7. Loading States | _/3 | _/3 | |
| 8. Error Handling | _/2 | _/2 | |
| 9. Responsive Design | _/3 | _/3 | |
| 10. Performance | _/3 | _/3 | |

**TOTAL:** _/32 passed (_%)

### Issues Found

1. [Issue description]
   - Severity: High/Medium/Low
   - Steps to reproduce:
   - Expected vs Actual:

### Screenshots

- Initial Load: [link]
- ReviewQueue: [link]
- ReviewDetails: [link]
- DecisionPanel: [link]
- HITLStats: [link]

### Overall Assessment

- [ ] Ready for production
- [ ] Minor fixes needed
- [ ] Major issues to resolve

### Next Steps

1. [Action item]
2. [Action item]
```

---

## 🎯 Quick Test Scenario

**5-Minute Smoke Test:**

1. ✅ Open http://localhost:5173 → Admin Dashboard → HITL tab
2. ✅ Verify 15 APVs load in left column
3. ✅ Click first APV → Verify details appear in center
4. ✅ Click all 4 tabs (CVE/Patch/Wargame/Validation)
5. ✅ Click "Approve" → Enter justification → Set confidence 90% → Submit
6. ✅ Verify success message
7. ✅ Check stats updated at bottom
8. ✅ Filter by "Critical" → Verify ~3 APVs shown

**If all 8 steps pass: ✅ Basic functionality working!**

---

## 🐛 Common Issues & Solutions

### Issue: "Reviews not loading"
**Solution:**
```bash
# Check Mock API
curl http://localhost:8003/hitl/health

# Check frontend .env
cat /home/juan/vertice-dev/frontend/.env | grep VITE_HITL_API_URL
```

### Issue: "CORS error in console"
**Solution:**
- Mock API already has CORS enabled for localhost:5173
- Check API is running on port 8003
- Verify frontend is on port 5173

### Issue: "Decision submit fails"
**Solution:**
- Check justification is at least 10 characters
- Check confidence is 0-100
- Check Mock API logs for errors

---

## 📝 Notes for Developers

**CSS Modules:**
- All styles use CSS Modules (`.module.css`)
- Class names scoped automatically
- No global conflicts

**React Query:**
- Caching: 30s stale time for lists
- Auto-refetch: Every 60s
- Retry: 2 attempts on failure

**Design System:**
- Primary: #fbbf24 (yellow)
- Accent: #f59e0b (orange)
- Background: #1f2937 (dark gray)
- Text: #ffffff (white)

**Accessibility:**
- WCAG 2.1 AA compliant
- Keyboard navigation supported
- Screen reader friendly

---

**End of Manual Testing Guide**
