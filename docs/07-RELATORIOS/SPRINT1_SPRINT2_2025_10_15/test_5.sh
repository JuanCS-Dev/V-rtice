#!/bin/bash
LOG_FILE="/tmp/maximus_validation/test_5_$(date +%Y%m%d_%H%M%S).log"
RESULTS_FILE="/tmp/maximus_validation/test_5_results.txt"
> $RESULTS_FILE
> $LOG_FILE

while IFS= read -r SERVICE; do
    echo "──────────────────────────────────────"
    echo "Testing: $SERVICE"
    
    cd "/home/juan/vertice-dev/backend/services/$SERVICE"
    
    PY_FILES=$(find . -maxdepth 3 -name "*.py" -type f ! -path "./__pycache__/*" ! -path "./tests/*" 2>/dev/null | wc -l)
    
    if [ "$PY_FILES" -eq 0 ]; then
        echo "SKIP: No Python files"
        continue
    fi
    
    if [ ! -d "tests" ]; then
        echo "FAIL: No tests"
        continue
    fi
    
    TEST_FILES=$(find tests -name "test_*.py" 2>/dev/null | wc -l)
    if [ "$TEST_FILES" -eq 0 ]; then
        echo "FAIL: No test files"
        continue
    fi
    
    TODO_COUNT=$(grep -r "TODO\|FIXME\|XXX\|HACK" --include="*.py" . 2>/dev/null | grep -v "/tests/" | grep -v "__pycache__" | wc -l)
    
    if [ "$TODO_COUNT" -gt 0 ]; then
        echo "FAIL: $TODO_COUNT TODOs"
        continue
    fi
    
    echo "Running pytest..."
    cd /home/juan/vertice-dev
    
    PYTHONPATH="/home/juan/vertice-dev/backend/services/$SERVICE:/home/juan/vertice-dev:$PYTHONPATH" \
    pytest "backend/services/$SERVICE/tests/" \
        --cov="backend/services/$SERVICE" \
        --cov-report=json:/tmp/cov_${SERVICE}.json \
        --cov-report=term \
        -v --tb=short 2>&1 | tee -a $LOG_FILE | tail -20
    
    if [ -f "/tmp/cov_${SERVICE}.json" ]; then
        COVERAGE=$(python3 -c "import json; print('{:.2f}'.format(json.load(open('/tmp/cov_${SERVICE}.json'))['totals']['percent_covered']))" 2>/dev/null || echo "0.00")
        echo "Coverage: ${COVERAGE}%"
        echo "$SERVICE|${COVERAGE}%" >> $RESULTS_FILE
    fi
    
done < /tmp/maximus_validation/test_5_services.txt
