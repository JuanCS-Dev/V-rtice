#!/bin/bash
# HITL Backend Startup Script
# Ensures all dependencies are installed and starts the server

set -e  # Exit on error

echo "============================================"
echo "🚀 HITL Backend Startup"
echo "============================================"
echo ""

# Check Python version
PYTHON_VERSION=$(/home/juan/vertice-dev/.venv/bin/python --version 2>&1)
echo "✓ Python: $PYTHON_VERSION"

# Change to correct directory
cd /home/juan/vertice-dev/backend/services/reactive_fabric_core
echo "✓ Working directory: $(pwd)"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
/home/juan/vertice-dev/.venv/bin/pip install -q -r hitl/requirements.txt
echo "✓ Dependencies installed"
echo ""

# Kill any existing process on port 8002
echo "🔍 Checking for existing processes on port 8002..."
if lsof -ti:8002 > /dev/null 2>&1; then
    echo "⚠️  Killing existing process on port 8002..."
    lsof -ti:8002 | xargs kill -9 2>/dev/null || true
    sleep 2
fi
echo "✓ Port 8002 is free"
echo ""

# Start server
echo "🌐 Starting HITL backend on port 8002..."
echo "============================================"
echo ""
PYTHONPATH=. /home/juan/vertice-dev/.venv/bin/python hitl/hitl_backend.py
