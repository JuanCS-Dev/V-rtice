#!/bin/bash
set -e

echo "🔍 TASK-001: Validating Structure and Scaffolding..."
echo ""

BASE_DIR="/home/juan/vertice-dev/backend/services/maximus_core_service/motor_integridade_processual"
ROOT_DIR="/home/juan/vertice-dev"

# Counter for checks
CHECKS_PASSED=0
TOTAL_CHECKS=0

check() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if eval "$1"; then
        echo "  ✅ $2"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
        return 0
    else
        echo "  ❌ $2"
        return 1
    fi
}

echo "📁 Checking Directory Structure..."
DIRS=(
    "$BASE_DIR/frameworks"
    "$BASE_DIR/models"
    "$BASE_DIR/resolution"
    "$BASE_DIR/arbiter"
    "$BASE_DIR/infrastructure"
    "$BASE_DIR/tests/unit"
    "$BASE_DIR/tests/integration"
    "$BASE_DIR/tests/e2e"
    "$BASE_DIR/tests/property"
    "$BASE_DIR/tests/wargaming"
)

for dir in "${DIRS[@]}"; do
    check "[ -d \"$dir\" ]" "Directory exists: $(basename $dir)"
done

echo ""
echo "📄 Checking Core Files..."
FILES=(
    "$BASE_DIR/__init__.py"
    "$BASE_DIR/api.py"
    "$BASE_DIR/config.py"
    "$BASE_DIR/pyproject.toml"
    "$ROOT_DIR/docker-compose.mip.yml"
)

for file in "${FILES[@]}"; do
    check "[ -f \"$file\" ]" "File exists: $(basename $file)"
done

echo ""
echo "📝 Checking Module Files..."
MODULE_FILES=(
    "$BASE_DIR/frameworks/__init__.py"
    "$BASE_DIR/frameworks/base.py"
    "$BASE_DIR/frameworks/kantian.py"
    "$BASE_DIR/frameworks/utilitarian.py"
    "$BASE_DIR/frameworks/virtue.py"
    "$BASE_DIR/frameworks/principialism.py"
    "$BASE_DIR/models/__init__.py"
    "$BASE_DIR/models/action_plan.py"
    "$BASE_DIR/models/verdict.py"
    "$BASE_DIR/models/audit.py"
    "$BASE_DIR/models/hitl.py"
    "$BASE_DIR/models/knowledge.py"
)

for file in "${MODULE_FILES[@]}"; do
    check "[ -f \"$file\" ]" "Module file exists: ${file#$BASE_DIR/}"
done

echo ""
echo "📖 Checking Docstrings..."
INIT_FILES=$(find "$BASE_DIR" -name "__init__.py" -type f)
for init_file in $INIT_FILES; do
    lines=$(grep -c '"""' "$init_file" 2>/dev/null || echo "0")
    relative_path="${init_file#$BASE_DIR/}"
    check "[ $lines -ge 2 ]" "Docstring in: $relative_path"
done

echo ""
echo "🔧 Validating pyproject.toml..."
cd "$BASE_DIR"
if command -v poetry &> /dev/null; then
    check "poetry check &> /dev/null" "Poetry configuration valid"
else
    echo "  ⚠️  Poetry not installed, skipping poetry check"
    echo "  ℹ️  Install with: curl -sSL https://install.python-poetry.org | python3 -"
fi

echo ""
echo "🐳 Validating docker-compose.mip.yml..."
cd "$ROOT_DIR"
check "docker compose -f docker-compose.mip.yml config > /dev/null 2>&1" "Docker-compose configuration valid"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "📊 TASK-001 Validation Results:"
echo "═══════════════════════════════════════════════════════════"
echo "  Checks Passed: $CHECKS_PASSED / $TOTAL_CHECKS"

if [ $CHECKS_PASSED -eq $TOTAL_CHECKS ]; then
    echo ""
    echo "✅ All checks passed"
    echo "✅ Structure: Complete"
    echo "✅ Files: All present"
    echo "✅ Docstrings: Complete"
    echo "✅ Configuration: Valid"
    echo ""
    echo "🎉 TASK-001: 100% COMPLETE"
    echo ""
    exit 0
else
    echo ""
    echo "❌ Some checks failed ($((TOTAL_CHECKS - CHECKS_PASSED)) failures)"
    echo "❌ TASK-001: INCOMPLETE"
    echo ""
    exit 1
fi
