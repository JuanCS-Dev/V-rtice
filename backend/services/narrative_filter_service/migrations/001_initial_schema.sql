-- HUB-AI Cockpit Soberano - PostgreSQL Schema Migration
-- Version: 1.0.0
-- Date: 2025-10-17

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- =============================================================================
-- CAMADA 1: Semantic Representations
-- =============================================================================

CREATE TABLE IF NOT EXISTS semantic_representations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id VARCHAR(255) UNIQUE NOT NULL,
    source_agent_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    content_embedding VECTOR(384),  -- sentence-transformers/all-MiniLM-L6-v2
    intent_classification VARCHAR(50) NOT NULL CHECK (intent_classification IN ('COOPERATIVE', 'COMPETITIVE', 'NEUTRAL', 'AMBIGUOUS')),
    intent_confidence DECIMAL(3,2) NOT NULL CHECK (intent_confidence BETWEEN 0 AND 1),
    raw_content TEXT,
    provenance_chain TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_semantic_agent_ts ON semantic_representations(source_agent_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_semantic_message_id ON semantic_representations(message_id);
CREATE INDEX IF NOT EXISTS idx_semantic_embedding ON semantic_representations USING ivfflat (content_embedding vector_cosine_ops) WITH (lists = 100);

-- =============================================================================
-- CAMADA 2: Strategic Patterns
-- =============================================================================

CREATE TABLE IF NOT EXISTS strategic_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_type VARCHAR(50) NOT NULL CHECK (pattern_type IN ('ALLIANCE', 'DECEPTION', 'INCONSISTENCY', 'COLLUSION')),
    agents_involved TEXT[] NOT NULL,
    detection_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    evidence_messages TEXT[] NOT NULL,
    mutual_information DECIMAL(5,4),
    deception_score DECIMAL(3,2) CHECK (deception_score BETWEEN 0 AND 1),
    inconsistency_score DECIMAL(3,2) CHECK (inconsistency_score BETWEEN 0 AND 1),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_strategic_pattern_type ON strategic_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_strategic_timestamp ON strategic_patterns(detection_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_strategic_agents ON strategic_patterns USING GIN (agents_involved);

-- =============================================================================
-- Alliances Graph
-- =============================================================================

CREATE TABLE IF NOT EXISTS alliances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_a VARCHAR(255) NOT NULL,
    agent_b VARCHAR(255) NOT NULL,
    strength DECIMAL(3,2) NOT NULL CHECK (strength BETWEEN 0 AND 1),
    first_detected TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_activity TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    interaction_count INT NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'DISSOLVED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(agent_a, agent_b)
);

CREATE INDEX IF NOT EXISTS idx_alliances_status ON alliances(status) WHERE status = 'ACTIVE';
CREATE INDEX IF NOT EXISTS idx_alliances_agents ON alliances(agent_a, agent_b);

-- =============================================================================
-- CAMADA 3: Verdicts
-- =============================================================================

CREATE TABLE IF NOT EXISTS verdicts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    category VARCHAR(50) NOT NULL CHECK (category IN ('COLLUSION', 'DECEPTION', 'ALLIANCE', 'THREAT', 'INCONSISTENCY')),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    title TEXT NOT NULL,
    agents_involved TEXT[] NOT NULL,
    target VARCHAR(255),
    evidence_chain TEXT[] NOT NULL,
    confidence DECIMAL(3,2) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    recommended_action VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'MITIGATED', 'DISMISSED')),
    mitigation_command_id UUID,
    color VARCHAR(7) DEFAULT '#FF0000',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_verdicts_severity_status ON verdicts(severity, status) WHERE status = 'ACTIVE';
CREATE INDEX IF NOT EXISTS idx_verdicts_timestamp ON verdicts(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_verdicts_category ON verdicts(category);

-- =============================================================================
-- C2L Commands
-- =============================================================================

CREATE TABLE IF NOT EXISTS c2l_commands (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    operator_id VARCHAR(255) NOT NULL,
    command_type VARCHAR(50) NOT NULL CHECK (command_type IN ('MUTE', 'ISOLATE', 'TERMINATE', 'SNAPSHOT_STATE', 'REVOKE_ACCESS', 'INJECT_CONSTRAINT')),
    target_agents TEXT[] NOT NULL,
    parameters JSONB,
    execution_deadline TIMESTAMPTZ,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'EXECUTING', 'EXECUTED', 'FAILED', 'TIMEOUT')),
    confirmation_received_at TIMESTAMPTZ,
    execution_result JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_c2l_operator ON c2l_commands(operator_id);
CREATE INDEX IF NOT EXISTS idx_c2l_status_ts ON c2l_commands(status, timestamp);
CREATE INDEX IF NOT EXISTS idx_c2l_type ON c2l_commands(command_type);

-- =============================================================================
-- Audit Trail
-- =============================================================================

CREATE TABLE IF NOT EXISTS audit_trail (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    operator_id VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    target VARCHAR(255),
    metadata JSONB,
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_operator_ts ON audit_trail(operator_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_trail(action);

-- =============================================================================
-- Triggers para updated_at
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_semantic_representations_updated_at ON semantic_representations;
CREATE TRIGGER update_semantic_representations_updated_at 
    BEFORE UPDATE ON semantic_representations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_alliances_updated_at ON alliances;
CREATE TRIGGER update_alliances_updated_at 
    BEFORE UPDATE ON alliances
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_verdicts_updated_at ON verdicts;
CREATE TRIGGER update_verdicts_updated_at 
    BEFORE UPDATE ON verdicts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Summary
-- =============================================================================

SELECT 
    'Tables Created' AS status,
    COUNT(*) AS count 
FROM information_schema.tables 
WHERE table_schema = 'public' 
    AND table_name IN (
        'semantic_representations', 
        'strategic_patterns', 
        'alliances', 
        'verdicts', 
        'c2l_commands', 
        'audit_trail'
    );
