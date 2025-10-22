-- Test Database Initialization Script
-- Sets up schemas and tables for integration tests
-- Author: Claude Code + JuanCS-Dev
-- Date: 2025-10-20

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Governance Schema
CREATE SCHEMA IF NOT EXISTS governance;

-- Audit Trail Table
CREATE TABLE IF NOT EXISTS governance.audit_trail (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    action_type VARCHAR(100) NOT NULL,
    actor VARCHAR(255),
    decision_id UUID,
    context JSONB,
    result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_timestamp ON governance.audit_trail(timestamp);
CREATE INDEX idx_audit_actor ON governance.audit_trail(actor);

-- Precedent Database Table
CREATE TABLE IF NOT EXISTS governance.precedents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id VARCHAR(255) UNIQUE NOT NULL,
    decision_type VARCHAR(100) NOT NULL,
    context JSONB NOT NULL,
    verdict VARCHAR(50) NOT NULL,
    justification TEXT,
    constitutional_basis TEXT[],
    embedding VECTOR(1536),  -- For semantic search (if pgvector available)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_precedents_type ON governance.precedents(decision_type);
CREATE INDEX idx_precedents_verdict ON governance.precedents(verdict);

-- HITL Decision Queue
CREATE TABLE IF NOT EXISTS governance.hitl_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    decision_id UUID UNIQUE NOT NULL,
    action_type VARCHAR(100) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    confidence DECIMAL(3,2),
    context JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    assigned_to VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    review_notes TEXT
);

CREATE INDEX idx_hitl_status ON governance.hitl_queue(status);
CREATE INDEX idx_hitl_risk ON governance.hitl_queue(risk_level);

-- Compliance Events
CREATE TABLE IF NOT EXISTS governance.compliance_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    regulation VARCHAR(50) NOT NULL,  -- GDPR, SOC2, ISO27001, etc
    severity VARCHAR(20) NOT NULL,
    details JSONB NOT NULL,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE INDEX idx_compliance_regulation ON governance.compliance_events(regulation);
CREATE INDEX idx_compliance_resolved ON governance.compliance_events(resolved);

-- Insert sample data for testing
INSERT INTO governance.precedents (case_id, decision_type, context, verdict, justification, constitutional_basis) VALUES
('CASE-001', 'data_access', '{"subject": "user_data", "purpose": "analysis"}', 'APPROVED', 'Legitimate purpose with consent', ARRAY['Lei Zero', 'Lei I']),
('CASE-002', 'harmful_action', '{"harm_type": "permanent", "target": "human"}', 'BLOCKED', 'Violates Lei Zero - causes permanent harm', ARRAY['Lei Zero']),
('CASE-003', 'privacy_breach', '{"data_type": "personal", "consent": false}', 'BLOCKED', 'GDPR violation - no consent', ARRAY['Lei I', 'Lei V'])
ON CONFLICT (case_id) DO NOTHING;

-- Grant permissions (assuming test user exists)
GRANT ALL ON SCHEMA governance TO maximus_test;
GRANT ALL ON ALL TABLES IN SCHEMA governance TO maximus_test;
GRANT ALL ON ALL SEQUENCES IN SCHEMA governance TO maximus_test;
