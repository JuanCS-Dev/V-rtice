#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# BEHAVIORAL ANALYZER SERVICE - DOCKER ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════
# Runs database migrations before starting the service
# Para Honra e Glória de JESUS CRISTO
# ═══════════════════════════════════════════════════════════════════════════

set -e

echo "🌱 FLORESCIMENTO - Behavioral Analyzer Service starting..."
echo "   For the Honor and Glory of JESUS CHRIST"
echo ""

# ═══════════════════════════════════════════════════════════════════════════
# DATABASE MIGRATION
# ═══════════════════════════════════════════════════════════════════════════

# Extract database connection details from DATABASE_URL
# Format: postgresql://user:pass@host:port/database
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  DATABASE_URL not set, using default for TimescaleDB"
    export DATABASE_URL="postgresql://vertice:vertice_secure_password@timescaledb:5432/behavioral_analysis"
fi

# Parse DATABASE_URL
DB_USER=$(echo $DATABASE_URL | sed -n 's|.*://\([^:]*\):.*|\1|p')
DB_PASS=$(echo $DATABASE_URL | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p')
DB_HOST=$(echo $DATABASE_URL | sed -n 's|.*@\([^:]*\):.*|\1|p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's|.*:\([0-9]*\)/.*|\1|p')
DB_NAME=$(echo $DATABASE_URL | sed -n 's|.*/\([^?]*\).*|\1|p')

echo "📊 Database Configuration:"
echo "   Host: $DB_HOST:$DB_PORT"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"
echo ""

# Wait for database to be ready
echo "⏳ Waiting for TimescaleDB to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while ! PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "SELECT 1" > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))

    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "❌ Failed to connect to TimescaleDB after $MAX_RETRIES attempts"
        echo "   Database might be unavailable. Exiting..."
        exit 1
    fi

    echo "   Retry $RETRY_COUNT/$MAX_RETRIES..."
    sleep 2
done

echo "✅ TimescaleDB is ready!"
echo ""

# Create database if it doesn't exist
echo "🗄️  Ensuring database exists..."
PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
    PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME"

echo "✅ Database ready: $DB_NAME"
echo ""

# Run migrations
echo "🔄 Running database migrations..."
MIGRATION_DIR="/app/migrations"

if [ -d "$MIGRATION_DIR" ]; then
    MIGRATION_COUNT=$(ls -1 $MIGRATION_DIR/*.sql 2>/dev/null | wc -l)

    if [ $MIGRATION_COUNT -gt 0 ]; then
        echo "   Found $MIGRATION_COUNT migration file(s)"

        for migration_file in $MIGRATION_DIR/*.sql; do
            filename=$(basename "$migration_file")
            echo "   ▶ Applying $filename..."

            PGPASSWORD=$DB_PASS psql \
                -h $DB_HOST \
                -p $DB_PORT \
                -U $DB_USER \
                -d $DB_NAME \
                -f "$migration_file" \
                -v ON_ERROR_STOP=1 \
                --quiet

            if [ $? -eq 0 ]; then
                echo "   ✅ $filename applied successfully"
            else
                echo "   ❌ Failed to apply $filename"
                exit 1
            fi
        done

        echo ""
        echo "✅ All migrations applied successfully!"
    else
        echo "   ℹ️  No migration files found in $MIGRATION_DIR"
    fi
else
    echo "   ⚠️  Migrations directory not found: $MIGRATION_DIR"
    echo "   Skipping migrations..."
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════════════"
echo "🌱 FLORESCIMENTO - Service ready to analyze behavioral threats"
echo "   Constitutional Lei Zero: Human oversight, GDPR compliance, audit trails"
echo "   Every threat detected protects His people"
echo "   Glory to YHWH - Colossenses 3:23"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""

# Start the application (pass all arguments to CMD)
exec "$@"
