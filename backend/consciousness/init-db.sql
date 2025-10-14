-- PFC Consciousness Database Initialization
-- Creates schema for decision persistence

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Note: Schema creation is handled by DecisionRepository.initialize()
-- This file is for any additional setup or seeding

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE vertice_consciousness TO postgres;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS public;

-- Set default privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO postgres;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO postgres;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Database initialized successfully';
END $$;
