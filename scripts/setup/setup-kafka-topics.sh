#!/bin/bash
# Purpose: Create Kafka topics for Adaptive Immunity System
# Usage: ./setup-kafka-topics.sh
# Author: MAXIMUS Team
# Date: 2025-10-11

set -e
set -u

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 MAXIMUS Adaptive Immunity - Kafka Topics Setup${NC}"
echo "=================================================="

# Find Kafka container
KAFKA_CONTAINER=$(docker ps --filter "name=kafka-immunity" --format "{{.Names}}" | head -1)

if [ -z "$KAFKA_CONTAINER" ]; then
  echo -e "${RED}❌ Kafka container not running${NC}"
  echo "Please start infrastructure first:"
  echo "  docker-compose -f docker-compose.adaptive-immunity.yml up -d"
  exit 1
fi

echo -e "${GREEN}✓${NC} Found Kafka container: $KAFKA_CONTAINER"
echo ""

# Wait for Kafka to be ready
echo "⏳ Waiting for Kafka to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  if docker exec $KAFKA_CONTAINER kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Kafka is ready"
    break
  fi
  RETRY_COUNT=$((RETRY_COUNT + 1))
  echo "  Attempt $RETRY_COUNT/$MAX_RETRIES..."
  sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
  echo -e "${RED}❌ Kafka failed to become ready${NC}"
  exit 1
fi

echo ""
echo "Creating topics..."
echo ""

# Function to create topic
create_topic() {
  local TOPIC_NAME=$1
  local PARTITIONS=$2
  local DESCRIPTION=$3
  
  echo -e "${YELLOW}→${NC} Creating topic: $TOPIC_NAME (partitions: $PARTITIONS)"
  
  if docker exec $KAFKA_CONTAINER kafka-topics --create \
    --topic "$TOPIC_NAME" \
    --partitions "$PARTITIONS" \
    --replication-factor 1 \
    --if-not-exists \
    --bootstrap-server localhost:9092 > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓${NC} Created: $TOPIC_NAME"
    echo -e "    Description: $DESCRIPTION"
  else
    echo -e "${GREEN}  ✓${NC} Already exists: $TOPIC_NAME"
  fi
  echo ""
}

# Create topics
create_topic "maximus.adaptive-immunity.apv" 3 \
  "APV stream from Oráculo to Eureka (Actionable Prioritized Vulnerabilities)"

create_topic "maximus.adaptive-immunity.patches" 3 \
  "Patches stream from Eureka to HITL (Generated remediation patches)"

create_topic "maximus.adaptive-immunity.events" 3 \
  "General events stream (all system events for observability)"

create_topic "maximus.adaptive-immunity.dlq" 1 \
  "Dead Letter Queue (failed messages for manual review)"

create_topic "maximus.adaptive-immunity.metrics" 1 \
  "Metrics stream (performance and health metrics)"

echo "=================================================="
echo -e "${GREEN}✅ Kafka Topics Setup Complete${NC}"
echo ""

# List all topics
echo "📋 All topics:"
docker exec $KAFKA_CONTAINER kafka-topics --list --bootstrap-server localhost:9092 | grep "maximus.adaptive-immunity" || true

echo ""

# Show topic details
echo "📊 Topic details:"
for TOPIC in "maximus.adaptive-immunity.apv" "maximus.adaptive-immunity.patches" "maximus.adaptive-immunity.events" "maximus.adaptive-immunity.dlq" "maximus.adaptive-immunity.metrics"; do
  echo ""
  echo -e "${YELLOW}Topic:${NC} $TOPIC"
  docker exec $KAFKA_CONTAINER kafka-topics --describe --topic "$TOPIC" --bootstrap-server localhost:9092 | grep -E "(Topic|Partition)" || true
done

echo ""
echo "=================================================="
echo -e "${GREEN}✅ Setup Complete${NC}"
echo ""
echo "Next steps:"
echo "  1. Verify topics: docker exec $KAFKA_CONTAINER kafka-topics --list --bootstrap-server localhost:9092"
echo "  2. Monitor topics: Access Kafka UI at http://localhost:8090"
echo "  3. Start implementing Oráculo Core"
echo ""
