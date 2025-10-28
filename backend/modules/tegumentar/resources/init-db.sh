#!/bin/bash
# Tegumentar Database Initialization Script
# Executado automaticamente pelo PostgreSQL container no primeiro boot

set -e

echo "🛡️  Inicializando database Tegumentar..."

# Criar database tegumentar
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE tegumentar;
    GRANT ALL PRIVILEGES ON DATABASE tegumentar TO $POSTGRES_USER;
EOSQL

echo "✅ Database 'tegumentar' criado"

# Aplicar schema
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "tegumentar" < /docker-entrypoint-initdb.d/schema.sql

echo "✅ Schema aplicado com sucesso"
echo "🎯 Tegumentar PostgreSQL pronto para uso!"
