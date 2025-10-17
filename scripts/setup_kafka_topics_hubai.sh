#!/bin/bash
# HUB-AI Cockpit Soberano - Kafka Topics Setup
# Creates topics for 3-layer narrative filter pipeline

set -e

KAFKA_BROKER="${KAFKA_BROKER:-localhost:9092}"
REPLICATION_FACTOR="${REPLICATION_FACTOR:-1}"

echo "=========================================="
echo "HUB-AI Cockpit Soberano - Kafka Topics"
echo "=========================================="
echo "Broker: $KAFKA_BROKER"
echo "Replication: $REPLICATION_FACTOR"
echo ""

# Check if kafka-topics command exists
if ! command -v kafka-topics.sh &> /dev/null; then
    echo "❌ kafka-topics.sh not found. Using docker exec..."
    KAFKA_CMD="docker exec vertice-kafka kafka-topics.sh"
else
    KAFKA_CMD="kafka-topics.sh"
fi

# Topic 1: Agent Communications (Input para Camada 1)
echo "Creating topic: agent-communications..."
$KAFKA_CMD --create \
  --bootstrap-server $KAFKA_BROKER \
  --topic agent-communications \
  --partitions 6 \
  --replication-factor $REPLICATION_FACTOR \
  --config retention.ms=604800000 \
  --config compression.type=snappy \
  --config max.message.bytes=1048576 \
  --if-not-exists

# Topic 2: Semantic Events (Output Camada 1 → Input Camada 2)
echo "Creating topic: semantic-events..."
$KAFKA_CMD --create \
  --bootstrap-server $KAFKA_BROKER \
  --topic semantic-events \
  --partitions 6 \
  --replication-factor $REPLICATION_FACTOR \
  --config retention.ms=259200000 \
  --config compression.type=snappy \
  --if-not-exists

# Topic 3: Strategic Patterns (Output Camada 2 → Input Camada 3)
echo "Creating topic: strategic-patterns..."
$KAFKA_CMD --create \
  --bootstrap-server $KAFKA_BROKER \
  --topic strategic-patterns \
  --partitions 3 \
  --replication-factor $REPLICATION_FACTOR \
  --config retention.ms=86400000 \
  --config compression.type=snappy \
  --if-not-exists

# Topic 4: Verdict Stream (Output Camada 3 → UI via WebSocket)
echo "Creating topic: verdict-stream..."
$KAFKA_CMD --create \
  --bootstrap-server $KAFKA_BROKER \
  --topic verdict-stream \
  --partitions 3 \
  --replication-factor $REPLICATION_FACTOR \
  --config retention.ms=86400000 \
  --config compression.type=snappy \
  --if-not-exists

echo ""
echo "✅ Topics created successfully!"
echo ""
echo "Listing created topics..."
$KAFKA_CMD --list \
  --bootstrap-server $KAFKA_BROKER | grep -E "(agent-communications|semantic-events|strategic-patterns|verdict-stream)"

echo ""
echo "=========================================="
echo "Topic Details:"
echo "=========================================="

for topic in agent-communications semantic-events strategic-patterns verdict-stream; do
    echo ""
    echo "📋 Topic: $topic"
    $KAFKA_CMD --describe \
      --bootstrap-server $KAFKA_BROKER \
      --topic $topic | grep -E "(Topic:|PartitionCount:|ReplicationFactor:)"
done

echo ""
echo "✅ Kafka topics setup complete!"
