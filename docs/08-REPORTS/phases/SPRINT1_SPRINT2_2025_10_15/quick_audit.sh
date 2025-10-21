#!/bin/bash
# Quick audit of TODOs and mocks using grep

cd /home/juan/vertice-dev/backend/services

echo "🔍 SPRINT 2 FASE 2.1: QUICK TODO/MOCK AUDIT"
echo "=========================================="
echo ""

echo "📊 Counting TODOs/FIXMEs/HACKs by service:"
echo ""

for dir in */; do
    service="${dir%/}"

    # Skip if no Python files
    if [ ! -f "$service"/*.py ] && [ ! -d "$service" ]; then
        continue
    fi

    # Count TODOs (case insensitive, skip test files for mocks)
    todo_count=$(find "$service" -name "*.py" -type f \
        ! -path "*/.venv/*" ! -path "*/__pycache__/*" \
        -exec grep -i -E "TODO|FIXME|HACK|XXX" {} \; 2>/dev/null | wc -l)

    # Count potential mocks in production code (not test files)
    mock_count=$(find "$service" -name "*.py" -type f \
        ! -name "*test*.py" ! -path "*/test*" \
        ! -path "*/.venv/*" ! -path "*/__pycache__/*" \
        -exec grep -E "mock_|Mock[A-Z]|NotImplementedError|pass.*#.*TODO" {} \; 2>/dev/null | wc -l)

    if [ "$todo_count" -gt 0 ] || [ "$mock_count" -gt 0 ]; then
        printf "%-40s TODOs: %5d  Mocks: %5d\n" "$service" "$todo_count" "$mock_count"
    fi
done

echo ""
echo "=========================================="
echo "📈 TOTALS"
echo "=========================================="

total_todos=$(find . -name "*.py" -type f \
    ! -path "*/.venv/*" ! -path "*/__pycache__/*" \
    -exec grep -i -E "TODO|FIXME|HACK|XXX" {} \; 2>/dev/null | wc -l)

total_mocks=$(find . -name "*.py" -type f \
    ! -name "*test*.py" ! -path "*/test*" \
    ! -path "*/.venv/*" ! -path "*/__pycache__/*" \
    -exec grep -E "mock_|Mock[A-Z]|NotImplementedError" {} \; 2>/dev/null | wc -l)

echo "Total TODOs: $total_todos"
echo "Total Mocks: $total_mocks"
