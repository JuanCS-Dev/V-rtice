#!/bin/bash
# Quick Integration Test - Vértice

FRONTEND_URL="https://vertice-frontend-vuvnhfmzpa-ue.a.run.app"
API_GATEWAY="http://34.148.161.131:8000"

echo "🧪 Quick Integration Test"
echo ""

echo -n "1. Frontend... "
if curl -s -f -m 3 "$FRONTEND_URL" > /dev/null 2>&1; then
    echo "✅"
else
    echo "❌"
fi

echo -n "2. API Gateway Health... "
if curl -s -f -m 3 "$API_GATEWAY/health" > /dev/null 2>&1; then
    echo "✅"
else
    echo "❌"
fi

echo -n "3. API Gateway Root... "
if curl -s -f -m 3 "$API_GATEWAY/" > /dev/null 2>&1; then
    echo "✅"
else
    echo "❌"
fi

echo ""
echo "✅ Integration test complete!"
