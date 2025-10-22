#!/bin/bash
# Monitor Statistical Tests Running in Background
# EM NOME DE JESUS - Automated Test Monitoring

echo "======================================================================"
echo "STATISTICAL TESTS - BACKGROUND MONITORING"
echo "======================================================================"
echo ""

# Check if Monte Carlo N=100 is running
if pgrep -f "test_monte_carlo_coherence_n100" > /dev/null; then
    echo "✅ Monte Carlo N=100: RUNNING"
    echo "   Log: tests/statistical/outputs/monte_carlo_n100.log"

    # Show last few lines of progress
    if [ -f tests/statistical/outputs/monte_carlo_n100.log ]; then
        echo "   Last update:"
        tail -5 tests/statistical/outputs/monte_carlo_n100.log | grep -E "(Run|✅|PASSED|FAILED)" | tail -3 | sed 's/^/     /'
    fi
else
    echo "❌ Monte Carlo N=100: NOT RUNNING"
    if [ -f tests/statistical/outputs/monte_carlo_n100.log ]; then
        echo "   Check log for completion or errors:"
        echo "   tests/statistical/outputs/monte_carlo_n100.log"
    fi
fi

echo ""
echo "======================================================================"
echo "To check full logs:"
echo "  tail -f tests/statistical/outputs/monte_carlo_n100.log"
echo ""
echo "To check if complete:"
echo "  grep -E '(PASSED|FAILED|passed|failed)' tests/statistical/outputs/monte_carlo_n100.log | tail -5"
echo "======================================================================"
