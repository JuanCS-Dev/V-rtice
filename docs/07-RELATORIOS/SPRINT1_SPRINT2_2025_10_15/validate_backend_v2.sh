#!/bin/bash

LOG_FILE="/tmp/maximus_validation/validation_v2_$(date +%Y%m%d_%H%M%S).log"
RESULTS_FILE="/tmp/maximus_validation/results_v2.txt"
CERTIFIED=0
FAILED=0
SKIPPED=0

> $RESULTS_FILE
> $LOG_FILE

echo "=== MAXIMUS BACKEND VALIDATION V2 ===" | tee -a $LOG_FILE
echo "Started: $(date)" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

while IFS= read -r SERVICE; do
    echo "──────────────────────────────────────" | tee -a $LOG_FILE
    echo "[$((CERTIFIED+FAILED+SKIPPED+1))/83] $SERVICE" | tee -a $LOG_FILE
    
    cd "/home/juan/vertice-dev/backend/services/$SERVICE"
    
    # Quick check - count Python files
    PY_FILES=$(find . -maxdepth 3 -name "*.py" -type f ! -path "./venv/*" ! -path "./__pycache__/*" ! -path "./tests/*" 2>/dev/null | wc -l)
    
    if [ "$PY_FILES" -eq 0 ]; then
        echo "⚠️  SKIPPED (no Python files)" | tee -a $LOG_FILE
        echo "$SERVICE|SKIPPED|No Python files" >> $RESULTS_FILE
        ((SKIPPED++))
        continue
    fi
    
    # Check for tests directory
    if [ ! -d "tests" ]; then
        echo "❌ FAILED (no tests)" | tee -a $LOG_FILE
        echo "$SERVICE|FAILED|0%|No tests directory" >> $RESULTS_FILE
        ((FAILED++))
        continue
    fi
    
    TEST_FILES=$(find tests -name "test_*.py" 2>/dev/null | wc -l)
    if [ "$TEST_FILES" -eq 0 ]; then
        echo "❌ FAILED (no test files)" | tee -a $LOG_FILE
        echo "$SERVICE|FAILED|0%|No test files in tests/" >> $RESULTS_FILE
        ((FAILED++))
        continue
    fi
    
    # Check for TODOs/FIXMEs in main code (not tests)
    TODO_COUNT=$(grep -r "TODO\|FIXME\|XXX\|HACK" --include="*.py" . 2>/dev/null | grep -v "/tests/" | grep -v "/venv/" | grep -v "__pycache__" | wc -l)
    
    if [ "$TODO_COUNT" -gt 0 ]; then
        echo "❌ FAILED ($TODO_COUNT TODOs)" | tee -a $LOG_FILE
        echo "$SERVICE|FAILED|?%|TODOs:$TODO_COUNT" >> $RESULTS_FILE
        ((FAILED++))
        continue
    fi
    
    # Quick static checks without full test run
    # Check for obvious mocks/stubs in main code
    MOCK_COUNT=$(grep -r "pass  # TODO\|raise NotImplementedError\|# STUB\|# PLACEHOLDER" --include="*.py" . 2>/dev/null | grep -v "/tests/" | grep -v "/venv/" | wc -l)
    
    if [ "$MOCK_COUNT" -gt 0 ]; then
        echo "❌ FAILED ($MOCK_COUNT mocks/stubs)" | tee -a $LOG_FILE
        echo "$SERVICE|FAILED|?%|Mocks:$MOCK_COUNT" >> $RESULTS_FILE
        ((FAILED++))
        continue
    fi
    
    # For now, mark as NEEDS_VALIDATION if it passes basic checks
    echo "⚙️  NEEDS_VALIDATION ($PY_FILES files, $TEST_FILES tests)" | tee -a $LOG_FILE
    echo "$SERVICE|NEEDS_VALIDATION|?%|Files:$PY_FILES|Tests:$TEST_FILES|TODOs:0" >> $RESULTS_FILE
    ((FAILED++))
    
done < /tmp/maximus_validation/services_list.txt

# Summary
TOTAL_SERVICES=$(wc -l < /tmp/maximus_validation/services_list.txt)

echo "" | tee -a $LOG_FILE
echo "═══════════════════════════════════════════════" | tee -a $LOG_FILE
echo "QUICK VALIDATION SUMMARY" | tee -a $LOG_FILE
echo "═══════════════════════════════════════════════" | tee -a $LOG_FILE
echo "Total services: $TOTAL_SERVICES" | tee -a $LOG_FILE
echo "Certified (100%): $CERTIFIED" | tee -a $LOG_FILE
echo "Needs validation: $(grep -c "NEEDS_VALIDATION" $RESULTS_FILE || echo 0)" | tee -a $LOG_FILE
echo "Failed basic checks: $(grep -c "^.*|FAILED|" $RESULTS_FILE || echo 0)" | tee -a $LOG_FILE
echo "Skipped: $SKIPPED" | tee -a $LOG_FILE

echo "" | tee -a $LOG_FILE
echo "Export counters..." | tee -a $LOG_FILE
echo "CERTIFIED=$CERTIFIED" > /tmp/maximus_validation/counters.env
echo "FAILED=$FAILED" >> /tmp/maximus_validation/counters.env
echo "SKIPPED=$SKIPPED" >> /tmp/maximus_validation/counters.env
echo "TOTAL_SERVICES=$TOTAL_SERVICES" >> /tmp/maximus_validation/counters.env

echo "" | tee -a $LOG_FILE
echo "Completed: $(date)" | tee -a $LOG_FILE
