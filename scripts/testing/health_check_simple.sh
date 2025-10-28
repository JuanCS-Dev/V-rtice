#!/bin/bash
# System health check before running tests

echo "🏥 SYSTEM HEALTH CHECK"
echo "====================="

echo ""
echo "🐳 Docker Containers:"
CONTAINER_COUNT=$(docker ps -q | wc -l)
echo "   Running: $CONTAINER_COUNT"
if [ "$CONTAINER_COUNT" -gt 10 ]; then
    echo "   ⚠️  WARNING: More than 10 containers running!"
fi
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Size}}"

echo ""
echo "🌡️  Temperatures:"
sensors 2>/dev/null | grep -E "Package|Composite|temp1" || echo "sensors not available"

CPU_TEMP=$(sensors 2>/dev/null | grep "Package id 0" | awk '{print $4}' | sed 's/+//;s/°C//' || echo "0")
if [ "${CPU_TEMP%.*}" -gt 60 ]; then
    echo "   ⚠️  WARNING: CPU temperature high (${CPU_TEMP}°C)"
fi

echo ""
echo "📊 System Load:"
uptime
LOAD=$(uptime | awk -F'load average:' '{print $2}' | awk -F',' '{print $1}' | xargs)
if (( $(echo "$LOAD > 4.0" | bc -l 2>/dev/null || echo "0") )); then
    echo "   ⚠️  WARNING: High load average ($LOAD)"
fi

echo ""
echo "💾 Memory:"
free -h | grep -E "Mem:|Swap:"
MEM_USED=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
if [ "$MEM_USED" -gt 80 ]; then
    echo "   ⚠️  WARNING: Memory usage high (${MEM_USED}%)"
fi

echo ""
echo "🔍 Disk I/O (NVMe):"
if command -v iostat &> /dev/null; then
    iostat -x nvme0n1 1 1 | tail -2
else
    echo "   iostat not installed"
fi

echo ""
echo "🐍 Python Processes:"
PYTHON_PROCS=$(pgrep -f "multiprocessing|uvicorn.*--workers" | wc -l)
echo "   Multiprocessing/Workers: $PYTHON_PROCS"
if [ "$PYTHON_PROCS" -gt 0 ]; then
    ps aux | grep -E "multiprocessing|uvicorn.*--workers" | grep -v grep | head -5
fi

echo ""
echo "✅ PRE-TEST CHECKLIST:"
echo "----------------------"
echo -n "   [ "
[ "$CONTAINER_COUNT" -le 5 ] && echo -n "✓" || echo -n "✗"
echo " ] Containers ≤ 5"

echo -n "   [ "
[ "${CPU_TEMP%.*}" -lt 50 ] && echo -n "✓" || echo -n "✗"
echo " ] CPU temp < 50°C"

echo -n "   [ "
(( $(echo "$LOAD < 2.0" | bc -l 2>/dev/null || echo "1") )) && echo -n "✓" || echo -n "✗"
echo " ] Load < 2.0"

echo -n "   [ "
[ "$MEM_USED" -lt 60 ] && echo -n "✓" || echo -n "✗"
echo " ] Memory < 60%"

echo -n "   [ "
[ "$PYTHON_PROCS" -eq 0 ] && echo -n "✓" || echo -n "✗"
echo " ] No stuck processes"

echo ""
