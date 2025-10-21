#!/bin/bash
# Complete system shutdown - stops all containers and processes

echo "🛑 Stopping all Docker containers..."
CONTAINERS=$(docker ps -q)
if [ -n "$CONTAINERS" ]; then
    docker stop $CONTAINERS
    echo "✅ Stopped $(echo $CONTAINERS | wc -w) containers"
else
    echo "ℹ️  No containers running"
fi

echo ""
echo "🔍 Checking for stuck Python processes..."
STUCK_PYTHON=$(pgrep -f "multiprocessing|uvicorn.*--workers" || true)
if [ -n "$STUCK_PYTHON" ]; then
    echo "⚠️  Found stuck processes: $STUCK_PYTHON"
    echo "   Run: pkill -9 -f 'multiprocessing|uvicorn.*--workers'"
else
    echo "✅ No stuck processes"
fi

echo ""
echo "🌡️  System Temperatures:"
sensors 2>/dev/null | grep -E "Package|Composite|temp1" || echo "sensors not available"

echo ""
echo "📊 System Load:"
uptime

echo ""
echo "💾 Memory Status:"
free -h | grep -E "Mem:|Swap:"

echo ""
echo "✅ Shutdown complete!"
