#!/bin/bash
# Script: setup_test_db_no_sudo.sh
# Purpose: Setup PostgreSQL test database (assuming postgres peer auth or psql access)
# Author: Claude Code
# Usage: ./scripts/setup_test_db_no_sudo.sh

set -e

echo "🐘 Setting up PostgreSQL test database for Social Memory..."

DB_NAME="maximus_test"
DB_USER="maximus"
DB_PASSWORD="test_password"

# Try to connect as current user to postgres database
psql -d postgres -c '\q' 2>/dev/null || {
    echo "❌ Cannot connect to PostgreSQL. Ensure PostgreSQL is running and you have access."
    echo "   Try: sudo -u postgres psql"
    exit 1
}

echo "  ├─ PostgreSQL accessible ✓"

# Create database
psql -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
    psql -d postgres -c "CREATE DATABASE $DB_NAME;"

# Create user
psql -d postgres -tc "SELECT 1 FROM pg_roles WHERE rolname = '$DB_USER'" | grep -q 1 || \
    psql -d postgres -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"

# Grant privileges
psql -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

# Run migration
psql -d $DB_NAME < /home/juan/vertice-dev/backend/services/maximus_core_service/migrations/001_create_social_patterns.sql

echo "✅ Setup complete!"
