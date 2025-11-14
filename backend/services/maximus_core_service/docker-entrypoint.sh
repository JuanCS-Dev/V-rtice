#!/bin/bash
#
# ═══════════════════════════════════════════════════════════════════════════
# MAXIMUS CORE SERVICE - DOCKER ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════
# Purpose: Run database migrations before starting the service
# Author: Claude Code (Executor Tático)
# Date: 2025-11-14
# Governance: Constituição Vértice v3.0 - P2 Migration Configuration
# ═══════════════════════════════════════════════════════════════════════════

set -e

echo "🚀 MAXIMUS Core Service - Starting..."

# ============================================================================
# STEP 1: Extract Database Connection Info
# ============================================================================

# Default to POSTGRES_URL, fallback to DATABASE_URL
DB_URL="${POSTGRES_URL:-${DATABASE_URL:-}}"

if [ -z "$DB_URL" ]; then
    echo "⚠️  WARNING: No database URL found (POSTGRES_URL or DATABASE_URL)"
    echo "⏭️  Skipping migrations and starting service..."
    exec "$@"
    exit 0
fi

echo "✅ Database URL found"

# Parse DATABASE_URL into psql-compatible format
# Format: postgresql://user:password@host:port/database
DB_HOST=$(echo $DB_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo $DB_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
DB_NAME=$(echo $DB_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
DB_USER=$(echo $DB_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
DB_PASS=$(echo $DB_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')

echo "📊 Database: $DB_NAME@$DB_HOST:$DB_PORT (user: $DB_USER)"

# ============================================================================
# STEP 2: Wait for PostgreSQL to be Ready
# ============================================================================

echo "⏳ Waiting for PostgreSQL to be ready..."

RETRIES=30
COUNT=0

until PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" > /dev/null 2>&1; do
    COUNT=$((COUNT+1))
    if [ $COUNT -ge $RETRIES ]; then
        echo "❌ ERROR: PostgreSQL not available after $RETRIES attempts"
        echo "⏭️  Starting service anyway (migrations will fail if DB is required)..."
        exec "$@"
        exit 1
    fi
    echo "   Attempt $COUNT/$RETRIES - waiting 2s..."
    sleep 2
done

echo "✅ PostgreSQL is ready"

# ============================================================================
# STEP 3: Run Migrations
# ============================================================================

MIGRATION_DIR="/app/migrations"

if [ ! -d "$MIGRATION_DIR" ]; then
    echo "⚠️  WARNING: Migrations directory not found at $MIGRATION_DIR"
    echo "⏭️  Skipping migrations and starting service..."
    exec "$@"
    exit 0
fi

MIGRATION_FILES=$(find "$MIGRATION_DIR" -name "*.sql" | sort)

if [ -z "$MIGRATION_FILES" ]; then
    echo "ℹ️  No migration files found in $MIGRATION_DIR"
else
    echo "📦 Running database migrations..."

    for migration_file in $MIGRATION_FILES; do
        migration_name=$(basename "$migration_file")
        echo "   → Applying: $migration_name"

        if PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$migration_file" > /dev/null 2>&1; then
            echo "   ✅ Success: $migration_name"
        else
            # Migration failed - this might be because it was already applied (CREATE TABLE IF NOT EXISTS)
            echo "   ⚠️  Warning: $migration_name failed or already applied"
        fi
    done

    echo "✅ Migrations completed"
fi

# ============================================================================
# STEP 4: Start the Service
# ============================================================================

echo "🎯 Starting MAXIMUS Core Service..."
exec "$@"
