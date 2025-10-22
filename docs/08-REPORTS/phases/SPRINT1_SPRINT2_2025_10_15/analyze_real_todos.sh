#!/bin/bash
# Analyze REAL TODOs (excluding test files and documentation)

cd /home/juan/vertice-dev/backend/services

echo "🔍 SPRINT 2 FASE 2.1: REAL TODO ANALYSIS"
echo "========================================"
echo ""

echo "Finding TODOs in production code (excluding tests and docs):"
echo ""

for dir in */; do
    service="${dir%/}"

    # Count TODOs in non-test Python files
    todo_count=$(find "$service" -name "*.py" -type f \
        ! -name "*test*.py" ! -path "*/tests/*" ! -path "*/.venv/*" \
        -exec grep -l "TODO\|FIXME\|HACK" {} \; 2>/dev/null | wc -l)

    if [ "$todo_count" -gt 0 ]; then
        # Get actual TODO lines
        actual_todos=$(find "$service" -name "*.py" -type f \
            ! -name "*test*.py" ! -path "*/tests/*" ! -path "*/.venv/*" \
            -exec grep -n "TODO\|FIXME\|HACK" {} + 2>/dev/null | wc -l)

        if [ "$actual_todos" -gt 0 ]; then
            printf "%-40s %3d files, %4d TODOs\n" "$service" "$todo_count" "$actual_todos"
        fi
    fi
done

echo ""
echo "========================================"
echo "🎯 ACTION PLAN"
echo "========================================"
echo ""
echo "Top priority services to clean:"
echo ""

find . -name "*.py" -type f \
    ! -name "*test*.py" ! -path "*/tests/*" ! -path "*/.venv/*" \
    -exec grep -l "TODO.*Implement\|TODO.*real\|FIXME" {} \; 2>/dev/null | \
    cut -d/ -f2 | sort | uniq -c | sort -rn | head -10
