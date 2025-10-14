#!/bin/bash
# Script: setup_test_db.sh
# Purpose: Setup PostgreSQL test database for Social Memory tests
# Author: Claude Code (Executor Tático)
# Date: 2025-10-14
# Usage: sudo ./scripts/setup_test_db.sh

set -e  # Exit on error

echo "🐘 Setting up PostgreSQL test database for Social Memory..."

# Colors for output
GREEN='\033[0.32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Database configuration
DB_NAME="maximus_test"
DB_USER="maximus"
DB_PASSWORD="test_password"

# Check if PostgreSQL is running
if ! sudo -u postgres psql -c '\q' 2>/dev/null; then
    echo -e "${RED}❌ PostgreSQL is not running. Start it with: sudo systemctl start postgresql${NC}"
    exit 1
fi

echo "  ├─ PostgreSQL is running ✓"

# Create database if not exists
echo "  ├─ Creating database '$DB_NAME'..."
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"

# Create user if not exists
echo "  ├─ Creating user '$DB_USER'..."
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname = '$DB_USER'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"

# Grant privileges
echo "  ├─ Granting privileges..."
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
sudo -u postgres psql -c "ALTER DATABASE $DB_NAME OWNER TO $DB_USER;"

# Run migration
MIGRATION_FILE="/home/juan/vertice-dev/backend/services/maximus_core_service/migrations/001_create_social_patterns.sql"

if [ ! -f "$MIGRATION_FILE" ]; then
    echo -e "${RED}❌ Migration file not found: $MIGRATION_FILE${NC}"
    exit 1
fi

echo "  ├─ Running migration 001_create_social_patterns.sql..."
sudo -u postgres psql $DB_NAME < "$MIGRATION_FILE" > /dev/null 2>&1

# Verify table exists
echo "  ├─ Verifying table 'social_patterns' exists..."
TABLE_EXISTS=$(sudo -u postgres psql $DB_NAME -tc "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'social_patterns');")

if [[ "$TABLE_EXISTS" =~ "t" ]]; then
    echo -e "${GREEN}  ✅ Table 'social_patterns' created successfully${NC}"
else
    echo -e "${RED}  ❌ Table 'social_patterns' was not created${NC}"
    exit 1
fi

# Verify pgvector extension (optional, for future CBR similarity search)
echo "  ├─ Checking pgvector extension..."
PGVECTOR_EXISTS=$(sudo -u postgres psql $DB_NAME -tc "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector');")

if [[ "$PGVECTOR_EXISTS" =~ "t" ]]; then
    echo "  ✅ pgvector extension already installed"
else
    echo "  ⚠️  pgvector extension not found (optional, needed for FASE 4: CBR similarity search)"
    echo "     To install: https://github.com/pgvector/pgvector"
fi

# Test connection with maximus user
echo "  ├─ Testing connection with maximus user..."
PGPASSWORD=$DB_PASSWORD psql -h localhost -U $DB_USER -d $DB_NAME -c '\q' 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}  ✅ Connection test successful${NC}"
else
    echo -e "${RED}  ❌ Connection test failed${NC}"
    exit 1
fi

# Count seed data
SEED_COUNT=$(PGPASSWORD=$DB_PASSWORD psql -h localhost -U $DB_USER -d $DB_NAME -tc "SELECT COUNT(*) FROM social_patterns;" 2>/dev/null | xargs)

echo "  ├─ Seed data: $SEED_COUNT agents"

echo ""
echo -e "${GREEN}🎉 PostgreSQL test database setup complete!${NC}"
echo ""
echo "Configuration:"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo "  Password: $DB_PASSWORD"
echo "  Host: localhost"
echo "  Port: 5432"
echo ""
echo "Next steps:"
echo "  1. cd /home/juan/vertice-dev/backend/services/maximus_core_service"
echo "  2. pytest compassion/test_social_memory.py -v"
echo ""
