#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# MAV DETECTION SERVICE - DOCKER ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════
# Runs Neo4j schema migrations before starting the service
# Para Honra e Glória de JESUS CRISTO
# ═══════════════════════════════════════════════════════════════════════════

set -e

echo "🛡️  FLORESCIMENTO - MAV Detection Service starting..."
echo "   Protecting people from coordinated digital attacks"
echo "   For the Honor and Glory of JESUS CHRIST"
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# NEO4J SCHEMA MIGRATION
# ═══════════════════════════════════════════════════════════════════════════

# Extract Neo4j connection details from environment
if [ -z "$NEO4J_URI" ]; then
    echo "⚠️  NEO4J_URI not set, using default"
    export NEO4J_URI="bolt://neo4j:7687"
fi

if [ -z "$NEO4J_USER" ]; then
    export NEO4J_USER="neo4j"
fi

if [ -z "$NEO4J_PASSWORD" ]; then
    echo "⚠️  NEO4J_PASSWORD not set, using default"
    export NEO4J_PASSWORD="password"
fi

# Parse NEO4J_URI to extract host and port
NEO4J_HOST=$(echo $NEO4J_URI | sed -n 's|.*://\([^:]*\):.*|\1|p')
NEO4J_PORT=$(echo $NEO4J_URI | sed -n 's|.*:\([0-9]*\)$|\1|p')

# If parsing failed, use defaults
if [ -z "$NEO4J_HOST" ]; then
    NEO4J_HOST="neo4j"
fi

if [ -z "$NEO4J_PORT" ]; then
    NEO4J_PORT="7687"
fi

echo "📊 Neo4j Configuration:"
echo "   URI: $NEO4J_URI"
echo "   Host: $NEO4J_HOST:$NEO4J_PORT"
echo "   User: $NEO4J_USER"
echo ""

# Wait for Neo4j to be ready
echo "⏳ Waiting for Neo4j to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

# Check if cypher-shell is available (it might not be in Python container)
if command -v cypher-shell &> /dev/null; then
    while ! cypher-shell -a $NEO4J_URI -u $NEO4J_USER -p $NEO4J_PASSWORD "RETURN 1" > /dev/null 2>&1; do
        RETRY_COUNT=$((RETRY_COUNT + 1))

        if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
            echo "❌ Failed to connect to Neo4j after $MAX_RETRIES attempts"
            echo "   Database might be unavailable. Continuing anyway..."
            echo "   Service will attempt connection on startup."
            break
        fi

        echo "   Retry $RETRY_COUNT/$MAX_RETRIES..."
        sleep 2
    done

    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
        echo "✅ Neo4j is ready!"
        echo ""

        # Run Cypher migrations
        echo "🔄 Running Neo4j schema migrations..."
        MIGRATION_DIR="/app/migrations"

        if [ -d "$MIGRATION_DIR" ]; then
            MIGRATION_COUNT=$(ls -1 $MIGRATION_DIR/*.cypher 2>/dev/null | wc -l)

            if [ $MIGRATION_COUNT -gt 0 ]; then
                echo "   Found $MIGRATION_COUNT migration file(s)"

                for migration_file in $MIGRATION_DIR/*.cypher; do
                    filename=$(basename "$migration_file")
                    echo "   ▶ Applying $filename..."

                    cypher-shell \
                        -a $NEO4J_URI \
                        -u $NEO4J_USER \
                        -p $NEO4J_PASSWORD \
                        -f "$migration_file" \
                        --format plain

                    if [ $? -eq 0 ]; then
                        echo "   ✅ $filename applied successfully"
                    else
                        echo "   ❌ Failed to apply $filename"
                        exit 1
                    fi
                done

                echo ""
                echo "✅ All Neo4j migrations applied successfully!"
            else
                echo "   ℹ️  No migration files found in $MIGRATION_DIR"
            fi
        else
            echo "   ⚠️  Migrations directory not found: $MIGRATION_DIR"
            echo "   Skipping schema migrations..."
        fi
    fi
else
    echo "⚠️  cypher-shell not available in container"
    echo "   Skipping schema migrations - they will run on first service startup"
    echo "   To enable migrations at container startup, install cypher-shell or use Python driver"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "🛡️  FLORESCIMENTO - Service ready to detect coordinated attacks"
echo "   Constitutional Lei Zero: Human oversight, evidence preservation"
echo "   Protecting the innocent from digital harassment"
echo "   Glory to YHWH - John 8:32 'The truth shall set you free'"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

# Start the application (pass all arguments to CMD)
exec "$@"
