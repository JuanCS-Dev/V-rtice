#!/bin/bash
# VCLI Shell Test Script
# Tests the bubbletea shell fix for command output display

set -e

VCLI_BIN="./bin/vcli"
TEST_RESULTS=()

echo "======================================"
echo "🧪 VCLI SHELL TEST SUITE"
echo "======================================"
echo ""

# Test 1: Binary exists
echo "Test 1: Checking binary..."
if [ -f "$VCLI_BIN" ]; then
    echo "✅ Binary exists: $VCLI_BIN"
    TEST_RESULTS+=("PASS: Binary exists")
else
    echo "❌ Binary not found: $VCLI_BIN"
    echo "Run: make build"
    exit 1
fi
echo ""

# Test 2: Help command
echo "Test 2: Testing help command..."
if $VCLI_BIN --help > /dev/null 2>&1; then
    echo "✅ Help command works"
    TEST_RESULTS+=("PASS: Help command")
else
    echo "❌ Help command failed"
    TEST_RESULTS+=("FAIL: Help command")
fi
echo ""

# Test 3: Shell command exists
echo "Test 3: Checking shell command..."
if $VCLI_BIN shell --help > /dev/null 2>&1; then
    echo "✅ Shell command exists"
    TEST_RESULTS+=("PASS: Shell command exists")
else
    echo "❌ Shell command not found"
    TEST_RESULTS+=("FAIL: Shell command not found")
fi
echo ""

# Test 4: Check NLP command status
echo "Test 4: Checking NLP/ask command..."
if [ -f "cmd/ask.go.broken" ]; then
    echo "⚠️  NLP command is disabled (ask.go.broken)"
    echo "   To enable: mv cmd/ask.go.broken cmd/ask.go"
    TEST_RESULTS+=("INFO: NLP disabled")
else
    if $VCLI_BIN ask --help > /dev/null 2>&1; then
        echo "✅ NLP command available"
        TEST_RESULTS+=("PASS: NLP enabled")
    else
        echo "❌ NLP command error"
        TEST_RESULTS+=("FAIL: NLP error")
    fi
fi
echo ""

# Test 5: Check executor capture method exists
echo "Test 5: Checking ExecuteWithCapture implementation..."
if grep -q "ExecuteWithCapture" internal/shell/executor.go; then
    echo "✅ ExecuteWithCapture method found"
    TEST_RESULTS+=("PASS: Capture method exists")
else
    echo "❌ ExecuteWithCapture method not found"
    TEST_RESULTS+=("FAIL: Capture method missing")
fi
echo ""

# Test 6: Check view renderCommandOutput exists
echo "Test 6: Checking renderCommandOutput in view..."
if grep -q "renderCommandOutput" internal/shell/bubbletea/view.go; then
    echo "✅ renderCommandOutput method found"
    TEST_RESULTS+=("PASS: Render method exists")
else
    echo "❌ renderCommandOutput method not found"
    TEST_RESULTS+=("FAIL: Render method missing")
fi
echo ""

# Test 7: Check model has commandOutput field
echo "Test 7: Checking commandOutput field in model..."
if grep -q "commandOutput.*\[\]string" internal/shell/bubbletea/model.go; then
    echo "✅ commandOutput field found in Model"
    TEST_RESULTS+=("PASS: Model field exists")
else
    echo "❌ commandOutput field not found"
    TEST_RESULTS+=("FAIL: Model field missing")
fi
echo ""

# Test 8: Check LLM configuration
echo "Test 8: Checking LLM API keys..."
KEYS_FOUND=0
if env | grep -q "OPENAI_API_KEY"; then
    echo "✅ OPENAI_API_KEY found in environment"
    KEYS_FOUND=$((KEYS_FOUND + 1))
fi
if env | grep -q "GEMINI_API_KEY"; then
    echo "✅ GEMINI_API_KEY found in environment"
    KEYS_FOUND=$((KEYS_FOUND + 1))
fi
if [ $KEYS_FOUND -eq 0 ]; then
    echo "⚠️  No LLM API keys found in environment"
    echo "   Set: export OPENAI_API_KEY=sk-..."
    echo "   Or:  export GEMINI_API_KEY=..."
    TEST_RESULTS+=("INFO: No LLM keys")
else
    echo "✅ Found $KEYS_FOUND LLM API key(s)"
    TEST_RESULTS+=("PASS: LLM keys configured")
fi
echo ""

# Test 9: Check MAXIMUS service availability
echo "Test 9: Checking MAXIMUS service..."
if curl -s -m 2 http://localhost:8080/health > /dev/null 2>&1; then
    echo "✅ MAXIMUS service responding on :8080"
    TEST_RESULTS+=("PASS: MAXIMUS online")
else
    echo "⚠️  MAXIMUS service not responding on :8080"
    echo "   May need to start backend services"
    TEST_RESULTS+=("INFO: MAXIMUS offline")
fi
echo ""

# Summary
echo "======================================"
echo "📊 TEST SUMMARY"
echo "======================================"
for result in "${TEST_RESULTS[@]}"; do
    echo "$result"
done
echo ""

# Count results
PASS_COUNT=$(printf '%s\n' "${TEST_RESULTS[@]}" | grep -c "^PASS" || true)
FAIL_COUNT=$(printf '%s\n' "${TEST_RESULTS[@]}" | grep -c "^FAIL" || true)
INFO_COUNT=$(printf '%s\n' "${TEST_RESULTS[@]}" | grep -c "^INFO" || true)

echo "Results: $PASS_COUNT passed, $FAIL_COUNT failed, $INFO_COUNT info"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo "✅ All critical tests passed!"
    echo ""
    echo "Next steps:"
    echo "1. Test shell manually: $VCLI_BIN shell"
    echo "2. Try commands: k8s get pods, /help, etc"
    echo "3. Enable NLP: mv cmd/ask.go.broken cmd/ask.go && make build"
    echo "4. Configure LLM keys if needed"
    exit 0
else
    echo "❌ Some tests failed. Review the output above."
    exit 1
fi
