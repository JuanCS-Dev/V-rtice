#!/bin/bash

# Start HITL Mock API Server
cd /home/juan/vertice-dev/backend/services/adaptive_immune_system

export PYTHONPATH=/home/juan/vertice-dev/backend/services/adaptive_immune_system:$PYTHONPATH

echo "🚀 Starting HITL Mock API Server..."
echo "📍 http://localhost:8003"
echo "📚 Docs: http://localhost:8003/docs"
echo ""

python3 -m hitl.test_mock_api
