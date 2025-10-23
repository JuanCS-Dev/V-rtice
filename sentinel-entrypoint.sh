#!/bin/sh
# Redis Sentinel Entrypoint
# Waits for redis-master DNS to be resolvable before starting

echo "Waiting for redis-master DNS to be resolvable..."

# Wait for DNS (max 60 seconds)
timeout=60
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if nslookup redis-master >/dev/null 2>&1; then
        echo "redis-master is resolvable!"
        break
    fi
    echo "Waiting for DNS... ($elapsed/$timeout)"
    sleep 2
    elapsed=$((elapsed + 2))
done

if [ $elapsed -ge $timeout ]; then
    echo "ERROR: redis-master DNS not resolvable after ${timeout}s"
    exit 1
fi

# Start Redis Sentinel
echo "Starting Redis Sentinel..."
exec redis-sentinel /etc/redis/sentinel.conf
