#!/bin/bash
# HUB-AI Cockpit Soberano - PostgreSQL Migration Runner
# Applies schema migrations for all HUB-AI services

set -e

POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-vertice-postgres}"
POSTGRES_USER="${POSTGRES_USER:-vertice}"
POSTGRES_DB="${POSTGRES_DB:-vertice_db}"

echo "=========================================="
echo "HUB-AI Cockpit Soberano - DB Migration"
echo "=========================================="
echo "Container: $POSTGRES_CONTAINER"
echo "Database: $POSTGRES_DB"
echo "User: $POSTGRES_USER"
echo ""

MIGRATION_FILE="backend/services/narrative_filter_service/migrations/001_initial_schema.sql"

if [ ! -f "$MIGRATION_FILE" ]; then
    echo "❌ Migration file not found: $MIGRATION_FILE"
    exit 1
fi

echo "Applying migration: $MIGRATION_FILE"
echo ""

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
    echo "⚠️  PostgreSQL container not running: $POSTGRES_CONTAINER"
    echo "Start it with: docker start $POSTGRES_CONTAINER"
    exit 1
fi

# Apply migration
docker exec -i "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$MIGRATION_FILE"

echo ""
echo "✅ Migration applied successfully!"
echo ""

# Verify tables
echo "Verifying created tables..."
docker exec "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as columns
FROM information_schema.tables t
WHERE table_schema = 'public' 
    AND table_name IN (
        'semantic_representations', 
        'strategic_patterns', 
        'alliances', 
        'verdicts', 
        'c2l_commands', 
        'audit_trail'
    )
ORDER BY table_name;
"

echo ""
echo "✅ Database setup complete!"
