#!/bin/bash
# Setup Kafka topics for Cockpit Soberano
# Narrative Filter Service - 4 topics

set -euo pipefail

KAFKA_BROKER="${KAFKA_BROKER:-localhost:9092}"
PARTITIONS="${PARTITIONS:-3}"
REPLICATION="${REPLICATION:-1}"

echo "🔧 Setting up Kafka topics for Cockpit Soberano..."
echo "Broker: $KAFKA_BROKER"
echo "Partitions: $PARTITIONS"
echo "Replication: $REPLICATION"
echo ""

# Function to create topic
create_topic() {
    local topic=$1
    local description=$2
    
    echo "📝 Creating topic: $topic"
    echo "   Description: $description"
    
    kafka-topics.sh --create \
        --bootstrap-server "$KAFKA_BROKER" \
        --topic "$topic" \
        --partitions "$PARTITIONS" \
        --replication-factor "$REPLICATION" \
        --if-not-exists \
        --config retention.ms=604800000 \
        --config compression.type=lz4
    
    echo "✅ Topic $topic created/verified"
    echo ""
}

# TOPIC 1: Raw agent communications (INPUT)
create_topic "agent-communications" \
    "Raw messages from multi-agent systems and MAXIMUS services"

# TOPIC 2: Semantic representations (INTERMEDIATE - Camada 1 → Camada 2)
create_topic "semantic-events" \
    "Processed semantic representations with embeddings and intent classification"

# TOPIC 3: Strategic patterns (INTERMEDIATE - Camada 2 → Camada 3)
create_topic "strategic-patterns" \
    "Detected strategic patterns (alliances, deception, inconsistencies, collusion)"

# TOPIC 4: Final verdicts (OUTPUT - Camada 3 → UI)
create_topic "verdicts-stream" \
    "Final verdicts with severity, color-coding, and C2L recommendations"

echo "🎯 All Kafka topics created successfully!"
echo ""
echo "To verify:"
echo "  kafka-topics.sh --list --bootstrap-server $KAFKA_BROKER"
echo ""
echo "To describe:"
echo "  kafka-topics.sh --describe --bootstrap-server $KAFKA_BROKER --topic <topic-name>"
