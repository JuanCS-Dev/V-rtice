#!/bin/bash
# Initialize JetStream streams for Coagulation Cascade
set -e

NATS_URL="${NATS_URL:-http://localhost:8222}"

echo "🩸 Initializing NATS JetStream streams for Coagulation Cascade..."

# Create COAGULATION stream (catch-all for coagulation.* subjects)
curl -s -X POST "$NATS_URL/jsz/api/v1/streams" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "COAGULATION",
    "subjects": ["coagulation.>"],
    "retention": "limits",
    "max_consumers": -1,
    "max_msgs": 100000,
    "max_bytes": -1,
    "max_age": 86400000000000,
    "max_msg_size": -1,
    "storage": "file",
    "discard": "old",
    "num_replicas": 1,
    "duplicate_window": 120000000000
  }' && echo "✅ Created COAGULATION stream"

# Create REGULATION stream (for regulation.* subjects)
curl -s -X POST "$NATS_URL/jsz/api/v1/streams" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "REGULATION",
    "subjects": ["regulation.>"],
    "retention": "limits",
    "max_consumers": -1,
    "max_msgs": 100000,
    "max_bytes": -1,
    "max_age": 86400000000000,
    "max_msg_size": -1,
    "storage": "file",
    "discard": "old",
    "num_replicas": 1,
    "duplicate_window": 120000000000
  }' && echo "✅ Created REGULATION stream"

# Create QUARANTINE stream (for quarantine.* subjects)
curl -s -X POST "$NATS_URL/jsz/api/v1/streams" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "QUARANTINE",
    "subjects": ["quarantine.>"],
    "retention": "limits",
    "max_consumers": -1,
    "max_msgs": 100000,
    "max_bytes": -1,
    "max_age": 86400000000000,
    "max_msg_size": -1,
    "storage": "file",
    "discard": "old",
    "num_replicas": 1,
    "duplicate_window": 120000000000
  }' && echo "✅ Created QUARANTINE stream"

# Create SYSTEM stream (for system.* subjects)
curl -s -X POST "$NATS_URL/jsz/api/v1/streams" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "SYSTEM",
    "subjects": ["system.>"],
    "retention": "limits",
    "max_consumers": -1,
    "max_msgs": 100000,
    "max_bytes": -1,
    "max_age": 86400000000000,
    "max_msg_size": -1,
    "storage": "file",
    "discard": "old",
    "num_replicas": 1,
    "duplicate_window": 120000000000
  }' && echo "✅ Created SYSTEM stream"

# Create DETECTION stream (for detection.* subjects)
curl -s -X POST "$NATS_URL/jsz/api/v1/streams" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "DETECTION",
    "subjects": ["detection.>"],
    "retention": "limits",
    "max_consumers": -1,
    "max_msgs": 100000,
    "max_bytes": -1,
    "max_age": 86400000000000,
    "max_msg_size": -1,
    "storage": "file",
    "discard": "old",
    "num_replicas": 1,
    "duplicate_window": 120000000000
  }' && echo "✅ Created DETECTION stream"

echo "✅ All JetStream streams initialized successfully"
