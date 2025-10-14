-- Migration: 001_create_social_patterns.sql
-- Purpose: Create PostgreSQL schema for SocialMemory storage
-- Author: Claude Code (Executor Tático)
-- Date: 2025-10-14
-- Governance: Constituição Vértice v2.5 - Padrão Pagani

-- ============================================================================
-- SOCIAL PATTERNS TABLE
-- ============================================================================
-- Stores long-term behavioral patterns and preferences for each agent
-- Uses JSONB for flexible pattern storage with GIN indexing for fast queries

CREATE TABLE IF NOT EXISTS social_patterns (
    -- Primary key: unique agent identifier
    agent_id VARCHAR(255) PRIMARY KEY,

    -- Pattern data: flexible JSONB structure
    -- Example: {"confusion_history": 0.7, "frustration_history": 0.3, "engagement_baseline": 0.8}
    patterns JSONB NOT NULL DEFAULT '{}',

    -- Metadata
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    interaction_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT interaction_count_positive CHECK (interaction_count >= 0)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- GIN index for fast JSONB queries (e.g., pattern lookups)
CREATE INDEX IF NOT EXISTS idx_social_patterns_gin
ON social_patterns USING GIN(patterns);

-- B-tree index for temporal queries (most recent updates)
CREATE INDEX IF NOT EXISTS idx_social_patterns_last_updated
ON social_patterns(last_updated DESC);

-- Partial index for high-interaction agents (optimization for hot data)
CREATE INDEX IF NOT EXISTS idx_social_patterns_high_interaction
ON social_patterns(agent_id)
WHERE interaction_count > 100;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Trigger function to auto-update last_updated timestamp
CREATE OR REPLACE FUNCTION update_social_patterns_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to call the function on UPDATE
CREATE TRIGGER trigger_update_social_patterns_timestamp
BEFORE UPDATE ON social_patterns
FOR EACH ROW
EXECUTE FUNCTION update_social_patterns_timestamp();

-- ============================================================================
-- HELPER VIEWS
-- ============================================================================

-- View: Recent interactions (last 7 days)
CREATE OR REPLACE VIEW social_patterns_recent AS
SELECT
    agent_id,
    patterns,
    interaction_count,
    last_updated,
    EXTRACT(EPOCH FROM (NOW() - last_updated)) / 3600 AS hours_since_update
FROM social_patterns
WHERE last_updated >= NOW() - INTERVAL '7 days'
ORDER BY last_updated DESC;

-- ============================================================================
-- SEED DATA (Development Only)
-- ============================================================================
-- Insert sample patterns for testing (to be removed in production)

INSERT INTO social_patterns (agent_id, patterns, interaction_count) VALUES
    ('dev_user_001', '{"confusion_history": 0.6, "frustration_history": 0.3, "engagement_baseline": 0.7}', 15),
    ('dev_user_002', '{"confusion_history": 0.2, "frustration_history": 0.8, "engagement_baseline": 0.4}', 42),
    ('dev_user_003', '{"confusion_history": 0.1, "frustration_history": 0.1, "engagement_baseline": 0.9}', 128)
ON CONFLICT (agent_id) DO NOTHING;

-- ============================================================================
-- GRANTS (Adjust according to your security model)
-- ============================================================================

-- Grant permissions to maximus user
GRANT SELECT, INSERT, UPDATE, DELETE ON social_patterns TO maximus;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO maximus;

-- ============================================================================
-- VALIDATION QUERIES (For migration testing)
-- ============================================================================

-- Verify table exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'social_patterns') THEN
        RAISE EXCEPTION 'Migration failed: social_patterns table not created';
    END IF;

    -- Verify indexes exist
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_social_patterns_gin') THEN
        RAISE EXCEPTION 'Migration failed: GIN index not created';
    END IF;

    -- Verify trigger exists
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trigger_update_social_patterns_timestamp') THEN
        RAISE EXCEPTION 'Migration failed: Trigger not created';
    END IF;

    RAISE NOTICE 'Migration 001 completed successfully';
END $$;

-- ============================================================================
-- ROLLBACK SCRIPT (For emergency rollback)
-- ============================================================================
-- To rollback this migration, run:
-- DROP TRIGGER IF EXISTS trigger_update_social_patterns_timestamp ON social_patterns;
-- DROP FUNCTION IF EXISTS update_social_patterns_timestamp();
-- DROP VIEW IF EXISTS social_patterns_recent;
-- DROP TABLE IF EXISTS social_patterns CASCADE;
