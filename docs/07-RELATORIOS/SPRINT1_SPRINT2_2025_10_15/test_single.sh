#!/bin/bash
SERVICE="agent_communication"
cd "/home/juan/vertice-dev/backend/services/$SERVICE"

echo "Service: $SERVICE"
echo "Location: $(pwd)"
echo ""

echo "Python files:"
find . -maxdepth 3 -name "*.py" -type f ! -path "./__pycache__/*" ! -path "./tests/*" 2>/dev/null

echo ""
echo "Test files:"
find tests -name "*.py" 2>/dev/null

echo ""
echo "Running pytest..."
cd /home/juan/vertice-dev

PYTHONPATH="/home/juan/vertice-dev/backend/services/$SERVICE:/home/juan/vertice-dev:$PYTHONPATH" \
pytest "backend/services/$SERVICE/tests/" \
    --cov="backend/services/$SERVICE" \
    --cov-report=term \
    -v
