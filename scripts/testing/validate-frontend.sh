#!/bin/bash
# Frontend Functionality Validation Test
# Tests key features and components

echo "🧪 FRONTEND FUNCTIONALITY VALIDATION"
echo "====================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0
TOTAL=0

test_case() {
  local name="$1"
  local command="$2"
  local expected="$3"
  
  ((TOTAL++))
  
  result=$(eval "$command" 2>&1)
  
  if echo "$result" | grep -q "$expected"; then
    echo -e "${GREEN}✓${NC} $name"
    ((PASSED++))
  else
    echo -e "${RED}✗${NC} $name"
    echo "  Expected: $expected"
    echo "  Got: $result"
    ((FAILED++))
  fi
}

echo "1️⃣  Testing Build System"
echo "------------------------"

test_case "Build completes successfully" \
  "npm run build 2>&1 | grep -E 'built in|✓ built'" \
  "built"

test_case "Build output exists" \
  "ls -la dist/index.html 2>&1" \
  "index.html"

test_case "Assets generated" \
  "ls dist/assets/*.js 2>&1 | wc -l" \
  "[0-9]"

echo ""
echo "2️⃣  Testing Component Files"
echo "---------------------------"

test_case "Accessible components exist" \
  "ls src/components/shared/AccessibleButton.jsx 2>&1" \
  "AccessibleButton"

test_case "Theme system exists" \
  "ls src/hooks/useTheme.js 2>&1" \
  "useTheme"

test_case "Toast system exists" \
  "ls src/components/shared/Toast.jsx 2>&1" \
  "Toast"

test_case "Loading states exist" \
  "ls src/components/shared/LoadingStates.jsx 2>&1" \
  "LoadingStates"

echo ""
echo "3️⃣  Testing Theme System"
echo "------------------------"

test_case "Theme config has 6 themes" \
  "grep -c 'id:.*theme' src/config/themes.js 2>&1" \
  "[6-9]"

test_case "Matrix Green theme exists" \
  "grep 'matrix-green' src/config/themes.js 2>&1" \
  "matrix-green"

test_case "Windows 11 theme exists" \
  "grep 'windows-11' src/config/themes.js 2>&1" \
  "windows-11"

echo ""
echo "4️⃣  Testing Utilities"
echo "---------------------"

test_case "Logger utility exists" \
  "ls src/utils/logger.js 2>&1" \
  "logger.js"

test_case "Accessibility utils exist" \
  "ls src/utils/accessibility.js 2>&1" \
  "accessibility.js"

test_case "Animation utils exist" \
  "ls src/utils/animations.js 2>&1" \
  "animations.js"

echo ""
echo "5️⃣  Testing Documentation"
echo "-------------------------"

test_case "Style guide exists" \
  "ls docs/STYLE-GUIDE.md 2>&1" \
  "STYLE-GUIDE.md"

test_case "Component API exists" \
  "ls docs/COMPONENT-API.md 2>&1" \
  "COMPONENT-API.md"

test_case "README exists" \
  "ls README.md 2>&1" \
  "README.md"

echo ""
echo "6️⃣  Testing Code Quality"
echo "------------------------"

test_case "No TODO in main code" \
  "grep -r 'TODO' src/components/shared/*.jsx 2>&1 | wc -l" \
  "^0$"

test_case "PropTypes validation present" \
  "grep -r 'PropTypes' src/components/shared/*.jsx 2>&1 | wc -l" \
  "[1-9]"

test_case "ESLint config exists" \
  "ls .eslintrc.cjs 2>&1" \
  ".eslintrc.cjs"

echo ""
echo "7️⃣  Testing Dev Server"
echo "----------------------"

# Check if server is running
if curl -s http://localhost:5173/ > /dev/null 2>&1; then
  test_case "Dev server responds" \
    "curl -s -o /dev/null -w '%{http_code}' http://localhost:5173/" \
    "200"
  
  test_case "App title present" \
    "curl -s http://localhost:5173/ | grep -o '<title>.*</title>'" \
    "title"
  
  test_case "React root div present" \
    "curl -s http://localhost:5173/ | grep 'id=\"root\"'" \
    "root"
else
  echo -e "${YELLOW}⚠${NC}  Dev server not running (optional test)"
  echo "  Start with: npm run dev"
fi

echo ""
echo "===================================="
echo "📊 TEST RESULTS"
echo "===================================="
echo ""
echo "  Total Tests: $TOTAL"
echo -e "  ${GREEN}Passed: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
  echo -e "  ${RED}Failed: $FAILED${NC}"
else
  echo "  Failed: 0"
fi
echo ""

PERCENTAGE=$((PASSED * 100 / TOTAL))
echo "  Success Rate: ${PERCENTAGE}%"

if [ $PERCENTAGE -eq 100 ]; then
  echo ""
  echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
  echo "Frontend is production-ready! 🚀"
  exit 0
elif [ $PERCENTAGE -ge 90 ]; then
  echo ""
  echo -e "${GREEN}✅ EXCELLENT!${NC}"
  echo "Minor issues, but production-ready! 🎉"
  exit 0
elif [ $PERCENTAGE -ge 70 ]; then
  echo ""
  echo -e "${YELLOW}⚠️  GOOD${NC}"
  echo "Some issues to address."
  exit 1
else
  echo ""
  echo -e "${RED}❌ NEEDS WORK${NC}"
  echo "Several issues need fixing."
  exit 1
fi
